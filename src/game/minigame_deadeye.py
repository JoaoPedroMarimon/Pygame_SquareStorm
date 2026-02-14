#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Deadeye - Equipes 4v4 com Desert Eagle.
Arena dividida ao meio por linha vermelha. Cada equipe de um lado.
Quando morre, jogador vai para corredor atras do time adversario com tiro normal.
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

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
HP_MAX = 2
NUM_RODADAS = 3

PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Arena principal (um pouco menor para dar espaco ao corredor)
ARENA_X = 100
ARENA_Y = 90
ARENA_W = LARGURA - 200
ARENA_H = ALTURA_JOGO - 200
ARENA_RECT = pygame.Rect(ARENA_X, ARENA_Y, ARENA_W, ARENA_H)

# Linha vermelha central
LINHA_X = ARENA_X + ARENA_W // 2

# Corredor de mortos (ao redor da arena - maior)
CORREDOR = 80
CORREDOR_TOP = pygame.Rect(ARENA_X - CORREDOR, ARENA_Y - CORREDOR, ARENA_W + CORREDOR * 2, CORREDOR)
CORREDOR_BOTTOM = pygame.Rect(ARENA_X - CORREDOR, ARENA_Y + ARENA_H, ARENA_W + CORREDOR * 2, CORREDOR)
CORREDOR_LEFT = pygame.Rect(ARENA_X - CORREDOR, ARENA_Y, CORREDOR, ARENA_H)
CORREDOR_RIGHT = pygame.Rect(ARENA_X + ARENA_W, ARENA_Y, CORREDOR, ARENA_H)

# Area total jogavel (arena + corredor)
AREA_TOTAL = pygame.Rect(ARENA_X - CORREDOR, ARENA_Y - CORREDOR,
                          ARENA_W + CORREDOR * 2, ARENA_H + CORREDOR * 2)

