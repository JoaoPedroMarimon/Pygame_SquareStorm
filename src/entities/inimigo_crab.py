#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inimigo Caranguejo — fases aquáticas (26+).
Persegue o jogador; quando perto, para, telegrafeia em vermelho e dá um dash.
Causa dano ao colidir durante o dash.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado


class InimigoCrab(Quadrado):

    COOLDOWN_DASH  = 3000   # ms entre cada dash
    DUR_TELEGRAFO  = 900    # ms de aviso (linha vermelha)
    VEL_DASH       = 20.0   # px/frame durante o dash
    DUR_RECUPERAR  = 600    # ms parado após o dash
    DIST_DASH_MAX  = 420    # comprimento máximo do dash

    def __init__(self, x, y):
        cor = (200, 70, 10)
        tamanho = int(TAMANHO_QUADRADO * 1.25)
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.75
        super().__init__(x, y, tamanho, cor, velocidade)

        self.vidas     = 4
        self.vidas_max = 4
        self.tipo_crab = True
        self.angulo_crab = math.pi
        self.cor_escura  = tuple(max(0, c - 55) for c in cor)

        # Máquina de estados
        self._estado       = 'perseguindo'   # perseguindo | telegrafando | dashando | recuperando
        self._tempo_estado  = 0
        self._proximo_dash  = pygame.time.get_ticks() + self.COOLDOWN_DASH

        # Dados do dash
        self._dash_dx     = 0.0
        self._dash_dy     = 0.0
        self._dash_dist   = 0.0   # distância percorrida no dash atual
        self._alvo_x      = 0.0   # posição alvo (onde o jogador estava ao telegrafar)
        self._alvo_y      = 0.0

        # Cooldown de dano por contato (dash)
        self._tempo_ultimo_dano = 0
        self._cooldown_dano     = 800   # ms — evita spam de dano

    # ------------------------------------------------------------------
    # Lógica principal (chamada pelo inimigo_ia)
    # ------------------------------------------------------------------

    def atualizar_crab(self, jogador, particulas, flashes):
        """Atualiza a máquina de estados do caranguejo."""
        tempo_atual = pygame.time.get_ticks()
        cx = self.x + self.tamanho / 2
        cy = self.y + self.tamanho / 2
        jx = jogador.x + jogador.tamanho / 2
        jy = jogador.y + jogador.tamanho / 2

        # Dano por contato em qualquer estado
        if self.rect.colliderect(jogador.rect):
            if tempo_atual - self._tempo_ultimo_dano > self._cooldown_dano:
                self._tempo_ultimo_dano = tempo_atual
                jogador.tomar_dano()

        # Perseguindo: rastreia normalmente
        if self._estado == 'perseguindo':
            dist = math.hypot(jx - cx, jy - cy)
            if dist > 0:
                self.angulo_crab = math.atan2(jy - cy, jx - cx)
            self._mover_para(jx, jy)
            if tempo_atual >= self._proximo_dash:
                self._iniciar_telegrafo(tempo_atual, cx, cy, jx, jy)

        elif self._estado == 'telegrafando':
            # Linha e ângulo rastreiam o jogador até o momento do dash
            dist = math.hypot(jx - cx, jy - cy)
            if dist > 0:
                ndx = (jx - cx) / dist
                ndy = (jy - cy) / dist
                self.angulo_crab  = math.atan2(ndy, ndx)
                self._dash_dx     = ndx
                self._dash_dy     = ndy
                # Linha sempre ultrapassa o jogador em 90px
                self._alvo_x = jx + ndx * 90
                self._alvo_y = jy + ndy * 90

            # Dispara o dash com a direção atual (já rastreada)
            if tempo_atual - self._tempo_estado >= self.DUR_TELEGRAFO:
                # Clamp do alvo às bordas da tela
                half = self.tamanho / 2
                self._alvo_x = max(half, min(LARGURA - half, self._alvo_x))
                self._alvo_y = max(half, min(ALTURA_JOGO - half, self._alvo_y))
                self._estado = 'dashando'
                self._tempo_estado = tempo_atual
                self._dash_dist = 0.0

        elif self._estado == 'dashando':
            vel = self.VEL_DASH * jogador.obter_fator_tempo()
            cx = self.x + self.tamanho / 2
            cy = self.y + self.tamanho / 2
            dist_alvo = math.hypot(self._alvo_x - cx, self._alvo_y - cy)

            if dist_alvo <= vel:
                # Chegou ao destino — encosta no alvo
                self.x = self._alvo_x - self.tamanho / 2
                self.y = self._alvo_y - self.tamanho / 2
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)
                # Dano por contato no frame final
                if self.rect.colliderect(jogador.rect):
                    if tempo_atual - self._tempo_ultimo_dano > self._cooldown_dano:
                        self._tempo_ultimo_dano = tempo_atual
                        jogador.tomar_dano()
                self._estado = 'recuperando'
                self._tempo_estado = tempo_atual
            else:
                self.x += self._dash_dx * vel
                self.y += self._dash_dy * vel
                self.rect.x = int(self.x)
                self.rect.y = int(self.y)

                # Dano por contato
                if self.rect.colliderect(jogador.rect):
                    if tempo_atual - self._tempo_ultimo_dano > self._cooldown_dano:
                        self._tempo_ultimo_dano = tempo_atual
                        jogador.tomar_dano()

        elif self._estado == 'recuperando':
            if tempo_atual - self._tempo_estado >= self.DUR_RECUPERAR:
                self._estado      = 'perseguindo'
                self._tempo_estado = tempo_atual
                self._proximo_dash = tempo_atual + self.COOLDOWN_DASH

    def _iniciar_telegrafo(self, tempo_atual, cx, cy, jx, jy):
        # Usa o ângulo atual (já apontado para o jogador) — não atualiza mais depois
        ang = math.atan2(jy - cy, jx - cx)
        self._dash_dx = math.cos(ang)
        self._dash_dy = math.sin(ang)
        self._alvo_x  = cx + self._dash_dx * self.DIST_DASH_MAX
        self._alvo_y  = cy + self._dash_dy * self.DIST_DASH_MAX
        self._estado  = 'telegrafando'
        self._tempo_estado = tempo_atual

    def _mover_para(self, tx, ty):
        cx = self.x + self.tamanho / 2
        cy = self.y + self.tamanho / 2
        dist = math.hypot(tx - cx, ty - cy)
        if dist > 0:
            self.x += (tx - cx) / dist * self.velocidade
            self.y += (ty - cy) / dist * self.velocidade
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------

    def desenhar(self, tela, tempo_atual=None):
        if tempo_atual is None:
            tempo_atual = pygame.time.get_ticks()

        if self.invulneravel and tempo_atual % 200 < 100:
            return

        # Linha de telegrafo (antes do corpo, por baixo)
        if self._estado == 'telegrafando':
            pulse = int(abs(math.sin(tempo_atual / 90)) * 180) + 75
            cor_linha = (255, pulse // 3, pulse // 3)
            cx0 = int(self.x + self.tamanho / 2)
            cy0 = int(self.y + self.tamanho / 2)
            pygame.draw.line(tela, cor_linha,
                             (cx0, cy0),
                             (int(self._alvo_x), int(self._alvo_y)), 3)

        cx = int(self.x + self.tamanho // 2)
        cy = int(self.y + self.tamanho // 2)
        ang = self.angulo_crab
        s   = self.tamanho // 2

        cos_a = math.cos(ang)
        sin_a = math.sin(ang)

        def pt(fx, fy):
            return (int(cx + cos_a * fx - sin_a * fy),
                    int(cy + sin_a * fx + cos_a * fy))

        # Cores
        cor_uso    = self.cor
        cor_escura = self.cor_escura
        if self.efeito_dano > 0:
            cor_uso = cor_escura = BRANCO
            self.efeito_dano -= 1
        if self._estado == 'dashando' and cor_uso != BRANCO:
            cor_uso = tuple(min(255, c + 60) for c in cor_uso)

        # === SOMBRA ===
        sombra = [pt(s, 0), pt(-s*.4, -s*.8), pt(-s*.4, s*.8)]
        pygame.draw.polygon(tela, (5, 12, 22),
                            [(p[0]+4, p[1]+4) for p in sombra])

        # === TABS DA CARAPAÇA NO FUNDO (substituem a cauda do peixe) ===
        for sinal in (-1, 1):
            tab = [pt(-s*.35, sinal*s*.3),
                   pt(-s*.75, sinal*s*.55),
                   pt(-s*.55, sinal*s*.85),
                   pt(-s*.3,  sinal*s*.72)]
            pygame.draw.polygon(tela, cor_escura, tab)
            tab_inner = [pt(-s*.40, sinal*s*.38),
                         pt(-s*.65, sinal*s*.57),
                         pt(-s*.50, sinal*s*.72),
                         pt(-s*.35, sinal*s*.62)]
            pygame.draw.polygon(tela, cor_uso, tab_inner)

        # === CORPO TRIANGULAR ===
        corpo = [pt(s, 0), pt(-s*.4, -s*.8), pt(-s*.4, s*.8)]
        pygame.draw.polygon(tela, cor_escura, corpo)
        corpo_inner = [pt(s*.82, 0), pt(-s*.32, -s*.62), pt(-s*.32, s*.62)]
        pygame.draw.polygon(tela, cor_uso, corpo_inner)

        # Brilho dorsal (faixa mais clara no centro)
        brilho = [pt(s*.55, -s*.05), pt(-s*.25, -s*.48), pt(-s*.25, -s*.15)]
        pygame.draw.polygon(tela, tuple(min(255, c+45) for c in cor_uso), brilho)

        # === ANÉIS DA CARAPAÇA (substituem escamas/linha lateral) ===
        for fx in (0.35, 0.05, -0.2):
            sp = pt(fx*s, -s*.55 + abs(fx)*s*.3)
            ep = pt(fx*s,  s*.55 - abs(fx)*s*.3)
            mp = pt((fx - 0.18)*s, 0)
            escala_cor = tuple(max(0, c - 65) for c in cor_uso)
            pygame.draw.line(tela, escala_cor,
                             (int(sp[0]), int(sp[1])), (int(mp[0]), int(mp[1])), 2)
            pygame.draw.line(tela, escala_cor,
                             (int(mp[0]), int(mp[1])), (int(ep[0]), int(ep[1])), 2)

        # === PINÇAS (saem das laterais próximas ao bico, apontam para frente) ===
        for sinal in (-1, 1):
            # Braço (do corpo até a base da pinça)
            arm = [pt(s*.25, sinal*s*.58),
                   pt(s*.50, sinal*s*.40),
                   pt(s*.85, sinal*s*.95),
                   pt(s*.55, sinal*s*1.05)]
            pygame.draw.polygon(tela, cor_escura, arm)
            pygame.draw.polygon(tela, cor_uso,
                                [pt(s*.32, sinal*s*.60),
                                 pt(s*.52, sinal*s*.46),
                                 pt(s*.78, sinal*s*.93),
                                 pt(s*.58, sinal*s*1.00)])

            # Dedo de cima da pinça
            d1 = [pt(s*.85, sinal*s*.95),
                  pt(s*1.5,  sinal*s*.65),
                  pt(s*1.25, sinal*s*.72)]
            pygame.draw.polygon(tela, cor_escura, d1)

            # Dedo de baixo da pinça
            d2 = [pt(s*.85, sinal*s*.95),
                  pt(s*1.5,  sinal*s*1.25),
                  pt(s*1.25, sinal*s*1.12)]
            pygame.draw.polygon(tela, cor_escura, d2)

            # Interior da pinça
            pygame.draw.polygon(tela, cor_uso,
                                [pt(s*.90, sinal*s*.95),
                                 pt(s*1.35, sinal*s*.74),
                                 pt(s*1.35, sinal*s*1.12)])

        # === PERNAS (4 finas, 2 por lado — área do meio do corpo) ===
        for offset_x in (-0.1, -0.32):
            for sinal in (-1, 1):
                lb = pt(offset_x*s, sinal*s*.62)
                lt = pt((offset_x - 0.12)*s, sinal*s*1.32)
                pygame.draw.line(tela, cor_escura,
                                 (int(lb[0]), int(lb[1])),
                                 (int(lt[0]), int(lt[1])), 2)

        # === OLHOS (hastes curtas perto do bico) ===
        for sinal in (-1, 1):
            hb = pt(s*.65, sinal*s*.22)
            ht = pt(s*.75, sinal*s*.42)
            pygame.draw.line(tela, cor_escura,
                             (int(hb[0]), int(hb[1])), (int(ht[0]), int(ht[1])), 2)
            pygame.draw.circle(tela, (20, 8, 2),   ht, max(2, s//5))
            pygame.draw.circle(tela, (255, 220, 50), ht, max(1, s//7))

        # === BARRA DE VIDA ===
        if self.vidas < self.vidas_max:
            larg = 46
            alt  = 5
            bx   = int(self.x) + (self.tamanho - larg) // 2
            by   = int(self.y) - 14
            pygame.draw.rect(tela, (60, 0, 0), (bx, by, larg, alt), 0, 2)
            px = int((self.vidas / self.vidas_max) * larg)
            if px > 0:
                pygame.draw.rect(tela, (230, 100, 0), (bx, by, px, alt), 0, 2)
