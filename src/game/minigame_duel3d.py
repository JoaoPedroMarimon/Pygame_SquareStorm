#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame ARENA 3D - deathmatch em primeira pessoa numa arena 3D, com todos os
jogadores da sala + bots.

Fluxo:
  1. SETUP      : cada jogador escolhe a arma; o host escolhe quantos bots entram.
  2. INTRO      : apresentação 2D dos duelistas (estilo dos outros minigames).
  3. TRANSICAO  : efeito de transição 2D -> 3D.
  4. FIGHT      : deathmatch em 3D (respawn, frag limit e tempo).
  5. FIM        : placar final e volta ao lobby.

Modelo de rede (igual aos outros minigames): HOST-AUTORITATIVO.
  - O host simula bots, dano, mortes, respawn, placar e projéteis, e transmite
    um snapshot ~30x por segundo.
  - Cada cliente é autoritativo sobre a PRÓPRIA posição (envia x/y/z/yaw) e
    manda pedidos de tiro; o host valida e resolve o dano.
  - Efeitos visuais (rastros, impactos, explosões, kills) viajam como eventos
    no snapshot, então todo mundo vê a mesma coisa.

O motor 3D (câmera, renderizador, arena, personagens) fica em duel3d_render.py.
"""

import math
import random
import pygame

from src.config import *
from src.utils.display_manager import present_frame, convert_mouse_position
from src.network.multiplayer_utils import ordenar_humanos, sou_host
from src.game.duel3d_render import (
    ARENA, PAREDE_H, OLHO_Y, ALTURA_JOGADOR, RAIO_JOGADOR, PASSO_MAX,
    OBSTACULOS, COLISORES, SPAWNS,
    Camera, Renderer3D, gerar_ceu, desenhar_ceu, desenhar_arena,
    desenhar_personagem, altura_chao, resolver_colisao, ray_cenario,
    linha_de_visao, normalizar, ang_lerp,
)

# ============================================================
#  CONSTANTES DE JOGO
# ============================================================

HP_MAX = 100
VEL_ANDAR = 6.4
VEL_SPRINT = 9.3
CONTROLE_AR = 0.72
GRAVIDADE = 22.0
FORCA_PULO = 7.5
SENS = 0.0022

MAX_JOGADORES = 8
FRAG_LIMITE = 15
TEMPO_PARTIDA = 210000       # 3min30
RESPAWN_MS = 2600

# Tempos de estado (ms)
TEMPO_SETUP = 20000
TEMPO_INTRO = 3000
TEMPO_TRANSICAO = 1500
TEMPO_FIM = 9000

# Rede
INTERVALO_SNAPSHOT = 33      # host -> clientes (~30Hz)
INTERVALO_INPUT = 33         # cliente -> host
INTERVALO_LOADOUT = 600      # reenvio da aparência/arma durante o SETUP

HEADSHOT_MULT = 1.9
ALTURA_CABECA = 1.28         # base da cabeça, a partir dos pés (ver duel3d_render)

PALETA_CORES = [AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)]

NOMES_BOTS = ["VIPER", "ORION", "RAZOR", "NOVA", "ECHO", "TITAN", "LYNX", "ZERO"]
CORES_BOTS = [(230, 70, 70), (90, 220, 130), (240, 190, 60), (170, 110, 255),
              (60, 220, 220), (255, 140, 60), (230, 110, 190), (140, 200, 255)]


# ============================================================
#  ARMAS
# ============================================================
# tipo: 'hitscan' (raio instantâneo) ou 'projetil' (foguete simulado)
# stats: barras 0..1 mostradas na tela de seleção (dano, cadência, alcance, controle)

ARMAS = [
    {
        'id': 'pulse', 'nome': 'PULSE RIFLE', 'tipo': 'hitscan',
        'cor': (95, 220, 255), 'dano': 16, 'cd': 150, 'mag': 30, 'recarga': 1250,
        'spread': 0.013, 'spread_mov': 0.020, 'pellets': 1, 'alcance': 95,
        'auto': True, 'kick': 0.9, 'largura': 3, 'falloff': 0.0,
        'desc': 'Automatica, precisa e confiavel.',
        'stats': (0.55, 0.75, 0.80, 0.85),
    },
    {
        'id': 'shotgun', 'nome': 'DEVASTATOR', 'tipo': 'hitscan',
        'cor': (255, 165, 60), 'dano': 13, 'cd': 720, 'mag': 6, 'recarga': 1750,
        'spread': 0.072, 'spread_mov': 0.086, 'pellets': 9, 'alcance': 32,
        'auto': False, 'kick': 3.2, 'largura': 2, 'falloff': 0.65,
        'desc': '9 chumbos. Devastadora de perto.',
        'stats': (0.95, 0.30, 0.25, 0.45),
    },
    {
        'id': 'rail', 'nome': 'CYAN LANCE', 'tipo': 'hitscan',
        'cor': (140, 255, 225), 'dano': 66, 'cd': 1250, 'mag': 4, 'recarga': 1900,
        'spread': 0.0, 'spread_mov': 0.006, 'pellets': 1, 'alcance': 160,
        'auto': False, 'kick': 2.6, 'largura': 5, 'falloff': 0.0, 'perfura': True,
        'desc': 'Raio perfurante. Atravessa quem estiver na linha.',
        'stats': (1.0, 0.15, 1.0, 0.70),
    },
    {
        'id': 'vortex', 'nome': 'VORTEX', 'tipo': 'hitscan',
        'cor': (255, 215, 120), 'dano': 8, 'cd': 68, 'mag': 80, 'recarga': 2500,
        'spread': 0.030, 'spread_mov': 0.052, 'pellets': 1, 'alcance': 70,
        'auto': True, 'kick': 0.5, 'largura': 2, 'falloff': 0.35,
        'desc': 'Metralhadora rotativa. Cospe chumbo sem parar.',
        'stats': (0.40, 1.0, 0.55, 0.35),
    },
    {
        'id': 'nova', 'nome': 'NOVA LAUNCHER', 'tipo': 'projetil',
        'cor': (255, 125, 210), 'dano': 42, 'cd': 1000, 'mag': 4, 'recarga': 2100,
        'spread': 0.0, 'spread_mov': 0.004, 'pellets': 1, 'alcance': 120,
        'auto': False, 'kick': 3.0, 'largura': 3, 'falloff': 0.0,
        'vel': 30.0, 'raio_exp': 4.6, 'dano_exp': 62,
        'desc': 'Foguete de plasma com dano em area.',
        'stats': (0.90, 0.25, 0.65, 0.40),
    },
]

ARMA_POR_ID = {a['id']: i for i, a in enumerate(ARMAS)}


# ============================================================
#  SOM
# ============================================================

_SONS = {}


def _tocar(nome, volume, canal):
    """Toca um som gerado (cacheado). Silencioso se o mixer não estiver ok."""
    try:
        som = _SONS.get(nome)
        if som is None:
            from src.utils import sound as _snd
            gerador = {'tiro': _snd.gerar_som_tiro,
                       'explosao': _snd.gerar_som_explosao,
                       'dano': _snd.gerar_som_dano}[nome]
            som = gerador()
            _SONS[nome] = som
        som.set_volume(volume)
        pygame.mixer.Channel(canal).play(som)
    except Exception:
        pass


# ============================================================
#  ENTIDADES
# ============================================================

class Duelista:
    """Jogador da arena (local, remoto ou bot)."""

    def __init__(self, idx, nome, cor, is_bot=False, is_local=False):
        self.idx = idx
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_local = is_local
        self.is_remote = (not is_bot and not is_local)
        self.player_id = None
        self.ativo = True
        self.chapeu = None

        # Transformação
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.vy = 0.0
        self.no_chao = True

        # Interpolação (jogadores que vêm pela rede)
        self.alvo_x = 0.0
        self.alvo_y = 0.0
        self.alvo_z = 0.0
        self.alvo_yaw = 0.0

        # Estado de combate
        self.hp = HP_MAX
        self.vivo = True
        self.kills = 0
        self.mortes = 0
        self.arma_idx = 0
        self.respawn_seq = 0
        self.respawn_em = 0
        self.morto_por = -1
        self.pronto = False

        # Arma (simulada localmente pelo dono; no host para os bots)
        self.municao = ARMAS[0]['mag']
        self.recarregando_ate = 0
        self.ultimo_tiro = 0

        # Animação
        self.passo = 0.0
        self.vel_atual = 0.0

        # IA
        self.bot_alvo = None
        self.bot_yaw_alvo = 0.0
        self.bot_pitch_alvo = 0.0
        self.bot_strafe = 1
        self.bot_troca_strafe = 0
        self.bot_reacao_ate = 0
        self.bot_erro = (0.0, 0.0)
        self.bot_proximo_erro = 0
        self.bot_pulo_em = 0
        self.bot_destino = None
        self.bot_ultimo_visto = 0

    # ---- utilidades ----
    def arma(self):
        return ARMAS[self.arma_idx]

    def olho(self):
        return (self.x, self.y + OLHO_Y, self.z)

    def centro(self):
        return (self.x, self.y + ALTURA_JOGADOR * 0.55, self.z)

    def cabeca(self):
        return (self.x, self.y + ALTURA_CABECA, self.z)

    def direcao(self):
        cp = math.cos(self.pitch)
        return (cp * math.sin(self.yaw), math.sin(self.pitch), cp * math.cos(self.yaw))

    def pronto_para_atirar(self, tempo):
        a = self.arma()
        if tempo < self.recarregando_ate:
            return False
        if self.municao <= 0:
            return False
        return tempo - self.ultimo_tiro >= a['cd']

    def iniciar_recarga(self, tempo):
        a = self.arma()
        if self.municao >= a['mag'] or tempo < self.recarregando_ate:
            return False
        self.recarregando_ate = tempo + a['recarga']
        return True

    def atualizar_recarga(self, tempo):
        if self.recarregando_ate and tempo >= self.recarregando_ate:
            self.municao = self.arma()['mag']
            self.recarregando_ate = 0

    def aplicar_arma(self, idx):
        self.arma_idx = idx % len(ARMAS)
        self.municao = ARMAS[self.arma_idx]['mag']
        self.recarregando_ate = 0


class Foguete:
    """Projétil do NOVA LAUNCHER (simulado só no host)."""

    _proximo_id = 1

    def __init__(self, dono_idx, pos, direcao, cor):
        self.id = Foguete._proximo_id
        Foguete._proximo_id += 1
        self.dono = dono_idx
        self.x, self.y, self.z = pos
        self.dx, self.dy, self.dz = direcao
        self.cor = cor
        self.vida = 4.0


class Mundo:
    """Agrupa listas de estado/efeitos para não passar 10 parâmetros por função."""

    def __init__(self):
        self.jogadores = []
        self.foguetes = []
        self.foguetes_render = []     # (x, y, z) recebidos do host
        self.particulas = []
        self.tracers = []
        self.explosoes = []
        self.dano_flutuante = []
        self.killfeed = []
        self.fx_pendentes = []
        # Feedback local
        self.hitmarker_ate = 0
        self.hitmarker_kill = False
        self.flash_dano_ate = 0
        self.indicadores_dano = []    # {'ang': rad, 'ate': ms}
        self.shake = 0.0
        self.idx_local = 0


# ============================================================
#  EFEITOS
# ============================================================

def _particula(mundo, pos, vel, cor, vida, raio, grav=True):
    mundo.particulas.append({'p': [pos[0], pos[1], pos[2]],
                             'v': [vel[0], vel[1], vel[2]],
                             'c': cor, 'vida': vida, 'max': vida,
                             'r': raio, 'g': grav})


def _faiscas(mundo, pos, cor, n=10, forca=4.0, vida=0.4):
    for _ in range(n):
        ang = random.uniform(0, 2 * math.pi)
        el = random.uniform(-0.2, 1.0)
        v = random.uniform(0.4, 1.0) * forca
        _particula(mundo, pos,
                   (math.cos(ang) * v, el * v, math.sin(ang) * v),
                   cor, vida * random.uniform(0.6, 1.3), random.uniform(0.03, 0.08))


def _atualizar_particulas(mundo, dt):
    for p in mundo.particulas[:]:
        p['vida'] -= dt
        if p['vida'] <= 0:
            mundo.particulas.remove(p)
            continue
        if p['g']:
            p['v'][1] -= 14.0 * dt
        p['p'][0] += p['v'][0] * dt
        p['p'][1] += p['v'][1] * dt
        p['p'][2] += p['v'][2] * dt
        if p['p'][1] < 0.03:
            p['p'][1] = 0.03
            p['v'][1] = -p['v'][1] * 0.35
            p['v'][0] *= 0.6
            p['v'][2] *= 0.6


def _aplicar_fx(mundo, ev, tempo, remoto=False):
    """
    Cria os visuais de um evento. remoto=True quando o evento chegou pela rede:
    nesse caso o dono do tiro ignora o próprio rastro, porque já o desenhou
    localmente na hora de atirar (predição).
    """
    k = ev.get('k')
    if k == 'tr':
        if remoto and ev.get('o') == mundo.idx_local:
            return
        mundo.tracers.append({'a': ev['a'], 'b': ev['b'], 'c': tuple(ev['c']),
                              'ate': tempo + 90, 'lg': ev.get('w', 3)})
        # Clarão na boca da arma — só dos OUTROS: o jogador local já vê o
        # clarão do próprio viewmodel, e faíscas coladas na câmera viram borrão.
        if ev.get('o') != mundo.idx_local:
            _faiscas(mundo, ev['a'], tuple(ev['c']), 3, 1.6, 0.14)
    elif k == 'im':
        _faiscas(mundo, ev['p'], tuple(ev.get('c', (255, 220, 150))), 8, 3.2, 0.35)
    elif k == 'hit':
        cor = tuple(ev.get('c', (255, 90, 90)))
        _faiscas(mundo, ev['p'], cor, 9, 4.0, 0.35)
        if ev.get('o') == mundo.idx_local:
            mundo.hitmarker_ate = tempo + 160
            mundo.hitmarker_kill = False
            mundo.dano_flutuante.append({'p': list(ev['p']), 'v': int(ev.get('d', 0)),
                                         'ate': tempo + 850, 'hs': bool(ev.get('hs'))})
        if ev.get('v') == mundo.idx_local:
            mundo.flash_dano_ate = tempo + 260
            mundo.shake = min(9.0, mundo.shake + 2.5)
            mundo.indicadores_dano.append({'ang': ev.get('a', 0.0), 'ate': tempo + 1100})
            _tocar('dano', 0.20, 3)
    elif k == 'ex':
        mundo.explosoes.append({'p': ev['p'], 'r': ev.get('r', 4.0),
                                'ini': tempo, 'ate': tempo + 420})
        for _ in range(26):
            ang = random.uniform(0, 2 * math.pi)
            el = random.uniform(-0.3, 1.1)
            v = random.uniform(3.0, 11.0)
            _particula(mundo, ev['p'],
                       (math.cos(ang) * v, el * v, math.sin(ang) * v),
                       random.choice([(255, 150, 60), (255, 90, 40), (255, 220, 130)]),
                       random.uniform(0.4, 0.9), random.uniform(0.06, 0.16))
        _tocar('explosao', 0.22, 2)
    elif k == 'mz':
        _faiscas(mundo, ev['p'], tuple(ev.get('c', (255, 220, 150))), 4, 2.0, 0.16)
    elif k == 'sp':
        for _ in range(20):
            ang = random.uniform(0, 2 * math.pi)
            _particula(mundo, (ev['p'][0], ev['p'][1] + 0.9, ev['p'][2]),
                       (math.cos(ang) * 2.4, random.uniform(1.0, 4.0), math.sin(ang) * 2.4),
                       (120, 230, 255), 0.6, 0.07, grav=False)
    elif k == 'kill':
        ia = ev.get('a', -1)
        iv = ev.get('v', -1)
        n = len(mundo.jogadores)
        alg = mundo.jogadores[ia] if 0 <= ia < n else None
        vit = mundo.jogadores[iv] if 0 <= iv < n else None
        mundo.killfeed.append({
            'a': alg.nome if alg else "ARENA",
            'v': vit.nome if vit else "?",
            'ca': alg.cor if alg else (180, 180, 190),
            'cv': vit.cor if vit else (180, 180, 190),
            'w': ev.get('w', 0),
            'ate': tempo + 5000,
        })
        if ia == mundo.idx_local:
            mundo.hitmarker_ate = tempo + 420
            mundo.hitmarker_kill = True
        if iv == mundo.idx_local:
            mundo.shake = 10.0


def _emitir(mundo, ev, tempo, rede=True):
    """Cria o efeito local e (no host) enfileira para a rede."""
    _aplicar_fx(mundo, ev, tempo, remoto=False)
    if rede:
        mundo.fx_pendentes.append(ev)


# ============================================================
#  FÍSICA
# ============================================================

def _fisica(p, mov_x, mov_z, vel, dt, pular):
    """Movimento horizontal com colisão + gravidade/pulo. Atualiza p."""
    if pular and p.no_chao:
        p.vy = FORCA_PULO
        p.no_chao = False

    fator = 1.0 if p.no_chao else CONTROLE_AR
    nx = p.x + mov_x * vel * dt * fator
    nz = p.z + mov_z * vel * dt * fator
    nx, nz = resolver_colisao(nx, nz, p.y)
    dist = math.hypot(nx - p.x, nz - p.z)
    p.x, p.z = nx, nz
    p.vel_atual = dist / max(dt, 0.001)
    p.passo += p.vel_atual * dt * 2.4

    y_ant = p.y
    p.vy -= GRAVIDADE * dt
    p.y += p.vy * dt
    chao = altura_chao(p.x, p.z, y_ant)
    if p.y <= chao:
        p.y = chao
        p.vy = 0.0
        p.no_chao = True
    else:
        p.no_chao = False
    if p.y < 0.0:
        p.y = 0.0
        p.vy = 0.0
        p.no_chao = True


def _spawn_livre(jogadores, quem, rng):
    """Escolhe o spawn mais distante dos inimigos vivos."""
    melhor = None
    melhor_score = -1e9
    ordem = list(range(len(SPAWNS)))
    rng.shuffle(ordem)
    for i in ordem:
        sx, sz, syaw = SPAWNS[i]
        score = 0.0
        for j in jogadores:
            if j is quem or not j.ativo or not j.vivo:
                continue
            score += math.hypot(j.x - sx, j.z - sz)
        if score > melhor_score:
            melhor_score = score
            melhor = (sx, sz, syaw)
    return melhor if melhor else (SPAWNS[0][0], SPAWNS[0][1], SPAWNS[0][2])


def _nascer(p, jogadores, rng, tempo):
    sx, sz, syaw = _spawn_livre(jogadores, p, rng)
    p.x, p.z = sx, sz
    p.y = 0.0
    p.vy = 0.0
    p.no_chao = True
    p.yaw = syaw
    p.pitch = 0.0
    p.hp = HP_MAX
    p.vivo = True
    p.municao = p.arma()['mag']
    p.recarregando_ate = 0
    p.ultimo_tiro = 0
    p.respawn_seq += 1
    p.alvo_x, p.alvo_y, p.alvo_z, p.alvo_yaw = p.x, p.y, p.z, p.yaw
    p.bot_reacao_ate = tempo + rng.randint(200, 500)
    return p


# ============================================================
#  COMBATE (só roda no host)
# ============================================================

def _ray_jogador(o, d, alvo, alcance):
    """Interseção raio x cilindro do jogador. Retorna (t, headshot) ou None."""
    ox = o[0] - alvo.x
    oz = o[2] - alvo.z
    a = d[0] * d[0] + d[2] * d[2]
    if a < 1e-9:
        return None
    b = 2.0 * (ox * d[0] + oz * d[2])
    c = ox * ox + oz * oz - (RAIO_JOGADOR + 0.12) ** 2
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    raiz = math.sqrt(disc)
    t = (-b - raiz) / (2 * a)
    if t < 0.05:
        t = (-b + raiz) / (2 * a)
        if t < 0.05:
            return None
    if t > alcance:
        return None
    y = o[1] + d[1] * t
    pes = alvo.y
    if y < pes or y > pes + ALTURA_JOGADOR:
        return None
    return (t, y >= pes + ALTURA_CABECA - 0.06)


def _raycast(mundo, origem, direcao, atirador, alcance, perfura=False):
    """
    Dispara um raio. Retorna (ponto_final, lista_de_acertos).
    Cada acerto = (jogador, distancia, headshot). Com perfura=True atravessa
    jogadores (mas não o cenário).
    """
    t_cenario = ray_cenario(origem, direcao, alcance)
    acertos = []
    for j in mundo.jogadores:
        if j is atirador or not j.ativo or not j.vivo:
            continue
        r = _ray_jogador(origem, direcao, j, alcance)
        if r and r[0] < t_cenario:
            acertos.append((j, r[0], r[1]))
    acertos.sort(key=lambda h: h[1])
    if not perfura:
        acertos = acertos[:1]
    fim = t_cenario if (perfura or not acertos) else acertos[0][1]
    ponto = (origem[0] + direcao[0] * fim,
             origem[1] + direcao[1] * fim,
             origem[2] + direcao[2] * fim)
    return ponto, acertos


def _aplicar_dano(mundo, alvo, dano, atacante, tempo, ponto, headshot=False,
                  arma_idx=0, rng=None):
    if not alvo.vivo or dano <= 0:
        return
    alvo.hp -= dano
    ang = math.atan2(atacante.x - alvo.x, atacante.z - alvo.z) if atacante else 0.0
    _emitir(mundo, {'k': 'hit', 'p': [round(ponto[0], 2), round(ponto[1], 2),
                                      round(ponto[2], 2)],
                    'c': list(alvo.cor), 'o': atacante.idx if atacante else -1,
                    'v': alvo.idx, 'd': int(dano), 'hs': bool(headshot),
                    'a': round(ang, 3)}, tempo)
    if alvo.hp <= 0:
        alvo.hp = 0
        alvo.vivo = False
        alvo.mortes += 1
        alvo.morto_por = atacante.idx if atacante else -1
        alvo.respawn_em = tempo + RESPAWN_MS
        if atacante and atacante is not alvo:
            atacante.kills += 1
        _emitir(mundo, {'k': 'ex', 'p': [round(alvo.x, 2), round(alvo.y + 0.9, 2),
                                         round(alvo.z, 2)], 'r': 1.8}, tempo)
        _emitir(mundo, {'k': 'kill', 'a': atacante.idx if atacante else -1,
                        'v': alvo.idx, 'w': arma_idx}, tempo)


def _explodir(mundo, pos, raio, dano_max, dono, tempo, arma_idx):
    _emitir(mundo, {'k': 'ex', 'p': [round(pos[0], 2), round(pos[1], 2), round(pos[2], 2)],
                    'r': raio}, tempo)
    for j in mundo.jogadores:
        if not j.ativo or not j.vivo:
            continue
        alvo = j.centro()
        d = math.sqrt((alvo[0] - pos[0]) ** 2 + (alvo[1] - pos[1]) ** 2 +
                      (alvo[2] - pos[2]) ** 2)
        if d > raio:
            continue
        if not linha_de_visao(pos, alvo):
            continue
        frac = 1.0 - (d / raio) ** 1.4
        dano = dano_max * max(0.15, frac)
        if j is dono:
            dano *= 0.45          # dano em si mesmo machuca, mas não é suicídio garantido
        _aplicar_dano(mundo, j, int(dano), dono, tempo, alvo, False, arma_idx)


def _dir_com_spread(direcao, espalha, rng):
    """Desvia a direção dentro de um cone (dispersão da arma)."""
    if espalha <= 0:
        return direcao
    ang = rng.uniform(0, 2 * math.pi)
    raio = espalha * math.sqrt(rng.random())
    lado = normalizar((direcao[2], 0.0, -direcao[0]))
    cima = (lado[1] * direcao[2] - lado[2] * direcao[1],
            lado[2] * direcao[0] - lado[0] * direcao[2],
            lado[0] * direcao[1] - lado[1] * direcao[0])
    ca = math.cos(ang) * raio
    sa = math.sin(ang) * raio
    return normalizar((direcao[0] + lado[0] * ca + cima[0] * sa,
                       direcao[1] + lado[1] * ca + cima[1] * sa,
                       direcao[2] + lado[2] * ca + cima[2] * sa))


def _origem_tiro(origem, direcao):
    """Ponto de onde o raio de fato sai (um pouco à frente do olho)."""
    return (origem[0] + direcao[0] * 0.45,
            origem[1] + direcao[1] * 0.45 - 0.05,
            origem[2] + direcao[2] * 0.45)


def _boca_arma(origem, direcao):
    """
    Ponto VISUAL de saída do tiro. Como no DOOM a arma fica CENTRALIZADA, o
    rastro nasce à frente e um pouco abaixo do olho (na boca do cano), sem
    desvio lateral. O raio em si continua saindo do olho — a mira não mente.
    """
    return (origem[0] + direcao[0] * 1.0,
            origem[1] + direcao[1] * 1.0 - 0.20,
            origem[2] + direcao[2] * 1.0)


def _tracers_locais(mundo, atirador, origem, direcao, tempo, rng):
    """
    Predição visual do cliente: desenha os rastros do próprio tiro na hora,
    sem esperar o host. O dano continua sendo decidido pelo host.
    """
    arma = atirador.arma()
    if arma['tipo'] == 'projetil':
        return
    espalha = arma['spread_mov'] if atirador.vel_atual > 1.0 else arma['spread']
    base = _origem_tiro(origem, direcao)
    visual = _boca_arma(origem, direcao)
    for _ in range(arma['pellets']):
        d = _dir_com_spread(direcao, espalha, rng)
        ponto, acertos = _raycast(mundo, base, d, atirador, arma['alcance'],
                                  arma.get('perfura', False))
        mundo.tracers.append({'a': list(visual), 'b': list(ponto), 'c': arma['cor'],
                              'ate': tempo + 90, 'lg': arma['largura']})
        if not acertos:
            _faiscas(mundo, ponto, arma['cor'], 6, 3.0, 0.3)


def _disparar(mundo, atirador, origem, direcao, tempo, rng):
    """Resolve um disparo no host (hitscan ou projétil)."""
    arma = atirador.arma()
    cor = arma['cor']
    atirador.ultimo_tiro = tempo
    if atirador.municao > 0:
        atirador.municao -= 1

    if arma['tipo'] == 'projetil':
        pos = (origem[0] + direcao[0] * 0.6, origem[1] + direcao[1] * 0.6 - 0.1,
               origem[2] + direcao[2] * 0.6)
        mundo.foguetes.append(Foguete(atirador.idx, pos, direcao, cor))
        _emitir(mundo, {'k': 'mz', 'p': [round(pos[0], 2), round(pos[1], 2),
                                         round(pos[2], 2)], 'c': list(cor)}, tempo)
        return

    movendo = atirador.vel_atual > 1.0
    espalha = arma['spread_mov'] if movendo else arma['spread']
    perfura = arma.get('perfura', False)
    base = _origem_tiro(origem, direcao)
    visual = _boca_arma(origem, direcao)

    for _ in range(arma['pellets']):
        d = _dir_com_spread(direcao, espalha, rng)
        ponto, acertos = _raycast(mundo, base, d, atirador, arma['alcance'], perfura)
        _emitir(mundo, {'k': 'tr',
                        'a': [round(visual[0], 2), round(visual[1], 2), round(visual[2], 2)],
                        'b': [round(ponto[0], 2), round(ponto[1], 2), round(ponto[2], 2)],
                        'c': list(cor), 'w': arma['largura'], 'o': atirador.idx}, tempo)
        if not acertos:
            _emitir(mundo, {'k': 'im', 'p': [round(ponto[0], 2), round(ponto[1], 2),
                                             round(ponto[2], 2)], 'c': list(cor)}, tempo)
            continue
        for (alvo, dist, hs) in acertos:
            dano = arma['dano']
            if arma['falloff'] > 0:
                queda = min(1.0, dist / arma['alcance'])
                dano *= (1.0 - arma['falloff'] * queda)
            if hs:
                dano *= HEADSHOT_MULT
            ponto_hit = (base[0] + d[0] * dist, base[1] + d[1] * dist, base[2] + d[2] * dist)
            _aplicar_dano(mundo, alvo, int(round(dano)), atirador, tempo, ponto_hit,
                          hs, atirador.arma_idx, rng)


def _atualizar_foguetes(mundo, dt, tempo, rng):
    for f in mundo.foguetes[:]:
        arma = ARMAS[ARMA_POR_ID['nova']]
        passo = arma['vel'] * dt
        origem = (f.x, f.y, f.z)
        d = (f.dx, f.dy, f.dz)
        dono = mundo.jogadores[f.dono] if 0 <= f.dono < len(mundo.jogadores) else None
        t_cen = ray_cenario(origem, d, passo + 0.35)
        alvo_j = None
        t_j = passo + 0.35
        for j in mundo.jogadores:
            if not j.ativo or not j.vivo or j is dono:
                continue
            r = _ray_jogador(origem, d, j, passo + 0.35)
            if r and r[0] < t_j:
                t_j = r[0]
                alvo_j = j
        if alvo_j is not None and t_j <= t_cen:
            ponto = (f.x + d[0] * t_j, f.y + d[1] * t_j, f.z + d[2] * t_j)
            _aplicar_dano(mundo, alvo_j, arma['dano'], dono, tempo, ponto, False,
                          ARMA_POR_ID['nova'])
            _explodir(mundo, ponto, arma['raio_exp'], arma['dano_exp'], dono, tempo,
                      ARMA_POR_ID['nova'])
            mundo.foguetes.remove(f)
            continue
        if t_cen <= passo:
            ponto = (f.x + d[0] * t_cen, f.y + d[1] * t_cen, f.z + d[2] * t_cen)
            _explodir(mundo, ponto, arma['raio_exp'], arma['dano_exp'], dono, tempo,
                      ARMA_POR_ID['nova'])
            mundo.foguetes.remove(f)
            continue
        f.x += d[0] * passo
        f.y += d[1] * passo
        f.z += d[2] * passo
        f.vida -= dt
        if f.vida <= 0:
            _explodir(mundo, (f.x, f.y, f.z), arma['raio_exp'], arma['dano_exp'],
                      dono, tempo, ARMA_POR_ID['nova'])
            mundo.foguetes.remove(f)


# ============================================================
#  IA DOS BOTS
# ============================================================

BOT_DIST_IDEAL = {'pulse': 14.0, 'shotgun': 5.5, 'rail': 22.0,
                  'vortex': 11.0, 'nova': 15.0}


def _bot_pensar(bot, mundo, dt, tempo, rng):
    """
    IA do bot: escolhe alvo visível, manobra mantendo a distância ideal da arma,
    desvia de obstáculos, mira com erro humano e atira quando está apontado.
    """
    olho = bot.olho()

    # ---- alvo: o inimigo visível mais "vantajoso" (perto e ferido) ----
    alvo = None
    melhor = 1e9
    for j in mundo.jogadores:
        if j is bot or not j.ativo or not j.vivo:
            continue
        d = math.hypot(j.x - bot.x, j.z - bot.z)
        if d > 60:
            continue
        if not linha_de_visao(olho, j.centro()):
            d += 45          # ainda considera, mas prefere quem está à vista
        score = d + j.hp * 0.12
        if score < melhor:
            melhor = score
            alvo = j
    bot.bot_alvo = alvo

    mov_x = mov_z = 0.0
    correr = False
    pular = False
    ideal = BOT_DIST_IDEAL.get(bot.arma()['id'], 12.0)

    if alvo is not None:
        dx = alvo.x - bot.x
        dz = alvo.z - bot.z
        dist = math.hypot(dx, dz) or 0.001
        dirx, dirz = dx / dist, dz / dist
        visivel = linha_de_visao(olho, alvo.centro())

        if tempo > bot.bot_troca_strafe:
            bot.bot_troca_strafe = tempo + rng.randint(700, 1600)
            bot.bot_strafe = -bot.bot_strafe

        # Orbita o alvo
        mov_x = -dirz * bot.bot_strafe
        mov_z = dirx * bot.bot_strafe

        if not visivel:
            # Sem visão: avança para reabrir o ângulo
            mov_x += dirx * 1.6
            mov_z += dirz * 1.6
            correr = True
        elif dist > ideal + 3.0:
            mov_x += dirx * 1.2
            mov_z += dirz * 1.2
            correr = dist > ideal + 9.0
        elif dist < ideal - 2.5:
            mov_x -= dirx * 1.1
            mov_z -= dirz * 1.1

        # Recua e pula quando está ferido (dá trabalho de acertar)
        if bot.hp < 40:
            mov_x -= dirx * 0.7
            mov_z -= dirz * 0.7
            if tempo > bot.bot_pulo_em and bot.no_chao:
                bot.bot_pulo_em = tempo + rng.randint(900, 1800)
                pular = True
        elif visivel and dist < 18 and tempo > bot.bot_pulo_em and bot.no_chao:
            bot.bot_pulo_em = tempo + rng.randint(1800, 4200)
            pular = True

        # ---- mira ----
        alvo_pt = alvo.cabeca() if rng.random() < 0.35 else alvo.centro()
        if bot.arma()['tipo'] == 'projetil':
            # Lidera o alvo pela velocidade do foguete
            t_voo = dist / ARMAS[ARMA_POR_ID['nova']]['vel']
            avx = math.sin(alvo.yaw) * alvo.vel_atual * 0.4
            avz = math.cos(alvo.yaw) * alvo.vel_atual * 0.4
            alvo_pt = (alvo_pt[0] + avx * t_voo, alvo_pt[1], alvo_pt[2] + avz * t_voo)

        adx = alvo_pt[0] - olho[0]
        ady = alvo_pt[1] - olho[1]
        adz = alvo_pt[2] - olho[2]
        plano = math.hypot(adx, adz) or 0.001
        bot.bot_yaw_alvo = math.atan2(adx, adz)
        bot.bot_pitch_alvo = math.atan2(ady, plano)

        # Erro de mira que muda de tempos em tempos (dá "personalidade")
        if tempo > bot.bot_proximo_erro:
            bot.bot_proximo_erro = tempo + rng.randint(280, 700)
            amp = 0.035 + min(0.06, dist / 900.0)
            bot.bot_erro = (rng.uniform(-amp, amp), rng.uniform(-amp * 0.6, amp * 0.6))

        # Vira a cabeça suavemente (não gira instantâneo como um aimbot)
        vel_giro = 5.2 * dt
        bot.yaw = ang_lerp(bot.yaw, bot.bot_yaw_alvo + bot.bot_erro[0], min(1.0, vel_giro))
        bot.pitch += (bot.bot_pitch_alvo + bot.bot_erro[1] - bot.pitch) * min(1.0, vel_giro)
        bot.pitch = max(-1.2, min(1.2, bot.pitch))

        # ---- atirar ----
        bot.atualizar_recarga(tempo)
        if bot.municao <= 0:
            bot.iniciar_recarga(tempo)
        elif visivel and tempo >= bot.bot_reacao_ate:
            erro_ang = abs((bot.bot_yaw_alvo - bot.yaw + math.pi) % (2 * math.pi) - math.pi)
            limite = 0.10 if bot.arma()['id'] != 'shotgun' else 0.20
            alcance = bot.arma()['alcance'] * (0.6 if bot.arma()['id'] == 'shotgun' else 0.9)
            # Foguete de pertinho explode na própria cara: o bot segura o tiro
            minimo = 6.0 if bot.arma()['tipo'] == 'projetil' else 0.0
            if (erro_ang < limite and minimo < dist < alcance
                    and bot.pronto_para_atirar(tempo)):
                _disparar(mundo, bot, bot.olho(), bot.direcao(), tempo, rng)
    else:
        # Sem alvo: patrulha em direção a um ponto da arena
        if bot.bot_destino is None or tempo > bot.bot_ultimo_visto:
            bot.bot_ultimo_visto = tempo + rng.randint(2500, 5000)
            bot.bot_destino = (rng.uniform(-ARENA * 0.8, ARENA * 0.8),
                               rng.uniform(-ARENA * 0.8, ARENA * 0.8))
        dx = bot.bot_destino[0] - bot.x
        dz = bot.bot_destino[1] - bot.z
        d = math.hypot(dx, dz)
        if d < 2.0:
            bot.bot_destino = None
        else:
            mov_x, mov_z = dx / d, dz / d
            correr = True
            bot.yaw = ang_lerp(bot.yaw, math.atan2(dx, dz), min(1.0, 3.5 * dt))
            bot.pitch *= 0.9
        bot.atualizar_recarga(tempo)
        bot.iniciar_recarga(tempo)

    # ---- desvio de obstáculos (sonar simples à frente) ----
    frente = (math.sin(bot.yaw), 0.0, math.cos(bot.yaw))
    pos_teste = (bot.x, bot.y + 0.9, bot.z)
    mag = math.hypot(mov_x, mov_z)
    if mag > 0.01:
        dir_mov = (mov_x / mag, 0.0, mov_z / mag)
        livre = ray_cenario(pos_teste, dir_mov, 2.6)
        if livre < 2.4:
            # Contorna: escolhe o lado com mais espaço
            esq = ray_cenario(pos_teste, (-dir_mov[2], 0.0, dir_mov[0]), 3.5)
            dirt = ray_cenario(pos_teste, (dir_mov[2], 0.0, -dir_mov[0]), 3.5)
            lado = 1 if dirt >= esq else -1
            mov_x = -dir_mov[2] * lado
            mov_z = dir_mov[0] * lado
            if livre < 1.2 and bot.no_chao and tempo > bot.bot_pulo_em:
                bot.bot_pulo_em = tempo + 1200
                pular = True
    del frente

    mag = math.hypot(mov_x, mov_z)
    if mag > 0.01:
        mov_x /= mag
        mov_z /= mag
    else:
        mov_x = mov_z = 0.0
    vel = VEL_SPRINT if correr else VEL_ANDAR
    _fisica(bot, mov_x, mov_z, vel, dt, pular)


# ============================================================
#  VIEWMODEL DAS ARMAS (2D, primeira pessoa)
# ============================================================

# ============================================================
#  VIEWMODEL ESTILO DOOM
# ============================================================
# O DOOM desenha a arma CENTRALIZADA na base da tela, vista POR TRÁS: o cano
# aponta para longe do jogador e some no fundo (encurtado pela perspectiva), com
# as duas mãos enluvadas segurando por baixo. Não é uma arma de perfil no canto.
#
# O balanço também é o do DOOM (p_pspr.c, A_WeaponReady):
#     sx = cos(t) * bob            -> vai e volta na horizontal
#     sy = sin(t & meio-círculo) * bob  -> só desce (por isso quica 2x mais rápido)
# Por isso _bob_doom() devolve o Y sempre positivo: a arma afunda e volta.

# Escala da arte da arma. _VM_KX alarga só na horizontal: no DOOM a arma ocupa
# cerca de um terço da largura da tela, e descrever a arte "alta e estreita"
# fica mais legível do que repetir números largos em cada bloco.
_VM_ESC = 2.0
_VM_KX = 1.95


def _bob_doom(fase, forca):
    """Balanço do DOOM: cosseno na horizontal, seno retificado na vertical."""
    return (math.cos(fase) * 16.0 * forca, abs(math.sin(fase)) * 13.0 * forca)


def _tons(cor):
    """Rampa de 4 tons (pixel art chapada: contorno, sombra, base, luz)."""
    return (tuple(int(c * 0.28) for c in cor),
            tuple(int(c * 0.60) for c in cor),
            cor,
            tuple(min(255, int(c * 1.42) + 26) for c in cor))


def _viewmodel(tela, arma_idx, tempo, recuo, bob_x, bob_y, recarga_frac, spin, cor_jogador):
    """
    Desenha a arma em primeira pessoa no estilo DOOM e devolve a posição da
    BOCA DO CANO na tela (para o clarão do disparo).

    Sistema de coordenadas da arte: (0, 0) é o centro da base da viewport,
    x cresce para a direita e **y cresce para CIMA** (a arma sobe da base).
    """
    arma = ARMAS[arma_idx]
    cor = arma['cor']
    esc = _VM_ESC

    # y = 0 da arte fica praticamente na borda de baixo da viewport: assim o
    # corpo da arma ocupa ~40% da tela e sobra espaço para ver os antebraços.
    cx = LARGURA / 2 + bob_x
    base = ALTURA_JOGO + 10 + bob_y + recuo * 26
    if recarga_frac > 0:
        # Ao recarregar a arma desce da tela e volta (igual à troca de arma no DOOM)
        base += math.sin(min(1.0, recarga_frac) * math.pi) * 330

    def P(x, y):
        return (cx + x * esc * _VM_KX, base - y * esc)

    def poly(cor_p, pts, contorno=None, lg=2):
        p = [P(x, y) for (x, y) in pts]
        pygame.draw.polygon(tela, cor_p, p)
        if contorno:
            pygame.draw.polygon(tela, contorno, p, max(1, int(lg * esc / 2)))
        return p

    def bloco(x_c, y0, y1, w0, w1, cor_b, chanfro=True):
        """
        Bloco em perspectiva: w0 é a largura embaixo (perto) e w1 em cima
        (longe). Ganha uma faixa clara à esquerda e escura à direita, que é
        o truque de sombreado dos sprites do DOOM.
        """
        esc_c, som_c, bas_c, luz_c = _tons(cor_b)
        poly(bas_c, [(x_c - w0 / 2, y0), (x_c + w0 / 2, y0),
                     (x_c + w1 / 2, y1), (x_c - w1 / 2, y1)], esc_c, 2)
        if chanfro:
            f0 = w0 * 0.22
            f1 = w1 * 0.22
            poly(luz_c, [(x_c - w0 / 2 + 2, y0), (x_c - w0 / 2 + f0, y0),
                         (x_c - w1 / 2 + f1, y1), (x_c - w1 / 2 + 2, y1)])
            poly(som_c, [(x_c + w0 / 2 - f0, y0), (x_c + w0 / 2 - 2, y0),
                         (x_c + w1 / 2 - 2, y1), (x_c + w1 / 2 - f1, y1)])

    def cano(x_c, y0, y1, w0, w1, cor_b, bore=True):
        """Cano visto por trás: bloco + boca escura no topo."""
        bloco(x_c, y0, y1, w0, w1, cor_b)
        if bore:
            esc_c = _tons(cor_b)[0]
            poly((8, 8, 12), [(x_c - w1 / 2 + 2, y1), (x_c + w1 / 2 - 2, y1),
                              (x_c + w1 / 2 - 4, y1 + 4), (x_c - w1 / 2 + 4, y1 + 4)])
            del esc_c

    def parafusos(x_c, y, larg, n, cor_p=(140, 146, 162)):
        for i in range(n):
            px = x_c - larg / 2 + (larg / max(1, n - 1)) * i
            pygame.draw.circle(tela, cor_p, (int(P(px, y)[0]), int(P(px, y)[1])),
                               max(2, int(2.2 * esc / 2)))

    def brilho(x_c, y, raio, cor_g, alpha=150):
        r = int(raio * esc)
        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (cor_g[0], cor_g[1], cor_g[2], alpha // 3), (r * 2, r * 2), r * 2)
        pygame.draw.circle(s, (cor_g[0], cor_g[1], cor_g[2], alpha), (r * 2, r * 2), r)
        pygame.draw.circle(s, (255, 255, 255, min(255, alpha + 70)), (r * 2, r * 2), max(1, r // 2))
        pos = P(x_c, y)
        tela.blit(s, (int(pos[0]) - r * 2, int(pos[1]) - r * 2))

    # ---- Mãos enluvadas (desenhadas por último, POR CIMA da arma, agarrando) ----
    maos = []

    def mao(x_c, y, esp=1.0):
        maos.append((x_c, y, esp))

    def desenhar_maos():
        # Manga escura na cor do jogador (identifica quem é você sem gritar) +
        # luva chapada. No DOOM as mãos entram por baixo, bem na base da tela.
        manga_som = tuple(int(c * 0.26) for c in cor_jogador)
        manga_bas = tuple(int(c * 0.46) for c in cor_jogador)
        manga_luz = tuple(min(255, int(c * 0.78)) for c in cor_jogador)
        pele_som, pele_bas, pele_luz = manga_som, manga_bas, manga_luz
        luva_som = (20, 22, 29)
        luva = (46, 49, 62)
        luva_luz = (84, 89, 108)
        contorno = (9, 9, 14)
        for (x_c, y, esp) in maos:
            lado = -1 if x_c < 0 else 1
            # A largura vem dividida por _VM_KX para o punho não esticar junto
            # com o corpo da arma (só a arma é alargada na horizontal).
            w = 36 * esp / _VM_KX
            # Manga: sai da base da tela, um pouco mais para fora, e sobe ao punho
            bx = x_c + lado * 24
            poly(pele_som, [(x_c - w * 0.40, y - 10), (x_c + w * 0.40, y - 10),
                            (bx + w * 0.50, -26), (bx - w * 0.50, -26)], contorno, 3)
            poly(pele_bas, [(x_c - w * 0.26, y - 10), (x_c + w * 0.18, y - 10),
                            (bx + w * 0.26, -26), (bx - w * 0.32, -26)])
            poly(pele_luz, [(x_c - w * 0.26, y - 12), (x_c - w * 0.18, y - 12),
                            (bx - w * 0.24, -26), (bx - w * 0.32, -26)])
            # Punho da manga (quebra a barra chapada do antebraço)
            poly(pele_som, [(x_c - w * 0.42, y - 10), (x_c + w * 0.42, y - 10),
                            (x_c + w * 0.44, y - 3), (x_c - w * 0.44, y - 3)], contorno, 2)
            # Punho fechado (mais alto que largo), por cima do corpo da arma
            poly(luva, [(x_c - w * 0.46, y - 15), (x_c + w * 0.46, y - 15),
                        (x_c + w * 0.50, y + 21), (x_c - w * 0.50, y + 21)], contorno, 3)
            poly(luva_som, [(x_c + lado * w * 0.24, y - 14), (x_c + lado * w * 0.48, y - 14),
                            (x_c + lado * w * 0.48, y + 20), (x_c + lado * w * 0.24, y + 20)])
            # Nós dos dedos (3 blocos no alto, estilo sprite)
            for k in range(3):
                fx = x_c - w * 0.30 + (w * 0.60 / 2) * k
                poly(luva_luz, [(fx - w * 0.13, y + 5), (fx + w * 0.13, y + 5),
                                (fx + w * 0.12, y + 20), (fx - w * 0.12, y + 20)],
                     contorno, 1)
            # Polegar dobrado por dentro
            poly(luva_luz, [(x_c - lado * w * 0.50, y - 4), (x_c - lado * w * 0.26, y - 9),
                            (x_c - lado * w * 0.20, y + 7), (x_c - lado * w * 0.44, y + 10)],
                 contorno, 2)

    aid = arma['id']
    metal = (86, 92, 108)
    metal_esc = (54, 58, 72)

    # ============================================================
    if aid == 'pulse':
        # Fuzil de plasma: corpo em cunha, dois trilhos de energia e cano curto
        bloco(0, 4, 46, 108, 92, metal_esc)                 # coronha (perto)
        bloco(0, 40, 104, 96, 66, metal)                    # receptor
        for s in (-1, 1):
            bloco(s * 40, 44, 96, 20, 14, (46, 50, 64))     # trilhos laterais
        # Células de energia pulsando nas laterais
        pulso = 0.55 + 0.45 * math.sin(tempo / 130.0)
        for s in (-1, 1):
            poly((int(cor[0] * pulso), int(cor[1] * pulso), int(cor[2] * pulso)),
                 [(s * 34 - 7, 54), (s * 34 + 7, 54), (s * 34 + 6, 88), (s * 34 - 6, 88)],
                 (16, 18, 26), 1)
        bloco(0, 100, 132, 60, 40, (66, 72, 88))            # bloco do cano
        cano(0, 128, 158, 34, 26, metal)                    # cano
        parafusos(0, 46, 70, 5)
        # Anel de energia na boca
        brilho(0, 152, 7, cor, int(90 + 60 * pulso))
        boca = (0, 160)
        mao(-42, 48, 1.0)
        mao(40, 56, 0.95)

    # ============================================================
    elif aid == 'shotgun':
        # Cano duplo visto por trás + bomba de madeira no meio
        bloco(0, 0, 40, 116, 104, (58, 44, 30))             # coronha de madeira
        bloco(0, 34, 74, 104, 88, metal_esc)                # caixa da culatra
        parafusos(0, 52, 66, 4, (168, 150, 96))
        for s in (-1, 1):
            cano(s * 23, 70, 172, 40, 30, metal)            # os dois canos
        bloco(0, 92, 126, 70, 60, (104, 74, 42))            # bomba (madeira)
        for i in range(5):                                  # ranhuras da bomba
            poly((66, 46, 26), [(-29, 98 + i * 6), (29, 98 + i * 6),
                                (29, 100 + i * 6), (-29, 100 + i * 6)])
        # Cartuchos vermelhos aparecendo na culatra
        for s in (-1, 1):
            poly((188, 44, 44), [(s * 23 - 9, 36), (s * 23 + 9, 36),
                                 (s * 23 + 8, 48), (s * 23 - 8, 48)], (90, 20, 20), 1)
        boca = (0, 176)
        mao(-44, 46, 1.05)
        mao(42, 96, 0.95)

    # ============================================================
    elif aid == 'rail':
        # Canhão de trilho: corpo largo com garra de 3 pontas e núcleo pulsante
        bloco(0, 0, 52, 132, 120, metal_esc)
        bloco(0, 46, 108, 124, 92, metal)
        parafusos(0, 20, 96, 6)
        # Bobinas que carregam ao longo do corpo
        for i in range(3):
            fase = (tempo / 200.0 + i * 0.4) % 1.0
            br = 0.3 + 0.7 * (1 - abs(fase - 0.5) * 2)
            cb = (int(cor[0] * br), int(cor[1] * br), int(cor[2] * br))
            poly((48, 54, 66), [(-56, 58 + i * 16), (56, 58 + i * 16),
                                (56, 66 + i * 16), (-56, 66 + i * 16)], (14, 16, 22), 1)
            poly(cb, [(-50, 60 + i * 16), (50, 60 + i * 16),
                      (50, 64 + i * 16), (-50, 64 + i * 16)])
        # Garra de três pontas
        for s in (-1, 0, 1):
            bloco(s * 34, 104, 168 - abs(s) * 18, 26, 16, (70, 78, 94))
        # Núcleo de energia no meio da garra
        pulso = 0.5 + 0.5 * math.sin(tempo / 150.0)
        brilho(0, 132, 12 + 3 * pulso, cor, int(120 + 80 * pulso))
        boca = (0, 150)
        mao(-52, 46, 1.05)
        mao(50, 52, 1.0)

    # ============================================================
    elif aid == 'vortex':
        # Metralhadora rotativa: feixe de canos girando visto de trás
        bloco(0, 0, 44, 120, 108, metal_esc)
        bloco(0, 38, 96, 112, 92, metal)
        parafusos(0, 16, 84, 5)
        # Caixa de munição com fita de cartuchos descendo pela esquerda
        bloco(-62, 12, 58, 44, 40, (78, 64, 36))
        for i in range(6):
            poly((198, 168, 78), [(-80 + i * 7, 20), (-75 + i * 7, 20),
                                  (-75 + i * 7, 34), (-80 + i * 7, 34)], (96, 78, 30), 1)
        # Carcaça do feixe
        bloco(0, 92, 122, 84, 74, (62, 68, 84))
        # 6 canos girando (os de trás ficam mais escuros)
        canos = []
        for i in range(6):
            a = spin + (2 * math.pi * i) / 6
            canos.append((math.cos(a) * 26, math.sin(a) * 12, math.sin(a)))
        canos.sort(key=lambda c: c[2])          # desenha os de trás primeiro
        for (dx, dy, prof) in canos:
            f = 0.55 + 0.45 * (prof + 1) / 2
            cb = (int(metal[0] * f), int(metal[1] * f), int(metal[2] * f))
            cano(dx, 118 + dy, 158 + dy, 22, 18, cb)
        # Eixo central
        pygame.draw.circle(tela, (40, 44, 56),
                           (int(P(0, 138)[0]), int(P(0, 138)[1])), int(7 * esc))
        pygame.draw.circle(tela, (96, 102, 118),
                           (int(P(0, 138)[0]), int(P(0, 138)[1])), int(4 * esc))
        boca = (0, 162)
        mao(-50, 46, 1.05)
        mao(48, 58, 0.95)

    # ============================================================
    else:  # nova
        # Lança-foguetes: tubo grosso com a boca enorme e o foguete à vista
        bloco(0, 0, 40, 124, 112, (58, 46, 68))             # apoio de ombro
        bloco(0, 34, 118, 116, 96, (74, 58, 88))            # tubo
        for s in (-1, 1):                                    # trilhos laterais
            bloco(s * 62, 40, 106, 16, 12, (46, 36, 56))
        parafusos(0, 50, 80, 5, (168, 140, 190))
        # Boca do tubo (elipse escura) com o foguete dentro
        bocal = P(0, 128)
        rw = int(52 * esc * _VM_KX)
        rh = int(17 * esc)
        pygame.draw.ellipse(tela, (92, 74, 108), (bocal[0] - rw, bocal[1] - rh, rw * 2, rh * 2))
        pygame.draw.ellipse(tela, (18, 14, 24),
                            (bocal[0] - rw + 6, bocal[1] - rh + 5,
                             (rw - 6) * 2, (rh - 5) * 2))
        carregado = recarga_frac <= 0.0
        if carregado:
            pulso = 0.5 + 0.5 * math.sin(tempo / 170.0)
            pygame.draw.ellipse(tela, (int(cor[0] * pulso), int(cor[1] * pulso),
                                       int(cor[2] * pulso)),
                                (bocal[0] - rw * 0.45, bocal[1] - rh * 0.5,
                                 rw * 0.9, rh * 1.0))
            brilho(0, 130, 9, cor, int(70 + 70 * pulso))
        # Mira de ferro em cima do tubo
        poly((52, 40, 62), [(-6, 118), (6, 118), (5, 136), (-5, 136)], (20, 14, 26), 1)
        boca = (0, 142)
        mao(-50, 44, 1.05)
        mao(48, 72, 0.95)

    desenhar_maos()
    return P(boca[0], boca[1])


def _muzzle_flash(tela, pos, cor, forca):
    """Clarão do disparo: estrela brilhante na boca do cano (fullbright, como no DOOM)."""
    if forca <= 0.02:
        return
    ox, oy = int(pos[0]), int(pos[1])
    r = int(10 + 20 * forca)
    lado = r * 6
    fl = pygame.Surface((lado, lado), pygame.SRCALPHA)
    c = lado // 2
    pygame.draw.circle(fl, (cor[0], cor[1], cor[2], int(70 * forca)), (c, c), int(r * 2.4))
    # Estrela de 6 pontas na cor da arma
    for i in range(6):
        a = (math.pi / 3) * i + 0.25
        comp = r * (2.0 if i % 2 == 0 else 1.3)
        pygame.draw.line(fl, (cor[0], cor[1], cor[2], int(150 * forca)), (c, c),
                         (c + math.cos(a) * comp, c + math.sin(a) * comp),
                         max(2, int(r * 0.34)))
    pygame.draw.circle(fl, (255, 238, 186, int(210 * forca)), (c, c), r)
    pygame.draw.circle(fl, (255, 255, 255, int(240 * forca)), (c, c), int(r * 0.52))
    tela.blit(fl, (ox - c, oy - c))
def _icone_arma(tela, rect, arma_idx, tempo, ativo):
    """Ícone simplificado da arma para os cards de seleção e o HUD."""
    arma = ARMAS[arma_idx]
    cor = arma['cor'] if ativo else tuple(int(c * 0.55) for c in arma['cor'])
    metal = (70, 76, 92) if ativo else (44, 48, 58)
    cx, cy = rect.centerx, rect.centery
    aid = arma['id']
    if aid == 'pulse':
        pygame.draw.rect(tela, metal, (cx - 46, cy - 6, 84, 12), 0, 3)
        pygame.draw.rect(tela, metal, (cx - 30, cy + 4, 16, 20), 0, 2)
        pygame.draw.rect(tela, metal, (cx - 52, cy - 2, 18, 16), 0, 2)
        pygame.draw.rect(tela, cor, (cx - 10, cy - 4, 30, 6), 0, 2)
        pygame.draw.circle(tela, cor, (cx + 40, cy), 5)
    elif aid == 'shotgun':
        pygame.draw.rect(tela, metal, (cx - 44, cy - 8, 86, 8), 0, 3)
        pygame.draw.rect(tela, metal, (cx - 44, cy + 1, 86, 8), 0, 3)
        pygame.draw.polygon(tela, (86, 66, 44), [(cx - 44, cy - 6), (cx - 60, cy + 18), (cx - 44, cy + 18)])
        pygame.draw.circle(tela, cor, (cx + 42, cy - 4), 4)
        pygame.draw.circle(tela, cor, (cx + 42, cy + 5), 4)
    elif aid == 'rail':
        pygame.draw.rect(tela, metal, (cx - 50, cy - 4, 96, 10), 0, 3)
        for i in range(3):
            pygame.draw.rect(tela, cor, (cx - 34 + i * 22, cy - 14, 8, 26), 0, 2)
        pygame.draw.polygon(tela, metal, [(cx - 40, cy + 6), (cx - 22, cy + 6), (cx - 30, cy + 26)])
        pygame.draw.circle(tela, cor, (cx + 46, cy), 5)
    elif aid == 'vortex':
        for i in range(3):
            pygame.draw.rect(tela, metal, (cx - 40, cy - 10 + i * 9, 78, 6), 0, 2)
        pygame.draw.circle(tela, (58, 62, 76), (cx + 40, cy - 1), 12)
        pygame.draw.circle(tela, cor, (cx + 40, cy - 1), 5)
        pygame.draw.rect(tela, (86, 74, 44), (cx - 52, cy + 4, 22, 18), 0, 3)
    else:
        pygame.draw.rect(tela, metal, (cx - 46, cy - 4, 88, 12), 0, 3)
        pygame.draw.circle(tela, (66, 52, 78), (cx - 6, cy + 4), 16)
        pygame.draw.circle(tela, cor, (cx - 6, cy + 4), 7)
        pygame.draw.polygon(tela, metal, [(cx - 34, cy + 8), (cx - 16, cy + 8), (cx - 24, cy + 28)])
        pygame.draw.circle(tela, cor, (cx + 42, cy + 2), 5)


# ============================================================
#  DESENHO 2D AUXILIAR
# ============================================================

def _chapeu_2d(tela, cx, topo, tipo):
    """Versão 2D compacta dos cosméticos de cabeça (intro/placar)."""
    if not tipo:
        return
    if tipo == 'cartola':
        pygame.draw.rect(tela, (20, 20, 25), (cx - 17, topo - 3, 34, 5), 0, 2)
        pygame.draw.rect(tela, (32, 32, 40), (cx - 11, topo - 17, 22, 15), 0, 3)
        pygame.draw.rect(tela, (200, 60, 70), (cx - 11, topo - 8, 22, 4))
    elif tipo == 'bone':
        pygame.draw.rect(tela, (210, 60, 60), (cx - 13, topo - 12, 26, 12), 0, 6)
        pygame.draw.rect(tela, (170, 40, 40), (cx - 2, topo - 2, 22, 5), 0, 3)
    elif tipo == 'coroa':
        pygame.draw.rect(tela, (255, 200, 40), (cx - 14, topo - 6, 28, 6), 0, 2)
        for px in (-14, -5, 4, 13):
            pygame.draw.polygon(tela, (255, 210, 60),
                                [(cx + px, topo - 5), (cx + px + 4, topo - 17),
                                 (cx + px + 8, topo - 5)])
    elif tipo == 'chifres':
        for s in (-1, 1):
            bx = cx + s * 9
            pygame.draw.polygon(tela, (190, 40, 40),
                                [(bx, topo + 1), (bx + s * 3, topo - 14), (bx + s * 8, topo + 1)])
    elif tipo == 'aureola':
        halo = pygame.Surface((36, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (255, 240, 120, 90), (0, 0, 36, 16))
        pygame.draw.ellipse(halo, (255, 235, 90), (0, 0, 36, 16), 3)
        tela.blit(halo, (cx - 18, topo - 16))
    elif tipo == 'festa':
        pygame.draw.polygon(tela, (90, 200, 220), [(cx - 10, topo), (cx + 10, topo), (cx, topo - 20)])
        pygame.draw.circle(tela, (255, 230, 90), (cx, topo - 20), 3)
    elif tipo == 'antena':
        for s in (-1, 1):
            pygame.draw.line(tela, (120, 120, 130), (cx + s * 4, topo), (cx + s * 8, topo - 14), 2)
            pygame.draw.circle(tela, (120, 255, 160), (cx + s * 8, topo - 15), 3)


def _quadrado_2d(tela, x, y, tam, cor, chapeu=None, olhando=1, brilho=True):
    """Avatar quadrado do jogador (mesmo estilo dos outros minigames)."""
    esc = tuple(max(0, c - 60) for c in cor)
    bri = tuple(min(255, c + 80) for c in cor)
    pygame.draw.rect(tela, (10, 9, 16), (x + 4, y + 5, tam, tam), 0, 6)
    pygame.draw.rect(tela, esc, (x, y, tam, tam), 0, 7)
    pygame.draw.rect(tela, cor, (x + 3, y + 3, tam - 6, tam - 6), 0, 5)
    if brilho:
        pygame.draw.rect(tela, bri, (x + 6, y + 6, max(5, tam // 5), max(5, tam // 5)), 0, 3)
    # Visor
    vy = y + tam // 2 - tam // 10
    vw = int(tam * 0.46)
    vx = x + (tam - vw) // 2 + int(olhando * tam * 0.09)
    pygame.draw.rect(tela, (14, 16, 24), (vx, vy, vw, max(4, tam // 6)), 0, 3)
    pygame.draw.rect(tela, (110, 235, 255), (vx + 2, vy + 2, vw - 4, max(2, tam // 10)), 0, 2)
    _chapeu_2d(tela, x + tam // 2, y, chapeu)


def _painel(tela, rect, alpha=170, borda=(70, 90, 130), raio=8):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (8, 10, 20, alpha), (0, 0, rect.width, rect.height), 0, raio)
    tela.blit(s, rect.topleft)
    pygame.draw.rect(tela, borda, rect, 1, raio)


def _texto(tela, fonte, txt, x, y, cor, centro=False, sombra=True):
    s = fonte.render(txt, True, cor)
    if centro:
        x = int(x - s.get_width() / 2)
    if sombra:
        tela.blit(fonte.render(txt, True, (0, 0, 0)), (x + 2, y + 2))
    tela.blit(s, (int(x), int(y)))
    return s.get_width()


# ============================================================
#  HUD DO COMBATE
# ============================================================

def _desenhar_mira(tela, cx, cy, espalha, sobre_inimigo, hitmarker, foi_kill, recarga):
    """Mira dinâmica: abre com o espalhamento e fica vermelha sobre inimigos."""
    cor = (255, 80, 80) if sobre_inimigo else (190, 240, 255)
    d = int(6 + espalha * 620)
    lg = 2
    for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pygame.draw.line(tela, (0, 0, 0), (cx + dx * d + 1, cy + dy * d + 1),
                         (cx + dx * (d + 9) + 1, cy + dy * (d + 9) + 1), lg + 2)
    for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pygame.draw.line(tela, cor, (cx + dx * d, cy + dy * d),
                         (cx + dx * (d + 9), cy + dy * (d + 9)), lg)
    pygame.draw.circle(tela, cor, (cx, cy), 2)

    if recarga > 0:
        raio = 26
        ang0 = -math.pi / 2
        pygame.draw.arc(tela, (60, 70, 90), (cx - raio, cy - raio, raio * 2, raio * 2),
                        0, math.tau, 3)
        pygame.draw.arc(tela, (255, 210, 90), (cx - raio, cy - raio, raio * 2, raio * 2),
                        ang0 - recarga * math.tau, ang0, 3)

    if hitmarker:
        c = (255, 235, 120) if not foi_kill else (255, 90, 90)
        for (sx, sy) in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
            pygame.draw.line(tela, c, (cx + sx * 7, cy + sy * 7),
                             (cx + sx * 15, cy + sy * 15), 3)


def _desenhar_radar(tela, mundo, jl, fonte):
    """Radar circular no canto: mostra quem está por perto, girado pelo yaw."""
    r = 74
    cx = LARGURA - r - 26
    cy = r + 26
    alcance = 42.0

    s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (6, 12, 20, 165), (r + 2, r + 2), r)
    pygame.draw.circle(s, (60, 170, 200, 120), (r + 2, r + 2), r, 2)
    pygame.draw.circle(s, (40, 110, 140, 90), (r + 2, r + 2), int(r * 0.66), 1)
    pygame.draw.circle(s, (40, 110, 140, 90), (r + 2, r + 2), int(r * 0.33), 1)
    pygame.draw.line(s, (40, 110, 140, 80), (r + 2, 4), (r + 2, r * 2), 1)
    pygame.draw.line(s, (40, 110, 140, 80), (4, r + 2), (r * 2, r + 2), 1)
    tela.blit(s, (cx - r - 2, cy - r - 2))

    # Cone de visão
    cone = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.polygon(cone, (90, 220, 255, 40),
                        [(r, r), (r - r * 0.62, r - r * 0.85), (r + r * 0.62, r - r * 0.85)])
    tela.blit(cone, (cx - r, cy - r))

    cos_y = math.cos(jl.yaw)
    sin_y = math.sin(jl.yaw)
    for p in mundo.jogadores:
        if not p.ativo or not p.vivo or p is jl:
            continue
        dx = p.x - jl.x
        dz = p.z - jl.z
        dist = math.hypot(dx, dz)
        if dist > alcance:
            continue
        # Projeta no referencial da câmera (frente = cima do radar)
        lado = dx * cos_y - dz * sin_y
        frente = dx * sin_y + dz * cos_y
        px = int(cx + (lado / alcance) * r)
        py = int(cy - (frente / alcance) * r)
        tam = 5
        pygame.draw.rect(tela, (0, 0, 0), (px - tam // 2 - 1, py - tam // 2 - 1, tam + 2, tam + 2))
        pygame.draw.rect(tela, p.cor, (px - tam // 2, py - tam // 2, tam, tam))
        if p.y > jl.y + 1.0:
            pygame.draw.polygon(tela, (255, 255, 255),
                                [(px, py - 7), (px - 3, py - 4), (px + 3, py - 4)])
        elif p.y < jl.y - 1.0:
            pygame.draw.polygon(tela, (255, 255, 255),
                                [(px, py + 7), (px - 3, py + 4), (px + 3, py + 4)])

    pygame.draw.rect(tela, (255, 255, 255), (cx - 2, cy - 2, 4, 4))
    _texto(tela, fonte, "RADAR", cx, cy + r + 6, (110, 180, 200), True)


def _desenhar_killfeed(tela, mundo, tempo, fonte):
    y = 218                      # abaixo do radar
    for ev in mundo.killfeed[-6:]:
        if tempo > ev['ate']:
            continue
        alpha = 1.0
        restante = ev['ate'] - tempo
        if restante < 400:
            alpha = restante / 400.0
        txt_a = ev['a']
        txt_v = ev['v']
        arma = ARMAS[ev['w']]['nome'] if 0 <= ev['w'] < len(ARMAS) else ''
        sa = fonte.render(txt_a, True, ev['ca'])
        sw = fonte.render(f"  [{arma}]  ", True, (200, 210, 230))
        sv = fonte.render(txt_v, True, ev['cv'])
        larg = sa.get_width() + sw.get_width() + sv.get_width()
        x = LARGURA - 26 - larg
        fundo = pygame.Surface((larg + 16, 22), pygame.SRCALPHA)
        fundo.fill((0, 0, 0, int(130 * alpha)))
        tela.blit(fundo, (x - 8, y - 2))
        for s, dx in ((sa, 0), (sw, sa.get_width()), (sv, sa.get_width() + sw.get_width())):
            s.set_alpha(int(255 * alpha))
            tela.blit(s, (x + dx, y))
        y += 26


def _desenhar_nametags(tela, rend, mundo, jl, fonte):
    """Nome + barra de vida flutuando sobre cada jogador visível."""
    for p in mundo.jogadores:
        if not p.ativo or not p.vivo or p is jl:
            continue
        s = rend.projetar((p.x, p.y + ALTURA_JOGADOR + 0.42, p.z))
        if not s:
            continue
        sx, sy, depth = s
        if depth > 46 or sx < -80 or sx > LARGURA + 80 or sy < -40 or sy > ALTURA_JOGO:
            continue
        if not linha_de_visao((jl.x, jl.y + OLHO_Y, jl.z), (p.x, p.y + 1.2, p.z)):
            continue
        escala = max(0.45, min(1.0, 14.0 / max(1.0, depth)))
        larg = int(64 * escala)
        alt = max(3, int(6 * escala))
        nome = fonte.render(p.nome, True, p.cor)
        if escala < 0.95:
            nome = pygame.transform.smoothscale(
                nome, (max(1, int(nome.get_width() * escala)),
                       max(1, int(nome.get_height() * escala))))
        tela.blit(nome, (int(sx - nome.get_width() / 2) + 1,
                         int(sy - nome.get_height()) + 1))
        bx = int(sx - larg / 2)
        by = int(sy + 3)
        pygame.draw.rect(tela, (0, 0, 0), (bx - 1, by - 1, larg + 2, alt + 2), 0, 2)
        frac = max(0.0, p.hp / HP_MAX)
        cor = (90, 230, 110) if frac > 0.5 else (255, 200, 60) if frac > 0.22 else (255, 70, 70)
        pygame.draw.rect(tela, (40, 44, 56), (bx, by, larg, alt))
        pygame.draw.rect(tela, cor, (bx, by, int(larg * frac), alt))


def _desenhar_dano_flutuante(tela, rend, mundo, tempo, fonte, fonte_hs):
    for d in mundo.dano_flutuante:
        t = 1.0 - max(0.0, (d['ate'] - tempo) / 850.0)
        s = rend.projetar((d['p'][0], d['p'][1] + t * 1.3, d['p'][2]))
        if not s:
            continue
        sx, sy, depth = s
        if depth > 60:
            continue
        alpha = int(255 * max(0.0, 1.0 - t * t))
        f = fonte_hs if d['hs'] else fonte
        cor = (255, 220, 90) if d['hs'] else (255, 255, 255)
        txt = f.render(("%d!" % d['v']) if d['hs'] else str(d['v']), True, cor)
        txt.set_alpha(alpha)
        sombra = f.render(("%d!" % d['v']) if d['hs'] else str(d['v']), True, (0, 0, 0))
        sombra.set_alpha(alpha)
        tela.blit(sombra, (int(sx - txt.get_width() / 2) + 2, int(sy) + 2))
        tela.blit(txt, (int(sx - txt.get_width() / 2), int(sy)))


def _desenhar_indicadores_dano(tela, mundo, jl, tempo):
    """Arcos ao redor da mira apontando de onde veio o tiro."""
    cx, cy = LARGURA // 2, ALTURA_JOGO // 2
    for ind in mundo.indicadores_dano:
        restante = ind['ate'] - tempo
        if restante <= 0:
            continue
        alpha = int(200 * min(1.0, restante / 1100.0))
        rel = ind['ang'] - jl.yaw
        s = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.arc(s, (255, 60, 60, alpha), (10, 10, 240, 240),
                        math.pi / 2 - rel - 0.34, math.pi / 2 - rel + 0.34, 9)
        tela.blit(s, (cx - 130, cy - 130))


def _desenhar_barra_hud(tela, mundo, jl, tempo, restante, fontes):
    """Faixa inferior: vida à esquerda, partida no meio, arma à direita."""
    f_peq, f_media, f_num = fontes
    topo = ALTURA_JOGO
    alt = ALTURA - ALTURA_JOGO
    pygame.draw.rect(tela, (9, 11, 20), (0, topo, LARGURA, alt))
    pygame.draw.line(tela, (50, 130, 170), (0, topo), (LARGURA, topo), 2)
    for i in range(0, LARGURA, 60):
        pygame.draw.line(tela, (16, 24, 40), (i, topo + 4), (i, ALTURA - 4), 1)

    # ---- Vida ----
    frac = max(0.0, jl.hp / HP_MAX)
    cor = (90, 230, 120) if frac > 0.5 else (255, 200, 60) if frac > 0.25 else (255, 70, 70)
    bx, by, bw, bh = 24, topo + 32, 300, 22
    pygame.draw.rect(tela, (24, 28, 38), (bx - 2, by - 2, bw + 4, bh + 4), 0, 4)
    pygame.draw.rect(tela, cor, (bx, by, int(bw * frac), bh), 0, 3)
    for i in range(1, 4):
        px = bx + int(bw * i / 4)
        pygame.draw.line(tela, (12, 14, 22), (px, by), (px, by + bh), 2)
    pygame.draw.rect(tela, (120, 140, 170), (bx, by, bw, bh), 1, 3)
    _texto(tela, f_num, str(max(0, jl.hp)), bx + bw + 16, topo + 18, cor)
    _texto(tela, f_peq, jl.nome, bx, topo + 12, (170, 200, 220))

    # ---- Centro: tempo e frags ----
    seg = max(0, restante // 1000)
    txt_tempo = "%d:%02d" % (seg // 60, seg % 60)
    cor_tempo = (255, 90, 90) if seg <= 20 else (230, 240, 255)
    _texto(tela, f_num, txt_tempo, LARGURA // 2, topo + 14, cor_tempo, True)
    _texto(tela, f_peq, f"FRAGS {jl.kills}/{FRAG_LIMITE}   MORTES {jl.mortes}",
           LARGURA // 2, topo + 58, (150, 180, 200), True)

    # ---- Arma / munição ----
    arma = jl.arma()
    dx = LARGURA - 30
    if tempo < jl.recarregando_ate:
        prog = 1.0 - (jl.recarregando_ate - tempo) / max(1, arma['recarga'])
        s_rec = f_peq.render("RECARREGANDO", True, (255, 200, 90))
        tela.blit(s_rec, (dx - s_rec.get_width(), topo + 22))
        pygame.draw.rect(tela, (30, 34, 44), (dx - 150, topo + 42, 150, 12), 0, 3)
        pygame.draw.rect(tela, (255, 200, 90), (dx - 150, topo + 42, int(150 * prog), 12), 0, 3)
    else:
        cor_mun = (255, 90, 90) if jl.municao <= max(1, arma['mag'] // 5) else (235, 245, 255)
        s_mag = f_peq.render(f"/ {arma['mag']}", True, (130, 150, 175))
        s = f_num.render(str(jl.municao), True, cor_mun)
        tela.blit(s_mag, (dx - s_mag.get_width(), topo + 40))
        tela.blit(s, (dx - s_mag.get_width() - s.get_width() - 8, topo + 16))
    _texto(tela, f_peq, arma['nome'], dx - 250, topo + 62, arma['cor'])
    _icone_arma(tela, pygame.Rect(dx - 300, topo + 12, 130, 46), jl.arma_idx, tempo, True)


def _desenhar_placar(tela, mundo, fontes, tempo, final=False, restante=0):
    """Tabela de pontuação (TAB durante a partida, ou tela final)."""
    f_peq, f_media, f_grande, f_titulo = fontes
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210 if final else 150))
    tela.blit(overlay, (0, 0))

    vivos = [p for p in mundo.jogadores if p.ativo]
    ranking = sorted(vivos, key=lambda p: (-p.kills, p.mortes, p.nome))

    largura = 900
    x0 = LARGURA // 2 - largura // 2
    y0 = 90

    if final:
        _texto(tela, f_titulo, "FIM DE PARTIDA", LARGURA // 2, 26, (255, 220, 120), True)
        if ranking:
            campeao = ranking[0]
            _texto(tela, f_grande, f"{campeao.nome} VENCEU!", LARGURA // 2, 96, campeao.cor, True)
        y0 = 160
    else:
        _texto(tela, f_grande, "PLACAR", LARGURA // 2, 40, (200, 235, 255), True)
        seg = max(0, restante // 1000)
        _texto(tela, f_peq, "Tempo restante  %d:%02d" % (seg // 60, seg % 60),
               LARGURA // 2, 84, (150, 180, 200), True)

    cab = pygame.Rect(x0, y0, largura, 30)
    _painel(tela, cab, 190, (60, 90, 130))
    _texto(tela, f_peq, "#", x0 + 18, y0 + 8, (140, 170, 200))
    _texto(tela, f_peq, "JOGADOR", x0 + 60, y0 + 8, (140, 170, 200))
    _texto(tela, f_peq, "ARMA", x0 + 400, y0 + 8, (140, 170, 200))
    _texto(tela, f_peq, "FRAGS", x0 + 640, y0 + 8, (140, 170, 200))
    _texto(tela, f_peq, "MORTES", x0 + 730, y0 + 8, (140, 170, 200))
    _texto(tela, f_peq, "K/D", x0 + 830, y0 + 8, (140, 170, 200))

    for i, p in enumerate(ranking):
        y = y0 + 40 + i * 46
        linha = pygame.Rect(x0, y, largura, 40)
        cor_fundo = (255, 210, 60, 26) if i == 0 else (40, 60, 90, 22)
        s = pygame.Surface((largura, 40), pygame.SRCALPHA)
        s.fill(cor_fundo)
        tela.blit(s, (x0, y))
        if p.is_local:
            pygame.draw.rect(tela, (120, 220, 255), linha, 2, 4)
        elif i == 0:
            pygame.draw.rect(tela, (255, 210, 60), linha, 1, 4)

        _texto(tela, f_media, str(i + 1), x0 + 16, y + 8,
               (255, 215, 0) if i == 0 else (150, 165, 190))
        _quadrado_2d(tela, x0 + 52, y + 5, 30, p.cor, p.chapeu)
        nome = p.nome + ("  (BOT)" if p.is_bot else "")
        _texto(tela, f_media, nome, x0 + 96, y + 8, BRANCO if not p.is_local else (150, 235, 255))
        _icone_arma(tela, pygame.Rect(x0 + 380, y + 6, 130, 28), p.arma_idx, tempo, True)
        _texto(tela, f_media, str(p.kills), x0 + 652, y + 8, (150, 255, 170))
        _texto(tela, f_media, str(p.mortes), x0 + 748, y + 8, (255, 150, 150))
        kd = p.kills / max(1, p.mortes)
        _texto(tela, f_media, "%.2f" % kd, x0 + 830, y + 8, (200, 210, 230))

    if final:
        _texto(tela, f_peq, "Voltando ao lobby...", LARGURA // 2, ALTURA - 40,
               (140, 160, 190), True)


def _desenhar_placar_mini(tela, mundo, jl, fonte):
    """Top 4 no canto superior esquerdo durante a partida."""
    ativos = sorted([p for p in mundo.jogadores if p.ativo],
                    key=lambda p: (-p.kills, p.nome))[:4]
    rect = pygame.Rect(20, 20, 230, 24 + len(ativos) * 22)
    _painel(tela, rect, 130, (50, 80, 120))
    _texto(tela, fonte, "LIDERES", 32, 26, (120, 190, 220))
    for i, p in enumerate(ativos):
        y = 46 + i * 22
        pygame.draw.rect(tela, p.cor, (32, y + 4, 10, 10), 0, 2)
        cor = (150, 235, 255) if p is jl else (215, 225, 240)
        _texto(tela, fonte, p.nome[:13], 50, y, cor)
        _texto(tela, fonte, str(p.kills), 232, y, (150, 255, 170))


# ============================================================
#  TELA DE PREPARAÇÃO (arma + bots)
# ============================================================

def _cards_armas():
    cards = []
    cw, ch = 262, 322
    gap = 18
    total = len(ARMAS) * cw + (len(ARMAS) - 1) * gap
    x0 = LARGURA // 2 - total // 2
    for i in range(len(ARMAS)):
        cards.append(pygame.Rect(x0 + i * (cw + gap), 178, cw, ch))
    return cards


def _desenhar_setup(tela, mundo, jl, cards, sel, mouse, host, num_bots, restante,
                    fontes, tempo, botoes_bots):
    f_peq, f_media, f_grande, f_titulo = fontes
    tela.fill((7, 9, 18))
    # Fundo: grade em perspectiva
    for i in range(26):
        y = 120 + i * i * 2.4
        if y > ALTURA:
            break
        a = max(10, 60 - i * 2)
        pygame.draw.line(tela, (a // 3, a // 2, a), (0, int(y)), (LARGURA, int(y)), 1)
    for i in range(-14, 15):
        pygame.draw.line(tela, (14, 30, 48), (LARGURA // 2 + i * 30, 120),
                         (LARGURA // 2 + i * 260, ALTURA), 1)

    _texto(tela, f_titulo, "ARENA 3D", LARGURA // 2, 28, (150, 235, 255), True)
    _texto(tela, f_peq, "Escolha sua arma  -  deathmatch de todos contra todos",
           LARGURA // 2, 100, (140, 175, 200), True)
    seg = max(0, restante // 1000)
    _texto(tela, f_media, f"{seg}s", LARGURA - 60, 30, (255, 200, 100), True)

    for i, rect in enumerate(cards):
        arma = ARMAS[i]
        hover = rect.collidepoint(mouse)
        ativo = (i == sel)
        realce = ativo or hover
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((18, 26, 40, 220) if realce else (12, 16, 26, 190))
        tela.blit(s, rect.topleft)
        pygame.draw.rect(tela, arma['cor'] if realce else (52, 66, 88), rect,
                         3 if ativo else 2, 10)
        if ativo:
            gl = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(gl, (arma['cor'][0], arma['cor'][1], arma['cor'][2], 40),
                             (0, 0, rect.width + 20, rect.height + 20), 6, 14)
            tela.blit(gl, (rect.x - 10, rect.y - 10))

        _icone_arma(tela, pygame.Rect(rect.x, rect.y + 24, rect.width, 70), i, tempo, realce)
        _texto(tela, f_media, arma['nome'], rect.centerx, rect.y + 104,
               arma['cor'] if realce else (190, 200, 215), True)
        # Descrição em duas linhas
        palavras = arma['desc'].split()
        linha = ""
        ly = rect.y + 136
        for w in palavras:
            teste = (linha + " " + w).strip()
            if f_peq.size(teste)[0] > rect.width - 26:
                _texto(tela, f_peq, linha, rect.centerx, ly, (150, 165, 185), True)
                ly += 17
                linha = w
            else:
                linha = teste
        if linha:
            _texto(tela, f_peq, linha, rect.centerx, ly, (150, 165, 185), True)

        rotulos = ("DANO", "CADENCIA", "ALCANCE", "CONTROLE")
        for k, val in enumerate(arma['stats']):
            by = rect.y + 196 + k * 26
            _texto(tela, f_peq, rotulos[k], rect.x + 16, by - 2, (120, 140, 160))
            bx = rect.x + 110
            bw = rect.width - 126
            pygame.draw.rect(tela, (26, 32, 44), (bx, by + 2, bw, 10), 0, 3)
            pygame.draw.rect(tela, arma['cor'], (bx, by + 2, int(bw * val), 10), 0, 3)
        _texto(tela, f_peq, str(i + 1), rect.x + 10, rect.y + 8, (120, 150, 175))

    # ---- Rodapé: jogadores + bots + começar ----
    rodape = pygame.Rect(60, 528, LARGURA - 120, 106)
    _painel(tela, rodape, 170, (50, 80, 120))

    x = rodape.x + 18
    _texto(tela, f_peq, "NA ARENA", x, rodape.y + 10, (120, 190, 220))
    for p in mundo.jogadores:
        if not p.ativo:
            continue
        _quadrado_2d(tela, x, rodape.y + 34, 30, p.cor, p.chapeu)
        marca = "BOT" if p.is_bot else (ARMAS[p.arma_idx]['nome'].split()[0] if p.pronto else "...")
        _texto(tela, f_peq, p.nome[:9], x - 4, rodape.y + 68,
               (150, 235, 255) if p.is_local else (200, 210, 225))
        _texto(tela, f_peq, marca, x - 4, rodape.y + 84,
               (140, 255, 160) if (p.pronto or p.is_bot) else (130, 140, 160))
        x += 74
        if x > rodape.right - 340:
            break

    bx = rodape.right - 300
    _texto(tela, f_peq, "BOTS NA PARTIDA", bx, rodape.y + 10, (120, 190, 220))
    menos, mais = botoes_bots
    for r, txt, ok in ((menos, "-", host), (mais, "+", host)):
        cor = (60, 150, 200) if ok else (50, 55, 70)
        pygame.draw.rect(tela, (16, 24, 36), r, 0, 6)
        pygame.draw.rect(tela, cor, r, 2, 6)
        _texto(tela, f_media, txt, r.centerx, r.y + 2, cor if ok else (80, 90, 110), True)
    _texto(tela, f_grande, str(num_bots), (menos.right + mais.left) // 2,
           menos.y - 4, (255, 220, 120), True)
    if not host:
        _texto(tela, f_peq, "(o host decide)", bx, rodape.y + 84, (120, 135, 155))

    dica = ("1-5 ou clique: arma   |   ENTER: confirmar   |   setas: bots   |   ESC: sair"
            if host else "1-5 ou clique: arma   |   ENTER: confirmar   |   ESC: sair")
    _texto(tela, f_peq, dica, LARGURA // 2, ALTURA - 34, (130, 160, 185), True)
    if host:
        _texto(tela, f_media, "ENTER PARA COMECAR", LARGURA // 2, ALTURA - 66,
               (255, 220, 120) if (tempo // 400) % 2 == 0 else (200, 170, 90), True)
    else:
        _texto(tela, f_media, "Aguardando o host iniciar...", LARGURA // 2, ALTURA - 66,
               (170, 200, 220), True)


# ============================================================
#  INTRO 2D E TRANSIÇÃO
# ============================================================

def _desenhar_intro(tela, gradiente, mundo, t_ms, fontes, tempo):
    f_peq, f_media, f_grande, f_titulo = fontes
    if gradiente:
        tela.blit(gradiente, (0, 0))
    else:
        tela.fill((10, 12, 24))
    veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    veu.fill((4, 6, 16, 190))
    tela.blit(veu, (0, 0))

    _texto(tela, f_titulo, "ARENA 3D", LARGURA // 2, 70, (160, 240, 255), True)
    _texto(tela, f_media, "DEATHMATCH", LARGURA // 2, 140, (255, 210, 120), True)

    ativos = [p for p in mundo.jogadores if p.ativo]
    n = max(1, len(ativos))
    card_w = min(180, (LARGURA - 120) // n)
    total = n * card_w
    x0 = LARGURA // 2 - total // 2
    base_y = 280

    for i, p in enumerate(ativos):
        atraso = i * 110
        if t_ms < atraso:
            continue
        ap = min(1.0, (t_ms - atraso) / 320.0)
        desloc = int((1.0 - ap) * 60)
        x = x0 + i * card_w
        y = base_y + desloc
        rect = pygame.Rect(x + 6, y, card_w - 12, 210)
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((14, 20, 34, int(200 * ap)))
        tela.blit(s, rect.topleft)
        pygame.draw.rect(tela, p.cor, rect, 2, 8)
        tam = 54
        _quadrado_2d(tela, rect.centerx - tam // 2, rect.y + 26, tam, p.cor, p.chapeu,
                     1 if i % 2 == 0 else -1)
        _texto(tela, f_media, p.nome[:11], rect.centerx, rect.y + 100, BRANCO, True)
        _texto(tela, f_peq, "BOT" if p.is_bot else ("VOCE" if p.is_local else "JOGADOR"),
               rect.centerx, rect.y + 126,
               (255, 200, 120) if p.is_bot else (150, 235, 255), True)
        _icone_arma(tela, pygame.Rect(rect.x, rect.y + 146, rect.width, 34),
                    p.arma_idx, tempo, True)
        _texto(tela, f_peq, ARMAS[p.arma_idx]['nome'], rect.centerx, rect.y + 184,
               ARMAS[p.arma_idx]['cor'], True)

    if t_ms > 1500:
        pontos = "." * (1 + (t_ms // 300) % 3)
        _texto(tela, f_media, "Preparando a arena" + pontos, LARGURA // 2, 560,
               (170, 200, 220), True)
    _texto(tela, f_peq, f"Primeiro a {FRAG_LIMITE} frags vence  -  WASD, mouse e pulo no ESPACO",
           LARGURA // 2, ALTURA - 46, (140, 165, 190), True)


def _desenhar_transicao(tela, t, fontes):
    f_peq, f_media, f_grande, f_titulo = fontes
    tela.fill((0, 0, 0))
    cx, cy = LARGURA // 2, ALTURA_JOGO // 2

    # Túnel de linhas
    for i in range(48):
        ang = (i / 48) * math.tau
        r0 = 40 + t * 200
        r1 = 40 + t * 1400
        c = int(60 + 150 * t)
        pygame.draw.line(tela, (c // 2, min(255, c), 255),
                         (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0),
                         (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1), 1)
    # Anéis
    for i in range(7):
        fase = (t * 2.4 - i * 0.13)
        if fase <= 0:
            continue
        raio = int(fase * max(LARGURA, ALTURA_JOGO))
        alpha = max(0, 210 - int(fase * 210))
        if alpha <= 0 or raio <= 0:
            continue
        s = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
        pygame.draw.circle(s, (70, 210, 255, alpha), (cx, cy), raio, 7)
        tela.blit(s, (0, 0))
    # Glitch
    rnd = random.Random(int(t * 90))
    for _ in range(14):
        gy = rnd.randint(0, ALTURA_JOGO)
        gh = rnd.randint(2, 12)
        gx = rnd.randint(-50, 50)
        col = rnd.choice([(90, 220, 255), (255, 90, 160), (255, 255, 255)])
        s = pygame.Surface((LARGURA, gh), pygame.SRCALPHA)
        s.fill((col[0], col[1], col[2], 90))
        tela.blit(s, (gx, gy))

    if t > 0.18:
        alpha = min(255, int((t - 0.18) * 420))
        txt = f_titulo.render("ENTRANDO NA ARENA", True, (200, 245, 255))
        txt.set_alpha(alpha)
        tela.blit(txt, (cx - txt.get_width() // 2, cy - 130))
    if t > 0.72:
        flash = pygame.Surface((LARGURA, ALTURA))
        flash.fill((255, 255, 255))
        flash.set_alpha(int((t - 0.72) / 0.28 * 255))
        tela.blit(flash, (0, 0))


# ============================================================
#  REDE
# ============================================================

def _construir_snapshot(mundo, estado, restante, num_bots):
    # Cor/chapéu/pronto só mudam antes da luta: fora do SETUP eles saem do
    # pacote (o snapshot vai 30x por segundo, cada campo economizado conta).
    enxuto = (estado == "FIGHT")
    pl = []
    for p in mundo.jogadores:
        d = {
            'x': round(p.x, 2), 'y': round(p.y, 2), 'z': round(p.z, 2),
            'yw': round(p.yaw, 3),
            'hp': int(p.hp), 'v': 1 if p.vivo else 0,
            'k': p.kills, 'm': p.mortes, 'w': p.arma_idx,
            'a': 1 if p.ativo else 0, 'rs': p.respawn_seq,
        }
        if not enxuto:
            d['pr'] = 1 if p.pronto else 0
            d['c'] = list(p.cor)
            d['ht'] = p.chapeu
        pl.append(d)
    snap = {
        'action': 'd3_state',
        'st': estado,
        't': int(restante),
        'nb': int(num_bots),
        'pl': pl,
        'pj': [[round(f.x, 2), round(f.y, 2), round(f.z, 2)] for f in mundo.foguetes],
    }
    if mundo.fx_pendentes:
        snap['fx'] = mundo.fx_pendentes[-60:]
    return snap


def _aplicar_snapshot(mundo, snap, tempo, jl):
    """Aplica o estado recebido do host. Retorna (estado, restante, num_bots)."""
    for i, pj in enumerate(snap.get('pl', [])):
        if i >= len(mundo.jogadores):
            break
        p = mundo.jogadores[i]
        p.ativo = bool(pj.get('a', 1))
        p.hp = pj.get('hp', p.hp)
        p.vivo = bool(pj.get('v', 1))
        p.kills = pj.get('k', p.kills)
        p.mortes = pj.get('m', p.mortes)
        # Aparência/arma do jogador local são decididas AQUI e informadas ao host
        # (d3_load). Não sobrescrevemos com o snapshot, senão a escolha "volta"
        # enquanto o pacote de loadout ainda está a caminho.
        if not p.is_local:
            if 'pr' in pj:
                p.pronto = bool(pj['pr'])
            cor = pj.get('c')
            if cor and len(cor) == 3:
                p.cor = tuple(cor)
            if 'ht' in pj:
                p.chapeu = pj['ht']
            w = pj.get('w', p.arma_idx)
            if w != p.arma_idx:
                p.aplicar_arma(w)

        rs = pj.get('rs', 0)
        if p.is_local:
            # Cliente é dono da própria posição — só teleporta ao renascer
            if rs != p.respawn_seq:
                p.respawn_seq = rs
                p.x, p.y, p.z = pj['x'], pj['y'], pj['z']
                p.yaw = pj.get('yw', p.yaw)
                p.pitch = 0.0
                p.vy = 0.0
                p.no_chao = True
                p.municao = p.arma()['mag']
                p.recarregando_ate = 0
                p.alvo_x, p.alvo_y, p.alvo_z = p.x, p.y, p.z
        else:
            p.respawn_seq = rs
            p.alvo_x = pj['x']
            p.alvo_y = pj['y']
            p.alvo_z = pj['z']
            p.alvo_yaw = pj.get('yw', p.yaw)
            # Distância grande = teletransporte (respawn): não interpola
            if abs(p.alvo_x - p.x) > 6 or abs(p.alvo_z - p.z) > 6:
                p.x, p.y, p.z = p.alvo_x, p.alvo_y, p.alvo_z
                p.yaw = p.alvo_yaw

    mundo.foguetes_render = [tuple(pj) for pj in snap.get('pj', [])]
    for ev in snap.get('fx', []):
        _aplicar_fx(mundo, ev, tempo, remoto=True)

    return snap.get('st'), snap.get('t', 0), snap.get('nb', 0)


def _interpolar(mundo, dt, host):
    """Suaviza jogadores cuja posição vem pela rede (30Hz -> 60fps)."""
    t = min(1.0, dt * 16.0)
    for p in mundo.jogadores:
        if p.is_local:
            continue
        if p.is_bot and host:
            continue
        ax = p.alvo_x - p.x
        az = p.alvo_z - p.z
        dist = math.hypot(ax, az)
        p.x += ax * t
        p.y += (p.alvo_y - p.y) * t
        p.z += az * t
        p.yaw = ang_lerp(p.yaw, p.alvo_yaw, t)
        p.vel_atual = dist / max(dt, 0.001)
        p.passo += p.vel_atual * dt * 2.4
        chao = altura_chao(p.x, p.z, p.y)
        p.no_chao = p.y <= chao + 0.12


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def executar_minigame_duel3d(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                             cliente, nome_jogador, customizacao):
    """Executa o minigame Arena 3D (deathmatch em primeira pessoa)."""
    print("[ARENA3D] Minigame Arena 3D iniciado!")

    rng = random.Random()
    if cliente:
        cliente.get_minigame_actions()          # descarta fila da partida anterior
        cliente.set_callback('on_minigame_action', None)

    f_titulo = pygame.font.SysFont("Arial", 54, True)
    f_grande = pygame.font.SysFont("Arial", 34, True)
    f_media = pygame.font.SysFont("Arial", 22, True)
    f_peq = pygame.font.SysFont("Arial", 14)
    f_nome = pygame.font.SysFont("Arial", 15, True)
    f_dano = pygame.font.SysFont("Arial", 20, True)
    f_hs = pygame.font.SysFont("Arial", 26, True)
    f_num = pygame.font.SysFont("Arial", 40, True)
    fontes_tela = (f_peq, f_media, f_grande, f_titulo)
    fontes_hud = (f_peq, f_media, f_num)

    host = sou_host(cliente)
    mundo = Mundo()

    # ---------- montar a lista de jogadores (ordem igual em todas as máquinas) ----------
    humanos = ordenar_humanos(cliente, nome_jogador)[:MAX_JOGADORES]
    jogador_local = None
    for i, (pid, nome, is_local) in enumerate(humanos):
        if is_local:
            cor = tuple(customizacao.get('cor', AZUL))
        else:
            cor = PALETA_CORES[((pid or 0) + 1) % len(PALETA_CORES)]
        d = Duelista(i, str(nome)[:12], cor, is_bot=False, is_local=is_local)
        d.player_id = pid
        if is_local:
            d.chapeu = customizacao.get('cosmetico_cabeca')
            jogador_local = d
        mundo.jogadores.append(d)

    n_humanos = len(mundo.jogadores)
    for i in range(n_humanos, MAX_JOGADORES):
        k = i - n_humanos
        b = Duelista(i, NOMES_BOTS[k % len(NOMES_BOTS)],
                     CORES_BOTS[k % len(CORES_BOTS)], is_bot=True)
        mundo.jogadores.append(b)

    if jogador_local is None:                    # single player / fallback
        jogador_local = mundo.jogadores[0]
        jogador_local.is_local = True
        jogador_local.is_remote = False
    mundo.idx_local = jogador_local.idx
    jl = jogador_local

    jogadores_por_pid = {p.player_id: p for p in mundo.jogadores
                         if not p.is_bot and p.player_id is not None}

    num_bots = max(0, min(MAX_JOGADORES - n_humanos, 5 if n_humanos <= 2 else 3))

    def _aplicar_ativos():
        for k, p in enumerate(mundo.jogadores):
            p.ativo = (k < n_humanos + num_bots)

    _aplicar_ativos()
    for i, p in enumerate(mundo.jogadores):
        sx, sz, syaw = SPAWNS[i % len(SPAWNS)]
        p.x, p.z, p.yaw = sx, sz, syaw
        p.alvo_x, p.alvo_z, p.alvo_yaw = sx, sz, syaw

    # ---------- estado ----------
    estado = "SETUP"
    tempo_estado = pygame.time.get_ticks()
    restante = TEMPO_PARTIDA
    fim_partida = 0
    sel_arma = 0
    jl.aplicar_arma(sel_arma)
    cards = _cards_armas()
    rodape_y = 528
    botoes_bots = (pygame.Rect(LARGURA - 240, rodape_y + 40, 40, 34),
                   pygame.Rect(LARGURA - 140, rodape_y + 40, 40, 34))

    cam = Camera(jl.x, jl.y + OLHO_Y, jl.z, jl.yaw)
    rend = Renderer3D(LARGURA, ALTURA_JOGO)
    ceu = gerar_ceu(random.Random(4242))

    mouse_preso = False
    ultimo_snapshot = 0
    ultimo_input = 0
    ultimo_loadout = 0
    recuo = 0.0
    recuo_pitch = 0.0
    flash_arma = 0.0
    spin = 0.0
    bob_fase = 0.0
    sway_x = sway_y = 0.0
    mostrar_placar = False

    def _prender(v):
        nonlocal mouse_preso
        if v == mouse_preso:
            return
        mouse_preso = v
        pygame.mouse.set_visible(not v)
        pygame.event.set_grab(v)
        if v:
            pygame.mouse.get_rel()

    def _sair():
        _prender(False)
        pygame.mouse.set_visible(True)
        try:
            pygame.event.set_grab(False)
        except Exception:
            pass

    def _enviar(dados):
        if cliente:
            try:
                cliente.send_minigame_action(dados)
            except Exception:
                pass

    def _sortear_armas_bots():
        """Host: dá uma arma a cada bot (feito antes da INTRO, pra aparecer lá)."""
        for p in mundo.jogadores:
            if p.is_bot:
                p.aplicar_arma(rng.randrange(len(ARMAS)))

    def _iniciar_partida(tempo):
        """Só o host chama: posiciona todo mundo e zera o placar."""
        nonlocal fim_partida
        for p in mundo.jogadores:
            p.kills = 0
            p.mortes = 0
            p.morto_por = -1
            if p.ativo:
                _nascer(p, mundo.jogadores, rng, tempo)
                _emitir(mundo, {'k': 'sp', 'p': [round(p.x, 2), round(p.y, 2),
                                                 round(p.z, 2)], 'i': p.idx}, tempo)
            else:
                p.vivo = False
        mundo.foguetes.clear()
        fim_partida = tempo + TEMPO_PARTIDA

    def _tentar_atirar(tempo, segurando):
        """Dispara com a arma do jogador local (predição + pedido ao host)."""
        nonlocal recuo, flash_arma, recuo_pitch
        if estado != "FIGHT" or not jl.vivo:
            return
        arma = jl.arma()
        if not arma['auto'] and segurando:
            return
        jl.atualizar_recarga(tempo)
        if tempo < jl.recarregando_ate:
            return
        if jl.municao <= 0:
            jl.iniciar_recarga(tempo)
            return
        if tempo - jl.ultimo_tiro < arma['cd']:
            return

        origem = jl.olho()
        direcao = jl.direcao()
        recuo = 1.0
        flash_arma = 1.0
        recuo_pitch += arma['kick'] * 0.012
        mundo.shake = min(10.0, mundo.shake + arma['kick'] * 0.8)
        _tocar('tiro', 0.16, 1)

        if host:
            _disparar(mundo, jl, origem, direcao, tempo, rng)
        else:
            # Cliente: consome munição/cooldown local e prevê o rastro
            jl.ultimo_tiro = tempo
            jl.municao -= 1
            _tracers_locais(mundo, jl, origem, direcao, tempo, rng)
            _enviar({'action': 'd3_fire',
                     'o': [round(origem[0], 2), round(origem[1], 2), round(origem[2], 2)],
                     'd': [round(direcao[0], 4), round(direcao[1], 4), round(direcao[2], 4)]})

    # ============================================================
    while True:
        tempo = pygame.time.get_ticks()
        tempo_no_estado = tempo - tempo_estado
        dt = min(0.05, max(0.001, relogio.get_time() / 1000.0))

        mouse_botao = pygame.mouse.get_pressed()
        teclas = pygame.key.get_pressed()

        # ---------------- EVENTOS ----------------
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                _sair()
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                _sair()
                return None

            if estado == "SETUP":
                if ev.type == pygame.KEYDOWN:
                    if pygame.K_1 <= ev.key <= pygame.K_5:
                        idx = ev.key - pygame.K_1
                        if idx < len(ARMAS):
                            sel_arma = idx
                            jl.aplicar_arma(idx)
                            jl.pronto = True
                            ultimo_loadout = 0
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        if host:
                            num_bots = min(MAX_JOGADORES - n_humanos, num_bots + 1)
                            _aplicar_ativos()
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        if host:
                            num_bots = max(0, num_bots - 1)
                            _aplicar_ativos()
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        jl.pronto = True
                        ultimo_loadout = 0
                        if host:
                            estado = "INTRO"
                            tempo_estado = tempo
                            _sortear_armas_bots()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mp = convert_mouse_position(ev.pos)
                    for i, r in enumerate(cards):
                        if r.collidepoint(mp):
                            sel_arma = i
                            jl.aplicar_arma(i)
                            jl.pronto = True
                            ultimo_loadout = 0
                            break
                    if host:
                        if botoes_bots[0].collidepoint(mp):
                            num_bots = max(0, num_bots - 1)
                            _aplicar_ativos()
                        elif botoes_bots[1].collidepoint(mp):
                            num_bots = min(MAX_JOGADORES - n_humanos, num_bots + 1)
                            _aplicar_ativos()

            elif estado == "FIGHT":
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_r:
                        jl.iniciar_recarga(tempo)
                    elif ev.key == pygame.K_TAB:
                        mostrar_placar = True
                elif ev.type == pygame.KEYUP and ev.key == pygame.K_TAB:
                    mostrar_placar = False
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    _tentar_atirar(tempo, False)

        # ---------------- REDE: RECEBER ----------------
        if cliente:
            acoes = cliente.get_minigame_actions()
            if host:
                for acao in acoes:
                    p = jogadores_por_pid.get(acao.get('player_id'))
                    if p is None or p is jl:
                        continue
                    act = acao.get('action')
                    if act == 'd3_in':
                        p.alvo_x = float(acao.get('x', p.alvo_x))
                        p.alvo_y = float(acao.get('y', p.alvo_y))
                        p.alvo_z = float(acao.get('z', p.alvo_z))
                        p.alvo_yaw = float(acao.get('yw', p.alvo_yaw))
                        lim = ARENA - RAIO_JOGADOR
                        p.alvo_x = max(-lim, min(lim, p.alvo_x))
                        p.alvo_z = max(-lim, min(lim, p.alvo_z))
                        p.alvo_y = max(0.0, min(PAREDE_H, p.alvo_y))
                    elif act == 'd3_fire':
                        if estado == "FIGHT" and p.vivo:
                            arma = p.arma()
                            # rate-limit tolerante (latência) para não virar turbo
                            if tempo - p.ultimo_tiro >= arma['cd'] * 0.7:
                                o = acao.get('o') or list(p.olho())
                                d = acao.get('d') or list(p.direcao())
                                _disparar(mundo, p, (float(o[0]), float(o[1]), float(o[2])),
                                          normalizar((float(d[0]), float(d[1]), float(d[2]))),
                                          tempo, rng)
                    elif act == 'd3_load':
                        w = int(acao.get('w', 0))
                        if 0 <= w < len(ARMAS) and w != p.arma_idx:
                            p.aplicar_arma(w)
                        cor = acao.get('cor')
                        if cor and len(cor) == 3:
                            p.cor = tuple(int(c) for c in cor)
                        p.chapeu = acao.get('ht')
                        p.pronto = bool(acao.get('pr', 1))
            else:
                snaps = [a for a in acoes if a.get('action') == 'd3_state']
                if snaps:
                    # Se chegou mais de um snapshot no mesmo frame, só o último
                    # vale como estado — mas os EFEITOS de todos são aplicados,
                    # senão perdemos rastros e kills num engasgo de rede.
                    for antigo in snaps[:-1]:
                        for ev in antigo.get('fx', []):
                            _aplicar_fx(mundo, ev, tempo, remoto=True)
                    novo_estado, restante, novo_nb = _aplicar_snapshot(mundo, snaps[-1],
                                                                       tempo, jl)
                    if novo_nb != num_bots:
                        num_bots = novo_nb
                    if novo_estado and novo_estado != estado:
                        estado = novo_estado
                        tempo_estado = tempo
                        if estado == "FIGHT":
                            recuo_pitch = 0.0
                            mundo.tracers.clear()

        # ---------------- MÁQUINA DE ESTADOS (host) ----------------
        if host:
            if estado == "SETUP":
                restante = max(0, TEMPO_SETUP - tempo_no_estado)
                if tempo_no_estado >= TEMPO_SETUP:
                    estado = "INTRO"
                    tempo_estado = tempo
                    _sortear_armas_bots()
            elif estado == "INTRO":
                if tempo_no_estado >= TEMPO_INTRO:
                    estado = "TRANSICAO"
                    tempo_estado = tempo
            elif estado == "TRANSICAO":
                if tempo_no_estado >= TEMPO_TRANSICAO:
                    estado = "FIGHT"
                    tempo_estado = tempo
                    _iniciar_partida(tempo)
            elif estado == "FIGHT":
                restante = max(0, fim_partida - tempo)
        else:
            if estado == "SETUP":
                restante = max(0, TEMPO_SETUP - tempo_no_estado)

        # O mouse fica preso a partida inteira (inclusive com o placar aberto):
        # soltar o grab no meio da luta joga o cursor do sistema pra tela.
        _prender(estado == "FIGHT")

        # ---------------- OLHAR (mouse) ----------------
        mdx, mdy = pygame.mouse.get_rel()
        if estado == "FIGHT" and mouse_preso and jl.vivo:
            jl.yaw = (jl.yaw + mdx * SENS) % math.tau
            jl.pitch = max(-1.35, min(1.35, jl.pitch - mdy * SENS))
            sway_x += (-mdx * 0.35 - sway_x) * 0.12
            sway_y += (-mdy * 0.25 - sway_y) * 0.12
        else:
            sway_x *= 0.9
            sway_y *= 0.9
        sway_x = max(-26, min(26, sway_x))
        sway_y = max(-18, min(18, sway_y))

        # ---------------- SIMULAÇÃO ----------------
        if estado == "FIGHT":
            jl.atualizar_recarga(tempo)
            if jl.vivo:
                fh = (math.sin(jl.yaw), math.cos(jl.yaw))
                rt = (math.cos(jl.yaw), -math.sin(jl.yaw))
                mx = mz = 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                    mx += fh[0]; mz += fh[1]
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                    mx -= fh[0]; mz -= fh[1]
                if teclas[pygame.K_d]:
                    mx += rt[0]; mz += rt[1]
                if teclas[pygame.K_a]:
                    mx -= rt[0]; mz -= rt[1]
                mag = math.hypot(mx, mz)
                if mag > 0:
                    mx /= mag
                    mz /= mag
                correr = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
                vel = VEL_SPRINT if (correr and mag > 0) else VEL_ANDAR
                pular = teclas[pygame.K_SPACE]
                _fisica(jl, mx, mz, vel, dt, pular)
                if mag > 0 and jl.no_chao:
                    bob_fase += dt * (9.0 if correr else 6.5)
                # Tiro contínuo (armas automáticas)
                if mouse_botao[0] and jl.arma()['auto']:
                    _tentar_atirar(tempo, True)
            else:
                jl.vel_atual = 0.0

            if host:
                for p in mundo.jogadores:
                    if p.is_bot and p.ativo and p.vivo:
                        _bot_pensar(p, mundo, dt, tempo, rng)
                _atualizar_foguetes(mundo, dt, tempo, rng)
                # Respawns
                for p in mundo.jogadores:
                    if p.ativo and not p.vivo and p.respawn_em and tempo >= p.respawn_em:
                        p.respawn_em = 0
                        _nascer(p, mundo.jogadores, rng, tempo)
                        _emitir(mundo, {'k': 'sp', 'p': [round(p.x, 2), round(p.y, 2),
                                                         round(p.z, 2)], 'i': p.idx}, tempo)
                # Fim de partida
                lider = max((p.kills for p in mundo.jogadores if p.ativo), default=0)
                if lider >= FRAG_LIMITE or tempo >= fim_partida:
                    estado = "FIM"
                    tempo_estado = tempo
                    restante = 0
                    _prender(False)

        elif estado == "FIM":
            if tempo_no_estado >= TEMPO_FIM:
                _sair()
                return None

        _interpolar(mundo, dt, host)
        _atualizar_particulas(mundo, dt)

        # Limpeza de efeitos temporários
        mundo.tracers = [t for t in mundo.tracers if tempo < t['ate']]
        mundo.explosoes = [e for e in mundo.explosoes if tempo < e['ate']]
        mundo.dano_flutuante = [d for d in mundo.dano_flutuante if tempo < d['ate']]
        mundo.indicadores_dano = [i for i in mundo.indicadores_dano if tempo < i['ate']]
        if len(mundo.killfeed) > 12:
            del mundo.killfeed[:-12]
        mundo.shake *= max(0.0, 1.0 - dt * 7.0)
        recuo *= max(0.0, 1.0 - dt * 9.0)
        flash_arma *= max(0.0, 1.0 - dt * 14.0)
        recuo_pitch *= max(0.0, 1.0 - dt * 6.0)
        spin += dt * (26.0 if (mouse_botao[0] and jl.arma()['id'] == 'vortex') else 4.0)

        # ---------------- REDE: ENVIAR ----------------
        if cliente and host:
            # Os efeitos acumulam entre os snapshots (60fps de jogo, 30Hz de rede)
            if tempo - ultimo_snapshot >= INTERVALO_SNAPSHOT:
                ultimo_snapshot = tempo
                _enviar(_construir_snapshot(mundo, estado, restante, num_bots))
                mundo.fx_pendentes.clear()
        elif cliente:
            if estado == "FIGHT" and jl.vivo and tempo - ultimo_input >= INTERVALO_INPUT:
                ultimo_input = tempo
                _enviar({'action': 'd3_in', 'x': round(jl.x, 2), 'y': round(jl.y, 2),
                         'z': round(jl.z, 2), 'yw': round(jl.yaw, 3)})
            if estado in ("SETUP", "INTRO") and tempo - ultimo_loadout >= INTERVALO_LOADOUT:
                ultimo_loadout = tempo
                _enviar({'action': 'd3_load', 'w': jl.arma_idx, 'cor': list(jl.cor),
                         'ht': jl.chapeu, 'pr': 1 if jl.pronto else 0})
            mundo.fx_pendentes.clear()
        else:
            mundo.fx_pendentes.clear()      # single player: nada a transmitir

        # ---------------- CÂMERA ----------------
        if jl.vivo or estado != "FIGHT":
            bob = math.sin(bob_fase) * 0.045 if jl.no_chao else 0.0
            cam.x = jl.x
            cam.y = jl.y + OLHO_Y + bob
            cam.z = jl.z
            cam.yaw = jl.yaw
            cam.pitch = max(-1.4, min(1.4, jl.pitch + recuo_pitch))
        else:
            # Câmera de morte: orbita o local da morte olhando pro assassino
            alvo = None
            if 0 <= jl.morto_por < len(mundo.jogadores):
                alvo = mundo.jogadores[jl.morto_por]
            orb = tempo / 1400.0
            cam.x = jl.x + math.cos(orb) * 3.2
            cam.z = jl.z + math.sin(orb) * 3.2
            cam.y = jl.y + 2.8
            if alvo is not None and alvo is not jl:
                cam.yaw = math.atan2(alvo.x - cam.x, alvo.z - cam.z)
                cam.pitch = -0.18
            else:
                cam.yaw = math.atan2(jl.x - cam.x, jl.z - cam.z)
                cam.pitch = -0.55
        if mundo.shake > 0.05:
            cam.x += rng.uniform(-1, 1) * mundo.shake * 0.006
            cam.y += rng.uniform(-1, 1) * mundo.shake * 0.006
            cam.z += rng.uniform(-1, 1) * mundo.shake * 0.006

        # ---------------- DESENHO ----------------
        if estado == "SETUP":
            mp = convert_mouse_position(pygame.mouse.get_pos())
            pygame.mouse.set_visible(True)
            _desenhar_setup(tela, mundo, jl, cards, sel_arma, mp, host, num_bots,
                            restante, fontes_tela, tempo, botoes_bots)

        elif estado == "INTRO":
            pygame.mouse.set_visible(False)
            _desenhar_intro(tela, gradiente_jogo, mundo, tempo_no_estado, fontes_tela, tempo)

        elif estado == "TRANSICAO":
            _desenhar_transicao(tela, min(1.0, tempo_no_estado / TEMPO_TRANSICAO), fontes_tela)

        else:
            # ---- Mundo 3D ----
            tela.set_clip(pygame.Rect(0, 0, LARGURA, ALTURA_JOGO))
            rend.iniciar(cam)
            desenhar_ceu(tela, rend, cam, ceu, tempo)
            desenhar_arena(rend, cam, tempo)

            for p in mundo.jogadores:
                if not p.ativo or not p.vivo or p is jl:
                    continue
                desenhar_personagem(rend, cam, p, tempo, ARMAS[p.arma_idx]['cor'])

            foguetes = ([(f.x, f.y, f.z) for f in mundo.foguetes] if host
                        else mundo.foguetes_render)
            for fpos in foguetes:
                rend.orb(fpos, 0.24, (255, 150, 220))
                rend.blob(fpos, 0.75, (255, 90, 190), 70)

            for tr in mundo.tracers:
                restante_tr = max(0, tr['ate'] - tempo)
                alpha = int(255 * min(1.0, restante_tr / 90.0))
                rend.feixe(tr['a'], tr['b'], tr['c'], tr['lg'], alpha)

            for ex in mundo.explosoes:
                dur = max(1, ex['ate'] - ex['ini'])
                t = min(1.0, (tempo - ex['ini']) / dur)
                raio = ex['r'] * (0.32 + 0.68 * t)
                rend.blob(ex['p'], raio, (255, int(190 - 130 * t), 70), int(115 * (1 - t)))
                rend.blob(ex['p'], raio * 0.62, (255, int(210 - 120 * t), 110),
                          int(90 * (1 - t)))
                if t < 0.35:
                    rend.orb(ex['p'], raio * 0.30, (255, 240, 190))

            for pa in mundo.particulas:
                frac = pa['vida'] / pa['max']
                rend.orb(pa['p'], pa['r'] * (0.4 + 0.6 * frac), pa['c'], brilho=False)

            rend.desenhar(tela)

            if estado == "FIGHT":
                _desenhar_nametags(tela, rend, mundo, jl, f_nome)
                _desenhar_dano_flutuante(tela, rend, mundo, tempo, f_dano, f_hs)

            # ---- Viewmodel ----
            if estado == "FIGHT" and jl.vivo:
                arma = jl.arma()
                # Balanço no formato do DOOM, com força proporcional à velocidade
                forca_bob = min(1.0, jl.vel_atual / VEL_ANDAR) if jl.no_chao else 0.25
                dbx, dby = _bob_doom(bob_fase, forca_bob)
                bob_x = dbx + sway_x
                bob_y = dby + sway_y * 0.6
                frac_rec = 0.0
                if tempo < jl.recarregando_ate:
                    frac_rec = 1.0 - (jl.recarregando_ate - tempo) / max(1, arma['recarga'])
                boca = _viewmodel(tela, jl.arma_idx, tempo, recuo, bob_x, bob_y,
                                  frac_rec, spin, jl.cor)
                _muzzle_flash(tela, boca, arma['cor'], flash_arma)

            tela.set_clip(None)

            # ---- HUD ----
            if estado == "FIGHT":
                if tempo < mundo.flash_dano_ate:
                    # Tinta vermelha curta (como a paleta de dano do DOOM), mas
                    # leve o bastante para ainda dar pra jogar enquanto pisca
                    f = (mundo.flash_dano_ate - tempo) / 260.0
                    s = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
                    s.fill((190, 20, 20, int(58 * f)))
                    pygame.draw.rect(s, (150, 0, 0, int(70 * f)),
                                     (0, 0, LARGURA, ALTURA_JOGO), 70)
                    tela.blit(s, (0, 0))
                if jl.hp < 35 and jl.vivo:
                    pulso = 0.5 + 0.5 * math.sin(tempo / 260.0)
                    vin = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
                    pygame.draw.rect(vin, (150, 0, 0, int(26 + 30 * pulso)),
                                     (0, 0, LARGURA, ALTURA_JOGO), 55)
                    tela.blit(vin, (0, 0))

                if jl.vivo:
                    arma = jl.arma()
                    espalha = arma['spread_mov'] if jl.vel_atual > 1.0 else arma['spread']
                    alvo_mira = False
                    ponto, acertos = _raycast(mundo, jl.olho(), jl.direcao(), jl,
                                              arma['alcance'], False)
                    alvo_mira = bool(acertos)
                    rec = 0.0
                    if tempo < jl.recarregando_ate:
                        rec = 1.0 - (jl.recarregando_ate - tempo) / max(1, arma['recarga'])
                    _desenhar_mira(tela, LARGURA // 2, ALTURA_JOGO // 2, espalha,
                                   alvo_mira, tempo < mundo.hitmarker_ate,
                                   mundo.hitmarker_kill, rec)
                    _desenhar_indicadores_dano(tela, mundo, jl, tempo)
                else:
                    ov = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
                    ov.fill((45, 0, 0, 55))
                    pygame.draw.rect(ov, (90, 0, 0, 110), (0, 0, LARGURA, ALTURA_JOGO), 90)
                    tela.blit(ov, (0, 0))
                    _texto(tela, f_titulo, "ELIMINADO", LARGURA // 2, ALTURA_JOGO // 2 - 90,
                           (255, 90, 90), True)
                    if 0 <= jl.morto_por < len(mundo.jogadores) and jl.morto_por != jl.idx:
                        alg = mundo.jogadores[jl.morto_por]
                        _texto(tela, f_media, f"por {alg.nome} ({ARMAS[alg.arma_idx]['nome']})",
                               LARGURA // 2, ALTURA_JOGO // 2 - 24, alg.cor, True)
                    seg_resp = max(0, (jl.respawn_em - tempo)) if jl.respawn_em else 0
                    _texto(tela, f_grande, "Renascendo em %.1fs" % (seg_resp / 1000.0),
                           LARGURA // 2, ALTURA_JOGO // 2 + 30, (230, 230, 240), True)

                _desenhar_killfeed(tela, mundo, tempo, f_peq)
                _desenhar_radar(tela, mundo, jl, f_peq)
                _desenhar_placar_mini(tela, mundo, jl, f_peq)
                _desenhar_barra_hud(tela, mundo, jl, tempo, restante, fontes_hud)

                if tempo_no_estado < 6000:
                    alpha = 255 if tempo_no_estado < 4000 else int(255 * (1 - (tempo_no_estado - 4000) / 2000))
                    dica = f_peq.render(
                        "WASD mover  |  SHIFT correr  |  ESPACO pular  |  CLIQUE atirar  |  R recarregar  |  TAB placar",
                        True, (170, 200, 220))
                    dica.set_alpha(max(0, alpha))
                    # Acima da arma: embaixo o viewmodel come o texto
                    tela.blit(dica, (LARGURA // 2 - dica.get_width() // 2,
                                     ALTURA_JOGO // 2 + 96))

                if mostrar_placar:
                    _desenhar_placar(tela, mundo, fontes_tela, tempo, False, restante)

                if tempo_no_estado < 400:
                    f = pygame.Surface((LARGURA, ALTURA))
                    f.fill((255, 255, 255))
                    f.set_alpha(int(255 * (1 - tempo_no_estado / 400.0)))
                    tela.blit(f, (0, 0))

            elif estado == "FIM":
                _desenhar_placar(tela, mundo, fontes_tela, tempo, True)

        present_frame()
        relogio.tick(FPS)
