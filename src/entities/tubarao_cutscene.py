#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mini cutscene do Tubarão – fases 26+.

Fluxo:
  1. tubarao_pula   – IN-GAME: shark sobe rápido, passa pelo jogador (engole)
  2. engolir        – IN-GAME: flash + jogador some
  3. tubarao_sobe   – IN-GAME: shark sobe para fora da tela
  4. fade_praia     – fade para preto
  5. praia          – shark oscila, pula e cospe player para cima
  6. camera_sobe    – câmera sobe: praia sai, gradiente vira espaço
  7. concluida      – cutscene termina; caller inicia FaseEspacoTubarao (gameplay real)
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import criar_gradiente, criar_estrelas
from src.utils.display_manager import present_frame
from src.game.fase_base import FaseBase


# ---------------------------------------------------------------------------
# Parâmetros do arco arco-íris
# ---------------------------------------------------------------------------
ARC_BASE_Y  = int(ALTURA_JOGO * 0.75)
ARC_HEIGHT  = int(ALTURA_JOGO * 0.55)


def arco_y(x_prog: float) -> float:
    """Posição Y do arco para progresso x ∈ [0, 1]."""
    return ARC_BASE_Y - math.sin(x_prog * math.pi) * ARC_HEIGHT


# ---------------------------------------------------------------------------
# Desenho do tubarão
# ---------------------------------------------------------------------------

