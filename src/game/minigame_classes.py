#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Batalha de Classes - Free-for-all (todos contra todos) numa arena grande.
8 jogadores (humanos + bots). Cada jogador recebe uma CLASSE DIFERENTE (sem
repetir: 8 classes para 8 jogadores). A classe define o visual e o ataque/habilidade.

Arena grande com camera + minimap (estilo Sabers, visual diferente). Ultimo
sobrevivente vence a rodada. Melhor de 3 rodadas.

Modelo host-autoritativo: só o host simula (bots, balas, dano, mortes, rodadas)
e transmite o estado; os clientes renderizam e mandam só o próprio input.

Classes e habilidades:
  - player   (Dash)        : tiro basico. HABILIDADE: dash (só ele tem dash).
  - ciano    (Veloz)       : velocidade muito alta (passiva). Tiros rapidos.
  - metralha (Metralhadora): empunha a metralhadora, rajada rapida de tiros.
  - mago     (Mago)        : cajado + chapeu, tiros em leque. HABILIDADE: escudo.
  - explosive(Explosivo)   : HABILIDADE: explosao em area (particulas p/ todo lado).
  - roxo     (Roxo)        : mais vida que os outros. Tiros fortes.
  - fantasma (Fantasma)    : HABILIDADE: ficar invisivel por um tempo.
  - granada  (Granada)     : arremessa granadas que explodem em area.
