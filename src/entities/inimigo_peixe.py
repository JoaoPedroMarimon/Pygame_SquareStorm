#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para inimigo peixe - fases aquáticas (26+).
O peixe é um inimigo triangular que se parece com um peixe
e atira bolhas em vez de projéteis normais.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.utils.sound import gerar_som_tiro


class InimigoPeixe(Quadrado):
    """
    Inimigo peixe com forma triangular.
    Aparece nas fases 26+, no ambiente aquático.
    Atira bolhas em vez de tiros normais.
    """

    def __init__(self, x, y):
        """Inicializa o inimigo peixe."""
        cor_peixe = (210, 30, 30)  # Vermelho
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.85
        tamanho = int(TAMANHO_QUADRADO * 1.35)

        super().__init__(x, y, tamanho, cor_peixe, velocidade)

        self.vidas = 3
        self.vidas_max = 3
        self.tipo_peixe = True
        self.tempo_cooldown = 1300  # 1.3s entre bolhas
        # Começa apontando para a esquerda (em direção ao jogador)
        self.angulo_peixe = math.pi

    def mover(self, dx, dy):
        """Move o peixe sem atualizar ângulo (ângulo é atualizado via atualizar_angulo_jogador)."""
        super().mover(dx, dy)

    def atualizar_angulo_jogador(self, jogador):
        """Atualiza o ângulo do peixe para apontar diretamente ao jogador."""
        cx = self.x + self.tamanho // 2
        cy = self.y + self.tamanho // 2
        jx = jogador.x + jogador.tamanho // 2
        jy = jogador.y + jogador.tamanho // 2
        self.angulo_peixe = math.atan2(jy - cy, jx - cx)

    def atirar(self, tiros, direcao=None):
        """Atira bolhas em vez de projéteis normais."""
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro < self.tempo_cooldown:
            return

        self.tempo_ultimo_tiro = tempo_atual
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        if direcao:
            dx, dy = direcao
        else:
            dx = math.cos(self.angulo_peixe)
            dy = math.sin(self.angulo_peixe)

        # Som de tiro
        try:
            pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))
        except Exception:
            pass

        # Criar bolha (tiro com tipo_bolha=True)
        bolha = Tiro(centro_x, centro_y, dx, dy, (150, 220, 255), 5)
        bolha.tipo_bolha = True
        bolha.raio = 9
        bolha.cor_interna = (220, 245, 255)
        bolha.ricochete = True
        bolha.vida_ricochete = 420  # ~7 segundos a 60fps
        tiros.append(bolha)

    def desenhar(self, tela, tempo_atual=None):
        """Desenha o inimigo como um peixe triangular com detalhes."""
        if tempo_atual is None:
            tempo_atual = pygame.time.get_ticks()

        # Piscar se invulnerável
        if self.invulneravel and tempo_atual % 200 < 100:
            return

        cx = int(self.x + self.tamanho // 2)
        cy = int(self.y + self.tamanho // 2)
        angulo = self.angulo_peixe
        size = self.tamanho // 2  # 20px

        cos_a = math.cos(angulo)
        sin_a = math.sin(angulo)
        perp_cos = -sin_a
        perp_sin = cos_a

        def pt(fx, fy):
            """Ponto relativo ao centro do peixe."""
            return (cx + cos_a * fx - sin_a * fy,
                    cy + sin_a * fx + cos_a * fy)

        # Determinar cor (efeito de dano = branco)
        cor_uso = self.cor
        cor_escura = self.cor_escura
        if self.efeito_dano > 0:
            cor_uso = BRANCO
            cor_escura = BRANCO
            self.efeito_dano -= 1

        # === SOMBRA ===
        sombra_body = [pt(size, 0), pt(-size * 0.4, -size * 0.8), pt(-size * 0.4, size * 0.8)]
        pygame.draw.polygon(tela, (5, 12, 22),
                            [(p[0] + 4, p[1] + 4) for p in sombra_body])

        # === CAUDA BIFURCADA (V) ===
        # Ponto de junção da cauda com o corpo
        cauda_raiz = pt(-size * 0.35, 0)
        cauda_top  = pt(-size * 1.05, -size * 0.65)
        cauda_mid  = pt(-size * 0.65, 0)
        cauda_bot  = pt(-size * 1.05,  size * 0.65)
        pygame.draw.polygon(tela, cor_escura,
                            [cauda_raiz, cauda_top, cauda_mid])
        pygame.draw.polygon(tela, cor_escura,
                            [cauda_raiz, cauda_bot, cauda_mid])
        # Detalhe interior da cauda (cor principal)
        inner_cauda_top = pt(-size * 0.95, -size * 0.48)
        inner_cauda_bot = pt(-size * 0.95,  size * 0.48)
        inner_cauda_mid = pt(-size * 0.60, 0)
        pygame.draw.polygon(tela, cor_uso,
                            [cauda_raiz, inner_cauda_top, inner_cauda_mid])
        pygame.draw.polygon(tela, cor_uso,
                            [cauda_raiz, inner_cauda_bot, inner_cauda_mid])

        # === CORPO TRIANGULAR ===
        corpo = [pt(size, 0), pt(-size * 0.4, -size * 0.8), pt(-size * 0.4, size * 0.8)]
        pygame.draw.polygon(tela, cor_escura, corpo)

        # Interior do corpo (ligeiramente menor, cor principal)
        corpo_inner = [pt(size * 0.82, 0),
                       pt(-size * 0.32, -size * 0.62),
                       pt(-size * 0.32,  size * 0.62)]
        pygame.draw.polygon(tela, cor_uso, corpo_inner)

        # Brilho ventral (barriga mais clara)
        barriga = [pt(size * 0.6, size * 0.08),
                   pt(-size * 0.2, size * 0.55),
                   pt(-size * 0.2, size * 0.18)]
        pygame.draw.polygon(tela, (min(255, cor_uso[0] + 50),
                                   min(255, cor_uso[1] + 50),
                                   min(255, cor_uso[2] + 60)), barriga)

        # === NADADEIRA DORSAL (triângulo no topo) ===
        fin_d = [pt(size * 0.1,  -size * 0.78),
                 pt(size * 0.35, -size * 1.25),
                 pt(-size * 0.2, -size * 0.78)]
        pygame.draw.polygon(tela, cor_escura, fin_d)
        fin_d_inner = [pt(size * 0.1,  -size * 0.78),
                       pt(size * 0.3,  -size * 1.1),
                       pt(-size * 0.12,-size * 0.78)]
        pygame.draw.polygon(tela, cor_uso, fin_d_inner)

        # === NADADEIRA PEITORAL (pequena, lateral) ===
        fin_p = [pt(size * 0.25,  size * 0.35),
                 pt(size * 0.55,  size * 0.78),
                 pt(-size * 0.05, size * 0.40)]
        pygame.draw.polygon(tela, cor_escura, fin_p)

        # === LINHA LATERAL (traço horizontal que divide o corpo) ===
        ll_start = pt(size * 0.75, 0)
        ll_end   = pt(-size * 0.3, 0)
        pygame.draw.line(tela, tuple(max(0, c - 80) for c in cor_uso),
                         (int(ll_start[0]), int(ll_start[1])),
                         (int(ll_end[0]),   int(ll_end[1])), 2)

        # === ESCAMAS (3 arcos pequenos no corpo) ===
        for i, (fx, fy_sign) in enumerate([(0.3, -0.3), (0.0, -0.25), (-0.18, -0.2)]):
            sp = pt(fx * size, fy_sign * size)
            ep = pt(fx * size, -fy_sign * size)
            # Linha curva aproximada com 3 pontos
            mp = pt((fx - 0.12) * size, 0)
            escala_cor = tuple(max(0, c - 70) for c in cor_uso)
            pygame.draw.line(tela, escala_cor,
                             (int(sp[0]), int(sp[1])), (int(mp[0]), int(mp[1])), 1)
            pygame.draw.line(tela, escala_cor,
                             (int(mp[0]), int(mp[1])), (int(ep[0]), int(ep[1])), 1)

        # === BARRA DE VIDA ===
        if self.vidas < self.vidas_max:
            vida_largura = 44
            altura_barra = 5
            vida_x = int(self.x) + (self.tamanho - vida_largura) // 2
            vida_y = int(self.y) - 14
            pygame.draw.rect(tela, (60, 0, 0), (vida_x, vida_y, vida_largura, altura_barra), 0, 2)
            vida_atual_px = int((self.vidas / self.vidas_max) * vida_largura)
            if vida_atual_px > 0:
                pygame.draw.rect(tela, (0, 210, 140),
                                 (vida_x, vida_y, vida_atual_px, altura_barra), 0, 2)
