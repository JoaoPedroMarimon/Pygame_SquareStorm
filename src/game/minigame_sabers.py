#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Sabers - Free-for-all com sabres de luz.
8 jogadores (humanos + bots), arena grande com camera, sabres de luz.
Ultimo sobrevivente vence a rodada. Melhor de 3 rodadas.
"""

import pygame
import math
import random
from src.config import *
from src.entities.particula import Particula, criar_explosao
from src.utils.visual import criar_estrelas, desenhar_estrelas, criar_mira, desenhar_mira
from src.utils.display_manager import present_frame, convert_mouse_position
from src.weapons.sabre_luz import (
    ativar_sabre, atualizar_sabre, arremessar_sabre,
    atualizar_sabre_arremessado, forcar_retorno_sabre,
    desenhar_sabre, desenhar_sabre_arremessado,
    alternar_modo_defesa, distancia_ponto_linha,
    criar_som_sabre_ativacao
)

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
HP_MAX = 2
NUM_RODADAS = 3

# Paleta de cores dos jogadores
PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Arena grande (maior que a tela)
ARENA_W = 3000
ARENA_H = 2000
ARENA_RECT = pygame.Rect(0, 0, ARENA_W, ARENA_H)

# Spawn points em circulo ao redor do centro
SPAWN_RAIO = 600
SPAWN_POINTS = []
for i in range(8):
    angulo = (2 * math.pi * i) / 8
    sx = ARENA_W // 2 + int(math.cos(angulo) * SPAWN_RAIO) - TAM_JOGADOR // 2
    sy = ARENA_H // 2 + int(math.sin(angulo) * SPAWN_RAIO) - TAM_JOGADOR // 2
    SPAWN_POINTS.append((sx, sy))

# Tempos de estado (ms)
TEMPO_INTRO = 2000
TEMPO_COLOR_SELECT = 5000
TEMPO_COUNTDOWN = 3000
TEMPO_ROUND_END = 2500
TEMPO_SCOREBOARD = 5000

# Velocidade de movimento
VEL_SABERS = 3.5

# Dash
DASH_VELOCIDADE = 25
DASH_DURACAO = 8
DASH_COOLDOWN = 500
DASH_INVULN_POS = 200

# Bot AI
BOT_STRAFE_INTERVALO = 800
BOT_DIST_IDEAL = 120
BOT_DIST_RECUAR = 60
BOT_DIST_AVANCAR = 200
BOT_ATAQUE_RANGE = 100
BOT_ARREMESSO_RANGE_MIN = 150
BOT_ARREMESSO_RANGE_MAX = 250

# Cores de sabre disponiveis
CORES_SABRE = [
    {'nome': 'Azul', 'cor_core': (200, 230, 255), 'cor_edge': (50, 150, 255), 'cor_glow': (100, 200, 255)},
    {'nome': 'Verde', 'cor_core': (200, 255, 200), 'cor_edge': (50, 255, 50), 'cor_glow': (100, 255, 100)},
    {'nome': 'Vermelho', 'cor_core': (255, 200, 200), 'cor_edge': (255, 50, 50), 'cor_glow': (255, 100, 100)},
    {'nome': 'Roxo', 'cor_core': (230, 200, 255), 'cor_edge': (180, 50, 255), 'cor_glow': (200, 100, 255)},
    {'nome': 'Amarelo', 'cor_core': (255, 255, 200), 'cor_edge': (255, 255, 50), 'cor_glow': (255, 255, 100)},
    {'nome': 'Branco', 'cor_core': (255, 255, 255), 'cor_edge': (220, 220, 255), 'cor_glow': (240, 240, 255)},
]

# Minimap
MINIMAP_W = 160
MINIMAP_H = int(MINIMAP_W * ARENA_H / ARENA_W)
MINIMAP_X = LARGURA - MINIMAP_W - 10
MINIMAP_Y = 10


# ============================================================
#  CLASSES
# ============================================================

class JogadorSabers:
    """Jogador no minigame Sabers."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_remote = is_remote
        self.hp = HP_MAX
        self.vivo = True
        self.kills = 0
        self.rodadas_vencidas = 0

        # Posicao
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0

        # Sabre
        self.cor_sabre_idx = 0  # indice em CORES_SABRE
        self.sabre_info = {
            'ativo': True,
            'animacao_ativacao': 100,
            'modo_defesa': False,
            'pos_cabo': (0, 0),
            'pos_ponta': (0, 0),
            'angulo': 0,
            'comprimento_atual': 90,
            'tempo_ultimo_hum': 0,
            'arremessado': False,
            'arremesso_pos_x': 0,
            'arremesso_pos_y': 0,
            'arremesso_vel_x': 0,
            'arremesso_vel_y': 0,
            'arremesso_rotacao': 0,
            'arremesso_retornando': False,
        }

        # Mira
        self.mira_x = 0.0
        self.mira_y = 0.0

        # Invulnerabilidade
        self.invulneravel_ate = 0

        # Cooldown de dano por alvo (dict: jogador_id -> ultimo_tempo)
        self.ultimo_dano_por_alvo = {}

        # Cores derivadas
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

        # Dash
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0

        # Bot AI
        self.bot_alvo = None
        self.bot_strafe_timer = 0
        self.bot_strafe_dir = 1
        self.bot_ataque_timer = 0
        self.bot_arremesso_timer = 0
        self.bot_defesa_timer = 0

    def reset_rodada(self, spawn_x, spawn_y):
        """Reseta para nova rodada."""
        self.hp = HP_MAX
        self.vivo = True
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.invulneravel_ate = 0
        self.ultimo_dano_por_alvo = {}
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0
        self.bot_alvo = None
        self.bot_strafe_timer = 0
        self.bot_ataque_timer = 0
        self.bot_arremesso_timer = 0
        self.bot_defesa_timer = 0
        # Resetar sabre
        self.sabre_info['ativo'] = True
        self.sabre_info['animacao_ativacao'] = 100
        self.sabre_info['modo_defesa'] = False
        self.sabre_info['arremessado'] = False
        self.sabre_info['arremesso_retornando'] = False
        self.sabre_info['comprimento_atual'] = 90

    def executar_dash(self, dx, dy):
        """Executa dash na direcao (dx, dy)."""
        tempo = pygame.time.get_ticks()
        if self.dash_ativo:
            return False
        if tempo - self.dash_tempo_cooldown < DASH_COOLDOWN:
            return False
        mag = math.sqrt(dx * dx + dy * dy)
        if mag < 0.01:
            dx, dy = 1.0, 0.0
        else:
            dx /= mag
            dy /= mag
        self.dash_ativo = True
        self.dash_frames_restantes = DASH_DURACAO
        self.dash_direcao = (dx, dy)
        self.dash_tempo_cooldown = tempo
        self.invulneravel_ate = tempo + 99999
        return True

    def atualizar_dash(self):
        """Atualiza estado do dash."""
        tempo = pygame.time.get_ticks()
        if self.dash_ativo:
            ddx, ddy = self.dash_direcao
            self.x += ddx * DASH_VELOCIDADE
            self.y += ddy * DASH_VELOCIDADE
            self.x = max(4, min(self.x, ARENA_W - TAM_JOGADOR - 4))
            self.y = max(4, min(self.y, ARENA_H - TAM_JOGADOR - 4))
            self.dash_frames_restantes -= 1
            if self.dash_frames_restantes <= 0:
                self.dash_ativo = False
                self.dash_tempo_fim = tempo
                self.invulneravel_ate = tempo + DASH_INVULN_POS
        if not self.dash_ativo and self.dash_tempo_fim > 0:
            if tempo - self.dash_tempo_fim >= DASH_INVULN_POS:
                self.dash_tempo_fim = 0

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)

    def get_centro(self):
        return (self.x + TAM_JOGADOR // 2, self.y + TAM_JOGADOR // 2)

    def desenhar(self, tela, fonte, cam_x, cam_y, show_hp=True):
        """Desenha o jogador na tela com offset de camera."""
        if not self.vivo:
            return

        tam = TAM_JOGADOR
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Nao desenhar se fora da tela
        if sx < -tam or sx > LARGURA + tam or sy < -tam or sy > ALTURA_JOGO + tam:
            return

        # Piscar se invulneravel
        tempo = pygame.time.get_ticks()
        if tempo < self.invulneravel_ate and (tempo // 80) % 2 == 0:
            return

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
        if show_hp:
            hp_w = tam
            hp_h = 4
            hp_x = sx
            hp_y = sy + tam + 4
            pygame.draw.rect(tela, (40, 40, 40), (hp_x, hp_y, hp_w, hp_h), 0, 2)
            hp_ratio = max(0, self.hp / HP_MAX)
            cor_hp = VERDE if hp_ratio > 0.5 else VERMELHO
            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h), 0, 2)


