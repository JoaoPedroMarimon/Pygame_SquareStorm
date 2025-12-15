#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para representar espinhos mortais nas bordas da arena (fases 11+).
"""

import pygame
import math
from src.config import LARGURA, ALTURA_JOGO, VERMELHO, VERMELHO_ESCURO


class Espinho:
    """Representa um espinho nas bordas da arena."""

    def __init__(self, x, y, largura, altura, direcao='horizontal'):
        """
        Inicializa um espinho.

        Args:
            x, y: Posição do espinho
            largura, altura: Dimensões do espinho
            direcao: 'horizontal' ou 'vertical'
        """
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.direcao = direcao
        self.rect = pygame.Rect(x, y, largura, altura)

        # Cores dos espinhos (tema tóxico/perigoso)
        self.cor_base = (100, 50, 50)  # Marrom escuro
        self.cor_ponta = (200, 50, 50)  # Vermelho

    def desenhar(self, tela, tempo_atual, progresso_animacao=1.0):
        """
        Desenha o espinho com efeito visual de perigo.

        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual em ms para animações
            progresso_animacao: Progresso da animação de crescimento (0.0 a 1.0)
        """
        # Efeito de pulsação
        pulso = abs(math.sin(tempo_atual / 300)) * 0.3 + 0.7
        cor_atual = tuple(int(c * pulso) for c in self.cor_ponta)

        # Aplicar efeito de crescimento suave com easing
        # Usa uma curva ease-out para um efeito mais dramático
        if progresso_animacao < 1.0:
            # Easing: easeOutElastic para efeito de "mola"
            p = 0.3
            s = p / 4
            if progresso_animacao == 0:
                escala = 0
            else:
                escala = pow(2, -10 * progresso_animacao) * math.sin((progresso_animacao - s) * (2 * math.pi) / p) + 1
                escala = max(0, min(1, escala))  # Garantir entre 0 e 1
        else:
            escala = 1.0

        if self.direcao == 'horizontal':
            # Desenhar espinhos triangulares na horizontal
            num_espinhos = int(self.largura / 30)
            tamanho_base = self.largura / num_espinhos
            altura_animada = self.altura * escala

            for i in range(num_espinhos):
                base_x = self.x + i * tamanho_base

                # Pontos do triângulo (espinho apontando para baixo ou cima)
                if self.y < ALTURA_JOGO / 2:  # Borda superior - apontar para baixo
                    pontos = [
                        (base_x, self.y),
                        (base_x + tamanho_base, self.y),
                        (base_x + tamanho_base / 2, self.y + altura_animada)
                    ]
                else:  # Borda inferior - apontar para cima
                    pontos = [
                        (base_x, self.y + self.altura),
                        (base_x + tamanho_base, self.y + self.altura),
                        (base_x + tamanho_base / 2, self.y + self.altura - altura_animada)
                    ]

                # Desenhar o triângulo
                pygame.draw.polygon(tela, cor_atual, pontos)
                pygame.draw.polygon(tela, self.cor_base, pontos, 2)

        else:  # vertical
            # Desenhar espinhos triangulares na vertical
            num_espinhos = int(self.altura / 30)
            tamanho_base = self.altura / num_espinhos
            largura_animada = self.largura * escala

            for i in range(num_espinhos):
                base_y = self.y + i * tamanho_base

                # Pontos do triângulo (espinho apontando para direita ou esquerda)
                if self.x < LARGURA / 2:  # Borda esquerda - apontar para direita
                    pontos = [
                        (self.x, base_y),
                        (self.x, base_y + tamanho_base),
                        (self.x + largura_animada, base_y + tamanho_base / 2)
                    ]
                else:  # Borda direita - apontar para esquerda
                    pontos = [
                        (self.x + self.largura, base_y),
                        (self.x + self.largura, base_y + tamanho_base),
                        (self.x + self.largura - largura_animada, base_y + tamanho_base / 2)
                    ]

                # Desenhar o triângulo
                pygame.draw.polygon(tela, cor_atual, pontos)
                pygame.draw.polygon(tela, self.cor_base, pontos, 2)


def criar_espinhos_bordas(espessura=30):
    """
    Cria espinhos em todas as bordas da arena.

    Args:
        espessura: Espessura da camada de espinhos

    Returns:
        Lista de objetos Espinho
    """
    espinhos = []

    # Espinhos na borda superior
    espinhos.append(Espinho(0, 0, LARGURA, espessura, 'horizontal'))

    # Espinhos na borda inferior
    espinhos.append(Espinho(0, ALTURA_JOGO - espessura, LARGURA, espessura, 'horizontal'))

    # Espinhos na borda esquerda
    espinhos.append(Espinho(0, 0, espessura, ALTURA_JOGO, 'vertical'))

    # Espinhos na borda direita
    espinhos.append(Espinho(LARGURA - espessura, 0, espessura, ALTURA_JOGO, 'vertical'))

    return espinhos
