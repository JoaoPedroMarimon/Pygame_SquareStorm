#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para inimigo fantasma tenebroso.
O fantasma fica visível por 2 segundos, depois invisível por 5 segundos.
Atira tiros normais quando visível.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.utils.sound import gerar_som_tiro


class InimigoFantasma(Quadrado):
    """
    Inimigo fantasma que alterna entre visível e invisível.
    Visível: 2 segundos | Invisível: 5 segundos
    """

    def __init__(self, x, y):
        """Inicializa o inimigo fantasma."""
        # Cor fantasmagórica (cinza-azulado etéreo)
        cor_fantasma = (150, 150, 200)  # Cinza-azul pálido
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.9  # Levemente mais lento, flutuando

        super().__init__(x, y, TAMANHO_QUADRADO, cor_fantasma, velocidade)

        # Atributos básicos
        self.vidas = 2
        self.vidas_max = 2

        # Sistema de visibilidade
        self.tempo_visivel = 3000  # 2 segundos visível
        self.tempo_invisivel = 5000  # 5 segundos invisível
        self.esta_visivel = True  # Começa visível
        self.tempo_mudanca_visibilidade = pygame.time.get_ticks()

        # Alpha para efeito de transparência
        self.alpha_atual = 255
        self.alpha_visivel = 255
        self.alpha_invisivel = 0  # Completamente invisível

        # Sistema de tiro
        self.tempo_cooldown = COOLDOWN_TIRO_INIMIGO
        self.tempo_ultimo_tiro = 0

        # Flag para identificar tipo
        self.tipo_fantasma = True

        # Efeito de flutuação
        self.tempo_flutuacao = random.uniform(0, 2 * math.pi)
        self.amplitude_flutuacao = 3

    def atualizar(self):
        """Atualiza o estado do fantasma (movimento + visibilidade)."""
        # Atualizar movimento base
        super().atualizar()

        # Atualizar visibilidade
        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_mudanca_visibilidade

        if self.esta_visivel:
            # Está visível, verificar se deve ficar invisível
            if tempo_decorrido >= self.tempo_visivel:
                self.esta_visivel = False
                self.tempo_mudanca_visibilidade = tempo_atual
        else:
            # Está invisível, verificar se deve ficar visível
            if tempo_decorrido >= self.tempo_invisivel:
                self.esta_visivel = True
                self.tempo_mudanca_visibilidade = tempo_atual

        # Atualizar alpha rapidamente para transição mais rápida
        alpha_alvo = self.alpha_visivel if self.esta_visivel else self.alpha_invisivel
        if self.alpha_atual < alpha_alvo:
            self.alpha_atual = min(self.alpha_atual + 25, alpha_alvo)
        elif self.alpha_atual > alpha_alvo:
            self.alpha_atual = max(self.alpha_atual - 25, alpha_alvo)

        # Atualizar flutuação
        self.tempo_flutuacao += 0.05

    def pode_atirar(self):
        """Fantasma só pode atirar quando está visível."""
        return self.esta_visivel

    def atirar(self, jogador, tiros_inimigo, particulas=None, flashes=None):
        """
        Atira na direção do jogador (apenas quando visível).

        Args:
            jogador: Objeto do jogador (alvo)
            tiros_inimigo: Lista de tiros inimigos
            particulas: Lista de partículas (opcional)
            flashes: Lista de flashes (opcional)
        """
        # Só atira quando visível
        if not self.pode_atirar():
            return

        tempo_atual = pygame.time.get_ticks()

        # Verificar cooldown
        if tempo_atual - self.tempo_ultimo_tiro < self.tempo_cooldown:
            return

        self.tempo_ultimo_tiro = tempo_atual

        # Calcular direção para o jogador
        dx = jogador.x - self.x
        dy = jogador.y - self.y
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia > 0:
            dx /= distancia
            dy /= distancia

            # Criar tiro fantasmagórico (mesma cor do fantasma)
            tiro = Tiro(
                self.x + self.tamanho // 2,
                self.y + self.tamanho // 2,
                dx, dy,
                (180, 180, 220),  # Tiro fantasmagórico azul-pálido
                7  # Velocidade padrão de tiro de inimigo
            )
            tiros_inimigo.append(tiro)

            # Som de tiro
            canal_disponivel = pygame.mixer.find_channel()
            if canal_disponivel:
                canal_disponivel.play(pygame.mixer.Sound(gerar_som_tiro()))

    def desenhar(self, tela, tempo_atual):
        """
        Desenha o fantasma como um quadrado com características assustadoras.

        Args:
            tela: Superfície do pygame onde desenhar
            tempo_atual: Tempo atual do jogo (para animações)
        """
        # Se está completamente invisível, não desenha nada
        if not self.esta_visivel and self.alpha_atual == 0:
            # Atualizar hitbox para colisão mesmo invisível
            offset_flutuacao = math.sin(self.tempo_flutuacao) * self.amplitude_flutuacao
            self.rect.y = int(self.y + offset_flutuacao)
            return

        # Criar surface com alpha para transparência
        fantasma_surface = pygame.Surface((self.tamanho, self.tamanho), pygame.SRCALPHA)

        # Flutuação vertical sutil
        offset_flutuacao = math.sin(self.tempo_flutuacao) * self.amplitude_flutuacao

        # ===== CORPO QUADRADO COM EFEITO FANTASMAGÓRICO =====

        # Aura/brilho externo (efeito etéreo) - só quando visível
        if self.esta_visivel:
            for i in range(3):
                aura_size = self.tamanho + (i * 4)
                aura_alpha = int(self.alpha_atual * 0.15 * (3 - i))
                aura_rect = pygame.Rect(-i*2, -i*2, aura_size, aura_size)
                pygame.draw.rect(fantasma_surface, (200, 200, 255, aura_alpha), aura_rect, 2)

        # Corpo principal do quadrado
        corpo_color = (*self.cor, int(self.alpha_atual))
        pygame.draw.rect(fantasma_surface, corpo_color, (0, 0, self.tamanho, self.tamanho))

        # Borda mais escura para dar profundidade
        borda_color = (100, 100, 180, int(self.alpha_atual))
        pygame.draw.rect(fantasma_surface, borda_color, (0, 0, self.tamanho, self.tamanho), 2)

        # ===== OLHOS ASSUSTADORES (só quando visível) =====
        if self.esta_visivel:
            olho_esquerdo_x = self.tamanho // 3
            olho_direito_x = 2 * self.tamanho // 3
            olho_y = self.tamanho // 3
            tamanho_olho = 8

            # Brilho externo dos olhos (aura vermelha/branca)
            brilho_alpha = int(min(255, self.alpha_atual * 1.5))
            cor_brilho = (255, 200, 200)

            pygame.draw.circle(fantasma_surface, (*cor_brilho, brilho_alpha),
                             (olho_esquerdo_x, olho_y), tamanho_olho + 2)
            pygame.draw.circle(fantasma_surface, (*cor_brilho, brilho_alpha),
                             (olho_direito_x, olho_y), tamanho_olho + 2)

            # Olhos internos (vermelho sangue quando visível)
            cor_olho = (255, 50, 50, int(self.alpha_atual))  # Vermelho sangue

            pygame.draw.circle(fantasma_surface, cor_olho,
                             (olho_esquerdo_x, olho_y), tamanho_olho)
            pygame.draw.circle(fantasma_surface, cor_olho,
                             (olho_direito_x, olho_y), tamanho_olho)

            # Pupilas pretas (mais assustadoras)
            pygame.draw.circle(fantasma_surface, (0, 0, 0, int(self.alpha_atual)),
                             (olho_esquerdo_x, olho_y), 3)
            pygame.draw.circle(fantasma_surface, (0, 0, 0, int(self.alpha_atual)),
                             (olho_direito_x, olho_y), 3)

            # Brilho nos olhos (reflexo)
            pygame.draw.circle(fantasma_surface, (255, 255, 255, int(self.alpha_atual)),
                             (olho_esquerdo_x - 2, olho_y - 2), 2)
            pygame.draw.circle(fantasma_surface, (255, 255, 255, int(self.alpha_atual)),
                             (olho_direito_x - 2, olho_y - 2), 2)

        # ===== BOCA ASSUSTADORA (só quando visível) =====
        if self.esta_visivel:
            boca_y = 2 * self.tamanho // 3
            boca_x_centro = self.tamanho // 2

            # Boca aberta em grito quando visível (mais assustador)
            boca_cor = (50, 0, 0, int(self.alpha_atual))  # Vermelho escuro/preto
            boca_largura = 12
            boca_altura = 10

            # Desenhar boca
            pygame.draw.ellipse(fantasma_surface, boca_cor,
                              (boca_x_centro - boca_largura // 2, boca_y,
                               boca_largura, boca_altura))

            # Dentes quando visível (mais assustador)
            if self.alpha_atual > 150:
                dente_cor = (255, 255, 200, int(self.alpha_atual))
                num_dentes = 4
                for i in range(num_dentes):
                    dente_x = boca_x_centro - 5 + i * 3
                    pygame.draw.rect(fantasma_surface, dente_cor,
                                   (dente_x, boca_y + 1, 2, 3))

        # ===== EFEITO DE NÉVOA/PARTÍCULAS (só quando visível) =====
        if self.esta_visivel and random.random() < 0.4:
            # Partículas flutuando ao redor do fantasma
            for _ in range(3):
                px = random.randint(0, self.tamanho)
                py = random.randint(0, self.tamanho)
                tamanho_particula = random.randint(1, 2)
                # Garantir que o alpha máximo seja pelo menos 20 para evitar range inválido
                alpha_max = max(20, int(self.alpha_atual * 0.6))
                particula_alpha = random.randint(20, alpha_max)
                cor_particula = (255, 200, 200)
                pygame.draw.circle(fantasma_surface, (*cor_particula, particula_alpha),
                                 (px, py), tamanho_particula)

        # ===== DESENHAR NA TELA =====
        pos_y_com_flutuacao = int(self.y + offset_flutuacao)
        tela.blit(fantasma_surface, (self.x, pos_y_com_flutuacao))

        # Atualizar hitbox para colisão
        self.rect.y = int(self.y + offset_flutuacao)

        # ===== BARRA DE VIDA (estilo padrão dos inimigos) =====
        if self.esta_visivel:
            vida_largura = 50
            altura_barra = 6

            # Fundo escuro
            pygame.draw.rect(tela, (40, 40, 40),
                            (self.x, pos_y_com_flutuacao - 15, vida_largura, altura_barra), 0, 2)

            # Vida atual
            vida_atual = int((self.vidas / self.vidas_max) * vida_largura)
            if vida_atual > 0:
                pygame.draw.rect(tela, self.cor,
                                (self.x, pos_y_com_flutuacao - 15, vida_atual, altura_barra), 0, 2)

    def esta_invisivel(self):
        """Retorna True se o fantasma está invisível (para lógica de jogo)."""
        return not self.esta_visivel

    def obter_alpha(self):
        """Retorna o alpha atual do fantasma."""
        return self.alpha_atual

    def esta_invulneravel(self):
        """Retorna True se o fantasma está invulnerável (invisível)."""
        return not self.esta_visivel