"""

import pygame
import math
import random
from src.config import *
from src.entities.tiro import Tiro
from src.entities.particula import Particula, criar_explosao
from src.utils.visual import criar_mira, desenhar_mira
from src.utils.display_manager import present_frame, convert_mouse_position
from src.entities.inimigo_metralhadora import InimigoMetralhadora
from src.entities.inimigo_mago import InimigoMago
from src.entities.inimigo_granada import InimigoGranada
from src.entities.inimigo_fantasma import InimigoFantasma
from src.network.multiplayer_utils import ordenar_humanos, sou_host

# Classes cujo visual é IDÊNTICO ao do inimigo correspondente do jogo base.
# (classe_id -> (Classe do inimigo, método que desenha o equipamento na mão))
_ENEMY_VISUAL = {
    'metralha': (InimigoMetralhadora, 'desenhar_metralhadora_inimigo'),
    'mago':     (InimigoMago, 'desenhar_cajado'),
    'granada':  (InimigoGranada, 'desenhar_equipamento_granada'),
    'fantasma': (InimigoFantasma, None),
}

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
HP_PADRAO = 4
NUM_RODADAS = 3

PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Arena grande (maior que a tela) - bem espaçosa para os players spawnarem longe
ARENA_W = 3800
ARENA_H = 2600
ARENA_RECT = pygame.Rect(0, 0, ARENA_W, ARENA_H)

# Spawn points em circulo ao redor do centro (raio grande = players distantes)
SPAWN_RAIO = 1150
SPAWN_POINTS = []
for _i in range(8):
    _ang = (2 * math.pi * _i) / 8
    _sx = ARENA_W // 2 + int(math.cos(_ang) * SPAWN_RAIO) - TAM_JOGADOR // 2
    _sy = ARENA_H // 2 + int(math.sin(_ang) * SPAWN_RAIO) - TAM_JOGADOR // 2
    SPAWN_POINTS.append((_sx, _sy))

# Tempos de estado (ms)
TEMPO_INTRO = 4200      # inclui a roleta de classes
TEMPO_COUNTDOWN = 3000
TEMPO_ROUND_END = 2500
TEMPO_SCOREBOARD = 5000

# Dash (só a classe player)
DASH_VELOCIDADE = 25
DASH_DURACAO = 8
DASH_COOLDOWN = 500
DASH_INVULN_POS = 200

# Habilidades ativas (SPACE)
SPECIAL_COOLDOWN = 3500
SHIELD_DURACAO = 1500     # mago
INVISIVEL_DURACAO = 2600  # fantasma
EXPLOSAO_RAIO = 130       # explosivo
EXPLOSAO_DANO = 2
VELOZ_MULT = 2.1          # multiplicador de velocidade do surto (ciano)
VELOZ_DURACAO = 1800      # ms do surto de velocidade

# Bot AI
BOT_STRAFE_INTERVALO = 800
BOT_DIST_IDEAL = 240
BOT_DIST_RECUAR = 120
BOT_DIST_AVANCAR = 420

# Balas
BALA_VIDA_MAX = 200   # frames antes de sumir (segurança)
BALA_ALCANCE = 620    # distância máxima percorrida antes de sumir

# Minimap
MINIMAP_W = 170
MINIMAP_H = int(MINIMAP_W * ARENA_H / ARENA_W)
MINIMAP_X = LARGURA - MINIMAP_W - 12
MINIMAP_Y = 12

# ============================================================
#  DEFINICAO DAS CLASSES
# ============================================================
# hp, cd (cooldown de tiro), dano, vbala, raio, spread, vel, special, explode
# cor_bala: cor das balas (None = usa a cor da classe). O mago atira bola de fogo.
CLASSES = [
    {'id': 'player',    'nome': 'Dash',         'cor': AZUL,           'hp': 4, 'vel': 3.9, 'cd': 340, 'dano': 1, 'vbala': 13, 'raio': 4, 'spread': 1, 'special': 'dash',     'explode': 0, 'cor_bala': None},
    {'id': 'ciano',     'nome': 'Veloz',        'cor': CIANO,          'hp': 3, 'vel': 6.8, 'cd': 300, 'dano': 1, 'vbala': 16, 'raio': 3, 'spread': 1, 'special': 'velocidade', 'explode': 0, 'cor_bala': None},
    {'id': 'metralha',  'nome': 'Metralhadora', 'cor': (190, 190, 195),'hp': 4, 'vel': 3.4, 'cd': 200, 'dano': 1, 'vbala': 15, 'raio': 3, 'spread': 1, 'special': None,       'explode': 0, 'cor_bala': None},
    {'id': 'mago',      'nome': 'Mago',         'cor': (150, 80, 220), 'hp': 4, 'vel': 3.3, 'cd': 560, 'dano': 1, 'vbala': 10, 'raio': 8, 'spread': 3, 'special': 'shield',   'explode': 0, 'cor_bala': (255, 100, 0)},
    {'id': 'explosive', 'nome': 'Explosivo',    'cor': (255, 140, 40), 'hp': 4, 'vel': 3.4, 'cd': 430, 'dano': 1, 'vbala': 12, 'raio': 5, 'spread': 1, 'special': 'explosao', 'explode': 0, 'cor_bala': None},
    {'id': 'roxo',      'nome': 'Roxo',         'cor': ROXO,           'hp': 7, 'vel': 3.5, 'cd': 460, 'dano': 2, 'vbala': 12, 'raio': 5, 'spread': 1, 'special': None,       'explode': 0, 'cor_bala': None},
    {'id': 'fantasma',  'nome': 'Fantasma',     'cor': (215, 215, 240),'hp': 4, 'vel': 3.8, 'cd': 360, 'dano': 1, 'vbala': 12, 'raio': 4, 'spread': 2, 'special': 'invisivel','explode': 0, 'cor_bala': None},
    {'id': 'granada',   'nome': 'Granada',      'cor': (80, 165, 70),  'hp': 4, 'vel': 3.2, 'cd': 850, 'dano': 2, 'vbala': 8,  'raio': 7, 'spread': 1, 'special': None,       'explode': 0, 'cor_bala': None},
]


# ============================================================
#  VISUAL DAS CLASSES
# ============================================================

def _marcador_classe(surf, ox, oy, tam, classe_id, cor, tempo):
    """Detalhes visuais fixos da classe sobre o quadrado (chapeu, olhos, etc.)."""
    cx = ox + tam // 2
    cor_clara = tuple(min(255, c + 90) for c in cor)
    cor_escura = tuple(max(0, c - 70) for c in cor)

    if classe_id == 'ciano':
        for i in range(3):
            ly = oy + 6 + i * 8
            pygame.draw.line(surf, cor_clara, (ox - 8 - i * 3, ly), (ox - 1, ly), 2)
    elif classe_id == 'mago':
        # Chapeu de mago (pontudo com estrela)
        pygame.draw.polygon(surf, (60, 40, 120), [(cx - 11, oy), (cx + 11, oy), (cx, oy - 20)])
        pygame.draw.circle(surf, (255, 230, 120), (cx, oy - 20), 3)
        pygame.draw.circle(surf, (255, 255, 180), (ox + 9, oy + 15), 2)
        pygame.draw.circle(surf, (255, 255, 180), (ox + tam - 9, oy + 15), 2)
    elif classe_id == 'explosive':
        pygame.draw.rect(surf, (120, 40, 20), (ox + 3, oy + tam // 2 - 3, tam - 6, 6))
        cor_faisca = (255, 220, 80) if (tempo // 120) % 2 == 0 else (255, 140, 40)
        pygame.draw.line(surf, (60, 50, 40), (cx, oy), (cx + 4, oy - 8), 2)
        pygame.draw.circle(surf, cor_faisca, (cx + 4, oy - 9), 2)
    elif classe_id == 'roxo':
        pygame.draw.line(surf, cor_escura, (ox + 6, oy + 10), (ox + 13, oy + 14), 3)
        pygame.draw.line(surf, cor_escura, (ox + tam - 6, oy + 10), (ox + tam - 13, oy + 14), 3)
        pygame.draw.circle(surf, (255, 80, 255), (ox + 10, oy + 17), 2)
        pygame.draw.circle(surf, (255, 80, 255), (ox + tam - 10, oy + 17), 2)
    elif classe_id == 'fantasma':
        pygame.draw.circle(surf, (40, 40, 60), (ox + 9, oy + 13), 3)
        pygame.draw.circle(surf, (40, 40, 60), (ox + tam - 9, oy + 13), 3)


# ============================================================
#  CLASSE DO JOGADOR
# ============================================================

class _AlvoMira:
    """Objeto mínimo usado como 'jogador alvo' para as funções de mira dos
    inimigos (elas leem apenas x, y, tamanho)."""
    __slots__ = ('x', 'y', 'tamanho')

    def __init__(self, cx, cy):
        self.tamanho = TAM_JOGADOR
        self.x = cx - TAM_JOGADOR // 2
        self.y = cy - TAM_JOGADOR // 2


class JogadorClasse:
    """Jogador (humano/bot) no free-for-all de classes."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor_pessoal = cor       # cor de identificação (borda + minimap)
        self.is_bot = is_bot
        self.is_remote = is_remote
        self.player_id = None
        self.hp_max = HP_PADRAO
        self.hp = HP_PADRAO
        self.vivo = True
        self.kills = 0
        self.rodadas_vencidas = 0

        # Classe
        self.classe_idx = 0
        self.classe_id = 'player'
        self.cor = cor
        self.vel = 3.9
        self.cd = 340
        self.dano = 1
        self.vbala = 13
        self.raio = 4
        self.spread = 1
        self.special = 'dash'
        self.explode = 0
        self.cor_bala = None

        # Visual de inimigo (metralha/mago/granada/fantasma). None = quadrado padrão.
        self._enemy = None
        self._enemy_equip = None

        # Posicao (mundo)
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.mira_x = 0.0
        self.mira_y = 0.0

        self.tempo_ultimo_tiro = 0
        self.invulneravel_ate = 0

        self._atualizar_cores()

        # Dash
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_direcao = (0.0, 0.0)
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0

        # Habilidades
        self.special_cooldown = -999999
        self.shield_ate = 0
        self.invisivel_ate = 0
        self.boost_ate = 0

        # Bot AI
        self.bot_alvo = None
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_strafe_dir = 1
        self.bot_next_special = 0

    def _atualizar_cores(self):
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

    def aplicar_classe(self, idx):
        idx = idx % len(CLASSES)
        c = CLASSES[idx]
        self.classe_idx = idx
        self.classe_id = c['id']
        self.cor = c['cor']
        self.hp_max = c['hp']
        self.hp = c['hp']
        self.vel = c['vel']
        self.cd = c['cd']
        self.dano = c['dano']
        self.vbala = c['vbala']
        self.raio = c['raio']
        self.spread = c['spread']
        self.special = c['special']
        self.explode = c['explode']
        self.cor_bala = c.get('cor_bala')
        self._atualizar_cores()
        # Visual de inimigo (se a classe usar)
        info = _ENEMY_VISUAL.get(self.classe_id)
        if info:
            enemy_cls, equip = info
            self._enemy = enemy_cls(0, 0)
            self._enemy_equip = equip
        else:
            self._enemy = None
            self._enemy_equip = None

    def reset_rodada(self, spawn_x, spawn_y):
        self.hp = self.hp_max
        self.vivo = True
        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.vx = 0.0
        self.vy = 0.0
        self.tempo_ultimo_tiro = 0
        self.invulneravel_ate = 0
        self.dash_ativo = False
        self.dash_frames_restantes = 0
        self.dash_tempo_cooldown = 0
        self.dash_tempo_fim = 0
        self.special_cooldown = -999999
        self.shield_ate = 0
        self.invisivel_ate = 0
        self.boost_ate = 0
        self.bot_next_shot = 0
        self.bot_strafe_timer = 0
        self.bot_next_special = 0

    def special_pronto(self):
        return pygame.time.get_ticks() - self.special_cooldown >= SPECIAL_COOLDOWN

    def vel_efetiva(self):
        """Velocidade atual (com o surto do Veloz, se ativo)."""
        if pygame.time.get_ticks() < self.boost_ate:
            return self.vel * VELOZ_MULT
        return self.vel

    # ---- Dash (player) ----
    def executar_dash(self, dx, dy):
        tempo = pygame.time.get_ticks()
        if self.dash_ativo or self.special != 'dash':
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

    # ---- Escudo (mago) ----
    def ativar_shield(self):
        tempo = pygame.time.get_ticks()
        if self.special != 'shield' or not self.special_pronto():
            return False
        self.shield_ate = tempo + SHIELD_DURACAO
        self.invulneravel_ate = tempo + SHIELD_DURACAO
        self.special_cooldown = tempo
        return True

    # ---- Invisibilidade (fantasma) ----
    def ficar_invisivel(self):
        tempo = pygame.time.get_ticks()
        if self.special != 'invisivel' or not self.special_pronto():
            return False
        self.invisivel_ate = tempo + INVISIVEL_DURACAO
        self.special_cooldown = tempo
        return True

    # ---- Explosao (explosivo) ----
    def preparar_explosao(self):
        if self.special != 'explosao' or not self.special_pronto():
            return False
        self.special_cooldown = pygame.time.get_ticks()
        return True

    # ---- Surto de velocidade (veloz) ----
    def ativar_boost(self):
        tempo = pygame.time.get_ticks()
        if self.special != 'velocidade' or not self.special_pronto():
            return False
        self.boost_ate = tempo + VELOZ_DURACAO
        self.special_cooldown = tempo
        return True

    def usar_special(self, dx, dy):
        """Ativa a habilidade da classe. Retorna o 'tipo' usado ou None."""
        if self.special == 'dash':
            return 'dash' if self.executar_dash(dx, dy) else None
        elif self.special == 'shield':
            return 'shield' if self.ativar_shield() else None
        elif self.special == 'invisivel':
            return 'invisivel' if self.ficar_invisivel() else None
        elif self.special == 'explosao':
            return 'explosao' if self.preparar_explosao() else None
        elif self.special == 'velocidade':
            return 'velocidade' if self.ativar_boost() else None
        return None

    def esta_invisivel(self):
        return pygame.time.get_ticks() < self.invisivel_ate

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), TAM_JOGADOR, TAM_JOGADOR)

    def get_centro(self):
        return (self.x + TAM_JOGADOR // 2, self.y + TAM_JOGADOR // 2)

    def _render_corpo(self, target, ox, oy, tam, tempo, eh_local):
        pygame.draw.rect(target, (15, 12, 20), (ox + 3, oy + 3, tam, tam), 0, 3)
        pygame.draw.rect(target, self.cor_escura, (ox, oy, tam, tam), 0, 5)
        pygame.draw.rect(target, self.cor, (ox + 2, oy + 2, tam - 4, tam - 4), 0, 3)
        pygame.draw.rect(target, self.cor_brilhante, (ox + 4, oy + 4, 7, 7), 0, 2)
        cor_id = BRANCO if eh_local else self.cor_pessoal
        pygame.draw.rect(target, cor_id, (ox, oy, tam, tam), 2, 5)
        _marcador_classe(target, ox, oy, tam, self.classe_id, self.cor, tempo)

    def _render_enemy(self, tela, sx, sy, tempo, mira_screen, alpha_e):
        """Delega o desenho ao visual do inimigo correspondente (metralha/mago/etc.)."""
        e = self._enemy
        e.x = sx
        e.y = sy
        e.tamanho = TAM_JOGADOR
        for a, v in (('esta_recarregando', False), ('escudo_ativo', False),
                     ('esta_invocando', False), ('esta_visivel', True),
                     ('cajado_visivel', True)):
            if hasattr(e, a):
                setattr(e, a, v)
        if hasattr(e, 'alpha_atual'):
            e.alpha_atual = alpha_e
        if hasattr(e, 'tempo_criacao'):
            e.tempo_criacao = tempo - 5000
        if hasattr(e, 'tempo_ultimo_lancamento'):
            e.tempo_ultimo_lancamento = tempo - 100000
        try:
            e.desenhar(tela, tempo)
            if self._enemy_equip:
                alvo = _AlvoMira(mira_screen[0], mira_screen[1])
                getattr(e, self._enemy_equip)(tela, tempo, alvo)
        except Exception:
            # Fallback: quadrado padrão se algo no visual do inimigo falhar
            self._render_corpo(tela, sx, sy, TAM_JOGADOR, tempo, False)

    def desenhar(self, tela, fonte, cam_x, cam_y, eh_local=False, show_hp=True):
        if not self.vivo:
            return
        tam = TAM_JOGADOR
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if sx < -tam - 40 or sx > LARGURA + tam or sy < -tam - 40 or sy > ALTURA_JOGO + tam:
            return

        tempo = pygame.time.get_ticks()
        invisivel = tempo < self.invisivel_ate

        # Invisivel: some para os outros; o dono se ve translucido
        if invisivel and not eh_local:
            return

        if not invisivel and tempo < self.invulneravel_ate and self.shield_ate <= tempo and (tempo // 80) % 2 == 0:
            return

        alpha = 70 if invisivel else 255
        if self._enemy is not None:
            # Visual idêntico ao inimigo correspondente (metralha/mago/granada/fantasma)
            mira_screen = (self.mira_x - cam_x, self.mira_y - cam_y)
            self._render_enemy(tela, sx, sy, tempo, mira_screen, alpha)
        elif alpha < 255:
            pad = 22
            temp = pygame.Surface((tam + pad * 2, tam + pad * 2), pygame.SRCALPHA)
            self._render_corpo(temp, pad, pad, tam, tempo, eh_local)
            temp.set_alpha(alpha)
            tela.blit(temp, (sx - pad, sy - pad))
        else:
            self._render_corpo(tela, sx, sy, tam, tempo, eh_local)

        # Escudo (mago)
        if tempo < self.shield_ate:
            pulso = 4 + int(3 * math.sin(tempo / 120))
            r = tam // 2 + 10 + pulso
            shield_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (120, 180, 255, 70), (r, r), r)
            pygame.draw.circle(shield_surf, (180, 220, 255, 160), (r, r), r, 2)
            tela.blit(shield_surf, (sx + tam // 2 - r, sy + tam // 2 - r))

        # Surto de velocidade (veloz): aura ciano + linhas de velocidade
        if tempo < self.boost_ate:
            ccx = sx + tam // 2
            ccy = sy + tam // 2
            r = tam // 2 + 6 + int(3 * math.sin(tempo / 80))
            aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (60, 255, 255, 90), (r, r), r, 3)
            tela.blit(aura, (ccx - r, ccy - r))
            mag = math.sqrt(self.vx * self.vx + self.vy * self.vy)
            if mag > 0.1:
                bdx, bdy = self.vx / mag, self.vy / mag
                for k in range(3):
                    off = 8 + k * 8
                    lx = ccx - bdx * off
                    ly = ccy - bdy * off
                    pygame.draw.line(tela, (120, 255, 255),
                                     (lx - bdy * 6, ly + bdx * 6),
                                     (lx + bdy * 6, ly - bdx * 6), 2)

        # Nome
        nome_surf = fonte.render(self.nome, True, BRANCO)
        nx = sx + tam // 2 - nome_surf.get_width() // 2
        ny = sy - 16
        bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        tela.blit(bg, (nx - 3, ny - 1))
        tela.blit(nome_surf, (nx, ny))

        if show_hp:
            hp_w = tam
            hp_h = 4
            hp_x = sx
            hp_y = sy + tam + 4
            pygame.draw.rect(tela, (40, 40, 40), (hp_x, hp_y, hp_w, hp_h), 0, 2)
            r = max(0, self.hp / max(1, self.hp_max))
            cor_hp = VERDE if r > 0.5 else AMARELO if r > 0.25 else VERMELHO
            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, int(hp_w * r), hp_h), 0, 2)


