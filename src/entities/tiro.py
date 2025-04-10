#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo da classe Tiro, que representa os projéteis disparados.
"""

import pygame
import math
import random
from src.config import LARGURA, ALTURA

class Tiro:
    """
    Classe para os projéteis.
    Gerencia o movimento, colisões e efeitos visuais dos tiros.
    """
    def __init__(self, x, y, dx, dy, cor, velocidade):
        self.x = x
        self.y = y
        self.raio = 6
        
        # Normalizar a direção
        comprimento = math.sqrt(dx**2 + dy**2)
        if comprimento > 0:
            self.dx = dx / comprimento
            self.dy = dy / comprimento
        else:
            self.dx = dx
            self.dy = dy
            
        self.cor = cor
        self.cor_interna = self._gerar_cor_brilhante(cor)
        self.velocidade = velocidade
        self.rect = pygame.Rect(x - self.raio, y - self.raio, self.raio * 2, self.raio * 2)
        self.tempo_criacao = pygame.time.get_ticks()
        self.particulas = []
        self.ultimo_rastro = 0
    
    def _gerar_cor_brilhante(self, cor):
        """Gera uma cor mais brilhante para o interior do tiro."""
        return tuple(min(255, c + 100) for c in cor)

    def atualizar(self):
        """Atualiza a posição e efeitos do tiro."""
        self.x += self.dx * self.velocidade
        self.y += self.dy * self.velocidade
        self.rect.x = self.x - self.raio
        self.rect.y = self.y - self.raio
        
        # Adicionar partículas de rastro
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_rastro > 50:  # A cada 50ms
            self.ultimo_rastro = tempo_atual
            for _ in range(2):
                particula = {
                    'x': self.x - self.dx * random.uniform(0, 10),
                    'y': self.y - self.dy * random.uniform(0, 10),
                    'raio': random.uniform(1, 3),
                    'vida': random.randint(5, 15)
                }
                self.particulas.append(particula)
        
        # Atualizar partículas
        for particula in self.particulas[:]:
            particula['vida'] -= 1
            particula['raio'] -= 0.1
            if particula['vida'] <= 0 or particula['raio'] <= 0:
                self.particulas.remove(particula)

    def desenhar(self, tela):
        """Desenha o tiro e seu rastro de partículas."""
        # Desenhar partículas de rastro
        for particula in self.particulas:
            alpha = int(255 * (particula['vida'] / 15))
            raio = int(particula['raio'])
            if raio > 0:
                pygame.draw.circle(tela, self.cor, (int(particula['x']), int(particula['y'])), raio)
        
        # Desenhar brilho externo
        pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), self.raio + 2)
        
        # Desenhar tiro principal
        pygame.draw.circle(tela, self.cor_interna, (int(self.x), int(self.y)), self.raio)

    def fora_da_tela(self):
        """Verifica se o tiro saiu dos limites da tela."""
        return (self.x < 0 or self.x > LARGURA or 
                self.y < 0 or self.y > ALTURA)