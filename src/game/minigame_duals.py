#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Duals - Duelos 1v1 em eliminatoria.
8 jogadores (humanos + bots), duelos eliminatorios ate restar 1 vencedor.
Armas caem na arena com o tempo. 5 de vida cada jogador por duelo.
"""

import pygame
import math
import random
from src.config import *
from src.entities.tiro import Tiro
from src.entities.particula import Particula, criar_explosao
from src.utils.visual import criar_estrelas, desenhar_estrelas, criar_mira, desenhar_mira
from src.utils.display_manager import present_frame, convert_mouse_position
from src.weapons.desert_eagle import desenhar_desert_eagle
from src.weapons.metralhadora import desenhar_metralhadora
from src.weapons.sniper import desenhar_sniper
from src.weapons.espingarda import desenhar_espingarda
from src.entities.misterioso_cutscene import InimigoMisterioso

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
HP_MAX = 5

# Paleta de cores
PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Arena (bem maior, ocupa quase toda a tela)
ARENA_X = 40
ARENA_Y = 60
ARENA_W = LARGURA - 80
ARENA_H = ALTURA_JOGO - 160
ARENA_RECT = pygame.Rect(ARENA_X, ARENA_Y, ARENA_W, ARENA_H)

# Posicoes de spawn dos duelistas (esquerda e direita da arena)
SPAWN_ESQ = (ARENA_X + 100, ARENA_Y + ARENA_H // 2 - TAM_JOGADOR // 2)
SPAWN_DIR = (ARENA_X + ARENA_W - 100 - TAM_JOGADOR, ARENA_Y + ARENA_H // 2 - TAM_JOGADOR // 2)

# Fila de espera (abaixo da arena)
FILA_Y = ARENA_Y + ARENA_H + 20
FILA_X_INICIO = LARGURA // 2 - 4 * 55
FILA_ESPACO = 55

# Tempos de estado (ms)
TEMPO_INTRO = 2000
TEMPO_COUNTDOWN = 2000
TEMPO_ROUND_END = 2500
TEMPO_SCOREBOARD = 5000

# Armas que caem
ARMA_TIPOS = [
    {'nome': 'Desert Eagle', 'cor': (200, 170, 0), 'dano': 3, 'velocidade': 15, 'cooldown': 500, 'tiros': 7, 'raio': 4},
    {'nome': 'Sniper', 'cor': (100, 200, 255), 'dano': 5, 'velocidade': 30, 'cooldown': 1200, 'tiros': 3, 'raio': 3},
    {'nome': 'Espingarda', 'cor': (255, 130, 50), 'dano': 2, 'velocidade': 12, 'cooldown': 700, 'tiros': 4, 'raio': 5, 'spread': 5},
    {'nome': 'Metralhadora', 'cor': (180, 180, 180), 'dano': 1, 'velocidade': 13, 'cooldown': 120, 'tiros': 20, 'raio': 3},
]
ARMA_DROP_INTERVALO = 4000  # ms entre drops
ARMA_TAM = 22

# Bot AI (inspirado em fase_base)
BOT_STRAFE_INTERVALO = 800   # ms entre mudancas de strafe
BOT_SHOOT_DELAY_MIN = 250
BOT_SHOOT_DELAY_MAX = 700
BOT_DIST_IDEAL = 180         # distancia ideal pro oponente
BOT_DIST_RECUAR = 80         # muito perto, recua
BOT_DIST_AVANCAR = 280       # muito longe, avanca

# Velocidade de movimento no duelo
VEL_DUELO = 3.5

# Dash
DASH_VELOCIDADE = 25
DASH_DURACAO = 8       # frames
DASH_COOLDOWN = 500    # ms
DASH_INVULN_POS = 200  # ms de invulnerabilidade apos o dash

# Escala de arma renderizada na mao (proporcional ao tamanho do jogador)
ESCALA_ARMA = TAM_JOGADOR / 40  # ~0.75 para TAM_JOGADOR=30
TAMANHO_SURF_ARMA = 150

# Misterioso
TAM_MISTERIOSO = int(TAMANHO_QUADRADO * 1.2)
MISTERIOSO_X = LARGURA - TAM_MISTERIOSO - 40
MISTERIOSO_Y = FILA_Y - 10
MISTERIOSO_CHANCE = 0.05  # 5% de chance de duelo bonus
MISTERIOSO_HP = 40
MISTERIOSO_RAIO_VEL = 35  # velocidade do raio
MISTERIOSO_RAIO_DANO = 999  # hit kill


# ============================================================
#  CLASSES
# ============================================================

class ArmaVoando:
    """Arma sendo jogada pelo misterioso via telecinese."""

    def __init__(self, config, origem_x, origem_y, destino_x, destino_y):
        self.config = config
        self.cor = config['cor']
        self.ox = float(origem_x)
        self.oy = float(origem_y)
        self.dx = float(destino_x)
        self.dy = float(destino_y)
        self.progresso = 0.0  # 0.0 -> 1.0
        self.velocidade = 0.025  # progresso por frame
        self.concluida = False

    def atualizar(self):
        self.progresso += self.velocidade
        if self.progresso >= 1.0:
            self.progresso = 1.0
            self.concluida = True

    def get_pos(self):
        t = self.progresso
        # Curva parabolica (arco)
        x = self.ox + (self.dx - self.ox) * t
        y = self.oy + (self.dy - self.oy) * t - math.sin(t * math.pi) * 120
        return x, y

    def desenhar(self, tela, tempo):
        x, y = self.get_pos()
        ix, iy = int(x), int(y)

        # Glow vermelho (telecinese)
        glow_r = 18
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (180, 0, 50, 60), (glow_r, glow_r), glow_r)
        tela.blit(glow_surf, (ix - glow_r, iy - glow_r))

        # Caixa da arma
        tam = 16
        pygame.draw.rect(tela, self.cor, (ix - tam // 2, iy - tam // 2, tam, tam), 0, 4)

        # Trilha de particulas vermelhas
        for i in range(3):
            t_back = max(0, self.progresso - (i + 1) * 0.03)
            tx = self.ox + (self.dx - self.ox) * t_back
            ty = self.oy + (self.dy - self.oy) * t_back - math.sin(t_back * math.pi) * 120
            alpha = int(120 * (1 - i / 3))
            trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (180, 0, 50, alpha), (4, 4), 4)
            tela.blit(trail_surf, (int(tx) - 4, int(ty) - 4))


class ArmaChao:
    """Arma que cai no chao da arena."""

    def __init__(self, config):
        self.nome = config['nome']
        self.cor = config['cor']
        self.dano = config['dano']
        self.velocidade = config['velocidade']
        self.cooldown = config['cooldown']
        self.tiros = config['tiros']
        self.raio = config['raio']
        self.spread = config.get('spread', 0)

        # Posicao aleatoria dentro da arena
        self.x = float(random.randint(ARENA_X + 80, ARENA_X + ARENA_W - 80))
        self.y = float(random.randint(ARENA_Y + 80, ARENA_Y + ARENA_H - 80))
        self.rect = pygame.Rect(int(self.x) - ARMA_TAM // 2, int(self.y) - ARMA_TAM // 2,
                                ARMA_TAM, ARMA_TAM)
        self.ativa = True
        self.tempo_spawn = pygame.time.get_ticks()

        # Visual
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

    def desenhar(self, tela, tempo):
        if not self.ativa:
            return
        ix, iy = int(self.x), int(self.y)
        tam = ARMA_TAM

        # Flutuacao
        flut = int(3 * math.sin(tempo / 300 + self.x))
        dy = iy + flut

        # Glow
        glow_r = tam + 6 + int(3 * math.sin(tempo / 200))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.cor, 30), (glow_r, glow_r), glow_r)
        tela.blit(glow_surf, (ix - glow_r, dy - glow_r))

        # Sombra
        pygame.draw.rect(tela, (15, 12, 20),
                         (ix - tam // 2 + 2, dy - tam // 2 + 2, tam, tam), 0, 4)
        # Caixa
        pygame.draw.rect(tela, self.cor_escura,
                         (ix - tam // 2, dy - tam // 2, tam, tam), 0, 5)
        pygame.draw.rect(tela, self.cor,
                         (ix - tam // 2 + 2, dy - tam // 2 + 2, tam - 4, tam - 4), 0, 3)
        pygame.draw.rect(tela, self.cor_brilhante,
                         (ix - tam // 2 + 4, dy - tam // 2 + 4, 6, 6), 0, 2)

        # Nome abreviado
        fonte = pygame.font.SysFont("Arial", 12, True)
        txt = fonte.render(self.nome[:3], True, BRANCO)
        tela.blit(txt, (ix - txt.get_width() // 2, dy - txt.get_height() // 2))

        # Atualizar rect para colisao (sem flutuacao)
        self.rect.x = ix - ARMA_TAM // 2
        self.rect.y = iy - ARMA_TAM // 2


class JogadorDuals:
    """Jogador no minigame Duals."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_remote = is_remote  # Jogador humano remoto (controlado via rede)
        self.hp = HP_MAX
        self.vivo = True
        self.eliminado = False  # eliminado do torneio
        self.vitorias = 0

        # Posicao
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.in_arena = False

        # Movimento (durante duelo)
        self.vx = 0.0
        self.vy = 0.0

        # Arma atual (None = tiro basico)
        self.arma = None
        self.tiros_arma = 0
        self.cooldown_arma = 400
        self.dano_arma = 1
        self.velocidade_arma = 10
        self.raio_arma = 4
        self.spread_arma = 0
        self.tempo_ultimo_tiro = 0

        # Mira (posicao do mouse ou alvo do bot)
        self.mira_x = 0.0
        self.mira_y = 0.0

        # Invulnerabilidade apos tomar dano
        self.invulneravel_ate = 0

        # Cores derivadas
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

        # Dash
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0

        # Bot AI (inspirado em fase_base - strafe, dodge, combate)
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_strafe_dir = 1  # 1 ou -1
        self.bot_move_timer = 0
        self.bot_dir_x = 0.0
        self.bot_dir_y = 0.0

    def reset_duelo(self):
        self.hp = HP_MAX
        self.vivo = True
        self.arma = None
        self.tiros_arma = 0
        self.cooldown_arma = 400
        self.dano_arma = 1
        self.velocidade_arma = 10
        self.raio_arma = 4
        self.spread_arma = 0
        self.tempo_ultimo_tiro = 0
        self.invulneravel_ate = 0
        self.vx = 0.0
        self.vy = 0.0
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_move_timer = 0

    def pegar_arma(self, arma_chao):
        self.arma = arma_chao.nome
        self.tiros_arma = arma_chao.tiros
        self.cooldown_arma = arma_chao.cooldown
        self.dano_arma = arma_chao.dano
        self.velocidade_arma = arma_chao.velocidade
        self.raio_arma = arma_chao.raio
        self.spread_arma = arma_chao.spread

    def executar_dash(self, dx, dy):
        """Executa dash na direcao (dx, dy). Retorna True se executou."""
        tempo = pygame.time.get_ticks()
        if self.dash_ativo:
            return False
        if tempo - self.dash_tempo_cooldown < DASH_COOLDOWN:
            return False
        # Normalizar direcao
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
        self.invulneravel_ate = tempo + 99999  # invulneravel durante o dash
        return True

    def atualizar_dash(self):
        """Atualiza estado do dash. Chamar a cada frame."""
        tempo = pygame.time.get_ticks()
        if self.dash_ativo:
            ddx, ddy = self.dash_direcao
            self.x += ddx * DASH_VELOCIDADE
            self.y += ddy * DASH_VELOCIDADE
            # Manter dentro da arena
            self.x = max(ARENA_X + 4, min(self.x, ARENA_X + ARENA_W - TAM_JOGADOR - 4))
            self.y = max(ARENA_Y + 4, min(self.y, ARENA_Y + ARENA_H - TAM_JOGADOR - 4))
            self.dash_frames_restantes -= 1
            if self.dash_frames_restantes <= 0:
                self.dash_ativo = False
                self.dash_tempo_fim = tempo
                # Invulnerabilidade pos-dash (200ms)
                self.invulneravel_ate = tempo + DASH_INVULN_POS
        # Pos-dash: verificar se invulnerabilidade expirou
        if not self.dash_ativo and self.dash_tempo_fim > 0:
            if tempo - self.dash_tempo_fim >= DASH_INVULN_POS:
                self.dash_tempo_fim = 0

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)

    def desenhar(self, tela, fonte, destaque=False, pulsacao=0, show_hp=False):
        tam = TAM_JOGADOR
        ix, iy = int(self.x), int(self.y)

        # Piscar se invulneravel
        tempo = pygame.time.get_ticks()
        if tempo < self.invulneravel_ate and (tempo // 80) % 2 == 0:
            return

        mod = 0
        if destaque:
            if pulsacao < 6:
                mod = int(pulsacao * 0.5)
            else:
                mod = int((12 - pulsacao) * 0.5)

        # Sombra
        pygame.draw.rect(tela, (15, 12, 20), (ix + 3, iy + 3, tam, tam), 0, 3)
        # Cor escura
        pygame.draw.rect(tela, self.cor_escura, (ix, iy, tam + mod, tam + mod), 0, 5)
        # Cor principal
        pygame.draw.rect(tela, self.cor, (ix + 2, iy + 2, tam + mod - 4, tam + mod - 4), 0, 3)
        # Highlight
        pygame.draw.rect(tela, self.cor_brilhante, (ix + 4, iy + 4, 7, 7), 0, 2)

        # Nome
        nome_surf = fonte.render(self.nome, True, BRANCO)
        nx = ix + tam // 2 - nome_surf.get_width() // 2
        ny = iy - 16

        bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        tela.blit(bg, (nx - 3, ny - 1))
        tela.blit(nome_surf, (nx, ny))

        # Barra de HP (so na arena)
        if show_hp:
            hp_w = tam + mod
            hp_h = 4
            hp_x = ix
            hp_y = iy + tam + mod + 4
            pygame.draw.rect(tela, (40, 40, 40), (hp_x, hp_y, hp_w, hp_h), 0, 2)
            hp_ratio = max(0, self.hp / HP_MAX)
            cor_hp = VERDE if hp_ratio > 0.5 else AMARELO if hp_ratio > 0.25 else VERMELHO
            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h), 0, 2)