# ============================================================
#  COMBATE
# ============================================================

class GranadaProj:
    """Granada arremessada, com física igual à do item granada.py (arremessa,
    perde velocidade com atrito, quica nas paredes e explode em área)."""

    def __init__(self, x, y, dx, dy, dono):
        self.x = float(x)
        self.y = float(y)
        vel = 12.0
        self.vx = dx * vel + random.uniform(-0.5, 0.5)
        self.vy = dy * vel + random.uniform(-0.5, 0.5)
        self.dono = dono
        self.raio = 10
        self.raio_explosao = 165
        self.dano = 2
        self.fricao = 0.99
        self.elasticidade = 0.9
        self.tempo_vida = 130          # ~2.1s até explodir por tempo
        self.tempo_explosao = 0        # contagem quando quase parada
        self.angulo = 0.0
        self.vel_rot = random.uniform(6, 12)

    def atualizar(self):
        """Retorna True enquanto voa; False quando deve explodir."""
        self.vx *= self.fricao
        self.vy *= self.fricao
        if math.hypot(self.vx, self.vy) < 0.6 and self.tempo_explosao == 0:
            self.tempo_explosao = 30    # 0.5s parada até explodir
        self.x += self.vx
        self.y += self.vy
        # Quicar nas paredes da arena
        if self.x - self.raio < 4:
            self.x = self.raio + 4
            self.vx = abs(self.vx) * self.elasticidade
        elif self.x + self.raio > ARENA_W - 4:
            self.x = ARENA_W - 4 - self.raio
            self.vx = -abs(self.vx) * self.elasticidade
        if self.y - self.raio < 4:
            self.y = self.raio + 4
            self.vy = abs(self.vy) * self.elasticidade
        elif self.y + self.raio > ARENA_H - 4:
            self.y = ARENA_H - 4 - self.raio
            self.vy = -abs(self.vy) * self.elasticidade
        self.angulo = (self.angulo + self.vel_rot) % 360
        self.tempo_vida -= 1
        if self.tempo_explosao > 0:
            self.tempo_explosao -= 1
            if self.tempo_explosao <= 0:
                return False
        return self.tempo_vida > 0

    def desenhar(self, tela, cam_x, cam_y, angulo=None):
        ang_g = self.angulo if angulo is None else angulo
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if not (-30 <= sx <= LARGURA + 30 and -30 <= sy <= ALTURA_JOGO + 30):
            return
        pygame.draw.circle(tela, (35, 70, 35), (sx, sy), self.raio + 1)
        pygame.draw.circle(tela, (60, 120, 60), (sx, sy), self.raio)
        pygame.draw.circle(tela, (85, 155, 85), (sx - 2, sy - 2), 3)
        # Alavanca/pino girando
        a = math.radians(ang_g)
        ex = sx + int(math.cos(a) * (self.raio + 4))
        ey = sy + int(math.sin(a) * (self.raio + 4))
        pygame.draw.line(tela, (200, 200, 120), (sx, sy), (ex, ey), 2)
        pygame.draw.circle(tela, (220, 220, 100), (ex, ey), 2)
        # Pisca quando prestes a explodir
        if self.tempo_explosao > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
            pygame.draw.circle(tela, (255, 90, 40), (sx, sy), self.raio + 5, 2)


def _desenhar_granada(tela, x, y, angulo, cam_x, cam_y):
    """Desenha uma granada (usado no cliente, a partir do snapshot)."""
    sx = int(x - cam_x)
    sy = int(y - cam_y)
    if not (-30 <= sx <= LARGURA + 30 and -30 <= sy <= ALTURA_JOGO + 30):
        return
    raio = 10
    pygame.draw.circle(tela, (35, 70, 35), (sx, sy), raio + 1)
    pygame.draw.circle(tela, (60, 120, 60), (sx, sy), raio)
    pygame.draw.circle(tela, (85, 155, 85), (sx - 2, sy - 2), 3)
    a = math.radians(angulo)
    ex = sx + int(math.cos(a) * (raio + 4))
    ey = sy + int(math.sin(a) * (raio + 4))
    pygame.draw.line(tela, (200, 200, 120), (sx, sy), (ex, ey), 2)
    pygame.draw.circle(tela, (220, 220, 100), (ex, ey), 2)


def _disparar_classe(jogador, alvo_x, alvo_y, tiros, particulas, flashes, granadas=None):
    """Dispara conforme a classe. alvo_x/alvo_y em coordenadas de MUNDO."""
    tempo = pygame.time.get_ticks()
    if tempo - jogador.tempo_ultimo_tiro < jogador.cd:
        return
    jogador.tempo_ultimo_tiro = tempo

    cx, cy = jogador.get_centro()
    dx = alvo_x - cx
    dy = alvo_y - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist
    else:
        dx, dy = 1.0, 0.0

    # Classe Granada: arremessa uma granada (física igual à granada.py)
    if jogador.classe_id == 'granada' and granadas is not None:
        granadas.append(GranadaProj(cx, cy, dx, dy, jogador))
        try:
            from src.utils.sound import gerar_som_tiro
            som = pygame.mixer.Sound(gerar_som_tiro())
            som.set_volume(0.2)
            pygame.mixer.Channel(1).play(som)
        except:
            pass
        return

    ponta_x = cx + dx * 25
    ponta_y = cy + dy * 25
    ang_base = math.atan2(dy, dx)
    cor_bala = jogador.cor_bala if jogador.cor_bala else jogador.cor
    n = max(1, jogador.spread)
    for i in range(n):
        offset = (i - (n - 1) / 2) * math.radians(14) if n > 1 else 0.0
        ndx = math.cos(ang_base + offset)
        ndy = math.sin(ang_base + offset)
        tiro = Tiro(ponta_x, ponta_y, ndx, ndy, cor_bala, velocidade=jogador.vbala)
        tiro.dano = jogador.dano
        tiro.raio = jogador.raio
        tiro.dono = jogador
        tiro.explode = jogador.explode
        tiro.frames = 0
        tiro.ox = ponta_x
        tiro.oy = ponta_y
        tiros.append(tiro)

    for _ in range(4):
        p = Particula(ponta_x + random.uniform(-3, 3), ponta_y + random.uniform(-3, 3),
                      (255, random.randint(150, 255), 0))
        p.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-1, 1)
        p.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-1, 1)
        p.vida = random.randint(8, 16)
        p.tamanho = random.uniform(2, 4)
        particulas.append(p)
    flashes.append({'x': ponta_x, 'y': ponta_y, 'raio': 14, 'vida': 6, 'cor': (255, 200, 0)})

    try:
        from src.utils.sound import gerar_som_tiro
        som = pygame.mixer.Sound(gerar_som_tiro())
        som.set_volume(0.18)
        pygame.mixer.Channel(1).play(som)
    except:
        pass


def _matar(alvo, dono, particulas, flashes):
    alvo.vivo = False
    if dono is not None and dono is not alvo:
        dono.kills += 1
    cx, cy = alvo.get_centro()
    flashes.append(criar_explosao(cx, cy, alvo.cor, particulas, 30))
    try:
        from src.utils.sound import gerar_som_explosao
        som = pygame.mixer.Sound(gerar_som_explosao())
        som.set_volume(0.3)
        pygame.mixer.Channel(2).play(som)
    except:
        pass


def _explodir(ex, ey, raio, dano, dono, jogadores, particulas, flashes, tempo, aplicar_dano=True):
    """Explosao em area. aplicar_dano=False só cria o efeito visual (cliente)."""
    if aplicar_dano:
        for d in jogadores:
            if d.vivo and d is not dono:
                dcx, dcy = d.get_centro()
                dist = math.sqrt((dcx - ex) ** 2 + (dcy - ey) ** 2)
                if dist <= raio + TAM_JOGADOR // 2 and tempo >= d.invulneravel_ate:
                    d.hp -= dano
                    d.invulneravel_ate = tempo + 300
                    flashes.append(criar_explosao(dcx, dcy, d.cor, particulas, 10))
                    if d.hp <= 0:
                        _matar(d, dono, particulas, flashes)
    # Particulas em todas as direcoes
    n_part = 44 if raio >= EXPLOSAO_RAIO else 22
    for _ in range(n_part):
        ang = random.uniform(0, 2 * math.pi)
        vel = random.uniform(3, 9)
        p = Particula(ex, ey, random.choice([(255, 140, 40), (255, 80, 0), (255, 220, 80)]))
        p.velocidade_x = math.cos(ang) * vel
        p.velocidade_y = math.sin(ang) * vel
        p.vida = random.randint(14, 28)
        p.tamanho = random.uniform(3, 6)
        particulas.append(p)
    flashes.append({'x': ex, 'y': ey, 'raio': raio, 'vida': 14, 'cor': (255, 150, 50)})


