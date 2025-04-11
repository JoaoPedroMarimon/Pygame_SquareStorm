#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para representar as moedinhas que aparecem no jogo.
"""

import pygame
import math
import random
from src.config import AMARELO

class Moeda:
    """
    Classe para representar as moedinhas que o jogador pode coletar.
    """
    def __init__(self, x, y, tamanho=25):
        self.x = x
        self.y = y
        self.tamanho = tamanho
        self.raio = tamanho // 2
        self.cor = AMARELO
        self.rect = pygame.Rect(x - self.raio, y - self.raio, tamanho, tamanho)
        self.tempo_criacao = pygame.time.get_ticks()
        self.tempo_vida = random.randint(5000, 10000)  # Duração aleatória entre 5-10 segundos
        self.angulo = 0
        self.brilho = 0
        self.direcao_brilho = 1
    
    def atualizar(self):
        """Atualiza o estado da moeda (animação, tempo de vida, etc.)."""
        # Atualiza a animação de rotação
        self.angulo = (self.angulo + 2) % 360
        
        # Atualiza o efeito de brilho pulsante
        self.brilho += 0.05 * self.direcao_brilho
        if self.brilho >= 1:
            self.brilho = 1
            self.direcao_brilho = -1
        elif self.brilho <= 0:
            self.brilho = 0
            self.direcao_brilho = 1
        
        # Verifica se a moeda ainda está viva
        tempo_atual = pygame.time.get_ticks()
        return tempo_atual - self.tempo_criacao < self.tempo_vida
    
    def desenhar(self, tela):
        """Desenha a moeda na tela com efeitos de animação."""
        # Calcular tamanho baseado no ângulo (simular rotação 3D)
        escala = 0.7 + 0.3 * abs(math.cos(math.radians(self.angulo)))
        largura_atual = int(self.tamanho * escala)
        
        # Calcular cores com efeito de brilho
        cor_base = self.cor
        cor_brilho = (255, 255, 150)  # Amarelo mais claro
        
        r = int(cor_base[0] * (1 - self.brilho) + cor_brilho[0] * self.brilho)
        g = int(cor_base[1] * (1 - self.brilho) + cor_brilho[1] * self.brilho)
        b = int(cor_base[2] * (1 - self.brilho) + cor_brilho[2] * self.brilho)
        
        cor_atual = (r, g, b)
        
        # Desenhar moeda como um círculo
        pygame.draw.circle(tela, cor_atual, (int(self.x), int(self.y)), int(self.raio * escala))
        
        # Adicionar detalhes internos para parecer uma moeda
        pygame.draw.circle(tela, (r-30, g-30, 0), (int(self.x), int(self.y)), int(self.raio * escala * 0.8), 1)
        
        # Adicionar brilho
        if self.brilho > 0.5:
            brilho_raio = int(self.raio * 0.3)
            brilho_pos_x = int(self.x - self.raio * 0.3)
            brilho_pos_y = int(self.y - self.raio * 0.3)
            pygame.draw.circle(tela, (255, 255, 255), (brilho_pos_x, brilho_pos_y), brilho_raio)
    
    def colidiu(self, rect):
        """Verifica se a moeda colidiu com um retângulo (jogador)."""
        return self.rect.colliderect(rect)
    
    def atualizar_rect(self):
        """Atualiza o retângulo de colisão da moeda."""
        self.rect.x = self.x - self.raio
        self.rect.y = self.y - self.raio