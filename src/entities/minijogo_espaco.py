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


# ---------------------------------------------------------------------------
# Fase 27 — Batata Quente
# ---------------------------------------------------------------------------

class MinijogoBatataQuente(MinijogoEspacoBase):
    """
    Fase 27: Batata Quente.
    O player começa com a bomba. Inimigos fogem de quem tem a bomba.
    Ao encostar em alguém a bomba transfere. Após TEMPO_BOMBA ms explode
    matando o portador. Termina quando todos os inimigos morreram.
    """

    TEMPO_BOMBA       = 6000   # ms antes de explodir
    COOLDOWN_TRANSFER = 1200   # imunidade de re-transferência

    def __init__(self, tela, relogio, jogador_original, grad_espaco, estrelas,
                 inimigos, fonte_titulo, fonte_normal):
        super().__init__(tela, relogio, jogador_original, grad_espaco, estrelas,
                         inimigos, fonte_titulo, fonte_normal)

        # Posiciona inimigos espalhados pela arena
        _pos = [
            (int(LARGURA * 0.18), int(ALTURA_JOGO * 0.18)),
            (int(LARGURA * 0.75), int(ALTURA_JOGO * 0.18)),
            (int(LARGURA * 0.18), int(ALTURA_JOGO * 0.76)),
            (int(LARGURA * 0.75), int(ALTURA_JOGO * 0.76)),
            (int(LARGURA * 0.46), int(ALTURA_JOGO * 0.47)),
        ]
        for i, ini in enumerate(self.inimigos):
            px, py = _pos[i % len(_pos)]
            ini.x, ini.y = px, py
            ini.rect.x, ini.rect.y = px, py

        # Bomba: 'jogador' ou índice int na lista self.inimigos
        self._bomb_holder  = 'jogador'
        self._bomb_inicio  = 0   # nunca reseta — contador global
        self._bomb_recebeu = {}  # holder_key -> tempo que recebeu (cooldown de re-transfer)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _holder_cx_cy(self):
        """Centro de quem tem a bomba."""
        if self._bomb_holder == 'jogador':
            j = self.jogador
            return j.x + j.tamanho // 2, j.y + j.tamanho // 2
        h = self.inimigos[self._bomb_holder]
        return h.x + h.tamanho // 2, h.y + h.tamanho // 2

    def _transferir(self, novo_holder, tempo_atual):
        self._bomb_holder = novo_holder
        # _bomb_inicio NÃO reseta — o timer da bomba continua correndo
        self._bomb_recebeu[novo_holder] = tempo_atual

    def _pode_receber(self, holder_key, tempo_atual):
        return tempo_atual - self._bomb_recebeu.get(holder_key, 0) >= self.COOLDOWN_TRANSFER

    def _ia_fugir_de(self, inimigo, fx, fy):
        """
        Afasta o inimigo do ponto (fx, fy) com:
        - repulsão de paredes (evita ficar preso no canto)
        - finta lateral periódica (movimento mais natural)
        """
        agora = pygame.time.get_ticks()
        cx = inimigo.x + inimigo.tamanho / 2
        cy = inimigo.y + inimigo.tamanho / 2

        # Direção de fuga base
        dx, dy = cx - fx, cy - fy
        dist = math.hypot(dx, dy)
        if dist < 1:
            dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
            dist = max(1.0, math.hypot(dx, dy))
        ndx, ndy = dx / dist, dy / dist

        # Repulsão de paredes: empurra para longe das bordas
        MARGEM = 140
        wx = 0.0
        wy = 0.0
        if cx < MARGEM:
            wx += (1.0 - cx / MARGEM) * 2.8
        if cx > LARGURA - MARGEM:
            wx -= (1.0 - (LARGURA - cx) / MARGEM) * 2.8
        if cy < MARGEM:
            wy += (1.0 - cy / MARGEM) * 2.8
        if cy > ALTURA_JOGO - MARGEM:
            wy -= (1.0 - (ALTURA_JOGO - cy) / MARGEM) * 2.8

        # Finta lateral periódica
        if not hasattr(inimigo, '_bq_dodge_t'):
            inimigo._bq_dodge_t   = agora
            inimigo._bq_dodge_dir = random.choice([-1, 1])
            inimigo._bq_dodge_int = random.randint(900, 1800)

        elapsed = agora - inimigo._bq_dodge_t
        if elapsed > inimigo._bq_dodge_int:
            inimigo._bq_dodge_t   = agora
            inimigo._bq_dodge_dir = random.choice([-1, 1])
            inimigo._bq_dodge_int = random.randint(900, 1800)
            elapsed = 0

        # Finta ativa nos primeiros 260ms do intervalo
        finta = elapsed < 260
        perp_x = -ndy * inimigo._bq_dodge_dir * 1.0 if finta else 0.0
        perp_y =  ndx * inimigo._bq_dodge_dir * 1.0 if finta else 0.0

        # Combinar forças
        fx_t = ndx + wx + perp_x
        fy_t = ndy + wy + perp_y
        mag  = math.hypot(fx_t, fy_t)
        if mag < 0.01:
            return

        vel = inimigo.velocidade * 1.4
        inimigo.x = max(15, min(LARGURA - inimigo.tamanho - 15,
                                inimigo.x + fx_t / mag * vel))
        inimigo.y = max(15, min(ALTURA_JOGO - inimigo.tamanho - 15,
                                inimigo.y + fy_t / mag * vel))
        inimigo.rect.x = int(inimigo.x)
        inimigo.rect.y = int(inimigo.y)

    def _ia_perseguir(self, inimigo, tx, ty):
        """Move o inimigo em direção a (tx, ty)."""
        cx = inimigo.x + inimigo.tamanho / 2
        cy = inimigo.y + inimigo.tamanho / 2
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        vel = inimigo.velocidade * 1.2
        inimigo.x = max(10, min(LARGURA  - inimigo.tamanho - 10,
                                inimigo.x + dx / dist * vel))
        inimigo.y = max(10, min(ALTURA_JOGO - inimigo.tamanho - 10,
                                inimigo.y + dy / dist * vel))
        inimigo.rect.x = int(inimigo.x)
        inimigo.rect.y = int(inimigo.y)

    # ------------------------------------------------------------------
    # Armas (desativadas durante o minijogo)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def _executar_conteudo(self) -> str:
        tempo_atual = pygame.time.get_ticks()
        self._bomb_inicio = tempo_atual
        self._bomb_holder = 'jogador'
        self._bomb_recebeu = {'jogador': tempo_atual}
        estado_armas = self._salvar_armas()
        self._desativar_armas()

        # Vidas exclusivas do minigame (independentes da partida)
        _vidas_reais = self.jogador.vidas
        self._mg_vidas = 2

        def _sair(resultado_str):
            self._restaurar_armas(estado_armas)
            self.jogador.vidas = _vidas_reais
            return resultado_str

        while True:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse   = self.obter_pos_mouse()

            resultado = self.processar_eventos()
            if resultado in ("sair", "menu"):
                return _sair('saiu')

            if self.pausado:
                self.renderizar_menu_pausa()
                present_frame()
                self.relogio.tick(FPS)
                continue

            # Invulnerabilidade inicial
            if self.jogador.invulneravel and self.jogador.duracao_invulneravel != float('inf'):
                self.jogador.duracao_invulneravel -= 1
                if self.jogador.duracao_invulneravel <= 0:
                    self.jogador.invulneravel = False

            # Quem acabou de pegar a bomba fica parado 500ms
            _congelado_player = (self._bomb_holder == 'jogador' and
                                 tempo_atual - self._bomb_recebeu.get('jogador', 0) < 500)
            if not _congelado_player:
                self.atualizar_jogador(pos_mouse, tempo_atual)
            else:
                # Salva posição, atualiza (animações/dash/etc), restaura posição
                _px, _py = self.jogador.x, self.jogador.y
                self.atualizar_jogador(pos_mouse, tempo_atual)
                self.jogador.x, self.jogador.y = _px, _py
                self.jogador.rect.x = int(_px)
                self.jogador.rect.y = int(_py)
            self._desativar_armas()
            self.tiros_jogador.clear()
            self.atualizar_moedas()

            hcx, hcy = self._holder_cx_cy()

            # ── IA dos inimigos ─────────────────────────────────────────
            for idx, ini in enumerate(self.inimigos):
                if ini.vidas <= 0:
                    continue
                if self._bomb_holder == idx:
                    # Congelado por 500ms após receber a bomba
                    if tempo_atual - self._bomb_recebeu.get(idx, 0) < 500:
                        continue
                    # Portador: persegue entidade mais próxima para passar a bomba
                    cx = ini.x + ini.tamanho / 2
                    cy = ini.y + ini.tamanho / 2
                    alvos = []
                    jcx = self.jogador.x + self.jogador.tamanho / 2
                    jcy = self.jogador.y + self.jogador.tamanho / 2
                    alvos.append((math.hypot(jcx - cx, jcy - cy), jcx, jcy))
                    for j, outro in enumerate(self.inimigos):
                        if j != idx and outro.vidas > 0:
                            ocx = outro.x + outro.tamanho / 2
                            ocy = outro.y + outro.tamanho / 2
                            alvos.append((math.hypot(ocx - cx, ocy - cy), ocx, ocy))
                    if alvos:
                        alvos.sort()
                        _, tx, ty = alvos[0]
                        self._ia_perseguir(ini, tx, ty)
                else:
                    # Não tem bomba: foge do portador
                    self._ia_fugir_de(ini, hcx, hcy)

            # ── Transferência por contato ────────────────────────────────
            pode = self._pode_receber(self._bomb_holder, tempo_atual)
            if pode:
                if self._bomb_holder == 'jogador':
                    # Player passa para inimigo que encostar
                    for idx, ini in enumerate(self.inimigos):
                        if ini.vidas > 0 and self._pode_receber(idx, tempo_atual):
                            if self.jogador.rect.colliderect(ini.rect):
                                self._transferir(idx, tempo_atual)
                                break
                else:
                    holder_ini = self.inimigos[self._bomb_holder]
                    # Inimigo portador encosta no player
                    if self._pode_receber('jogador', tempo_atual):
                        if holder_ini.rect.colliderect(self.jogador.rect):
                            self._transferir('jogador', tempo_atual)
                    # Inimigo portador encosta em outro inimigo
                    if self._bomb_holder != 'jogador':   # pode ter mudado acima
                        for idx, ini in enumerate(self.inimigos):
                            if idx != self._bomb_holder and ini.vidas > 0:
                                if self._pode_receber(idx, tempo_atual):
                                    if holder_ini.rect.colliderect(ini.rect):
                                        self._transferir(idx, tempo_atual)
                                        break

            # ── Explosão ─────────────────────────────────────────────────
            if tempo_atual - self._bomb_inicio >= self.TEMPO_BOMBA:
                from src.entities.particula import criar_explosao
                if self._bomb_holder == 'jogador':
                    from src.entities.particula import criar_explosao as _exp
                    jex = int(self.jogador.x + self.jogador.tamanho / 2)
                    jey = int(self.jogador.y + self.jogador.tamanho / 2)
                    _exp(jex, jey, (255, 140, 0), self.particulas, 40)
                    self._mg_vidas -= 1
                    if self._mg_vidas <= 0:
                        return _sair('morreu')
                    # Sobreviveu — passa a bomba para o inimigo mais próximo
                    vivos_idx_p = [i for i, ini in enumerate(self.inimigos) if ini.vidas > 0]
                    if vivos_idx_p:
                        mais_perto_p = min(vivos_idx_p,
                                           key=lambda i: math.hypot(
                                               self.inimigos[i].x - jex,
                                               self.inimigos[i].y - jey))
                        self._transferir(mais_perto_p, tempo_atual)
                        self._bomb_inicio = tempo_atual
                else:
                    morto = self.inimigos[self._bomb_holder]
                    morto.vidas = 0
                    ex = int(morto.x + morto.tamanho / 2)
                    ey = int(morto.y + morto.tamanho / 2)
                    criar_explosao(ex, ey, (255, 140, 0), self.particulas, 40)

                    # Passa a bomba para a entidade viva mais próxima
                    vivos_idx = [i for i, ini in enumerate(self.inimigos) if ini.vidas > 0]
                    if not vivos_idx:
                        return _sair('sobreviveu')

                    # Próximo holder: inimigo mais próximo do portador morto
                    jcx = self.jogador.x + self.jogador.tamanho / 2
                    jcy = self.jogador.y + self.jogador.tamanho / 2
                    mais_perto = min(vivos_idx,
                                     key=lambda i: math.hypot(
                                         self.inimigos[i].x - jcx,
                                         self.inimigos[i].y - jcy))
                    self._transferir(mais_perto, tempo_atual)
                    self._bomb_inicio = tempo_atual

            # ── Condições de fim ─────────────────────────────────────────
            # Morte do player tratada pela bomba — não usa verificar_jogador_morto
            self.processar_transicoes()   # mantém efeitos visuais, ignora resultado

            # Única condição de vitória: todos os inimigos mortos
            if all(ini.vidas <= 0 for ini in self.inimigos):
                return _sair('sobreviveu')

            # ── Render ───────────────────────────────────────────────────
            self.atualizar_efeitos_visuais()
            self.renderizar_fundo()
            self.renderizar_objetos_jogo(tempo_atual, self.inimigos)
            self._desenhar_bomba(tempo_atual)
            self._desenhar_hud()
            self.renderizar_mira(pos_mouse)
            present_frame()
            self.relogio.tick(FPS)

    # ------------------------------------------------------------------
    # Visual
    # ------------------------------------------------------------------

    def _desenhar_bomba(self, tempo_atual):
        """Desenha o ícone de bomba + barra de tempo sobre o portador."""
        if self._bomb_holder == 'jogador':
            bx = int(self.jogador.x + self.jogador.tamanho // 2)
            by = int(self.jogador.y) - 20
        else:
            h  = self.inimigos[self._bomb_holder]
            if h.vidas <= 0:
                return
            bx = int(h.x + h.tamanho // 2)
            by = int(h.y) - 20

        restante = max(0, self.TEMPO_BOMBA - (tempo_atual - self._bomb_inicio))
        freq = 300 if restante > 2000 else (150 if restante > 1000 else 70)
        pulse = (tempo_atual // freq) % 2 == 0

        # Corpo da bomba
        cor_bomba = (255, 60, 0) if (pulse and restante < 2000) else (25, 25, 25)
        pygame.draw.circle(self.tela, cor_bomba, (bx, by), 11)
        pygame.draw.circle(self.tela, (80, 80, 80), (bx, by), 11, 2)

        # Mecha
        pygame.draw.line(self.tela, (180, 130, 0), (bx, by - 11), (bx + 7, by - 20), 2)
        # Faísca pulsante
        if pulse:
            pygame.draw.circle(self.tela, (255, 255, 80), (bx + 7, by - 20), 4)

        # Barra de tempo debaixo da bomba
        bar_w, bar_h = 44, 5
        bar_x = bx - bar_w // 2
        bar_y = by + 16
        pygame.draw.rect(self.tela, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h), 0, 2)
        prog = int(restante / self.TEMPO_BOMBA * bar_w)
        if prog > 0:
            cor_bar = ((0, 200, 60)   if restante > 3000 else
                       (255, 200, 0)  if restante > 1500 else
                       (255, 40, 40))
            pygame.draw.rect(self.tela, cor_bar, (bar_x, bar_y, prog, bar_h), 0, 2)

    def _desenhar_hud(self):
        """Contador de inimigos vivos + vidas do player no minigame."""
        vivos = sum(1 for ini in self.inimigos if ini.vidas > 0)
        desenhar_texto(self.tela, f"INIMIGOS: {vivos}", 26, (220, 220, 220),
                       LARGURA // 2, 24)
        vidas = getattr(self, '_mg_vidas', 2)
        cor_vidas = (255, 80, 80) if vidas == 1 else (220, 220, 220)
        desenhar_texto(self.tela, f"VIDAS: {vidas}", 24, cor_vidas, 80, 24)