# ============================================================
#  FUNCOES AUXILIARES
# ============================================================

def _disparar(jogador, mouse_x, mouse_y, tiros, particulas, flashes):
    """Dispara um tiro do jogador."""
    tempo = pygame.time.get_ticks()
    if tempo - jogador.tempo_ultimo_tiro < jogador.cooldown_arma:
        return

    # Gastar municao de arma especial
    if jogador.arma:
        jogador.tiros_arma -= 1
        if jogador.tiros_arma <= 0:
            jogador.arma = None
            jogador.cooldown_arma = 400
            jogador.dano_arma = 1
            jogador.velocidade_arma = 10
            jogador.raio_arma = 4
            jogador.spread_arma = 0

    jogador.tempo_ultimo_tiro = tempo

    cx = jogador.x + TAM_JOGADOR // 2
    cy = jogador.y + TAM_JOGADOR // 2

    dx = mouse_x - cx
    dy = mouse_y - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist

    ponta_x = cx + dx * 25
    ponta_y = cy + dy * 25

    n_tiros = jogador.spread_arma if jogador.spread_arma > 0 else 1
    for i in range(n_tiros):
        if n_tiros > 1:
            spread_ang = math.radians(random.uniform(-12, 12))
            ndx = dx * math.cos(spread_ang) - dy * math.sin(spread_ang)
            ndy = dx * math.sin(spread_ang) + dy * math.cos(spread_ang)
        else:
            ndx, ndy = dx, dy

        tiro = Tiro(ponta_x, ponta_y, ndx, ndy, jogador.cor, velocidade=jogador.velocidade_arma)
        tiro.dano = jogador.dano_arma
        tiro.raio = jogador.raio_arma
        tiro.dono = jogador
        tiros.append(tiro)

    # Efeito
    for _ in range(5):
        p = Particula(ponta_x + random.uniform(-3, 3), ponta_y + random.uniform(-3, 3),
                      (255, random.randint(150, 255), 0))
        p.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-1, 1)
        p.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-1, 1)
        p.vida = random.randint(8, 18)
        p.tamanho = random.uniform(2, 4)
        particulas.append(p)

    flashes.append({
        'x': ponta_x, 'y': ponta_y,
        'raio': 15, 'vida': 6,
        'cor': (255, 200, 0)
    })

    # Som
    try:
        from src.utils.sound import gerar_som_tiro
        som = pygame.mixer.Sound(gerar_som_tiro())
        som.set_volume(0.25)
        pygame.mixer.Channel(1).play(som)
    except:
        pass