# ============================================================
#  FUNCOES AUXILIARES
# ============================================================

def _atualizar_camera(jogador, cam_x, cam_y):
    """Atualiza camera para seguir o jogador com interpolacao."""
    alvo_x = jogador.x + TAM_JOGADOR // 2 - LARGURA // 2
    alvo_y = jogador.y + TAM_JOGADOR // 2 - ALTURA_JOGO // 2

    # Interpolacao suave
    cam_x += (alvo_x - cam_x) * 0.08
    cam_y += (alvo_y - cam_y) * 0.08

    # Clampar aos limites da arena
    cam_x = max(0, min(cam_x, ARENA_W - LARGURA))
    cam_y = max(0, min(cam_y, ARENA_H - ALTURA_JOGO))

    return cam_x, cam_y


def _desenhar_arena(tela, cam_x, cam_y, tempo):
    """Desenha a arena espacial/futurista de sabres."""
    # Fundo espacial profundo
    tela.fill((4, 2, 12))

    # --- Estrelas de fundo (parallax lento) ---
    # Camada distante (move pouco com a camera - efeito parallax)
    parallax = 0.15
    for i in range(60):
        # Posicoes pseudo-aleatorias fixas baseadas no indice
        sx_base = (i * 1471 + 137) % 2000
        sy_base = (i * 947 + 251) % 1400
        sx = int(sx_base - cam_x * parallax) % (LARGURA + 40) - 20
        sy = int(sy_base - cam_y * parallax) % (ALTURA_JOGO + 40) - 20
        brilho = 40 + (i * 37) % 50
        # Estrelas cintilam
        cintila = math.sin(tempo / (300 + i * 17) + i * 2.3)
        brilho = int(brilho + cintila * 20)
        brilho = max(20, min(100, brilho))
        tam_e = 1 if i % 3 != 0 else 2
        pygame.draw.circle(tela, (brilho, brilho, brilho + 15), (sx, sy), tam_e)

    # --- Nebulosa sutil (manchas de cor no fundo) ---
    for i in range(5):
        nx_w = (i * 743 + 200) % ARENA_W
        ny_w = (i * 557 + 300) % ARENA_H
        nx_s = int(nx_w - cam_x * 0.3)
        ny_s = int(ny_w - cam_y * 0.3)
        if -120 <= nx_s <= LARGURA + 120 and -120 <= ny_s <= ALTURA_JOGO + 120:
            raio_neb = 80 + (i * 31) % 60
            neb_surf = pygame.Surface((raio_neb * 2, raio_neb * 2), pygame.SRCALPHA)
            # Cores nebulosas alternadas
            cores_neb = [(20, 8, 40), (8, 12, 35), (25, 5, 30), (10, 15, 30), (15, 5, 35)]
            cn = cores_neb[i % len(cores_neb)]
            alpha_neb = int(18 + 8 * math.sin(tempo / 2000 + i))
            pygame.draw.circle(neb_surf, (*cn, alpha_neb), (raio_neb, raio_neb), raio_neb)
            tela.blit(neb_surf, (nx_s - raio_neb, ny_s - raio_neb))

    # --- Piso: placas metalicas futuristas ---
    placa = 80  # tamanho de cada placa
    start_px = max(0, int(cam_x // placa) * placa)
    start_py = max(0, int(cam_y // placa) * placa)
    end_px = min(ARENA_W, int((cam_x + LARGURA) // placa + 2) * placa)
    end_py = min(ARENA_H, int((cam_y + ALTURA_JOGO) // placa + 2) * placa)

    for py_t in range(start_py, end_py, placa):
        for px_t in range(start_px, end_px, placa):
            sx = int(px_t - cam_x)
            sy = int(py_t - cam_y)
            idx = (px_t // placa + py_t // placa)

            # Cor base da placa com variacao sutil
            variacao = ((idx * 7 + 3) % 5)
            r = 14 + variacao
            g = 12 + variacao
            b = 22 + variacao * 2
            pygame.draw.rect(tela, (r, g, b), (sx, sy, placa, placa))

            # Borda interna da placa (juntas metalicas)
            cor_junta = (22 + variacao, 18 + variacao, 32 + variacao * 2)
            pygame.draw.rect(tela, cor_junta, (sx, sy, placa, placa), 1)

            # Detalhe no canto de algumas placas (parafusos)
            if idx % 4 == 0:
                pygame.draw.circle(tela, (28, 24, 40), (sx + 5, sy + 5), 2, 1)
                pygame.draw.circle(tela, (28, 24, 40), (sx + placa - 5, sy + 5), 2, 1)
                pygame.draw.circle(tela, (28, 24, 40), (sx + 5, sy + placa - 5), 2, 1)
                pygame.draw.circle(tela, (28, 24, 40), (sx + placa - 5, sy + placa - 5), 2, 1)

            # Linha de luz neon em algumas placas
            if idx % 7 == 0:
                pulso = (math.sin(tempo / 600 + idx * 0.5) + 1) / 2
                neon_alpha = int(15 + pulso * 20)
                cor_neon = (neon_alpha, neon_alpha // 2, neon_alpha * 2)
                pygame.draw.line(tela, cor_neon, (sx + 10, sy + placa // 2), (sx + placa - 10, sy + placa // 2), 1)

    # --- Linhas de energia no piso (trilhas luminosas) ---
    pulso_energia = (math.sin(tempo / 800) + 1) / 2
    for gy in range(0, ARENA_H, 320):
        sy = int(gy - cam_y)
        if -2 <= sy <= ALTURA_JOGO + 2:
            alpha_e = int(18 + pulso_energia * 14)
            cor_trilha = (alpha_e // 2, alpha_e // 3, alpha_e)
            pygame.draw.line(tela, cor_trilha, (0, sy), (LARGURA, sy), 1)
            # Glow da trilha
            glow_surf = pygame.Surface((LARGURA, 6), pygame.SRCALPHA)
            glow_surf.fill((20, 10, 50, int(8 + pulso_energia * 6)))
            tela.blit(glow_surf, (0, sy - 3))

    for gx in range(0, ARENA_W, 320):
        sx = int(gx - cam_x)
        if -2 <= sx <= LARGURA + 2:
            alpha_e = int(18 + pulso_energia * 14)
            cor_trilha = (alpha_e // 2, alpha_e // 3, alpha_e)
            pygame.draw.line(tela, cor_trilha, (sx, 0), (sx, ALTURA_JOGO), 1)

    # --- Marcas de spawn (hexagonos nos pontos de spawn) ---
    for i, (spx, spy) in enumerate(SPAWN_POINTS):
        msx = int(spx + TAM_JOGADOR // 2 - cam_x)
        msy = int(spy + TAM_JOGADOR // 2 - cam_y)
        if -50 <= msx <= LARGURA + 50 and -50 <= msy <= ALTURA_JOGO + 50:
            # Hexagono
            hex_r = 25
            cor_hex = (30, 20, 55)
            pts = []
            for h in range(6):
                ang = math.pi / 6 + h * math.pi / 3
                pts.append((msx + int(math.cos(ang) * hex_r), msy + int(math.sin(ang) * hex_r)))
            pygame.draw.polygon(tela, cor_hex, pts, 1)
            # Numero do spawn
            pygame.draw.circle(tela, cor_hex, (msx, msy), 3, 1)

    # --- Bordas da arena com glow forte ---
    borda_cor = (90, 50, 160)
    borda_glow = (50, 25, 110)
    borda_glow2 = (30, 15, 70)
    # Superior
    by = int(-cam_y)
    if -10 <= by <= ALTURA_JOGO:
        pygame.draw.line(tela, borda_glow2, (0, by - 4), (LARGURA, by - 4), 8)
        pygame.draw.line(tela, borda_glow, (0, by - 1), (LARGURA, by - 1), 4)
        pygame.draw.line(tela, borda_cor, (0, by), (LARGURA, by), 2)
    # Inferior
    by = int(ARENA_H - cam_y)
    if 0 <= by <= ALTURA_JOGO + 10:
        pygame.draw.line(tela, borda_glow2, (0, by + 4), (LARGURA, by + 4), 8)
        pygame.draw.line(tela, borda_glow, (0, by + 1), (LARGURA, by + 1), 4)
        pygame.draw.line(tela, borda_cor, (0, by), (LARGURA, by), 2)
    # Esquerda
    bx = int(-cam_x)
    if -10 <= bx <= LARGURA:
        pygame.draw.line(tela, borda_glow2, (bx - 4, 0), (bx - 4, ALTURA_JOGO), 8)
        pygame.draw.line(tela, borda_glow, (bx - 1, 0), (bx - 1, ALTURA_JOGO), 4)
        pygame.draw.line(tela, borda_cor, (bx, 0), (bx, ALTURA_JOGO), 2)
    # Direita
    bx = int(ARENA_W - cam_x)
    if 0 <= bx <= LARGURA + 10:
        pygame.draw.line(tela, borda_glow2, (bx + 4, 0), (bx + 4, ALTURA_JOGO), 8)
        pygame.draw.line(tela, borda_glow, (bx + 1, 0), (bx + 1, ALTURA_JOGO), 4)
        pygame.draw.line(tela, borda_cor, (bx, 0), (bx, ALTURA_JOGO), 2)

    # --- Particulas flutuantes (poeira estelar) ---
    for i in range(18):
        px_w = ((tempo * 0.018 + i * 347) % ARENA_W)
        py_w = ((tempo * 0.012 + i * 523) % ARENA_H)
        px_s = int(px_w - cam_x)
        py_s = int(py_w - cam_y)
        if 0 <= px_s <= LARGURA and 0 <= py_s <= ALTURA_JOGO:
            brilho = int(35 + 25 * math.sin(tempo / 400 + i * 1.7))
            tam_p = 1 if i % 2 == 0 else 2
            pygame.draw.circle(tela, (brilho, brilho, brilho + 25), (px_s, py_s), tam_p)


def _desenhar_minimap(tela, jogadores, jogador_local, cam_x, cam_y):
    """Desenha minimap no canto superior direito."""
    # Fundo
    minimap_surf = pygame.Surface((MINIMAP_W, MINIMAP_H), pygame.SRCALPHA)
    minimap_surf.fill((0, 0, 0, 150))

    # Bordas da arena no minimap
    pygame.draw.rect(minimap_surf, (60, 50, 90), (0, 0, MINIMAP_W, MINIMAP_H), 1)

    # Viewport
    vx = int((cam_x / ARENA_W) * MINIMAP_W)
    vy = int((cam_y / ARENA_H) * MINIMAP_H)
    vw = int((LARGURA / ARENA_W) * MINIMAP_W)
    vh = int((ALTURA_JOGO / ARENA_H) * MINIMAP_H)
    pygame.draw.rect(minimap_surf, (100, 100, 150, 80), (vx, vy, vw, vh), 1)

    # Jogadores
    for j in jogadores:
        if not j.vivo:
            continue
        mx = int((j.x / ARENA_W) * MINIMAP_W)
        my = int((j.y / ARENA_H) * MINIMAP_H)
        tam = 4 if j is jogador_local else 3
        cor = j.cor if j is not jogador_local else BRANCO
        pygame.draw.rect(minimap_surf, cor, (mx - tam // 2, my - tam // 2, tam, tam))

    tela.blit(minimap_surf, (MINIMAP_X, MINIMAP_Y))


def _desenhar_sabre_jogador(tela, jogador, tempo, cam_x, cam_y):
    """Desenha o sabre de um jogador com offset de camera."""
    if not jogador.vivo:
        return

    sabre = jogador.sabre_info
    cor_sabre = CORES_SABRE[jogador.cor_sabre_idx]

    # Se arremessado, desenhar versao girando
    if sabre.get('arremessado', False):
        pos_x = sabre['arremesso_pos_x'] - cam_x
        pos_y = sabre['arremesso_pos_y'] - cam_y

        # Fora da tela? nao desenhar
        if pos_x < -100 or pos_x > LARGURA + 100 or pos_y < -100 or pos_y > ALTURA_JOGO + 100:
            return

        rotacao = math.radians(sabre['arremesso_rotacao'])
        comprimento_lamina = 90
        comprimento_cabo = 25
        largura_lamina = 6

        cos_r = math.cos(rotacao)
        sin_r = math.sin(rotacao)

        cabo_inicio_x = -comprimento_cabo
        lamina_fim_x = comprimento_lamina

        p1_x = pos_x + cabo_inicio_x * cos_r
        p1_y = pos_y + cabo_inicio_x * sin_r
        p2_x = pos_x + lamina_fim_x * cos_r
        p2_y = pos_y + lamina_fim_x * sin_r

        pygame.draw.line(tela, cor_sabre['cor_edge'], (p1_x, p1_y), (p2_x, p2_y), largura_lamina + 2)
        pygame.draw.line(tela, cor_sabre['cor_core'], (p1_x, p1_y), (p2_x, p2_y), largura_lamina - 2)
        pygame.draw.line(tela, (255, 255, 255), (p1_x, p1_y), (p2_x, p2_y), 2)

        # Cabo
        cor_cabo_metal = (150, 150, 160)
        largura_cabo = 8
        half_cabo = largura_cabo // 2
        cabo_points = []
        for offset in [-half_cabo, half_cabo]:
            perp_x = -sin_r * offset
            perp_y = cos_r * offset
            cabo_points.append((
                pos_x - comprimento_cabo * cos_r + perp_x,
                pos_y - comprimento_cabo * sin_r + perp_y
            ))
        for offset in [half_cabo, -half_cabo]:
            perp_x = -sin_r * offset
            perp_y = cos_r * offset
            cabo_points.append((pos_x + perp_x, pos_y + perp_y))
        pygame.draw.polygon(tela, cor_cabo_metal, cabo_points)
        return

    # Sabre na mao - calcular posicoes no mundo, depois converter pra tela
    centro_x = jogador.x + TAM_JOGADOR // 2
    centro_y = jogador.y + TAM_JOGADOR // 2

    # Calcular angulo baseado na mira
    dx = jogador.mira_x - centro_x
    dy = jogador.mira_y - centro_y

    if sabre['modo_defesa']:
        angulo_mouse = math.atan2(dy, dx)
        angulo = angulo_mouse - math.pi / 2
    else:
        angulo = math.atan2(dy, dx)

    cos_a = math.cos(angulo)
    sin_a = math.sin(angulo)

    if sabre['modo_defesa']:
        angulo_mouse = math.atan2(dy, dx)
        distancia_cabo = 35
        cabo_x = centro_x + math.cos(angulo_mouse) * distancia_cabo
        cabo_y = centro_y + math.sin(angulo_mouse) * distancia_cabo
    else:
        distancia_cabo = 20
        cabo_x = centro_x + cos_a * distancia_cabo
        cabo_y = centro_y + sin_a * distancia_cabo

    comprimento_lamina = 90
    ponta_x = cabo_x + cos_a * comprimento_lamina
    ponta_y = cabo_y + sin_a * comprimento_lamina

    # Atualizar sabre_info para colisoes
    sabre['pos_cabo'] = (cabo_x, cabo_y)
    sabre['pos_ponta'] = (ponta_x, ponta_y)
    sabre['angulo'] = angulo
    sabre['comprimento_atual'] = comprimento_lamina

    # Converter para coordenadas de tela
    scabo_x = cabo_x - cam_x
    scabo_y = cabo_y - cam_y
    sponta_x = ponta_x - cam_x
    sponta_y = ponta_y - cam_y

    # Fora da tela?
    min_sx = min(scabo_x, sponta_x)
    max_sx = max(scabo_x, sponta_x)
    min_sy = min(scabo_y, sponta_y)
    max_sy = max(scabo_y, sponta_y)
    if max_sx < -20 or min_sx > LARGURA + 20 or max_sy < -20 or min_sy > ALTURA_JOGO + 20:
        return

    # Cabo
    cor_cabo_metal = (150, 150, 160)
    cor_cabo_detalhes = (100, 100, 110)
    cabo_comprimento = 25
    cabo_largura = 6
    half_width = cabo_largura // 2
    half_length = cabo_comprimento // 2
    perp_x = -sin_a * half_width
    perp_y = cos_a * half_width
    para_x = cos_a * half_length
    para_y = sin_a * half_length

    cabo_points = [
        (scabo_x - para_x + perp_x, scabo_y - para_y + perp_y),
        (scabo_x + para_x + perp_x, scabo_y + para_y + perp_y),
        (scabo_x + para_x - perp_x, scabo_y + para_y - perp_y),
        (scabo_x - para_x - perp_x, scabo_y - para_y - perp_y),
    ]
    pygame.draw.polygon(tela, cor_cabo_metal, cabo_points)
    pygame.draw.polygon(tela, cor_cabo_detalhes, cabo_points, 2)

    # Detalhes do cabo
    for i in range(3):
        ring_pos = 0.2 + i * 0.3
        ring_x = scabo_x + (ring_pos - 0.5) * cabo_comprimento * cos_a
        ring_y = scabo_y + (ring_pos - 0.5) * cabo_comprimento * sin_a
        ring_perp_x = -sin_a * (cabo_largura - 1)
        ring_perp_y = cos_a * (cabo_largura - 1)
        pygame.draw.line(tela, cor_cabo_detalhes,
                         (ring_x - ring_perp_x, ring_y - ring_perp_y),
                         (ring_x + ring_perp_x, ring_y + ring_perp_y), 2)

    # Emissor
    emissor_x = scabo_x + half_length * cos_a
    emissor_y = scabo_y + half_length * sin_a
    pygame.draw.circle(tela, (200, 200, 220), (int(emissor_x), int(emissor_y)), 4)

    # Lamina
    pulso = (math.sin(tempo / 200) + 1) / 2
    vibracao = math.sin(tempo / 50) * 0.5
    lamina_end_x = sponta_x + vibracao * sin_a
    lamina_end_y = sponta_y - vibracao * cos_a

    pygame.draw.line(tela, cor_sabre['cor_edge'],
                     (emissor_x, emissor_y), (lamina_end_x, lamina_end_y), 6)
    pygame.draw.line(tela, cor_sabre['cor_core'],
                     (emissor_x, emissor_y), (lamina_end_x, lamina_end_y), 3)
    pygame.draw.line(tela, (255, 255, 255),
                     (emissor_x, emissor_y), (lamina_end_x, lamina_end_y), 1)

    # Faiscas na ponta
    if pulso > 0.7:
        for i in range(3):
            spark_x = lamina_end_x + random.uniform(-3, 3)
            spark_y = lamina_end_y + random.uniform(-3, 3)
            pygame.draw.circle(tela, cor_sabre['cor_core'],
                               (int(spark_x), int(spark_y)), random.randint(1, 2))

    # Particulas de energia
    for i in range(4):
        pp = (i + 1) / 5
        px = emissor_x + (lamina_end_x - emissor_x) * pp + random.uniform(-1, 1)
        py = emissor_y + (lamina_end_y - emissor_y) * pp + random.uniform(-1, 1)
        if int(150 * pulso) > 50:
            pygame.draw.circle(tela, cor_sabre['cor_glow'], (int(px), int(py)), 2)


def _processar_dano_sabre_minigame(atacante, alvo, tempo):
    """Processa dano do sabre do atacante no alvo. Retorna True se acertou."""
    if not atacante.vivo or not alvo.vivo:
        return False
    if atacante is alvo:
        return False

    sabre = atacante.sabre_info
    if not sabre['ativo'] or sabre.get('arremessado', False):
        return False
    if sabre['comprimento_atual'] <= 10:
        return False

    # Verificar invulnerabilidade do alvo
    if tempo < alvo.invulneravel_ate:
        return False

    # Cooldown por alvo
    alvo_id = id(alvo)
    ultimo = atacante.ultimo_dano_por_alvo.get(alvo_id, 0)
    if tempo - ultimo < 500:
        return False

    # Calcular lamina (excluindo cabo)
    cabo_x, cabo_y = sabre['pos_cabo']
    ponta_x, ponta_y = sabre['pos_ponta']
    angulo = sabre['angulo']
    tamanho_cabo = 15

    lamina_inicio_x = cabo_x + math.cos(angulo) * tamanho_cabo
    lamina_inicio_y = cabo_y + math.sin(angulo) * tamanho_cabo
    linha_inicio = (lamina_inicio_x, lamina_inicio_y)
    linha_fim = (ponta_x, ponta_y)

    centro_alvo = alvo.get_centro()
    distancia = distancia_ponto_linha(centro_alvo, linha_inicio, linha_fim)

    raio_hit = 8 + TAM_JOGADOR // 4

    if distancia <= raio_hit:
        atacante.ultimo_dano_por_alvo[alvo_id] = tempo
        alvo.hp -= 1
        alvo.invulneravel_ate = tempo + 300
        if alvo.hp <= 0:
            alvo.vivo = False
            atacante.kills += 1
        return True

    return False


def _processar_dano_sabre_arremessado_minigame(atacante, alvo, tempo):
    """Processa dano do sabre arremessado do atacante no alvo."""
    if not atacante.vivo or not alvo.vivo:
        return False
    if atacante is alvo:
        return False

    sabre = atacante.sabre_info
    if not sabre.get('arremessado', False):
        return False

    if tempo < alvo.invulneravel_ate:
        return False

    # Cooldown
    alvo_id = id(alvo)
    ultimo = atacante.ultimo_dano_por_alvo.get(alvo_id, 0)
    if tempo - ultimo < 300:
        return False

    raio_dano = 50
    centro_alvo = alvo.get_centro()
    dx = centro_alvo[0] - sabre['arremesso_pos_x']
    dy = centro_alvo[1] - sabre['arremesso_pos_y']
    distancia = math.sqrt(dx ** 2 + dy ** 2)

    if distancia < raio_dano:
        atacante.ultimo_dano_por_alvo[alvo_id] = tempo
        alvo.hp -= 1
        alvo.invulneravel_ate = tempo + 300
        if alvo.hp <= 0:
            alvo.vivo = False
            atacante.kills += 1
        return True

    return False


def _verificar_colisao_sabre_defesa(atacante, defensor):
    """
    Verifica se o sabre arremessado do atacante colidiu com o sabre
    em modo defesa do defensor. Se sim, forca retorno do sabre.
    Retorna True se houve colisao.
    """
    if not atacante.vivo or not defensor.vivo:
        return False
    if atacante is defensor:
        return False

    sabre_atk = atacante.sabre_info
    sabre_def = defensor.sabre_info

    # Atacante precisa ter sabre arremessado
    if not sabre_atk.get('arremessado', False):
        return False
    # Defensor precisa estar em modo defesa e sabre ativo (nao arremessado)
    if not sabre_def['ativo'] or not sabre_def['modo_defesa']:
        return False
    if sabre_def.get('arremessado', False):
        return False

    # Posicao do sabre voando
    sabre_pos = (sabre_atk['arremesso_pos_x'], sabre_atk['arremesso_pos_y'])

    # Lamina do defensor
    cabo_def = sabre_def['pos_cabo']
    ponta_def = sabre_def['pos_ponta']

    distancia = distancia_ponto_linha(sabre_pos, cabo_def, ponta_def)

    if distancia < 40:  # raio de colisao sabre-vs-sabre
        # Forcar retorno do sabre arremessado
        sabre_atk['arremesso_retornando'] = True
        # Inverter velocidade para efeito visual
        sabre_atk['arremesso_vel_x'] = -sabre_atk['arremesso_vel_x']
        sabre_atk['arremesso_vel_y'] = -sabre_atk['arremesso_vel_y']
        return True

    return False


def _atualizar_sabre_arremessado_minigame(jogador):
    """Atualiza fisica do sabre arremessado com limites da arena."""
    sabre = jogador.sabre_info
    if not sabre.get('arremessado', False):
        return False

    # Rotacao
    sabre['arremesso_rotacao'] = (sabre['arremesso_rotacao'] + 25) % 360

    centro_x = jogador.x + TAM_JOGADOR // 2
    centro_y = jogador.y + TAM_JOGADOR // 2

    # Verificar retorno
    if not sabre['arremesso_retornando']:
        distancia_do_jogador = math.sqrt(
            (sabre['arremesso_pos_x'] - centro_x) ** 2 +
            (sabre['arremesso_pos_y'] - centro_y) ** 2
        )
        if distancia_do_jogador > 60:
            if (sabre['arremesso_pos_x'] <= 20 or
                    sabre['arremesso_pos_x'] >= ARENA_W - 20 or
                    sabre['arremesso_pos_y'] <= 20 or
                    sabre['arremesso_pos_y'] >= ARENA_H - 20):
                sabre['arremesso_retornando'] = True

        # Distancia maxima
        if distancia_do_jogador > 700:
            sabre['arremesso_retornando'] = True

    if sabre['arremesso_retornando']:
        dx = centro_x - sabre['arremesso_pos_x']
        dy = centro_y - sabre['arremesso_pos_y']
        distancia = math.sqrt(dx ** 2 + dy ** 2)

        if distancia < 30:
            sabre['arremessado'] = False
            sabre['arremesso_retornando'] = False
            return False

        dx /= distancia
        dy /= distancia
        sabre['arremesso_vel_x'] = dx * 15
        sabre['arremesso_vel_y'] = dy * 15

    sabre['arremesso_pos_x'] += sabre['arremesso_vel_x']
    sabre['arremesso_pos_y'] += sabre['arremesso_vel_y']

    return True


def _bot_ai_sabers(bot, jogadores, tempo):
    """IA do bot no modo sabers."""
    if not bot.vivo:
        bot.vx = 0
        bot.vy = 0
        return

    bot_cx, bot_cy = bot.get_centro()

    # Encontrar alvo mais proximo
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

    if not melhor_alvo:
        bot.vx = 0
        bot.vy = 0
        return

    bot.bot_alvo = melhor_alvo

    dx = melhor_alvo.x - bot.x
    dy = melhor_alvo.y - bot.y
    dist = melhor_dist
    if dist < 1:
        dist = 1
    dir_x = dx / dist
    dir_y = dy / dist

    # Strafe
    if tempo > bot.bot_strafe_timer:
        bot.bot_strafe_timer = tempo + BOT_STRAFE_INTERVALO + random.randint(-200, 200)
        bot.bot_strafe_dir = -bot.bot_strafe_dir

    strafe_x = -dir_y * bot.bot_strafe_dir
    strafe_y = dir_x * bot.bot_strafe_dir

    mover_x = strafe_x
    mover_y = strafe_y

    # Ajuste de distancia
    if dist < BOT_DIST_RECUAR:
        mover_x -= dir_x * 0.7
        mover_y -= dir_y * 0.7
    elif dist > BOT_DIST_AVANCAR:
        mover_x += dir_x * 0.5
        mover_y += dir_y * 0.5
    elif dist > BOT_DIST_IDEAL:
        mover_x += dir_x * 0.3
        mover_y += dir_y * 0.3

    # Evitar bordas
    margem = 80
    if bot_cx < margem:
        mover_x += 0.8
    elif bot_cx > ARENA_W - margem:
        mover_x -= 0.8
    if bot_cy < margem:
        mover_y += 0.8
    elif bot_cy > ARENA_H - margem:
        mover_y -= 0.8

    # Normalizar
    mag = math.sqrt(mover_x * mover_x + mover_y * mover_y)
    if mag > 0:
        mover_x /= mag
        mover_y /= mag

    bot.vx = mover_x * VEL_SABERS
    bot.vy = mover_y * VEL_SABERS

    # Mira: mirar no alvo
    bot.mira_x = melhor_alvo.x + TAM_JOGADOR // 2
    bot.mira_y = melhor_alvo.y + TAM_JOGADOR // 2

    # Detectar sabre arremessado vindo na direcao
    for j in jogadores:
        if j is bot or not j.vivo:
            continue
        s = j.sabre_info
        if s.get('arremessado', False) and not s.get('arremesso_retornando', False):
            sdx = bot_cx - s['arremesso_pos_x']
            sdy = bot_cy - s['arremesso_pos_y']
            sdist = math.sqrt(sdx * sdx + sdy * sdy)
            if sdist < 150:
                # Ativar modo defesa apontando para o sabre
                if not bot.sabre_info['modo_defesa'] and not bot.sabre_info.get('arremessado', False):
                    bot.sabre_info['modo_defesa'] = True
                    bot.bot_defesa_timer = tempo + 800
                    bot.mira_x = s['arremesso_pos_x']
                    bot.mira_y = s['arremesso_pos_y']
                break

    # Desativar defesa apos timer
    if bot.sabre_info['modo_defesa'] and tempo > bot.bot_defesa_timer:
        bot.sabre_info['modo_defesa'] = False

    # Arremessar sabre
    if not bot.sabre_info.get('arremessado', False) and not bot.sabre_info['modo_defesa']:
        if BOT_ARREMESSO_RANGE_MIN < dist < BOT_ARREMESSO_RANGE_MAX:
            if random.random() < 0.005 and tempo > bot.bot_arremesso_timer:
                # Arremessar
                alvo_pos = (melhor_alvo.x + TAM_JOGADOR // 2, melhor_alvo.y + TAM_JOGADOR // 2)
                _arremessar_sabre_jogador(bot, alvo_pos)
                bot.bot_arremesso_timer = tempo + 2000

    # Dash
    if not bot.dash_ativo:
        if dist < 50:
            # Muito perto - dash para longe
            bot.executar_dash(-dir_x, -dir_y)
        elif random.random() < 0.005:
            bot.executar_dash(-dir_y * bot.bot_strafe_dir, dir_x * bot.bot_strafe_dir)


def _arremessar_sabre_jogador(jogador, pos_alvo):
    """Arremessa o sabre de um jogador na direcao do alvo."""
    sabre = jogador.sabre_info
    if sabre.get('arremessado', False) or sabre['modo_defesa']:
        return False

    centro_x = jogador.x + TAM_JOGADOR // 2
    centro_y = jogador.y + TAM_JOGADOR // 2

    dx = pos_alvo[0] - centro_x
    dy = pos_alvo[1] - centro_y
    distancia = math.sqrt(dx ** 2 + dy ** 2)
    if distancia == 0:
        return False

    dx /= distancia
    dy /= distancia

    sabre['arremessado'] = True
    sabre['arremesso_pos_x'] = centro_x
    sabre['arremesso_pos_y'] = centro_y
    sabre['arremesso_vel_x'] = dx * 12
    sabre['arremesso_vel_y'] = dy * 12
    sabre['arremesso_rotacao'] = 0
    sabre['arremesso_retornando'] = False
    sabre['modo_defesa'] = False

    return True


def _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_score, fonte_peq, tempo, start_time):
    """Desenha o scoreboard final."""
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
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

        if rank == 0:
            linha_surf.fill((255, 200, 0, 30))
        elif rank == 1:
            linha_surf.fill((200, 200, 200, 20))
        elif rank == 2:
            linha_surf.fill((180, 100, 30, 20))
        else:
            linha_surf.fill((40, 40, 60, 20))

        tela.blit(linha_surf, (linha_x, y))

        medalhas = ["1st", "2nd", "3rd"]
        pos_text = medalhas[rank] if rank < 3 else f"{rank + 1}th"
        pos_cor = [(255, 215, 0), (200, 200, 210), (205, 127, 50)][rank] if rank < 3 else (150, 150, 160)
        pos_s = fonte_score.render(pos_text, True, pos_cor)
        tela.blit(pos_s, (linha_x + 15, y + 8))

        # Quadrado do jogador
        sq_x = linha_x + 80
        sq_y = y + 6
        sq_tam = 28
        cor_esc = tuple(max(0, c - 60) for c in j.cor)
        pygame.draw.rect(tela, cor_esc, (sq_x, sq_y, sq_tam, sq_tam), 0, 4)
        pygame.draw.rect(tela, j.cor, (sq_x + 2, sq_y + 2, sq_tam - 4, sq_tam - 4), 0, 3)

        # Sabre ao lado do quadrado
        cor_s = CORES_SABRE[j.cor_sabre_idx]
        pygame.draw.line(tela, cor_s['cor_edge'], (sq_x + sq_tam + 5, sq_y + 2), (sq_x + sq_tam + 5, sq_y + sq_tam - 2), 4)
        pygame.draw.line(tela, cor_s['cor_core'], (sq_x + sq_tam + 5, sq_y + 2), (sq_x + sq_tam + 5, sq_y + sq_tam - 2), 2)

        nome_s = fonte_score.render(j.nome, True, BRANCO)
        tela.blit(nome_s, (sq_x + sq_tam + 18, y + 8))

        stats_s = fonte_peq.render(f"{j.rodadas_vencidas}R  {j.kills}K", True, (180, 255, 180))
        tela.blit(stats_s, (linha_x + 370, y + 12))

        if rank < 3:
            pygame.draw.rect(tela, pos_cor, (linha_x, y, linha_w, 42), 1, 3)

    if tempo_decorrido > 3000:
        inst = fonte_peq.render("Voltando ao menu...", True, (120, 120, 140))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))


def _desenhar_color_select(tela, jogador_local, fonte_grande, fonte_media, fonte_peq, tempo, tempo_restante):
    """Desenha a tela de selecao de cor do sabre."""
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    tela.blit(overlay, (0, 0))

    titulo = fonte_grande.render("ESCOLHA A COR DO SABRE", True, (200, 220, 255))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 80))

    # Timer
    timer_s = fonte_media.render(f"{max(0, tempo_restante / 1000):.1f}s", True, BRANCO)
    tela.blit(timer_s, (LARGURA // 2 - timer_s.get_width() // 2, 130))

    # Opcoes de cor
    total_w = len(CORES_SABRE) * 100
    start_x = LARGURA // 2 - total_w // 2

    for i, cor_info in enumerate(CORES_SABRE):
        x = start_x + i * 100
        y = 200
        w, h = 80, 120

        selecionado = (i == jogador_local.cor_sabre_idx)

        # Fundo
        bg_cor = (40, 40, 60) if not selecionado else (60, 60, 100)
        pygame.draw.rect(tela, bg_cor, (x, y, w, h), 0, 8)

        if selecionado:
            pulso = (math.sin(tempo / 300) + 1) / 2
            borda_cor = tuple(min(255, int(c * (0.7 + 0.3 * pulso))) for c in cor_info['cor_glow'])
            pygame.draw.rect(tela, borda_cor, (x, y, w, h), 3, 8)
        else:
            pygame.draw.rect(tela, (80, 80, 100), (x, y, w, h), 1, 8)

        # Preview do sabre (linha vertical)
        sabre_x = x + w // 2
        sabre_y1 = y + 15
        sabre_y2 = y + h - 30
        pygame.draw.line(tela, cor_info['cor_edge'], (sabre_x, sabre_y1), (sabre_x, sabre_y2), 6)
        pygame.draw.line(tela, cor_info['cor_core'], (sabre_x, sabre_y1), (sabre_x, sabre_y2), 3)
        pygame.draw.line(tela, (255, 255, 255), (sabre_x, sabre_y1), (sabre_x, sabre_y2), 1)

        # Cabo
        pygame.draw.rect(tela, (150, 150, 160), (sabre_x - 3, sabre_y2, 6, 15), 0, 2)

        # Nome
        nome_s = fonte_peq.render(cor_info['nome'], True, BRANCO)
        tela.blit(nome_s, (x + w // 2 - nome_s.get_width() // 2, y + h - 12))

        # Tecla
        tecla_s = fonte_peq.render(str(i + 1), True, (150, 150, 180))
        tela.blit(tecla_s, (x + w // 2 - tecla_s.get_width() // 2, y + h + 5))

    # Instrucoes
    inst = fonte_peq.render("Pressione 1-6 ou clique para escolher  |  Cor padrao: Azul", True, (120, 120, 160))
    tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, 350))


def _desenhar_hud_sabers(tela, jogador, fonte_hud, fonte_peq, jogadores_vivos, rodada, tempo):
    """Desenha HUD do minigame sabers."""
    # HP como coracoes
    for i in range(HP_MAX):
        hx = 15 + i * 25
        hy = 10
        if i < jogador.hp:
            pygame.draw.rect(tela, VERMELHO, (hx, hy, 18, 18), 0, 4)
            pygame.draw.rect(tela, (255, 100, 100), (hx + 2, hy + 2, 6, 6), 0, 2)
        else:
            pygame.draw.rect(tela, (60, 40, 40), (hx, hy, 18, 18), 1, 4)

    # Info
    info = fonte_peq.render(f"Vivos: {jogadores_vivos}  |  Rodada: {rodada}/{NUM_RODADAS}", True, (180, 180, 200))
    tela.blit(info, (LARGURA // 2 - info.get_width() // 2, 8))

    # Cor do sabre
    cor_s = CORES_SABRE[jogador.cor_sabre_idx]
    pygame.draw.line(tela, cor_s['cor_edge'], (70, 15), (70, 28), 4)
    pygame.draw.line(tela, cor_s['cor_core'], (70, 15), (70, 28), 2)

    # Kills
    kills_s = fonte_peq.render(f"Kills: {jogador.kills}", True, (180, 255, 180))
    tela.blit(kills_s, (90, 12))

    # Controles
    ctrl = fonte_peq.render("LMB: Arremessar / Puxar  RMB: Defesa  SPACE: Dash", True, (100, 100, 130))
    tela.blit(ctrl, (LARGURA // 2 - ctrl.get_width() // 2, ALTURA_JOGO - 18))


# ============================================================
#  LOOP PRINCIPAL DO MINIGAME
# ============================================================

def executar_minigame_sabers(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                              cliente, nome_jogador, customizacao):
    """Executa o minigame Sabers."""
    print("[SABERS] Minigame Sabers iniciado!")

    # Seed compartilhado
    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)
        print(f"[SABERS] Usando seed compartilhado: {seed}")

    # Limpar fila de acoes pendentes
    if cliente:
        cliente.get_minigame_actions()

    # Fontes
    fonte_grande = pygame.font.SysFont("Arial", 48, True)
    fonte_media = pygame.font.SysFont("Arial", 28, True)
    fonte_peq = pygame.font.SysFont("Arial", 14)
    fonte_nomes = pygame.font.SysFont("Arial", 12)
    fonte_hud = pygame.font.SysFont("Arial", 18, True)
    fonte_score = pygame.font.SysFont("Arial", 22, True)
    fonte_countdown = pygame.font.SysFont("Arial", 72, True)

    # Mira customizada
    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)

    # Criar jogadores (sempre 8)
    jogadores = []
    cor_local = customizacao.get('cor', AZUL)

    jogador_humano = JogadorSabers(nome_jogador, cor_local, is_bot=False)
    jogadores.append(jogador_humano)

    remotos = {}
    if cliente:
        remotos = cliente.get_remote_players()

    for pid, rp in remotos.items():
        ci = (pid - 1) % len(PALETA_CORES)
        jogadores.append(JogadorSabers(rp.name, PALETA_CORES[ci], is_bot=False, is_remote=True))

    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo", "Bot Foxtrot", "Bot Golf", "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        jogadores.append(JogadorSabers(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True))
        bot_idx += 1

    # Bots escolhem cor de sabre aleatoria
    for j in jogadores:
        if j.is_bot:
            j.cor_sabre_idx = random.randint(0, len(CORES_SABRE) - 1)

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

    particulas = []
    flashes = []

    rodada_atual = 1
    scoreboard_start = 0
    round_vencedor = None
    alpha_fade = 255

    while True:
        tempo = pygame.time.get_ticks()
        tempo_no_estado = tempo - tempo_estado

        # ========== EVENTOS ==========
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.mouse.set_visible(True)
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True)
                    return None

                # Selecao de cor
                if estado == "COLOR_SELECT":
                    for i in range(min(6, len(CORES_SABRE))):
                        if ev.key == pygame.K_1 + i:
                            jogador_humano.cor_sabre_idx = i
                            if cliente:
                                cliente.send_minigame_action({
                                    'action': 'saber_color',
                                    'cor_idx': i,
                                })

                # Dash
                if ev.key == pygame.K_SPACE and estado == "FIGHT":
                    if jogador_humano.vivo and not jogador_humano.dash_ativo:
                        teclas_dash = pygame.key.get_pressed()
                        ddx, ddy = 0.0, 0.0
                        if teclas_dash[pygame.K_w] or teclas_dash[pygame.K_UP]:
                            ddy -= 1
                        if teclas_dash[pygame.K_s] or teclas_dash[pygame.K_DOWN]:
                            ddy += 1
                        if teclas_dash[pygame.K_a] or teclas_dash[pygame.K_LEFT]:
                            ddx -= 1
                        if teclas_dash[pygame.K_d] or teclas_dash[pygame.K_RIGHT]:
                            ddx += 1
                        if jogador_humano.executar_dash(ddx, ddy) and cliente:
                            cliente.send_minigame_action({
                                'action': 'saber_dash',
                                'dx': ddx, 'dy': ddy,
                            })

            # Click esquerdo - arremessar sabre (ou forcar retorno) / Click direito - modo defesa
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1 and estado == "FIGHT" and jogador_humano.vivo:
                    if jogador_humano.sabre_info.get('arremessado', False):
                        # Sabre ja no ar - forcar retorno
                        jogador_humano.sabre_info['arremesso_retornando'] = True
                        if cliente:
                            cliente.send_minigame_action({'action': 'saber_recall'})
                    else:
                        # Arremessar
                        mx, my = convert_mouse_position(pygame.mouse.get_pos())
                        mundo_mx = mx + cam_x
                        mundo_my = my + cam_y
                        if _arremessar_sabre_jogador(jogador_humano, (mundo_mx, mundo_my)):
                            if cliente:
                                cliente.send_minigame_action({
                                    'action': 'saber_throw',
                                    'mx': mundo_mx, 'my': mundo_my,
                                })
                if ev.button == 3 and estado == "FIGHT":  # Botao direito
                    if jogador_humano.vivo and not jogador_humano.sabre_info.get('arremessado', False):
                        jogador_humano.sabre_info['modo_defesa'] = not jogador_humano.sabre_info['modo_defesa']
                        if cliente:
                            cliente.send_minigame_action({
                                'action': 'saber_defense',
                                'defesa': jogador_humano.sabre_info['modo_defesa'],
                            })

                # Click esquerdo na tela de selecao de cor
                if ev.button == 1 and estado == "COLOR_SELECT":
                    mx, my = convert_mouse_position(pygame.mouse.get_pos())
                    total_w = len(CORES_SABRE) * 100
                    start_x = LARGURA // 2 - total_w // 2
                    for i in range(len(CORES_SABRE)):
                        rx = start_x + i * 100
                        ry = 200
                        if rx <= mx <= rx + 80 and ry <= my <= ry + 120:
                            jogador_humano.cor_sabre_idx = i
                            if cliente:
                                cliente.send_minigame_action({
                                    'action': 'saber_color',
                                    'cor_idx': i,
                                })

        # ========== MAQUINA DE ESTADOS ==========

        if estado == "INTRO":
            if tempo_no_estado < 500:
                alpha_fade = int(255 * (1 - tempo_no_estado / 500))
            else:
                alpha_fade = 0

            if tempo_no_estado >= TEMPO_INTRO:
                estado = "COLOR_SELECT"
                tempo_estado = tempo

        elif estado == "COLOR_SELECT":
            if tempo_no_estado >= TEMPO_COLOR_SELECT:
                estado = "COUNTDOWN"
                tempo_estado = tempo
                # Ativar sabres de todos
                for j in jogadores:
                    j.sabre_info['ativo'] = True
                    j.sabre_info['animacao_ativacao'] = 100
                    j.sabre_info['comprimento_atual'] = 90

        elif estado == "COUNTDOWN":
            if tempo_no_estado >= TEMPO_COUNTDOWN:
                estado = "FIGHT"
                tempo_estado = tempo

        elif estado == "FIGHT":
            # Processar acoes remotas
            if cliente:
                for action in cliente.get_minigame_actions():
                    act = action.get('action')
                    for j in jogadores:
                        if j.is_remote and j.vivo:
                            if act == 'saber_input':
                                j.x = action.get('x', j.x)
                                j.y = action.get('y', j.y)
                                j.mira_x = action.get('mx', j.mira_x)
                                j.mira_y = action.get('my', j.mira_y)
                            elif act == 'saber_throw':
                                rmx = action.get('mx', 0)
                                rmy = action.get('my', 0)
                                _arremessar_sabre_jogador(j, (rmx, rmy))
                            elif act == 'saber_defense':
                                j.sabre_info['modo_defesa'] = action.get('defesa', False)
                            elif act == 'saber_dash':
                                j.executar_dash(action.get('dx', 0), action.get('dy', 0))
                            elif act == 'saber_color':
                                j.cor_sabre_idx = action.get('cor_idx', 0) % len(CORES_SABRE)
                            elif act == 'saber_recall':
                                j.sabre_info['arremesso_retornando'] = True

            # Movimento do jogador humano local
            teclas = pygame.key.get_pressed()
            if jogador_humano.vivo and not jogador_humano.dash_ativo:
                dx_mov, dy_mov = 0.0, 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                    dy_mov -= VEL_SABERS
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                    dy_mov += VEL_SABERS
                if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                    dx_mov -= VEL_SABERS
                if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                    dx_mov += VEL_SABERS
                # Normalizar diagonal
                if dx_mov != 0 and dy_mov != 0:
                    f = VEL_SABERS / math.sqrt(dx_mov * dx_mov + dy_mov * dy_mov)
                    dx_mov *= f
                    dy_mov *= f
                jogador_humano.vx = dx_mov
                jogador_humano.vy = dy_mov

            # Mira do jogador humano
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            jogador_humano.mira_x = float(mouse_pos[0]) + cam_x
            jogador_humano.mira_y = float(mouse_pos[1]) + cam_y

            # Bot AI
            for j in jogadores:
                if j.is_bot and j.vivo:
                    _bot_ai_sabers(j, jogadores, tempo)

            # Atualizar posicoes
            for j in jogadores:
                if j.vivo:
                    j.atualizar_dash()
                    if not j.dash_ativo and not j.is_remote:
                        j.x += j.vx
                        j.y += j.vy
                    j.x = max(4, min(j.x, ARENA_W - TAM_JOGADOR - 4))
                    j.y = max(4, min(j.y, ARENA_H - TAM_JOGADOR - 4))

            # Enviar posicao do jogador local
            if cliente and jogador_humano.vivo:
                cliente.send_minigame_action({
                    'action': 'saber_input',
                    'x': jogador_humano.x, 'y': jogador_humano.y,
                    'mx': jogador_humano.mira_x, 'my': jogador_humano.mira_y,
                })

            # Atualizar sabres arremessados
            for j in jogadores:
                if j.vivo:
                    _atualizar_sabre_arremessado_minigame(j)

            # Processar dano sabre (melee) - todos vs todos
            for atk in jogadores:
                if not atk.vivo:
                    continue
                for alvo in jogadores:
                    if atk is alvo or not alvo.vivo:
                        continue
                    if _processar_dano_sabre_minigame(atk, alvo, tempo):
                        # Efeito visual
                        cx, cy = alvo.get_centro()
                        for _ in range(12):
                            cor_s = CORES_SABRE[atk.cor_sabre_idx]
                            p = Particula(cx + random.uniform(-10, 10),
                                          cy + random.uniform(-10, 10),
                                          cor_s['cor_glow'])
                            p.velocidade_x = random.uniform(-4, 4)
                            p.velocidade_y = random.uniform(-4, 4)
                            p.vida = random.randint(8, 15)
                            p.tamanho = random.uniform(2, 4)
                            particulas.append(p)
                        flashes.append({
                            'x': cx, 'y': cy,
                            'raio': 20, 'vida': 10,
                            'cor': cor_s['cor_glow']
                        })
                        if not alvo.vivo:
                            # Morte - explosao grande
                            for _ in range(25):
                                p = Particula(cx + random.uniform(-15, 15),
                                              cy + random.uniform(-15, 15),
                                              alvo.cor)
                                p.velocidade_x = random.uniform(-6, 6)
                                p.velocidade_y = random.uniform(-6, 6)
                                p.vida = random.randint(15, 30)
                                p.tamanho = random.uniform(3, 6)
                                particulas.append(p)
                            # Som
                            try:
                                from src.utils.sound import gerar_som_explosao
                                som = pygame.mixer.Sound(gerar_som_explosao())
                                som.set_volume(0.3)
                                pygame.mixer.Channel(2).play(som)
                            except:
                                pass

            # Processar dano sabre arremessado
            for atk in jogadores:
                if not atk.vivo:
                    continue
                for alvo in jogadores:
                    if atk is alvo or not alvo.vivo:
                        continue
                    if _processar_dano_sabre_arremessado_minigame(atk, alvo, tempo):
                        cx, cy = alvo.get_centro()
                        cor_s = CORES_SABRE[atk.cor_sabre_idx]
                        for _ in range(10):
                            p = Particula(cx + random.uniform(-8, 8),
                                          cy + random.uniform(-8, 8),
                                          cor_s['cor_glow'])
                            p.velocidade_x = random.uniform(-3, 3)
                            p.velocidade_y = random.uniform(-3, 3)
                            p.vida = random.randint(8, 15)
                            p.tamanho = random.uniform(2, 4)
                            particulas.append(p)
                        flashes.append({
                            'x': cx, 'y': cy,
                            'raio': 18, 'vida': 8,
                            'cor': cor_s['cor_glow']
                        })
                        if not alvo.vivo:
                            for _ in range(25):
                                p = Particula(cx + random.uniform(-15, 15),
                                              cy + random.uniform(-15, 15),
                                              alvo.cor)
                                p.velocidade_x = random.uniform(-6, 6)
                                p.velocidade_y = random.uniform(-6, 6)
                                p.vida = random.randint(15, 30)
                                p.tamanho = random.uniform(3, 6)
                                particulas.append(p)

            # Colisao sabre arremessado vs sabre em defesa
            for atk in jogadores:
                for defensor in jogadores:
                    if atk is defensor:
                        continue
                    if _verificar_colisao_sabre_defesa(atk, defensor):
                        # Efeito de deflexao
                        sx = atk.sabre_info['arremesso_pos_x']
                        sy = atk.sabre_info['arremesso_pos_y']
                        for _ in range(15):
                            p = Particula(sx + random.uniform(-10, 10),
                                          sy + random.uniform(-10, 10),
                                          (200, 220, 255))
                            p.velocidade_x = random.uniform(-5, 5)
                            p.velocidade_y = random.uniform(-5, 5)
                            p.vida = random.randint(10, 20)
                            p.tamanho = random.uniform(2, 5)
                            particulas.append(p)
                        flashes.append({
                            'x': sx, 'y': sy,
                            'raio': 25, 'vida': 12,
                            'cor': (150, 200, 255)
                        })
                        # Som
                        try:
                            from src.utils.sound import gerar_som_tiro
                            som = pygame.mixer.Sound(gerar_som_tiro())
                            som.set_volume(0.2)
                            pygame.mixer.Channel(7).play(som)
                        except:
                            pass

            # Checar fim da rodada
            vivos = [j for j in jogadores if j.vivo]
            if len(vivos) <= 1:
                if len(vivos) == 1:
                    round_vencedor = vivos[0]
                    round_vencedor.rodadas_vencidas += 1
                else:
                    round_vencedor = None
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
                    # Resetar para nova rodada
                    for i, j in enumerate(jogadores):
                        j.reset_rodada(SPAWN_POINTS[i][0], SPAWN_POINTS[i][1])
                    particulas.clear()
                    flashes.clear()
                    estado = "COUNTDOWN"
                    tempo_estado = tempo

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                pygame.mouse.set_visible(True)
                return None

        # ========== ATUALIZAR CAMERA ==========
        if jogador_humano.vivo:
            cam_x, cam_y = _atualizar_camera(jogador_humano, cam_x, cam_y)
        else:
            # Seguir um jogador vivo como espectador
            vivos = [j for j in jogadores if j.vivo]
            if vivos:
                cam_x, cam_y = _atualizar_camera(vivos[0], cam_x, cam_y)

        # ========== ATUALIZAR PARTICULAS ==========
        for p in particulas[:]:
            p.atualizar()
            if p.vida <= 0:
                particulas.remove(p)

        for f in flashes[:]:
            f['vida'] -= 1
            if f['vida'] <= 0:
                flashes.remove(f)

        # ========== DESENHAR ==========
        _desenhar_arena(tela, cam_x, cam_y, tempo)

        # Jogadores
        for j in jogadores:
            if j.vivo:
                j.desenhar(tela, fonte_nomes, cam_x, cam_y, show_hp=(estado == "FIGHT"))

        # Sabres
        if estado in ("FIGHT", "ROUND_END"):
            for j in jogadores:
                if j.vivo:
                    _desenhar_sabre_jogador(tela, j, tempo, cam_x, cam_y)

        # Particulas (com offset de camera)
        for p in particulas:
            px = int(p.x - cam_x)
            py = int(p.y - cam_y)
            if 0 <= px <= LARGURA and 0 <= py <= ALTURA_JOGO:
                tam = max(1, int(p.tamanho))
                pygame.draw.circle(tela, p.cor, (px, py), tam)

        # Flashes (com offset de camera)
        for f in flashes:
            fx = int(f['x'] - cam_x)
            fy = int(f['y'] - cam_y)
            if -50 <= fx <= LARGURA + 50 and -50 <= fy <= ALTURA_JOGO + 50:
                raio = f['raio']
                alpha = min(255, int(f['vida'] * 25))
                flash_surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*f['cor'], alpha), (raio, raio), raio)
                tela.blit(flash_surf, (fx - raio, fy - raio))

        # HUD
        if estado == "FIGHT":
            jogadores_vivos = len([j for j in jogadores if j.vivo])
            _desenhar_hud_sabers(tela, jogador_humano, fonte_hud, fonte_peq,
                                 jogadores_vivos, rodada_atual, tempo)

        # Minimap
        if estado in ("FIGHT", "COUNTDOWN"):
            _desenhar_minimap(tela, jogadores, jogador_humano, cam_x, cam_y)

        # Mira customizada
        if estado in ("FIGHT", "COUNTDOWN"):
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            desenhar_mira(tela, mouse_pos, (mira_surface, mira_rect))

        # Color select overlay
        if estado == "COLOR_SELECT":
            tempo_restante = TEMPO_COLOR_SELECT - tempo_no_estado
            _desenhar_color_select(tela, jogador_humano, fonte_grande, fonte_media,
                                    fonte_peq, tempo, tempo_restante)

        # Countdown
        if estado == "COUNTDOWN":
            segundos = 3 - tempo_no_estado // 1000
            if segundos > 0:
                cd_text = str(segundos)
                cd_cor = AMARELO
            else:
                cd_text = "FIGHT!"
                cd_cor = VERMELHO
            cd_surf = fonte_countdown.render(cd_text, True, cd_cor)
            tela.blit(cd_surf, (LARGURA // 2 - cd_surf.get_width() // 2,
                                ALTURA_JOGO // 2 - cd_surf.get_height() // 2))

        # Round end
        if estado == "ROUND_END":
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            tela.blit(overlay, (0, 0))

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
            _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_score,
                                  fonte_peq, tempo, scoreboard_start)

        # Fade de intro
        if alpha_fade > 0:
            fade_surf = pygame.Surface((LARGURA, ALTURA_JOGO))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha_fade)
            tela.blit(fade_surf, (0, 0))

        # Titulo durante intro
        if estado == "INTRO" and tempo_no_estado > 500:
            alpha_titulo = min(255, int((tempo_no_estado - 500) * 0.5))
            titulo = fonte_grande.render("SABERS", True, (200, 220, 255))
            titulo.set_alpha(alpha_titulo)
            tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2,
                               ALTURA_JOGO // 2 - titulo.get_height() // 2 - 20))
            sub = fonte_media.render("Free-for-all com Sabres de Luz", True, (150, 170, 200))
            sub.set_alpha(alpha_titulo)
            tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2,
                            ALTURA_JOGO // 2 + 20))

        present_frame()
        relogio.tick(60)