# Spawns equipe A (lado esquerdo)
SPAWNS_A = [
    (ARENA_X + 80, ARENA_Y + ARENA_H // 5),
    (ARENA_X + 80, ARENA_Y + 2 * ARENA_H // 5),
    (ARENA_X + 80, ARENA_Y + 3 * ARENA_H // 5),
    (ARENA_X + 80, ARENA_Y + 4 * ARENA_H // 5),
]

# Spawns equipe B (lado direito)
SPAWNS_B = [
    (ARENA_X + ARENA_W - 80 - TAM_JOGADOR, ARENA_Y + ARENA_H // 5),
    (ARENA_X + ARENA_W - 80 - TAM_JOGADOR, ARENA_Y + 2 * ARENA_H // 5),
    (ARENA_X + ARENA_W - 80 - TAM_JOGADOR, ARENA_Y + 3 * ARENA_H // 5),
    (ARENA_X + ARENA_W - 80 - TAM_JOGADOR, ARENA_Y + 4 * ARENA_H // 5),
]

# Spawns zona de mortos (atras do time inimigo)
# Time A morre -> spawna atras do time B (corredor direito)
SPAWN_MORTO_A = (ARENA_X + ARENA_W + 5, ARENA_Y + ARENA_H // 2 - TAM_JOGADOR // 2)
# Time B morre -> spawna atras do time A (corredor esquerdo)
SPAWN_MORTO_B = (ARENA_X - CORREDOR + 5, ARENA_Y + ARENA_H // 2 - TAM_JOGADOR // 2)

# Tempos de estado (ms)
TEMPO_INTRO = 2000
TEMPO_TEAM_SHOW = 3000
TEMPO_COUNTDOWN = 3000
TEMPO_ROUND_END = 2500
TEMPO_SCOREBOARD = 5000

# Velocidade
VEL_DEADEYE = 3.5

# Dash
DASH_VELOCIDADE = 25
DASH_DURACAO = 8
DASH_COOLDOWN = 500
DASH_INVULN_POS = 200

# Bot AI
BOT_STRAFE_INTERVALO = 800
BOT_SHOOT_DELAY_MIN = 500
BOT_SHOOT_DELAY_MAX = 900
BOT_DIST_IDEAL = 200
BOT_DIST_RECUAR = 80
BOT_DIST_AVANCAR = 350

# Arma
TAMANHO_SURF_ARMA = 120
ESCALA_ARMA = 0.75

# Cores equipes
COR_EQUIPE_A = (60, 120, 255)   # azul
COR_EQUIPE_B = (255, 60, 60)    # vermelho


# ============================================================
#  CLASSE
# ============================================================

class JogadorDeadeye:
    """Jogador no minigame Deadeye."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_remote = is_remote
        self.hp = HP_MAX
        self.vivo = True
        self.kills = 0
        self.equipe = 0  # 0=A, 1=B
        self.rodadas_vencidas = 0

        # Zona de mortos
        self.morto_zona = False
        self.tem_deagle = False  # so 1 jogador por vez tem a deagle

        # Posicao
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0

        # Arma (padrao: sem arma, so o portador da deagle atira)
        self.arma = None
        self.cooldown_arma = 400
        self.dano_arma = 1
        self.velocidade_arma = 10
        self.raio_arma = 4
        self.tiros_arma = 0
        self.tempo_ultimo_tiro = 0

        # Mira
        self.mira_x = 0.0
        self.mira_y = 0.0

        # Invulnerabilidade
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

        # Bot AI
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_strafe_dir = 1
        self.bot_move_timer = 0
        self.bot_dir_x = 0.0
        self.bot_dir_y = 0.0

    def reset_rodada(self, spawn_x, spawn_y):
        """Reseta para nova rodada."""
        self.hp = HP_MAX
        self.vivo = True
        self.morto_zona = False
        self.tem_deagle = False
        self.arma = None
        self.cooldown_arma = 400
        self.dano_arma = 1
        self.velocidade_arma = 10
        self.raio_arma = 4
        self.tiros_arma = 0
        self.tempo_ultimo_tiro = 0
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.invulneravel_ate = 0
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_move_timer = 0

    def dar_deagle(self):
        """Da a Desert Eagle para este jogador."""
        self.tem_deagle = True
        self.arma = 'Desert Eagle'
        self.cooldown_arma = 500
        self.dano_arma = 3
        self.velocidade_arma = 15
        self.raio_arma = 4

    def tirar_deagle(self):
        """Remove a Desert Eagle deste jogador."""
        self.tem_deagle = False
        self.arma = None
        self.cooldown_arma = 400
        self.dano_arma = 1
        self.velocidade_arma = 10
        self.raio_arma = 4

    def ir_zona_mortos(self):
        """Transfere jogador para a zona de mortos."""
        self.morto_zona = True
        self.tem_deagle = False
        self.vivo = True  # continua vivo na zona
        self.hp = 999  # imortal na zona
        self.invulneravel_ate = pygame.time.get_ticks() + 1000
        # Tiro normal (mais lento que o normal)
        self.arma = None
        self.cooldown_arma = 500
        self.dano_arma = 1
        self.velocidade_arma = 7
        self.raio_arma = 3
        self.vx = 0.0
        self.vy = 0.0
        self.dash_ativo = False
        # Spawn atras do time inimigo
        if self.equipe == 0:
            self.x, self.y = float(SPAWN_MORTO_A[0]), float(SPAWN_MORTO_A[1])
        else:
            self.x, self.y = float(SPAWN_MORTO_B[0]), float(SPAWN_MORTO_B[1])

    def na_arena(self):
        """Retorna True se esta na arena principal (nao na zona de mortos)."""
        return self.vivo and not self.morto_zona

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
            self._clampar_posicao()
            self.dash_frames_restantes -= 1
            if self.dash_frames_restantes <= 0:
                self.dash_ativo = False
                self.dash_tempo_fim = tempo
                self.invulneravel_ate = tempo + DASH_INVULN_POS
        if not self.dash_ativo and self.dash_tempo_fim > 0:
            if tempo - self.dash_tempo_fim >= DASH_INVULN_POS:
                self.dash_tempo_fim = 0

    def _clampar_posicao(self):
        """Mantem jogador dentro dos limites corretos."""
        if self.morto_zona:
            # Pode andar no corredor ao redor da arena
            self.x = max(AREA_TOTAL.left + 2, min(self.x, AREA_TOTAL.right - TAM_JOGADOR - 2))
            self.y = max(AREA_TOTAL.top + 2, min(self.y, AREA_TOTAL.bottom - TAM_JOGADOR - 2))
            # Nao pode entrar na arena principal
            jrect = pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)
            arena_inner = pygame.Rect(ARENA_X + 2, ARENA_Y + 2, ARENA_W - 4, ARENA_H - 4)
            if jrect.colliderect(arena_inner):
                # Empurrar pra fora da arena
                cx = self.x + TAM_JOGADOR // 2
                cy = self.y + TAM_JOGADOR // 2
                acx = ARENA_X + ARENA_W // 2
                acy = ARENA_Y + ARENA_H // 2
                # Determinar lado mais proximo para empurrar
                dist_left = abs(cx - ARENA_X)
                dist_right = abs(cx - (ARENA_X + ARENA_W))
                dist_top = abs(cy - ARENA_Y)
                dist_bottom = abs(cy - (ARENA_Y + ARENA_H))
                menor = min(dist_left, dist_right, dist_top, dist_bottom)
                if menor == dist_left:
                    self.x = ARENA_X - TAM_JOGADOR - 2
                elif menor == dist_right:
                    self.x = ARENA_X + ARENA_W + 2
                elif menor == dist_top:
                    self.y = ARENA_Y - TAM_JOGADOR - 2
                else:
                    self.y = ARENA_Y + ARENA_H + 2
        else:
            # Na arena: ficar dentro da arena, respeitar linha vermelha
            self.y = max(ARENA_Y + 4, min(self.y, ARENA_Y + ARENA_H - TAM_JOGADOR - 4))
            if self.equipe == 0:
                # Time A: lado esquerdo, nao pode cruzar linha
                self.x = max(ARENA_X + 4, min(self.x, LINHA_X - TAM_JOGADOR - 4))
            else:
                # Time B: lado direito, nao pode cruzar linha
                self.x = max(LINHA_X + 4, min(self.x, ARENA_X + ARENA_W - TAM_JOGADOR - 4))

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)

    def get_centro(self):
        return (self.x + TAM_JOGADOR // 2, self.y + TAM_JOGADOR // 2)

    def desenhar(self, tela, fonte, show_hp=True):
        """Desenha o jogador na tela."""
        if not self.vivo:
            return

        tam = TAM_JOGADOR
        ix, iy = int(self.x), int(self.y)

        # Piscar se invulneravel
        tempo = pygame.time.get_ticks()
        if tempo < self.invulneravel_ate and (tempo // 80) % 2 == 0:
            return

        # Sombra
        pygame.draw.rect(tela, (15, 12, 20), (ix + 3, iy + 3, tam, tam), 0, 3)
        # Cor escura
        pygame.draw.rect(tela, self.cor_escura, (ix, iy, tam, tam), 0, 5)
        # Cor principal
        pygame.draw.rect(tela, self.cor, (ix + 2, iy + 2, tam - 4, tam - 4), 0, 3)
        # Highlight
        pygame.draw.rect(tela, self.cor_brilhante, (ix + 4, iy + 4, 7, 7), 0, 2)

        # Indicador de equipe (bolinha na lateral)
        cor_eq = COR_EQUIPE_A if self.equipe == 0 else COR_EQUIPE_B
        pygame.draw.circle(tela, cor_eq, (ix + tam + 4, iy + 4), 3)

        # Indicador zona de mortos (X sobre o jogador)
        if self.morto_zona:
            ghost_surf = pygame.Surface((tam, tam), pygame.SRCALPHA)
            ghost_surf.fill((100, 100, 100, 60))
            tela.blit(ghost_surf, (ix, iy))

        # Nome (verde se for o jogador humano controlado)
        cor_nome = (0, 255, 100) if not self.is_bot and not self.is_remote else BRANCO
        nome_surf = fonte.render(self.nome, True, cor_nome)
        nx = ix + tam // 2 - nome_surf.get_width() // 2
        ny = iy - 16
        bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        tela.blit(bg, (nx - 3, ny - 1))
        tela.blit(nome_surf, (nx, ny))

        # Barra de HP (so se na arena)
        if show_hp and not self.morto_zona:
            hp_w = tam
            hp_h = 4
            hp_x = ix
            hp_y = iy + tam + 4
            pygame.draw.rect(tela, (40, 40, 40), (hp_x, hp_y, hp_w, hp_h), 0, 2)
            hp_ratio = max(0, self.hp / HP_MAX)
            cor_hp = VERDE if hp_ratio > 0.5 else VERMELHO
            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h), 0, 2)


# ============================================================
#  FUNCOES AUXILIARES
# ============================================================

def _disparar_deadeye(jogador, mouse_x, mouse_y, tiros, particulas, flashes):
    """Dispara um tiro (Desert Eagle ou normal dependendo do estado)."""
    tempo = pygame.time.get_ticks()
    if tempo - jogador.tempo_ultimo_tiro < jogador.cooldown_arma:
        return

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

    cor_tiro = COR_EQUIPE_A if jogador.equipe == 0 else COR_EQUIPE_B
    tiro = Tiro(ponta_x, ponta_y, dx, dy, cor_tiro, velocidade=jogador.velocidade_arma)
    tiro.dano = jogador.dano_arma
    tiro.raio = jogador.raio_arma
    tiro.dono = jogador
    tiros.append(tiro)

    # Efeitos
    if jogador.tem_deagle:
        # Desert Eagle: efeito dourado maior
        for _ in range(10):
            p = Particula(ponta_x + random.uniform(-3, 3), ponta_y + random.uniform(-3, 3),
                          (255, random.randint(180, 255), 0))
            p.velocidade_x = dx * random.uniform(3, 7) + random.uniform(-1.5, 1.5)
            p.velocidade_y = dy * random.uniform(3, 7) + random.uniform(-1.5, 1.5)
            p.vida = random.randint(8, 18)
            p.tamanho = random.uniform(2, 4)
            particulas.append(p)

        flashes.append({
            'x': ponta_x, 'y': ponta_y,
            'raio': 20, 'vida': 8,
            'cor': (255, 200, 0)
        })
    else:
        # Tiro normal: efeito menor
        for _ in range(5):
            p = Particula(ponta_x + random.uniform(-3, 3), ponta_y + random.uniform(-3, 3),
                          (255, random.randint(150, 255), 0))
            p.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-1, 1)
            p.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-1, 1)
            p.vida = random.randint(6, 14)
            p.tamanho = random.uniform(1.5, 3)
            particulas.append(p)

        flashes.append({
            'x': ponta_x, 'y': ponta_y,
            'raio': 12, 'vida': 6,
            'cor': (255, 180, 0)
        })

    # Som
    try:
        from src.utils.sound import gerar_som_tiro
        som = pygame.mixer.Sound(gerar_som_tiro())
        vol = 0.35 if jogador.tem_deagle else 0.2
        som.set_volume(vol)
        pygame.mixer.Channel(1).play(som)
    except:
        pass


def _desenhar_arma_jogador(tela, jogador, tempo_atual):
    """Desenha a Desert Eagle na mao do jogador."""
    if not jogador.vivo or not jogador.tem_deagle:
        return

    centro_x = jogador.x + TAM_JOGADOR // 2
    centro_y = jogador.y + TAM_JOGADOR // 2

    dx = jogador.mira_x - centro_x
    dy = jogador.mira_y - centro_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist
    else:
        dx, dy = 1.0, 0.0

    temp_surf = pygame.Surface((TAMANHO_SURF_ARMA, TAMANHO_SURF_ARMA), pygame.SRCALPHA)

    class _Temp:
        pass

    jt = _Temp()
    jt.x = TAMANHO_SURF_ARMA // 2 - TAM_JOGADOR // 2
    jt.y = TAMANHO_SURF_ARMA // 2 - TAM_JOGADOR // 2
    jt.tamanho = TAM_JOGADOR
    jt.cor = jogador.cor
    jt.tempo_ultimo_tiro = jogador.tempo_ultimo_tiro
    jt.tempo_cooldown = jogador.cooldown_arma
    jt.desert_eagle_ativa = True
    jt.tiros_desert_eagle = 999

    pos_mouse_temp = (
        TAMANHO_SURF_ARMA // 2 + dx * 60,
        TAMANHO_SURF_ARMA // 2 + dy * 60
    )

    desenhar_desert_eagle(temp_surf, jt, pos_mouse_temp)

    novo_tam = int(TAMANHO_SURF_ARMA * ESCALA_ARMA)
    arma_reduzida = pygame.transform.scale(temp_surf, (novo_tam, novo_tam))
    tela.blit(arma_reduzida, (int(centro_x) - novo_tam // 2, int(centro_y) - novo_tam // 2))


def _desenhar_arena(tela, tempo):
    """Desenha a arena com divisao por equipes."""
    # Arena principal
    arena_surf = pygame.Surface((ARENA_W, ARENA_H), pygame.SRCALPHA)
    arena_surf.fill((20, 18, 32, 200))

    # Grid sutil
    for gx in range(0, ARENA_W, 40):
        pygame.draw.line(arena_surf, (30, 28, 45), (gx, 0), (gx, ARENA_H), 1)
    for gy in range(0, ARENA_H, 40):
        pygame.draw.line(arena_surf, (30, 28, 45), (0, gy), (ARENA_W, gy), 1)

    # Tonalidade por lado
    lado_a = pygame.Surface((ARENA_W // 2, ARENA_H), pygame.SRCALPHA)
    lado_a.fill((40, 60, 120, 15))
    arena_surf.blit(lado_a, (0, 0))

    lado_b = pygame.Surface((ARENA_W // 2, ARENA_H), pygame.SRCALPHA)
    lado_b.fill((120, 40, 40, 15))
    arena_surf.blit(lado_b, (ARENA_W // 2, 0))

    tela.blit(arena_surf, (ARENA_X, ARENA_Y))

    # Borda arena
    borda_cor = (60, 50, 90)
    pygame.draw.rect(tela, borda_cor, (ARENA_X, ARENA_Y, ARENA_W, ARENA_H), 2, 5)

    # Corredor de mortos (fundo mais escuro)
    corr_cor = (10, 8, 18, 160)
    # Top
    cs = pygame.Surface((CORREDOR_TOP.width, CORREDOR_TOP.height), pygame.SRCALPHA)
    cs.fill(corr_cor)
    tela.blit(cs, CORREDOR_TOP.topleft)
    pygame.draw.rect(tela, (40, 30, 50), CORREDOR_TOP, 1)
    # Bottom
    cs = pygame.Surface((CORREDOR_BOTTOM.width, CORREDOR_BOTTOM.height), pygame.SRCALPHA)
    cs.fill(corr_cor)
    tela.blit(cs, CORREDOR_BOTTOM.topleft)
    pygame.draw.rect(tela, (40, 30, 50), CORREDOR_BOTTOM, 1)
    # Left
    cs = pygame.Surface((CORREDOR_LEFT.width, CORREDOR_LEFT.height), pygame.SRCALPHA)
    cs.fill(corr_cor)
    tela.blit(cs, CORREDOR_LEFT.topleft)
    pygame.draw.rect(tela, (40, 30, 50), CORREDOR_LEFT, 1)
    # Right
    cs = pygame.Surface((CORREDOR_RIGHT.width, CORREDOR_RIGHT.height), pygame.SRCALPHA)
    cs.fill(corr_cor)
    tela.blit(cs, CORREDOR_RIGHT.topleft)
    pygame.draw.rect(tela, (40, 30, 50), CORREDOR_RIGHT, 1)

    # Borda externa total
    pygame.draw.rect(tela, (50, 40, 70), AREA_TOTAL, 1)

    # Linha vermelha central com glow pulsante
    pulso = (math.sin(tempo / 400) + 1) / 2
    glow_alpha = int(40 + pulso * 40)
    # Glow largo
    glow_surf = pygame.Surface((20, ARENA_H), pygame.SRCALPHA)
    glow_surf.fill((255, 30, 30, glow_alpha))
    tela.blit(glow_surf, (LINHA_X - 10, ARENA_Y))
    # Linha principal
    pygame.draw.line(tela, (255, 40, 40), (LINHA_X, ARENA_Y), (LINHA_X, ARENA_Y + ARENA_H), 3)
    # Linha brilhante fina
    bright = int(200 + pulso * 55)
    pygame.draw.line(tela, (bright, bright // 3, bright // 3),
                     (LINHA_X, ARENA_Y), (LINHA_X, ARENA_Y + ARENA_H), 1)

    # Labels nas zonas de mortos
    fonte_zona = pygame.font.SysFont("Arial", 10)
    txt_l = fonte_zona.render("DEAD ZONE", True, (60, 50, 50))
    tela.blit(txt_l, (ARENA_X - CORREDOR + 2, ARENA_Y - CORREDOR + 2))
    txt_r = fonte_zona.render("DEAD ZONE", True, (60, 50, 50))
    tela.blit(txt_r, (ARENA_X + ARENA_W + 2, ARENA_Y - CORREDOR + 2))


def _desenhar_portador_indicador(tela, jogador, fonte, tempo):
    """Desenha indicador sobre o jogador que tem a deagle."""
    if not jogador.vivo or not jogador.tem_deagle:
        return
    ix = int(jogador.x)
    iy = int(jogador.y)
    # Seta dourada pulsante acima do jogador
    pulso = math.sin(tempo / 200) * 3
    py = iy - 28 + int(pulso)
    px = ix + TAM_JOGADOR // 2
    # Triangulo apontando pra baixo
    pygame.draw.polygon(tela, (255, 220, 50), [
        (px, py + 8), (px - 6, py), (px + 6, py)
    ])
    # Texto "DEAGLE"
    txt = fonte.render("DEAGLE", True, (255, 220, 80))
    tela.blit(txt, (px - txt.get_width() // 2, py - 14))


def _desenhar_hud(tela, jogadores, jogador_humano, equipe_a_rodadas, equipe_b_rodadas,
                  fonte_hud, fonte_peq, estado, esperando_resultado=False):
    """Desenha o HUD do jogo."""
    # Titulo
    titulo = fonte_hud.render("DEADEYE", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 5))

    # Contagem de vivos por equipe
    vivos_a = sum(1 for j in jogadores if j.equipe == 0 and j.na_arena())
    vivos_b = sum(1 for j in jogadores if j.equipe == 1 and j.na_arena())
    mortos_zona_a = sum(1 for j in jogadores if j.equipe == 0 and j.morto_zona)
    mortos_zona_b = sum(1 for j in jogadores if j.equipe == 1 and j.morto_zona)

    # Equipe A (esquerda)
    eq_a_txt = fonte_hud.render(f"EQUIPE A: {vivos_a}/4", True, COR_EQUIPE_A)
    tela.blit(eq_a_txt, (20, 5))

    # Rodadas equipe A
    for i in range(NUM_RODADAS):
        cor_r = COR_EQUIPE_A if i < equipe_a_rodadas else (40, 40, 40)
        pygame.draw.circle(tela, cor_r, (22 + i * 16, 30), 5)

    # Equipe B (direita)
    eq_b_txt = fonte_hud.render(f"EQUIPE B: {vivos_b}/4", True, COR_EQUIPE_B)
    tela.blit(eq_b_txt, (LARGURA - eq_b_txt.get_width() - 20, 5))

    # Rodadas equipe B
    for i in range(NUM_RODADAS):
        cor_r = COR_EQUIPE_B if i < equipe_b_rodadas else (40, 40, 40)
        pygame.draw.circle(tela, cor_r, (LARGURA - 20 - (NUM_RODADAS - 1 - i) * 16, 30), 5)

    # Info jogador local
    if jogador_humano.vivo:
        # HP
        hp_txt = f"HP: {jogador_humano.hp}" if not jogador_humano.morto_zona else "DEAD ZONE"
        cor_hp = VERDE if jogador_humano.hp > 1 else VERMELHO
        if jogador_humano.morto_zona:
            cor_hp = (150, 100, 100)
        hp_surf = fonte_hud.render(hp_txt, True, cor_hp)
        tela.blit(hp_surf, (LARGURA // 2 - hp_surf.get_width() // 2, ALTURA_JOGO - 30))

        # Status da arma
        if jogador_humano.tem_deagle:
            if esperando_resultado:
                arma_nome = "Desert Eagle - AGUARDANDO..."
            else:
                arma_nome = "Desert Eagle - SEU TURNO!"
            arma_cor = (255, 220, 50)
        elif jogador_humano.morto_zona:
            arma_nome = "Tiro Normal"
            arma_cor = (150, 130, 130)
        else:
            arma_nome = "Aguardando turno..."
            arma_cor = (120, 120, 120)
        arma_surf = fonte_peq.render(arma_nome, True, arma_cor)
        tela.blit(arma_surf, (LARGURA // 2 - arma_surf.get_width() // 2, ALTURA_JOGO - 15))

        # Dash cooldown
        tempo = pygame.time.get_ticks()
        if not jogador_humano.is_bot:
            cd_restante = max(0, DASH_COOLDOWN - (tempo - jogador_humano.dash_tempo_cooldown))
            if cd_restante > 0:
                cd_ratio = cd_restante / DASH_COOLDOWN
                cd_w = 60
                cd_x = LARGURA // 2 - cd_w // 2
                cd_y = ALTURA_JOGO - 40
                pygame.draw.rect(tela, (40, 40, 40), (cd_x, cd_y, cd_w, 4), 0, 2)
                pygame.draw.rect(tela, CIANO, (cd_x, cd_y, int(cd_w * (1 - cd_ratio)), 4), 0, 2)


def _desenhar_scoreboard(tela, jogadores, equipe_a_rodadas, equipe_b_rodadas,
                         fonte_grande, fonte_media, fonte_score, fonte_peq,
                         tempo, start_time):
    """Desenha o scoreboard final."""
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))

    # Vencedor
    if equipe_a_rodadas > equipe_b_rodadas:
        vencedor_txt = "EQUIPE A VENCEU!"
        vencedor_cor = COR_EQUIPE_A
    elif equipe_b_rodadas > equipe_a_rodadas:
        vencedor_txt = "EQUIPE B VENCEU!"
        vencedor_cor = COR_EQUIPE_B
    else:
        vencedor_txt = "EMPATE!"
        vencedor_cor = (200, 200, 200)

    titulo = fonte_grande.render(vencedor_txt, True, vencedor_cor)
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 30))

    # Placar rodadas
    placar = fonte_media.render(f"{equipe_a_rodadas} x {equipe_b_rodadas}", True, BRANCO)
    tela.blit(placar, (LARGURA // 2 - placar.get_width() // 2, 85))

    # Ranking por kills
    ranking = sorted(jogadores, key=lambda j: -j.kills)

    tempo_decorrido = tempo - start_time
    y_base = 130
    for rank, j in enumerate(ranking):
        delay = rank * 200
        if tempo_decorrido < delay:
            continue

        alpha = min(255, int((tempo_decorrido - delay) * 0.8))
        cor_eq = COR_EQUIPE_A if j.equipe == 0 else COR_EQUIPE_B

        # Fundo da linha
        linha_surf = pygame.Surface((400, 28), pygame.SRCALPHA)
        linha_surf.fill((20, 18, 32, alpha))
        lx = LARGURA // 2 - 200
        ly = y_base + rank * 32
        tela.blit(linha_surf, (lx, ly))

        # Borda equipe
        pygame.draw.rect(tela, cor_eq, (lx, ly, 4, 28))

        # Posicao
        pos_txt = fonte_peq.render(f"#{rank + 1}", True, (180, 180, 180))
        tela.blit(pos_txt, (lx + 12, ly + 6))

        # Cor do jogador
        pygame.draw.rect(tela, j.cor, (lx + 45, ly + 7, 14, 14), 0, 2)

        # Nome
        nome = fonte_peq.render(j.nome, True, BRANCO)
        tela.blit(nome, (lx + 68, ly + 6))

        # Kills
        kills_txt = fonte_peq.render(f"{j.kills} kills", True, (255, 200, 100))
        tela.blit(kills_txt, (lx + 330, ly + 6))


def _bot_ai_deadeye(bot, jogadores, tiros, particulas, flashes, tempo,
                     esperando_resultado):
    """IA do bot no Deadeye. Apenas movimentacao e mira - tiro e controlado no loop principal."""
    # Bots na zona de mortos: mira e movimentacao tratada aqui
    # Bots na arena: so se movem e desviam, tiro da deagle e controlado no main loop

    # Encontrar inimigo mais proximo
    melhor_alvo = None
    melhor_dist = float('inf')

    for j in jogadores:
        if j.equipe == bot.equipe or not j.vivo:
            continue
        # Bots na arena so miram em quem esta na arena
        if not bot.morto_zona and j.morto_zona:
            continue
        # Bots mortos so miram nos que estao na arena
        if bot.morto_zona and j.morto_zona:
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

    bot_cx = bot.x + TAM_JOGADOR // 2
    bot_cy = bot.y + TAM_JOGADOR // 2

    dx = melhor_alvo.x - bot.x
    dy = melhor_alvo.y - bot.y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1:
        dist = 1
    dir_x = dx / dist
    dir_y = dy / dist

    # Strafe
    if tempo > bot.bot_strafe_timer:
        bot.bot_strafe_timer = tempo + BOT_STRAFE_INTERVALO + random.randint(-300, 100)
        bot.bot_strafe_dir = -bot.bot_strafe_dir

    strafe_x = -dir_y * bot.bot_strafe_dir
    strafe_y = dir_x * bot.bot_strafe_dir

    # === DODGE: achar o tiro MAIS PERIGOSO (mais perto) e desviar dele ===
    melhor_tiro_dist = float('inf')
    dodge_perp_x, dodge_perp_y = 0.0, 0.0
    tiro_perigoso = False
    tiro_muito_perto = False

    for tiro in tiros:
        if not hasattr(tiro, 'dono') or tiro.dono is bot:
            continue
        if hasattr(tiro, 'dono') and tiro.dono and tiro.dono.equipe == bot.equipe:
            continue
        tx = bot_cx - tiro.x
        ty = bot_cy - tiro.y
        tdist = math.sqrt(tx * tx + ty * ty)
        if tdist > 350:
            continue
        dot = tiro.dx * tx + tiro.dy * ty
        if dot <= 0:
            continue
        perp_x = tx - tiro.dx * dot
        perp_y = ty - tiro.dy * dot
        perp_dist = math.sqrt(perp_x * perp_x + perp_y * perp_y)
        if perp_dist < TAM_JOGADOR + 40 and tdist < melhor_tiro_dist:
            melhor_tiro_dist = tdist
            tiro_perigoso = True
            if tdist < 100:
                tiro_muito_perto = True
            # Direcao perpendicular ao tiro (para onde desviar)
            if perp_dist > 1:
                dodge_perp_x = -perp_x / perp_dist
                dodge_perp_y = -perp_y / perp_dist
            else:
                # Tiro vindo direto: desviar pro lado do strafe atual
                dodge_perp_x = -tiro.dy * bot.bot_strafe_dir
                dodge_perp_y = tiro.dx * bot.bot_strafe_dir

    # Compor movimento final
    if tiro_perigoso:
        # Strafe forte + desvio do tiro mais perigoso na mesma direcao
        mover_x = strafe_x + dodge_perp_x * 2.0
        mover_y = strafe_y + dodge_perp_y * 2.0
    else:
        # Sem perigo: strafe normal
        mover_x = strafe_x
        mover_y = strafe_y

    # Ajuste de distancia
    if not bot.morto_zona:
        if dist < BOT_DIST_RECUAR:
            mover_x -= dir_x * 0.5
            mover_y -= dir_y * 0.5
        elif dist > BOT_DIST_AVANCAR:
            mover_x += dir_x * 0.4
            mover_y += dir_y * 0.4
        elif dist > BOT_DIST_IDEAL:
            mover_x += dir_x * 0.2
            mover_y += dir_y * 0.2

    mag = math.sqrt(mover_x * mover_x + mover_y * mover_y)
    if mag > 0:
        mover_x /= mag
        mover_y /= mag

    # Velocidade: boost ao desviar
    vel = VEL_DEADEYE * 1.6 if tiro_perigoso else VEL_DEADEYE
    bot.vx = mover_x * vel
    bot.vy = mover_y * vel

    # Mira
    imprecisao = min(dist / 600, 0.2)
    angulo_mira = math.atan2(dy, dx) + random.uniform(-imprecisao, imprecisao)
    bot.mira_x = bot_cx + math.cos(angulo_mira) * dist
    bot.mira_y = bot_cy + math.sin(angulo_mira) * dist

    # Dash - complemento ocasional da movimentacao
    if not bot.dash_ativo and not bot.morto_zona:
        usar_dash = False
        dash_dx, dash_dy = 0.0, 0.0
        if tiro_muito_perto and random.random() < 0.12:
            usar_dash = True
            dash_dx = dodge_perp_x
            dash_dy = dodge_perp_y
        elif dist < 60:
            usar_dash = True
            dash_dx = -dir_x
            dash_dy = -dir_y
        elif random.random() < 0.003:
            usar_dash = True
            dash_dx = -dir_y * bot.bot_strafe_dir
            dash_dy = dir_x * bot.bot_strafe_dir
        if usar_dash:
            bot.executar_dash(dash_dx, dash_dy)


# ============================================================
#  MAIN
# ============================================================

def executar_minigame_deadeye(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                               cliente, nome_jogador, customizacao):
    """Executa o minigame Deadeye."""
    print("[DEADEYE] Minigame Deadeye iniciado!")

    # Seed compartilhado
    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)

    # Limpar acoes pendentes
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

    # Fundo
    estrelas = criar_estrelas(120)

    # Mira
    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)

    # Criar jogadores (sempre 8)
    jogadores = []
    cor_local = customizacao.get('cor', AZUL)

    jogador_humano = JogadorDeadeye(nome_jogador, cor_local, is_bot=False)
    jogadores.append(jogador_humano)

    remotos = {}
    if cliente:
        remotos = cliente.get_remote_players()

    for pid, rp in remotos.items():
        ci = (pid - 1) % len(PALETA_CORES)
        jogadores.append(JogadorDeadeye(rp.name, PALETA_CORES[ci], is_bot=False, is_remote=True))

    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo", "Bot Foxtrot", "Bot Golf", "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        jogadores.append(JogadorDeadeye(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True))
        bot_idx += 1

    # Distribuir equipes aleatoriamente
    indices = list(range(8))
    random.shuffle(indices)
    for i, idx in enumerate(indices):
        jogadores[idx].equipe = 0 if i < 4 else 1
        # Cor do jogador = cor da equipe
        cor_eq = COR_EQUIPE_A if jogadores[idx].equipe == 0 else COR_EQUIPE_B
        jogadores[idx].cor = cor_eq
        jogadores[idx].cor_escura = tuple(max(0, c - 60) for c in cor_eq)
        jogadores[idx].cor_brilhante = tuple(min(255, c + 80) for c in cor_eq)

    # Estado
    estado = "INTRO"
    tempo_estado = pygame.time.get_ticks()
    rodada_atual = 0
    equipe_a_rodadas = 0
    equipe_b_rodadas = 0

    tiros = []
    particulas = []
    flashes = []

    alpha_fade = 255
    scoreboard_start = 0
    round_vencedor = -1

    # Sistema de turno da deagle
    portador_idx = -1     # indice do jogador que tem a deagle
    bala_deagle = None    # tiro ativo da deagle (None se ninguem atirou)
    esperando_resultado = False  # True enquanto a bala da deagle esta no ar

    def _dar_deagle_para(idx):
        """Da a deagle para o jogador no indice idx, tirando de todos os outros."""
        nonlocal portador_idx
        for i, j in enumerate(jogadores):
            if i == idx:
                j.dar_deagle()
            else:
                if j.tem_deagle:
                    j.tirar_deagle()
        portador_idx = idx

    def _proximo_portador(equipe_alvo):
        """Encontra um jogador vivo na arena da equipe_alvo para receber a deagle."""
        candidatos = [i for i, j in enumerate(jogadores)
                      if j.equipe == equipe_alvo and j.na_arena()]
        if candidatos:
            return random.choice(candidatos)
        return None

    def _iniciar_rodada():
        nonlocal tiros, particulas, flashes, portador_idx, bala_deagle, esperando_resultado
        tiros = []
        particulas = []
        flashes = []
        bala_deagle = None
        esperando_resultado = False
        # Spawn jogadores
        count_a = 0
        count_b = 0
        for j in jogadores:
            if j.equipe == 0:
                sx, sy = SPAWNS_A[count_a]
                j.reset_rodada(sx, sy)
                count_a += 1
            else:
                sx, sy = SPAWNS_B[count_b]
                j.reset_rodada(sx, sy)
                count_b += 1
        # Deagle para jogador aleatorio de equipe aleatoria
        equipe_inicial = random.randint(0, 1)
        idx = _proximo_portador(equipe_inicial)
        if idx is not None:
            _dar_deagle_para(idx)

    _iniciar_rodada()

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
                # Dash
                if ev.key == pygame.K_SPACE and estado == "FIGHT":
                    if jogador_humano.vivo and not jogador_humano.dash_ativo:
                        teclas = pygame.key.get_pressed()
                        ddx, ddy = 0.0, 0.0
                        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                            ddy -= 1
                        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                            ddy += 1
                        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                            ddx -= 1
                        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                            ddx += 1
                        if ddx == 0 and ddy == 0:
                            mx, my = jogador_humano.mira_x, jogador_humano.mira_y
                            cx, cy = jogador_humano.get_centro()
                            ddx = mx - cx
                            ddy = my - cy
                        jogador_humano.executar_dash(ddx, ddy)

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1 and estado == "FIGHT" and jogador_humano.vivo:
                    if jogador_humano.tem_deagle and not esperando_resultado:
                        # Jogador humano tem a deagle e pode atirar
                        _disparar_deadeye(jogador_humano, jogador_humano.mira_x,
                                          jogador_humano.mira_y, tiros, particulas, flashes)
                        # Marcar a bala como deagle bullet
                        if tiros:
                            bala_deagle = tiros[-1]
                            bala_deagle.is_deagle = True
                            esperando_resultado = True
                    elif jogador_humano.morto_zona:
                        # Na zona de mortos, tiro normal livre
                        _disparar_deadeye(jogador_humano, jogador_humano.mira_x,
                                          jogador_humano.mira_y, tiros, particulas, flashes)

        # ========== LOGICA DE ESTADO ==========
        if estado == "INTRO":
            if tempo_no_estado < 500:
                alpha_fade = int(255 * (1 - tempo_no_estado / 500))
            else:
                alpha_fade = 0
            if tempo_no_estado >= TEMPO_INTRO:
                estado = "TEAM_SHOW"
                tempo_estado = tempo

        elif estado == "TEAM_SHOW":
            if tempo_no_estado >= TEMPO_TEAM_SHOW:
                estado = "COUNTDOWN"
                tempo_estado = tempo

        elif estado == "COUNTDOWN":
            if tempo_no_estado >= TEMPO_COUNTDOWN:
                estado = "FIGHT"
                tempo_estado = tempo

        elif estado == "FIGHT":
            # Movimento do jogador humano
            if jogador_humano.vivo and not jogador_humano.dash_ativo:
                teclas = pygame.key.get_pressed()
                vx, vy = 0.0, 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                    vy -= VEL_DEADEYE
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                    vy += VEL_DEADEYE
                if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                    vx -= VEL_DEADEYE
                if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                    vx += VEL_DEADEYE
                if vx != 0 and vy != 0:
                    vx *= 0.7071
                    vy *= 0.7071
                jogador_humano.vx = vx
                jogador_humano.vy = vy

            # Mira do jogador humano
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            jogador_humano.mira_x = mouse_pos[0]
            jogador_humano.mira_y = mouse_pos[1]

            # Atualizar posicoes de todos
            for j in jogadores:
                if j.vivo and not j.dash_ativo:
                    j.x += j.vx
                    j.y += j.vy
                    j._clampar_posicao()
                j.atualizar_dash()

            # Bot AI
            for j in jogadores:
                if j.is_bot and j.vivo:
                    _bot_ai_deadeye(j, jogadores, tiros, particulas, flashes, tempo,
                                    esperando_resultado)

            # Bot com deagle: atirar apos delay
            if portador_idx >= 0 and not esperando_resultado:
                portador = jogadores[portador_idx]
                if portador.is_bot and portador.vivo and portador.tem_deagle:
                    if tempo >= portador.bot_next_shot:
                        _disparar_deadeye(portador, portador.mira_x, portador.mira_y,
                                          tiros, particulas, flashes)
                        if tiros:
                            bala_deagle = tiros[-1]
                            bala_deagle.is_deagle = True
                            esperando_resultado = True

            # Bots na zona de mortos: atiram livremente com tiro normal
            for j in jogadores:
                if j.is_bot and j.morto_zona and j.vivo:
                    if tempo >= j.bot_next_shot:
                        _disparar_deadeye(j, j.mira_x, j.mira_y, tiros, particulas, flashes)
                        j.bot_next_shot = tempo + random.randint(500, 800)

            # Rede
            if cliente and jogador_humano.vivo:
                cliente.send_minigame_action({
                    'action': 'deadeye_input',
                    'x': jogador_humano.x, 'y': jogador_humano.y,
                    'mx': jogador_humano.mira_x, 'my': jogador_humano.mira_y,
                })

            # Processar acoes remotas
            if cliente:
                acoes = cliente.get_minigame_actions()
                for acao in acoes:
                    act = acao.get('action', '')
                    if act == 'deadeye_input':
                        for j in jogadores:
                            if j.is_remote and j.vivo:
                                j.x = acao.get('x', j.x)
                                j.y = acao.get('y', j.y)
                                j.mira_x = acao.get('mx', j.mira_x)
                                j.mira_y = acao.get('my', j.mira_y)
                    elif act == 'deadeye_shot':
                        for j in jogadores:
                            if j.is_remote and j.vivo and j.tem_deagle:
                                _disparar_deadeye(j, j.mira_x, j.mira_y,
                                                  tiros, particulas, flashes)
                                if tiros:
                                    bala_deagle = tiros[-1]
                                    bala_deagle.is_deagle = True
                                    esperando_resultado = True

            # Atualizar tiros
            tiros_remover = []
            deagle_acertou = False
            deagle_errou = False

            for tiro in tiros:
                tiro.atualizar()
                is_deagle_bullet = getattr(tiro, 'is_deagle', False)

                # Remover se fora da area total
                if (tiro.x < AREA_TOTAL.left - 20 or tiro.x > AREA_TOTAL.right + 20 or
                        tiro.y < AREA_TOTAL.top - 20 or tiro.y > AREA_TOTAL.bottom + 20):
                    tiros_remover.append(tiro)
                    if is_deagle_bullet and tiro is bala_deagle:
                        deagle_errou = True
                    continue

                # Tiros de jogadores eliminados desaparecem na area da propria equipe
                if hasattr(tiro, 'dono') and tiro.dono and tiro.dono.morto_zona:
                    if tiro.dono.equipe == 0 and tiro.x < LINHA_X:
                        tiros_remover.append(tiro)
                        continue
                    elif tiro.dono.equipe == 1 and tiro.x > LINHA_X:
                        tiros_remover.append(tiro)
                        continue

                # Colisao com jogadores
                for j in jogadores:
                    if not j.vivo:
                        continue
                    if hasattr(tiro, 'dono') and tiro.dono is j:
                        continue
                    if hasattr(tiro, 'dono') and tiro.dono and tiro.dono.equipe == j.equipe:
                        continue
                    if j.morto_zona:
                        continue
                    if tempo < j.invulneravel_ate:
                        continue

                    jrect = j.get_rect()
                    if jrect.collidepoint(int(tiro.x), int(tiro.y)):
                        j.hp -= tiro.dano
                        j.invulneravel_ate = tempo + 300
                        tiros_remover.append(tiro)

                        # Atribuir kill
                        if hasattr(tiro, 'dono') and tiro.dono:
                            if j.hp <= 0:
                                tiro.dono.kills += 1

                        # Se era a bala da deagle: acertou!
                        if is_deagle_bullet and tiro is bala_deagle:
                            deagle_acertou = True

                        # Efeito de dano
                        cx, cy = j.get_centro()
                        for _ in range(8):
                            p = Particula(cx + random.uniform(-8, 8),
                                          cy + random.uniform(-8, 8),
                                          (255, random.randint(100, 200), 0))
                            p.velocidade_x = random.uniform(-4, 4)
                            p.velocidade_y = random.uniform(-4, 4)
                            p.vida = random.randint(8, 15)
                            p.tamanho = random.uniform(2, 4)
                            particulas.append(p)

                        if j.hp <= 0:
                            for _ in range(20):
                                p = Particula(cx + random.uniform(-12, 12),
                                              cy + random.uniform(-12, 12),
                                              j.cor)
                                p.velocidade_x = random.uniform(-5, 5)
                                p.velocidade_y = random.uniform(-5, 5)
                                p.vida = random.randint(15, 30)
                                p.tamanho = random.uniform(3, 6)
                                particulas.append(p)
                            flashes.append({
                                'x': cx, 'y': cy,
                                'raio': 25, 'vida': 10,
                                'cor': (255, 200, 100)
                            })
                            j.ir_zona_mortos()
                        break

            for t in tiros_remover:
                if t in tiros:
                    tiros.remove(t)

            # === TURNO DA DEAGLE ===
            if deagle_acertou:
                # Acertou! Portador atual mantem a deagle
                bala_deagle = None
                esperando_resultado = False
                # Se o portador morreu (foi pra zona), passa pro outro time
                if portador_idx >= 0 and jogadores[portador_idx].morto_zona:
                    outra_equipe = 1 - jogadores[portador_idx].equipe
                    novo = _proximo_portador(outra_equipe)
                    if novo is not None:
                        _dar_deagle_para(novo)
                        jogadores[novo].bot_next_shot = tempo + random.randint(800, 1500)
                else:
                    # Portador continua, reseta cooldown do bot
                    if portador_idx >= 0 and jogadores[portador_idx].is_bot:
                        jogadores[portador_idx].bot_next_shot = tempo + random.randint(800, 1500)

            elif deagle_errou:
                # Errou! Passa a deagle para alguem da outra equipe
                bala_deagle = None
                esperando_resultado = False
                if portador_idx >= 0:
                    equipe_atual = jogadores[portador_idx].equipe
                    jogadores[portador_idx].tirar_deagle()
                    outra_equipe = 1 - equipe_atual
                    novo = _proximo_portador(outra_equipe)
                    if novo is None:
                        # Outro time nao tem ninguem na arena, tenta o mesmo time
                        novo = _proximo_portador(equipe_atual)
                    if novo is not None:
                        _dar_deagle_para(novo)
                        jogadores[novo].bot_next_shot = tempo + random.randint(800, 1500)

            # Se o portador morreu (levou tiro normal de morto), passar deagle
            if portador_idx >= 0 and jogadores[portador_idx].morto_zona and not esperando_resultado:
                equipe_portador = jogadores[portador_idx].equipe
                jogadores[portador_idx].tirar_deagle()
                outra_equipe = 1 - equipe_portador
                novo = _proximo_portador(outra_equipe)
                if novo is None:
                    novo = _proximo_portador(equipe_portador)
                if novo is not None:
                    _dar_deagle_para(novo)
                    jogadores[novo].bot_next_shot = tempo + random.randint(800, 1500)

            # Verificar condicao de vitoria
            vivos_a = sum(1 for j in jogadores if j.equipe == 0 and j.na_arena())
            vivos_b = sum(1 for j in jogadores if j.equipe == 1 and j.na_arena())

            if vivos_a == 0 or vivos_b == 0:
                estado = "ROUND_END"
                tempo_estado = tempo
                rodada_atual += 1
                if vivos_a == 0:
                    round_vencedor = 1
                    equipe_b_rodadas += 1
                else:
                    round_vencedor = 0
                    equipe_a_rodadas += 1

        elif estado == "ROUND_END":
            if tempo_no_estado >= TEMPO_ROUND_END:
                # Verificar se alguem venceu o jogo
                if equipe_a_rodadas >= 2 or equipe_b_rodadas >= 2 or rodada_atual >= NUM_RODADAS:
                    estado = "SCOREBOARD"
                    tempo_estado = tempo
                    scoreboard_start = tempo
                else:
                    estado = "COUNTDOWN"
                    tempo_estado = tempo
                    _iniciar_rodada()

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                pygame.mouse.set_visible(True)
                return None

        # ========== ATUALIZAR PARTICULAS E FLASHES ==========
        for p in particulas[:]:
            p.atualizar()
            if p.vida <= 0:
                particulas.remove(p)

        for f in flashes[:]:
            f['vida'] -= 1
            if f['vida'] <= 0:
                flashes.remove(f)

        # ========== DESENHO ==========
        tela.fill((4, 2, 12))
        tela.blit(gradiente_jogo, (0, 0))
        desenhar_estrelas(tela, estrelas)

        # Arena
        _desenhar_arena(tela, tempo)

        # Jogadores
        for j in jogadores:
            j.desenhar(tela, fonte_nomes, show_hp=(estado == "FIGHT"))

        # Armas (Desert Eagle visual) + indicador do portador
        if estado == "FIGHT":
            for j in jogadores:
                if j.vivo and j.tem_deagle:
                    _desenhar_arma_jogador(tela, j, tempo)
                    _desenhar_portador_indicador(tela, j, fonte_peq, tempo)

        # Tiros
        for tiro in tiros:
            tiro.desenhar(tela)

        # Particulas
        for p in particulas:
            p.desenhar(tela)

        # Flashes
        for f in flashes:
            alpha_f = int(255 * (f['vida'] / 10))
            flash_surf = pygame.Surface((f['raio'] * 2, f['raio'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (*f['cor'], alpha_f), (f['raio'], f['raio']), f['raio'])
            tela.blit(flash_surf, (int(f['x']) - f['raio'], int(f['y']) - f['raio']))

        # Mira
        if estado == "FIGHT":
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            desenhar_mira(tela, mouse_pos, (mira_surface, mira_rect))

        # HUD
        _desenhar_hud(tela, jogadores, jogador_humano, equipe_a_rodadas, equipe_b_rodadas,
                      fonte_hud, fonte_peq, estado, esperando_resultado)

        # TEAM_SHOW
        if estado == "TEAM_SHOW":
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            tela.blit(overlay, (0, 0))

            titulo = fonte_grande.render("EQUIPES", True, (255, 220, 100))
            tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 40))

            # Equipe A
            eq_a_titulo = fonte_media.render("EQUIPE A", True, COR_EQUIPE_A)
            tela.blit(eq_a_titulo, (LARGURA // 4 - eq_a_titulo.get_width() // 2, 100))
            y_a = 140
            for j in jogadores:
                if j.equipe == 0:
                    pygame.draw.rect(tela, j.cor, (LARGURA // 4 - 50, y_a, 20, 20), 0, 3)
                    nome_s = fonte_hud.render(j.nome, True, BRANCO)
                    tela.blit(nome_s, (LARGURA // 4 - 22, y_a + 1))
                    y_a += 30

            # Equipe B
            eq_b_titulo = fonte_media.render("EQUIPE B", True, COR_EQUIPE_B)
            tela.blit(eq_b_titulo, (3 * LARGURA // 4 - eq_b_titulo.get_width() // 2, 100))
            y_b = 140
            for j in jogadores:
                if j.equipe == 1:
                    pygame.draw.rect(tela, j.cor, (3 * LARGURA // 4 - 50, y_b, 20, 20), 0, 3)
                    nome_s = fonte_hud.render(j.nome, True, BRANCO)
                    tela.blit(nome_s, (3 * LARGURA // 4 - 22, y_b + 1))
                    y_b += 30

            # VS
            vs_txt = fonte_grande.render("VS", True, (200, 200, 200))
            tela.blit(vs_txt, (LARGURA // 2 - vs_txt.get_width() // 2, 160))

        # COUNTDOWN
        if estado == "COUNTDOWN":
            segundos = 3 - tempo_no_estado // 1000
            if segundos > 0:
                cd_txt = fonte_countdown.render(str(segundos), True, BRANCO)
                tela.blit(cd_txt, (LARGURA // 2 - cd_txt.get_width() // 2,
                                   ALTURA_JOGO // 2 - cd_txt.get_height() // 2))
            else:
                go_txt = fonte_countdown.render("FIGHT!", True, (255, 50, 50))
                tela.blit(go_txt, (LARGURA // 2 - go_txt.get_width() // 2,
                                   ALTURA_JOGO // 2 - go_txt.get_height() // 2))

        # ROUND_END
        if estado == "ROUND_END":
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            tela.blit(overlay, (0, 0))

            if round_vencedor == 0:
                msg = "EQUIPE A VENCEU A RODADA!"
                cor_msg = COR_EQUIPE_A
            else:
                msg = "EQUIPE B VENCEU A RODADA!"
                cor_msg = COR_EQUIPE_B

            msg_surf = fonte_grande.render(msg, True, cor_msg)
            tela.blit(msg_surf, (LARGURA // 2 - msg_surf.get_width() // 2,
                                 ALTURA_JOGO // 2 - msg_surf.get_height() // 2))

            placar_txt = fonte_media.render(f"{equipe_a_rodadas} x {equipe_b_rodadas}", True, BRANCO)
            tela.blit(placar_txt, (LARGURA // 2 - placar_txt.get_width() // 2,
                                   ALTURA_JOGO // 2 + 40))

        # SCOREBOARD
        if estado == "SCOREBOARD":
            _desenhar_scoreboard(tela, jogadores, equipe_a_rodadas, equipe_b_rodadas,
                                fonte_grande, fonte_media, fonte_score, fonte_peq,
                                tempo, scoreboard_start)

        # INTRO fade
        if estado == "INTRO":
            # Titulo
            if tempo_no_estado > 300:
                titulo = fonte_grande.render("DEADEYE", True, (255, 220, 100))
                tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2,
                                   ALTURA_JOGO // 2 - titulo.get_height() // 2))
                sub = fonte_media.render("4 vs 4 - Desert Eagle", True, (200, 180, 130))
                tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2,
                                ALTURA_JOGO // 2 + 30))

            if alpha_fade > 0:
                fade_surf = pygame.Surface((LARGURA, ALTURA_JOGO))
                fade_surf.fill((0, 0, 0))
                fade_surf.set_alpha(alpha_fade)
                tela.blit(fade_surf, (0, 0))

        # Barra inferior
        pygame.draw.rect(tela, (10, 8, 20), (0, ALTURA_JOGO, LARGURA, ALTURA - ALTURA_JOGO))

        present_frame()
        relogio.tick(FPS)