def _explosao_burst(j, tiros, particulas, flashes, tempo, criar_balas=True):
    """
    Habilidade do explosivo: solta uma rajada de TIROS em todas as direções
    (além do clarão e das partículas). O dano vem das próprias balas.
    criar_balas=False -> só o efeito visual (usado no cliente).
    """
    cx, cy = j.get_centro()
    # Clarão + partículas de fogo
    for _ in range(30):
        ang = random.uniform(0, 2 * math.pi)
        vel = random.uniform(3, 9)
        p = Particula(cx, cy, random.choice([(255, 140, 40), (255, 80, 0), (255, 220, 80)]))
        p.velocidade_x = math.cos(ang) * vel
        p.velocidade_y = math.sin(ang) * vel
        p.vida = random.randint(14, 28)
        p.tamanho = random.uniform(3, 6)
        particulas.append(p)
    flashes.append({'x': cx, 'y': cy, 'raio': EXPLOSAO_RAIO, 'vida': 14, 'cor': (255, 150, 50)})

    # Rajada de tiros radial (o dano é das balas)
    if criar_balas:
        n = 22
        for i in range(n):
            ang = (2 * math.pi * i) / n
            ndx = math.cos(ang)
            ndy = math.sin(ang)
            tiro = Tiro(cx + ndx * 22, cy + ndy * 22, ndx, ndy, (255, 140, 40), velocidade=11)
            tiro.dano = 1
            tiro.raio = 5
            tiro.dono = j
            tiro.explode = 0
            tiro.frames = 0
            tiro.ox = cx + ndx * 22
            tiro.oy = cy + ndy * 22
            tiros.append(tiro)

    try:
        from src.utils.sound import gerar_som_explosao
        som = pygame.mixer.Sound(gerar_som_explosao())
        som.set_volume(0.3)
        pygame.mixer.Channel(2).play(som)
    except:
        pass


# ============================================================
#  IA DO BOT
# ============================================================

def _bot_ai(bot, jogadores, tiros, particulas, flashes, tempo, granadas=None):
    """
    IA estrategista: mira liderando o alvo, desvia muito bem de balas (previsão
    de trajetória), ajusta a postura (defensiva com pouca vida, agressiva quando
    o alvo está fraco) e usa a habilidade da classe de forma inteligente.
    Retorna a ação de habilidade a aplicar no host, ou None.
    """
    if not bot.vivo:
        bot.vx = 0
        bot.vy = 0
        return None

    bot_cx, bot_cy = bot.get_centro()

    # --- Escolha de alvo: prioriza o mais fraco/proximo (vivo e visivel) ---
    alvo = None
    melhor_score = float('inf')
    for jj in jogadores:
        if jj is bot or not jj.vivo or jj.esta_invisivel():
            continue
        d = math.hypot(jj.x - bot.x, jj.y - bot.y)
        score = d + jj.hp * 60          # prefere alvos perto E com pouca vida
        if score < melhor_score:
            melhor_score = score
            alvo = jj
    if not alvo:
        bot.vx = bot.vy = 0
        return None
    bot.bot_alvo = alvo

    dx = alvo.x - bot.x
    dy = alvo.y - bot.y
    dist = math.hypot(dx, dy) or 1
    dir_x = dx / dist
    dir_y = dy / dist

    # --- Strafe (orbita o alvo) ---
    if tempo > bot.bot_strafe_timer:
        bot.bot_strafe_timer = tempo + BOT_STRAFE_INTERVALO + random.randint(-200, 200)
        bot.bot_strafe_dir = -bot.bot_strafe_dir
    mover_x = -dir_y * bot.bot_strafe_dir
    mover_y = dir_x * bot.bot_strafe_dir

    # --- Desvio de balas (previsão de trajetória; reage cedo e forte) ---
    perigo = 0.0
    for tiro in tiros:
        if not hasattr(tiro, 'dono') or tiro.dono is bot:
            continue
        tx = bot_cx - tiro.x
        ty = bot_cy - tiro.y
        d2 = tx * tx + ty * ty
        if d2 > 320 * 320:
            continue
        dot = tiro.dx * tx + tiro.dy * ty
        if dot <= 0:
            continue
        perp_x = tx - tiro.dx * dot
        perp_y = ty - tiro.dy * dot
        pd = math.hypot(perp_x, perp_y)
        # Quanto mais perto da linha e mais perto do tiro, maior o peso do desvio
        if pd < TAM_JOGADOR + 34:
            proximidade = 1.0 - min(1.0, math.sqrt(d2) / 320)
            peso = (2.2 + proximidade * 2.5)
            if pd > 1:
                mover_x -= (perp_x / pd) * peso
                mover_y -= (perp_y / pd) * peso
            else:
                mover_x += -tiro.dy * peso
                mover_y += tiro.dx * peso
            perigo = max(perigo, proximidade + (1.0 - pd / (TAM_JOGADOR + 34)))

    # --- Fugir de granadas próximas ---
    if granadas:
        for g in granadas:
            gx = bot_cx - g.x
            gy = bot_cy - g.y
            gd = math.hypot(gx, gy)
            if gd < g.raio_explosao + 40:
                perigo = max(perigo, 0.8)
                if gd > 1:
                    mover_x += gx / gd * 2.5
                    mover_y += gy / gd * 2.5

    # --- Postura: defensiva com pouca vida, agressiva quando o alvo está fraco ---
    vida_frac = bot.hp / max(1, bot.hp_max)
    agressivo = (alvo.hp <= 1 and vida_frac > 0.4) or vida_frac > 0.75
    defensivo = vida_frac <= 0.35 or perigo > 0.9

    ideal = BOT_DIST_IDEAL
    if defensivo:
        ideal = BOT_DIST_AVANCAR       # mantém mais longe
    elif agressivo:
        ideal = BOT_DIST_RECUAR + 40   # pressiona

    if dist < ideal - 40:
        mover_x -= dir_x * 0.8
        mover_y -= dir_y * 0.8
    elif dist > ideal + 60:
        mover_x += dir_x * (0.7 if not defensivo else 0.3)
        mover_y += dir_y * (0.7 if not defensivo else 0.3)

    # --- Evitar as paredes da arena ---
    margem = 110
    if bot_cx < margem:
        mover_x += 1.0
    elif bot_cx > ARENA_W - margem:
        mover_x -= 1.0
    if bot_cy < margem:
        mover_y += 1.0
    elif bot_cy > ARENA_H - margem:
        mover_y -= 1.0

    mag = math.hypot(mover_x, mover_y)
    if mag > 0:
        mover_x /= mag
        mover_y /= mag
    vloc = bot.vel_efetiva()
    bot.vx = mover_x * vloc
    bot.vy = mover_y * vloc

    # --- Mira: lidera o alvo pela velocidade da bala (interceptação) ---
    vbala = max(6.0, bot.vbala)
    tempo_bala = dist / vbala
    prev_x = alvo.x + TAM_JOGADOR // 2 + alvo.vx * tempo_bala
    prev_y = alvo.y + TAM_JOGADOR // 2 + alvo.vy * tempo_bala
    impr = min(dist / 900, 0.16)       # bem mais preciso que antes
    adx = prev_x - bot_cx
    ady = prev_y - bot_cy
    ang = math.atan2(ady, adx) + random.uniform(-impr, impr)
    bot.mira_x = bot_cx + math.cos(ang) * dist
    bot.mira_y = bot_cy + math.sin(ang) * dist

    # --- Habilidade da classe (uso inteligente) ---
    acao_special = None
    if bot.special and tempo >= bot.bot_next_special:
        usou = None
        if bot.special == 'dash':
            # Dash pra fugir de perigo/parede, ou pra fechar distância ocasional
            if perigo > 0.7 or dist < 70:
                usou = 'dash' if bot.executar_dash(-dir_x, -dir_y) else None
            elif agressivo and dist > 200 and random.random() < 0.4:
                usou = 'dash' if bot.executar_dash(dir_x, dir_y) else None
        elif bot.special == 'shield':
            if perigo > 0.6 or (dist < 260 and vida_frac < 0.6):
                usou = 'shield' if bot.ativar_shield() else None
        elif bot.special == 'invisivel':
            if perigo > 0.7 or vida_frac < 0.5:
                usou = 'invisivel' if bot.ficar_invisivel() else None
        elif bot.special == 'explosao':
            if dist < EXPLOSAO_RAIO - 10:
                usou = 'explosao' if bot.preparar_explosao() else None
        elif bot.special == 'velocidade':
            if agressivo or perigo > 0.6 or dist > 300:
                usou = 'velocidade' if bot.ativar_boost() else None
        if usou:
            acao_special = usou
            bot.bot_next_special = tempo + SPECIAL_COOLDOWN + random.randint(0, 700)
        else:
            bot.bot_next_special = tempo + 300

    # --- Atirar (não desperdiça tiro muito longe; granada tem alcance próprio) ---
    alcance = 660 if bot.classe_id == 'granada' else 560
    if tempo >= bot.bot_next_shot and dist < alcance:
        _disparar_classe(bot, bot.mira_x, bot.mira_y, tiros, particulas, flashes, granadas)
        bot.bot_next_shot = tempo + bot.cd + random.randint(0, 100)

    return acao_special


# ============================================================
#  CAMERA / ARENA / MINIMAP
# ============================================================