def _disparar_raio(bot, oponente, tiros, particulas, flashes):
    """Misterioso dispara um raio super rapido que mata em hit kill."""
    cx = bot.x + TAM_JOGADOR // 2
    cy = bot.y + TAM_JOGADOR // 2
    ox = oponente.x + TAM_JOGADOR // 2
    oy = oponente.y + TAM_JOGADOR // 2

    dx = ox - cx
    dy = oy - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist

    ponta_x = cx + dx * 25
    ponta_y = cy + dy * 25

    tiro = Tiro(ponta_x, ponta_y, dx, dy, (255, 0, 60), velocidade=MISTERIOSO_RAIO_VEL)
    tiro.dano = MISTERIOSO_RAIO_DANO
    tiro.raio = 8
    tiro.dono = bot
    tiros.append(tiro)

    # Linha de raio instantanea ao longo da trajetoria (efeito visual)
    comprimento_raio = min(dist, 500)
    for step in range(0, int(comprimento_raio), 12):
        rx = ponta_x + dx * step
        ry = ponta_y + dy * step
        # Particulas ao longo do raio
        p = Particula(rx + random.uniform(-4, 4), ry + random.uniform(-4, 4),
                      random.choice([(255, 0, 40), (200, 0, 80), (255, 50, 50), (180, 0, 0)]))
        p.velocidade_x = random.uniform(-1.5, 1.5)
        p.velocidade_y = random.uniform(-1.5, 1.5)
        p.vida = random.randint(8, 18)
        p.tamanho = random.uniform(2, 5)
        particulas.append(p)

    # Explosao na ponta de saida
    for _ in range(15):
        p = Particula(ponta_x + random.uniform(-6, 6), ponta_y + random.uniform(-6, 6),
                      random.choice([(255, 30, 30), (255, 80, 0), (200, 0, 60)]))
        p.velocidade_x = dx * random.uniform(4, 10) + random.uniform(-3, 3)
        p.velocidade_y = dy * random.uniform(4, 10) + random.uniform(-3, 3)
        p.vida = random.randint(15, 30)
        p.tamanho = random.uniform(3, 7)
        particulas.append(p)

    # Flash grande na origem
    flashes.append({
        'x': ponta_x, 'y': ponta_y,
        'raio': 30, 'vida': 12,
        'cor': (255, 0, 50)
    })
    # Flash no alvo
    flashes.append({
        'x': ox, 'y': oy,
        'raio': 20, 'vida': 8,
        'cor': (255, 50, 0)
    })

    try:
        from src.utils.sound import gerar_som_tiro
        som = pygame.mixer.Sound(gerar_som_tiro())
        som.set_volume(0.4)
        pygame.mixer.Channel(1).play(som)
    except:
        pass


def _bot_ai(bot, oponente, armas_chao, tiros, particulas, flashes, tempo):
    """
    IA do bot durante o duelo - inspirada em fase_base.
    Strafe perpendicular ao oponente, ajuste de distancia, evasao de paredes,
    prioridade em pegar armas, desvio de tiros inimigos.
    """
    if not oponente.vivo:
        bot.vx = 0
        bot.vy = 0
        return

    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2

    # --- Direcao ate o oponente ---
    dx = oponente.x - bot.x
    dy = oponente.y - bot.y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1:
        dist = 1
    dir_x = dx / dist
    dir_y = dy / dist

    # --- Strafe perpendicular (muda a cada BOT_STRAFE_INTERVALO) ---
    if tempo > bot.bot_strafe_timer:
        bot.bot_strafe_timer = tempo + BOT_STRAFE_INTERVALO + random.randint(-200, 200)
        bot.bot_strafe_dir = -bot.bot_strafe_dir

    strafe_x = -dir_y * bot.bot_strafe_dir
    strafe_y = dir_x * bot.bot_strafe_dir

    # --- Detectar tiros inimigos vindo na direcao do bot ---
    dodge_x, dodge_y = 0.0, 0.0
    for tiro in tiros:
        if not hasattr(tiro, 'dono') or tiro.dono is bot:
            continue
        # Vetor do tiro ate o bot
        tx = bot_cx - tiro.x
        ty = bot_cy - tiro.y
        tdist = math.sqrt(tx * tx + ty * ty)
        if tdist > 200:
            continue  # muito longe, ignorar

        # Produto escalar: o tiro esta vindo na direcao do bot?
        dot = tiro.dx * tx + tiro.dy * ty
        if dot <= 0:
            continue  # tiro se afastando

        # Distancia perpendicular do bot a trajetoria do tiro
        # projecao do vetor bot-tiro na direcao do tiro
        proj_x = tiro.dx * dot
        proj_y = tiro.dy * dot
        perp_x = tx - proj_x
        perp_y = ty - proj_y
        perp_dist = math.sqrt(perp_x * perp_x + perp_y * perp_y)

        if perp_dist < TAM_JOGADOR + 20:
            # Tiro vai passar perto - desviar perpendicularmente
            if perp_dist > 1:
                # Desviar no sentido oposto (afastar da trajetoria)
                dodge_x -= perp_x / perp_dist * 1.5
                dodge_y -= perp_y / perp_dist * 1.5
            else:
                # Exatamente na linha - desviar lateralmente
                dodge_x += -tiro.dy * 1.5
                dodge_y += tiro.dx * 1.5

    # --- Movimento composto: strafe + ajuste de distancia ---
    mover_x = strafe_x + dodge_x
    mover_y = strafe_y + dodge_y

    # --- Misterioso nao pega armas, so combate ---
    if bot.nome == "???":
        # Combate puro: ajuste de distancia
        if dist < BOT_DIST_RECUAR:
            mover_x -= dir_x * 0.7
            mover_y -= dir_y * 0.7
        elif dist > BOT_DIST_AVANCAR:
            mover_x += dir_x * 0.5
            mover_y += dir_y * 0.5
        elif dist > BOT_DIST_IDEAL:
            mover_x += dir_x * 0.2
            mover_y += dir_y * 0.2
    else:
        # --- Buscar arma no chao (PRIORIDADE quando sem arma) ---
        melhor_arma = None
        melhor_dist_arma = float('inf')
        for a in armas_chao:
            if a.ativa:
                ad = math.sqrt((a.x - bot_cx) ** 2 + (a.y - bot_cy) ** 2)
                if ad < melhor_dist_arma:
                    melhor_dist_arma = ad
                    melhor_arma = a

        if not bot.arma and melhor_arma:
            # Sem arma: prioridade total em ir pegar
            ax = melhor_arma.x - bot_cx
            ay = melhor_arma.y - bot_cy
            ad = math.sqrt(ax * ax + ay * ay)
            if ad > 0:
                peso = 1.5 if ad < 150 else 1.0
                mover_x = (ax / ad) * peso + dodge_x
                mover_y = (ay / ad) * peso + dodge_y
        elif not bot.arma:
            # Sem arma e nenhuma no chao: manter distancia, esperar drop
            if dist < BOT_DIST_RECUAR:
                mover_x -= dir_x * 0.7
                mover_y -= dir_y * 0.7
            elif dist > BOT_DIST_AVANCAR:
                mover_x += dir_x * 0.3
                mover_y += dir_y * 0.3
        else:
            # Tem arma: combate normal com ajuste de distancia
            if dist < BOT_DIST_RECUAR:
                mover_x -= dir_x * 0.7
                mover_y -= dir_y * 0.7
            elif dist > BOT_DIST_AVANCAR:
                mover_x += dir_x * 0.5
                mover_y += dir_y * 0.5
            elif dist > BOT_DIST_IDEAL:
                mover_x += dir_x * 0.2
                mover_y += dir_y * 0.2

            # Com arma, mas se tiver uma melhor perto, buscar
            if melhor_arma and melhor_dist_arma < 120:
                ax = melhor_arma.x - bot_cx
                ay = melhor_arma.y - bot_cy
                ad = math.sqrt(ax * ax + ay * ay)
                if ad > 0:
                    mover_x += (ax / ad) * 0.4
                    mover_y += (ay / ad) * 0.4

    # --- Evitar paredes da arena ---
    centro_x = bot.x + TAM_JOGADOR // 2
    centro_y = bot.y + TAM_JOGADOR // 2
    margem = 50

    if centro_x < ARENA_X + margem:
        mover_x += 0.8
    elif centro_x > ARENA_X + ARENA_W - margem:
        mover_x -= 0.8
    if centro_y < ARENA_Y + margem:
        mover_y += 0.8
    elif centro_y > ARENA_Y + ARENA_H - margem:
        mover_y -= 0.8

    # --- Normalizar e aplicar velocidade ---
    mag = math.sqrt(mover_x * mover_x + mover_y * mover_y)
    if mag > 0:
        mover_x /= mag
        mover_y /= mag

    bot.vx = mover_x * VEL_DUELO
    bot.vy = mover_y * VEL_DUELO

    # --- Mira: mirar no oponente com imprecisao baseada em distancia ---
    imprecisao = min(dist / 600, 0.3)
    angulo_mira = math.atan2(dy, dx) + random.uniform(-imprecisao, imprecisao)
    bot.mira_x = bot.x + TAM_JOGADOR // 2 + math.cos(angulo_mira) * dist
    bot.mira_y = bot.y + TAM_JOGADOR // 2 + math.sin(angulo_mira) * dist

    # --- Dash do bot ---
    # Dash quando muito perto ou aleatoriamente durante combate
    if not bot.dash_ativo:
        usar_dash = False
        dash_dx, dash_dy = 0.0, 0.0

        if dist < 60:
            # Muito perto - dash para longe
            usar_dash = True
            dash_dx = -dir_x
            dash_dy = -dir_y
        elif random.random() < 0.008:
            # Dash aleatorio lateral (evasao)
            usar_dash = True
            dash_dx = -dir_y * bot.bot_strafe_dir
            dash_dy = dir_x * bot.bot_strafe_dir

        if usar_dash:
            bot.executar_dash(dash_dx, dash_dy)

    # --- Atirar ---
    if tempo >= bot.bot_next_shot:
        if bot.nome == "???":
            # Misterioso dispara raio instantaneo (hit kill)
            _disparar_raio(bot, oponente, tiros, particulas, flashes)
            bot.bot_next_shot = tempo + random.randint(1800, 2800)
        else:
            _disparar(bot, bot.mira_x, bot.mira_y, tiros, particulas, flashes)
            # Cadencia depende da arma
            if bot.arma == 'Metralhadora':
                bot.bot_next_shot = tempo + random.randint(100, 200)
            elif bot.arma == 'Sniper':
                bot.bot_next_shot = tempo + random.randint(800, 1200)
            else:
                bot.bot_next_shot = tempo + random.randint(BOT_SHOOT_DELAY_MIN, BOT_SHOOT_DELAY_MAX)


