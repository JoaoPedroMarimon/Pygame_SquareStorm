#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minijogos do espaço — um por fase (26-30).

Para adicionar uma nova fase:
  1. Crie uma subclasse de MinijogoEspacoBase
  2. Implemente `_executar_conteudo()` → retorna 'sobreviveu'|'morreu'|'saiu'
  3. Registre em `criar_minijogo_espaco()` no NivelFactory
"""

import pygame
import math
import random
from src.config import *
from src.game.fase_base import FaseBase
from src.utils.display_manager import present_frame
from src.utils.visual import desenhar_texto


# ---------------------------------------------------------------------------
# Gradiente céu compartilhado (copiado de TubaraoMiniCutscene para evitar
# importação circular)
# ---------------------------------------------------------------------------

def _cor_ceu(alt_n):
    KF = [(0.00, (135, 206, 250)), (0.35, (80, 145, 225)),  (0.60, (35,  70, 165)),
          (0.85, (15,  25,  95)), (1.15, (10,   8,  50)),  (1.60, (10,   0,  30))]
    for i in range(len(KF) - 1):
        t0, c0 = KF[i]; t1, c1 = KF[i + 1]
        if alt_n <= t1:
            t = max(0.0, min(1.0, (alt_n - t0) / (t1 - t0)))
            return (int(c0[0] + (c1[0] - c0[0]) * t),
                    int(c0[1] + (c1[1] - c0[1]) * t),
                    int(c0[2] + (c1[2] - c0[2]) * t))
    return KF[-1][1]


# ---------------------------------------------------------------------------
# Base compartilhada
# ---------------------------------------------------------------------------

class MinijogoEspacoBase(FaseBase):
    """
    Base para todos os minijogos do espaço.
    Herda FaseBase (gameplay completo: tiros, armas, IA, partículas…).
    Subclasses implementam `_executar_conteudo()`.
    A animação de queda de volta à água é compartilhada aqui.
    """

    def __init__(self, tela, relogio, jogador_original, grad_espaco, estrelas,
                 inimigos, fonte_titulo, fonte_normal):
        super().__init__(tela, relogio, 1, grad_espaco,
                         fonte_titulo, fonte_normal,
                         pos_jogador=(LARGURA // 4, ALTURA_JOGO // 2))

        # Substitui jogador dummy pelo jogador real
        self.jogador = jogador_original
        self.jogador.x = LARGURA // 4
        self.jogador.y = ALTURA_JOGO // 2
        self.jogador.rect.x = self.jogador.x
        self.jogador.rect.y = self.jogador.y
        self.jogador.invulneravel = True
        self.jogador.duracao_invulneravel = 90   # ~1.5 s de invulnerabilidade inicial

        # Pula intro/congelamento do FaseBase
        self.mostrando_inicio   = False
        self.em_congelamento    = False
        self.contador_inicio    = 0
        self.tempo_congelamento = 0

        self.estrelas  = estrelas
        self.inimigos  = inimigos
        self.tempo_movimento_inimigos = [0] * len(inimigos)
        self.intervalo_movimento      = 350

        # Estado da queda de volta à água (usado após minijogo)
        self._mar_y_queda     = ALTURA_JOGO * 0.55
        self._queda_scroll    = float(ALTURA_JOGO)
        self._queda_pj_x      = float(LARGURA // 4)
        self._queda_pj_y      = float(ALTURA_JOGO // 2)
        self._queda_pj_vy     = 0.0
        self._queda_splash    = []
        self._queda_splashado = False
        self._queda_timer     = 0

    # ------------------------------------------------------------------
    # Ponto de entrada público
    # ------------------------------------------------------------------

    def executar_espaco(self) -> str:
        """
        Fade-in → conteúdo do minijogo → queda de volta à água.
        Retorna: 'sobreviveu' | 'morreu' | 'saiu'
        """
        # Fade-in de entrada
        for alpha in range(200, -1, -10):
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return 'saiu'
            self.renderizar_fundo()
            if alpha > 0:
                ov = pygame.Surface((LARGURA, ALTURA_JOGO))
                ov.fill((0, 0, 0))
                ov.set_alpha(alpha)
                self.tela.blit(ov, (0, 0))
            present_frame()
            self.relogio.tick(FPS)

        resultado = self._executar_conteudo()

        if resultado == 'sobreviveu':
            self._executar_queda()

        return resultado

    def _executar_conteudo(self) -> str:
        """Sobrescreva nas subclasses. Retorna 'sobreviveu'|'morreu'|'saiu'."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Animação de queda de volta à água (compartilhada por todas as fases)
    # ------------------------------------------------------------------

    def _executar_queda(self):
        self._queda_scroll    = float(ALTURA_JOGO)
        self._queda_pj_x     = float(self.jogador.x)
        self._queda_pj_y     = float(self.jogador.y)
        self._queda_pj_vy    = 0.0
        self._queda_splash   = []
        self._queda_splashado = False
        self._queda_timer    = 0

        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
            self._atualizar_queda()
            self._renderizar_queda(pygame.time.get_ticks())
            present_frame()
            self.relogio.tick(FPS)
            if self._queda_splashado and self._queda_timer > 70:
                break

    def _atualizar_queda(self):
        SCROLL_VEL = ALTURA_JOGO / 100.0

        if not self._queda_splashado:
            self._queda_scroll = max(0.0, self._queda_scroll - SCROLL_VEL)
            self._queda_pj_vy += 0.85
            self._queda_pj_y  += self._queda_pj_vy

            agua_y = self._mar_y_queda + self._queda_scroll
            if self._queda_pj_y >= agua_y:
                self._queda_splashado = True
                self._queda_pj_y = agua_y
                for _ in range(28):
                    self._queda_splash.append({
                        'x': self._queda_pj_x + random.uniform(-90, 90),
                        'y': agua_y,
                        'vy': random.uniform(-11, -3),
                        'vida': 55,
                    })
        else:
            self._queda_timer += 1

        for p in self._queda_splash[:]:
            p['y']   += p['vy']
            p['vy']  += 0.4
            p['vida'] -= 1
            if p['vida'] <= 0:
                self._queda_splash.remove(p)

        for est in self.estrelas:
            est[0] -= est[4]
            if est[0] < 0:
                est[0] = LARGURA
                est[1] = random.randint(0, ALTURA_JOGO)

    def _renderizar_queda(self, tempo_atual):
        sc   = self._queda_scroll
        prog = sc / ALTURA_JOGO

        # Gradiente de céu: espaço → praia
        for y in range(0, ALTURA_JOGO, 3):
            alt_n = (ALTURA_JOGO - y + sc) / ALTURA_JOGO
            pygame.draw.rect(self.tela, _cor_ceu(alt_n), (0, y, LARGURA, 3))

        # Estrelas somem conforme chegamos à praia
        if prog > 0.05:
            for est in self.estrelas:
                sy = int(est[1]) + int(sc) - ALTURA_JOGO
                if -5 < sy < ALTURA_JOGO:
                    bri = int(int(est[3]) * prog)
                    tam = max(1, int(est[2]))
                    pygame.draw.circle(self.tela, (bri, bri, bri), (int(est[0]), sy), tam)

        # Mar subindo de baixo
        off = int(sc)
        my  = int(self._mar_y_queda) + off
        if my < ALTURA_JOGO + 100:
            pygame.draw.rect(self.tela, (20, 50, 120), (0, my, LARGURA, ALTURA_JOGO - my + 200))
            for i in range(0, LARGURA, 50):
                wy = my + int(math.sin((tempo_atual + i * 10) / 200) * 8)
                if 0 <= wy < ALTURA_JOGO:
                    pygame.draw.line(self.tela, (40, 100, 180), (i, wy), (i + 50, wy), 4)

        # Partículas de splash
        for p in self._queda_splash:
            pygame.draw.circle(self.tela, (80, 130, 210),
                               (int(p['x']), int(p['y'])), 5)

        # Player caindo
        if not self._queda_splashado:
            ts  = TAMANHO_QUADRADO
            cor = self.jogador.cor if hasattr(self.jogador, 'cor') else (40, 100, 200)
            pygame.draw.rect(self.tela, cor,
                             (int(self._queda_pj_x), int(self._queda_pj_y), ts, ts))
            pygame.draw.rect(self.tela, (255, 255, 255),
                             (int(self._queda_pj_x), int(self._queda_pj_y), ts, ts), 2)

        # Fade para preto ao final (esconde transição de volta ao jogo)
        if self._queda_splashado:
            fade_alpha = min(220, self._queda_timer * 3)
            ov = pygame.Surface((LARGURA, ALTURA_JOGO))
            ov.fill((0, 0, 0))
            ov.set_alpha(fade_alpha)
            self.tela.blit(ov, (0, 0))


