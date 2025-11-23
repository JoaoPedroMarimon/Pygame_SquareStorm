#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de drops de itens para o modo Versus multiplayer.
Itens caem do céu e podem ser coletados pelos jogadores.
"""

import pygame
import random
import math
from src.config import *


class ItemDrop:
    """Representa um item que caiu no chão e pode ser coletado."""

    def __init__(self, x, y, tipo, subtipo=None):
        """
        Args:
            x, y: Posição do item
            tipo: 'arma' ou 'item'
            subtipo: Nome específico (ex: 'espingarda', 'granada', etc.)
        """
        self.x = x
        self.y = y
        self.tipo = tipo
        self.subtipo = subtipo
        self.tamanho = 30
        self.rect = pygame.Rect(x - self.tamanho // 2, y - self.tamanho // 2,
                                self.tamanho, self.tamanho)

        # Animação de queda
        self.altura_queda = -200  # Começa acima da tela
        self.velocidade_queda = 0
        self.caindo = True

        # Animação de pulso
        self.tempo_criacao = pygame.time.get_ticks()

        # Cor baseada no tipo
        self.cor = self._obter_cor()

    def _obter_cor(self):
        """Retorna cor baseada no tipo de item."""
        cores_armas = {
            'espingarda': AMARELO,
            'metralhadora': LARANJA,
            'desert_eagle': (255, 215, 0),  # Dourado
        }

        cores_itens = {
            'granada': VERMELHO,
            'vida': VERDE,
            'moeda': AMARELO,
            'sabre': CIANO,
        }

        if self.tipo == 'arma':
            return cores_armas.get(self.subtipo, BRANCO)
        else:
            return cores_itens.get(self.subtipo, BRANCO)

    def atualizar(self):
        """Atualiza física da queda."""
        if self.caindo:
            self.velocidade_queda += 0.5  # Gravidade
            self.altura_queda += self.velocidade_queda

            # Chegou no chão
            if self.altura_queda >= 0:
                self.altura_queda = 0
                self.caindo = False
                # Bounce effect
                self.velocidade_queda = 0

    def desenhar(self, tela):
        """Desenha o item com efeitos visuais."""
        tempo_atual = pygame.time.get_ticks()

        # Posição real (considerando queda)
        pos_y_real = self.y + self.altura_queda

        # Sombra (quando está caindo)
        if self.caindo:
            sombra_alpha = int(150 * (1 - abs(self.altura_queda) / 200))
            pygame.draw.circle(tela, (0, 0, 0, sombra_alpha),
                             (int(self.x), int(self.y)), self.tamanho // 2)

        # Efeito de pulso quando no chão
        pulso = 0
        if not self.caindo:
            pulso = math.sin(tempo_atual / 200) * 3

        # Caixa do item
        tamanho_atual = self.tamanho + int(pulso)
        item_rect = pygame.Rect(
            self.x - tamanho_atual // 2,
            pos_y_real - tamanho_atual // 2,
            tamanho_atual,
            tamanho_atual
        )

        # Desenhar caixa com brilho
        pygame.draw.rect(tela, self.cor, item_rect, 0, 5)
        pygame.draw.rect(tela, BRANCO, item_rect, 3, 5)

        # Brilho interno
        brilho_rect = pygame.Rect(
            item_rect.x + 5,
            item_rect.y + 5,
            item_rect.width - 10,
            item_rect.height - 10
        )
        cor_brilho = tuple(min(255, c + 100) for c in self.cor)
        pygame.draw.rect(tela, cor_brilho, brilho_rect, 0, 3)

        # Ícone/letra indicando tipo
        fonte_icone = pygame.font.SysFont("Arial", 16, True)
        if self.tipo == 'arma':
            icone_letra = self.subtipo[0].upper()  # Primeira letra
        else:
            icones = {
                'granada': 'G',
                'vida': '+',
                'moeda': '$',
                'sabre': 'S'
            }
            icone_letra = icones.get(self.subtipo, '?')

        texto = fonte_icone.render(icone_letra, True, BRANCO)
        tela.blit(texto, (item_rect.centerx - texto.get_width() // 2,
                         item_rect.centery - texto.get_height() // 2))

        # Partículas brilhantes ao redor (quando no chão)
        if not self.caindo and random.random() < 0.1:
            for _ in range(2):
                px = self.x + random.randint(-20, 20)
                py = self.y + random.randint(-20, 20)
                pygame.draw.circle(tela, self.cor, (int(px), int(py)), 2)

    def pode_coletar(self):
        """Retorna se o item pode ser coletado (não está mais caindo)."""
        return not self.caindo

    def colidiu_com(self, jogador):
        """Verifica colisão com jogador."""
        if not self.pode_coletar():
            return False

        # Usar hitbox do jogador
        jogador_rect = pygame.Rect(jogador.x - jogador.tamanho // 2,
                                   jogador.y - jogador.tamanho // 2,
                                   jogador.tamanho,
                                   jogador.tamanho)

        return self.rect.colliderect(jogador_rect)


def gerar_item_aleatorio():
    """
    Gera um tipo de item aleatório para dropar.
    Retorna (tipo, subtipo).
    """
    # 60% chance de arma, 40% chance de item
    if random.random() < 0.6:
        armas = ['espingarda', 'metralhadora', 'desert_eagle']
        return ('arma', random.choice(armas))
    else:
        itens = ['granada', 'vida', 'sabre']
        return ('item', random.choice(itens))


def spawnar_item_aleatorio(largura, altura):
    """
    Spawna um item em posição aleatória.
    Retorna objeto ItemDrop.
    """
    # Posição aleatória na arena
    margem = 50
    x = random.randint(margem, largura - margem)
    y = random.randint(margem, altura - margem)

    tipo, subtipo = gerar_item_aleatorio()

    print(f"[DROP] Spawnando {subtipo} ({tipo}) em ({x}, {y})")

    return ItemDrop(x, y, tipo, subtipo)