def _atualizar_camera(jogador, cam_x, cam_y):
    alvo_x = jogador.x + TAM_JOGADOR // 2 - LARGURA // 2
    alvo_y = jogador.y + TAM_JOGADOR // 2 - ALTURA_JOGO // 2
    cam_x += (alvo_x - cam_x) * 0.08
    cam_y += (alvo_y - cam_y) * 0.08
    cam_x = max(0, min(cam_x, ARENA_W - LARGURA))
    cam_y = max(0, min(cam_y, ARENA_H - ALTURA_JOGO))
    return cam_x, cam_y


def _desenhar_arena(tela, cam_x, cam_y, tempo):
    """Arena 'grade de circuito' (tema teal/ciano - visual distinto do Sabers)."""
    tela.fill((6, 14, 16))
    placa = 80
    start_px = max(0, int(cam_x // placa) * placa)
    start_py = max(0, int(cam_y // placa) * placa)
    end_px = min(ARENA_W, int((cam_x + LARGURA) // placa + 2) * placa)
    end_py = min(ARENA_H, int((cam_y + ALTURA_JOGO) // placa + 2) * placa)
    for py_t in range(start_py, end_py, placa):
        for px_t in range(start_px, end_px, placa):
            sx = int(px_t - cam_x)
            sy = int(py_t - cam_y)
            idx = (px_t // placa + py_t // placa)
            v = (idx * 7 + 3) % 5
            pygame.draw.rect(tela, (10 + v, 20 + v, 24 + v), (sx, sy, placa, placa))
            pygame.draw.rect(tela, (16 + v, 34 + v, 40 + v), (sx, sy, placa, placa), 1)
            if idx % 5 == 0:
                pulso = (math.sin(tempo / 600 + idx * 0.5) + 1) / 2
                a = int(20 + pulso * 30)
                pygame.draw.line(tela, (0, a, a), (sx + 12, sy + placa // 2),
                                 (sx + placa - 12, sy + placa // 2), 1)

    pulso_e = (math.sin(tempo / 800) + 1) / 2
    a = int(30 + pulso_e * 30)
    for gy in range(0, ARENA_H, 320):
        sy = int(gy - cam_y)
        if -2 <= sy <= ALTURA_JOGO + 2:
            pygame.draw.line(tela, (0, a, int(a * 1.2)), (0, sy), (LARGURA, sy), 1)
    for gx in range(0, ARENA_W, 320):
        sx = int(gx - cam_x)
        if -2 <= sx <= LARGURA + 2:
            pygame.draw.line(tela, (0, a, int(a * 1.2)), (sx, 0), (sx, ALTURA_JOGO), 1)

    for (spx, spy) in SPAWN_POINTS:
        msx = int(spx + TAM_JOGADOR // 2 - cam_x)
        msy = int(spy + TAM_JOGADOR // 2 - cam_y)
        if -50 <= msx <= LARGURA + 50 and -50 <= msy <= ALTURA_JOGO + 50:
            pts = []
            for h in range(6):
                ang = math.pi / 6 + h * math.pi / 3
                pts.append((msx + int(math.cos(ang) * 24), msy + int(math.sin(ang) * 24)))
            pygame.draw.polygon(tela, (60, 45, 20), pts, 1)

    borda = (40, 200, 200)
    glow = (20, 110, 120)
    by = int(-cam_y)
    if -10 <= by <= ALTURA_JOGO:
        pygame.draw.line(tela, glow, (0, by - 2), (LARGURA, by - 2), 6)
        pygame.draw.line(tela, borda, (0, by), (LARGURA, by), 2)
    by = int(ARENA_H - cam_y)
    if 0 <= by <= ALTURA_JOGO + 10:
        pygame.draw.line(tela, glow, (0, by + 2), (LARGURA, by + 2), 6)
        pygame.draw.line(tela, borda, (0, by), (LARGURA, by), 2)
    bx = int(-cam_x)
    if -10 <= bx <= LARGURA:
        pygame.draw.line(tela, glow, (bx - 2, 0), (bx - 2, ALTURA_JOGO), 6)
        pygame.draw.line(tela, borda, (bx, 0), (bx, ALTURA_JOGO), 2)
    bx = int(ARENA_W - cam_x)
    if 0 <= bx <= LARGURA + 10:
        pygame.draw.line(tela, glow, (bx + 2, 0), (bx + 2, ALTURA_JOGO), 6)
        pygame.draw.line(tela, borda, (bx, 0), (bx, ALTURA_JOGO), 2)


def _desenhar_minimap(tela, jogadores, jogador_local, cam_x, cam_y):
    surf = pygame.Surface((MINIMAP_W, MINIMAP_H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 150))
    pygame.draw.rect(surf, (30, 90, 95), (0, 0, MINIMAP_W, MINIMAP_H), 1)
    vx = int((cam_x / ARENA_W) * MINIMAP_W)
    vy = int((cam_y / ARENA_H) * MINIMAP_H)
    vw = int((LARGURA / ARENA_W) * MINIMAP_W)
    vh = int((ALTURA_JOGO / ARENA_H) * MINIMAP_H)
    pygame.draw.rect(surf, (100, 150, 150, 90), (vx, vy, vw, vh), 1)
    for j in jogadores:
        if not j.vivo:
            continue
        # Nao revela jogadores invisiveis (exceto o proprio)
        if j.esta_invisivel() and j is not jogador_local:
            continue
        mx = int((j.x / ARENA_W) * MINIMAP_W)
        my = int((j.y / ARENA_H) * MINIMAP_H)
        tam = 5 if j is jogador_local else 3
        cor = BRANCO if j is jogador_local else j.cor_pessoal
        pygame.draw.rect(surf, cor, (mx - tam // 2, my - tam // 2, tam, tam))
    tela.blit(surf, (MINIMAP_X, MINIMAP_Y))


# Descrição curta da habilidade de cada classe (tela de seleção)
_DESC_HAB = {
    'player': 'Dash', 'ciano': 'Velocidade', 'metralha': 'Metralhadora',
    'mago': 'Escudo', 'explosive': 'Explosao', 'roxo': 'Mais vida',
    'fantasma': 'Invisivel', 'granada': 'Granadas',
}

# Cache de inimigos usados só para desenhar os ícones das classes (previews)
_PREVIEW_ENEMIES = {}


def _desenhar_icone_classe(tela, ox, oy, tam, classe_idx, tempo):
    """Desenha o ícone de uma classe: visual do inimigo (metralha/mago/granada/
    fantasma) ou o quadrado + marcador para as demais."""
    classe = CLASSES[classe_idx]
    cid = classe['id']
    info = _ENEMY_VISUAL.get(cid)
    if info:
        e = _PREVIEW_ENEMIES.get(cid)
        if e is None:
            e = info[0](0, 0)
            _PREVIEW_ENEMIES[cid] = e
        e.x = ox
        e.y = oy
        e.tamanho = tam
        for a, v in (('esta_recarregando', False), ('escudo_ativo', False),
                     ('esta_invocando', False), ('esta_visivel', True),
                     ('cajado_visivel', True)):
            if hasattr(e, a):
                setattr(e, a, v)
        if hasattr(e, 'alpha_atual'):
            e.alpha_atual = 255
        if hasattr(e, 'tempo_criacao'):
            e.tempo_criacao = tempo - 5000
        if hasattr(e, 'tempo_ultimo_lancamento'):
            e.tempo_ultimo_lancamento = tempo - 100000
        try:
            e.desenhar(tela, tempo)
            equip = info[1]
            if equip:
                alvo = _AlvoMira(ox + tam + 26, oy + tam // 2)
                getattr(e, equip)(tela, tempo, alvo)
        except Exception:
            pass
    else:
        cor = classe['cor']
        pygame.draw.rect(tela, tuple(max(0, c - 60) for c in cor), (ox, oy, tam, tam), 0, 4)
        pygame.draw.rect(tela, cor, (ox + 2, oy + 2, tam - 4, tam - 4), 0, 3)
        pygame.draw.rect(tela, tuple(min(255, c + 80) for c in cor), (ox + 4, oy + 4, 7, 7), 0, 2)
        _marcador_classe(tela, ox, oy, tam, cid, cor, tempo)


def _cards_classe_rects():
    """Retorna os Rects dos cards de classe (grade 4x2) da tela de seleção."""
    cards = []
    cw, ch = 170, 140
    cols = 4
    gx = (LARGURA - cw * cols) // (cols + 1)
    gy = 24
    y0 = 180
    for i in range(len(CLASSES)):
        c = i % cols
        r = i // cols
        x = gx + c * (cw + gx)
        y = y0 + r * (ch + gy)
        cards.append(pygame.Rect(x, y, cw, ch))
    return cards


def _desenhar_class_select(tela, cards, sel_idx, mouse_pos, fonte_grande,
                           fonte_media, fonte_peq, tempo, is_host):
    """Tela onde o HOST escolhe a sua classe (o resto é aleatorio)."""
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    tela.blit(overlay, (0, 0))

    if not is_host:
        msg = fonte_grande.render("Aguardando o host escolher a classe...", True, (200, 220, 220))
        tela.blit(msg, (LARGURA // 2 - msg.get_width() // 2, ALTURA_JOGO // 2 - 20))
        pontos = "." * (1 + (tempo // 400) % 3)
        p = fonte_media.render(pontos, True, (150, 190, 190))
        tela.blit(p, (LARGURA // 2 - p.get_width() // 2, ALTURA_JOGO // 2 + 30))
        return

    tit = fonte_grande.render("ESCOLHA SUA CLASSE", True, (200, 240, 240))
    tela.blit(tit, (LARGURA // 2 - tit.get_width() // 2, 70))
    sub = fonte_peq.render("As classes dos outros jogadores serao aleatorias (sem repetir)",
                           True, (150, 180, 180))
    tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 128))

    for i, rect in enumerate(cards):
        classe = CLASSES[i]
        selecionado = (i == sel_idx)
        hover = rect.collidepoint(mouse_pos)
        realce = selecionado or hover
        cor = classe['cor']
        pygame.draw.rect(tela, (22, 34, 38) if not realce else (34, 52, 58), rect, 0, 12)
        borda = cor if realce else (70, 90, 95)
        pygame.draw.rect(tela, borda, rect, 3 if realce else 2, 12)

        # Preview do ícone da classe (visual do inimigo quando aplicável)
        tam = TAM_JOGADOR
        px = rect.centerx - tam // 2
        py = rect.y + 20
        _desenhar_icone_classe(tela, px, py, tam, i, tempo)

        nome_s = fonte_media.render(classe['nome'], True, BRANCO if realce else (210, 220, 220))
        tela.blit(nome_s, (rect.centerx - nome_s.get_width() // 2, rect.y + 66))
        desc = f"HP {classe['hp']}  -  {_DESC_HAB.get(classe['id'], '')}"
        desc_s = fonte_peq.render(desc, True, (170, 200, 200))
        tela.blit(desc_s, (rect.centerx - desc_s.get_width() // 2, rect.y + 100))
        tecla_s = fonte_peq.render(str(i + 1), True, (140, 170, 170))
        tela.blit(tecla_s, (rect.x + 8, rect.y + 6))

    dica = fonte_peq.render("Setas/1-8/Mouse: Escolher   |   ENTER ou Clique: Confirmar", True, (160, 200, 200))
    tela.blit(dica, (LARGURA // 2 - dica.get_width() // 2, ALTURA_JOGO - 40))


def _desenhar_roleta(tela, jogadores, fonte_media, fonte_peq, tempo_no_estado):
    n = len(jogadores)
    card_w = 150
    gap = 14
    total = n * card_w + (n - 1) * gap
    x0 = LARGURA // 2 - total // 2
    y = ALTURA_JOGO // 2 - 45 + 20
    titulo = fonte_media.render("SORTEANDO CLASSES...", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, y - 70))
    for i, j in enumerate(jogadores):
        rx = x0 + i * (card_w + gap)
        travar_em = 900 + i * 320
        travado = tempo_no_estado >= travar_em
        cidx = j.classe_idx if travado else (tempo_no_estado // 70 + i) % len(CLASSES)
        classe = CLASSES[cidx]
        rect = pygame.Rect(rx, y, card_w, 90)
        pygame.draw.rect(tela, (18, 30, 34), rect, 0, 10)
        borda = classe['cor'] if travado else (70, 90, 95)
        pygame.draw.rect(tela, borda, rect, 3 if travado else 1, 10)
        tam = 28
        px = rect.centerx - tam // 2
        py = rect.y + 12
        cor = classe['cor']
        _desenhar_icone_classe(tela, px, py, tam, cidx, pygame.time.get_ticks())
        nome_j = fonte_peq.render(j.nome[:12], True, (200, 210, 210))
        tela.blit(nome_j, (rect.centerx - nome_j.get_width() // 2, rect.y + 44))
        nome_c = fonte_peq.render(classe['nome'], True, cor if travado else (150, 160, 160))
        tela.blit(nome_c, (rect.centerx - nome_c.get_width() // 2, rect.y + 64))


def _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_score, fonte_peq, tempo, start_time):
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))
    titulo = fonte_grande.render("RESULTADO", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 40))
    ranking = sorted(jogadores, key=lambda j: (-j.rodadas_vencidas, -j.kills))
    tempo_decorrido = tempo - start_time
    y_base = 120
    for rank, j in enumerate(ranking):
        if tempo_decorrido < rank * 300:
            continue
        y = y_base + rank * 50
        linha_w = 520
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
        pygame.draw.rect(tela, tuple(max(0, c - 60) for c in j.cor), (sq_x, sq_y, sq_tam, sq_tam), 0, 4)
        pygame.draw.rect(tela, j.cor, (sq_x + 2, sq_y + 2, sq_tam - 4, sq_tam - 4), 0, 3)
        pygame.draw.rect(tela, j.cor_pessoal, (sq_x, sq_y, sq_tam, sq_tam), 2, 4)
        nome_s = fonte_score.render(f"{j.nome}  ({CLASSES[j.classe_idx]['nome']})", True, BRANCO)
        tela.blit(nome_s, (sq_x + sq_tam + 12, y + 8))
        stats_s = fonte_peq.render(f"{j.rodadas_vencidas}R  {j.kills}K", True, (180, 255, 180))
        tela.blit(stats_s, (linha_x + 400, y + 12))
        if rank < 3:
            pygame.draw.rect(tela, pos_cor, (linha_x, y, linha_w, 42), 1, 3)
    if tempo_decorrido > 3000:
        inst = fonte_peq.render("Voltando ao lobby...", True, (120, 120, 140))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))


def _desenhar_hud(tela, jogador, fonte_peq, vivos, rodada, tempo):
    for i in range(jogador.hp_max):
        hx = 15 + i * 22
        hy = 10
        if i < jogador.hp:
            pygame.draw.rect(tela, VERMELHO, (hx, hy, 16, 16), 0, 4)
            pygame.draw.rect(tela, (255, 100, 100), (hx + 2, hy + 2, 5, 5), 0, 2)
        else:
            pygame.draw.rect(tela, (60, 40, 40), (hx, hy, 16, 16), 1, 4)
    info = fonte_peq.render(f"Vivos: {vivos}  |  Rodada: {rodada}/{NUM_RODADAS}", True, (180, 200, 200))
    tela.blit(info, (LARGURA // 2 - info.get_width() // 2, 8))
    cls_s = fonte_peq.render(f"Classe: {CLASSES[jogador.classe_idx]['nome']}", True, jogador.cor)
    tela.blit(cls_s, (15, 34))
    kills_s = fonte_peq.render(f"Kills: {jogador.kills}", True, (180, 255, 180))
    tela.blit(kills_s, (170, 34))

    # Indicador de habilidade (só classes com habilidade ativa)
    nomes_hab = {'dash': 'DASH', 'shield': 'ESCUDO', 'invisivel': 'INVISIVEL',
                 'explosao': 'EXPLOSAO', 'velocidade': 'VELOCIDADE'}
    if jogador.special in nomes_hab:
        if jogador.special == 'dash':
            pronto = (tempo - jogador.dash_tempo_cooldown >= DASH_COOLDOWN) and not jogador.dash_ativo
        else:
            pronto = jogador.special_pronto()
        cor_h = (120, 220, 255) if pronto else (90, 90, 110)
        hab = nomes_hab[jogador.special]
        hab_s = fonte_peq.render(f"SPACE: {hab}" + ("" if pronto else " (recarregando)"), True, cor_h)
        tela.blit(hab_s, (300, 34))

    ctrl = fonte_peq.render("WASD: Mover | Segure CLICK: Atirar | SPACE: Habilidade | ESC: Sair",
                            True, (100, 120, 120))
    tela.blit(ctrl, (LARGURA // 2 - ctrl.get_width() // 2, ALTURA_JOGO - 18))


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def executar_minigame_classes(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                              cliente, nome_jogador, customizacao):
    """Executa o minigame Batalha de Classes (free-for-all)."""
    print("[CLASSES] Minigame Batalha de Classes (FFA) iniciado!")

    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)
        print(f"[CLASSES] Usando seed compartilhado: {seed}")

    if cliente:
        cliente.get_minigame_actions()

    fonte_grande = pygame.font.SysFont("Arial", 48, True)
    fonte_media = pygame.font.SysFont("Arial", 28, True)
    fonte_peq = pygame.font.SysFont("Arial", 14)
    fonte_nomes = pygame.font.SysFont("Arial", 12)
    fonte_score = pygame.font.SysFont("Arial", 22, True)
    fonte_countdown = pygame.font.SysFont("Arial", 72, True)

    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)

    host_autoritativo = sou_host(cliente)

    jogadores = []
    cor_local = customizacao.get('cor', AZUL)
    jogador_humano = None
    for pid, nome, is_local in ordenar_humanos(cliente, nome_jogador):
        cor = cor_local if is_local else PALETA_CORES[(pid - 1) % len(PALETA_CORES)]
        j = JogadorClasse(nome, cor, is_bot=False, is_remote=not is_local)
        j.player_id = pid
        jogadores.append(j)
        if is_local:
            jogador_humano = j

    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo", "Bot Foxtrot", "Bot Golf", "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        b = JogadorClasse(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True)
        b.player_id = None
        jogadores.append(b)
        bot_idx += 1

    # As classes são atribuídas quando o HOST escolhe a sua (tela CLASS_SELECT):
    # o host fica com a escolhida e os outros recebem o resto embaralhado (sem
    # repetir). O host é autoritativo e envia a atribuição no snapshot ('cls').

    jogadores_por_pid = {
        j.player_id: j for j in jogadores
        if not j.is_bot and j.player_id is not None
    }

    for i, j in enumerate(jogadores):
        j.x = float(SPAWN_POINTS[i][0])
        j.y = float(SPAWN_POINTS[i][1])

    cam_x = max(0, min(float(jogador_humano.x - LARGURA // 2), ARENA_W - LARGURA))
    cam_y = max(0, min(float(jogador_humano.y - ALTURA_JOGO // 2), ARENA_H - ALTURA_JOGO))

    estado = "CLASS_SELECT"
    tempo_estado = pygame.time.get_ticks()
    tiros = []
    particulas = []
    flashes = []
    tiros_render = []
    granadas = []           # GranadaProj (host) em coords de mundo
    granadas_render = []    # (x, y, angulo) recebidos do host (cliente)
    rodada_atual = 1
    scoreboard_start = 0
    round_vencedor = None
    alpha_fade = 255
    ultimo_pedido_tiro = 0

    # Seleção de classe (host)
    sel_classe = 0
    cards_classe = _cards_classe_rects()

    def _idx_de(d):
        return jogadores.index(d) if d in jogadores else -1

    def _construir_snapshot():
        pl = []
        for j in jogadores:
            pl.append({
                'x': round(j.x, 1), 'y': round(j.y, 1),
                'mx': round(j.mira_x, 1), 'my': round(j.mira_y, 1),
                'hp': j.hp, 'v': j.vivo, 'k': j.kills, 'rv': j.rodadas_vencidas,
                'cls': j.classe_idx,
                'inv': max(0, j.invulneravel_ate - tempo),
                'sh': max(0, j.shield_ate - tempo),
                'iv': max(0, j.invisivel_ate - tempo),
                'vb': max(0, j.boost_ate - tempo),
            })
        bul = [[round(t.x, 1), round(t.y, 1), t.raio, list(t.cor)] for t in tiros]
        gr = [[round(g.x, 1), round(g.y, 1), round(g.angulo, 1)] for g in granadas]
        return {
            'action': 'classe_state',
            'st': estado, 'rd': rodada_atual, 'rvi': _idx_de(round_vencedor),
            'pl': pl, 'bul': bul, 'gr': gr,
        }

    def _aplicar_snapshot(snap):
        nonlocal estado, tempo_estado, rodada_atual, round_vencedor
        novo = snap.get('st', estado)
        if novo != estado:
            estado = novo
            tempo_estado = pygame.time.get_ticks()
        rodada_atual = snap.get('rd', rodada_atual)
        now = pygame.time.get_ticks()
        pl = snap.get('pl', [])
        for idx, j in enumerate(jogadores):
            if idx >= len(pl):
                break
            pj = pl[idx]
            if pj.get('cls') is not None and pj['cls'] != j.classe_idx:
                j.aplicar_classe(pj['cls'])
            eh_local = (j is jogador_humano and estado == "FIGHT" and pj['v'])
            if not eh_local:
                j.x = pj['x']
                j.y = pj['y']
                j.mira_x = pj['mx']
                j.mira_y = pj['my']
            j.hp = pj['hp']
            j.vivo = pj['v']
            j.kills = pj['k']
            j.rodadas_vencidas = pj['rv']
            j.invulneravel_ate = now + pj['inv']
            j.shield_ate = now + pj.get('sh', 0)
            j.invisivel_ate = now + pj.get('iv', 0)
            if not eh_local:
                j.boost_ate = now + pj.get('vb', 0)
        rvi = snap.get('rvi', -1)
        round_vencedor = jogadores[rvi] if 0 <= rvi < len(jogadores) else None
        tiros_render.clear()
        for b in snap.get('bul', []):
            cor = tuple(b[3]) if len(b) > 3 else (255, 240, 150)
            tiros_render.append((b[0], b[1], b[2], cor))
        granadas_render.clear()
        for g in snap.get('gr', []):
            granadas_render.append((g[0], g[1], g[2]))

    def _aplicar_special_host(j, tipo):
        """Aplica o efeito autoritativo de uma habilidade no host."""
        if tipo == 'shield':
            j.shield_ate = tempo + SHIELD_DURACAO
            j.invulneravel_ate = tempo + SHIELD_DURACAO
        elif tipo == 'invisivel':
            j.invisivel_ate = tempo + INVISIVEL_DURACAO
        elif tipo == 'velocidade':
            j.boost_ate = tempo + VELOZ_DURACAO
        elif tipo == 'dash':
            j.invulneravel_ate = tempo + 300
        elif tipo == 'explosao':
            _explosao_burst(j, tiros, particulas, flashes, tempo, criar_balas=True)

    while True:
        tempo = pygame.time.get_ticks()
        tempo_no_estado = tempo - tempo_estado

        def _confirmar_classe(escolhida):
            """Host escolhe a sua classe; os outros recebem o resto (sem repetir)."""
            nonlocal estado, tempo_estado
            restantes = [i for i in range(len(CLASSES)) if i != escolhida]
            random.shuffle(restantes)
            jogador_humano.aplicar_classe(escolhida)
            it = iter(restantes)
            for jj in jogadores:
                if jj is jogador_humano:
                    continue
                jj.aplicar_classe(next(it))
            estado = "INTRO"
            tempo_estado = tempo

        # ========== EVENTOS ==========
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.mouse.set_visible(True)
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.mouse.set_visible(True)
                return None

            # Tela de escolha de classe (só o host escolhe)
            if estado == "CLASS_SELECT":
                if host_autoritativo:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key in (pygame.K_RIGHT, pygame.K_d):
                            sel_classe = (sel_classe + 1) % len(CLASSES)
                        elif ev.key in (pygame.K_LEFT, pygame.K_a):
                            sel_classe = (sel_classe - 1) % len(CLASSES)
                        elif ev.key in (pygame.K_DOWN, pygame.K_s):
                            sel_classe = (sel_classe + 4) % len(CLASSES)
                        elif ev.key in (pygame.K_UP, pygame.K_w):
                            sel_classe = (sel_classe - 4) % len(CLASSES)
                        elif pygame.K_1 <= ev.key <= pygame.K_8:
                            idx = ev.key - pygame.K_1
                            if idx < len(CLASSES):
                                _confirmar_classe(idx)
                        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            _confirmar_classe(sel_classe)
                    elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        cp = convert_mouse_position(ev.pos)
                        for ci, crect in enumerate(cards_classe):
                            if crect.collidepoint(cp):
                                sel_classe = ci
                                _confirmar_classe(ci)
                                break
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE and estado == "FIGHT" and jogador_humano.vivo and not jogador_humano.is_remote:
                    teclas_s = pygame.key.get_pressed()
                    ddx, ddy = 0.0, 0.0
                    if teclas_s[pygame.K_w] or teclas_s[pygame.K_UP]:
                        ddy -= 1
                    if teclas_s[pygame.K_s] or teclas_s[pygame.K_DOWN]:
                        ddy += 1
                    if teclas_s[pygame.K_a] or teclas_s[pygame.K_LEFT]:
                        ddx -= 1
                    if teclas_s[pygame.K_d] or teclas_s[pygame.K_RIGHT]:
                        ddx += 1
                    tipo = jogador_humano.usar_special(ddx, ddy)
                    if tipo:
                        if tipo == 'explosao':
                            # visual local imediato; as balas (dano) são do host
                            _explosao_burst(jogador_humano, tiros, particulas, flashes,
                                            tempo, criar_balas=host_autoritativo)
                        if cliente:
                            cliente.send_minigame_action({'action': 'classe_special', 'tipo': tipo})

        # ========== MIRA DO JOGADOR LOCAL (mundo) ==========
        if estado in ("FIGHT", "COUNTDOWN"):
            mp = convert_mouse_position(pygame.mouse.get_pos())
            jogador_humano.mira_x = float(mp[0]) + cam_x
            jogador_humano.mira_y = float(mp[1]) + cam_y

        # ========== TIRO CONTINUO ==========
        if estado == "FIGHT" and jogador_humano.vivo:
            if pygame.mouse.get_pressed()[0]:
                wx, wy = jogador_humano.mira_x, jogador_humano.mira_y
                if host_autoritativo:
                    _disparar_classe(jogador_humano, wx, wy, tiros, particulas, flashes, granadas)
                elif cliente and tempo - ultimo_pedido_tiro >= jogador_humano.cd:
                    ultimo_pedido_tiro = tempo
                    cliente.send_minigame_action({'action': 'classe_shot', 'mx': wx, 'my': wy})

        # ========== MAQUINA DE ESTADOS (host simula) ==========
        if host_autoritativo and estado == "INTRO":
            if tempo_no_estado >= TEMPO_INTRO:
                estado = "COUNTDOWN"
                tempo_estado = tempo

        elif host_autoritativo and estado == "COUNTDOWN":
            if tempo_no_estado >= TEMPO_COUNTDOWN:
                estado = "FIGHT"
                tempo_estado = tempo
                for j in jogadores:
                    if j.is_bot:
                        j.bot_next_shot = tempo + random.randint(300, 800)
                        j.bot_strafe_timer = tempo + random.randint(200, 600)
                        j.bot_next_special = tempo + random.randint(800, 2000)

        elif host_autoritativo and estado == "FIGHT":
            teclas = pygame.key.get_pressed()
            if jogador_humano.vivo and not jogador_humano.dash_ativo:
                vloc = jogador_humano.vel_efetiva()
                dxm, dym = 0.0, 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                    dym -= vloc
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                    dym += vloc
                if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                    dxm -= vloc
                if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                    dxm += vloc
                if dxm != 0 and dym != 0:
                    f = vloc / math.sqrt(dxm * dxm + dym * dym)
                    dxm *= f
                    dym *= f
                jogador_humano.vx = dxm
                jogador_humano.vy = dym

            for j in jogadores:
                if j.is_bot and j.vivo:
                    acao = _bot_ai(j, jogadores, tiros, particulas, flashes, tempo, granadas)
                    if acao:
                        _aplicar_special_host(j, acao)

            for j in jogadores:
                if j.vivo:
                    j.atualizar_dash()
                    if not j.dash_ativo and not j.is_remote:
                        j.x += j.vx
                        j.y += j.vy
                    j.x = max(4, min(j.x, ARENA_W - TAM_JOGADOR - 4))
                    j.y = max(4, min(j.y, ARENA_H - TAM_JOGADOR - 4))

            for tiro in tiros[:]:
                tiro.atualizar()
                tiro.frames = getattr(tiro, 'frames', 0) + 1
                percorrido = math.hypot(tiro.x - getattr(tiro, 'ox', tiro.x),
                                        tiro.y - getattr(tiro, 'oy', tiro.y))
                if (not ARENA_RECT.collidepoint(tiro.x, tiro.y)
                        or tiro.frames > BALA_VIDA_MAX or percorrido > BALA_ALCANCE):
                    if getattr(tiro, 'explode', 0):
                        _explodir(tiro.x, tiro.y, tiro.explode, tiro.dano, tiro.dono,
                                  jogadores, particulas, flashes, tempo)
                    tiros.remove(tiro)
                    continue
                acertou = False
                for alvo in jogadores:
                    if (alvo.vivo and tiro.dono is not alvo
                            and tempo >= alvo.invulneravel_ate
                            and alvo.get_rect().colliderect(tiro.rect)):
                        if getattr(tiro, 'explode', 0):
                            _explodir(tiro.x, tiro.y, tiro.explode, tiro.dano, tiro.dono,
                                      jogadores, particulas, flashes, tempo)
                        else:
                            alvo.hp -= tiro.dano
                            alvo.invulneravel_ate = tempo + 300
                            cx, cy = alvo.get_centro()
                            flashes.append(criar_explosao(cx, cy, alvo.cor, particulas, 8))
                            if alvo.hp <= 0:
                                _matar(alvo, tiro.dono, particulas, flashes)
                        tiros.remove(tiro)
                        acertou = True
                        break
                if acertou:
                    continue

            # Granadas (explodem em área ao parar/estourar o tempo)
            for g in granadas[:]:
                if not g.atualizar():
                    _explodir(g.x, g.y, g.raio_explosao, g.dano, g.dono,
                              jogadores, particulas, flashes, tempo)
                    granadas.remove(g)

            vivos = [j for j in jogadores if j.vivo]
            if len(vivos) <= 1:
                round_vencedor = vivos[0] if len(vivos) == 1 else None
                if round_vencedor:
                    round_vencedor.rodadas_vencidas += 1
                estado = "ROUND_END"
                tempo_estado = tempo
                tiros.clear()
                granadas.clear()

        elif host_autoritativo and estado == "ROUND_END":
            if tempo_no_estado >= TEMPO_ROUND_END:
                if rodada_atual >= NUM_RODADAS:
                    estado = "SCOREBOARD"
                    tempo_estado = tempo
                    scoreboard_start = tempo
                else:
                    rodada_atual += 1
                    for i, j in enumerate(jogadores):
                        j.reset_rodada(SPAWN_POINTS[i][0], SPAWN_POINTS[i][1])
                    particulas.clear()
                    flashes.clear()
                    tiros.clear()
                    granadas.clear()
                    estado = "COUNTDOWN"
                    tempo_estado = tempo

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                pygame.mouse.set_visible(True)
                return None

        # --- Cliente: prevê o movimento do próprio jogador ---
        if (not host_autoritativo and estado == "FIGHT" and jogador_humano.vivo):
            teclas = pygame.key.get_pressed()
            if not jogador_humano.dash_ativo:
                vloc = jogador_humano.vel_efetiva()
                dxm, dym = 0.0, 0.0
                if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                    dym -= vloc
                if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                    dym += vloc
                if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                    dxm -= vloc
                if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                    dxm += vloc
                if dxm != 0 and dym != 0:
                    f = vloc / math.sqrt(dxm * dxm + dym * dym)
                    dxm *= f
                    dym *= f
                jogador_humano.vx = dxm
                jogador_humano.vy = dym
            jogador_humano.atualizar_dash()
            if not jogador_humano.dash_ativo:
                jogador_humano.x += jogador_humano.vx
                jogador_humano.y += jogador_humano.vy
            jogador_humano.x = max(4, min(jogador_humano.x, ARENA_W - TAM_JOGADOR - 4))
            jogador_humano.y = max(4, min(jogador_humano.y, ARENA_H - TAM_JOGADOR - 4))

        if estado == "INTRO" and tempo_no_estado < 500:
            alpha_fade = int(255 * (1 - tempo_no_estado / 500))
        else:
            alpha_fade = 0

        # ========== REDE ==========
        if cliente:
            if host_autoritativo:
                for acao in cliente.get_minigame_actions():
                    j = jogadores_por_pid.get(acao.get('player_id'))
                    if j is None or j is jogador_humano:
                        continue
                    act = acao.get('action', '')
                    if act == 'classe_input':
                        if j.vivo:
                            j.x = acao.get('x', j.x)
                            j.y = acao.get('y', j.y)
                            j.mira_x = acao.get('mx', j.mira_x)
                            j.mira_y = acao.get('my', j.mira_y)
                            j.x = max(4, min(j.x, ARENA_W - TAM_JOGADOR - 4))
                            j.y = max(4, min(j.y, ARENA_H - TAM_JOGADOR - 4))
                    elif act == 'classe_shot':
                        if j.vivo and estado == "FIGHT":
                            _disparar_classe(j, acao.get('mx', 0), acao.get('my', 0),
                                             tiros, particulas, flashes, granadas)
                    elif act == 'classe_special':
                        _aplicar_special_host(j, acao.get('tipo'))
                cliente.send_minigame_action(_construir_snapshot())
            else:
                if estado == "FIGHT" and jogador_humano.vivo:
                    cliente.send_minigame_action({
                        'action': 'classe_input',
                        'x': jogador_humano.x, 'y': jogador_humano.y,
                        'mx': jogador_humano.mira_x, 'my': jogador_humano.mira_y,
                    })
                ultimo_snap = None
                for acao in cliente.get_minigame_actions():
                    if acao.get('action') == 'classe_state':
                        ultimo_snap = acao
                if ultimo_snap:
                    _aplicar_snapshot(ultimo_snap)

        # ========== CAMERA ==========
        if jogador_humano.vivo:
            cam_x, cam_y = _atualizar_camera(jogador_humano, cam_x, cam_y)
        else:
            vivos = [j for j in jogadores if j.vivo]
            if vivos:
                cam_x, cam_y = _atualizar_camera(vivos[0], cam_x, cam_y)

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
        _desenhar_arena(tela, cam_x, cam_y, tempo)

        for j in jogadores:
            if j.vivo:
                eh_local = (j is jogador_humano)
                j.desenhar(tela, fonte_nomes, cam_x, cam_y,
                           eh_local=eh_local, show_hp=(estado == "FIGHT"))

        # Balas
        if host_autoritativo:
            lista_balas = [(t.x, t.y, t.raio, t.cor) for t in tiros]
        else:
            lista_balas = tiros_render
        for bx, by, braio, bcor in lista_balas:
            sx = int(bx - cam_x)
            sy = int(by - cam_y)
            if -20 <= sx <= LARGURA + 20 and -20 <= sy <= ALTURA_JOGO + 20:
                pygame.draw.circle(tela, (0, 0, 0), (sx, sy), int(braio) + 2)
                pygame.draw.circle(tela, bcor, (sx, sy), int(braio))

        # Granadas
        if host_autoritativo:
            for g in granadas:
                g.desenhar(tela, cam_x, cam_y)
        else:
            for gx, gy, ga in granadas_render:
                _desenhar_granada(tela, gx, gy, ga, cam_x, cam_y)

        for p in particulas:
            px = int(p.x - cam_x)
            py = int(p.y - cam_y)
            if 0 <= px <= LARGURA and 0 <= py <= ALTURA_JOGO:
                pygame.draw.circle(tela, p.cor, (px, py), max(1, int(p.tamanho)))

        for f in flashes:
            fx = int(f['x'] - cam_x)
            fy = int(f['y'] - cam_y)
            if f['raio'] > 0 and -60 <= fx <= LARGURA + 60 and -60 <= fy <= ALTURA_JOGO + 60:
                raio = f['raio']
                alpha = min(255, int(f['vida'] * 22))
                flash_surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (*f['cor'], alpha), (raio, raio), raio)
                tela.blit(flash_surf, (fx - raio, fy - raio))

        if estado == "FIGHT":
            vivos_n = len([j for j in jogadores if j.vivo])
            _desenhar_hud(tela, jogador_humano, fonte_peq, vivos_n, rodada_atual, tempo)

        if estado in ("FIGHT", "COUNTDOWN"):
            _desenhar_minimap(tela, jogadores, jogador_humano, cam_x, cam_y)

        # ========== OVERLAYS ==========
        # Cursor visível só na escolha de classe (usa mouse); no jogo usa a mira
        pygame.mouse.set_visible(estado == "CLASS_SELECT")

        if estado == "CLASS_SELECT":
            mp = convert_mouse_position(pygame.mouse.get_pos())
            _desenhar_class_select(tela, cards_classe, sel_classe, mp,
                                   fonte_grande, fonte_media, fonte_peq, tempo, host_autoritativo)

        if estado == "INTRO" and tempo_no_estado > 400:
            _desenhar_roleta(tela, jogadores, fonte_media, fonte_peq, tempo_no_estado)

        if estado == "COUNTDOWN":
            seg = 3 - tempo_no_estado // 1000
            cd_text = str(seg) if seg > 0 else "LUTEM!"
            cd_cor = AMARELO if seg > 0 else VERMELHO
            cd_s = fonte_countdown.render(cd_text, True, cd_cor)
            tela.blit(cd_s, (LARGURA // 2 - cd_s.get_width() // 2,
                             ALTURA_JOGO // 2 - cd_s.get_height() // 2))

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
            msg_s = fonte_grande.render(msg, True, cor_msg)
            tela.blit(msg_s, (LARGURA // 2 - msg_s.get_width() // 2,
                              ALTURA_JOGO // 2 - msg_s.get_height() // 2))

        if estado == "SCOREBOARD":
            _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_score, fonte_peq,
                                 tempo, scoreboard_start)

        if alpha_fade > 0:
            fade_surf = pygame.Surface((LARGURA, ALTURA_JOGO))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha_fade)
            tela.blit(fade_surf, (0, 0))

        if estado == "INTRO" and tempo_no_estado > 500:
            alpha_t = min(255, int((tempo_no_estado - 500) * 0.5))
            titulo = fonte_grande.render("BATALHA DE CLASSES", True, (180, 240, 240))
            titulo.set_alpha(alpha_t)
            tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 70))
            sub = fonte_media.render("Todos contra todos!", True, (150, 200, 200))
            sub.set_alpha(alpha_t)
            tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 122))

        if estado in ("FIGHT", "COUNTDOWN"):
            mp = convert_mouse_position(pygame.mouse.get_pos())
            desenhar_mira(tela, mp, (mira_surface, mira_rect))

        present_frame()
        relogio.tick(FPS)