def _desenhar_arma_jogador(tela, jogador, tempo_atual):
    """
    Desenha a arma equipada na mao do jogador, seguindo a mira.
    Usa o mesmo sistema de fase_multiplayer_nova: surface temporaria + escala.
    """
    centro_x = jogador.x + TAM_JOGADOR // 2
    centro_y = jogador.y + TAM_JOGADOR // 2

    # Direcao da mira
    dx = jogador.mira_x - centro_x
    dy = jogador.mira_y - centro_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist
    else:
        dx, dy = 1.0, 0.0

    # Surface temporaria grande para desenhar a arma
    temp_surf = pygame.Surface((TAMANHO_SURF_ARMA, TAMANHO_SURF_ARMA), pygame.SRCALPHA)

    # Jogador temporario para as funcoes de desenho
    class _Temp:
        pass

    jt = _Temp()
    jt.x = TAMANHO_SURF_ARMA // 2 - TAM_JOGADOR // 2
    jt.y = TAMANHO_SURF_ARMA // 2 - TAM_JOGADOR // 2
    jt.tamanho = TAM_JOGADOR
    jt.cor = jogador.cor
    jt.tempo_ultimo_tiro = jogador.tempo_ultimo_tiro
    jt.tempo_cooldown = jogador.cooldown_arma

    # Posicao do mouse na surface temporaria (direcao certa)
    pos_mouse_temp = (
        TAMANHO_SURF_ARMA // 2 + dx * 60,
        TAMANHO_SURF_ARMA // 2 + dy * 60
    )

    arma = jogador.arma
    if arma == 'Desert Eagle':
        jt.desert_eagle_ativa = True
        jt.tiros_desert_eagle = jogador.tiros_arma
        desenhar_desert_eagle(temp_surf, jt, pos_mouse_temp)
    elif arma == 'Metralhadora':
        jt.metralhadora_ativa = False  # sem laser
        jt.tiros_metralhadora = jogador.tiros_arma
        desenhar_metralhadora(temp_surf, jt, tempo_atual, pos_mouse_temp)
    elif arma == 'Sniper':
        jt.sniper_ativa = False  # sem laser
        jt.sniper_mirando = False
        jt.recuo_sniper = 0
        desenhar_sniper(temp_surf, jt, tempo_atual, pos_mouse_temp)
    elif arma == 'Espingarda':
        jt.espingarda_ativa = True
        jt.recuo_espingarda = 0
        jt.tempo_recuo = 0
        desenhar_espingarda(temp_surf, jt, tempo_atual, pos_mouse_temp)
    else:
        # Tiro basico - nao desenha arma
        return

    # Escalar e desenhar
    novo_tam = int(TAMANHO_SURF_ARMA * ESCALA_ARMA)
    arma_reduzida = pygame.transform.scale(temp_surf, (novo_tam, novo_tam))
    tela.blit(arma_reduzida, (int(centro_x) - novo_tam // 2, int(centro_y) - novo_tam // 2))


def _desenhar_arena(tela, tempo):
    """Desenha a arena do duelo."""
    arena_surf = pygame.Surface((ARENA_W, ARENA_H), pygame.SRCALPHA)
    arena_surf.fill((20, 18, 32, 200))

    # Grid sutil
    for gx in range(0, ARENA_W, 40):
        pygame.draw.line(arena_surf, (30, 28, 45), (gx, 0), (gx, ARENA_H), 1)
    for gy in range(0, ARENA_H, 40):
        pygame.draw.line(arena_surf, (30, 28, 45), (0, gy), (ARENA_W, gy), 1)

    tela.blit(arena_surf, (ARENA_X, ARENA_Y))

    # Borda com glow
    borda_cor = (60, 50, 90)
    pygame.draw.rect(tela, borda_cor, (ARENA_X, ARENA_Y, ARENA_W, ARENA_H), 2, 5)

    # Linha central tracejada
    cx = ARENA_X + ARENA_W // 2
    for y in range(ARENA_Y + 10, ARENA_Y + ARENA_H - 10, 12):
        alpha = 30 + int(15 * math.sin(tempo / 500 + y * 0.05))
        pygame.draw.line(tela, (alpha, alpha, alpha + 20), (cx, y), (cx, y + 6), 1)


def _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_media, fonte_score,
                          fonte_peq, tempo, start_time):
    """Desenha o scoreboard final."""
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))

    titulo = fonte_grande.render("RESULTADO", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 40))

    ranking = sorted(enumerate(jogadores), key=lambda x: -x[1].vitorias)

    tempo_decorrido = tempo - start_time
    y_base = 120
    for rank, (idx, j) in enumerate(ranking):
        delay = rank * 300
        if tempo_decorrido < delay:
            continue

        y = y_base + rank * 50

        linha_w = 460
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

        sq_x = linha_x + 80
        sq_y = y + 6
        sq_tam = 28
        cor_esc = tuple(max(0, c - 60) for c in j.cor)
        pygame.draw.rect(tela, cor_esc, (sq_x, sq_y, sq_tam, sq_tam), 0, 4)
        pygame.draw.rect(tela, j.cor, (sq_x + 2, sq_y + 2, sq_tam - 4, sq_tam - 4), 0, 3)

        nome_cor = (180, 0, 50) if j.nome == "???" else BRANCO
        nome_s = fonte_score.render(j.nome, True, nome_cor)
        tela.blit(nome_s, (sq_x + sq_tam + 12, y + 8))

        vic_s = fonte_peq.render(f"{j.vitorias} vitorias", True, (180, 255, 180))
        tela.blit(vic_s, (linha_x + 320, y + 12))

        if rank < 3:
            pygame.draw.rect(tela, pos_cor, (linha_x, y, linha_w, 42), 1, 3)

    if tempo_decorrido > 3000:
        inst = fonte_peq.render("Voltando ao menu...", True, (120, 120, 140))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))


