#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minigame Aim - Tiro ao Alvo com turnos.
8 jogadores (humanos + bots), InimigoMisterioso entrega Desert Eagle via telecinese.
5 alvos moveis de dificuldade progressiva, 5 balas por turno.
"""

import pygame
import math
import random
from src.config import *
from src.entities.tiro import Tiro
from src.entities.particula import Particula, criar_explosao
from src.entities.misterioso_cutscene import InimigoMisterioso
from src.weapons.desert_eagle import desenhar_desert_eagle, criar_efeito_disparo_desert_eagle
from src.utils.visual import criar_gradiente, criar_estrelas, desenhar_estrelas, criar_mira, desenhar_mira
from src.utils.display_manager import present_frame, convert_mouse_position

# ============================================================
#  CONSTANTES
# ============================================================

TAM_JOGADOR = 30
TAM_MISTERIOSO = int(TAMANHO_QUADRADO * 1.2)

# Paleta de cores (mesma do lobby)
PALETA_CORES = [
    AZUL, VERMELHO, VERDE, AMARELO, CIANO, ROXO, LARANJA, (255, 105, 180)
]

# Configuracao dos 5 alvos (facil embaixo perto do jogador, dificil em cima longe)
ALVOS_CONFIG = [
    {'cor': VERMELHO,  'velocidade': 1.5, 'tamanho': 40, 'y_offset': 460},
    {'cor': LARANJA,   'velocidade': 2.5, 'tamanho': 36, 'y_offset': 390},
    {'cor': AMARELO,   'velocidade': 4.0, 'tamanho': 32, 'y_offset': 310},
    {'cor': VERDE,     'velocidade': 5.5, 'tamanho': 28, 'y_offset': 230},
    {'cor': CIANO,     'velocidade': 7.0, 'tamanho': 24, 'y_offset': 150},
]

# Layout
FILA_Y = ALTURA_JOGO - 80
FILA_X_INICIO = 100
FILA_ESPACO = 60
POS_TIRO_X = LARGURA // 2
POS_TIRO_Y = ALTURA_JOGO - 200
MISTERIOSO_X = FILA_X_INICIO + 8 * FILA_ESPACO + 560
MISTERIOSO_Y = FILA_Y - 10
ALVO_X_MIN = 200
ALVO_X_MAX = LARGURA - 200

# Bot AI
BOT_DELAY_MIN = 500   # ms
BOT_DELAY_MAX = 1500

# Tempos de estado
TEMPO_INTRO = 2000
TEMPO_TURN_START = 1000
TEMPO_DELIVERY = 1500
TEMPO_TURN_END = 1500
TEMPO_SCOREBOARD = 6000


# ============================================================
#  CLASSES
# ============================================================

class AlvoMovel:
    """Alvo que se move horizontalmente."""

    def __init__(self, indice, config):
        self.indice = indice
        self.tamanho = config['tamanho']
        self.cor = config['cor']
        self.velocidade = config['velocidade']
        self.y = config['y_offset']
        self.x = float(LARGURA // 2)
        self.direcao = 1 if random.random() > 0.5 else -1
        self.ativo = False
        self.acertado = False

        # Cores derivadas
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

        self.rect = pygame.Rect(int(self.x), int(self.y), self.tamanho, self.tamanho)

    def reset(self):
        self.x = float(random.randint(ALVO_X_MIN + 100, ALVO_X_MAX - 100))
        self.direcao = 1 if random.random() > 0.5 else -1
        self.ativo = False
        self.acertado = False

    def atualizar(self):
        if not self.ativo or self.acertado:
            return
        self.x += self.velocidade * self.direcao
        if self.x <= ALVO_X_MIN:
            self.x = ALVO_X_MIN
            self.direcao = 1
        elif self.x + self.tamanho >= ALVO_X_MAX:
            self.x = ALVO_X_MAX - self.tamanho
            self.direcao = -1
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def desenhar(self, tela, tempo):
        if not self.ativo or self.acertado:
            return
        ix, iy = int(self.x), int(self.y)
        tam = self.tamanho

        # Sombra
        pygame.draw.rect(tela, (15, 12, 20), (ix + 3, iy + 3, tam, tam), 0, 3)
        # Cor escura (fundo)
        pygame.draw.rect(tela, self.cor_escura, (ix, iy, tam, tam), 0, 5)
        # Cor principal
        pygame.draw.rect(tela, self.cor, (ix + 2, iy + 2, tam - 4, tam - 4), 0, 3)
        # Highlight
        pygame.draw.rect(tela, self.cor_brilhante, (ix + 4, iy + 4, 7, 7), 0, 2)

        # Numero do alvo
        fonte = pygame.font.SysFont("Arial", 14, True)
        num = fonte.render(str(self.indice + 1), True, BRANCO)
        tela.blit(num, (ix + tam // 2 - num.get_width() // 2,
                        iy + tam // 2 - num.get_height() // 2))

    def checar_colisao(self, tiro):
        if not self.ativo or self.acertado:
            return False
        return self.rect.colliderect(tiro.rect)


class JogadorAim:
    """Jogador ou bot no minigame Aim."""

    def __init__(self, nome, cor, is_bot=True, is_remote=False):
        self.nome = nome
        self.cor = cor
        self.is_bot = is_bot
        self.is_remote = is_remote  # Jogador humano remoto (controlado via rede)
        self.acertos = 0
        self.tiros_restantes = 5
        self.alvo_atual = 0
        self.tempo_turno = 0  # tempo em ms que levou a rodada
        self.tempo_inicio_turno = 0

        # Posicao na fila
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        # Cores derivadas
        self.cor_escura = tuple(max(0, c - 60) for c in self.cor)
        self.cor_brilhante = tuple(min(255, c + 80) for c in self.cor)

        # Bot AI
        self.bot_timer = 0
        self.bot_next_shot = 0
        self.bot_mouse_x = POS_TIRO_X
        self.bot_mouse_y = POS_TIRO_Y - 100
        # Quantos alvos o bot vai acertar nesta rodada (1 a 5)
        self.bot_alvos_acertar = random.randint(1, 5)
        # Cada bot tem seu proprio ritmo de tiro (alguns rapidos, outros lentos)
        self.bot_delay_min = random.randint(200, 800)
        self.bot_delay_max = self.bot_delay_min + random.randint(200, 800)

    def reset_turno(self):
        self.tiros_restantes = 5
        self.alvo_atual = 0
        self.acertos = 0
        self.bot_timer = 0
        self.bot_next_shot = 0
        self.tempo_inicio_turno = 0
        if self.is_bot:
            self.bot_alvos_acertar = random.randint(1, 5)

    def desenhar(self, tela, fonte, is_vez=False, pulsacao=0):
        tam = TAM_JOGADOR
        ix, iy = int(self.x), int(self.y)

        mod = 0
        if is_vez:
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
        cor_nome = (100, 255, 100) if is_vez else BRANCO
        nome_surf = fonte.render(self.nome, True, cor_nome)
        nx = ix + tam // 2 - nome_surf.get_width() // 2
        ny = iy - 16

        bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        tela.blit(bg, (nx - 3, ny - 1))
        tela.blit(nome_surf, (nx, ny))


# ============================================================
#  FUNCAO DE DESENHO DA DESERT EAGLE SIMPLES (para arma flutuando)
# ============================================================

def _desenhar_deagle_flutuante(tela, x, y, angulo, escala=1.0):
    """Desenha uma Desert Eagle flutuando (sem jogador)."""
    cor_metal_claro = (180, 180, 190)
    cor_metal_medio = (120, 120, 130)
    cor_metal_escuro = (60, 60, 70)
    cor_punho_preto = (30, 30, 35)
    cor_cano_interno = (20, 20, 25)

    tamanho_surf = 80
    surf = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
    ox, oy = 40, 40

    # Slide
    sw, sh = 34, 7
    sx = ox - 16
    sy = oy - 4
    pygame.draw.rect(surf, cor_metal_medio, (sx, sy, sw, sh), 0, 2)
    pygame.draw.line(surf, cor_metal_claro, (sx + 2, sy + 1), (sx + sw - 4, sy + 1), 2)

    # Cano
    cx, cy = sx + sw, oy
    pygame.draw.circle(surf, cor_metal_medio, (cx, cy), 3)
    pygame.draw.circle(surf, cor_cano_interno, (cx, cy), 2)

    # Frame
    fx = sx + 3
    fy = oy - 5
    pygame.draw.rect(surf, cor_metal_escuro, (fx, fy, 22, 10), 0, 2)

    # Punho
    punho_pontos = [
        (fx, oy + 2), (fx + 10, oy + 1), (fx + 8, oy + 12), (fx - 3, oy + 10)
    ]
    pygame.draw.polygon(surf, cor_punho_preto, punho_pontos)

    # Rotacionar
    angulo_graus = math.degrees(angulo)
    surf_rot = pygame.transform.rotate(surf, -angulo_graus)
    rect = surf_rot.get_rect(center=(int(x), int(y)))
    tela.blit(surf_rot, rect)


def _bezier_quadratico(p0, p1, p2, t):
    """Calcula ponto em curva bezier quadratica."""
    u = 1 - t
    x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
    y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
    return x, y


# ============================================================
#  CLASSE PRINCIPAL - JOGADOR SIMULADO (para desert eagle drawing)
# ============================================================

class _JogadorSimulado:
    """Objeto minimo que imita um jogador para desenhar_desert_eagle."""
    def __init__(self, x, y, cor):
        self.x = x
        self.y = y
        self.tamanho = TAM_JOGADOR
        self.cor = cor
        self.tempo_ultimo_tiro = 0
        self.tempo_cooldown = 300
        self.desert_eagle_ativa = True
        self.tiros_desert_eagle = 5


# ============================================================
#  LOOP PRINCIPAL DO MINIGAME
# ============================================================

def executar_minigame_aim(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal,
                          cliente, nome_jogador, customizacao):
    """
    Executa o minigame Aim.

    Args:
        tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal: pygame basics
        cliente: GameClient (pode ser None para single player)
        nome_jogador: nome do jogador local
        customizacao: dict com 'cor', 'bots', etc.
    """
    print("[AIM] Minigame Aim iniciado!")

    # --- Seed compartilhado para sincronizar random entre host e clientes ---
    seed = customizacao.get('seed')
    if seed is not None:
        random.seed(seed)
        print(f"[AIM] Usando seed compartilhado: {seed}")

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

    # --- Fundo (fase 1 style) ---
    estrelas = criar_estrelas(120)

    # --- Mira customizada ---
    pygame.mouse.set_visible(False)
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)

    # --- Criar jogadores (sempre 8) ---
    jogadores = []
    cor_local = customizacao.get('cor', AZUL)

    # Jogador humano local
    jogador_humano = JogadorAim(nome_jogador, cor_local, is_bot=False)
    jogadores.append(jogador_humano)

    # Jogadores remotos (se houver)
    remotos = {}
    if cliente:
        remotos = cliente.get_remote_players()
    n_humanos = 1 + len(remotos)

    # Adicionar jogadores remotos (humanos controlados via rede)
    pid_idx = 1
    for pid, rp in remotos.items():
        ci = (pid - 1) % len(PALETA_CORES)
        jogadores.append(JogadorAim(rp.name, PALETA_CORES[ci], is_bot=False, is_remote=True))
        pid_idx += 1

    # Preencher com bots ate 8
    nomes_bots = ["Bot Alpha", "Bot Bravo", "Bot Charlie", "Bot Delta",
                  "Bot Echo", "Bot Foxtrot", "Bot Golf", "Bot Hotel"]
    bot_idx = 0
    while len(jogadores) < 8:
        ci = len(jogadores) % len(PALETA_CORES)
        jogadores.append(JogadorAim(nomes_bots[bot_idx], PALETA_CORES[ci], is_bot=True))
        bot_idx += 1

    # Ordem aleatoria dos turnos - embaralhar a lista de jogadores diretamente
    # assim a fila ja reflete a ordem de jogo
    random.shuffle(jogadores)

    # Posicionar na fila (ja na ordem embaralhada)
    for i, j in enumerate(jogadores):
        j.x = float(FILA_X_INICIO + i * FILA_ESPACO)
        j.y = float(FILA_Y)
        j.target_x = j.x
        j.target_y = j.y

    # Ordem sequencial (jogadores ja estao embaralhados)
    ordem = list(range(8))

    # --- Misterioso ---
    misterioso = InimigoMisterioso(MISTERIOSO_X, MISTERIOSO_Y)

    # --- Alvos ---
    alvos = []
    for i, cfg in enumerate(ALVOS_CONFIG):
        alvos.append(AlvoMovel(i, cfg))

    # --- Estado ---
    estado = "INTRO"
    tempo_estado = pygame.time.get_ticks()
    turno_idx = 0
    jogador_vez = None

    # Tiros ativos
    tiros = []
    particulas = []
    flashes = []

    # Animacao de entrega
    entrega_progresso = 0.0
    entrega_arma_pos = (0, 0)

    # Pulsacao
    pulsacao = 0
    ultimo_pulso = 0

    # Fade
    alpha_fade = 255

    # Cooldown de tiro do jogador humano
    ultimo_tiro_humano = 0
    COOLDOWN_TIRO = 300

    # Resultado
    resultado_final = None

    # HUD flash messages
    hud_msg = ""
    hud_msg_fim = 0

    # Jogador simulado para desenhar desert eagle
    jogador_sim = None

    # Misterioso jogada (5% de chance)
    misterioso_joga = random.random() < 0.06
    misterioso_turno = False  # True quando eh a vez do misterioso

    # Scoreboard timer
    scoreboard_start = 0

    while True:
        tempo = pygame.time.get_ticks()
        dt = 1.0 / 60.0
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

            # Tiro do jogador humano local
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if estado == "AIMING" and jogador_vez and not jogador_vez.is_bot and not jogador_vez.is_remote:
                    if jogador_vez.tiros_restantes > 0 and tempo - ultimo_tiro_humano > COOLDOWN_TIRO:
                        ultimo_tiro_humano = tempo
                        mx, my = convert_mouse_position(pygame.mouse.get_pos())
                        _disparar_tiro(jogador_vez, mx, my, tiros, particulas, flashes)
                        # Enviar tiro para os outros jogadores via rede
                        if cliente:
                            cliente.send_minigame_action({
                                'action': 'aim_shot',
                                'mx': mx, 'my': my,
                            })

        # ========== PULSACAO ==========
        if tempo - ultimo_pulso > 100:
            ultimo_pulso = tempo
            pulsacao = (pulsacao + 1) % 12

        # ========== MAQUINA DE ESTADOS ==========

        if estado == "INTRO":
            # Fade in
            if tempo_no_estado < 500:
                alpha_fade = int(255 * (1 - tempo_no_estado / 500))
            else:
                alpha_fade = 0

            if tempo_no_estado >= TEMPO_INTRO:
                estado = "TURN_START"
                tempo_estado = tempo
                turno_idx = 0
                jogador_vez = jogadores[ordem[turno_idx]]
                jogador_vez.reset_turno()

        elif estado == "TURN_START":
            # Mover jogador da vez para posicao de tiro
            jogador_vez.target_x = float(POS_TIRO_X - TAM_JOGADOR // 2)
            jogador_vez.target_y = float(POS_TIRO_Y)

            if tempo_no_estado >= TEMPO_TURN_START:
                if misterioso_turno and jogador_vez.nome == "???":
                    # Misterioso pula delivery - ja tem a arma
                    estado = "AIMING"
                    tempo_estado = tempo
                    for a in alvos:
                        a.reset()
                    alvos[0].ativo = True
                    jogador_vez.alvo_atual = 0
                    jogador_vez.tiros_restantes = 5
                    jogador_vez.tempo_inicio_turno = tempo
                    jogador_sim = _JogadorSimulado(
                        jogador_vez.target_x, jogador_vez.target_y, jogador_vez.cor
                    )
                    jogador_vez.bot_next_shot = tempo + random.randint(jogador_vez.bot_delay_min, jogador_vez.bot_delay_max)
                else:
                    estado = "DELIVERY"
                    tempo_estado = tempo
                    entrega_progresso = 0.0

        elif estado == "DELIVERY":
            # Animacao de entrega da Desert Eagle via telecinese
            t = min(1.0, tempo_no_estado / TEMPO_DELIVERY)
            # Ease in-out
            entrega_progresso = t * t * (3 - 2 * t)

            p0 = (MISTERIOSO_X + TAM_MISTERIOSO // 2, MISTERIOSO_Y)
            p2 = (jogador_vez.target_x + TAM_JOGADOR // 2, jogador_vez.target_y)
            p1 = ((p0[0] + p2[0]) / 2, min(p0[1], p2[1]) - 120)  # Ponto de controle acima
            entrega_arma_pos = _bezier_quadratico(p0, p1, p2, entrega_progresso)

            # Particulas roxas de telecinese
            if random.random() < 0.6:
                px, py = entrega_arma_pos
                part = Particula(px + random.uniform(-8, 8), py + random.uniform(-8, 8), (180, 50, 230))
                part.velocidade_x = random.uniform(-1, 1)
                part.velocidade_y = random.uniform(-2, 0)
                part.vida = random.randint(15, 30)
                part.tamanho = random.uniform(2, 5)
                particulas.append(part)

            if tempo_no_estado >= TEMPO_DELIVERY:
                estado = "AIMING"
                tempo_estado = tempo
                # Ativar primeiro alvo
                for a in alvos:
                    a.reset()
                alvos[0].ativo = True
                jogador_vez.alvo_atual = 0
                jogador_vez.tiros_restantes = 5
                jogador_vez.tempo_inicio_turno = tempo

                # Criar jogador simulado para desenhar a arma
                jogador_sim = _JogadorSimulado(
                    jogador_vez.target_x, jogador_vez.target_y, jogador_vez.cor
                )

                if jogador_vez.is_bot:
                    jogador_vez.bot_next_shot = tempo + random.randint(jogador_vez.bot_delay_min, jogador_vez.bot_delay_max)

        elif estado == "AIMING":
            # Atualizar alvo atual
            alvo_idx = jogador_vez.alvo_atual
            if alvo_idx < len(alvos):
                alvos[alvo_idx].atualizar()

            # Atualizar jogador simulado para desert eagle (usar target pos para estabilidade)
            if jogador_sim:
                jogador_sim.x = jogador_vez.target_x
                jogador_sim.y = jogador_vez.target_y
                jogador_sim.cor = jogador_vez.cor
                jogador_sim.tiros_desert_eagle = jogador_vez.tiros_restantes

            # Processar tiros de jogadores remotos via rede
            if jogador_vez.is_remote and jogador_vez.tiros_restantes > 0 and cliente:
                for action in cliente.get_minigame_actions():
                    if action.get('action') == 'aim_shot':
                        rmx = action.get('mx', 0)
                        rmy = action.get('my', 0)
                        _disparar_tiro(jogador_vez, rmx, rmy, tiros, particulas, flashes)

            # Bot AI
            if jogador_vez.is_bot and jogador_vez.tiros_restantes > 0:
                # Misterioso so atira quando nao tem bala voando (espera acertar pra atirar de novo)
                misterioso_pode = jogador_vez.nome != "???" or len(tiros) == 0
                if misterioso_pode and tempo >= jogador_vez.bot_next_shot:
                    _bot_atirar(jogador_vez, alvos, tiros, particulas, flashes, tempo)
                    jogador_vez.bot_next_shot = tempo + random.randint(jogador_vez.bot_delay_min, jogador_vez.bot_delay_max)
                else:
                    # Bot jitter de mira
                    if alvo_idx < len(alvos) and alvos[alvo_idx].ativo:
                        a = alvos[alvo_idx]
                        jogador_vez.bot_mouse_x = a.x + a.tamanho // 2 + random.uniform(-30, 30)
                        jogador_vez.bot_mouse_y = a.y + a.tamanho // 2 + random.uniform(-20, 20)

            # Atualizar tiros
            for tiro in tiros[:]:
                tiro.atualizar()
                if tiro.fora_da_tela():
                    tiros.remove(tiro)
                    continue

                # Checar colisao com alvo atual
                if alvo_idx < len(alvos) and alvos[alvo_idx].checar_colisao(tiro):
                    # Acertou!
                    a = alvos[alvo_idx]
                    a.acertado = True
                    jogador_vez.acertos += 1

                    # Efeito de explosao
                    flash = criar_explosao(a.x + a.tamanho // 2, a.y + a.tamanho // 2,
                                          a.cor, particulas, 20)
                    flashes.append(flash)

                    tiros.remove(tiro)

                    # Proximo alvo
                    jogador_vez.alvo_atual += 1
                    if jogador_vez.alvo_atual < len(alvos):
                        alvos[jogador_vez.alvo_atual].ativo = True
                    continue

            # Checar fim do turno (so quando nao tem mais balas E nenhum tiro voando)
            turno_acabou = False
            if jogador_vez.alvo_atual >= len(alvos):
                turno_acabou = True
            elif jogador_vez.tiros_restantes <= 0 and len(tiros) == 0:
                turno_acabou = True

            if turno_acabou:
                jogador_vez.tempo_turno = tempo - jogador_vez.tempo_inicio_turno
                estado = "TURN_END"
                tempo_estado = tempo
                tiros.clear()

        elif estado == "TURN_END":
            # Mover jogador de volta pra fila (ou misterioso de volta pro canto)
            if misterioso_turno and jogador_vez.nome == "???":
                jogador_vez.target_x = float(MISTERIOSO_X)
                jogador_vez.target_y = float(MISTERIOSO_Y)
            else:
                fila_idx = ordem[turno_idx]
                jogador_vez.target_x = float(FILA_X_INICIO + fila_idx * FILA_ESPACO)
                jogador_vez.target_y = float(FILA_Y)
            jogador_sim = None

            if tempo_no_estado >= TEMPO_TURN_END:
                turno_idx += 1
                if turno_idx >= 8 and not misterioso_turno:
                    if misterioso_joga:
                        # Misterioso entra na jogada!
                        misterioso_turno = True
                        misterioso_aim = JogadorAim("???", (20, 20, 20), is_bot=True)
                        misterioso_aim.bot_alvos_acertar = 5
                        misterioso_aim.bot_delay_min = 300
                        misterioso_aim.bot_delay_max = 400
                        misterioso_aim.x = float(MISTERIOSO_X)
                        misterioso_aim.y = float(MISTERIOSO_Y)
                        misterioso_aim.target_x = float(MISTERIOSO_X)
                        misterioso_aim.target_y = float(MISTERIOSO_Y)
                        jogadores.append(misterioso_aim)
                        jogador_vez = misterioso_aim
                        jogador_vez.reset_turno()
                        jogador_vez.bot_alvos_acertar = 5
                        estado = "TURN_START"
                        tempo_estado = tempo
                    else:
                        estado = "SCOREBOARD"
                        tempo_estado = tempo
                        scoreboard_start = tempo
                elif misterioso_turno:
                    # Misterioso terminou - agora scoreboard
                    estado = "SCOREBOARD"
                    tempo_estado = tempo
                    scoreboard_start = tempo
                else:
                    estado = "TURN_START"
                    tempo_estado = tempo
                    jogador_vez = jogadores[ordem[turno_idx]]
                    jogador_vez.reset_turno()

        elif estado == "SCOREBOARD":
            if tempo_no_estado >= TEMPO_SCOREBOARD:
                estado = "FIM"
                pygame.mouse.set_visible(True)
                return None

        # ========== INTERPOLACAO DE POSICAO ==========
        for j in jogadores:
            j.x += (j.target_x - j.x) * 0.12
            j.y += (j.target_y - j.y) * 0.12

        # ========== PARTICULAS ==========
        for p in particulas[:]:
            p.atualizar()
            if p.vida <= 0:
                particulas.remove(p)

        # Flashes
        for f in flashes[:]:
            f['vida'] -= 1
            f['raio'] -= 2
            if f['vida'] <= 0:
                flashes.remove(f)

        # ========== DESENHAR ==========

        # Fundo
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
        desenhar_estrelas(tela, estrelas)

        # Linhas de demarcacao dos alvos (guias visuais)
        for i, cfg in enumerate(ALVOS_CONFIG):
            y_linha = cfg['y_offset'] + cfg['tamanho'] // 2
            alpha_l = 20 + int(10 * math.sin(tempo / 800 + i))
            cor_l = (alpha_l, alpha_l, alpha_l + 15)
            pygame.draw.line(tela, cor_l, (ALVO_X_MIN, y_linha), (ALVO_X_MAX, y_linha), 1)

        # Alvos
        for a in alvos:
            a.desenhar(tela, tempo)

        # Posicao de tiro (marca no chao)
        if estado in ("TURN_START", "DELIVERY", "AIMING"):
            pulso_marca = int(3 * math.sin(tempo / 300))
            pygame.draw.circle(tela, (50, 50, 80),
                              (POS_TIRO_X, POS_TIRO_Y + TAM_JOGADOR + 10),
                              20 + pulso_marca, 2)

        # Misterioso com aura (nao desenhar no canto se ele esta jogando)
        if not (misterioso_turno and estado in ("TURN_START", "DELIVERY", "AIMING", "TURN_END")):
            misterioso.x = MISTERIOSO_X
            misterioso.y = MISTERIOSO_Y
            misterioso.rect.x = MISTERIOSO_X
            misterioso.rect.y = MISTERIOSO_Y
            misterioso.desenhar_com_aura(tela, tempo)

        # Jogadores na fila
        for i, j in enumerate(jogadores):
            if j.nome == "???":
                # Desenhar misterioso com aura em vez do quadrado generico
                misterioso.x = int(j.x)
                misterioso.y = int(j.y)
                misterioso.rect.x = int(j.x)
                misterioso.rect.y = int(j.y)
                misterioso.desenhar_com_aura(tela, tempo)
                continue
            is_vez = (jogador_vez is j)
            j.desenhar(tela, fonte_nomes, is_vez=is_vez, pulsacao=pulsacao)

        # Arma sendo entregue (durante DELIVERY)
        if estado == "DELIVERY":
            ax, ay = entrega_arma_pos
            angulo_arma = math.atan2(
                jogador_vez.target_y - MISTERIOSO_Y,
                jogador_vez.target_x - MISTERIOSO_X
            ) * entrega_progresso
            _desenhar_deagle_flutuante(tela, ax, ay, angulo_arma)

            # Glow roxo
            glow_s = int(25 + 10 * math.sin(tempo / 200))
            glow_surf = pygame.Surface((glow_s * 2, glow_s * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (180, 50, 230, 40), (glow_s, glow_s), glow_s)
            tela.blit(glow_surf, (int(ax) - glow_s, int(ay) - glow_s))

        # Desert Eagle no jogador durante AIMING
        if estado == "AIMING" and jogador_sim:
            if jogador_vez.is_bot:
                pos_mouse = (int(jogador_vez.bot_mouse_x), int(jogador_vez.bot_mouse_y))
            else:
                pos_mouse = convert_mouse_position(pygame.mouse.get_pos())
            jogador_sim.tempo_ultimo_tiro = ultimo_tiro_humano if not jogador_vez.is_bot else jogador_vez.bot_timer
            desenhar_desert_eagle(tela, jogador_sim, pos_mouse)

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

        # Barra superior com info
        hud_bg = pygame.Surface((LARGURA, 50), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        tela.blit(hud_bg, (0, 0))

        # Titulo
        titulo_s = fonte_hud.render("AIM CHALLENGE", True, (200, 200, 255))
        tela.blit(titulo_s, (LARGURA // 2 - titulo_s.get_width() // 2, 5))

        # Turno
        if estado not in ("INTRO", "SCOREBOARD", "FIM"):
            total_turnos = 9 if misterioso_turno else 8
            turno_atual = min(turno_idx + 1, total_turnos)
            turno_s = fonte_peq.render(f"Turno {turno_atual}/{total_turnos}", True, (180, 180, 200))
            tela.blit(turno_s, (15, 8))

            if jogador_vez:
                cor_vez = (180, 0, 50) if jogador_vez.nome == "???" else jogador_vez.cor
                vez_s = fonte_peq.render(f"Vez: {jogador_vez.nome}", True, cor_vez)
                tela.blit(vez_s, (15, 26))

        # Balas restantes e acertos (durante AIMING)
        if estado == "AIMING" and jogador_vez:
            # Balas
            for i in range(5):
                bx = LARGURA - 140 + i * 22
                by = 10
                if i < jogador_vez.tiros_restantes:
                    pygame.draw.circle(tela, (255, 200, 0), (bx, by + 6), 5)
                    pygame.draw.circle(tela, (200, 150, 0), (bx, by + 6), 5, 1)
                else:
                    pygame.draw.circle(tela, (60, 60, 60), (bx, by + 6), 5, 1)

            # Acertos
            acerto_s = fonte_peq.render(f"Acertos: {jogador_vez.acertos}/5", True, VERDE)
            tela.blit(acerto_s, (LARGURA - 140, 28))

        # Instrucoes
        if estado == "AIMING" and jogador_vez and not jogador_vez.is_bot:
            inst_s = fonte_peq.render("CLICK para atirar", True, (150, 150, 170))
            tela.blit(inst_s, (LARGURA // 2 - inst_s.get_width() // 2, ALTURA_JOGO - 20))

        # ========== SCOREBOARD ==========
        if estado == "SCOREBOARD":
            _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_media, fonte_score,
                                fonte_peq, tempo, scoreboard_start)

        # ========== INTRO TEXTO ==========
        if estado == "INTRO" and tempo_no_estado > 500:
            titulo_intro = fonte_grande.render("AIM CHALLENGE", True, (255, 220, 100))
            tela.blit(titulo_intro,
                     (LARGURA // 2 - titulo_intro.get_width() // 2, ALTURA_JOGO // 2 - 60))
            sub_intro = fonte_media.render("Acerte os alvos!", True, (200, 200, 220))
            tela.blit(sub_intro,
                     (LARGURA // 2 - sub_intro.get_width() // 2, ALTURA_JOGO // 2))

        # ========== TURN_END texto ==========
        if estado == "TURN_END" and jogador_vez:
            tempo_seg = jogador_vez.tempo_turno / 1000.0
            res_s = fonte_media.render(
                f"{jogador_vez.nome}: {jogador_vez.acertos}/5 acertos - {tempo_seg:.1f}s",
                True, jogador_vez.cor
            )
            tela.blit(res_s, (LARGURA // 2 - res_s.get_width() // 2, ALTURA_JOGO // 2 - 20))

        # Fade
        if alpha_fade > 0:
            fade_surf = pygame.Surface((LARGURA, ALTURA))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha_fade)
            tela.blit(fade_surf, (0, 0))

        # ESC hint
        esc_s = fonte_peq.render("ESC: Sair", True, (80, 80, 100))
        tela.blit(esc_s, (LARGURA - 70, ALTURA_JOGO - 20))

        # Mira customizada
        mouse_mira = convert_mouse_position(pygame.mouse.get_pos())
        desenhar_mira(tela, mouse_mira, (mira_surface, mira_rect))

        present_frame()
        relogio.tick(FPS)


# ============================================================
#  FUNCOES AUXILIARES
# ============================================================

def _disparar_tiro(jogador_aim, mouse_x, mouse_y, tiros, particulas, flashes):
    """Dispara um tiro da Desert Eagle."""
    if jogador_aim.tiros_restantes <= 0:
        return

    jogador_aim.tiros_restantes -= 1

    # Usar target_pos (posicao estavel de tiro) para que bala saia de onde a arma esta visualmente
    cx = jogador_aim.target_x + TAM_JOGADOR // 2
    cy = jogador_aim.target_y + TAM_JOGADOR // 2

    dx = mouse_x - cx
    dy = mouse_y - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0:
        dx /= dist
        dy /= dist

    # Posicao da ponta do cano
    ponta_x = cx + dx * 35
    ponta_y = cy + dy * 35

    tiro = Tiro(ponta_x, ponta_y, dx, dy, jogador_aim.cor, velocidade=15)
    tiro.dano = 3
    tiro.raio = 4
    tiros.append(tiro)

    # Efeitos
    criar_efeito_disparo_desert_eagle(ponta_x, ponta_y, dx, dy, particulas)
    flashes.append({
        'x': ponta_x, 'y': ponta_y,
        'raio': 20, 'vida': 8,
        'cor': (255, 200, 0)
    })

    # Som
    try:
        from src.utils.sound import gerar_som_tiro
        som = pygame.mixer.Sound(gerar_som_tiro())
        som.set_volume(0.3)
        pygame.mixer.Channel(1).play(som)
    except:
        pass


def _prever_posicao_alvo_x(alvo, frames):
    """Simula a posicao X central do alvo apos N frames, considerando bounces nas paredes."""
    x = alvo.x
    direcao = alvo.direcao
    vel = alvo.velocidade
    tam = alvo.tamanho
    for _ in range(int(round(frames))):
        x += vel * direcao
        if x <= ALVO_X_MIN:
            x = ALVO_X_MIN
            direcao = 1
        elif x + tam >= ALVO_X_MAX:
            x = ALVO_X_MAX - tam
            direcao = -1
    return x + tam // 2


def _bot_atirar(jogador_aim, alvos, tiros, particulas, flashes, tempo):
    """Bot AI - acerta exatamente bot_alvos_acertar alvos, erra o resto."""
    alvo_idx = jogador_aim.alvo_atual
    if alvo_idx >= len(alvos):
        return
    alvo = alvos[alvo_idx]
    if not alvo.ativo:
        return

    # Centro atual do alvo
    alvo_cx = alvo.x + alvo.tamanho // 2
    alvo_cy = alvo.y + alvo.tamanho // 2

    # Calcular lead para acertar (desconta 35px do offset da ponta do cano)
    dx_dist = alvo_cx - (jogador_aim.target_x + TAM_JOGADOR // 2)
    dy_dist = alvo_cy - (jogador_aim.target_y + TAM_JOGADOR // 2)
    dist = math.sqrt(dx_dist * dx_dist + dy_dist * dy_dist)
    tempo_viagem = max(0, dist - 35) / 15.0
    lead_x = alvo.velocidade * alvo.direcao * tempo_viagem

    # Misterioso sempre acerta com precisao perfeita
    is_misterioso = jogador_aim.nome == "???"

    # Vai acertar este alvo? So se ainda nao atingiu a meta
    vai_acertar = jogador_aim.acertos < jogador_aim.bot_alvos_acertar

    if vai_acertar:
        if is_misterioso:
            # Mira perfeita - simula posicao exata do alvo com bounces nas paredes
            mx = _prever_posicao_alvo_x(alvo, tempo_viagem)
            my = alvo_cy
        else:
            # Mira com lead preciso mas com pequeno erro
            mx = alvo_cx + lead_x + random.uniform(-2, 2)
            my = alvo_cy + random.uniform(-2, 2)
    else:
        # Erra de proposito - mira longe do alvo
        mx = alvo_cx + random.choice([-1, 1]) * random.uniform(60, 120)
        my = alvo_cy + random.uniform(-40, 40)

    jogador_aim.bot_mouse_x = mx
    jogador_aim.bot_mouse_y = my
    jogador_aim.bot_timer = tempo

    _disparar_tiro(jogador_aim, mx, my, tiros, particulas, flashes)


def _desenhar_scoreboard(tela, jogadores, fonte_grande, fonte_media, fonte_score,
                          fonte_peq, tempo, start_time):
    """Desenha o scoreboard final."""
    # Fundo semi-transparente
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    tela.blit(overlay, (0, 0))

    # Titulo
    titulo = fonte_grande.render("RESULTADO", True, (255, 220, 100))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 40))

    # Ordenar por acertos (maior primeiro), desempate por tempo (menor primeiro)
    ranking = sorted(enumerate(jogadores), key=lambda x: (-x[1].acertos, x[1].tempo_turno))

    # Desenhar cada jogador
    tempo_decorrido = tempo - start_time
    y_base = 120
    for rank, (idx, j) in enumerate(ranking):
        # Animacao: cada linha aparece com delay
        delay = rank * 300
        if tempo_decorrido < delay:
            continue

        alpha_entry = min(255, int((tempo_decorrido - delay) * 2))
        y = y_base + rank * 55

        # Fundo da linha
        linha_w = 500
        linha_x = LARGURA // 2 - linha_w // 2
        linha_surf = pygame.Surface((linha_w, 45), pygame.SRCALPHA)

        if rank == 0:
            linha_surf.fill((255, 200, 0, 30))  # Destaque ouro
        elif rank == 1:
            linha_surf.fill((200, 200, 200, 20))  # Prata
        elif rank == 2:
            linha_surf.fill((180, 100, 30, 20))  # Bronze
        else:
            linha_surf.fill((40, 40, 60, 20))

        tela.blit(linha_surf, (linha_x, y))

        # Posicao
        medalhas = ["1st", "2nd", "3rd"]
        pos_text = medalhas[rank] if rank < 3 else f"{rank + 1}th"
        pos_cor = [(255, 215, 0), (200, 200, 210), (205, 127, 50)][rank] if rank < 3 else (150, 150, 160)
        pos_s = fonte_score.render(pos_text, True, pos_cor)
        tela.blit(pos_s, (linha_x + 15, y + 10))

        # Quadrado colorido do jogador
        sq_x = linha_x + 80
        sq_y = y + 8
        sq_tam = 28
        cor_esc = tuple(max(0, c - 60) for c in j.cor)
        pygame.draw.rect(tela, cor_esc, (sq_x, sq_y, sq_tam, sq_tam), 0, 4)
        pygame.draw.rect(tela, j.cor, (sq_x + 2, sq_y + 2, sq_tam - 4, sq_tam - 4), 0, 3)

        # Nome
        nome_s = fonte_score.render(j.nome, True, BRANCO)
        tela.blit(nome_s, (sq_x + sq_tam + 12, y + 10))

        # Acertos
        ac_s = fonte_peq.render(f"{j.acertos}/5 acertos", True, (180, 255, 180))
        tela.blit(ac_s, (linha_x + 280, y + 8))

        # Tempo
        tempo_s_val = j.tempo_turno / 1000.0
        tempo_s_txt = fonte_peq.render(f"{tempo_s_val:.1f}s", True, (180, 200, 255))
        tela.blit(tempo_s_txt, (linha_x + 280, y + 26))

        # Borda
        if rank < 3:
            pygame.draw.rect(tela, pos_cor, (linha_x, y, linha_w, 45), 1, 3)

    # Instrucao
    if tempo_decorrido > 3000:
        inst = fonte_peq.render("Voltando ao menu...", True, (120, 120, 140))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA_JOGO - 30))