# ---------------------------------------------------------------------------
# Fase 26 — Desviar dos tiros
# ---------------------------------------------------------------------------

class MinijogoDesviarTiros(MinijogoEspacoBase):
    """
    Fase 26: linha vermelha divide a tela.
    Inimigos à direita, player à esquerda.
    Inimigos disparam; player deve sobreviver DURACAO ms.
    Matar todos os inimigos antes também conta como vitória.
    """

    DURACAO   = 15_000   # ms de sobrevivência necessária
    LINHA_X   = LARGURA // 2

    def __init__(self, tela, relogio, jogador_original, grad_espaco, estrelas,
                 inimigos, fonte_titulo, fonte_normal):
        super().__init__(tela, relogio, jogador_original, grad_espaco, estrelas,
                         inimigos, fonte_titulo, fonte_normal)

        # Posiciona inimigos no lado direito em forma de grade
        cols, linha_y_base = 2, ALTURA_JOGO // 4
        for i, inimigo in enumerate(self.inimigos):
            col = i % cols
            row = i // cols
            inimigo.x = self.LINHA_X + 100 + col * 160
            inimigo.y = linha_y_base + row * 180
            inimigo.rect.x = inimigo.x
            inimigo.rect.y = inimigo.y

    # Flags de arma que existem no jogador
    _ARMA_FLAGS = ('espingarda_ativa', 'metralhadora_ativa', 'desert_eagle_ativa',
                   'spas12_ativa', 'sniper_ativa', 'sabre_equipado', 'granada_selecionada')

    def _salvar_armas(self):
        return {f: getattr(self.jogador, f, False) for f in self._ARMA_FLAGS}

    def _restaurar_armas(self, estado):
        for f, v in estado.items():
            if hasattr(self.jogador, f):
                setattr(self.jogador, f, v)

    def _desativar_armas(self):
        for f in self._ARMA_FLAGS:
            if hasattr(self.jogador, f):
                setattr(self.jogador, f, False)

    def _executar_conteudo(self) -> str:
        from src.entities.inimigo_ia import atualizar_IA_inimigo

        estado_armas = self._salvar_armas()
        self._desativar_armas()
        tempo_inicio = pygame.time.get_ticks()

        while True:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse   = self.obter_pos_mouse()

            resultado = self.processar_eventos()
            if resultado in ("sair", "menu"):
                self._restaurar_armas(estado_armas)
                return 'saiu'

            if self.pausado:
                self.renderizar_menu_pausa()
                present_frame()
                self.relogio.tick(FPS)
                continue

            # Invulnerabilidade de entrada
            if self.jogador.invulneravel and self.jogador.duracao_invulneravel != float('inf'):
                self.jogador.duracao_invulneravel -= 1
                if self.jogador.duracao_invulneravel <= 0:
                    self.jogador.invulneravel = False

            fator_tempo = self.jogador.obter_fator_tempo()
            self.atualizar_jogador(pos_mouse, tempo_atual)

            # Garante que nenhuma arma fique ativa (player pode tentar equipar com E)
            self._desativar_armas()
            self.tiros_jogador.clear()

            # Confina player ao lado esquerdo
            limite_direita = self.LINHA_X - 10 - self.jogador.tamanho
            if self.jogador.x > limite_direita:
                self.jogador.x = limite_direita
                self.jogador.rect.x = limite_direita

            self.atualizar_moedas()

            # IA dos inimigos (confinados ao lado direito)
            for idx, inimigo in enumerate(self.inimigos):
                while len(self.tempo_movimento_inimigos) <= idx:
                    self.tempo_movimento_inimigos.append(0)
                vel_orig = inimigo.velocidade
                inimigo.velocidade *= fator_tempo
                self.tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                    inimigo, idx, self.jogador,
                    self.tiros_jogador, self.inimigos,
                    tempo_atual, self.tempo_movimento_inimigos,
                    self.intervalo_movimento, 26,
                    self.tiros_inimigo, self.movimento_x, self.movimento_y,
                    self.particulas, self.flashes
                )
                inimigo.velocidade = vel_orig
                # Impede inimigo de cruzar a linha
                if inimigo.x < self.LINHA_X + 10:
                    inimigo.x = self.LINHA_X + 10
                    inimigo.rect.x = inimigo.x

            # Cancela novamente caso a IA tenha empurrado tiros do jogador
            self.tiros_jogador.clear()

            self.atualizar_tiros_inimigo()   # tiros inimigos continuam normalmente
            self.atualizar_efeitos_visuais()

            self.verificar_jogador_morto()
            if self.processar_transicoes() == "derrota":
                self._restaurar_armas(estado_armas)
                return 'morreu'

            tempo_decorrido = tempo_atual - tempo_inicio

            # Vitória: sobreviveu o tempo todo
            if tempo_decorrido >= self.DURACAO:
                self._restaurar_armas(estado_armas)
                return 'sobreviveu'

            # ── Renderizar ──────────────────────────────────────────────
            self.renderizar_fundo()
            self._desenhar_linha_divisoria(tempo_atual)
            self.renderizar_objetos_jogo(tempo_atual, self.inimigos)
            self._desenhar_hud_minijogo(tempo_decorrido)
            self.renderizar_mira(pos_mouse)
            present_frame()
            self.relogio.tick(FPS)

    def _desenhar_linha_divisoria(self, tempo_atual):
        """Linha vermelha pulsante no centro."""
        pulse = int(abs(math.sin(tempo_atual / 220)) * 80) + 160
        cor   = (pulse, 15, 15)
        # Linha tracejada
        for y in range(0, ALTURA_JOGO, 14):
            pygame.draw.line(self.tela, cor,
                             (self.LINHA_X, y),
                             (self.LINHA_X, min(y + 9, ALTURA_JOGO)), 3)

    def _desenhar_hud_minijogo(self, tempo_decorrido):
        """Contador de sobrevivência no topo esquerdo."""
        restante = max(0, (self.DURACAO - tempo_decorrido + 999) // 1000)
        cor_txt  = (255, 100, 100) if restante <= 5 else (255, 220, 220)
        desenhar_texto(self.tela, f"SOBREVIVA  {restante}s", 28, cor_txt,
                       self.LINHA_X // 2, 28)
