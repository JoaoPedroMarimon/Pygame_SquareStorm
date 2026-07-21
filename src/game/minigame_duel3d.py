#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Duelo 3D - 1v1 que começa em 2D e faz uma transição para 3D.

Fluxo:
  1. INTRO_2D    : os dois duelistas aparecem em 2D (estilo dos outros minigames).
  2. TRANSICAO   : efeito de transição 2D -> 3D (flash, anéis, glitch, túnel).
  3. DUELO_3D    : duelo em primeira pessoa num renderizador 3D por software
                   (projeção em perspectiva + fog + painter; câmera FPS estilo do
                   projeto 3d_ptn: yaw/pitch pelo mouse, WASD, forward/right).
  4. RESULTADO   : vitória/derrota e volta ao lobby.

Nesta primeira versão o oponente é um bot (o 3D em rede fica para depois).
"""

import math
import random
import pygame
from src.config import *
from src.utils.display_manager import present_frame

# ============================================================
#  CONSTANTES
# ============================================================

FOV = math.radians(72)
NEAR = 0.15
ARENA = 9.0
PAREDE_H = 3.6
OLHO_Y = 1.45
HP_MAX = 6

VEL_JOGADOR = 5.4
SENS = 0.0022
RAIO_OPONENTE = 0.55
ALCANCE_TIRO = 45.0

TEMPO_INTRO = 2400
TEMPO_TRANSICAO = 1700
TEMPO_RESULTADO = 3200

# Fog (profundidade)
FOG_START = 7.0
FOG_END = 30.0
FOG_COR = (24, 22, 44)

# Céu
CEU_TOPO = (10, 8, 22)
CEU_HORIZONTE = (48, 34, 74)


# ============================================================
#  MATEMÁTICA VETORIAL
# ============================================================

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _fog(cor, depth):
    if depth <= FOG_START:
        return cor
    t = min(1.0, (depth - FOG_START) / (FOG_END - FOG_START))
    return (int(cor[0] + (FOG_COR[0] - cor[0]) * t),
            int(cor[1] + (FOG_COR[1] - cor[1]) * t),
            int(cor[2] + (FOG_COR[2] - cor[2]) * t))


class Camera:
    """Câmera FPS (yaw/pitch, forward/right) — mesmo esquema do projeto 3d_ptn."""

    def __init__(self, x, z, yaw):
        self.x = x
        self.y = OLHO_Y
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
        U = _cross(F, R)
        return F, R, U

    def forward_horizontal(self):
        return (math.sin(self.yaw), 0.0, math.cos(self.yaw))

    def right(self):
        return (math.cos(self.yaw), 0.0, -math.sin(self.yaw))


# ============================================================
#  RENDERIZADOR 3D POR SOFTWARE
# ============================================================

class Renderer3D:
    """Coleta polígonos/linhas/orbes, ordena por profundidade (painter) e desenha."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.f = (w / 2) / math.tan(FOV / 2)
        self.itens = []

    def iniciar(self, cam):
        self.cam = cam
        self.cpos = (cam.x, cam.y, cam.z)
        self.F, self.R, self.U = cam.base()
        self.itens = []

    def _para_cam(self, p):
        rel = _sub(p, self.cpos)
        return (_dot(rel, self.R), _dot(rel, self.U), _dot(rel, self.F))

    def _proj(self, c):
        sx = self.w / 2 + (c[0] / c[2]) * self.f
        sy = self.h / 2 - (c[1] / c[2]) * self.f
        return (sx, sy)

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

    def poligono(self, pts_mundo, cor, borda=None):
        cam_pts = self._clip_near([self._para_cam(p) for p in pts_mundo])
        if len(cam_pts) < 3:
            return
        depth = sum(c[2] for c in cam_pts) / len(cam_pts)
        tela_pts = [self._proj(c) for c in cam_pts]
        self.itens.append((depth, ('poly', tela_pts, _fog(cor, depth), borda)))

    def linha(self, p0, p1, cor, largura=1):
        a = self._para_cam(p0)
        b = self._para_cam(p1)
        if a[2] < NEAR and b[2] < NEAR:
            return
        if a[2] < NEAR:
            t = (NEAR - a[2]) / (b[2] - a[2])
            a = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR)
        elif b[2] < NEAR:
            t = (NEAR - b[2]) / (a[2] - b[2])
            b = (b[0] + (a[0] - b[0]) * t, b[1] + (a[1] - b[1]) * t, NEAR)
        depth = (a[2] + b[2]) / 2
        self.itens.append((depth, ('line', self._proj(a), self._proj(b), _fog(cor, depth), largura)))

    def feixe(self, p0, p1, cor):
        """Feixe brilhante (tiro do jogador): núcleo branco + glow colorido."""
        a = self._para_cam(p0)
        b = self._para_cam(p1)
        if a[2] < NEAR and b[2] < NEAR:
            return
        if a[2] < NEAR:
            t = (NEAR - a[2]) / (b[2] - a[2])
            a = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR)
        elif b[2] < NEAR:
            t = (NEAR - b[2]) / (a[2] - b[2])
            b = (b[0] + (a[0] - b[0]) * t, b[1] + (a[1] - b[1]) * t, NEAR)
        self.itens.append((min(a[2], b[2]), ('beam', self._proj(a), self._proj(b), cor)))

    def orb(self, pos, raio_mundo, cor):
        c = self._para_cam(pos)
        if c[2] < NEAR:
            return
        s = self._proj(c)
        r = max(1, int(raio_mundo * self.f / c[2]))
        self.itens.append((c[2], ('orb', s, r, _fog(cor, c[2]))))

    def blob(self, pos, raio_mundo, cor, alpha):
        c = self._para_cam(pos)
        if c[2] < NEAR:
            return
        s = self._proj(c)
        r = max(1, int(raio_mundo * self.f / c[2]))
        self.itens.append((c[2] + 0.01, ('blob', s, r, cor, alpha)))

    def desenhar(self, tela):
        self.itens.sort(key=lambda it: -it[0])
        for _, it in self.itens:
            tipo = it[0]
            if tipo == 'poly':
                _, pts, cor, borda = it
                pygame.draw.polygon(tela, cor, pts)
                if borda:
                    pygame.draw.polygon(tela, borda, pts, 1)
            elif tipo == 'line':
                _, a, b, cor, lg = it
                pygame.draw.line(tela, cor, a, b, lg)
            elif tipo == 'beam':
                _, a, b, cor = it
                pygame.draw.line(tela, tuple(c // 3 for c in cor), a, b, 7)
                pygame.draw.line(tela, cor, a, b, 4)
                pygame.draw.line(tela, (255, 255, 255), a, b, 1)
            elif tipo == 'orb':
                _, s, r, cor = it
                ix, iy = int(s[0]), int(s[1])
                gl = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                pygame.draw.circle(gl, (*cor, 90), (r * 2, r * 2), r * 2)
                pygame.draw.circle(gl, (*cor, 150), (r * 2, r * 2), int(r * 1.3))
                tela.blit(gl, (ix - r * 2, iy - r * 2))
                pygame.draw.circle(tela, cor, (ix, iy), r)
                pygame.draw.circle(tela, (255, 255, 255), (ix, iy), max(1, r // 2))
            elif tipo == 'blob':
                _, s, r, cor, alpha = it
                bl = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(bl, (*cor, alpha), (r, r), r)
                tela.blit(bl, (int(s[0]) - r, int(s[1]) - r))


# ============================================================
#  CÉU E ARENA
# ============================================================

def _desenhar_ceu(tela, estrelas, tempo):
    metade = int(ALTURA_JOGO * 0.56)
    for y in range(0, metade, 2):
        t = y / metade
        cor = tuple(int(CEU_TOPO[i] + (CEU_HORIZONTE[i] - CEU_TOPO[i]) * (t ** 1.4)) for i in range(3))
        pygame.draw.rect(tela, cor, (0, y, LARGURA, 2))
    # Estrelas (cintilam)
    for (sx, sy, br, tam) in estrelas:
        cint = 0.6 + 0.4 * math.sin(tempo / 400 + sx * 0.05)
        c = int(br * cint)
        pygame.draw.circle(tela, (c, c, min(255, c + 25)), (sx, sy), tam)
    # Lua com brilho
    lx, ly = int(LARGURA * 0.78), int(ALTURA_JOGO * 0.16)
    glow = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.circle(glow, (120, 140, 200, 40), (80, 80), 80)
    pygame.draw.circle(glow, (150, 170, 220, 60), (80, 80), 45)
    tela.blit(glow, (lx - 80, ly - 80))
    pygame.draw.circle(tela, (210, 220, 240), (lx, ly), 26)
    pygame.draw.circle(tela, (180, 190, 215), (lx - 8, ly - 6), 6)
    # Brilho no horizonte
    hb = pygame.Surface((LARGURA, 60), pygame.SRCALPHA)
    for i in range(60):
        a = int(70 * (1 - i / 60))
        pygame.draw.line(hb, (80, 60, 130, a), (0, i), (LARGURA, i))
    tela.blit(hb, (0, metade - 30))
    # Fundo abaixo do horizonte
    pygame.draw.rect(tela, (8, 8, 14), (0, metade, LARGURA, ALTURA_JOGO - metade))


def _add_box(rend, cx, cz, y0, y1, meia_x, meia_z, cor):
    x0, x1 = cx - meia_x, cx + meia_x
    z0, z1 = cz - meia_z, cz + meia_z
    esc = tuple(int(c * 0.55) for c in cor)
    med = tuple(int(c * 0.78) for c in cor)
    cla = tuple(min(255, int(c * 1.08)) for c in cor)
    rend.poligono([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], cor)
    rend.poligono([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], esc)
    rend.poligono([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], med)
    rend.poligono([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], med)
    rend.poligono([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], cla)


def _desenhar_arena_3d(rend, tempo):
    A = ARENA
    # Chão xadrez
    tile = 3.0
    n = int(A / tile)
    for iz in range(-n, n):
        for ix in range(-n, n):
            x0 = ix * tile
            z0 = iz * tile
            claro = (ix + iz) % 2 == 0
            cor = (34, 34, 48) if claro else (24, 24, 36)
            rend.poligono([(x0, 0, z0), (x0 + tile, 0, z0),
                           (x0 + tile, 0, z0 + tile), (x0, 0, z0 + tile)], cor)
    # Grade sobre o chão
    pulso = 0.5 + 0.5 * math.sin(tempo / 500)
    cor_grid = (int(50 + 40 * pulso), int(70 + 60 * pulso), int(110 + 80 * pulso))
    x = -A
    while x <= A + 0.01:
        rend.linha((x, 0.02, -A), (x, 0.02, A), cor_grid, 1)
        rend.linha((-A, 0.02, x), (A, 0.02, x), cor_grid, 1)
        x += tile
    # Pad central luminoso
    ppulso = 0.5 + 0.5 * math.sin(tempo / 350)
    rend.blob((0, 0.05, 0), 2.2, (60, 200, 255), int(30 + 30 * ppulso))
    for (a, b) in [((-1.6, 0.06, -1.6), (1.6, 0.06, -1.6)),
                   ((-1.6, 0.06, 1.6), (1.6, 0.06, 1.6)),
                   ((-1.6, 0.06, -1.6), (-1.6, 0.06, 1.6)),
                   ((1.6, 0.06, -1.6), (1.6, 0.06, 1.6))]:
        rend.linha(a, b, (90, 220, 255), 2)
    # Paredes
    cor_p = (46, 42, 76)
    cor_p2 = (36, 32, 60)
    rend.poligono([(-A, 0, -A), (A, 0, -A), (A, PAREDE_H, -A), (-A, PAREDE_H, -A)], cor_p)
    rend.poligono([(-A, 0, A), (A, 0, A), (A, PAREDE_H, A), (-A, PAREDE_H, A)], cor_p2)
    rend.poligono([(-A, 0, -A), (-A, 0, A), (-A, PAREDE_H, A), (-A, PAREDE_H, -A)], cor_p2)
    rend.poligono([(A, 0, -A), (A, 0, A), (A, PAREDE_H, A), (A, PAREDE_H, -A)], cor_p)
    # Faixa de neon no topo das paredes
    neon = (90, 210, 255)
    for (a, b) in [((-A, PAREDE_H, -A), (A, PAREDE_H, -A)),
                   ((-A, PAREDE_H, A), (A, PAREDE_H, A)),
                   ((-A, PAREDE_H, -A), (-A, PAREDE_H, A)),
                   ((A, PAREDE_H, -A), (A, PAREDE_H, A))]:
        rend.linha(a, b, neon, 3)
    # Pilares nos cantos, com neon
    for (px, pz) in [(-A + 0.6, -A + 0.6), (A - 0.6, -A + 0.6),
                     (-A + 0.6, A - 0.6), (A - 0.6, A - 0.6)]:
        _add_box(rend, px, pz, 0.0, PAREDE_H, 0.5, 0.5, (30, 28, 52))
        rend.linha((px, 0.1, pz), (px, PAREDE_H, pz), (70, 200, 255), 1)


def _desenhar_oponente(rend, cam, ox, oz, cor, tempo, hp_frac):
    """Boneco 3D do oponente: sombra + aura + pernas + corpo + cabeça + visor."""
    bob = math.sin(tempo / 220) * 0.05
    # Sombra no chão
    rend.blob((ox, 0.04, oz), 0.7, (0, 0, 0), 120)
    # Aura pulsante (fica mais vermelha com pouca vida)
    apulso = 0.5 + 0.5 * math.sin(tempo / 250)
    aura_cor = (int(60 + 180 * (1 - hp_frac)), int(180 * hp_frac + 40), 200)
    rend.blob((ox, 0.06, oz), 0.85 + 0.1 * apulso, aura_cor, int(50 + 40 * apulso))
    # Pernas
    _add_box(rend, ox - 0.16, oz, 0.0 + bob, 0.55 + bob, 0.12, 0.14, tuple(int(c * 0.7) for c in cor))
    _add_box(rend, ox + 0.16, oz, 0.0 + bob, 0.55 + bob, 0.12, 0.14, tuple(int(c * 0.7) for c in cor))
    # Corpo
    _add_box(rend, ox, oz, 0.5 + bob, 1.18 + bob, 0.32, 0.22, cor)
    # Cabeça
    _add_box(rend, ox, oz, 1.18 + bob, 1.62 + bob, 0.22, 0.2,
             tuple(min(255, c + 25) for c in cor))
    # Visor brilhante virado para o jogador
    ddx = cam.x - ox
    ddz = cam.z - oz
    dd = math.hypot(ddx, ddz) or 1
    vx = ox + (ddx / dd) * 0.22
    vz = oz + (ddz / dd) * 0.22
    rend.orb((vx, 1.4 + bob, vz), 0.1, (255, 70, 60))


# ============================================================
#  ENTIDADES
# ============================================================

class TiroInimigo:
    def __init__(self, x, y, z, dx, dy, dz):
        self.x, self.y, self.z = x, y, z
        v = 9.5
        self.vx, self.vy, self.vz = dx * v, dy * v, dz * v
        self.vida = 3.0
        self.trilha = []

    def atualizar(self, dt):
        self.trilha.append((self.x, self.y, self.z))
        if len(self.trilha) > 5:
            self.trilha.pop(0)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vida -= dt
        return self.vida > 0 and abs(self.x) < ARENA and abs(self.z) < ARENA


# ============================================================
#  DESENHO 2D (intro / transição / HUD)
# ============================================================

def _desenhar_duelista_2d(tela, x, y, tam, cor, nome, fonte, olhando_dir):
    esc = tuple(max(0, c - 60) for c in cor)
    bri = tuple(min(255, c + 80) for c in cor)
    pygame.draw.rect(tela, (12, 10, 18), (x + 4, y + 4, tam, tam), 0, 6)
    pygame.draw.rect(tela, esc, (x, y, tam, tam), 0, 8)
    pygame.draw.rect(tela, cor, (x + 3, y + 3, tam - 6, tam - 6), 0, 6)
    pygame.draw.rect(tela, bri, (x + 6, y + 6, 10, 10), 0, 3)
    ex = x + (tam - 14 if olhando_dir else 6)
    pygame.draw.rect(tela, (20, 20, 30), (ex, y + tam // 2 - 4, 8, 8), 0, 2)
    ns = fonte.render(nome, True, BRANCO)
    tela.blit(ns, (x + tam // 2 - ns.get_width() // 2, y - 24))


def _desenhar_intro_2d(tela, gradiente, tempo_no_estado, nome_l, cor_l, nome_o, cor_o,
                       fonte_grande, fonte_media, fonte_peq):
    tela.blit(gradiente, (0, 0))
    pygame.draw.rect(tela, (18, 16, 26), (0, ALTURA_JOGO - 120, LARGURA, 120))
    pygame.draw.line(tela, (60, 55, 90), (0, ALTURA_JOGO - 120), (LARGURA, ALTURA_JOGO - 120), 2)
    prog = min(1.0, tempo_no_estado / 1000)
    tam = 60
    y = ALTURA_JOGO - 120 - tam
    lx = int(120 + prog * 180)
    ox = int(LARGURA - 120 - tam - prog * 180)
    _desenhar_duelista_2d(tela, lx, y, tam, cor_l, nome_l, fonte_peq, True)
    _desenhar_duelista_2d(tela, ox, y, tam, cor_o, nome_o, fonte_peq, False)
    titulo = fonte_grande.render("DUELO", True, (200, 220, 255))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 90))
    vs = fonte_media.render(f"{nome_l}   VS   {nome_o}", True, (255, 220, 120))
    tela.blit(vs, (LARGURA // 2 - vs.get_width() // 2, 170))
    if tempo_no_estado > 1200:
        sub = fonte_peq.render("Preparando arena...", True, (150, 160, 190))
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, ALTURA_JOGO // 2))


def _desenhar_transicao(tela, t, fonte_grande):
    tela.fill((0, 0, 0))
    cx, cy = LARGURA // 2, ALTURA_JOGO // 2
    for i in range(6):
        fase = (t * 2.2 - i * 0.14)
        if fase <= 0:
            continue
        raio = int(fase * max(LARGURA, ALTURA_JOGO))
        alpha = max(0, 200 - int(fase * 200))
        if alpha <= 0 or raio <= 0:
            continue
        s = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 200, 255, alpha), (cx, cy), raio, 6)
        tela.blit(s, (0, 0))
    random.seed(int(t * 120))
    for _ in range(12):
        gy = random.randint(0, ALTURA_JOGO)
        gh = random.randint(2, 10)
        gx = random.randint(-40, 40)
        col = random.choice([(90, 220, 255), (255, 90, 160), (255, 255, 255)])
        s = pygame.Surface((LARGURA, gh), pygame.SRCALPHA)
        s.fill((*col, 90))
        tela.blit(s, (gx, gy))
    for i in range(24):
        ang = (i / 24) * 2 * math.pi
        r0 = 60 + t * 120
        r1 = 60 + t * 700
        x0 = cx + math.cos(ang) * r0
        y0 = cy + math.sin(ang) * r0
        x1 = cx + math.cos(ang) * r1
        y1 = cy + math.sin(ang) * r1
        c = int(80 + 120 * t)
        pygame.draw.line(tela, (c, min(255, c + 80), 255), (x0, y0), (x1, y1), 1)
    if t > 0.25:
        txt = fonte_grande.render("MODO 3D", True, (200, 240, 255))
        txt.set_alpha(min(255, int((t - 0.25) * 400)))
        tela.blit(txt, (cx - txt.get_width() // 2, cy - 120))
    if t > 0.7:
        flash = pygame.Surface((LARGURA, ALTURA_JOGO))
        flash.fill((255, 255, 255))
        flash.set_alpha(int((t - 0.7) / 0.3 * 255))
        tela.blit(flash, (0, 0))


def _desenhar_arma_viewmodel(tela, tempo, atirando_ate):
    """Blaster sci-fi em primeira pessoa, com muzzle flash ao atirar."""
    bx = LARGURA - 340
    by = ALTURA_JOGO + 10
    recuo = 16 if pygame.time.get_ticks() < atirando_ate else 0
    bob = int(math.sin(tempo / 260) * 4)
    by += bob + recuo

    # Coronha / corpo (perspectiva subindo da base)
    corpo = [(bx, by), (bx + 210, by - 120), (bx + 320, by - 150),
             (bx + 330, by - 118), (bx + 150, by)]
    pygame.draw.polygon(tela, (34, 36, 46), corpo)
    pygame.draw.polygon(tela, (18, 20, 28), corpo, 3)
    # Cano
    cano = [(bx + 200, by - 118), (bx + 340, by - 150),
            (bx + 360, by - 140), (bx + 220, by - 104)]
    pygame.draw.polygon(tela, (52, 56, 70), cano)
    # Linha de energia brilhante no cano
    ecor = (70, 210, 255)
    pygame.draw.line(tela, ecor, (bx + 210, by - 112), (bx + 350, by - 146), 3)
    # Núcleo de energia pulsante
    pulso = 4 + int(3 * math.sin(tempo / 120))
    core = (bx + 150, by - 70)
    gl = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(gl, (70, 210, 255, 120), (30, 30), 26)
    tela.blit(gl, (core[0] - 30, core[1] - 30))
    pygame.draw.circle(tela, (120, 230, 255), core, pulso + 5)
    pygame.draw.circle(tela, (255, 255, 255), core, pulso)
    # Boca do cano
    boca = (bx + 352, by - 148)
    pygame.draw.circle(tela, (30, 32, 40), boca, 8)
    pygame.draw.circle(tela, (70, 200, 255), boca, 4)
    # Muzzle flash
    if pygame.time.get_ticks() < atirando_ate:
        fl = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(fl, (255, 240, 160, 200), (60, 60), 34)
        pygame.draw.circle(fl, (255, 255, 255, 230), (60, 60), 16)
        tela.blit(fl, (boca[0] - 60, boca[1] - 60))


def _desenhar_hud_3d(tela, hp_jog, hp_opo, nome_o, fonte_peq, mira_hit):
    cx, cy = LARGURA // 2, ALTURA_JOGO // 2
    cor_mira = (255, 90, 90) if mira_hit else (200, 240, 255)
    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        pygame.draw.line(tela, cor_mira, (cx + dx * 4, cy + dy * 4),
                         (cx + dx * 13, cy + dy * 13), 2)
    pygame.draw.circle(tela, cor_mira, (cx, cy), 2)

    def barra(x, y, w, hp, cor, label, lc):
        pygame.draw.rect(tela, (24, 24, 34), (x - 3, y - 3, w + 6, 22), 0, 6)
        frac = max(0, hp / HP_MAX)
        pygame.draw.rect(tela, cor, (x, y, int(w * frac), 16), 0, 4)
        pygame.draw.rect(tela, (130, 140, 165), (x, y, w, 16), 1, 4)
        ls = fonte_peq.render(label, True, lc)
        tela.blit(ls, (x, y - 22))

    barra(24, ALTURA_JOGO - 42, 240, hp_jog, (80, 220, 120), "VOCE", (200, 255, 210))
    barra(LARGURA - 264, 34, 240, hp_opo, (230, 90, 90), nome_o, (255, 200, 200))


# ============================================================
#  IA DO OPONENTE
# ============================================================

def _oponente_ai(op, cam, dt, tempo, tiros_inimigo):
    px, pz = cam.x, cam.z
    dx = px - op['x']
    dz = pz - op['z']
    dist = math.hypot(dx, dz) or 1
    dirx, dirz = dx / dist, dz / dist
    if tempo > op['strafe_t']:
        op['strafe_t'] = tempo + random.randint(700, 1400)
        op['strafe_dir'] *= -1
    sx, sz = -dirz * op['strafe_dir'], dirx * op['strafe_dir']
    mx, mz = sx, sz
    ideal = 6.0
    if dist < ideal - 1:
        mx -= dirx
        mz -= dirz
    elif dist > ideal + 1:
        mx += dirx
        mz += dirz
    mag = math.hypot(mx, mz) or 1
    vel = 3.4
    op['x'] += (mx / mag) * vel * dt
    op['z'] += (mz / mag) * vel * dt
    lim = ARENA - 0.6
    op['x'] = max(-lim, min(lim, op['x']))
    op['z'] = max(-lim, min(lim, op['z']))
    if tempo > op['next_shot']:
        op['next_shot'] = tempo + random.randint(900, 1500)
        ax = px + random.uniform(-1.2, 1.2) - op['x']
        ay = OLHO_Y - 1.3
        az = pz + random.uniform(-1.2, 1.2) - op['z']
        d = math.sqrt(ax * ax + ay * ay + az * az) or 1
        tiros_inimigo.append(TiroInimigo(op['x'], 1.3, op['z'], ax / d, ay / d, az / d))


def _raycast_oponente(cam, op):
    F, _, _ = cam.base()
    ox = op['x'] - cam.x
    oz = op['z'] - cam.z
    fx, fz = F[0], F[2]
    fmag = math.hypot(fx, fz) or 1
    fx, fz = fx / fmag, fz / fmag
    t = ox * fx + oz * fz
    if t <= 0 or t > ALCANCE_TIRO:
        return False
    d = math.hypot(ox - fx * t, oz - fz * t)
    return d <= RAIO_OPONENTE + 0.15


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def executar_minigame_duel3d(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                             cliente, nome_jogador, customizacao):
    """Executa o minigame Duelo 3D."""
    print("[DUEL3D] Minigame Duelo 3D iniciado!")
    if cliente:
        cliente.get_minigame_actions()

    fonte_grande = pygame.font.SysFont("Arial", 52, True)
    fonte_media = pygame.font.SysFont("Arial", 28, True)
    fonte_peq = pygame.font.SysFont("Arial", 15)

    cor_l = customizacao.get('cor', AZUL)
    cor_o = (230, 60, 60)
    nome_l = nome_jogador
    nome_o = "Rival"

    rend = Renderer3D(LARGURA, ALTURA_JOGO)
    cam = Camera(0.0, ARENA - 2.5, math.pi)
    oponente = {'x': 0.0, 'z': -(ARENA - 2.5),
                'strafe_t': 0, 'strafe_dir': 1, 'next_shot': 2000}
    hp_jog = HP_MAX
    hp_opo = HP_MAX
    tiros_inimigo = []
    tracers = []
    sparks = []            # (x,y,z,vida) faíscas de acerto
    hit_flash_ate = 0
    atirando_ate = 0
    resultado = None

    estrelas = []
    for _ in range(90):
        sx = random.randint(0, LARGURA)
        sy = random.randint(0, int(ALTURA_JOGO * 0.5))
        estrelas.append((sx, sy, random.randint(80, 200), random.choice([1, 1, 2])))

    estado = "INTRO_2D"
    tempo_estado = pygame.time.get_ticks()
    mouse_preso = False

    def _prender_mouse(v):
        nonlocal mouse_preso
        mouse_preso = v
        pygame.mouse.set_visible(not v)
        pygame.event.set_grab(v)
        if v:
            pygame.mouse.get_rel()

    def _sair():
        _prender_mouse(False)
        pygame.mouse.set_visible(True)

    while True:
        tempo = pygame.time.get_ticks()
        tempo_no_estado = tempo - tempo_estado
        dt = min(0.05, relogio.get_time() / 1000.0)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                _sair()
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                _sair()
                return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and estado == "DUELO_3D":
                if hp_jog > 0 and hp_opo > 0:
                    atirando_ate = tempo + 100
                    F, _, _ = cam.base()
                    p0 = (cam.x + F[0] * 0.4, cam.y - 0.12, cam.z + F[2] * 0.4)
                    p1 = (cam.x + F[0] * ALCANCE_TIRO, cam.y + F[1] * ALCANCE_TIRO,
                          cam.z + F[2] * ALCANCE_TIRO)
                    tracers.append([p0, p1, 0.08])
                    if _raycast_oponente(cam, oponente):
                        hp_opo -= 1
                        sparks.append([oponente['x'], 1.3, oponente['z'], 0.25])
                        if hp_opo <= 0:
                            resultado = 'vitoria'

        # ---- estados ----
        if estado == "INTRO_2D":
            if tempo_no_estado >= TEMPO_INTRO:
                estado = "TRANSICAO"
                tempo_estado = tempo
        elif estado == "TRANSICAO":
            if tempo_no_estado >= TEMPO_TRANSICAO:
                estado = "DUELO_3D"
                tempo_estado = tempo
                _prender_mouse(True)
        elif estado == "DUELO_3D":
            mdx, mdy = pygame.mouse.get_rel() if mouse_preso else (0, 0)
            cam.yaw += mdx * SENS                       # (corrigido: não invertido)
            cam.pitch = max(-1.3, min(1.3, cam.pitch - mdy * SENS))
            if hp_jog > 0 and hp_opo > 0:
                teclas = pygame.key.get_pressed()
                fh = cam.forward_horizontal()
                rt = cam.right()
                mvx = mvz = 0.0
                if teclas[pygame.K_w]:
                    mvx += fh[0]; mvz += fh[2]
                if teclas[pygame.K_s]:
                    mvx -= fh[0]; mvz -= fh[2]
                if teclas[pygame.K_d]:
                    mvx += rt[0]; mvz += rt[2]
                if teclas[pygame.K_a]:
                    mvx -= rt[0]; mvz -= rt[2]
                mag = math.hypot(mvx, mvz)
                if mag > 0:
                    cam.x += (mvx / mag) * VEL_JOGADOR * dt
                    cam.z += (mvz / mag) * VEL_JOGADOR * dt
                lim = ARENA - 0.5
                cam.x = max(-lim, min(lim, cam.x))
                cam.z = max(-lim, min(lim, cam.z))
                _oponente_ai(oponente, cam, dt, tempo, tiros_inimigo)
            for t in tiros_inimigo[:]:
                if not t.atualizar(dt):
                    tiros_inimigo.remove(t)
                    continue
                d = math.sqrt((t.x - cam.x) ** 2 + (t.y - cam.y) ** 2 + (t.z - cam.z) ** 2)
                if d < 0.6:
                    tiros_inimigo.remove(t)
                    hp_jog -= 1
                    hit_flash_ate = tempo + 250
                    if hp_jog <= 0:
                        resultado = 'derrota'
            for tr in tracers[:]:
                tr[2] -= dt
                if tr[2] <= 0:
                    tracers.remove(tr)
            for sp in sparks[:]:
                sp[3] -= dt
                if sp[3] <= 0:
                    sparks.remove(sp)
            if resultado and tempo_no_estado > 200:
                estado = "RESULTADO"
                tempo_estado = tempo
                _prender_mouse(False)
        elif estado == "RESULTADO":
            if tempo_no_estado >= TEMPO_RESULTADO:
                _sair()
                return None

        # ---- desenhar ----
        if estado == "INTRO_2D":
            _desenhar_intro_2d(tela, gradiente_jogo, tempo_no_estado, nome_l, cor_l,
                               nome_o, cor_o, fonte_grande, fonte_media, fonte_peq)
        elif estado == "TRANSICAO":
            _desenhar_transicao(tela, tempo_no_estado / TEMPO_TRANSICAO, fonte_grande)
        else:
            _desenhar_ceu(tela, estrelas, tempo)
            rend.iniciar(cam)
            _desenhar_arena_3d(rend, tempo)
            if hp_opo > 0:
                _desenhar_oponente(rend, cam, oponente['x'], oponente['z'],
                                   cor_o, tempo, hp_opo / HP_MAX)
            for t in tiros_inimigo:
                for k, (tx, ty, tz) in enumerate(t.trilha):
                    rend.blob((tx, ty, tz), 0.13, (255, 140, 40), 40 + k * 20)
                rend.orb((t.x, t.y, t.z), 0.19, (255, 170, 60))
            for tr in tracers:
                rend.feixe(tr[0], tr[1], (120, 230, 255))
            for sp in sparks:
                rend.orb((sp[0], sp[1], sp[2]), 0.3 * (sp[3] / 0.25), (255, 230, 150))
            rend.desenhar(tela)

            _desenhar_arma_viewmodel(tela, tempo, atirando_ate)
            mira_hit = (hp_opo > 0 and _raycast_oponente(cam, oponente))
            _desenhar_hud_3d(tela, hp_jog, hp_opo, nome_o, fonte_peq, mira_hit)

            if tempo < hit_flash_ate:
                s = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
                s.fill((200, 0, 0, int(120 * (hit_flash_ate - tempo) / 250)))
                tela.blit(s, (0, 0))
            if estado == "DUELO_3D" and tempo_no_estado < 300:
                f = pygame.Surface((LARGURA, ALTURA_JOGO))
                f.fill((255, 255, 255))
                f.set_alpha(int(255 * (1 - tempo_no_estado / 300)))
                tela.blit(f, (0, 0))
            if estado == "DUELO_3D" and tempo_no_estado < 3500:
                inst = fonte_peq.render("WASD: Mover  |  Mouse: Mirar  |  Clique: Atirar  |  ESC: Sair",
                                        True, (180, 200, 220))
                tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))
            if estado == "RESULTADO":
                ov = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 170))
                tela.blit(ov, (0, 0))
                msg, cor = ("VITORIA!", (120, 255, 140)) if resultado == 'vitoria' else ("DERROTA", (255, 100, 100))
                s = fonte_grande.render(msg, True, cor)
                tela.blit(s, (LARGURA // 2 - s.get_width() // 2, ALTURA_JOGO // 2 - 60))
                sub = fonte_peq.render("Voltando ao lobby...", True, (180, 180, 200))
                tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, ALTURA_JOGO // 2 + 20))

        present_frame()
        relogio.tick(FPS)