def _gerar_bracket(jogadores):
    """Gera ordem embaralhada para os duelos eliminatorios."""
    indices = list(range(len(jogadores)))
    random.shuffle(indices)
    return indices


# ============================================================
#  LOOP PRINCIPAL DO MINIGAME
# ============================================================

def executar_minigame_duals(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                             cliente, nome_jogador, customizacao):
    """Executa o minigame Duals."""
    print("[DUALS] Minigame Duals iniciado!")

    # --- Seed compartilhado para sincronizar random entre host e clientes ---
    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)
        print(f"[DUALS] Usando seed compartilhado: {seed}")

    # Limpar fila de ações pendentes de sessões anteriores
    if cliente:
        cliente.get_minigame_actions()

    # --- Fontes ---
    fonte_grande = pygame.font.SysFont("Arial", 48, True)
    fonte_media = pygame.font.SysFont("Arial", 28, True)
    fonte_peq = pygame.font.SysFont("Arial", 14)
    fonte_nomes = pygame.font.SysFont("Arial", 12)
    fonte_hud = pygame.font.SysFont("Arial", 18, True)
    fonte_score = pygame.font.SysFont("Arial", 22, True)
    fonte_countdown = pygame.font.SysFont("Arial", 72, True)

    # --- Fundo ---
    estrelas = criar_estrelas(120)

    # --- Mira customizada ---
    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)

    # --- Criar jogadores (sempre 8) ---
    jogadores = []
    cor_local = customizacao.get('cor', AZUL)

    jogador_humano = JogadorDuals(nome_jogador, cor_local, is_bot=False)
    jogadores.append(jogador_humano)

    remotos = {}
    if cliente:
        remotos = cliente.get_remote_players()

    pid_idx = 1
    for pid, rp in remotos.items():
        ci = (pid - 1) % len(PALETA_CORES)
        jogadores.append(JogadorDuals(rp.name, PALETA_CORES[ci], is_bot=False, is_remote=True))
        pid_idx += 1

    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo", "Bot Foxtrot", "Bot Golf", "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        jogadores.append(JogadorDuals(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True))
        bot_idx += 1

    # --- Misterioso ---
    misterioso = InimigoMisterioso(MISTERIOSO_X, MISTERIOSO_Y)
    misterioso_joga = random.random() < MISTERIOSO_CHANCE
    misterioso_duelo = False  # True quando o duelo bonus esta acontecendo
    armas_voando = []  # ArmaVoando em transito (telecinese)

    # --- Bracket de eliminacao ---
    ordem = _gerar_bracket(jogadores)
    sobreviventes = list(ordem)
    duelo_idx = 0
    rodada = 1

    for i, j in enumerate(jogadores):
        j.x = float(FILA_X_INICIO + i * FILA_ESPACO)
        j.y = float(FILA_Y)
        j.target_x = j.x
        j.target_y = j.y

    # --- Estado ---
    estado = "INTRO"
    tempo_estado = pygame.time.get_ticks()

    duelista1 = None
    duelista2 = None

    tiros = []
    particulas = []
    flashes = []

    armas_chao = []
    ultimo_drop = 0

    pulsacao = 0
    ultimo_pulso = 0

    alpha_fade = 255

    scoreboard_start = 0

    round_msg = ""
    round_vencedor = None

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
                # Dash do jogador humano local
                if ev.key == pygame.K_SPACE and estado == "FIGHT":
                    for d in (duelista1, duelista2):
                        if d and not d.is_bot and not d.is_remote and d.vivo and not d.dash_ativo:
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
                            if d.executar_dash(ddx, ddy) and cliente:
                                cliente.send_minigame_action({
                                    'action': 'duel_dash',
                                    'dx': ddx, 'dy': ddy,
                                })

            # Tiro do jogador humano local
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if estado == "FIGHT":
                    for d in (duelista1, duelista2):
                        if d and not d.is_bot and not d.is_remote and d.vivo:
                            mx, my = convert_mouse_position(pygame.mouse.get_pos())
                            _disparar(d, mx, my, tiros, particulas, flashes)
                            if cliente:
                                cliente.send_minigame_action({
                                    'action': 'duel_shot',
                                    'mx': mx, 'my': my,
                                })

        # ========== PULSACAO ==========
        if tempo - ultimo_pulso > 100:
            ultimo_pulso = tempo
            pulsacao = (pulsacao + 1) % 12

        # ========== ATUALIZAR MIRA ==========
        # Mira do jogador humano local (remotos recebem via rede)
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        for d in (duelista1, duelista2):
            if d and not d.is_bot and not d.is_remote:
                d.mira_x = float(mouse_pos[0])
                d.mira_y = float(mouse_pos[1])

        # ========== MAQUINA DE ESTADOS ==========

        if estado == "INTRO":
            if tempo_no_estado < 500:
                alpha_fade = int(255 * (1 - tempo_no_estado / 500))
            else:
                alpha_fade = 0

            if tempo_no_estado >= TEMPO_INTRO:
                estado = "SETUP_DUEL"
                tempo_estado = tempo

        elif estado == "SETUP_DUEL":
            if len(sobreviventes) < 2:
                estado = "SCOREBOARD"
                tempo_estado = tempo
                scoreboard_start = tempo
            else:
                idx1 = sobreviventes[duelo_idx * 2]
                idx2 = sobreviventes[duelo_idx * 2 + 1]
                duelista1 = jogadores[idx1]
                duelista2 = jogadores[idx2]
                duelista1.reset_duelo()
                duelista2.reset_duelo()

                duelista1.target_x = float(SPAWN_ESQ[0])
                duelista1.target_y = float(SPAWN_ESQ[1])
                duelista1.in_arena = True
                duelista2.target_x = float(SPAWN_DIR[0])
                duelista2.target_y = float(SPAWN_DIR[1])
                duelista2.in_arena = True

                tiros.clear()
                armas_chao.clear()
                particulas.clear()
                flashes.clear()
                ultimo_drop = tempo

                round_msg = f"{duelista1.nome}  vs  {duelista2.nome}"

                estado = "COUNTDOWN"
                tempo_estado = tempo

        elif estado == "COUNTDOWN":
            duelista1.x += (duelista1.target_x - duelista1.x) * 0.15
            duelista1.y += (duelista1.target_y - duelista1.y) * 0.15
            duelista2.x += (duelista2.target_x - duelista2.x) * 0.15
            duelista2.y += (duelista2.target_y - duelista2.y) * 0.15

            if tempo_no_estado >= TEMPO_COUNTDOWN:
                estado = "FIGHT"
                tempo_estado = tempo
                duelista1.x = duelista1.target_x
                duelista1.y = duelista1.target_y
                duelista2.x = duelista2.target_x
                duelista2.y = duelista2.target_y

                for d in (duelista1, duelista2):
                    if d.is_bot:
                        d.bot_next_shot = tempo + random.randint(500, 1000)
                        d.bot_strafe_timer = tempo + random.randint(200, 600)

        elif estado == "FIGHT":
            # --- Processar ações remotas via rede ---
            if cliente:
                for action in cliente.get_minigame_actions():
                    act = action.get('action')
                    for d in (duelista1, duelista2):
                        if d and d.is_remote and d.vivo:
                            if act == 'duel_input':
                                # Posição e mira do jogador remoto
                                d.x = action.get('x', d.x)
                                d.y = action.get('y', d.y)
                                d.mira_x = action.get('mx', d.mira_x)
                                d.mira_y = action.get('my', d.mira_y)
                            elif act == 'duel_shot':
                                rmx = action.get('mx', 0)
                                rmy = action.get('my', 0)
                                _disparar(d, rmx, rmy, tiros, particulas, flashes)
                            elif act == 'duel_dash':
                                ddx = action.get('dx', 0)
                                ddy = action.get('dy', 0)
                                d.executar_dash(ddx, ddy)

            # --- Movimento do jogador humano local ---
            teclas = pygame.key.get_pressed()
            for d in (duelista1, duelista2):
                if d and not d.is_bot and not d.is_remote and d.vivo:
                    dx_mov, dy_mov = 0.0, 0.0
                    if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                        dy_mov -= VEL_DUELO
                    if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                        dy_mov += VEL_DUELO
                    if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                        dx_mov -= VEL_DUELO
                    if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                        dx_mov += VEL_DUELO
                    d.vx = dx_mov
                    d.vy = dy_mov

            # --- Bot AI ---
            for d, oponente in [(duelista1, duelista2), (duelista2, duelista1)]:
                if d and d.is_bot and d.vivo:
                    _bot_ai(d, oponente, armas_chao, tiros, particulas, flashes, tempo)

            # --- Atualizar dash e posicoes dos duelistas ---
            for d in (duelista1, duelista2):
                if d and d.vivo:
                    if d.is_remote:
                        # Jogador remoto: posição vem da rede, só atualiza dash local
                        d.atualizar_dash()
                    else:
                        d.atualizar_dash()
                        if not d.dash_ativo:
                            # Movimento normal so quando nao esta em dash
                            d.x += d.vx
                            d.y += d.vy
                    d.x = max(ARENA_X + 4, min(d.x, ARENA_X + ARENA_W - TAM_JOGADOR - 4))
                    d.y = max(ARENA_Y + 4, min(d.y, ARENA_Y + ARENA_H - TAM_JOGADOR - 4))

            # --- Enviar posição final do jogador humano local via rede ---
            if cliente:
                for d in (duelista1, duelista2):
                    if d and not d.is_bot and not d.is_remote and d.vivo:
                        cliente.send_minigame_action({
                            'action': 'duel_input',
                            'x': d.x, 'y': d.y,
                            'mx': d.mira_x, 'my': d.mira_y,
                        })

            # --- Drop de armas (misterioso joga via telecinese) ---
            if tempo - ultimo_drop >= ARMA_DROP_INTERVALO:
                ultimo_drop = tempo
                if len([a for a in armas_chao if a.ativa]) < 3 and len(armas_voando) < 2:
                    tipo = random.choice(ARMA_TIPOS)
                    dest_x = random.randint(ARENA_X + 80, ARENA_X + ARENA_W - 80)
                    dest_y = random.randint(ARENA_Y + 80, ARENA_Y + ARENA_H - 80)
                    armas_voando.append(ArmaVoando(
                        tipo,
                        MISTERIOSO_X + TAM_MISTERIOSO // 2,
                        MISTERIOSO_Y + TAM_MISTERIOSO // 2,
                        dest_x, dest_y
                    ))

            # --- Atualizar armas voando (telecinese) ---
            for av in armas_voando[:]:
                av.atualizar()
                if av.concluida:
                    arma = ArmaChao(av.config)
                    arma.x = av.dx
                    arma.y = av.dy
                    arma.rect.x = int(av.dx) - ARMA_TAM // 2
                    arma.rect.y = int(av.dy) - ARMA_TAM // 2
                    armas_chao.append(arma)
                    armas_voando.remove(av)
                    # Efeito de chegada
                    for _ in range(10):
                        p = Particula(av.dx, av.dy, (180, 0, 50))
                        p.velocidade_x = random.uniform(-3, 3)
                        p.velocidade_y = random.uniform(-3, 3)
                        p.vida = random.randint(10, 20)
                        p.tamanho = random.uniform(2, 5)
                        particulas.append(p)

            # --- Checar coleta de armas (misterioso nao pega armas) ---
            for d in (duelista1, duelista2):
                if d and d.vivo and d.nome != "???":
                    d_rect = d.get_rect()
                    for arma in armas_chao:
                        if arma.ativa and d_rect.colliderect(arma.rect):
                            d.pegar_arma(arma)
                            arma.ativa = False
                            for _ in range(8):
                                p = Particula(arma.x, arma.y, arma.cor)
                                p.vida = random.randint(10, 20)
                                p.tamanho = random.uniform(2, 5)
                                particulas.append(p)

            # --- Atualizar tiros ---
            for tiro in tiros[:]:
                tiro.atualizar()
                if tiro.fora_da_tela():
                    tiros.remove(tiro)
                    continue

                # Colisao com paredes da arena
                if not ARENA_RECT.collidepoint(tiro.x, tiro.y):
                    tiros.remove(tiro)
                    continue

                # Colisao com duelistas
                for d in (duelista1, duelista2):
                    if d and d.vivo and hasattr(tiro, 'dono') and tiro.dono is not d:
                        if tempo >= d.invulneravel_ate and d.get_rect().colliderect(tiro.rect):
                            d.hp -= tiro.dano
                            d.invulneravel_ate = tempo + 300
                            flash = criar_explosao(
                                d.x + TAM_JOGADOR // 2, d.y + TAM_JOGADOR // 2,
                                d.cor, particulas, 10
                            )
                            flashes.append(flash)
                            if tiro in tiros:
                                tiros.remove(tiro)

                            if d.hp <= 0:
                                d.vivo = False
                                flash2 = criar_explosao(
                                    d.x + TAM_JOGADOR // 2, d.y + TAM_JOGADOR // 2,
                                    d.cor, particulas, 30
                                )
                                flashes.append(flash2)
                            break

            # --- Checar fim do duelo ---
            if duelista1 and duelista2:
                vencedor = None
                perdedor = None
                if not duelista1.vivo:
                    vencedor = duelista2
                    perdedor = duelista1
                elif not duelista2.vivo:
                    vencedor = duelista1
                    perdedor = duelista2

                if vencedor:
                    vencedor.vitorias += 1
                    round_vencedor = vencedor

                    if misterioso_duelo:
                        # Duelo bonus do misterioso acabou
                        tiros.clear()
                        armas_chao.clear()
                        armas_voando.clear()
                        if vencedor.nome == "???":
                            round_msg = "??? venceu..."
                            # Misterioso fica em 1o no placar
                            vencedor.vitorias = max(j.vitorias for j in jogadores) + 1
                        else:
                            round_msg = f"{vencedor.nome} derrotou ???!"
                        vencedor.in_arena = False
                        perdedor.in_arena = False
                        perdedor.eliminado = True
                        # Posicionar de volta na fila
                        for d in (vencedor, perdedor):
                            if d.nome == "???":
                                d.target_x = float(MISTERIOSO_X)
                                d.target_y = float(MISTERIOSO_Y)
                            else:
                                idx_d = jogadores.index(d)
                                d.target_x = float(FILA_X_INICIO + idx_d * FILA_ESPACO)
                                d.target_y = float(FILA_Y)
                        estado = "ROUND_END"
                        tempo_estado = tempo
                        # Forcar ir pro scoreboard apos o round_end
                        sobreviventes.clear()
                    else:
                        perdedor.eliminado = True
                        perdedor.in_arena = False

                        idx_p = jogadores.index(perdedor)
                        perdedor.target_x = float(FILA_X_INICIO + idx_p * FILA_ESPACO)
                        perdedor.target_y = float(FILA_Y)

                        vencedor.in_arena = False
                        idx_v = jogadores.index(vencedor)
                        vencedor.target_x = float(FILA_X_INICIO + idx_v * FILA_ESPACO)
                        vencedor.target_y = float(FILA_Y)

                        tiros.clear()
                        armas_chao.clear()
                        armas_voando.clear()

                        round_msg = f"{vencedor.nome} venceu!"
                        estado = "ROUND_END"
                        tempo_estado = tempo

        elif estado == "ROUND_END":
            if tempo_no_estado >= TEMPO_ROUND_END:
                duelo_idx += 1

                total_duelos_rodada = len(sobreviventes) // 2
                if duelo_idx >= total_duelos_rodada:
                    novos_sobreviventes = []
                    for i in range(0, len(sobreviventes), 2):
                        j1 = jogadores[sobreviventes[i]]
                        j2 = jogadores[sobreviventes[i + 1]]
                        if not j1.eliminado:
                            novos_sobreviventes.append(sobreviventes[i])
                        else:
                            novos_sobreviventes.append(sobreviventes[i + 1])
                    sobreviventes = novos_sobreviventes
                    duelo_idx = 0
                    rodada += 1

                if len(sobreviventes) < 2:
                    # Checar se misterioso quer duelar
                    if misterioso_joga and not misterioso_duelo:
                        misterioso_duelo = True
                        # Criar jogador misterioso para o duelo
                        misterioso_player = JogadorDuals("???", (20, 20, 20), is_bot=True)
                        misterioso_player.hp = MISTERIOSO_HP
                        jogadores.append(misterioso_player)

                        # O campeao eh o unico sobrevivente
                        campeao_idx = sobreviventes[0]
                        campeao = jogadores[campeao_idx]
                        campeao.reset_duelo()

                        # Posicionar
                        campeao.target_x = float(SPAWN_ESQ[0])
                        campeao.target_y = float(SPAWN_ESQ[1])
                        campeao.in_arena = True

                        misterioso_player.x = float(MISTERIOSO_X)
                        misterioso_player.y = float(MISTERIOSO_Y)
                        misterioso_player.target_x = float(SPAWN_DIR[0])
                        misterioso_player.target_y = float(SPAWN_DIR[1])
                        misterioso_player.in_arena = True

                        duelista1 = campeao
                        duelista2 = misterioso_player

                        tiros.clear()
                        armas_chao.clear()
                        armas_voando.clear()
                        particulas.clear()
                        flashes.clear()
                        ultimo_drop = tempo

                        round_msg = f"{campeao.nome}  vs  ???"
                        estado = "COUNTDOWN"
                        tempo_estado = tempo
                    else:
                        estado = "SCOREBOARD"
                        tempo_estado = tempo
                        scoreboard_start = tempo
                else:
                    estado = "SETUP_DUEL"
                    tempo_estado = tempo

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                pygame.mouse.set_visible(True)
                return None

        # ========== INTERPOLACAO DE POSICAO (fila) ==========
        for j in jogadores:
            if not j.in_arena:
                j.x += (j.target_x - j.x) * 0.12
                j.y += (j.target_y - j.y) * 0.12

        # ========== PARTICULAS ==========
        for p in particulas[:]:
            p.atualizar()
            if p.vida <= 0:
                particulas.remove(p)

        for f in flashes[:]:
            f['vida'] -= 1
            f['raio'] -= 2
            if f['vida'] <= 0:
                flashes.remove(f)

        # ========== DESENHAR ==========

        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
        desenhar_estrelas(tela, estrelas)

        # Arena
        _desenhar_arena(tela, tempo)

        # Armas no chao
        for arma in armas_chao:
            arma.desenhar(tela, tempo)

        # Misterioso com aura (ao lado da fila, so quando nao esta duelando)
        if not (misterioso_duelo and estado in ("COUNTDOWN", "FIGHT")):
            misterioso.x = MISTERIOSO_X
            misterioso.y = MISTERIOSO_Y
            misterioso.rect.x = MISTERIOSO_X
            misterioso.rect.y = MISTERIOSO_Y
            misterioso.desenhar_com_aura(tela, tempo)
        elif misterioso_duelo and duelista2 and duelista2.nome == "???":
            if duelista2.vivo or estado == "COUNTDOWN":
                # Desenhar misterioso com aura na posicao do duelista2 (tamanho do player)
                misterioso.tamanho = TAM_JOGADOR
                misterioso.x = int(duelista2.x)
                misterioso.y = int(duelista2.y)
                misterioso.rect = pygame.Rect(int(duelista2.x), int(duelista2.y), TAM_JOGADOR, TAM_JOGADOR)
                misterioso.desenhar_com_aura(tela, tempo)

        # Armas voando (telecinese do misterioso)
        for av in armas_voando:
            av.desenhar(tela, tempo)

        # Jogadores na fila
        for i, j in enumerate(jogadores):
            if not j.in_arena:
                j.desenhar(tela, fonte_nomes, pulsacao=pulsacao)
                if j.eliminado:
                    ix, iy = int(j.x), int(j.y)
                    pygame.draw.line(tela, VERMELHO,
                                     (ix + 2, iy + 2),
                                     (ix + TAM_JOGADOR - 2, iy + TAM_JOGADOR - 2), 3)
                    pygame.draw.line(tela, VERMELHO,
                                     (ix + TAM_JOGADOR - 2, iy + 2),
                                     (ix + 2, iy + TAM_JOGADOR - 2), 3)

        # Duelistas na arena
        if estado in ("COUNTDOWN", "FIGHT", "ROUND_END"):
            # Efeito visual de dash (rastro atras do jogador)
            for d in (duelista1, duelista2):
                if d and d.vivo and d.dash_ativo:
                    ddx, ddy = d.dash_direcao
                    for i in range(3):
                        alpha = int(180 * (1 - i / 3))
                        offset = (i + 1) * 15
                        trail_x = d.x - ddx * offset
                        trail_y = d.y - ddy * offset
                        trail_surf = pygame.Surface((TAM_JOGADOR, TAM_JOGADOR), pygame.SRCALPHA)
                        pygame.draw.rect(trail_surf, (*d.cor, alpha),
                                         (0, 0, TAM_JOGADOR, TAM_JOGADOR), 0, 5)
                        tela.blit(trail_surf, (int(trail_x), int(trail_y)))
                    # Particulas de energia orbitando
                    for i in range(8):
                        angulo = (tempo * 5 + i * 45) % 360
                        raio = 30 + math.sin(tempo / 100 + i) * 5
                        px = d.x + TAM_JOGADOR // 2 + int(raio * math.cos(math.radians(angulo)))
                        py = d.y + TAM_JOGADOR // 2 + int(raio * math.sin(math.radians(angulo)))
                        pygame.draw.circle(tela, (100, 200, 255), (px, py), 4)

            for d in (duelista1, duelista2):
                if d and (d.vivo or estado == "COUNTDOWN"):
                    # Misterioso eh desenhado com aura acima, pular aqui
                    if misterioso_duelo and d.nome == "???":
                        continue
                    d.desenhar(tela, fonte_nomes, destaque=True, pulsacao=pulsacao, show_hp=True)

            # Armas na mao dos duelistas (durante luta)
            if estado == "FIGHT":
                for d in (duelista1, duelista2):
                    if d and d.vivo and d.arma:
                        _desenhar_arma_jogador(tela, d, tempo)

        # Tiros
        for tiro in tiros:
            tiro.desenhar(tela)

        # Particulas
        for p in particulas:
            p.desenhar(tela)

        # Flashes
        for f in flashes:
            if f['vida'] > 0 and f['raio'] > 0:
                flash_surf = pygame.Surface((f['raio'] * 2, f['raio'] * 2), pygame.SRCALPHA)
                alpha_f = min(255, int(255 * (f['vida'] / 10)))
                pygame.draw.circle(flash_surf, (*f['cor'], alpha_f),
                                   (f['raio'], f['raio']), f['raio'])
                tela.blit(flash_surf, (int(f['x']) - f['raio'], int(f['y']) - f['raio']))

        # ========== HUD ==========
        hud_bg = pygame.Surface((LARGURA, 50), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        tela.blit(hud_bg, (0, 0))

        titulo_s = fonte_hud.render("DUEL", True, (200, 200, 255))
        tela.blit(titulo_s, (LARGURA // 2 - titulo_s.get_width() // 2, 5))

        if estado not in ("INTRO", "SCOREBOARD"):
            if misterioso_duelo:
                rodada_nome = "BOSS"
                rodada_cor = (180, 0, 50)
            else:
                rodada_nomes = {1: "Quartas", 2: "Semifinal", 3: "FINAL"}
                rodada_nome = rodada_nomes.get(rodada, f"Rodada {rodada}")
                rodada_cor = (180, 180, 200)
            rodada_s = fonte_peq.render(rodada_nome, True, rodada_cor)
            tela.blit(rodada_s, (15, 8))

            if duelista1 and duelista2:
                vs_s = fonte_peq.render(f"{duelista1.nome} vs {duelista2.nome}", True, (200, 200, 220))
                tela.blit(vs_s, (15, 26))

        # HP bars no HUD
        if estado == "FIGHT" and duelista1 and duelista2:
            hp_bar_w = 150
            hp_bar_h = 12
            hp_x1 = LARGURA // 2 - hp_bar_w - 40
            hp_y = 30

            hp_max1 = MISTERIOSO_HP if duelista1.nome == "???" else HP_MAX
            hp_max2 = MISTERIOSO_HP if duelista2.nome == "???" else HP_MAX

            nome1 = fonte_peq.render(duelista1.nome, True, duelista1.cor)
            tela.blit(nome1, (hp_x1, hp_y - 14))
            pygame.draw.rect(tela, (40, 40, 40), (hp_x1, hp_y, hp_bar_w, hp_bar_h), 0, 3)
            r1 = max(0, duelista1.hp / hp_max1)
            cor1 = VERDE if r1 > 0.5 else AMARELO if r1 > 0.25 else VERMELHO
            pygame.draw.rect(tela, cor1, (hp_x1, hp_y, int(hp_bar_w * r1), hp_bar_h), 0, 3)

            hp_x2 = LARGURA // 2 + 40
            if duelista2.nome == "???":
                # Misterioso sem barra de vida - so nome
                nome2 = fonte_peq.render("???", True, (180, 0, 50))
                tela.blit(nome2, (hp_x2 + hp_bar_w - nome2.get_width(), hp_y - 14))
                # Barra misteriosa (nao mostra HP real)
                pygame.draw.rect(tela, (40, 40, 40), (hp_x2, hp_y, hp_bar_w, hp_bar_h), 0, 3)
                pygame.draw.rect(tela, (180, 0, 50), (hp_x2, hp_y, hp_bar_w, hp_bar_h), 1, 3)
            else:
                nome2_cor = duelista2.cor
                nome2 = fonte_peq.render(duelista2.nome, True, nome2_cor)
                tela.blit(nome2, (hp_x2 + hp_bar_w - nome2.get_width(), hp_y - 14))
                pygame.draw.rect(tela, (40, 40, 40), (hp_x2, hp_y, hp_bar_w, hp_bar_h), 0, 3)
                r2 = max(0, duelista2.hp / hp_max2)
                cor2 = VERDE if r2 > 0.5 else AMARELO if r2 > 0.25 else VERMELHO
                pygame.draw.rect(tela, cor2, (hp_x2, hp_y, int(hp_bar_w * r2), hp_bar_h), 0, 3)

            vs_txt = fonte_hud.render("VS", True, (255, 80, 80))
            tela.blit(vs_txt, (LARGURA // 2 - vs_txt.get_width() // 2, hp_y - 3))

            # Mostrar arma atual dos duelistas no HUD
            for hud_d, hud_x in [(duelista1, hp_x1), (duelista2, hp_x2)]:
                if hud_d.arma:
                    arma_txt = fonte_peq.render(f"{hud_d.arma} [{hud_d.tiros_arma}]", True, (200, 200, 100))
                    tela.blit(arma_txt, (hud_x, hp_y + hp_bar_h + 2))

            # Indicador de dash para jogador humano
            for hud_d in (duelista1, duelista2):
                if hud_d and not hud_d.is_bot:
                    dash_pronto = (tempo - hud_d.dash_tempo_cooldown >= DASH_COOLDOWN) and not hud_d.dash_ativo
                    cor_dash = (100, 200, 255) if dash_pronto else (60, 60, 80)
                    dash_txt = fonte_peq.render("DASH" if dash_pronto else "DASH (CD)", True, cor_dash)
                    tela.blit(dash_txt, (LARGURA // 2 - dash_txt.get_width() // 2, hp_y + hp_bar_h + 4))

        # ========== COUNTDOWN ==========
        if estado == "COUNTDOWN":
            vs_big = fonte_media.render(round_msg, True, (255, 220, 100))
            tela.blit(vs_big, (LARGURA // 2 - vs_big.get_width() // 2, ARENA_Y + 20))

            t = tempo_no_estado
            if t < 500:
                count_txt = "3"
            elif t < 1000:
                count_txt = "2"
            elif t < 1500:
                count_txt = "1"
            else:
                count_txt = "GO!"

            cor_count = (255, 255, 100) if count_txt == "GO!" else (255, 255, 255)
            count_s = fonte_countdown.render(count_txt, True, cor_count)
            tela.blit(count_s, (LARGURA // 2 - count_s.get_width() // 2,
                                ARENA_Y + ARENA_H // 2 - count_s.get_height() // 2))

        # ========== ROUND END ==========
        if estado == "ROUND_END":
            msg_s = fonte_media.render(round_msg, True, (100, 255, 100))
            tela.blit(msg_s, (LARGURA // 2 - msg_s.get_width() // 2,
                              ARENA_Y + ARENA_H // 2 - 20))

        # ========== INTRO ==========
        if estado == "INTRO" and tempo_no_estado > 500:
            titulo_intro = fonte_grande.render("DUEL", True, (255, 220, 100))
            tela.blit(titulo_intro,
                      (LARGURA // 2 - titulo_intro.get_width() // 2, ALTURA_JOGO // 2 - 60))
            sub_intro = fonte_media.render("Duelos 1v1 - Eliminatoria!", True, (200, 200, 220))
            tela.blit(sub_intro,
                      (LARGURA // 2 - sub_intro.get_width() // 2, ALTURA_JOGO // 2))

        # ========== SCOREBOARD ==========
        if estado == "SCOREBOARD":
            _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_media, fonte_score,
                                 fonte_peq, tempo, scoreboard_start)

        # Fade
        if alpha_fade > 0:
            fade_surf = pygame.Surface((LARGURA, ALTURA))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha_fade)
            tela.blit(fade_surf, (0, 0))

        # ESC hint
        esc_s = fonte_peq.render("ESC: Sair", True, (80, 80, 100))
        tela.blit(esc_s, (LARGURA - 70, ALTURA_JOGO - 20))

        # Instrucoes
        if estado == "FIGHT":
            for d in (duelista1, duelista2):
                if d and not d.is_bot and d.vivo:
                    inst = fonte_peq.render("WASD: Mover | CLICK: Atirar | SPACE: Dash", True, (150, 150, 170))
                    tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 20))
                    break

        # Mira customizada
        mouse_mira = convert_mouse_position(pygame.mouse.get_pos())
        desenhar_mira(tela, mouse_mira, (mira_surface, mira_rect))

        present_frame()
        relogio.tick(FPS)
