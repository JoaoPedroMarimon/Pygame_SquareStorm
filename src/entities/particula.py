#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo da classe Particula, para efeitos visuais de explosões e impactos.
"""

import pygame
import random

class Particula:
    """
    Classe para gerenciar partículas de efeitos visuais.
    Usada para explosões, impactos e outros efeitos.
    """
    def __init__(self, x, y, cor):
        self.x = x
        self.y = y
        self.cor = cor
        self.cor_original = cor
        self.tamanho = random.randint(3, 7)
        self.velocidade_x = random.uniform(-4, 4)
        self.velocidade_y = random.uniform(-4, 4)
        self.vida = random.randint(30, 60)
        self.vida_maxima = self.vida
        self.gravidade = random.uniform(0.05, 0.15)
        self.rotacao = random.randint(0, 360)
        self.vel_rotacao = random.randint(-8, 8)

    def atualizar(self):
        """Atualiza a posição e estado da partícula."""
        self.x += self.velocidade_x
        self.y += self.velocidade_y
        self.velocidade_y += self.gravidade  # Adiciona um pouco de gravidade
        self.vida -= 1
        self.rotacao = (self.rotacao + self.vel_rotacao) % 360
        
        # Diminuir o tamanho gradualmente
        self.tamanho = max(0, self.tamanho * 0.95)
        
        # Ajustar a cor para desvanecer
        fade_factor = self.vida / self.vida_maxima
        # CORREÇÃO: Garantir que os valores sejam inteiros válidos (0-255)
        self.cor = tuple(max(0, min(255, int(c * fade_factor))) for c in self.cor_original)

    def desenhar(self, tela):
        """Desenha a partícula na tela."""
        if self.tamanho > 0.5:
            try:
                # Criar uma pequena superfície rotacionada para a partícula
                tamanho_surf = int(self.tamanho * 2)
                if tamanho_surf <= 0:
                    return
                
                surf = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
                
                # Garantir que a cor é uma tupla de inteiros válidos
                cor_valida = tuple(max(0, min(255, int(c))) for c in self.cor)
                
                # Desenhar um polígono ou círculo na superfície
                if random.random() < 0.7:  # 70% chance de ser círculo
                    raio = max(1, int(self.tamanho))
                    pygame.draw.circle(surf, cor_valida, (tamanho_surf//2, tamanho_surf//2), raio)
                else:  # 30% chance de ser um quadrado
                    pygame.draw.rect(surf, cor_valida, (0, 0, tamanho_surf, tamanho_surf))
                
                # Rotacionar a superfície
                surf_rot = pygame.transform.rotate(surf, self.rotacao)
                
                # Obter o retângulo da superfície rotacionada
                rect = surf_rot.get_rect()
                rect.center = (int(self.x), int(self.y))
                
                # Desenhar na tela
                tela.blit(surf_rot, rect)
            except (ValueError, TypeError) as e:
                # Se houver algum erro, apenas ignore esta partícula
                pass

    def acabou(self):
        """Verifica se a partícula completou seu ciclo de vida."""
        return self.vida <= 0

def criar_explosao(x, y, cor, particulas, quantidade=30):
    """
    Cria uma explosão de partículas.
    
    Args:
        x, y: Coordenadas da explosão
        cor: Cor base das partículas
        particulas: Lista onde adicionar as partículas
        quantidade: Número de partículas a criar
        
    Returns:
        Dicionário com informações do flash luminoso
    """
    # Garantir que a cor base é válida
    cor_valida = tuple(max(0, min(255, int(c))) for c in cor)
    
    for _ in range(quantidade):
        # Variações de cor para mais diversidade visual
        cor_var = tuple(max(0, min(255, int(c) + random.randint(-30, 30))) for c in cor_valida)
        particulas.append(Particula(x, y, cor_var))
    
    # Adicionar um flash de luz
    flash = {
        'x': x,
        'y': y,
        'raio': 40,
        'vida': 10,
        'cor': (255, 255, 255)  # Branco
    }
    return flash