def _desenhar_tubarao_surf(L: int, boca_aberta: bool = False) -> pygame.Surface:
    H  = L // 3
    sw = L * 3 + 20
    sh = H * 6 + 20
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    ox, oy = sw // 2, sh // 2

    C  = (65,  95, 125);  CL = (95, 135, 170);  CB = (205, 210, 215)
    CD = (38,  58,  78);  CF = (50,  75, 105);  CG = (170,  40,  40);  CT = (245, 245, 240)

    pygame.draw.polygon(surf, C, [
        (ox-L//2+H//3, oy+H//6),(ox-L//2-H//3, oy),(ox-L//2+H//3, oy-H//6),
        (ox-L//4, oy-H//2),(ox, oy-H//2+2),(ox+L//4, oy-H//2+4),
        (ox+L//2-H//4, oy-H//4),(ox+L//2+H//5, oy-H//8),(ox+L//2+H//3, oy),
        (ox+L//2+H//5, oy+H//8),(ox+L//2-H//4, oy+H//4),
        (ox+L//4, oy+H//2-2),(ox, oy+H//2-1),(ox-L//4, oy+H//2-3),
    ])
    pygame.draw.polygon(surf, CB, [
        (ox+L//2+H//3, oy),(ox+L//2+H//5, oy+H//8),(ox+L//2-H//4, oy+H//4),
        (ox+L//4, oy+H//2-2),(ox, oy+H//2-1),(ox-L//4, oy+H//2-3),(ox-L//4, oy+H//6),
    ])
    for i in range(3):
        pygame.draw.line(surf, CL, (ox-L//4+i*10, oy-H//2+2), (ox+L//4-i*5, oy-H//2+5), 2)

    pygame.draw.polygon(surf, CD, [(ox-L//2+H//3,oy-H//6),(ox-L//2-H//3,oy),(ox-L//2-H//2-H//3,oy-H-H//3),(ox-L//2-H//8,oy-H//4)])
    pygame.draw.polygon(surf, CF, [(ox-L//2+H//3,oy-H//6),(ox-L//2-H//2-H//8,oy-H+H//4),(ox-L//2-H//8,oy-H//4)])
    pygame.draw.polygon(surf, CD, [(ox-L//2+H//3,oy+H//6),(ox-L//2-H//3,oy),(ox-L//2-H//2,oy+H+H//3),(ox-L//2-H//8,oy+H//4)])
    pygame.draw.polygon(surf, CF, [(ox-L//2+H//3,oy+H//6),(ox-L//2-H//2+H//8,oy+H-H//4),(ox-L//2-H//8,oy+H//4)])

    pygame.draw.polygon(surf, CD, [(ox-L//6,oy-H//2+2),(ox-L//3,oy-H//2-H-H//3),(ox,oy-H//2+2)])
    pygame.draw.polygon(surf, CF, [(ox-L//6,oy-H//2+2),(ox-L//3+H//8,oy-H//2-H+H//4),(ox-L//10,oy-H//2+2)])
    pygame.draw.line(surf, CL, (ox-L//6+2,oy-H//2+2), (ox-L//3+H//6,oy-H//2-H//2), 1)

    pygame.draw.polygon(surf, CD, [(ox+L//5,oy+2),(ox,oy+H//2-2),(ox-L//8,oy+H//2),(ox-L//6,oy+H//6)])
    pygame.draw.polygon(surf, CF, [(ox+L//5,oy+2),(ox+L//20,oy+H//2-5),(ox-L//10,oy+H//6)])

    ex, ey = ox+L//3, oy-H//6
    pygame.draw.circle(surf, (28,28,38), (ex,ey), H//4)
    pygame.draw.circle(surf, (12,12,18),  (ex,ey), H//5)
    pygame.draw.circle(surf, (195,220,240), (ex-max(1,H//10),ey-max(1,H//10)), max(1,H//10))

    if boca_aberta:
        ab = H//2+8
        pygame.draw.polygon(surf, CG, [(ox+L//2+H//3,oy),(ox+L//2+H//5,oy-ab),(ox+L//2-H//4,oy-H//3),(ox+L//2+H//5,oy+ab)])
        for i in range(4):
            dx=ox+L//2+H//4-i*8; dy=oy-ab+4
            pygame.draw.polygon(surf, CT, [(dx,dy),(dx+5,dy+11),(dx+9,dy)])
        for i in range(3):
            dx=ox+L//2+H//4-i*8-4; dy=oy+ab-4
            pygame.draw.polygon(surf, CT, [(dx,dy),(dx+5,dy-9),(dx+9,dy)])
    else:
        pygame.draw.line(surf, CD, (ox+L//2+H//3,oy-2), (ox+L//2-H//4,oy-H//3+2), 2)
        pygame.draw.line(surf, CD, (ox+L//2+H//3,oy+2), (ox+L//2-H//4,oy+H//4-2), 2)

    pygame.draw.line(surf, CD, (ox-L//3,oy-H//8), (ox+L//3,oy-H//8), 1)
    pygame.draw.line(surf, CD, (ox-L//4,oy-H//2+3), (ox+L//4,oy-H//2+5), 3)
    return surf


def desenhar_tubarao(tela, cx, cy, tamanho, angulo, boca_aberta=False):
    surf = _desenhar_tubarao_surf(tamanho, boca_aberta)
    rot  = pygame.transform.rotate(surf, -math.degrees(angulo))
    tela.blit(rot, rot.get_rect(center=(int(cx), int(cy))))


# ---------------------------------------------------------------------------
# Fase real do espaço (gameplay dentro do loop da fase)
# ---------------------------------------------------------------------------

class FaseEspacoTubarao(FaseBase):
    """
    Mini-fase do espaço usada após a cutscene do tubarão.
    Herda FaseBase para ter toda a lógica de gameplay (tiros, armas, IA etc.).
    O jogador é o mesmo objeto da fase principal; saí pela direita para terminar.
    """

    def __init__(self, tela, relogio, jogador_original, grad_espaco, estrelas,
                 inimigos, fonte_titulo, fonte_normal):
        # numero_fase=1 → tema estrelas brancas padrão, sem espinhos/relâmpagos
        super().__init__(tela, relogio, 1, grad_espaco,
                         fonte_titulo, fonte_normal,
                         pos_jogador=(50, ALTURA_JOGO // 2))

        # Substituir o jogador dummy pelo jogador real, posicionado na entrada
        self.jogador         = jogador_original
        self.jogador.x       = 50
        self.jogador.y       = ALTURA_JOGO // 2
        self.jogador.rect.x  = 50
        self.jogador.rect.y  = ALTURA_JOGO // 2
        # Breve invulnerabilidade para não morrer imediatamente ao aparecer
        self.jogador.invulneravel         = True
        self.jogador.duracao_invulneravel = 90   # ~1.5 s a 60 fps

        # Pular tela de introdução e congelamento
        self.mostrando_inicio  = False
        self.em_congelamento   = False
        self.fade_in           = 180   # fade-in rápido ao entrar
        self.contador_inicio   = 0
        self.tempo_congelamento = 0

        # Substituir estrelas pelas da cutscene (já animadas)
        self.estrelas  = estrelas

        # Inimigos do espaço
        self.inimigos  = inimigos
        self.tempo_movimento_inimigos = [0] * len(inimigos)
        self.intervalo_movimento      = 350

    def executar_espaco(self):
        """Loop real de gameplay no espaço."""
        from src.entities.inimigo_ia import atualizar_IA_inimigo
        from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos

        self._caindo         = False
        self._queda_scroll   = float(ALTURA_JOGO)
        self._queda_pj_x     = float(LARGURA // 2)
        self._queda_pj_y     = float(ALTURA_JOGO // 2)
        self._queda_pj_vy    = 0.0
        self._queda_splash   = []
        self._queda_splashado = False
        self._queda_timer    = 0
        self._mar_y_queda    = ALTURA_JOGO * 0.55

        while True:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse   = self.obter_pos_mouse()

            resultado = self.processar_eventos()
            if resultado in ("sair", "menu"):
                break

            if self.pausado:
                self.renderizar_menu_pausa()
                present_frame()
                self.relogio.tick(FPS)
                continue

            # ── Animação de queda de volta à água ──────────────────────────
            if self._caindo:
                self._atualizar_queda()
                self._renderizar_queda(tempo_atual)
                present_frame()
                self.relogio.tick(FPS)
                if self._queda_splashado and self._queda_timer > 70:
                    break
                continue

            # ── Gameplay normal ─────────────────────────────────────────────
            if self.fade_in > 0:
                self.fade_in = max(0, self.fade_in - 8)

            if self.jogador.invulneravel and self.jogador.duracao_invulneravel != float('inf'):
                self.jogador.duracao_invulneravel -= 1
                if self.jogador.duracao_invulneravel <= 0:
                    self.jogador.invulneravel = False

            fator_tempo = self.jogador.obter_fator_tempo()

            self.atualizar_jogador(pos_mouse, tempo_atual)
            atualizar_invocacoes_com_inimigos(self.inimigos, self.particulas, self.flashes)
            self.atualizar_moedas()

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
                if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                    inimigo.y      = ALTURA_JOGO - inimigo.tamanho
                    inimigo.rect.y = inimigo.y

            self.atualizar_tiros_jogador(self.inimigos)
            self.atualizar_tiros_inimigo()
            self.processar_sabre_luz(self.inimigos)
            self.processar_granadas(self.inimigos)
            self.atualizar_efeitos_visuais()

            self.verificar_jogador_morto()
            trans = self.processar_transicoes()
            if trans == "derrota":
                break

            # Todos os inimigos mortos → cair de volta
            if self.inimigos and all(i.vidas <= 0 for i in self.inimigos):
                self._queda_pj_x = float(self.jogador.x)
                self._queda_pj_y = float(self.jogador.y)
                self._queda_pj_vy = 0.0
                self._caindo = True
                continue

            # Renderizar gameplay
            self.renderizar_fundo()
            self.renderizar_objetos_jogo(tempo_atual, self.inimigos)
            self.renderizar_hud(tempo_atual, self.inimigos)

            if self.fade_in > 0:
                fade_surf = pygame.Surface((LARGURA, ALTURA))
                fade_surf.fill((0, 0, 0))
                fade_surf.set_alpha(self.fade_in)
                self.tela.blit(fade_surf, (0, 0))

            self.renderizar_mira(pos_mouse)
            present_frame()
            self.relogio.tick(FPS)

    def _atualizar_queda(self):
        """Atualiza câmera e player durante a queda de volta à água."""
        SCROLL_VEL = ALTURA_JOGO / 100.0   # ~100 frames para chegar à praia

        if not self._queda_splashado:
            self._queda_scroll = max(0.0, self._queda_scroll - SCROLL_VEL)

            # Gravidade no player
            self._queda_pj_vy += 0.85
            self._queda_pj_y  += self._queda_pj_vy

            # Y da superfície da água na tela (aparece de baixo conforme scroll cai)
            agua_y = self._mar_y_queda + self._queda_scroll
            if self._queda_pj_y >= agua_y:
                self._queda_splashado = True
                self._queda_pj_y      = agua_y
                for _ in range(28):
                    self._queda_splash.append({
                        'x':   self._queda_pj_x + random.uniform(-90, 90),
                        'y':   agua_y,
                        'vy':  random.uniform(-11, -3),
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

        # Animar estrelas
        for est in self.estrelas:
            est[0] -= est[4]
            if est[0] < 0:
                est[0] = LARGURA
                est[1] = random.randint(0, ALTURA_JOGO)

    def _renderizar_queda(self, tempo_atual):
        """Renderiza a animação de queda (céu transicionando de espaço → praia)."""
        sc   = self._queda_scroll
        prog = sc / ALTURA_JOGO  # 1 = espaço, 0 = praia

        # Gradiente céu (mesmo sistema de _rend_camera_sobe mas com scroll decrescente)
        for y in range(0, ALTURA_JOGO, 3):
            alt_n = (ALTURA_JOGO - y + sc) / ALTURA_JOGO
            pygame.draw.rect(self.tela, TubaraoMiniCutscene._cor_ceu(alt_n), (0, y, LARGURA, 3))

        # Estrelas (somem conforme chegamos à praia)
        if prog > 0.05:
            for est in self.estrelas:
                sy = int(est[1]) + int(sc) - ALTURA_JOGO
                if -5 < sy < ALTURA_JOGO:
                    bri = int(int(est[3]) * prog)
                    tam = max(1, int(est[2]))
                    pygame.draw.circle(self.tela, (bri, bri, bri), (int(est[0]), sy), tam)

        # Mar e praia subindo de baixo
        off = int(sc)
        my  = int(self._mar_y_queda) + off
        if my < ALTURA_JOGO + 100:
            pygame.draw.rect(self.tela, (20, 50, 120), (0, my, LARGURA, ALTURA_JOGO - my + 200))
            for i in range(0, LARGURA, 50):
                wy = my + int(math.sin((tempo_atual + i * 10) / 200) * 8)
                if 0 <= wy < ALTURA_JOGO:
                    pygame.draw.line(self.tela, (40, 100, 180), (i, wy), (i + 50, wy), 4)

        # Splash
        for p in self._queda_splash:
            pygame.draw.circle(self.tela, (80, 130, 210), (int(p['x']), int(p['y'])), 5)

        # Player caindo (quadrado)
        if not self._queda_splashado:
            ts  = TAMANHO_QUADRADO
            cor = self.jogador.cor if hasattr(self.jogador, 'cor') else (40, 100, 200)
            pygame.draw.rect(self.tela, cor,
                             (int(self._queda_pj_x), int(self._queda_pj_y), ts, ts))
            pygame.draw.rect(self.tela, (255, 255, 255),
                             (int(self._queda_pj_x), int(self._queda_pj_y), ts, ts), 2)

        # Fade para preto após o splash (prepara transição de volta ao jogo)
        if self._queda_splashado:
            fade_alpha = min(255, self._queda_timer * 4)
            ov = pygame.Surface((LARGURA, ALTURA_JOGO))
            ov.fill((0, 0, 0))
            ov.set_alpha(fade_alpha)
            self.tela.blit(ov, (0, 0))

    def _desenhar_arco(self):
        """Arco-íris guia no espaço."""
        cores = [
            (255, 80,  80), (255, 160, 40), (255, 230, 40),
            ( 80, 230, 80), ( 40, 160,255), (120,  60,220),
        ]
        n = len(cores)
        steps = 60
        for s in range(steps):
            pa = s / steps
            pb = (s + 1) / steps
            pygame.draw.line(
                self.tela, cores[int(pa * n) % n],
                (int(pa * LARGURA), int(arco_y(pa))),
                (int(pb * LARGURA), int(arco_y(pb))), 2
            )


# ---------------------------------------------------------------------------
# Cutscene do tubarão (shark + praia + câmera) — sem o espaço
# ---------------------------------------------------------------------------

class TubaraoMiniCutscene:
    """
    Cutscene: shark engole o jogador in-game → praia → câmera sobe para o espaço.
    Termina quando a câmera chega ao espaço; NÃO restaura posição do jogador.
    Retorna (gradiente_espaco, estrelas) para uso pela FaseEspacoTubarao.
    """

    TAMANHO  = 110
    VEL_PULA = 32.0

    def __init__(self, jogador, tela, relogio, render_gameplay):
        self.jogador         = jogador
        self.tela            = tela
        self.relogio         = relogio
        self.render_gameplay = render_gameplay   # callable(surf, show_player=True)

        self.estado       = "tubarao_pula"
        self.tempo_estado = 0
        self.concluida    = False

        cx = jogador.x + jogador.tamanho // 2
        cy = jogador.y + jogador.tamanho // 2

        dirs = ['baixo', 'baixo', 'baixo', 'esquerda', 'direita']
        self.direcao = random.choice(dirs)
        if self.direcao == 'baixo':
            self.tx, self.ty = float(cx), float(ALTURA_JOGO + self.TAMANHO + 30)
            self.tvx, self.tvy = 0.0, -self.VEL_PULA
            self.t_ang = -math.pi / 2
        elif self.direcao == 'esquerda':
            self.tx, self.ty = float(-self.TAMANHO * 2), float(cy)
            self.tvx, self.tvy = self.VEL_PULA, 0.0
            self.t_ang = 0.0
        else:
            self.tx, self.ty = float(LARGURA + self.TAMANHO * 2), float(cy)
            self.tvx, self.tvy = -self.VEL_PULA, 0.0
            self.t_ang = math.pi

        self.t_alvo_x = float(cx);  self.t_alvo_y = float(cy)
        self.t_boca   = False;       self._passou  = False;  self._shake = 0

        # Praia
        self.sol_pos = (LARGURA // 2, ALTURA_JOGO // 5)
        self.mar_y   = ALTURA_JOGO * 0.55
        self.splash  = []
        self.tp_x    = float(LARGURA // 2)
        self.tp_y    = self.mar_y - 30.0
        self.tp_ang  = -math.pi / 2
        self.tp_vy   = 0.0
        self.t_boca_praia = False
        self.pj_x          = float(LARGURA // 2)
        self.pj_y          = self.mar_y - 30.0
        self.pj_vy         = 0.0
        self.pj_vis        = False
        self.pj_caiu_agua  = False   # não usado com player subindo, mantido por compatibilidade
        self.pj_tempo_caiu = 0
        self.praia_alpha_in = 0
        self.tp_caiu_agua  = False
        self.tp_tempo_caiu = 0

        # Espaço (para a câmera)
        self._grad_espaco  = criar_gradiente((10, 0, 30), (0, 10, 40))
        self._estrelas     = criar_estrelas(120)
        self._cam_scroll   = 0.0

        self.alpha_fade    = 0

    # ------------------------------------------------------------------ loop

    def executar(self):
        """
        Roda a cutscene até a câmera chegar ao espaço.
        NÃO restaura a posição do jogador.
        Retorna (gradiente_espaco, estrelas).
        """
        self.jogador.invulneravel         = True
        self.jogador.duracao_invulneravel = float('inf')
        if hasattr(self.jogador, 'em_cutscene'):
            self.jogador.em_cutscene = True

        self.tempo_estado = pygame.time.get_ticks()

        while not self.concluida:
            tempo_atual = pygame.time.get_ticks()
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.concluida = True
            self._atualizar(tempo_atual)
            self._renderizar(tempo_atual)
            present_frame()
            self.relogio.tick(FPS)

        return self._grad_espaco, self._estrelas

    # -------------------------------------------------------- atualizar

    def _mudar(self, novo, tempo_atual):
        self.estado = novo;  self.tempo_estado = tempo_atual

    def _atualizar(self, tempo_atual):
        t = tempo_atual - self.tempo_estado
        e = self.estado
        if   e == "tubarao_pula":  self._upd_pula(t, tempo_atual)
        elif e == "engolir":       self._upd_engolir(t, tempo_atual)
        elif e == "tubarao_sobe":  self._upd_sobe(t, tempo_atual)
        elif e == "fade_praia":    self._upd_fade(t, tempo_atual, "praia", 500)
        elif e == "praia":         self._upd_praia(t, tempo_atual)
        elif e == "camera_sobe":   self._upd_camera_sobe(t, tempo_atual)
        elif e == "concluida":     self.concluida = True

    def _upd_pula(self, t, tempo_atual):
        self.tx += self.tvx;  self.ty += self.tvy
        if self._shake > 0:
            self._shake -= 1
        if not self._passou:
            if math.hypot(self.tx - self.t_alvo_x, self.ty - self.t_alvo_y) < self.TAMANHO * 0.85:
                self._passou = True;  self.t_boca = True;  self._shake = 10
                self._mudar("engolir", tempo_atual);  return
        if self.tx < -350 or self.tx > LARGURA+350 or self.ty < -350 or self.ty > ALTURA_JOGO+350:
            self._mudar("engolir", tempo_atual)

    def _upd_engolir(self, t, tempo_atual):
        self.t_boca = True;  self.tx += self.tvx;  self.ty += self.tvy
        if t >= 250:
            self.tvx = 0.0;  self.tvy = -self.VEL_PULA;  self.t_ang = -math.pi/2
            self._mudar("tubarao_sobe", tempo_atual)

    def _upd_sobe(self, t, tempo_atual):
        self.tx += self.tvx;  self.ty += self.tvy;  self.t_boca = False
        if self.ty < -self.TAMANHO * 2:
            self._mudar("fade_praia", tempo_atual);  self.alpha_fade = 0

    def _upd_fade(self, t, tempo_atual, proximo, duracao):
        self.alpha_fade = min(255, int(255 * t / duracao))
        if t >= duracao:
            self.alpha_fade = 0;  self._mudar(proximo, tempo_atual)
            if proximo == "praia":
                self.tp_x=float(LARGURA//2); self.tp_y=self.mar_y-30.0
                self.tp_ang=-math.pi/2; self.tp_vy=0.0; self.t_boca_praia=False
                self.pj_x=float(LARGURA//2); self.pj_y=self.mar_y-30.0
                self.pj_vy=0.0; self.pj_vis=False; self.splash=[]
                self.pj_caiu_agua=False; self.pj_tempo_caiu=0
                self.tp_caiu_agua=False; self.tp_tempo_caiu=0
                self.praia_alpha_in = 255   # fade-in da cena praia

    def _upd_praia(self, t, tempo_atual):
        # Fade-in da cena
        if self.praia_alpha_in > 0:
            self.praia_alpha_in = max(0, self.praia_alpha_in - 14)

        if t < 700:
            self.tp_y = self.mar_y - 30.0 + math.sin(t / 90) * 16
            self.t_boca_praia = False
        elif t < 1000:
            prog = (t - 700) / 300
            self.tp_y = (self.mar_y - 30.0) - prog * 200
            self.t_boca_praia = prog > 0.7
            if prog > 0.7 and not self.pj_vis:
                self.pj_vis = True
                self.pj_x = self.tp_x;  self.pj_y = self.tp_y - 20.0
                self.pj_vy = -22.0   # player sobe rápido rumo ao espaço
                for _ in range(20):
                    self.splash.append({'x': self.tp_x+random.uniform(-70,70),
                                        'y': self.mar_y, 'vy': random.uniform(-9,-2),
                                        'vida': 45, 'cor': (80,130,210)})
        else:
            # Tubarão cai devagar de volta à água
            if not self.tp_caiu_agua:
                self.tp_vy += 0.35          # aceleração suave
                self.tp_y  += self.tp_vy
                self.t_boca_praia = False
                if self.tp_y >= self.mar_y:
                    self.tp_caiu_agua  = True
                    self.tp_tempo_caiu = tempo_atual
                    self.tp_y          = self.mar_y
                    for _ in range(30):
                        self.splash.append({'x': self.tp_x + random.uniform(-90, 90),
                                            'y': self.mar_y, 'vy': random.uniform(-12, -4),
                                            'vida': 60, 'cor': (80,130,210)})

        # Player sobe direto para o espaço (sem retorno)
        if self.pj_vis:
            self.pj_vy += 0.25       # levíssima gravidade para arco bonito
            self.pj_y  += self.pj_vy

        for p in self.splash[:]:
            p['y'] += p['vy'];  p['vy'] += 0.35;  p['vida'] -= 1
            if p['vida'] <= 0: self.splash.remove(p)

        # Câmera sobe depois que o tubarão cai na água e uma pausa breve
        if self.tp_caiu_agua and tempo_atual - self.tp_tempo_caiu > 1000:
            self._cam_scroll = 0.0;  self._mudar("camera_sobe", tempo_atual)

    def _upd_camera_sobe(self, t, tempo_atual):
        DUR = 1400
        self._cam_scroll = min(float(ALTURA_JOGO), ALTURA_JOGO * t / DUR)
        for est in self._estrelas:
            est[0] -= est[4]
            if est[0] < 0:
                est[0] = LARGURA;  est[1] = random.randint(0, ALTURA_JOGO)
        if t >= DUR:
            self._cam_scroll = float(ALTURA_JOGO)
            self._mudar("concluida", tempo_atual)

    # -------------------------------------------------------- renderizar

    def _renderizar(self, tempo_atual):
        t = tempo_atual - self.tempo_estado
        e = self.estado

        if e in ("tubarao_pula", "engolir", "tubarao_sobe"):
            sp      = e in ("engolir", "tubarao_sobe")
            hud_on  = False   # HUD nunca aparece durante a cutscene
            ox, oy = (random.randint(-6,6), random.randint(-6,6)) if self._shake > 0 else (0,0)
            if ox or oy:
                tmp = pygame.Surface((LARGURA, ALTURA))
                self.render_gameplay(tmp, show_player=not sp, show_hud=hud_on)
                self.tela.blit(tmp, (ox, oy))
            else:
                self.render_gameplay(self.tela, show_player=not sp, show_hud=hud_on)
            desenhar_tubarao(self.tela, self.tx+ox, self.ty+oy, self.TAMANHO, self.t_ang, self.t_boca)
            if e == "engolir":
                fa = max(0, 160 - int(160 * t / 250))
                fs = pygame.Surface((LARGURA, ALTURA_JOGO)); fs.fill((200,240,255)); fs.set_alpha(fa)
                self.tela.blit(fs, (0, 0))

        elif e == "fade_praia":
            self.render_gameplay(self.tela, show_player=False, show_hud=False)
            self._overlay(self.alpha_fade)

        elif e == "praia":
            self._rend_praia(tempo_atual)

        elif e == "camera_sobe":
            self._rend_camera_sobe(tempo_atual)

    def _rend_praia(self, tempo_atual):
        self.tela.fill((135, 206, 250))
        sx, sy = self.sol_pos
        pygame.draw.circle(self.tela, (255,255,100), (sx,sy), 60)
        for i in range(3):
            r=75+i*20; bs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(bs,(255,255,150,max(0,28-i*9)),(r,r),r); self.tela.blit(bs,(sx-r,sy-r))
        for i in range(12):
            a=i*math.pi/6+tempo_atual/2000
            pygame.draw.line(self.tela,(255,235,60),(sx,sy),(sx+int(math.cos(a)*90),sy+int(math.sin(a)*90)),2)
        my=int(self.mar_y)
        pygame.draw.rect(self.tela,(20,50,120),(0,my,LARGURA,ALTURA_JOGO-my+100))
        for i in range(0,LARGURA,50):
            wy=my+int(math.sin((tempo_atual+i*10)/200)*8)
            pygame.draw.line(self.tela,(40,100,180),(i,wy),(i+50,wy),4)
        for p in self.splash:
            pygame.draw.circle(self.tela,p['cor'],(int(p['x']),int(p['y'])),5)
        if not self.tp_caiu_agua:
            desenhar_tubarao(self.tela,int(self.tp_x),int(self.tp_y),self.TAMANHO,self.tp_ang,self.t_boca_praia)
        if self.pj_vis and not self.pj_caiu_agua:
            ts=TAMANHO_QUADRADO; cor=self.jogador.cor if hasattr(self.jogador,'cor') else AZUL
            pygame.draw.rect(self.tela,cor,(int(self.pj_x),int(self.pj_y),ts,ts))
            pygame.draw.rect(self.tela,(255,255,255),(int(self.pj_x),int(self.pj_y),ts,ts),2)
        if self.praia_alpha_in > 0:
            self._overlay(self.praia_alpha_in)

    @staticmethod
    def _cor_ceu(alt_n):
        KF = [(0.00,(135,206,250)),(0.35,(80,145,225)),(0.60,(35,70,165)),
              (0.85,(15,25,95)),(1.15,(10,8,50)),(1.60,(10,0,30))]
        for i in range(len(KF)-1):
            t0,c0=KF[i]; t1,c1=KF[i+1]
            if alt_n<=t1:
                t=max(0.0,min(1.0,(alt_n-t0)/(t1-t0)))
                return (int(c0[0]+(c1[0]-c0[0])*t),int(c0[1]+(c1[1]-c0[1])*t),int(c0[2]+(c1[2]-c0[2])*t))
        return KF[-1][1]

    def _rend_camera_sobe(self, tempo_atual):
        sc   = self._cam_scroll
        prog = sc / ALTURA_JOGO
        # Gradiente de céu
        for y in range(0, ALTURA_JOGO, 3):
            alt_n = (ALTURA_JOGO - y + sc) / ALTURA_JOGO
            pygame.draw.rect(self.tela, self._cor_ceu(alt_n), (0, y, LARGURA, 3))
        # Estrelas de cima
        for est in self._estrelas:
            sy = int(est[1]) + int(sc) - ALTURA_JOGO
            if -5 < sy < ALTURA_JOGO:
                bri = int(int(est[3]) * prog);  tam = max(1, int(est[2]))
                pygame.draw.circle(self.tela, (bri,bri,bri), (int(est[0]), sy), tam)
        # Praia descendo
        off = int(sc)
        sx, sy0 = self.sol_pos;  sy = sy0 + off
        if sy < ALTURA_JOGO + 150:
            for i in range(12):
                a=i*math.pi/6+tempo_atual/2000
                pygame.draw.line(self.tela,(255,235,60),(sx,sy),(sx+int(math.cos(a)*80),sy+int(math.sin(a)*80)),2)
            pygame.draw.circle(self.tela,(255,255,100),(sx,sy),55)
        my=int(self.mar_y)+off
        if my < ALTURA_JOGO+100:
            pygame.draw.rect(self.tela,(20,50,120),(0,my,LARGURA,ALTURA_JOGO-my+200))
            for i in range(0,LARGURA,50):
                wy=my+int(math.sin((tempo_atual+i*10)/200)*8)
                if 0<=wy<ALTURA_JOGO:
                    pygame.draw.line(self.tela,(40,100,180),(i,wy),(i+50,wy),4)
        desenhar_tubarao(self.tela,int(self.tp_x),int(self.tp_y)+off,self.TAMANHO,self.tp_ang,False)

    def _overlay(self, alpha):
        ov=pygame.Surface((LARGURA,ALTURA_JOGO)); ov.fill((0,0,0)); ov.set_alpha(alpha)
        self.tela.blit(ov,(0,0))


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def executar_cutscene_tubarao(tela, relogio, jogador, render_gameplay,
                               fonte_titulo, fonte_normal, numero_fase=26):
    """
    Executa:
      1. Cutscene (shark + praia + câmera)
      2. Minijogo do espaço (específico por fase, via NivelFactory)
    Restaura posição do jogador ao final.
    """
    from src.game.nivel_factory import NivelFactory

    jog_x0, jog_y0 = jogador.x, jogador.y

    # 1. Cutscene
    cutscene = TubaraoMiniCutscene(jogador, tela, relogio, render_gameplay)
    grad_espaco, estrelas = cutscene.executar()

    # 2. Minijogo do espaço (retorna None se a fase não tiver minijogo configurado)
    minijogo = NivelFactory.criar_minijogo_espaco(
        numero_fase, tela, relogio, jogador,
        grad_espaco, estrelas, fonte_titulo, fonte_normal
    )

    morreu_no_espaco = False
    if minijogo is not None:
        resultado = minijogo.executar_espaco()
        morreu_no_espaco = (resultado == 'morreu')
        minijogo.limpar()

    # 3. Restaurar jogador
    jogador.x      = jog_x0;  jogador.y      = jog_y0
    jogador.rect.x = jog_x0;  jogador.rect.y = jog_y0
    if hasattr(jogador, 'em_cutscene'):
        jogador.em_cutscene = False

    if morreu_no_espaco:
        # Deixa vidas = 0 para a fase principal detectar a derrota normalmente
        jogador.vidas                = 0
        jogador.invulneravel         = False
        jogador.duracao_invulneravel = 0
    else:
        jogador.invulneravel         = False
        jogador.duracao_invulneravel = 0
        # Fade de preto → jogo (sem HUD para não aparecer abruptamente)
        ov = pygame.Surface((LARGURA, ALTURA_JOGO))
        ov.fill((0, 0, 0))
        for alpha in range(255, -1, -10):
            render_gameplay(tela, show_hud=False)
            if alpha > 0:
                ov.set_alpha(alpha)
                tela.blit(ov, (0, 0))
            present_frame()
            relogio.tick(FPS)
