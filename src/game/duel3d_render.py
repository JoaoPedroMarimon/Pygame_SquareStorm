#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Motor 3D por software do minigame Arena 3D (src/game/minigame_duel3d.py).

Contém a parte "burra" do minigame: matemática vetorial, câmera FPS,
renderizador por painter's algorithm (com backface culling, iluminação por
face, névoa e camadas), o desenho do céu/arena e o desenho dos personagens
quadrados em 3D.

A lógica de jogo, rede e HUD fica em minigame_duel3d.py.
"""

import math
import pygame
from src.config import LARGURA, ALTURA_JOGO

# ============================================================
#  CONSTANTES DO MUNDO
# ============================================================

FOV = math.radians(78)
NEAR = 0.12

# Meia-extensão da arena: o chão vai de -ARENA a +ARENA nos dois eixos.
ARENA = 24.0
PAREDE_H = 7.5

# Jogador. As três medidas conversam com o boneco desenhado em
# desenhar_personagem(): o modelo tem ~1.62 de altura e a cabeça começa em 1.28.
# O olho fica ABAIXO da cabeça de propósito — se ficasse dentro dela, todo tiro
# na horizontal viraria headshot e o multiplicador perderia a graça.
OLHO_Y = 1.22
ALTURA_JOGADOR = 1.62
RAIO_JOGADOR = 0.40

# Névoa (dá profundidade e esconde o corte do horizonte)
FOG_START = 16.0
FOG_END = 68.0
FOG_COR = (14, 16, 32)

# Luz direcional (para sombrear as faces das caixas)
_LUZ = (0.42, 0.80, -0.36)
_lmag = math.sqrt(_LUZ[0] ** 2 + _LUZ[1] ** 2 + _LUZ[2] ** 2)
LUZ = (_LUZ[0] / _lmag, _LUZ[1] / _lmag, _LUZ[2] / _lmag)

# Camadas de desenho (resolvem o z-fighting do painter's algorithm).
# Dentro de uma camada ordenamos por profundidade; entre camadas, a maior vem
# por cima. É o que garante que a grade e as sombras apareçam SOBRE o piso:
# uma linha que atravessa a arena inteira tem profundidade média lá longe e
# seria coberta pelas placas de piso próximas se estivesse na mesma camada.
CAMADA_CHAO = 0        # placas do piso
CAMADA_DECAL = 0.5     # grade, anéis, sombras, marcações no chão
CAMADA_MUNDO = 1       # paredes, obstáculos, personagens, efeitos


# ============================================================
#  MATEMÁTICA
# ============================================================

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def normalizar(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if m < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / m, v[1] / m, v[2] / m)


def ang_lerp(a, b, t):
    """Interpola ângulos pelo caminho mais curto."""
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * t


def _fog(cor, depth):
    if depth <= FOG_START:
        return cor
    t = (depth - FOG_START) / (FOG_END - FOG_START)
    if t > 1.0:
        t = 1.0
    return (int(cor[0] + (FOG_COR[0] - cor[0]) * t),
            int(cor[1] + (FOG_COR[1] - cor[1]) * t),
            int(cor[2] + (FOG_COR[2] - cor[2]) * t))


class Camera:
    """Câmera FPS: yaw/pitch, com base ortonormal (right, up, forward)."""

    __slots__ = ('x', 'y', 'z', 'yaw', 'pitch')

    def __init__(self, x=0.0, y=OLHO_Y, z=0.0, yaw=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = 0.0

    def base(self):
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        F = (cp * sy, sp, cp * cy)
        R = (cy, 0.0, -sy)
        U = cross(F, R)
        return F, R, U

    def forward(self):
        cp = math.cos(self.pitch)
        return (cp * math.sin(self.yaw), math.sin(self.pitch), cp * math.cos(self.yaw))

    def forward_horizontal(self):
        return (math.sin(self.yaw), 0.0, math.cos(self.yaw))

    def right(self):
        return (math.cos(self.yaw), 0.0, -math.sin(self.yaw))


# ============================================================
#  RENDERIZADOR
# ============================================================

# Caches de superfícies translúcidas: recriar um Surface por frame para cada
# mancha/glow custa caro, e as variações visuais são poucas.
_CACHE_BLOB = {}
_CACHE_GLOW = {}


def _blob_surface(r, cor, alpha):
    chave = (r, cor, alpha)
    surf = _CACHE_BLOB.get(chave)
    if surf is None:
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (cor[0], cor[1], cor[2], alpha), (r, r), r)
        if len(_CACHE_BLOB) > 900:
            _CACHE_BLOB.clear()
        _CACHE_BLOB[chave] = surf
    return surf


def _glow_surface(r, cor):
    chave = (r, cor)
    surf = _CACHE_GLOW.get(chave)
    if surf is None:
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (cor[0], cor[1], cor[2], 60), (r * 2, r * 2), r * 2)
        pygame.draw.circle(surf, (cor[0], cor[1], cor[2], 130), (r * 2, r * 2), int(r * 1.35))
        if len(_CACHE_GLOW) > 900:
            _CACHE_GLOW.clear()
        _CACHE_GLOW[chave] = surf
    return surf


class Renderer3D:
    """
    Renderizador por software: acumula polígonos/linhas/orbes já projetados,
    ordena por (camada, profundidade) e desenha do mais longe para o mais perto.
    """

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.hw = w / 2
        self.hh = h / 2
        self.f = (w / 2) / math.tan(FOV / 2)
        self.itens = []
        self.cx = self.cy = self.cz = 0.0
        self.F = (0.0, 0.0, 1.0)
        self.R = (1.0, 0.0, 0.0)
        self.U = (0.0, 1.0, 0.0)

    def iniciar(self, cam):
        self.cx, self.cy, self.cz = cam.x, cam.y, cam.z
        self.F, self.R, self.U = cam.base()
        self.itens = []

    # ---------- transformações ----------

    def para_cam(self, p):
        rx = p[0] - self.cx
        ry = p[1] - self.cy
        rz = p[2] - self.cz
        R = self.R
        U = self.U
        F = self.F
        return (rx * R[0] + ry * R[1] + rz * R[2],
                rx * U[0] + ry * U[1] + rz * U[2],
                rx * F[0] + ry * F[1] + rz * F[2])

    def projetar(self, p):
        """Projeta um ponto do mundo. Retorna (sx, sy, depth) ou None."""
        c = self.para_cam(p)
        if c[2] < NEAR:
            return None
        iz = self.f / c[2]
        return (self.hw + c[0] * iz, self.hh - c[1] * iz, c[2])

    def projetar_direcao(self, d):
        """Projeta uma direção (ponto no infinito). Retorna (sx, sy) ou None."""
        fz = dot(d, self.F)
        if fz < 0.001:
            return None
        iz = self.f / fz
        return (self.hw + dot(d, self.R) * iz, self.hh - dot(d, self.U) * iz)

    @staticmethod
    def _clip_near(verts):
        out = []
        n = len(verts)
        for i in range(n):
            cur = verts[i]
            nxt = verts[(i + 1) % n]
            cur_in = cur[2] >= NEAR
            nxt_in = nxt[2] >= NEAR
            if cur_in:
                out.append(cur)
            if cur_in != nxt_in:
                t = (NEAR - cur[2]) / (nxt[2] - cur[2])
                out.append((cur[0] + (nxt[0] - cur[0]) * t,
                            cur[1] + (nxt[1] - cur[1]) * t, NEAR))
        return out

    # ---------- primitivas ----------

    def _emitir(self, cam_pts, cor, camada, borda=None):
        """Recebe pontos já em espaço de câmera, clipa, projeta e enfileira."""
        if len(cam_pts) < 3:
            return
        dentro = False
        for c in cam_pts:
            if c[2] >= NEAR:
                dentro = True
                break
        if not dentro:
            return
        pts = self._clip_near(cam_pts)
        if len(pts) < 3:
            return

        soma = 0.0
        tela_pts = []
        minx = miny = 1e9
        maxx = maxy = -1e9
        f = self.f
        hw = self.hw
        hh = self.hh
        for c in pts:
            z = c[2]
            soma += z
            iz = f / z
            x = hw + c[0] * iz
            y = hh - c[1] * iz
            tela_pts.append((x, y))
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y

        # Culling de tela (polígono totalmente fora da viewport)
        if maxx < 0 or minx > self.w or maxy < 0 or miny > self.h:
            return
        # Polígono degenerado (menor que 1px)
        if maxx - minx < 0.7 and maxy - miny < 0.7:
            return

        depth = soma / len(pts)
        if depth > FOG_END * 1.35:
            return
        self.itens.append((camada, depth, ('p', tela_pts, _fog(cor, depth), borda)))

    def poligono(self, pts_mundo, cor, camada=CAMADA_MUNDO, borda=None):
        self._emitir([self.para_cam(p) for p in pts_mundo], cor, camada, borda)

    def linha(self, p0, p1, cor, largura=1, camada=CAMADA_MUNDO):
        a = self.para_cam(p0)
        b = self.para_cam(p1)
        if a[2] < NEAR and b[2] < NEAR:
            return
        if a[2] < NEAR:
            t = (NEAR - a[2]) / (b[2] - a[2])
            a = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR)
        elif b[2] < NEAR:
            t = (NEAR - b[2]) / (a[2] - b[2])
            b = (b[0] + (a[0] - b[0]) * t, b[1] + (a[1] - b[1]) * t, NEAR)
        depth = (a[2] + b[2]) / 2
        if depth > FOG_END * 1.35:
            return
        iz = self.f / a[2]
        pa = (self.hw + a[0] * iz, self.hh - a[1] * iz)
        iz = self.f / b[2]
        pb = (self.hw + b[0] * iz, self.hh - b[1] * iz)
        if ((pa[0] < 0 and pb[0] < 0) or (pa[0] > self.w and pb[0] > self.w) or
                (pa[1] < 0 and pb[1] < 0) or (pa[1] > self.h and pb[1] > self.h)):
            return
        self.itens.append((camada, depth, ('l', pa, pb, _fog(cor, depth), largura)))

    def feixe(self, p0, p1, cor, largura=4, alpha=255):
        """Feixe brilhante (rastro de tiro): núcleo branco + glow colorido."""
        a = self.para_cam(p0)
        b = self.para_cam(p1)
        if a[2] < NEAR and b[2] < NEAR:
            return
        if a[2] < NEAR:
            t = (NEAR - a[2]) / (b[2] - a[2])
            a = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR)
        elif b[2] < NEAR:
            t = (NEAR - b[2]) / (a[2] - b[2])
            b = (b[0] + (a[0] - b[0]) * t, b[1] + (a[1] - b[1]) * t, NEAR)
        iz = self.f / a[2]
        pa = (self.hw + a[0] * iz, self.hh - a[1] * iz)
        iz = self.f / b[2]
        pb = (self.hw + b[0] * iz, self.hh - b[1] * iz)
        self.itens.append((CAMADA_MUNDO, min(a[2], b[2]),
                           ('f', pa, pb, cor, largura, alpha)))

    def orb(self, pos, raio_mundo, cor, brilho=True, raio_max=70):
        c = self.para_cam(pos)
        # Perto demais da câmera: viraria um disco gigante na tela (é uma
        # faísca dentro da "cabeça" do jogador). Descarta.
        if c[2] < 0.55:
            return
        iz = self.f / c[2]
        s = (self.hw + c[0] * iz, self.hh - c[1] * iz)
        if s[0] < -80 or s[0] > self.w + 80 or s[1] < -80 or s[1] > self.h + 80:
            return
        r = int(raio_mundo * iz)
        if r < 1:
            r = 1
        elif r > raio_max:
            r = raio_max
        self.itens.append((CAMADA_MUNDO, c[2], ('o', s, r, _fog(cor, c[2]), brilho)))

    def blob(self, pos, raio_mundo, cor, alpha, camada=CAMADA_MUNDO):
        """Mancha translúcida (sombra, aura, fumaça)."""
        c = self.para_cam(pos)
        if c[2] < NEAR:
            return
        iz = self.f / c[2]
        s = (self.hw + c[0] * iz, self.hh - c[1] * iz)
        if s[0] < -120 or s[0] > self.w + 120 or s[1] < -120 or s[1] > self.h + 120:
            return
        r = int(raio_mundo * iz)
        if r < 1:
            r = 1
        elif r > 380:
            r = 380
        # Quantiza o raio: mantém o cache de superfícies pequeno
        if r > 12:
            q = 2 if r < 64 else 8
            r -= r % q
        self.itens.append((camada, c[2] - 0.02, ('b', s, r, cor, alpha)))

    def caixa(self, cx, cy, cz, mx, my, mz, yaw, cor,
              camada=CAMADA_MUNDO, brilho=1.0, topo=True, neon=None):
        """
        Caixa (opcionalmente rotacionada em yaw) com iluminação por face e
        backface culling. cx/cy/cz = centro, mx/my/mz = meias-dimensões.
        """
        if yaw:
            c = math.cos(yaw)
            s = math.sin(yaw)
        else:
            c, s = 1.0, 0.0
        # Eixos locais no mundo (mesma convenção da câmera)
        axx, axz = c * mx, -s * mx
        azx, azz = s * mz, c * mz

        # 8 vértices: índice = (i>0)*4 + (j>0)*2 + (k>0)
        vw = []
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    vw.append((cx + axx * i + azx * k,
                               cy + my * j,
                               cz + axz * i + azz * k))
        vc = [self.para_cam(p) for p in vw]

        nx = (c, 0.0, -s)
        nz = (s, 0.0, c)
        dx = cx - self.cx
        dy = cy - self.cy
        dz = cz - self.cz

        faces = (
            # (normal, sinal, índices)
            (nx, 1, (5, 4, 6, 7)),        # +x
            (nx, -1, (0, 1, 3, 2)),       # -x
            (nz, 1, (1, 5, 7, 3)),        # +z
            (nz, -1, (4, 0, 2, 6)),       # -z
        )
        for (n, sg, idx) in faces:
            # Vetor do olho até o centro da face
            ox = dx + n[0] * sg * (mx if n is nx else mz)
            oz = dz + n[2] * sg * (mx if n is nx else mz)
            if (n[0] * sg) * ox + (n[2] * sg) * oz >= 0:
                continue
            lum = 0.52 + 0.48 * max(0.0, (n[0] * sg) * LUZ[0] + (n[2] * sg) * LUZ[2])
            lum *= brilho
            cf = (min(255, int(cor[0] * lum)), min(255, int(cor[1] * lum)),
                  min(255, int(cor[2] * lum)))
            self._emitir([vc[i] for i in idx], cf, camada)

        if topo and dy < -my:
            lum = (0.62 + 0.38 * LUZ[1]) * brilho
            cf = (min(255, int(cor[0] * lum)), min(255, int(cor[1] * lum)),
                  min(255, int(cor[2] * lum)))
            self._emitir([vc[2], vc[6], vc[7], vc[3]], cf, camada)

        if neon:
            # Fita de neon na aresta superior
            top = (vw[3], vw[7], vw[6], vw[2])
            for i in range(4):
                self.linha(top[i], top[(i + 1) % 4], neon, 2, camada)

    # ---------- saída ----------

    def desenhar(self, tela):
        self.itens.sort(key=lambda it: (it[0], -it[1]))
        linha = pygame.draw.line
        poly = pygame.draw.polygon
        circ = pygame.draw.circle
        for _, _, it in self.itens:
            tipo = it[0]
            if tipo == 'p':
                _, pts, cor, borda = it
                poly(tela, cor, pts)
                if borda:
                    poly(tela, borda, pts, 1)
            elif tipo == 'l':
                _, a, b, cor, lg = it
                linha(tela, cor, a, b, lg)
            elif tipo == 'f':
                _, a, b, cor, lg, alpha = it
                if alpha >= 250:
                    linha(tela, (cor[0] // 3, cor[1] // 3, cor[2] // 3), a, b, lg * 2)
                    linha(tela, cor, a, b, lg)
                    linha(tela, (255, 255, 255), a, b, max(1, lg // 3))
                else:
                    f = alpha / 255.0
                    c2 = (int(cor[0] * f), int(cor[1] * f), int(cor[2] * f))
                    linha(tela, c2, a, b, max(1, int(lg * f)))
            elif tipo == 'o':
                _, s, r, cor, brilho = it
                ix, iy = int(s[0]), int(s[1])
                if brilho and r < 150:
                    gl = _glow_surface(r, cor)
                    tela.blit(gl, (ix - r * 2, iy - r * 2))
                circ(tela, cor, (ix, iy), r)
                if r > 2:
                    circ(tela, (255, 255, 255), (ix, iy), max(1, r // 2))
            elif tipo == 'b':
                _, s, r, cor, alpha = it
                bl = _blob_surface(r, cor, alpha)
                tela.blit(bl, (int(s[0]) - r, int(s[1]) - r))


# ============================================================
#  ARENA (geometria compartilhada por render, colisão e raycast)
# ============================================================

def _cx(x, z, mx, mz, y0, y1, cor, neon=None, estilo='metal'):
    return {'x': float(x), 'z': float(z), 'mx': float(mx), 'mz': float(mz),
            'y0': float(y0), 'y1': float(y1), 'cor': cor, 'neon': neon,
            'estilo': estilo}


def _construir_obstaculos():
    """Layout simétrico: plataforma central, pilares, caixotes e barreiras."""
    obs = []
    # --- Plataforma central em dois níveis (ponto alto da arena) ---
    obs.append(_cx(0, 0, 5.2, 5.2, 0.0, 1.10, (40, 42, 76), (80, 220, 255), 'plataforma'))
    obs.append(_cx(0, 0, 2.5, 2.5, 1.10, 1.85, (50, 52, 92), (150, 245, 255), 'plataforma'))
    # Degraus de acesso nos 4 lados
    for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        obs.append(_cx(sx * 6.4, sz * 6.4,
                       1.7 if sx else 3.4, 3.4 if sx else 1.7,
                       0.0, 0.55, (33, 35, 64), (60, 170, 225), 'plataforma'))
    # --- Pilares altos (cobertura total) ---
    for (px, pz) in ((-12.5, -12.5), (12.5, -12.5), (-12.5, 12.5), (12.5, 12.5)):
        obs.append(_cx(px, pz, 1.45, 1.45, 0.0, PAREDE_H, (34, 30, 62),
                       (170, 100, 255), 'pilar'))
    # --- Caixotes (dá pra subir e pular) ---
    for (px, pz, h) in ((-17.5, 0, 2.3), (17.5, 0, 2.3), (0, -17.5, 2.3), (0, 17.5, 2.3),
                        (-9.5, -18.5, 1.5), (9.5, 18.5, 1.5),
                        (18.5, -9.5, 1.5), (-18.5, 9.5, 1.5)):
        obs.append(_cx(px, pz, 1.5, 1.5, 0.0, h, (72, 56, 38), (255, 175, 70), 'caixote'))
    # Caixotes empilhados junto dos grandes (mini escada)
    for (px, pz) in ((-17.5, 3.4), (17.5, -3.4), (3.4, -17.5), (-3.4, 17.5)):
        obs.append(_cx(px, pz, 1.1, 1.1, 0.0, 1.15, (66, 52, 36), (255, 175, 70), 'caixote'))
    # --- Barreiras baixas (protegem, mas dá pra atirar por cima) ---
    for (px, pz, hx, hz) in ((-7.0, -13.5, 3.6, 0.45), (7.0, 13.5, 3.6, 0.45),
                             (-13.5, 7.0, 0.45, 3.6), (13.5, -7.0, 0.45, 3.6)):
        obs.append(_cx(px, pz, hx, hz, 0.0, 1.0, (46, 48, 66), (90, 230, 200), 'barreira'))
    return obs


OBSTACULOS = _construir_obstaculos()

# Muros invisíveis do perímetro (colisão + bloqueio de tiro).
MUROS = [
    _cx(0, -ARENA - 1.0, ARENA + 2.0, 1.0, 0.0, PAREDE_H, (0, 0, 0)),
    _cx(0, ARENA + 1.0, ARENA + 2.0, 1.0, 0.0, PAREDE_H, (0, 0, 0)),
    _cx(-ARENA - 1.0, 0, 1.0, ARENA + 2.0, 0.0, PAREDE_H, (0, 0, 0)),
    _cx(ARENA + 1.0, 0, 1.0, ARENA + 2.0, 0.0, PAREDE_H, (0, 0, 0)),
]

COLISORES = OBSTACULOS + MUROS

# Pontos de nascimento: círculo grande ao redor do centro, olhando pro meio.
SPAWNS = []
for _i in range(8):
    _a = (2 * math.pi * _i) / 8 + math.pi / 8
    SPAWNS.append((math.cos(_a) * ARENA * 0.76, math.sin(_a) * ARENA * 0.76,
                   math.atan2(-math.cos(_a), -math.sin(_a))))


# Altura máxima de degrau que o jogador sobe andando. É usada tanto pela
# colisão horizontal quanto pela busca de chão — as duas PRECISAM combinar,
# senão dá pra entrar dentro de um degrau e não ter chão embaixo.
PASSO_MAX = 0.6


def altura_chao(x, z, y_ref, raio=RAIO_JOGADOR):
    """Topo mais alto em que os pés podem pousar (0 = chão da arena)."""
    melhor = 0.0
    limite = y_ref + PASSO_MAX
    for b in COLISORES:
        if b['y1'] <= melhor or b['y1'] > limite:
            continue
        if abs(x - b['x']) < b['mx'] + raio and abs(z - b['z']) < b['mz'] + raio:
            melhor = b['y1']
    return melhor


def resolver_colisao(x, z, y_pes, raio=RAIO_JOGADOR):
    """Empurra (x, z) para fora das caixas que bloqueiam a altura dos pés."""
    topo_corpo = y_pes + ALTURA_JOGADOR
    limite = y_pes + PASSO_MAX
    for b in COLISORES:
        if b['y1'] <= limite or b['y0'] >= topo_corpo:
            continue
        dx = x - b['x']
        dz = z - b['z']
        px = b['mx'] + raio - abs(dx)
        pz = b['mz'] + raio - abs(dz)
        if px > 0 and pz > 0:
            # Empurra pelo eixo de menor penetração
            if px < pz:
                x = b['x'] + (b['mx'] + raio) * (1 if dx >= 0 else -1)
            else:
                z = b['z'] + (b['mz'] + raio) * (1 if dz >= 0 else -1)
    lim = ARENA - raio - 0.05
    x = max(-lim, min(lim, x))
    z = max(-lim, min(lim, z))
    return x, z


def _ray_caixa(o, d, b):
    """Slab test raio x AABB. Retorna t de entrada (>0) ou None."""
    t0 = 0.0
    t1 = 1e9
    for (oi, di, cen, mei) in ((o[0], d[0], b['x'], b['mx']),
                               (o[1], d[1], (b['y0'] + b['y1']) / 2, (b['y1'] - b['y0']) / 2),
                               (o[2], d[2], b['z'], b['mz'])):
        lo = cen - mei
        hi = cen + mei
        if abs(di) < 1e-9:
            if oi < lo or oi > hi:
                return None
            continue
        a = (lo - oi) / di
        c = (hi - oi) / di
        if a > c:
            a, c = c, a
        if a > t0:
            t0 = a
        if c < t1:
            t1 = c
        if t0 > t1:
            return None
    return t0 if t0 > 0.001 else None


def ray_cenario(o, d, alcance):
    """Distância até o primeiro obstáculo/muro atingido (ou alcance)."""
    melhor = alcance
    for b in COLISORES:
        t = _ray_caixa(o, d, b)
        if t is not None and t < melhor:
            melhor = t
    return melhor


def linha_de_visao(a, b):
    """True se não há cenário entre os pontos a e b."""
    d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    dist = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    if dist < 0.001:
        return True
    d = (d[0] / dist, d[1] / dist, d[2] / dist)
    return ray_cenario(a, d, dist) >= dist - 0.02


# ============================================================
#  CÉU
# ============================================================

CEU_TOPO = (6, 6, 20)
CEU_MEIO = (26, 18, 56)
CEU_HORIZONTE = (74, 44, 96)


def gerar_ceu(rng):
    """Gera estrelas/nuvens/skyline em coordenadas de esfera (azimute/elevação)."""
    estrelas = []
    for _ in range(150):
        az = rng.uniform(0, 2 * math.pi)
        el = rng.uniform(0.02, 1.2)
        estrelas.append((az, el, rng.randint(90, 230), rng.choice([1, 1, 1, 2])))
    nebulosas = []
    for _ in range(7):
        nebulosas.append((rng.uniform(0, 2 * math.pi), rng.uniform(0.15, 0.75),
                          rng.randint(120, 260),
                          rng.choice([(90, 40, 140), (40, 70, 150), (120, 40, 100)])))
    # Skyline: torres distantes em volta de todo o horizonte
    skyline = []
    az = 0.0
    while az < 2 * math.pi:
        larg = rng.uniform(0.035, 0.085)
        alt = rng.uniform(0.02, 0.115)
        skyline.append((az, larg, alt, rng.random() < 0.35))
        az += larg + rng.uniform(0.005, 0.03)
    return {'estrelas': estrelas, 'nebulosas': nebulosas, 'skyline': skyline}


def _dir_esfera(az, el):
    ce = math.cos(el)
    return (ce * math.sin(az), math.sin(el), ce * math.cos(az))


def desenhar_ceu(tela, rend, cam, ceu, tempo):
    """Céu noturno com horizonte que acompanha o pitch e paralaxe no yaw."""
    h = ALTURA_JOGO
    horizonte = rend.hh + math.tan(cam.pitch) * rend.f
    hy = int(max(-h, min(h * 2, horizonte)))

    # Gradiente do céu (só a parte visível acima do horizonte)
    topo = max(0, min(h, hy))
    if topo > 0:
        passo = 3
        for y in range(0, topo, passo):
            t = 1.0 - (y / topo)
            t = t ** 1.25
            if t > 0.5:
                k = (t - 0.5) * 2
                cor = tuple(int(CEU_MEIO[i] + (CEU_TOPO[i] - CEU_MEIO[i]) * k) for i in range(3))
            else:
                k = t * 2
                cor = tuple(int(CEU_HORIZONTE[i] + (CEU_MEIO[i] - CEU_HORIZONTE[i]) * k) for i in range(3))
            pygame.draw.rect(tela, cor, (0, y, LARGURA, passo))
    if hy < h:
        pygame.draw.rect(tela, (10, 9, 18), (0, max(0, hy), LARGURA, h - max(0, hy)))

    # Nebulosas
    for (az, el, raio, cor) in ceu['nebulosas']:
        s = rend.projetar_direcao(_dir_esfera(az, el))
        if not s or s[1] > hy + 40:
            continue
        neb = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(neb, (cor[0], cor[1], cor[2], 26), (raio, raio), raio)
        pygame.draw.circle(neb, (cor[0], cor[1], cor[2], 22), (raio, raio), int(raio * 0.6))
        tela.blit(neb, (int(s[0]) - raio, int(s[1]) - raio))

    # Estrelas
    for (az, el, br, tam) in ceu['estrelas']:
        s = rend.projetar_direcao(_dir_esfera(az, el))
        if not s:
            continue
        if s[0] < -5 or s[0] > LARGURA + 5 or s[1] < -5 or s[1] > hy:
            continue
        cint = 0.55 + 0.45 * math.sin(tempo / 380.0 + az * 9.0)
        c = int(br * cint)
        pygame.draw.circle(tela, (c, c, min(255, c + 30)), (int(s[0]), int(s[1])), tam)

    # Lua com halo
    s = rend.projetar_direcao(_dir_esfera(2.35, 0.52))
    if s and -200 < s[0] < LARGURA + 200 and s[1] < hy + 100:
        lx, ly = int(s[0]), int(s[1])
        glow = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(glow, (130, 150, 220, 26), (130, 130), 130)
        pygame.draw.circle(glow, (160, 180, 235, 40), (130, 130), 74)
        tela.blit(glow, (lx - 130, ly - 130))
        pygame.draw.circle(tela, (222, 230, 248), (lx, ly), 34)
        pygame.draw.circle(tela, (196, 205, 230), (lx - 11, ly - 8), 8)
        pygame.draw.circle(tela, (200, 210, 234), (lx + 9, ly + 11), 5)

    # Planeta anelado (detalhe do skybox)
    s = rend.projetar_direcao(_dir_esfera(4.9, 0.30))
    if s and -160 < s[0] < LARGURA + 160 and s[1] < hy + 60:
        px, py = int(s[0]), int(s[1])
        pygame.draw.circle(tela, (120, 70, 130), (px, py), 20)
        pygame.draw.circle(tela, (150, 95, 155), (px - 5, py - 5), 13)
        anel = pygame.Surface((90, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(anel, (200, 160, 220, 90), (0, 0, 90, 30), 3)
        tela.blit(anel, (px - 45, py - 15))

    # Skyline distante (silhueta de torres com janelas acesas)
    for (az, larg, alt, luz) in ceu['skyline']:
        a = rend.projetar_direcao(_dir_esfera(az, 0.0))
        b = rend.projetar_direcao(_dir_esfera(az + larg, 0.0))
        c = rend.projetar_direcao(_dir_esfera(az + larg * 0.5, alt))
        if not a or not b or not c:
            continue
        x0, x1 = a[0], b[0]
        if x1 < x0 or x1 - x0 > LARGURA * 0.5:
            continue
        if x1 < -20 or x0 > LARGURA + 20:
            continue
        topo_t = c[1]
        base = a[1]
        if base < topo_t:
            continue
        pygame.draw.rect(tela, (17, 15, 32), (int(x0), int(topo_t), int(x1 - x0) + 1,
                                              int(base - topo_t) + 2))
        pygame.draw.line(tela, (58, 40, 92), (int(x0), int(topo_t)), (int(x1), int(topo_t)), 1)
        if luz:
            jy = int(topo_t) + 6
            while jy < base - 4:
                pygame.draw.rect(tela, (120, 90, 60), (int(x0) + 3, jy, 2, 3))
                jy += 9
            pygame.draw.circle(tela, (255, 90, 90) if (tempo // 700) % 2 else (110, 40, 40),
                               (int((x0 + x1) / 2), int(topo_t) - 2), 2)


# ============================================================
#  ARENA (desenho)
# ============================================================

_TILE = 6.0


def desenhar_arena(rend, cam, tempo):
    """Chão, grade, decalques e paredes com painéis de neon."""
    A = ARENA
    fx, fz = math.sin(cam.yaw), math.cos(cam.yaw)

    # ---- Chão em placas (culling por cone de visão) ----
    n = int(A / _TILE)
    for iz in range(-n, n):
        z0 = iz * _TILE
        for ix in range(-n, n):
            x0 = ix * _TILE
            mcx = x0 + _TILE / 2 - cam.x
            mcz = z0 + _TILE / 2 - cam.z
            if mcx * fx + mcz * fz < -_TILE:
                continue
            if mcx * mcx + mcz * mcz > (FOG_END * 1.2) ** 2:
                continue
            claro = (ix + iz) % 2 == 0
            cor = (30, 34, 54) if claro else (17, 19, 32)
            rend.poligono([(x0, 0, z0), (x0 + _TILE, 0, z0),
                           (x0 + _TILE, 0, z0 + _TILE), (x0, 0, z0 + _TILE)],
                          cor, CAMADA_CHAO)

    # ---- Grade luminosa (em segmentos: cada pedaço tem a própria profundidade) ----
    pulso = 0.5 + 0.5 * math.sin(tempo / 900.0)
    cor_grid = (int(24 + 26 * pulso), int(70 + 60 * pulso), int(96 + 70 * pulso))
    for i in range(-n, n + 1):
        v = i * _TILE
        for j in range(-n, n):
            w0 = j * _TILE
            w1 = w0 + _TILE
            # Segmento paralelo a Z
            mcx = v - cam.x
            mcz = w0 + _TILE / 2 - cam.z
            if mcx * fx + mcz * fz > -_TILE and mcx * mcx + mcz * mcz < 3000:
                rend.linha((v, 0.02, w0), (v, 0.02, w1), cor_grid, 1, CAMADA_DECAL)
            # Segmento paralelo a X
            mcx = w0 + _TILE / 2 - cam.x
            mcz = v - cam.z
            if mcx * fx + mcz * fz > -_TILE and mcx * mcx + mcz * mcz < 3000:
                rend.linha((w0, 0.02, v), (w1, 0.02, v), cor_grid, 1, CAMADA_DECAL)

    # ---- Anel luminoso central ----
    seg = 30
    r1 = 8.6
    pulso_c = 0.5 + 0.5 * math.sin(tempo / 420.0)
    cor_anel = (int(50 + 60 * pulso_c), int(180 + 60 * pulso_c), 255)
    ant = None
    for i in range(seg + 1):
        a = (2 * math.pi * i) / seg
        p = (math.cos(a) * r1, 0.03, math.sin(a) * r1)
        if ant:
            rend.linha(ant, p, cor_anel, 2, CAMADA_DECAL)
        ant = p
    # Anel interno (pulsa junto com o externo)
    ant = None
    for i in range(seg + 1):
        a = (2 * math.pi * i) / seg
        p = (math.cos(a) * (r1 - 1.4), 0.03, math.sin(a) * (r1 - 1.4))
        if ant:
            rend.linha(ant, p, (int(cor_anel[0] * 0.5), int(cor_anel[1] * 0.5),
                                int(cor_anel[2] * 0.6)), 1, CAMADA_DECAL)
        ant = p

    # Traços correndo pelo chão em direção ao centro (guia visual)
    for i in range(8):
        a = (2 * math.pi * i) / 8
        ca, sa = math.cos(a), math.sin(a)
        for k in range(3):
            fase = (tempo / 1100.0 + k * 0.33) % 1.0
            rr = 18.0 - fase * 7.0
            br = int(60 + 120 * (1 - fase))
            rend.linha((ca * rr, 0.05, sa * rr), (ca * (rr - 1.1), 0.05, sa * (rr - 1.1)),
                       (int(br * 0.3), int(br * 0.8), br), 2, CAMADA_DECAL)

    # ---- Paredes em segmentos com painéis ----
    seg_n = 8
    passo = (2 * A) / seg_n
    for lado in range(4):
        for i in range(seg_n):
            a0 = -A + i * passo
            a1 = a0 + passo
            if lado == 0:
                p0, p1 = (a0, -A), (a1, -A)
            elif lado == 1:
                p0, p1 = (a1, A), (a0, A)
            elif lado == 2:
                p0, p1 = (-A, a1), (-A, a0)
            else:
                p0, p1 = (A, a0), (A, a1)
            mcx = (p0[0] + p1[0]) / 2 - cam.x
            mcz = (p0[1] + p1[1]) / 2 - cam.z
            if mcx * fx + mcz * fz < -6:
                continue
            escuro = (i % 2 == 0)
            cor = (30, 28, 52) if escuro else (24, 23, 44)
            rend.poligono([(p0[0], 0, p0[1]), (p1[0], 0, p1[1]),
                           (p1[0], PAREDE_H, p1[1]), (p0[0], PAREDE_H, p0[1])], cor)
            # Painel de neon vertical
            fase = 0.5 + 0.5 * math.sin(tempo / 600.0 + i * 0.8 + lado)
            cneon = (int(30 + 60 * fase), int(120 + 100 * fase), int(180 + 70 * fase))
            mx = (p0[0] + p1[0]) / 2
            mz = (p0[1] + p1[1]) / 2
            rend.linha((mx, 0.6, mz), (mx, PAREDE_H - 0.6, mz), cneon, 3)
            # Faixa horizontal a meia altura
            rend.linha((p0[0], 2.6, p0[1]), (p1[0], 2.6, p1[1]), (52, 60, 110), 2)
            # Fita de neon no topo (por segmento, senão a parede cobre a linha)
            rend.linha((p0[0], PAREDE_H - 0.05, p0[1]),
                       (p1[0], PAREDE_H - 0.05, p1[1]), (90, 220, 255), 4)
            # Rodapé luminoso
            rend.linha((p0[0], 0.06, p0[1]), (p1[0], 0.06, p1[1]),
                       (40, 120, 170), 2, CAMADA_DECAL)

    cantos = [(-A, -A), (A, -A), (A, A), (-A, A)]

    # Holofotes nos cantos
    for (px, pz) in cantos:
        sx = -1 if px < 0 else 1
        sz = -1 if pz < 0 else 1
        bx = px - sx * 1.2
        bz = pz - sz * 1.2
        rend.caixa(bx, PAREDE_H - 0.6, bz, 0.5, 0.5, 0.5, 0.0, (44, 44, 70))
        rend.orb((bx, PAREDE_H - 1.2, bz), 0.34, (255, 235, 180))
        rend.blob((bx, PAREDE_H - 1.6, bz), 2.4, (255, 220, 150), 26)

    # ---- Obstáculos ----
    for b in OBSTACULOS:
        cy = (b['y0'] + b['y1']) / 2
        my = (b['y1'] - b['y0']) / 2
        dx = b['x'] - cam.x
        dz = b['z'] - cam.z
        if dx * fx + dz * fz < -(b['mx'] + b['mz'] + 4):
            continue
        estilo = b['estilo']
        if estilo == 'caixote':
            rend.caixa(b['x'], cy, b['z'], b['mx'], my, b['mz'], 0.0, b['cor'])
            # Cintas metálicas
            for yy in (b['y0'] + (b['y1'] - b['y0']) * 0.3, b['y0'] + (b['y1'] - b['y0']) * 0.75):
                rend.caixa(b['x'], yy, b['z'], b['mx'] + 0.03, 0.07, b['mz'] + 0.03,
                           0.0, (120, 96, 58), topo=False)
            rend.orb((b['x'], b['y1'] + 0.12, b['z']), 0.09, b['neon'])
        elif estilo == 'pilar':
            rend.caixa(b['x'], cy, b['z'], b['mx'], my, b['mz'], 0.0, b['cor'])
            pl = 0.5 + 0.5 * math.sin(tempo / 500.0 + b['x'])
            cn = (int(b['neon'][0] * (0.5 + 0.5 * pl)), int(b['neon'][1] * (0.5 + 0.5 * pl)),
                  int(b['neon'][2] * (0.5 + 0.5 * pl)))
            for s in (-1, 1):
                rend.linha((b['x'] + s * (b['mx'] + 0.02), b['y0'] + 0.4, b['z']),
                           (b['x'] + s * (b['mx'] + 0.02), b['y1'] - 0.4, b['z']), cn, 3)
                rend.linha((b['x'], b['y0'] + 0.4, b['z'] + s * (b['mz'] + 0.02)),
                           (b['x'], b['y1'] - 0.4, b['z'] + s * (b['mz'] + 0.02)), cn, 3)
        elif estilo == 'plataforma':
            rend.caixa(b['x'], cy, b['z'], b['mx'], my, b['mz'], 0.0, b['cor'],
                       neon=b['neon'])
        else:  # barreira
            rend.caixa(b['x'], cy, b['z'], b['mx'], my, b['mz'], 0.0, b['cor'],
                       neon=b['neon'])

    # Núcleo flutuante sobre a plataforma central
    bob = math.sin(tempo / 700.0) * 0.22
    giro = tempo / 900.0
    rend.orb((0, 3.4 + bob, 0), 0.45, (120, 240, 255))
    for i in range(3):
        a = giro + (2 * math.pi * i) / 3
        rend.orb((math.cos(a) * 1.1, 3.4 + bob + math.sin(giro * 2 + i) * 0.2,
                  math.sin(a) * 1.1), 0.14, (200, 130, 255))
    rend.blob((0, 3.4 + bob, 0), 1.8, (90, 200, 255), 22)


# ============================================================
#  PERSONAGENS QUADRADOS EM 3D
# ============================================================

def _mistura(cor, alvo, t):
    return (int(cor[0] + (alvo[0] - cor[0]) * t),
            int(cor[1] + (alvo[1] - cor[1]) * t),
            int(cor[2] + (alvo[2] - cor[2]) * t))


def _chapeu_3d(rend, x, y, z, yaw, tipo, tempo):
    """Cosmético de cabeça em 3D (mesmos tipos do lobby)."""
    if not tipo:
        return
    if tipo == 'cartola':
        rend.caixa(x, y + 0.03, z, 0.30, 0.03, 0.30, yaw, (24, 24, 30))
        rend.caixa(x, y + 0.22, z, 0.19, 0.17, 0.19, yaw, (32, 32, 40))
        rend.caixa(x, y + 0.14, z, 0.20, 0.04, 0.20, yaw, (190, 55, 65), topo=False)
    elif tipo == 'bone':
        rend.caixa(x, y + 0.10, z, 0.22, 0.10, 0.22, yaw, (205, 60, 60))
        rend.caixa(x + math.sin(yaw) * 0.30, y + 0.03, z + math.cos(yaw) * 0.30,
                   0.20, 0.03, 0.13, yaw, (168, 42, 42))
        rend.orb((x, y + 0.22, z), 0.05, (255, 210, 90))
    elif tipo == 'coroa':
        rend.caixa(x, y + 0.06, z, 0.24, 0.06, 0.24, yaw, (238, 190, 44))
        for (ox, oz) in ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)):
            rend.caixa(x + ox * math.cos(yaw) + oz * math.sin(yaw), y + 0.20,
                       z - ox * math.sin(yaw) + oz * math.cos(yaw),
                       0.05, 0.10, 0.05, yaw, (255, 205, 60))
        rend.orb((x, y + 0.12, z + 0.001), 0.06, (230, 70, 100))
    elif tipo == 'chifres':
        for s in (-1, 1):
            ox = s * 0.20
            rend.caixa(x + ox * math.cos(yaw), y + 0.14, z - ox * math.sin(yaw),
                       0.07, 0.16, 0.07, yaw, (176, 34, 34))
            rend.caixa(x + ox * 1.25 * math.cos(yaw), y + 0.30, z - ox * 1.25 * math.sin(yaw),
                       0.05, 0.10, 0.05, yaw, (215, 62, 62))
    elif tipo == 'aureola':
        r = 0.30
        ant = None
        for i in range(13):
            a = (2 * math.pi * i) / 12
            p = (x + math.cos(a) * r, y + 0.34 + math.sin(tempo / 500.0) * 0.03,
                 z + math.sin(a) * r)
            if ant:
                rend.linha(ant, p, (255, 235, 110), 3)
            ant = p
    elif tipo == 'festa':
        rend.caixa(x, y + 0.10, z, 0.17, 0.10, 0.17, yaw, (80, 200, 220))
        rend.caixa(x, y + 0.26, z, 0.09, 0.09, 0.09, yaw, (255, 120, 180))
        rend.orb((x, y + 0.40, z), 0.07, (255, 230, 90))
    elif tipo == 'antena':
        cy_, sy_ = math.cos(yaw), math.sin(yaw)
        for s in (-1, 1):
            bx = x + (s * 0.13) * cy_
            bz = z - (s * 0.13) * sy_
            tx = x + (s * 0.26) * cy_
            tz = z - (s * 0.26) * sy_
            rend.linha((bx, y, bz), (tx, y + 0.32, tz), (130, 130, 145), 2)
            rend.orb((tx, y + 0.34, tz), 0.06, (120, 255, 170))


def desenhar_personagem(rend, cam, p, tempo, cor_arma=(150, 200, 255), detalhe=True):
    """
    Boneco quadrado 3D: pernas animadas, tronco, braços, cabeça com visor,
    mochila de energia, arma na mão e sombra no chão.
    """
    x, z, y = p.x, p.z, p.y
    yaw = p.yaw
    cor = p.cor
    esc = _mistura(cor, (0, 0, 0), 0.42)
    cla = _mistura(cor, (255, 255, 255), 0.30)

    dcx = x - cam.x
    dcz = z - cam.z
    dist2 = dcx * dcx + dcz * dcz

    # Sombra projetada (camada de decalque: fica por cima do piso)
    chao = altura_chao(x, z, y + 0.1)
    rend.blob((x, chao + 0.03, z), 0.52, (0, 0, 0), 110, CAMADA_DECAL)

    if dist2 > 46 * 46:
        return

    # LOD: longe demais -> boneco simplificado
    if dist2 > 26 * 26 or not detalhe:
        rend.caixa(x, y + 0.62, z, 0.30, 0.42, 0.22, yaw, cor)
        rend.caixa(x, y + 1.30, z, 0.21, 0.20, 0.21, yaw, cla)
        return

    passo = getattr(p, 'passo', 0.0)
    andando = getattr(p, 'vel_atual', 0.0) > 0.4
    balanco = math.sin(passo) * (0.20 if andando else 0.0)
    bob = (abs(math.sin(passo)) * 0.045) if andando else math.sin(tempo / 620.0) * 0.02
    no_ar = getattr(p, 'no_chao', True) is False

    if no_ar:
        balanco = 0.35
        bob = 0.0

    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)

    def mundo(lx, lz):
        """Converte offset local (direita, frente) para o mundo."""
        return (x + lx * cos_y + lz * sin_y, z - lx * sin_y + lz * cos_y)

    # --- Pernas (alternam frente/trás) ---
    for s, fase in ((-1, balanco), (1, -balanco)):
        px, pz = mundo(s * 0.155, fase * 0.55)
        alt = 0.30 - abs(fase) * 0.10
        rend.caixa(px, y + alt + bob, pz, 0.115, alt, 0.135, yaw,
                   _mistura(esc, (30, 30, 40), 0.25))
        # Bota
        rend.caixa(px, y + 0.06 + bob, pz + 0.02, 0.13, 0.07, 0.16, yaw, (26, 26, 36))

    base_y = y + 0.58 + bob

    # --- Tronco ---
    rend.caixa(x, base_y + 0.30, z, 0.30, 0.32, 0.20, yaw, cor)
    # Peitoral / colete
    px, pz = mundo(0.0, 0.21)
    rend.caixa(px, base_y + 0.34, pz, 0.24, 0.20, 0.03, yaw, esc, topo=False)
    rend.orb((px, base_y + 0.34, pz), 0.06, cla)
    # Cinto
    rend.caixa(x, base_y + 0.02, z, 0.31, 0.05, 0.21, yaw, (34, 34, 46), topo=False)

    # --- Mochila de energia ---
    bx, bz = mundo(0.0, -0.26)
    rend.caixa(bx, base_y + 0.34, bz, 0.20, 0.22, 0.08, yaw, _mistura(esc, (40, 46, 70), 0.5))
    pulso = 0.5 + 0.5 * math.sin(tempo / 260.0 + x)
    rend.orb((bx, base_y + 0.42, bz), 0.07 + 0.02 * pulso, (110, 230, 255))

    # --- Ombreiras + braços ---
    for s in (-1, 1):
        ox_, oz_ = mundo(s * 0.35, 0.0)
        rend.caixa(ox_, base_y + 0.56, oz_, 0.10, 0.09, 0.16, yaw, cla)
        ax, az = mundo(s * 0.36, 0.10 if s > 0 else -balanco * 0.35)
        rend.caixa(ax, base_y + 0.32, az, 0.085, 0.22, 0.10, yaw, esc)
        # Luva
        rend.caixa(ax, base_y + 0.10, az, 0.09, 0.07, 0.11, yaw, (32, 32, 44))

    # --- Cabeça + visor ---
    hy = base_y + 0.82
    rend.caixa(x, hy, z, 0.215, 0.20, 0.215, yaw, cla)
    vx, vz = mundo(0.0, 0.22)
    rend.caixa(vx, hy + 0.02, vz, 0.165, 0.065, 0.025, yaw, (14, 16, 24), topo=False)
    cor_visor = (255, 90, 80) if getattr(p, 'hp', 100) < 35 else (110, 235, 255)
    rend.orb((vx, hy + 0.02, vz), 0.055, cor_visor)
    # Antena lateral
    tx, tz = mundo(0.19, -0.05)
    rend.linha((tx, hy + 0.16, tz), (tx, hy + 0.40, tz), (150, 160, 180), 2)
    rend.orb((tx, hy + 0.42, tz), 0.045, (255, 120, 120))

    _chapeu_3d(rend, x, hy + 0.20, z, yaw, getattr(p, 'chapeu', None), tempo)

    # --- Arma na mão (cano apontando pra frente do boneco) ---
    gx, gz = mundo(0.34, 0.42)
    rend.caixa(gx, base_y + 0.20, gz, 0.08, 0.09, 0.34, yaw, (48, 50, 64))
    cx_, cz_ = mundo(0.34, 0.72)
    rend.caixa(cx_, base_y + 0.21, cz_, 0.05, 0.05, 0.22, yaw, (32, 34, 44))
    mx, mz = mundo(0.34, 0.94)
    rend.orb((mx, base_y + 0.21, mz), 0.06, cor_arma)
    # Faixa de energia na lateral da arma
    rend.linha((gx, base_y + 0.29, gz), (cx_, base_y + 0.27, cz_), cor_arma, 2)
