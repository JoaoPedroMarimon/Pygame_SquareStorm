#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame BoxFight - Construcao e Combate.
8 jogadores (humanos + bots), arena colorida com camera.
Jogadores constroem paredes (Q) e atiram com SPAS ou Metralhadora (E).
Paredes tem 10 HP e sao destruidas por tiros.
Bots constroem e atiram automaticamente.
"""

import pygame
import math
import random
from src.config import *
from src.entities.particula import Particula
from src.utils.visual import criar_mira, desenhar_mira
from src.utils.display_manager import present_frame, convert_mouse_position
from src.weapons.spas12 import desenhar_spas12
from src.weapons.metralhadora import desenhar_metralhadora

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
HP_MAX = 3
NUM_RODADAS = 3

PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Arena grande (igual ao Sabers)
ARENA_W = 3000
ARENA_H = 2000

# Grid de construcao
GRID_SIZE = 80
GRID_COLS = ARENA_W // GRID_SIZE   # 37
GRID_ROWS = ARENA_H // GRID_SIZE   # 25

# Paredes
PAREDE_HP_MAX = 10
PAREDE_ESPESSURA = 12
PAREDE_DANO_SPAS = 4
PAREDE_DANO_MET = 1

# Secoes de parede (cada parede se divide em N segmentos editaveis individualmente)
SECOES_POR_PAREDE = 4
SECAO_TAMANHO = GRID_SIZE // SECOES_POR_PAREDE  # 20px por secao

# Distancia maxima para construir/editar a partir do centro do jogador
BUILD_MAX_DIST = 220

# Spawn points em circulo
SPAWN_RAIO = 600
SPAWN_POINTS = []
for _i in range(8):
    _ang = (2 * math.pi * _i) / 8
    _sx = ARENA_W // 2 + int(math.cos(_ang) * SPAWN_RAIO) - TAM_JOGADOR // 2
    _sy = ARENA_H // 2 + int(math.sin(_ang) * SPAWN_RAIO) - TAM_JOGADOR // 2
    SPAWN_POINTS.append((_sx, _sy))

# Tempos de estado (ms)
TEMPO_INTRO = 2000
TEMPO_COUNTDOWN = 3000
TEMPO_ROUND_END = 2500
TEMPO_SCOREBOARD = 5000

# Velocidade
VEL_BOXFIGHT = 3.5

# Cura
CURA_DURACAO = 2500   # ms segurando F para curar completamente


# Armas: None -> sem arma, 'spas', 'metralhadora'
ARMAS = {
    None: {
        'nome': 'Nenhuma',
        'cooldown': 9999,
        'velocidade_proj': 0,
        'dano_player': 0,
        'dano_parede': 0,
        'raio_proj': 4,
        'cor_proj': (200, 200, 200),
        'espalhamento': 0.0,
        'num_pellets': 1,
    },
    'spas': {
        'nome': 'SPAS-12',
        'cooldown': 650,
        'velocidade_proj': 11,
        'dano_player': 2,
        'dano_parede': PAREDE_DANO_SPAS,
        'raio_proj': 5,
        'cor_proj': (255, 140, 40),
        'espalhamento': 0.22,
        'num_pellets': 5,
    },
    'metralhadora': {
        'nome': 'Metralhadora',
        'cooldown': 110,
        'velocidade_proj': 14,
        'dano_player': 1,
        'dano_parede': PAREDE_DANO_MET,
        'raio_proj': 4,
        'cor_proj': (255, 255, 60),
        'espalhamento': 0.05,
        'num_pellets': 1,
    },
}

# Bot AI
BOT_STRAFE_INTERVALO = 700
BOT_DIST_IDEAL = 160
BOT_DIST_RECUAR = 60
BOT_DIST_AVANCAR = 160
BOT_BUILD_CHANCE = 0.0015
BOT_BUILD_DURACAO = 900
BOT_SHOOT_BASE_DELAY = 280
BOT_RUSH_CONSTRUIR_DUR = 230   # ms parado construindo a box
BOT_RUSH_AVANCAR_DUR   = 580   # ms max avancando antes de nova box
BOT_RUSH_CHANCE        = 0.0015  # chance por frame de re-entrar em rush durante a partida

# Superfície temporária para desenhar armas (igual ao padrão do Deadeye)
_SURF_ARMA_TAM   = 120
_SURF_ARMA_ESCALA = 0.65   # 120 * 0.65 ≈ 78px centrado no player de 30px

# Minimap
MINIMAP_W = 160
MINIMAP_H = int(MINIMAP_W * ARENA_H / ARENA_W)
MINIMAP_X = LARGURA - MINIMAP_W - 10
MINIMAP_Y = 10

# Paleta neon para os quadrados do arena (colorido!)
PALETA_ARENA_NEON = [
    (255, 40,  100),   # rosa neon
    (40,  255, 120),   # verde neon
    (40,  140, 255),   # azul neon
    (255, 220, 30),    # amarelo neon
    (200, 40,  255),   # roxo neon
    (30,  230, 230),   # ciano neon
    (255, 110, 30),    # laranja neon
    (255, 60,  200),   # magenta neon
    (120, 255, 60),    # lima neon
    (60,  180, 255),   # celeste neon
]


# ============================================================
#  CLASSE JOGADOR
# ============================================================

class JogadorBoxFight:
    """Jogador no minigame BoxFight."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_remote = is_remote
        self.hp = HP_MAX
        self.vivo = True
        self.kills = 0
        self.rodadas_vencidas = 0

        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.mira_x = 0.0
        self.mira_y = 0.0

        self.arma = None
        self.tempo_ultimo_tiro = 0
        self.em_construcao = False
        self.modo_edicao = False
        self.estado_pre_edicao = None  # 'construcao' ou 'arma' — estado antes do modo edicao

        self.invulneravel_ate = 0

        self.cura_usado = False
        self.cura_inicio = 0
        self.cura_ativo = False

        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

        # Bot AI
        self.bot_alvo = None
        self.bot_strafe_timer = 0
        self.bot_strafe_dir = 1
        self.bot_build_timer = 0
        self.bot_shoot_timer = 0
        self.bot_edit_timer = 0

        # Rush mode
        self.bot_rush_ativo = False
        self.bot_rush_alvo  = None
        self.bot_rush_fase  = 'construir'  # 'construir' | 'editar' | 'avancar'
        self.bot_rush_timer = 0
        self.bot_rush_celula_ini = (0, 0)

        # Modo evacuacao (cura)
        self.bot_evacuando = False

    def reset_rodada(self, spawn_x, spawn_y):
        self.hp = HP_MAX
        self.vivo = True
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.invulneravel_ate = 0
        self.em_construcao = False
        self.modo_edicao = False
        self.estado_pre_edicao = None
        self.cura_usado = False
        self.cura_inicio = 0
        self.cura_ativo = False
        self.tempo_ultimo_tiro = 0
        self.bot_alvo = None
        self.bot_strafe_timer = 0
        self.bot_build_timer = 0
        self.bot_edit_timer = 0
        self.bot_rush_ativo = False
        self.bot_rush_alvo  = None
        self.bot_rush_fase  = 'construir'
        self.bot_rush_timer = 0
        self.bot_rush_celula_ini = (0, 0)
        self.bot_evacuando = False

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)

    def get_centro(self):
        return (self.x + TAM_JOGADOR // 2, self.y + TAM_JOGADOR // 2)

    def desenhar(self, tela, fonte, cam_x, cam_y):
        if not self.vivo:
            return
        tam = TAM_JOGADOR
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if sx < -tam - 10 or sx > LARGURA + tam or sy < -tam - 10 or sy > ALTURA_JOGO + tam:
            return

        tempo = pygame.time.get_ticks()
        if tempo < self.invulneravel_ate and (tempo // 80) % 2 == 0:
            return

        # Anel de modo construcao
        if self.em_construcao:
            pulso = int(180 + 75 * math.sin(tempo / 200))
            pygame.draw.circle(tela, (50, pulso, 50),
                               (sx + tam // 2, sy + tam // 2), tam // 2 + 6, 2)

        # Simbolo de cura (+) acima do jogador
        if self.cura_ativo:
            cx_h = sx + tam // 2
            cy_h = sy - 26
            pulso_c = int(160 + 95 * abs(math.sin(tempo / 150)))
            cor_c = (50, pulso_c, 80)
            pygame.draw.rect(tela, cor_c, (cx_h - 9, cy_h - 3, 18, 6), 0, 2)
            pygame.draw.rect(tela, cor_c, (cx_h - 3, cy_h - 9, 6, 18), 0, 2)

        # Sombra
        pygame.draw.rect(tela, (15, 12, 20), (sx + 3, sy + 3, tam, tam), 0, 3)
        # Cor escura
        pygame.draw.rect(tela, self.cor_escura, (sx, sy, tam, tam), 0, 5)
        # Cor principal
        pygame.draw.rect(tela, self.cor, (sx + 2, sy + 2, tam - 4, tam - 4), 0, 3)
        # Highlight
        pygame.draw.rect(tela, self.cor_brilhante, (sx + 4, sy + 4, 7, 7), 0, 2)

        # Nome
        nome_surf = fonte.render(self.nome, True, BRANCO)
        nx = sx + tam // 2 - nome_surf.get_width() // 2
        ny = sy - 16
        bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        tela.blit(bg, (nx - 3, ny - 1))
        tela.blit(nome_surf, (nx, ny))

        # Barra de HP
        hp_w = tam
        hp_h = 4
        hp_x = sx
        hp_y = sy + tam + 4
        pygame.draw.rect(tela, (40, 40, 40), (hp_x, hp_y, hp_w, hp_h), 0, 2)
        hp_ratio = max(0, self.hp / HP_MAX)
        cor_hp = VERDE if hp_ratio > 0.5 else VERMELHO
        pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h), 0, 2)

        # Barra de progresso de cura abaixo do HP
        if self.cura_ativo and self.cura_inicio > 0:
            progresso = min(1.0, (pygame.time.get_ticks() - self.cura_inicio) / CURA_DURACAO)
            cy_bar = hp_y + hp_h + 3
            pygame.draw.rect(tela, (20, 55, 30), (hp_x, cy_bar, hp_w, 4), 0, 2)
            pygame.draw.rect(tela, (80, 255, 120), (hp_x, cy_bar, int(hp_w * progresso), 4), 0, 2)


# ============================================================
#  CAMERA
# ============================================================

def _atualizar_camera(jogador, cam_x, cam_y):
    """Camera suave seguindo o jogador (igual ao Sabers)."""
    alvo_x = jogador.x + TAM_JOGADOR // 2 - LARGURA // 2
    alvo_y = jogador.y + TAM_JOGADOR // 2 - ALTURA_JOGO // 2
    cam_x += (alvo_x - cam_x) * 0.08
    cam_y += (alvo_y - cam_y) * 0.08
    cam_x = max(0, min(cam_x, ARENA_W - LARGURA))
    cam_y = max(0, min(cam_y, ARENA_H - ALTURA_JOGO))
    return cam_x, cam_y


# ============================================================
#  ARENA COLORIDA
# ============================================================

def _desenhar_arena_boxfight(tela, cam_x, cam_y, tempo):
    """Desenha a arena com quadrados neon coloridos."""
    tela.fill((6, 6, 14))

    start_gx = max(0, int(cam_x // GRID_SIZE) * GRID_SIZE)
    start_gy = max(0, int(cam_y // GRID_SIZE) * GRID_SIZE)
    end_gx = min(ARENA_W, int((cam_x + LARGURA) // GRID_SIZE + 2) * GRID_SIZE)
    end_gy = min(ARENA_H, int((cam_y + ALTURA_JOGO) // GRID_SIZE + 2) * GRID_SIZE)

    pulso = (math.sin(tempo / 1200) + 1) / 2

    for gy in range(start_gy, end_gy, GRID_SIZE):
        for gx in range(start_gx, end_gx, GRID_SIZE):
            sx = int(gx - cam_x)
            sy = int(gy - cam_y)

            cell_x = gx // GRID_SIZE
            cell_y = gy // GRID_SIZE

            # Cor base deterministica por celula
            cor_idx = (cell_x * 7 + cell_y * 13 + cell_x * cell_y * 3) % len(PALETA_ARENA_NEON)
            cor_base = PALETA_ARENA_NEON[cor_idx]

            # Fator de escurecimento - quadrados sao coloridos mas nao ofuscantes
            fator = 0.10 + 0.035 * pulso
            cor_cell = tuple(int(c * fator) for c in cor_base)
            pygame.draw.rect(tela, cor_cell, (sx, sy, GRID_SIZE, GRID_SIZE))

            # Borda da celula (grade neon)
            fator_borda = 0.30 + 0.10 * pulso
            cor_borda = tuple(int(c * fator_borda) for c in cor_base)
            pygame.draw.rect(tela, cor_borda, (sx, sy, GRID_SIZE, GRID_SIZE), 1)

    # Glow nas linhas de grade
    pulso_grade = (math.sin(tempo / 700) + 1) / 2
    alpha_g = int(18 + pulso_grade * 14)
    for gy in range(0, ARENA_H, GRID_SIZE):
        sy = int(gy - cam_y)
        if -2 <= sy <= ALTURA_JOGO + 2:
            pygame.draw.line(tela, (alpha_g, alpha_g, alpha_g + 25),
                             (0, sy), (LARGURA, sy), 1)
    for gx in range(0, ARENA_W, GRID_SIZE):
        sx = int(gx - cam_x)
        if -2 <= sx <= LARGURA + 2:
            pygame.draw.line(tela, (alpha_g, alpha_g, alpha_g + 25),
                             (sx, 0), (sx, ALTURA_JOGO), 1)

    # Bordas da arena com glow
    borda_cor  = (255, 80, 80)
    borda_glow = (120, 30, 30)
    borda_gw2  = (60,  15, 15)

    def _borda_h(y_mundo):
        sy = int(y_mundo - cam_y)
        if -10 <= sy <= ALTURA_JOGO + 10:
            pygame.draw.line(tela, borda_gw2,  (0, sy - 4), (LARGURA, sy - 4), 8)
            pygame.draw.line(tela, borda_glow, (0, sy - 1), (LARGURA, sy - 1), 4)
            pygame.draw.line(tela, borda_cor,  (0, sy),     (LARGURA, sy),     2)

    def _borda_v(x_mundo):
        sx = int(x_mundo - cam_x)
        if -10 <= sx <= LARGURA + 10:
            pygame.draw.line(tela, borda_gw2,  (sx - 4, 0), (sx - 4, ALTURA_JOGO), 8)
            pygame.draw.line(tela, borda_glow, (sx - 1, 0), (sx - 1, ALTURA_JOGO), 4)
            pygame.draw.line(tela, borda_cor,  (sx, 0),     (sx, ALTURA_JOGO),     2)

    _borda_h(0)
    _borda_h(ARENA_H)
    _borda_v(0)
    _borda_v(ARENA_W)


# ============================================================
#  SISTEMA DE PAREDES
# ============================================================

def _get_secao_rects(chave, parede):
    """
    Retorna lista de (idx, Rect) para cada secao PRESENTE da parede.
    Horizontal: 4 fatias ao longo de X.
    Vertical:   4 fatias ao longo de Y.
    """
    gi, gj, orient = chave
    secoes = parede['secoes']
    rects = []
    for idx, presente in enumerate(secoes):
        if not presente:
            continue
        if orient == 'h':
            r = pygame.Rect(
                gi * GRID_SIZE + idx * SECAO_TAMANHO,
                gj * GRID_SIZE - PAREDE_ESPESSURA // 2,
                SECAO_TAMANHO,
                PAREDE_ESPESSURA,
            )
        else:
            r = pygame.Rect(
                gi * GRID_SIZE - PAREDE_ESPESSURA // 2,
                gj * GRID_SIZE + idx * SECAO_TAMANHO,
                PAREDE_ESPESSURA,
                SECAO_TAMANHO,
            )
        rects.append((idx, r))
    return rects


def _obter_secao_em(mx_world, my_world, paredes, dono, player_cx, player_cy):
    """
    Retorna (chave, idx) da secao de parede pertencente a 'dono'
    que contem o ponto (mx_world, my_world) e esta dentro de BUILD_MAX_DIST.
    Retorna (None, None) se nenhuma encontrada.
    """
    for chave, parede in paredes.items():
        if parede.get('dono') is not dono:
            continue
        for idx, sect_rect in _get_secao_rects(chave, parede):
            # Expandir ligeiramente para facilitar o clique
            hit_rect = sect_rect.inflate(4, 4)
            if hit_rect.collidepoint(mx_world, my_world):
                dx = sect_rect.centerx - player_cx
                dy = sect_rect.centery - player_cy
                if dx * dx + dy * dy <= BUILD_MAX_DIST * BUILD_MAX_DIST:
                    return chave, idx
    return None, None


def _remover_secao_parede(paredes, chave, idx):
    """Remove a secao 'idx' de uma parede. Deleta a parede se todas as secoes sumidas."""
    if chave not in paredes:
        return False
    parede = paredes[chave]
    if 0 <= idx < len(parede['secoes']):
        parede['secoes'][idx] = False
    if not any(parede['secoes']):
        del paredes[chave]
    return True


def _obter_posicao_parede(mx_world, my_world):
    """
    Dado ponto do mouse no mundo, retorna (chave, rect) da parede
    mais proxima das linhas de grade. Retorna (None, None) se fora de alcance.
    """
    THRESHOLD = GRID_SIZE * 0.32

    # Linha horizontal mais proxima
    gy_h_float = my_world / GRID_SIZE
    gy_h_idx = round(gy_h_float)
    gy_h = gy_h_idx * GRID_SIZE
    dist_h = abs(my_world - gy_h)
    gx_h_idx = int(mx_world // GRID_SIZE)

    # Linha vertical mais proxima
    gx_v_float = mx_world / GRID_SIZE
    gx_v_idx = round(gx_v_float)
    gx_v = gx_v_idx * GRID_SIZE
    dist_v = abs(mx_world - gx_v)
    gy_v_idx = int(my_world // GRID_SIZE)

    if dist_h <= dist_v and dist_h < THRESHOLD:
        gi = gx_h_idx
        gj = gy_h_idx
        if 0 <= gi < GRID_COLS and 0 <= gj <= GRID_ROWS:
            chave = (gi, gj, 'h')
            rect = pygame.Rect(
                gi * GRID_SIZE,
                gj * GRID_SIZE - PAREDE_ESPESSURA // 2,
                GRID_SIZE,
                PAREDE_ESPESSURA,
            )
            return chave, rect
    elif dist_v < THRESHOLD:
        gi = gx_v_idx
        gj = gy_v_idx
        if 0 <= gi <= GRID_COLS and 0 <= gj < GRID_ROWS:
            chave = (gi, gj, 'v')
            rect = pygame.Rect(
                gi * GRID_SIZE - PAREDE_ESPESSURA // 2,
                gj * GRID_SIZE,
                PAREDE_ESPESSURA,
                GRID_SIZE,
            )
            return chave, rect

    return None, None


def _colocar_parede(paredes, chave, rect, dono=None):
    """Coloca uma parede se a posicao estiver livre. 'dono' = jogador que construiu."""
    if chave not in paredes:
        paredes[chave] = {
            'hp': PAREDE_HP_MAX,
            'rect': pygame.Rect(rect),
            'secoes': [True] * SECOES_POR_PAREDE,
            'dono': dono,
        }
        return True
    return False


def _danificar_parede(paredes, chave, dano):
    """Danifica parede. Retorna True se foi destruida."""
    if chave not in paredes:
        return False
    paredes[chave]['hp'] -= dano
    if paredes[chave]['hp'] <= 0:
        del paredes[chave]
        return True
    return False


def _projetil_colide_parede(proj, paredes):
    """Verifica colisao do projetil com alguma secao presente. Retorna chave ou None."""
    r = proj['raio']
    proj_rect = pygame.Rect(int(proj['x']) - r, int(proj['y']) - r, r * 2, r * 2)
    for chave, parede in paredes.items():
        for _, sect_rect in _get_secao_rects(chave, parede):
            if proj_rect.colliderect(sect_rect):
                return chave
    return None


def _resolver_colisao_jogador_paredes(jogador, paredes):
    """
    Empurra o jogador para fora de qualquer parede que ele esteja colidindo.
    Resolve pelo eixo de menor sobreposicao (MTV - Minimum Translation Vector).
    Itera algumas vezes para resolver multiplas colisoes por frame.
    Bots ignoram colisao com suas proprias paredes (evita o efeito de super-dash
    causado pelo MTV quando o bot constroi paredes ao redor de si mesmo).
    """
    for _ in range(4):
        jogador_rect = jogador.get_rect()
        resolveu = False

        for chave, parede in paredes.items():
            # Em rush, bot ignora proprias paredes (evita super-dash pelo MTV
            # quando constroi a box ao redor de si mesmo)
            if jogador.is_bot and jogador.bot_rush_ativo and parede.get('dono') is jogador:
                continue
            for _, sect_rect in _get_secao_rects(chave, parede):
                if not jogador_rect.colliderect(sect_rect):
                    continue

                # Calcula sobreposicao em cada eixo/direcao
                ol_esq  = jogador_rect.right  - sect_rect.left
                ol_dir  = sect_rect.right     - jogador_rect.left
                ol_cima = jogador_rect.bottom - sect_rect.top
                ol_bx   = sect_rect.bottom    - jogador_rect.top

                min_ol = min(ol_esq, ol_dir, ol_cima, ol_bx)

                if min_ol <= 0:
                    continue

                if min_ol == ol_esq:
                    jogador.x -= ol_esq
                    if jogador.vx > 0:
                        jogador.vx = 0
                elif min_ol == ol_dir:
                    jogador.x += ol_dir
                    if jogador.vx < 0:
                        jogador.vx = 0
                elif min_ol == ol_cima:
                    jogador.y -= ol_cima
                    if jogador.vy > 0:
                        jogador.vy = 0
                else:
                    jogador.y += ol_bx
                    if jogador.vy < 0:
                        jogador.vy = 0

                jogador_rect = jogador.get_rect()
                resolveu = True

        if not resolveu:
            break


def _desenhar_paredes(tela, paredes, cam_x, cam_y, dono_edicao=None, drag_secoes=None):
    """
    Desenha todas as paredes secao por secao.
    dono_edicao: jogador em modo edicao — suas paredes aparecem em azul.
    drag_secoes: set de (chave, idx) selecionados via drag — aparecem em cinza.
    """
    if drag_secoes is None:
        drag_secoes = set()

    for chave, parede in paredes.items():
        rect_w = parede['rect']
        hp_ratio = parede['hp'] / PAREDE_HP_MAX
        em_edicao = (dono_edicao is not None and parede.get('dono') is dono_edicao)

        if em_edicao:
            # Paredes proprias no modo edicao: azul solido
            cor_base  = (28, 80, 200)
            cor_borda = (65, 145, 255)
            cor_div   = (18, 52, 150)
        else:
            r = int(150 * hp_ratio + 50)
            g = int(110 * hp_ratio + 35)
            b = int(70  * hp_ratio + 20)
            cor_base  = (r, g, b)
            cor_borda = (min(255, r + 70), min(255, g + 50), min(255, b + 30))
            cor_div   = (max(0, r - 30), max(0, g - 20), max(0, b - 10))

        sect_list = _get_secao_rects(chave, parede)
        if not sect_list:
            continue

        for idx, sect_rect in sect_list:
            sx = int(sect_rect.x - cam_x)
            sy = int(sect_rect.y - cam_y)
            if sx > LARGURA + 20 or sx + sect_rect.width < -20:
                continue
            if sy > ALTURA_JOGO + 20 or sy + sect_rect.height < -20:
                continue

            # Secao selecionada via drag: cinza (pendente remocao)
            if em_edicao and (chave, idx) in drag_secoes:
                s_base  = (140, 140, 155)
                s_borda = (180, 180, 195)
                s_div   = (105, 105, 120)
            else:
                s_base  = cor_base
                s_borda = cor_borda
                s_div   = cor_div

            # Sombra
            pygame.draw.rect(tela, (10, 8, 5),
                             (sx - 1, sy - 1, sect_rect.width + 2, sect_rect.height + 2), 0, 2)
            # Corpo
            pygame.draw.rect(tela, s_base,
                             (sx, sy, sect_rect.width, sect_rect.height), 0, 2)
            # Borda
            pygame.draw.rect(tela, s_borda,
                             (sx, sy, sect_rect.width, sect_rect.height), 1, 2)
            # Divisao interna
            orient = chave[2]
            if orient == 'h':
                pygame.draw.line(tela, s_div,
                                 (sx + sect_rect.width // 2, sy),
                                 (sx + sect_rect.width // 2, sy + sect_rect.height), 1)
            else:
                pygame.draw.line(tela, s_div,
                                 (sx, sy + sect_rect.height // 2),
                                 (sx + sect_rect.width, sy + sect_rect.height // 2), 1)

        # Barra de HP (somente paredes normais, nao em modo edicao)
        if not em_edicao and hp_ratio < 1.0:
            sx_full = int(rect_w.x - cam_x)
            sy_full = int(rect_w.y - cam_y)
            bar_w = max(rect_w.width, rect_w.height)
            bar_h = 3
            bx = sx_full + (rect_w.width - bar_w) // 2
            by = sy_full - 6
            pygame.draw.rect(tela, (40, 0, 0), (bx, by, bar_w, bar_h), 0, 1)
            pygame.draw.rect(tela, (220, 50, 50),
                             (bx, by, int(bar_w * hp_ratio), bar_h), 0, 1)


def _desenhar_preview_construcao(tela, mx_world, my_world, cam_x, cam_y, paredes,
                                 player_cx, player_cy):
    """Preview da parede que seria colocada em modo construcao."""
    chave, rect_w = _obter_posicao_parede(mx_world, my_world)
    if chave is None or rect_w is None:
        return

    ddx = rect_w.centerx - player_cx
    ddy = rect_w.centery - player_cy
    muito_longe = ddx * ddx + ddy * ddy > BUILD_MAX_DIST * BUILD_MAX_DIST

    sx = int(rect_w.x - cam_x)
    sy = int(rect_w.y - cam_y)
    if chave in paredes or muito_longe:
        # Posicao ocupada ou fora do alcance - mostrar vermelho
        preview = pygame.Surface((rect_w.width, rect_w.height), pygame.SRCALPHA)
        preview.fill((220, 50, 50, 100))
        tela.blit(preview, (sx, sy))
        pygame.draw.rect(tela, (255, 60, 60), (sx, sy, rect_w.width, rect_w.height), 2)
    else:
        # Livre e dentro do alcance - mostrar verde
        preview = pygame.Surface((rect_w.width, rect_w.height), pygame.SRCALPHA)
        preview.fill((80, 220, 80, 120))
        tela.blit(preview, (sx, sy))
        pygame.draw.rect(tela, (100, 255, 100), (sx, sy, rect_w.width, rect_w.height), 2)


# ============================================================
#  ARMAS VISUAIS
# ============================================================

def _desenhar_arma_boxfight(tela, jogador, cam_x, cam_y, tempo):
    """
    Desenha a arma segurada pelo jogador usando os scripts visuais reais
    (desenhar_spas12 / desenhar_metralhadora), escalados para o tamanho do player.
    Padrao identico ao Deadeye: superficie temporaria + pygame.transform.scale.
    Nao desenha quando em modo edicao ou construcao.
    """
    if (not jogador.vivo or not jogador.arma
            or jogador.modo_edicao or jogador.em_construcao):
        return

    # Centro do jogador em coordenadas de tela
    scx = jogador.x + TAM_JOGADOR // 2 - cam_x
    scy = jogador.y + TAM_JOGADOR // 2 - cam_y

    if scx < -100 or scx > LARGURA + 100 or scy < -100 or scy > ALTURA_JOGO + 100:
        return

    # Direcao unitaria da mira
    adx = jogador.mira_x - (jogador.x + TAM_JOGADOR // 2)
    ady = jogador.mira_y - (jogador.y + TAM_JOGADOR // 2)
    dist_m = math.sqrt(adx * adx + ady * ady)
    if dist_m < 1:
        adx, ady = 1.0, 0.0
    else:
        adx /= dist_m
        ady /= dist_m

    # Superficie temporaria transparente (igual ao Deadeye)
    tam = _SURF_ARMA_TAM
    temp_surf = pygame.Surface((tam, tam), pygame.SRCALPHA)

    # Proxy-object posicionado no centro da superficie temporaria
    class _Jt:
        pass
    jt = _Jt()
    jt.x      = tam // 2 - TAM_JOGADOR // 2
    jt.y      = tam // 2 - TAM_JOGADOR // 2
    jt.tamanho = TAM_JOGADOR
    jt.cor     = jogador.cor
    # Suprimir barra de cooldown: tempo_cooldown=0 faz a condicao nunca ativar
    jt.tempo_cooldown    = 0
    jt.tempo_ultimo_tiro = 0

    # Posicao do mouse na superficie temporaria (60px na direcao da mira)
    pos_mouse_temp = (tam // 2 + adx * 60, tam // 2 + ady * 60)

    if jogador.arma == 'spas':
        desenhar_spas12(temp_surf, jt, tempo, pos_mouse_temp)
    elif jogador.arma == 'metralhadora':
        desenhar_metralhadora(temp_surf, jt, tempo, pos_mouse_temp)

    # Escalar e centralizar no jogador (mesmo padrao do Deadeye)
    novo_tam = int(tam * _SURF_ARMA_ESCALA)
    arma_surf = pygame.transform.scale(temp_surf, (novo_tam, novo_tam))
    tela.blit(arma_surf, (int(scx) - novo_tam // 2, int(scy) - novo_tam // 2))


# ============================================================
#  PROJETEIS
# ============================================================

def _criar_tiro(jogador, projeteis, cx, cy, dx, dy, tempo):
    """Cria projeteis para o jogador na direcao (dx, dy)."""
    if not jogador.arma:
        return
    info = ARMAS[jogador.arma]
    for _ in range(info['num_pellets']):
        ang = math.atan2(dy, dx) + random.uniform(-info['espalhamento'], info['espalhamento'])
        vx = math.cos(ang) * info['velocidade_proj']
        vy = math.sin(ang) * info['velocidade_proj']
        projeteis.append({
            'x': float(cx),
            'y': float(cy),
            'vx': vx,
            'vy': vy,
            'dono': jogador,
            'arma': jogador.arma,
            'raio': info['raio_proj'],
            'cor': info['cor_proj'],
            'vida': 90,
        })


def _atualizar_projeteis(projeteis, jogadores, paredes, particulas, kill_feed, tempo):
    """Atualiza posicoes e colisoes dos projeteis."""
    for proj in projeteis[:]:
        proj['x'] += proj['vx']
        proj['y'] += proj['vy']
        proj['vida'] -= 1

        # Saiu da arena ou expirou
        if (proj['x'] < 0 or proj['x'] > ARENA_W or
                proj['y'] < 0 or proj['y'] > ARENA_H or proj['vida'] <= 0):
            if proj in projeteis:
                projeteis.remove(proj)
            continue

        # Colisao com parede
        chave_parede = _projetil_colide_parede(proj, paredes)
        if chave_parede:
            dano_p = ARMAS[proj['arma']]['dano_parede']
            destruida = _danificar_parede(paredes, chave_parede, dano_p)
            # Particulas de impacto
            for _ in range(6):
                p = Particula(proj['x'] + random.uniform(-5, 5),
                              proj['y'] + random.uniform(-5, 5),
                              (180, 120, 60))
                p.velocidade_x = random.uniform(-3, 3)
                p.velocidade_y = random.uniform(-3, 3)
                p.vida = random.randint(5, 10)
                p.tamanho = random.uniform(1, 3)
                particulas.append(p)
            if destruida:
                for _ in range(10):
                    p = Particula(proj['x'] + random.uniform(-10, 10),
                                  proj['y'] + random.uniform(-10, 10),
                                  (220, 160, 80))
                    p.velocidade_x = random.uniform(-4, 4)
                    p.velocidade_y = random.uniform(-4, 4)
                    p.vida = random.randint(10, 20)
                    p.tamanho = random.uniform(2, 4)
                    particulas.append(p)
            if proj in projeteis:
                projeteis.remove(proj)
            continue

        # Colisao com jogadores
        removido = False
        for j in jogadores:
            if j is proj['dono'] or not j.vivo:
                continue
            if tempo < j.invulneravel_ate:
                continue
            if j.get_rect().collidepoint(proj['x'], proj['y']):
                dano_j = ARMAS[proj['arma']]['dano_player']
                j.hp -= dano_j
                j.invulneravel_ate = tempo + 300
                cx_j, cy_j = j.get_centro()
                if j.hp <= 0:
                    j.vivo = False
                    proj['dono'].kills += 1
                    # Kill feed
                    kill_feed.append({
                        'killer':      proj['dono'].nome,
                        'victim':      j.nome,
                        'killer_cor':  proj['dono'].cor,
                        'victim_cor':  j.cor,
                        'tempo':       tempo,
                    })
                    if len(kill_feed) > 6:
                        kill_feed.pop(0)
                    # Particulas de morte
                    for _ in range(18):
                        p = Particula(cx_j + random.uniform(-12, 12),
                                      cy_j + random.uniform(-12, 12),
                                      j.cor)
                        p.velocidade_x = random.uniform(-6, 6)
                        p.velocidade_y = random.uniform(-6, 6)
                        p.vida = random.randint(18, 32)
                        p.tamanho = random.uniform(3, 6)
                        particulas.append(p)
                    # Flash branco de impacto
                    for _ in range(8):
                        p = Particula(cx_j + random.uniform(-6, 6),
                                      cy_j + random.uniform(-6, 6),
                                      (255, 255, 255))
                        p.velocidade_x = random.uniform(-9, 9)
                        p.velocidade_y = random.uniform(-9, 9)
                        p.vida = random.randint(6, 12)
                        p.tamanho = random.uniform(1, 3)
                        particulas.append(p)
                else:
                    for _ in range(8):
                        p = Particula(cx_j + random.uniform(-8, 8),
                                      cy_j + random.uniform(-8, 8),
                                      proj['cor'])
                        p.velocidade_x = random.uniform(-3, 3)
                        p.velocidade_y = random.uniform(-3, 3)
                        p.vida = random.randint(5, 12)
                        p.tamanho = random.uniform(1, 3)
                        particulas.append(p)
                if proj in projeteis:
                    projeteis.remove(proj)
                removido = True
                break
        if removido:
            continue


def _desenhar_projeteis(tela, projeteis, cam_x, cam_y):
    """Desenha todos os projeteis."""
    for proj in projeteis:
        sx = int(proj['x'] - cam_x)
        sy = int(proj['y'] - cam_y)
        if -20 <= sx <= LARGURA + 20 and -20 <= sy <= ALTURA_JOGO + 20:
            pygame.draw.circle(tela, proj['cor'], (sx, sy), proj['raio'])
            # Trail
            tx = int(proj['x'] - proj['vx'] * 2.5 - cam_x)
            ty = int(proj['y'] - proj['vy'] * 2.5 - cam_y)
            trail_cor = tuple(max(0, c - 120) for c in proj['cor'])
            pygame.draw.line(tela, trail_cor, (tx, ty), (sx, sy), max(1, proj['raio'] - 1))


# ============================================================
#  BOT AI
# ============================================================

def _bot_construir_parede_defensiva(bot, paredes, alvo):
    """
    Constroi apenas nas 4 bordas da celula atual do bot.
    Escolhe a borda que melhor bloqueia a direcao do inimigo.
    """
    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2

    gx = int(bot_cx // GRID_SIZE)
    gy = int(bot_cy // GRID_SIZE)

    # As 4 bordas da celula onde o bot esta
    esp = PAREDE_ESPESSURA // 2
    candidatos = [
        ((gx,     gy,     'h'),
         pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE - esp, GRID_SIZE, PAREDE_ESPESSURA)),
        ((gx,     gy + 1, 'h'),
         pygame.Rect(gx * GRID_SIZE, (gy + 1) * GRID_SIZE - esp, GRID_SIZE, PAREDE_ESPESSURA)),
        ((gx,     gy,     'v'),
         pygame.Rect(gx * GRID_SIZE - esp, gy * GRID_SIZE, PAREDE_ESPESSURA, GRID_SIZE)),
        ((gx + 1, gy,     'v'),
         pygame.Rect((gx + 1) * GRID_SIZE - esp, gy * GRID_SIZE, PAREDE_ESPESSURA, GRID_SIZE)),
    ]

    if alvo:
        alvo_cx = alvo.x + TAM_JOGADOR // 2
        alvo_cy = alvo.y + TAM_JOGADOR // 2
        dx = alvo_cx - bot_cx
        dy = alvo_cy - bot_cy
        dist_a = math.sqrt(dx * dx + dy * dy)
        if dist_a > 1:
            ndx = dx / dist_a
            ndy = dy / dist_a
            # Ordenar bordas pela que mais aponta para o inimigo (dot product)
            def _score(c):
                _, rect = c
                bx = rect.centerx - bot_cx
                by = rect.centery - bot_cy
                d = math.sqrt(bx * bx + by * by)
                if d < 1:
                    return 0.0
                return (bx / d) * ndx + (by / d) * ndy
            candidatos.sort(key=_score, reverse=True)
        else:
            random.shuffle(candidatos)
    else:
        random.shuffle(candidatos)

    for chave, rect in candidatos:
        gi, gj, _ = chave
        if 0 <= gi <= GRID_COLS and 0 <= gj <= GRID_ROWS and chave not in paredes:
            _colocar_parede(paredes, chave, rect, dono=bot)
            return


def _bot_abrir_gap_tiro(bot, paredes, alvo):
    """
    Remove a secao da propria parede do bot mais alinhada com a direcao do alvo,
    criando um gap para atirar por ele.
    """
    if not alvo:
        return False
    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2
    alvo_cx = alvo.x + TAM_JOGADOR // 2
    alvo_cy = alvo.y + TAM_JOGADOR // 2

    dx_a = alvo_cx - bot_cx
    dy_a = alvo_cy - bot_cy
    dist_a = math.sqrt(dx_a ** 2 + dy_a ** 2)
    if dist_a < 1:
        return False
    ndx = dx_a / dist_a
    ndy = dy_a / dist_a

    melhor_chave, melhor_idx, melhor_score = None, None, -1.0
    for chave, parede in paredes.items():
        if parede.get('dono') is not bot:
            continue
        for idx, sect_rect in _get_secao_rects(chave, parede):
            scx = sect_rect.centerx
            scy = sect_rect.centery
            dx_s = scx - bot_cx
            dy_s = scy - bot_cy
            d_s = math.sqrt(dx_s ** 2 + dy_s ** 2)
            if d_s > BUILD_MAX_DIST or d_s < 1:
                continue
            dot = (dx_s / d_s) * ndx + (dy_s / d_s) * ndy
            if dot > 0.5 and dot > melhor_score:
                melhor_score = dot
                melhor_chave = chave
                melhor_idx = idx

    if melhor_chave is not None:
        _remover_secao_parede(paredes, melhor_chave, melhor_idx)
        return True
    return False


def _bot_rush_boxfight(bot, paredes, jogadores, tempo):
    """
    Modo rushador: o bot avança em ciclos de
      construir box → editar parede da frente → avançar → repetir.
    Sai do modo quando chega perto do alvo ou o alvo morre.
    """
    # Atualizar/escolher alvo: aleatorio
    if not bot.bot_rush_alvo or not bot.bot_rush_alvo.vivo:
        vivos = [j for j in jogadores if j is not bot and j.vivo]
        if not vivos:
            bot.bot_rush_ativo = False
            bot.em_construcao = False
            return
        bot.bot_rush_alvo = random.choice(vivos)

    alvo = bot.bot_rush_alvo
    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2
    alvo_cx = alvo.x + TAM_JOGADOR // 2
    alvo_cy = alvo.y + TAM_JOGADOR // 2
    dx = alvo_cx - bot_cx
    dy = alvo_cy - bot_cy
    dist = math.sqrt(dx * dx + dy * dy)

    # Chegou perto: sair do rush
    if dist < 130:
        bot.bot_rush_ativo = False
        bot.em_construcao = False
        bot.vx = 0
        bot.vy = 0
        bot.bot_alvo = alvo
        return

    ndx = dx / dist
    ndy = dy / dist
    gx = int(bot_cx // GRID_SIZE)
    gy = int(bot_cy // GRID_SIZE)
    esp = PAREDE_ESPESSURA // 2

    # ---- FASE: construir box ----
    if bot.bot_rush_fase == 'construir':
        bot.vx = 0
        bot.vy = 0
        bot.em_construcao = True

        bordas = [
            ((gx,     gy,     'h'),
             pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE - esp,
                         GRID_SIZE, PAREDE_ESPESSURA)),
            ((gx,     gy + 1, 'h'),
             pygame.Rect(gx * GRID_SIZE, (gy + 1) * GRID_SIZE - esp,
                         GRID_SIZE, PAREDE_ESPESSURA)),
            ((gx,     gy,     'v'),
             pygame.Rect(gx * GRID_SIZE - esp, gy * GRID_SIZE,
                         PAREDE_ESPESSURA, GRID_SIZE)),
            ((gx + 1, gy,     'v'),
             pygame.Rect((gx + 1) * GRID_SIZE - esp, gy * GRID_SIZE,
                         PAREDE_ESPESSURA, GRID_SIZE)),
        ]
        for chave, rect in bordas:
            gi, gj, _ = chave
            if 0 <= gi <= GRID_COLS and 0 <= gj <= GRID_ROWS:
                _colocar_parede(paredes, chave, rect, dono=bot)

        if tempo >= bot.bot_rush_timer:
            bot.bot_rush_fase = 'editar'

    # ---- FASE: editar parede da frente ----
    elif bot.bot_rush_fase == 'editar':
        bot.vx = 0
        bot.vy = 0
        bot.em_construcao = False

        # A borda que mais aponta na direcao do alvo
        bordas_info = [
            ((gx,     gy,     'h'), ( 0.0, -1.0)),
            ((gx,     gy + 1, 'h'), ( 0.0, +1.0)),
            ((gx,     gy,     'v'), (-1.0,  0.0)),
            ((gx + 1, gy,     'v'), (+1.0,  0.0)),
        ]
        melhor_chave = None
        melhor_dot   = -2.0
        for chave, normal in bordas_info:
            dot = normal[0] * ndx + normal[1] * ndy
            if dot > melhor_dot and chave in paredes:
                melhor_dot   = dot
                melhor_chave = chave

        if melhor_chave is not None and melhor_dot > 0.2:
            parede = paredes.get(melhor_chave)
            if parede:
                # Remover secoes centrais (indices 1 e 2) para gap de 40px
                for idx in (1, 2):
                    _remover_secao_parede(paredes, melhor_chave, idx)

        bot.bot_rush_fase = 'avancar'
        bot.bot_rush_timer = tempo + BOT_RUSH_AVANCAR_DUR
        bot.bot_rush_celula_ini = (gx, gy)

    # ---- FASE: avancar ----
    elif bot.bot_rush_fase == 'avancar':
        bot.em_construcao = False
        bot.vx = ndx * VEL_BOXFIGHT * 1.3
        bot.vy = ndy * VEL_BOXFIGHT * 1.3

        cur_gx = int((bot.x + TAM_JOGADOR // 2) // GRID_SIZE)
        cur_gy = int((bot.y + TAM_JOGADOR // 2) // GRID_SIZE)

        # Nova celula atingida ou timeout: iniciar proxima box
        if (cur_gx, cur_gy) != bot.bot_rush_celula_ini or tempo >= bot.bot_rush_timer:
            bot.vx = 0
            bot.vy = 0
            bot.bot_rush_fase = 'construir'
            bot.bot_rush_timer = tempo + BOT_RUSH_CONSTRUIR_DUR

    # Manter mira no alvo (para _bot_atirar funcionar durante 'avancar')
    bot.bot_alvo = alvo
    bot.mira_x = alvo_cx
    bot.mira_y = alvo_cy


def _bot_ai_boxfight(bot, jogadores, paredes, tempo):
    """IA do bot no BoxFight: movimenta, constroi defensivamente, edita paredes e mira."""
    if not bot.vivo:
        bot.vx = 0
        bot.vy = 0
        return

    bot_cx, bot_cy = bot.get_centro()

    if bot.arma is None:
        bot.arma = random.choice(['spas', 'metralhadora'])

    # Encontrar alvo ANTES do bloco de construcao para usar na IA defensiva
    melhor_alvo = None
    melhor_dist = float('inf')
    for j in jogadores:
        if j is bot or not j.vivo:
            continue
        dx = j.x - bot.x
        dy = j.y - bot.y
        d = math.sqrt(dx * dx + dy * dy)
        if d < melhor_dist:
            melhor_dist = d
            melhor_alvo = j

    hp_ratio = bot.hp / HP_MAX

    # ---- Modo evacuacao (HP critico + cura disponivel) ----
    if (not bot.bot_evacuando and bot.hp <= BOT_EVAC_HP_THRESHOLD
            and not bot.cura_usado and not bot.bot_rush_ativo):
        bot.bot_evacuando = True
        bot.bot_rush_ativo = False
        bot.cura_inicio = 0

    if bot.bot_evacuando:
        _bot_evacuar(bot, paredes, jogadores, tempo)
        return

    # ---- Modo rush ----
    if bot.bot_rush_ativo:
        _bot_rush_boxfight(bot, paredes, jogadores, tempo)
        return

    # Chance aleatoria de re-entrar em rush durante a partida
    if not bot.bot_rush_ativo and melhor_alvo and random.random() < BOT_RUSH_CHANCE:
        bot.bot_rush_ativo = True
        bot.bot_rush_alvo  = melhor_alvo
        bot.bot_rush_fase  = 'construir'
        bot.bot_rush_timer = tempo + BOT_RUSH_CONSTRUIR_DUR

    # Modo construcao defensiva
    if bot.em_construcao:
        if tempo > bot.bot_build_timer:
            bot.em_construcao = False
        else:
            # Constroi com mais frequencia quando HP esta baixo
            freq = 0.18 if hp_ratio < 0.5 else 0.12
            if random.random() < freq:
                _bot_construir_parede_defensiva(bot, paredes, melhor_alvo)
            bot.vx = 0
            bot.vy = 0
            return

    # Chance de entrar em construcao (aumenta com HP baixo e com inimigo proximo)
    build_chance = BOT_BUILD_CHANCE * (1.0 + (1.0 - hp_ratio) * 4.0)
    if melhor_dist < 180:
        build_chance *= 2.0  # urgencia quando inimigo esta perto
    if random.random() < build_chance:
        bot.em_construcao = True
        duracao = int(BOT_BUILD_DURACAO * (1.5 if hp_ratio < 0.5 else 1.0))
        bot.bot_build_timer = tempo + duracao

    # Editar propria parede: abrir gap para atirar ocasionalmente
    if melhor_alvo and tempo > bot.bot_edit_timer:
        if random.random() < 0.006:
            _bot_abrir_gap_tiro(bot, paredes, melhor_alvo)
            bot.bot_edit_timer = tempo + random.randint(1200, 2800)

    if not melhor_alvo:
        bot.vx = 0
        bot.vy = 0
        return

    bot.bot_alvo = melhor_alvo

    dx = melhor_alvo.x - bot.x
    dy = melhor_alvo.y - bot.y
    dist = max(melhor_dist, 1)
    dir_x = dx / dist
    dir_y = dy / dist

    # Strafe
    if tempo > bot.bot_strafe_timer:
        bot.bot_strafe_timer = tempo + BOT_STRAFE_INTERVALO + random.randint(-200, 200)
        bot.bot_strafe_dir = -bot.bot_strafe_dir

    strafe_x = -dir_y * bot.bot_strafe_dir
    strafe_y =  dir_x * bot.bot_strafe_dir

    # Base: avanca diretamente, strafe como componente lateral
    mover_x = strafe_x * 0.5
    mover_y = strafe_y * 0.5

    if dist < BOT_DIST_RECUAR:
        mover_x -= dir_x * 1.0
        mover_y -= dir_y * 1.0
    elif dist > BOT_DIST_IDEAL:
        mover_x += dir_x * 1.0
        mover_y += dir_y * 1.0

    # Com HP baixo, recua levemente mas continua pressionando
    if hp_ratio < 0.4:
        mover_x -= dir_x * 0.25
        mover_y -= dir_y * 0.25

    # Evitar bordas
    margem = 100
    if bot_cx < margem:             mover_x += 0.9
    elif bot_cx > ARENA_W - margem: mover_x -= 0.9
    if bot_cy < margem:             mover_y += 0.9
    elif bot_cy > ARENA_H - margem: mover_y -= 0.9

    mag = math.sqrt(mover_x * mover_x + mover_y * mover_y)
    if mag > 0:
        mover_x /= mag
        mover_y /= mag

    bot.vx = mover_x * VEL_BOXFIGHT
    bot.vy = mover_y * VEL_BOXFIGHT

    bot.mira_x = melhor_alvo.x + TAM_JOGADOR // 2
    bot.mira_y = melhor_alvo.y + TAM_JOGADOR // 2



def _bot_atirar(bot, jogadores, paredes, projeteis, tempo):
    """Bot atira se nao estiver em modo construcao e tiver alvo."""
    if bot.em_construcao or not bot.arma:
        return
    if not bot.bot_alvo or not bot.bot_alvo.vivo:
        return
    info = ARMAS[bot.arma]
    if tempo - bot.tempo_ultimo_tiro < info['cooldown']:
        return
    if tempo < bot.bot_shoot_timer:
        return

    # Imprecisao do bot (proporcional a distancia)
    alvo = bot.bot_alvo
    dist_alvo = math.sqrt((alvo.x - bot.x) ** 2 + (alvo.y - bot.y) ** 2)
    imprecisao = min(30, dist_alvo * 0.06)

    alvo_x = alvo.x + TAM_JOGADOR // 2 + random.uniform(-imprecisao, imprecisao)
    alvo_y = alvo.y + TAM_JOGADOR // 2 + random.uniform(-imprecisao, imprecisao)

    cx, cy = bot.get_centro()
    dx = alvo_x - cx
    dy = alvo_y - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1:
        return
    dx /= dist
    dy /= dist

    _criar_tiro(bot, projeteis, cx, cy, dx, dy, tempo)
    bot.tempo_ultimo_tiro = tempo
    bot.bot_shoot_timer = tempo + random.randint(BOT_SHOOT_BASE_DELAY - 80, BOT_SHOOT_BASE_DELAY + 150)


# ============================================================
#  BOT EVACUACAO (cura de emergencia)
# ============================================================

BOT_EVAC_HP_THRESHOLD = 1   # HP abaixo ou igual para ativar evacuacao

def _bot_evacuar(bot, paredes, jogadores, tempo):
    """
    Bot para, fecha-se em box, e se cura.
    Continua atirando (em_construcao permanece False para nao bloquear _bot_atirar).
    """
    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2
    gx = int(bot_cx // GRID_SIZE)
    gy = int(bot_cy // GRID_SIZE)
    esp = PAREDE_ESPESSURA // 2

    # Construir as 4 paredes da box continuamente
    bordas = [
        ((gx,     gy,     'h'), pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE - esp, GRID_SIZE, PAREDE_ESPESSURA)),
        ((gx,     gy + 1, 'h'), pygame.Rect(gx * GRID_SIZE, (gy + 1) * GRID_SIZE - esp, GRID_SIZE, PAREDE_ESPESSURA)),
        ((gx,     gy,     'v'), pygame.Rect(gx * GRID_SIZE - esp, gy * GRID_SIZE, PAREDE_ESPESSURA, GRID_SIZE)),
        ((gx + 1, gy,     'v'), pygame.Rect((gx + 1) * GRID_SIZE - esp, gy * GRID_SIZE, PAREDE_ESPESSURA, GRID_SIZE)),
    ]
    for chave, rect in bordas:
        gi, gj, _ = chave
        if 0 <= gi <= GRID_COLS and 0 <= gj <= GRID_ROWS:
            _colocar_parede(paredes, chave, rect, dono=bot)

    # Parar de mover
    bot.vx = 0
    bot.vy = 0

    # Iniciar timer de cura
    if bot.cura_inicio == 0:
        bot.cura_inicio = tempo
    bot.cura_ativo = True

    # Manter alvo e mira para _bot_atirar continuar funcionando
    vivos = [j for j in jogadores if j is not bot and j.vivo]
    if vivos:
        if bot.bot_alvo is None or not bot.bot_alvo.vivo:
            bot.bot_alvo = min(vivos, key=lambda j: (j.x - bot.x) ** 2 + (j.y - bot.y) ** 2)
        bot.mira_x = bot.bot_alvo.x + TAM_JOGADOR // 2
        bot.mira_y = bot.bot_alvo.y + TAM_JOGADOR // 2

    # Verificar conclusao da cura
    if tempo - bot.cura_inicio >= CURA_DURACAO:
        bot.hp = HP_MAX
        bot.cura_usado = True
        bot.cura_ativo = False
        bot.cura_inicio = 0
        bot.bot_evacuando = False


# ============================================================
#  HUD
# ============================================================

def _desenhar_hud_boxfight(tela, jogador, fonte_hud, fonte_peq, jogadores_vivos, rodada, tempo):
    """HUD do BoxFight."""
    # HP
    for i in range(HP_MAX):
        hx = 15 + i * 22
        hy = 10
        if i < jogador.hp:
            pygame.draw.rect(tela, VERMELHO, (hx, hy, 16, 16), 0, 3)
            pygame.draw.rect(tela, (255, 100, 100), (hx + 2, hy + 2, 5, 5), 0, 2)
        else:
            pygame.draw.rect(tela, (60, 40, 40), (hx, hy, 16, 16), 1, 3)

    # Arma
    arma_nome = ARMAS[jogador.arma]['nome']
    if jogador.arma == 'spas':
        arma_cor = (255, 140, 40)
    elif jogador.arma == 'metralhadora':
        arma_cor = (255, 255, 60)
    else:
        arma_cor = (140, 140, 140)
    arma_s = fonte_peq.render(f"[E] {arma_nome}", True, arma_cor)
    tela.blit(arma_s, (15, 30))

    # Modo construcao
    if jogador.em_construcao:
        pulso = int(160 + 95 * abs(math.sin(tempo / 200)))
        modo_s = fonte_peq.render("[Q] CONSTRUCAO ATIVO", True, (50, pulso, 50))
    else:
        modo_s = fonte_peq.render("[Q] Construir", True, (70, 120, 70))
    tela.blit(modo_s, (15, 47))

    # Modo edicao
    if jogador.modo_edicao:
        pulso_e = int(160 + 95 * abs(math.sin(tempo / 200)))
        edit_s = fonte_peq.render("[G] EDICAO ATIVO", True, (pulso_e, pulso_e, 30))
    else:
        edit_s = fonte_peq.render("[G] Editar Parede", True, (110, 110, 50))
    tela.blit(edit_s, (15, 64))

    # Cura
    if jogador.cura_ativo:
        pulso_f = int(160 + 95 * abs(math.sin(tempo / 150)))
        cura_s = fonte_peq.render("[F] CURANDO...", True, (50, pulso_f, 80))
        tela.blit(cura_s, (15, 81))
    elif jogador.cura_usado:
        cura_s = fonte_peq.render("[F] Cura: USADA", True, (80, 80, 80))
        tela.blit(cura_s, (15, 81))
    else:
        cura_s = fonte_peq.render("[F] Curar (1x)", True, (80, 200, 100))
        tela.blit(cura_s, (15, 81))

    # Info central
    info = fonte_peq.render(
        f"Vivos: {jogadores_vivos}  |  Rodada: {rodada}/{NUM_RODADAS}", True, (180, 180, 200))
    tela.blit(info, (LARGURA // 2 - info.get_width() // 2, 8))

    # Kills
    kills_s = fonte_peq.render(f"Kills: {jogador.kills}", True, (180, 255, 180))
    tela.blit(kills_s, (LARGURA - kills_s.get_width() - MINIMAP_W - 20, 12))

    # Controles
    ctrl = fonte_peq.render(
        "WASD: Mover  |  E: Arma  |  Q: Construir  |  G: Editar  |  F: Curar  |  LMB: Atirar/Colocar/Remover",
        True, (100, 100, 130))
    tela.blit(ctrl, (LARGURA // 2 - ctrl.get_width() // 2, ALTURA_JOGO - 18))


# ============================================================
#  KILL FEED
# ============================================================

KILL_FEED_DURACAO = 5000   # ms cada entrada fica visivel
KILL_FEED_FADE    = 1200   # ms de fade antes de sumir

def _desenhar_kill_feed(tela, kill_feed, fonte, tempo):
    """Desenha o kill feed no canto superior direito, abaixo do minimap."""
    kf_x = LARGURA - 10
    kf_y = MINIMAP_Y + MINIMAP_H + 8

    for entrada in kill_feed:
        idade = tempo - entrada['tempo']
        if idade > KILL_FEED_DURACAO:
            continue

        alpha = 255
        if idade > KILL_FEED_DURACAO - KILL_FEED_FADE:
            frac = (idade - (KILL_FEED_DURACAO - KILL_FEED_FADE)) / KILL_FEED_FADE
            alpha = int(255 * (1.0 - frac))

        k_surf = fonte.render(entrada['killer'], True, entrada['killer_cor'])
        sep_surf = fonte.render(' > ', True, (200, 200, 200))
        v_surf = fonte.render(entrada['victim'],  True, entrada['victim_cor'])

        total_w = k_surf.get_width() + sep_surf.get_width() + v_surf.get_width()
        row_h   = k_surf.get_height()
        x_start = kf_x - total_w

        bg = pygame.Surface((total_w + 8, row_h + 4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(140 * alpha / 255)))
        tela.blit(bg, (x_start - 4, kf_y - 2))

        for surf in (k_surf, sep_surf, v_surf):
            surf.set_alpha(alpha)

        tela.blit(k_surf,   (x_start, kf_y))
        tela.blit(sep_surf, (x_start + k_surf.get_width(), kf_y))
        tela.blit(v_surf,   (x_start + k_surf.get_width() + sep_surf.get_width(), kf_y))

        kf_y += row_h + 4


# ============================================================
#  MINIMAP
# ============================================================

def _desenhar_minimap_boxfight(tela, jogadores, jogador_local, paredes, cam_x, cam_y):
    """Minimap no canto superior direito."""
    surf = pygame.Surface((MINIMAP_W, MINIMAP_H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 150))
    pygame.draw.rect(surf, (80, 60, 100), (0, 0, MINIMAP_W, MINIMAP_H), 1)

    # Viewport
    vx = int((cam_x / ARENA_W) * MINIMAP_W)
    vy = int((cam_y / ARENA_H) * MINIMAP_H)
    vw = int((LARGURA / ARENA_W) * MINIMAP_W)
    vh = int((ALTURA_JOGO / ARENA_H) * MINIMAP_H)
    pygame.draw.rect(surf, (100, 100, 160, 80), (vx, vy, vw, vh), 1)

    # Paredes (pequenos pontos)
    for _, parede in paredes.items():
        rect = parede['rect']
        px = int((rect.centerx / ARENA_W) * MINIMAP_W)
        py = int((rect.centery / ARENA_H) * MINIMAP_H)
        pygame.draw.circle(surf, (160, 120, 60), (px, py), 1)

    # Jogadores
    for j in jogadores:
        if not j.vivo:
            continue
        mx = int((j.x / ARENA_W) * MINIMAP_W)
        my = int((j.y / ARENA_H) * MINIMAP_H)
        tam = 4 if j is jogador_local else 3
        cor = BRANCO if j is jogador_local else j.cor
        pygame.draw.rect(surf, cor, (mx - tam // 2, my - tam // 2, tam, tam))

    tela.blit(surf, (MINIMAP_X, MINIMAP_Y))


# ============================================================
#  SCOREBOARD
# ============================================================

def _desenhar_scoreboard_boxfight(tela, jogadores, fonte_grande, fonte_score, fonte_peq, tempo, start_time):
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    tela.blit(overlay, (0, 0))

    titulo = fonte_grande.render("RESULTADO", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 40))

    ranking = sorted(jogadores, key=lambda j: (-j.rodadas_vencidas, -j.kills))
    tempo_decorrido = tempo - start_time
    y_base = 120

    for rank, j in enumerate(ranking):
        delay = rank * 300
        if tempo_decorrido < delay:
            continue

        y = y_base + rank * 50
        linha_w = 500
        linha_x = LARGURA // 2 - linha_w // 2
        linha_surf = pygame.Surface((linha_w, 42), pygame.SRCALPHA)

        alphas = [(255, 200, 0, 30), (200, 200, 200, 20), (180, 100, 30, 20), (40, 40, 60, 20)]
        linha_surf.fill(alphas[min(rank, 3)])
        tela.blit(linha_surf, (linha_x, y))

        medalhas = ["1st", "2nd", "3rd"]
        pos_text = medalhas[rank] if rank < 3 else f"{rank + 1}th"
        pos_cores = [(255, 215, 0), (200, 200, 210), (205, 127, 50), (150, 150, 160)]
        pos_cor = pos_cores[min(rank, 3)]
        pos_s = fonte_score.render(pos_text, True, pos_cor)
        tela.blit(pos_s, (linha_x + 15, y + 8))

        sq_x, sq_y, sq_tam = linha_x + 80, y + 6, 28
        cor_esc = tuple(max(0, c - 60) for c in j.cor)
        pygame.draw.rect(tela, cor_esc, (sq_x, sq_y, sq_tam, sq_tam), 0, 4)
        pygame.draw.rect(tela, j.cor, (sq_x + 2, sq_y + 2, sq_tam - 4, sq_tam - 4), 0, 3)

        # Icone de arma
        arma_cor_map = {'spas': (255, 140, 40), 'metralhadora': (255, 255, 60), None: (80, 80, 80)}
        # (mostrar arma que o jogador tinha ao fim)

        nome_s = fonte_score.render(j.nome, True, BRANCO)
        tela.blit(nome_s, (sq_x + sq_tam + 18, y + 8))

        stats_s = fonte_peq.render(f"{j.rodadas_vencidas}R  {j.kills}K", True, (180, 255, 180))
        tela.blit(stats_s, (linha_x + 370, y + 12))

        if rank < 3:
            pygame.draw.rect(tela, pos_cor, (linha_x, y, linha_w, 42), 1, 3)

    if tempo_decorrido > 3000:
        inst = fonte_peq.render("Voltando ao menu...", True, (120, 120, 140))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def executar_minigame_boxfight(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                                cliente, nome_jogador, customizacao):
    """Executa o minigame BoxFight."""
    print("[BOXFIGHT] Minigame BoxFight iniciado!")

    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)
        print(f"[BOXFIGHT] Seed: {seed}")

    if cliente:
        cliente.get_minigame_actions()

    # Fontes
    fonte_grande    = pygame.font.SysFont("Arial", 48, True)
    fonte_media     = pygame.font.SysFont("Arial", 28, True)
    fonte_peq       = pygame.font.SysFont("Arial", 14)
    fonte_nomes     = pygame.font.SysFont("Arial", 12)
    fonte_hud       = pygame.font.SysFont("Arial", 18, True)
    fonte_score     = pygame.font.SysFont("Arial", 22, True)
    fonte_countdown = pygame.font.SysFont("Arial", 72, True)

    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, (255, 140, 40))

    # Criar jogadores (sempre 8)
    jogadores = []
    cor_local = customizacao.get('cor', AZUL)
    jogador_humano = JogadorBoxFight(nome_jogador, cor_local, is_bot=False)
    jogador_humano.arma = None  # começa sem arma; pega com E
    jogadores.append(jogador_humano)

    remotos = {}
    if cliente:
        remotos = cliente.get_remote_players()

    for pid, rp in remotos.items():
        ci = (pid - 1) % len(PALETA_CORES)
        jr = JogadorBoxFight(rp.name, PALETA_CORES[ci], is_bot=False, is_remote=True)
        jr.arma = 'spas'
        jogadores.append(jr)

    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo",  "Bot Foxtrot", "Bot Golf",  "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        bot = JogadorBoxFight(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True)
        bot.arma = random.choice(['spas', 'metralhadora'])
        jogadores.append(bot)
        bot_idx += 1

    # Posicionar nos spawn points
    for i, j in enumerate(jogadores):
        j.x = float(SPAWN_POINTS[i][0])
        j.y = float(SPAWN_POINTS[i][1])

    # Camera
    cam_x = float(jogador_humano.x - LARGURA // 2)
    cam_y = float(jogador_humano.y - ALTURA_JOGO // 2)
    cam_x = max(0, min(cam_x, ARENA_W - LARGURA))
    cam_y = max(0, min(cam_y, ARENA_H - ALTURA_JOGO))

    # Estado
    estado = "INTRO"
    tempo_estado = pygame.time.get_ticks()
    alpha_fade = 255

    # Dados do jogo
    paredes   = {}   # chave -> {'hp': int, 'rect': Rect, 'secoes': [...], 'dono': ...}
    projeteis  = []
    particulas = []
    flashes    = []
    kill_feed  = []  # lista de {'killer', 'victim', 'killer_cor', 'victim_cor', 'tempo'}
    drag_edit_secoes: set = set()  # (chave, idx) selecionados durante drag de edicao
    drag_edit_ativo  = False

    rodada_atual    = 1
    scoreboard_start = 0
    round_vencedor  = None

    while True:
        tempo = pygame.time.get_ticks()
        tempo_no_estado = tempo - tempo_estado

        # ============================================================
        #  EVENTOS
        # ============================================================
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.mouse.set_visible(True)
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True)
                    return None

                if estado == "FIGHT" and jogador_humano.vivo:
                    # Q: toggle modo construcao (desativa modo edicao)
                    if ev.key == pygame.K_q:
                        jogador_humano.em_construcao = not jogador_humano.em_construcao
                        if jogador_humano.em_construcao:
                            jogador_humano.modo_edicao = False

                    # E: sair de qualquer modo e pegar/trocar arma
                    if ev.key == pygame.K_e:
                        # Sair do modo edicao se ativo
                        if jogador_humano.modo_edicao:
                            jogador_humano.modo_edicao = False
                            jogador_humano.estado_pre_edicao = None
                            drag_edit_secoes.clear()
                            drag_edit_ativo = False
                        # Sair do modo construcao se ativo
                        jogador_humano.em_construcao = False
                        # Ciclar arma
                        if jogador_humano.arma is None:
                            jogador_humano.arma = 'spas'
                        elif jogador_humano.arma == 'spas':
                            jogador_humano.arma = 'metralhadora'
                        else:
                            jogador_humano.arma = 'spas'
                        if cliente:
                            cliente.send_minigame_action({
                                'action': 'boxfight_arma',
                                'arma': jogador_humano.arma,
                            })

                    # G: toggle modo edicao; salva e restaura estado anterior
                    if ev.key == pygame.K_g:
                        if not jogador_humano.modo_edicao:
                            # Entrar no modo edicao — salvar estado atual
                            if jogador_humano.em_construcao:
                                jogador_humano.estado_pre_edicao = 'construcao'
                            else:
                                jogador_humano.estado_pre_edicao = 'arma'
                            jogador_humano.em_construcao = False
                            jogador_humano.modo_edicao = True
                        else:
                            # Sair do modo edicao — restaurar estado anterior
                            jogador_humano.modo_edicao = False
                            if jogador_humano.estado_pre_edicao == 'construcao':
                                jogador_humano.em_construcao = True
                            jogador_humano.estado_pre_edicao = None
                            drag_edit_secoes.clear()
                            drag_edit_ativo = False


            # Clique esquerdo
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if estado == "FIGHT" and jogador_humano.vivo:
                    mx_s, my_s = convert_mouse_position(pygame.mouse.get_pos())
                    mx_world = float(mx_s) + cam_x
                    my_world = float(my_s) + cam_y

                    if jogador_humano.em_construcao:
                        # Colocar parede (dentro do limite de distancia)
                        chave_c, rect_c = _obter_posicao_parede(mx_world, my_world)
                        if chave_c and rect_c:
                            cx_h2, cy_h2 = jogador_humano.get_centro()
                            ddx_b = rect_c.centerx - cx_h2
                            ddy_b = rect_c.centery - cy_h2
                            if ddx_b * ddx_b + ddy_b * ddy_b <= BUILD_MAX_DIST * BUILD_MAX_DIST:
                                if _colocar_parede(paredes, chave_c, rect_c,
                                                   dono=jogador_humano) and cliente:
                                    cliente.send_minigame_action({
                                        'action': 'boxfight_parede',
                                        'chave': list(chave_c),
                                        'rect': [rect_c.x, rect_c.y, rect_c.width, rect_c.height],
                                    })
                    elif jogador_humano.modo_edicao:
                        # Iniciar drag de selecao (remocao ocorre ao soltar LMB)
                        drag_edit_ativo = True
                        cx_h2, cy_h2 = jogador_humano.get_centro()
                        chave_e, idx_e = _obter_secao_em(
                            mx_world, my_world, paredes, jogador_humano, cx_h2, cy_h2)
                        if chave_e is not None:
                            drag_edit_secoes.add((chave_e, idx_e))
                    else:
                        # Atirar (clique inicial)
                        if jogador_humano.arma:
                            info = ARMAS[jogador_humano.arma]
                            if tempo - jogador_humano.tempo_ultimo_tiro >= info['cooldown']:
                                cx_h, cy_h = jogador_humano.get_centro()
                                dx_t = mx_world - cx_h
                                dy_t = my_world - cy_h
                                dist_t = math.sqrt(dx_t * dx_t + dy_t * dy_t)
                                if dist_t > 0:
                                    dx_t /= dist_t
                                    dy_t /= dist_t
                                _criar_tiro(jogador_humano, projeteis, cx_h, cy_h, dx_t, dy_t, tempo)
                                jogador_humano.tempo_ultimo_tiro = tempo
                                try:
                                    from src.utils.sound import gerar_som_tiro
                                    som = pygame.mixer.Sound(gerar_som_tiro())
                                    som.set_volume(0.18)
                                    pygame.mixer.Channel(1).play(som)
                                except Exception:
                                    pass

            # Soltar LMB: aplica remocoes e sai automaticamente do modo edicao
            # Scroll: restaurar parede editada (modo edicao)
            if ev.type == pygame.MOUSEWHEEL:
                if estado == "FIGHT" and jogador_humano.vivo:
                    mp_s = convert_mouse_position(pygame.mouse.get_pos())
                    mx_w = float(mp_s[0]) + cam_x
                    my_w = float(mp_s[1]) + cam_y
                    cx_r, cy_r = jogador_humano.get_centro()
                    chave_r, _ = _obter_secao_em(mx_w, my_w, paredes,
                                                  jogador_humano, cx_r, cy_r)
                    if chave_r is not None and chave_r in paredes:
                        paredes[chave_r]['secoes'] = [True] * SECOES_POR_PAREDE

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if drag_edit_ativo and drag_edit_secoes:
                    for chave_d, idx_d in list(drag_edit_secoes):
                        _remover_secao_parede(paredes, chave_d, idx_d)
                drag_edit_secoes.clear()
                drag_edit_ativo = False
                # Sair do modo edicao automaticamente ao soltar o mouse
                if jogador_humano.modo_edicao:
                    jogador_humano.modo_edicao = False
                    if jogador_humano.estado_pre_edicao == 'construcao':
                        jogador_humano.em_construcao = True
                    jogador_humano.estado_pre_edicao = None

        # ============================================================
        #  MAQUINA DE ESTADOS
        # ============================================================

        if estado == "INTRO":
            if tempo_no_estado < 500:
                alpha_fade = int(255 * (1 - tempo_no_estado / 500))
            else:
                alpha_fade = 0
            if tempo_no_estado >= TEMPO_INTRO:
                estado = "COUNTDOWN"
                tempo_estado = tempo

        elif estado == "COUNTDOWN":
            if tempo_no_estado >= TEMPO_COUNTDOWN:
                estado = "FIGHT"
                tempo_estado = tempo
                # Ativar rush mode em todos os bots no inicio da rodada
                for _j in jogadores:
                    if _j.is_bot and _j.vivo:
                        _j.bot_rush_ativo = True
                        _j.bot_rush_alvo  = None
                        _j.bot_rush_fase  = 'construir'
                        _j.bot_rush_timer = tempo + BOT_RUSH_CONSTRUIR_DUR

        elif estado == "FIGHT":
            # Acoes remotas
            if cliente:
                for action in cliente.get_minigame_actions():
                    act = action.get('action')
                    for j in jogadores:
                        if not j.is_remote or not j.vivo:
                            continue
                        if act == 'boxfight_input':
                            j.x = action.get('x', j.x)
                            j.y = action.get('y', j.y)
                            j.mira_x = action.get('mx', j.mira_x)
                            j.mira_y = action.get('my', j.mira_y)
                        elif act == 'boxfight_tiro':
                            cx2 = action.get('cx', j.x + TAM_JOGADOR // 2)
                            cy2 = action.get('cy', j.y + TAM_JOGADOR // 2)
                            dx2 = action.get('dx', 1.0)
                            dy2 = action.get('dy', 0.0)
                            _criar_tiro(j, projeteis, cx2, cy2, dx2, dy2, tempo)
                        elif act == 'boxfight_parede':
                            chave_r = tuple(action.get('chave', [0, 0, 'h']))
                            rd = action.get('rect', [0, 0, 1, 1])
                            _colocar_parede(paredes, chave_r, pygame.Rect(rd))
                        elif act == 'boxfight_arma':
                            j.arma = action.get('arma')

            # Movimento do jogador humano
            teclas = pygame.key.get_pressed()
            if jogador_humano.vivo:
                dx_mov, dy_mov = 0.0, 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:    dy_mov -= VEL_BOXFIGHT
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:  dy_mov += VEL_BOXFIGHT
                if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:  dx_mov -= VEL_BOXFIGHT
                if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: dx_mov += VEL_BOXFIGHT
                if dx_mov != 0 and dy_mov != 0:
                    f = VEL_BOXFIGHT / math.sqrt(dx_mov * dx_mov + dy_mov * dy_mov)
                    dx_mov *= f
                    dy_mov *= f
                jogador_humano.vx = dx_mov
                jogador_humano.vy = dy_mov

            # Cura com F (segurar 2.5s, 1 vez por round)
            if jogador_humano.vivo and not jogador_humano.cura_usado:
                if teclas[pygame.K_f]:
                    if jogador_humano.cura_inicio == 0:
                        jogador_humano.cura_inicio = tempo
                    jogador_humano.cura_ativo = True
                    if tempo - jogador_humano.cura_inicio >= CURA_DURACAO:
                        jogador_humano.hp = HP_MAX
                        jogador_humano.cura_usado = True
                        jogador_humano.cura_ativo = False
                        jogador_humano.cura_inicio = 0
                        cx_c, cy_c = jogador_humano.get_centro()
                        for _ in range(20):
                            p = Particula(cx_c + random.uniform(-15, 15),
                                          cy_c + random.uniform(-15, 15),
                                          (80, 255, 120))
                            p.velocidade_x = random.uniform(-4, 4)
                            p.velocidade_y = random.uniform(-5, -1)
                            p.vida = random.randint(15, 30)
                            p.tamanho = random.uniform(2, 5)
                            particulas.append(p)
                else:
                    jogador_humano.cura_ativo = False
                    jogador_humano.cura_inicio = 0
            elif not jogador_humano.vivo or jogador_humano.cura_usado:
                jogador_humano.cura_ativo = False
                jogador_humano.cura_inicio = 0

            # Tiro continuo com LMB mantido (metralhadora)
            mouse_buttons = pygame.mouse.get_pressed()
            if (mouse_buttons[0] and jogador_humano.vivo
                    and not jogador_humano.em_construcao
                    and not jogador_humano.modo_edicao
                    and jogador_humano.arma):
                info = ARMAS[jogador_humano.arma]
                if tempo - jogador_humano.tempo_ultimo_tiro >= info['cooldown']:
                    mouse_pos_s = convert_mouse_position(pygame.mouse.get_pos())
                    mx_world_c = float(mouse_pos_s[0]) + cam_x
                    my_world_c = float(mouse_pos_s[1]) + cam_y
                    cx_h, cy_h = jogador_humano.get_centro()
                    dx_t = mx_world_c - cx_h
                    dy_t = my_world_c - cy_h
                    dist_t = math.sqrt(dx_t * dx_t + dy_t * dy_t)
                    if dist_t > 0:
                        dx_t /= dist_t
                        dy_t /= dist_t
                    _criar_tiro(jogador_humano, projeteis, cx_h, cy_h, dx_t, dy_t, tempo)
                    jogador_humano.tempo_ultimo_tiro = tempo
                    if cliente:
                        cliente.send_minigame_action({
                            'action': 'boxfight_tiro',
                            'cx': cx_h, 'cy': cy_h,
                            'dx': dx_t, 'dy': dy_t,
                        })
                    try:
                        from src.utils.sound import gerar_som_tiro
                        som = pygame.mixer.Sound(gerar_som_tiro())
                        som.set_volume(0.12)
                        pygame.mixer.Channel(1).play(som)
                    except Exception:
                        pass

            # Construcao continua: segurando LMB no modo construcao
            if (mouse_buttons[0] and jogador_humano.vivo
                    and jogador_humano.em_construcao):
                mp_cb = convert_mouse_position(pygame.mouse.get_pos())
                mx_cb = float(mp_cb[0]) + cam_x
                my_cb = float(mp_cb[1]) + cam_y
                chave_cb, rect_cb = _obter_posicao_parede(mx_cb, my_cb)
                if chave_cb and rect_cb:
                    cx_cb, cy_cb = jogador_humano.get_centro()
                    ddx_cb = rect_cb.centerx - cx_cb
                    ddy_cb = rect_cb.centery - cy_cb
                    if ddx_cb * ddx_cb + ddy_cb * ddy_cb <= BUILD_MAX_DIST * BUILD_MAX_DIST:
                        if _colocar_parede(paredes, chave_cb, rect_cb,
                                           dono=jogador_humano) and cliente:
                            cliente.send_minigame_action({
                                'action': 'boxfight_parede',
                                'chave': list(chave_cb),
                                'rect': [rect_cb.x, rect_cb.y,
                                         rect_cb.width, rect_cb.height],
                            })

            # Mira do jogador humano
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            jogador_humano.mira_x = float(mouse_pos[0]) + cam_x
            jogador_humano.mira_y = float(mouse_pos[1]) + cam_y

            # Expandir selecao do drag de edicao enquanto LMB mantido
            if drag_edit_ativo and jogador_humano.modo_edicao and jogador_humano.vivo:
                if pygame.mouse.get_pressed()[0]:
                    mp_d = convert_mouse_position(pygame.mouse.get_pos())
                    cx_d, cy_d = jogador_humano.get_centro()
                    chave_d2, idx_d2 = _obter_secao_em(
                        float(mp_d[0]) + cam_x, float(mp_d[1]) + cam_y,
                        paredes, jogador_humano, cx_d, cy_d)
                    if chave_d2 is not None:
                        drag_edit_secoes.add((chave_d2, idx_d2))
                else:
                    # LMB solto fora de foco — aplica e limpa
                    for chave_d, idx_d in list(drag_edit_secoes):
                        _remover_secao_parede(paredes, chave_d, idx_d)
                    drag_edit_secoes.clear()
                    drag_edit_ativo = False

            # Bot AI
            for j in jogadores:
                if j.is_bot and j.vivo:
                    _bot_ai_boxfight(j, jogadores, paredes, tempo)
                    _bot_atirar(j, jogadores, paredes, projeteis, tempo)

            # Atualizar posicoes
            for j in jogadores:
                if j.vivo:
                    if not j.is_remote:
                        j.x += j.vx
                        j.y += j.vy
                    j.x = max(4, min(j.x, ARENA_W - TAM_JOGADOR - 4))
                    j.y = max(4, min(j.y, ARENA_H - TAM_JOGADOR - 4))

            # Colisao de jogadores com paredes (nao se aplica a remotos)
            for j in jogadores:
                if j.vivo and not j.is_remote:
                    _resolver_colisao_jogador_paredes(j, paredes)
                    j.x = max(4, min(j.x, ARENA_W - TAM_JOGADOR - 4))
                    j.y = max(4, min(j.y, ARENA_H - TAM_JOGADOR - 4))

            # Enviar posicao local
            if cliente and jogador_humano.vivo:
                cliente.send_minigame_action({
                    'action': 'boxfight_input',
                    'x': jogador_humano.x,
                    'y': jogador_humano.y,
                    'mx': jogador_humano.mira_x,
                    'my': jogador_humano.mira_y,
                })

            # Projeteis
            _atualizar_projeteis(projeteis, jogadores, paredes, particulas, kill_feed, tempo)

            # Checar fim da rodada
            vivos = [j for j in jogadores if j.vivo]
            if len(vivos) <= 1:
                round_vencedor = vivos[0] if vivos else None
                if round_vencedor:
                    round_vencedor.rodadas_vencidas += 1
                estado = "ROUND_END"
                tempo_estado = tempo

        elif estado == "ROUND_END":
            if tempo_no_estado >= TEMPO_ROUND_END:
                if rodada_atual >= NUM_RODADAS:
                    estado = "SCOREBOARD"
                    tempo_estado = tempo
                    scoreboard_start = tempo
                else:
                    rodada_atual += 1
                    for i, j in enumerate(jogadores):
                        j.reset_rodada(SPAWN_POINTS[i][0], SPAWN_POINTS[i][1])
                        if j.is_bot:
                            j.arma = random.choice(['spas', 'metralhadora'])
                    paredes.clear()
                    projeteis.clear()
                    particulas.clear()
                    flashes.clear()
                    kill_feed.clear()
                    drag_edit_secoes.clear()
                    drag_edit_ativo = False
                    estado = "COUNTDOWN"
                    tempo_estado = tempo

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                pygame.mouse.set_visible(True)
                return None

        # ============================================================
        #  CAMERA
        # ============================================================
        if jogador_humano.vivo:
            cam_x, cam_y = _atualizar_camera(jogador_humano, cam_x, cam_y)
        else:
            vivos_cam = [j for j in jogadores if j.vivo]
            if vivos_cam:
                cam_x, cam_y = _atualizar_camera(vivos_cam[0], cam_x, cam_y)

        # ============================================================
        #  ATUALIZAR PARTICULAS
        # ============================================================
        for p in particulas[:]:
            p.atualizar()
            if p.vida <= 0:
                particulas.remove(p)

        for f in flashes[:]:
            f['vida'] -= 1
            if f['vida'] <= 0:
                flashes.remove(f)

        # ============================================================
        #  DESENHAR
        # ============================================================
        _desenhar_arena_boxfight(tela, cam_x, cam_y, tempo)

        # Preview de construcao
        if jogador_humano.em_construcao and estado == "FIGHT" and jogador_humano.vivo:
            mp = convert_mouse_position(pygame.mouse.get_pos())
            pcx, pcy = jogador_humano.get_centro()
            _desenhar_preview_construcao(tela,
                                         float(mp[0]) + cam_x,
                                         float(mp[1]) + cam_y,
                                         cam_x, cam_y, paredes, pcx, pcy)

        # Paredes (azul para as proprias quando em modo edicao; cinza para selecionadas)
        _dono_ed = (jogador_humano
                    if (jogador_humano.modo_edicao and estado == "FIGHT" and jogador_humano.vivo)
                    else None)
        _desenhar_paredes(tela, paredes, cam_x, cam_y, _dono_ed, drag_edit_secoes)

        # Projeteis
        _desenhar_projeteis(tela, projeteis, cam_x, cam_y)

        # Particulas
        for p in particulas:
            px = int(p.x - cam_x)
            py = int(p.y - cam_y)
            if 0 <= px <= LARGURA and 0 <= py <= ALTURA_JOGO:
                pygame.draw.circle(tela, p.cor, (px, py), max(1, int(p.tamanho)))

        # Jogadores e armas
        for j in jogadores:
            if j.vivo:
                j.desenhar(tela, fonte_nomes, cam_x, cam_y)
                _desenhar_arma_boxfight(tela, j, cam_x, cam_y, tempo)

        # HUD
        if estado == "FIGHT":
            jogadores_vivos = len([j for j in jogadores if j.vivo])
            _desenhar_hud_boxfight(tela, jogador_humano, fonte_hud, fonte_peq,
                                   jogadores_vivos, rodada_atual, tempo)

        # Minimap
        if estado in ("FIGHT", "COUNTDOWN"):
            _desenhar_minimap_boxfight(tela, jogadores, jogador_humano, paredes, cam_x, cam_y)

        # Kill feed
        if estado in ("FIGHT", "ROUND_END"):
            _desenhar_kill_feed(tela, kill_feed, fonte_score, tempo)

        # Mira
        if estado in ("FIGHT", "COUNTDOWN"):
            mp = convert_mouse_position(pygame.mouse.get_pos())
            desenhar_mira(tela, mp, (mira_surface, mira_rect))

        # Countdown
        if estado == "COUNTDOWN":
            segundos = 3 - tempo_no_estado // 1000
            cd_text = str(max(0, segundos)) if segundos > 0 else "FIGHT!"
            cd_cor  = AMARELO if segundos > 0 else VERMELHO
            cd_surf = fonte_countdown.render(cd_text, True, cd_cor)
            tela.blit(cd_surf, (LARGURA // 2 - cd_surf.get_width() // 2,
                                 ALTURA_JOGO // 2 - cd_surf.get_height() // 2))

        # Round end
        if estado == "ROUND_END":
            ov = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 110))
            tela.blit(ov, (0, 0))
            if round_vencedor:
                msg = f"{round_vencedor.nome} venceu a rodada {rodada_atual}!"
                cor_msg = round_vencedor.cor
            else:
                msg = "Empate!"
                cor_msg = AMARELO
            msg_surf = fonte_grande.render(msg, True, cor_msg)
            tela.blit(msg_surf, (LARGURA // 2 - msg_surf.get_width() // 2,
                                  ALTURA_JOGO // 2 - msg_surf.get_height() // 2))

        # Scoreboard
        if estado == "SCOREBOARD":
            _desenhar_scoreboard_boxfight(tela, jogadores, fonte_grande, fonte_score,
                                          fonte_peq, tempo, scoreboard_start)

        # Intro fade + titulo
        if estado == "INTRO":
            if alpha_fade > 0:
                fade_surf = pygame.Surface((LARGURA, ALTURA_JOGO))
                fade_surf.fill((0, 0, 0))
                fade_surf.set_alpha(alpha_fade)
                tela.blit(fade_surf, (0, 0))
            if tempo_no_estado > 500:
                alpha_t = min(255, int((tempo_no_estado - 500) * 0.5))
                titulo_s = fonte_grande.render("BOXFIGHT", True, (255, 150, 50))
                titulo_s.set_alpha(alpha_t)
                tela.blit(titulo_s, (LARGURA // 2 - titulo_s.get_width() // 2,
                                      ALTURA_JOGO // 2 - titulo_s.get_height() // 2 - 20))
                sub_s = fonte_media.render("Construa. Atire. Sobreviva.", True, (220, 160, 80))
                sub_s.set_alpha(alpha_t)
                tela.blit(sub_s, (LARGURA // 2 - sub_s.get_width() // 2,
                                   ALTURA_JOGO // 2 + 20))

        present_frame()
        relogio.tick(60)
