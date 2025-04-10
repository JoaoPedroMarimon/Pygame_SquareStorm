#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para efeitos visuais como gradientes, estrelas e renderização de texto.
"""

import pygame
import random
from src.config import LARGURA, ALTURA, BRANCO

def criar_gradiente(cor1, cor2):
    """
    Cria uma superfície com um gradiente vertical.
    
    Args:
        cor1: Cor RGB do topo
        cor2: Cor RGB da base
        
    Returns:
        Superfície com gradiente
    """
    gradiente = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        r = cor1[0] + (cor2[0] - cor1[0]) * y / ALTURA
        g = cor1[1] + (cor2[1] - cor1[1]) * y / ALTURA
        b = cor1[2] + (cor2[2] - cor1[2]) * y / ALTURA
        pygame.draw.line(gradiente, (r, g, b), (0, y), (LARGURA, y))
    return gradiente

def criar_estrelas(quantidade):
    """
    Cria uma lista de estrelas para o fundo.
    
    Args:
        quantidade: Número de estrelas a criar
        
    Returns:
        Lista de estrelas (cada uma é uma lista [x, y, tamanho, brilho, velocidade])
    """
    estrelas = []
    for _ in range(quantidade):
        x = random.randint(0, LARGURA)
        y = random.randint(0, ALTURA)
        tamanho = random.uniform(0.5, 2.5)
        brilho = random.randint(100, 255)
        vel = random.uniform(0.1, 0.5)
        estrelas.append([x, y, tamanho, brilho, vel])
    return estrelas

def desenhar_estrelas(tela, estrelas):
    """
    Desenha e atualiza as estrelas na tela.
    
    Args:
        tela: Superfície onde desenhar
        estrelas: Lista de estrelas
    """
    for estrela in estrelas:
        x, y, tamanho, brilho, vel = estrela
        # Desenhar a estrela
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
        
        # Mover a estrela (paralaxe)
        estrela[0] -= vel
        
        # Se a estrela sair da tela, reposicioná-la
        if estrela[0] < 0:
            estrela[0] = LARGURA
            estrela[1] = random.randint(0, ALTURA)

def desenhar_texto(tela, texto, tamanho, cor, x, y, fonte=None, sombra=True):
    """
    Desenha texto na tela, opcionalmente com uma sombra.
    
    Args:
        tela: Superfície onde desenhar
        texto: String a ser renderizada
        tamanho: Tamanho da fonte
        cor: Cor RGB do texto
        x, y: Coordenadas do centro do texto
        fonte: Objeto de fonte (opcional)
        sombra: Se True, adiciona sombra ao texto
        
    Returns:
        Rect do texto desenhado
    """
    if fonte is None:
        fonte = pygame.font.SysFont("Arial", tamanho, True)
    
    if sombra:
        # Desenhar sombra do texto
        superficie_sombra = fonte.render(texto, True, (30, 30, 30))
        rect_sombra = superficie_sombra.get_rect()
        rect_sombra.center = (x + 2, y + 2)
        tela.blit(superficie_sombra, rect_sombra)
    
    # Desenhar texto principal
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    rect.center = (x, y)
    tela.blit(superficie, rect)
    
    return rect  # Retorna o retângulo para interação com botões

def criar_botao(tela, texto, x, y, largura, altura, cor_normal, cor_hover, cor_texto):
    """
    Cria um botão interativo na tela.
    
    Args:
        tela: Superfície onde desenhar
        texto: Texto do botão
        x, y: Coordenadas do centro do botão
        largura, altura: Dimensões do botão
        cor_normal: Cor RGB quando não hover
        cor_hover: Cor RGB quando hover
        cor_texto: Cor RGB do texto
        
    Returns:
        True se o mouse estiver sobre o botão, False caso contrário
    """
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(x - largura // 2, y - altura // 2, largura, altura)
    
    hover = rect.collidepoint(mouse_pos)
    
    # Desenhar o botão com efeito de hover
    if hover:
        pygame.draw.rect(tela, cor_hover, rect, 0, 10)
        pygame.draw.rect(tela, (255, 255, 255), rect, 2, 10)
    else:
        pygame.draw.rect(tela, cor_normal, rect, 0, 10)
        pygame.draw.rect(tela, (150, 150, 150), rect, 2, 10)
    
    # Renderizar o texto do botão
    fonte = pygame.font.SysFont("Arial", 28, True)
    texto_surf = fonte.render(texto, True, cor_texto)
    texto_rect = texto_surf.get_rect(center=rect.center)
    tela.blit(texto_surf, texto_rect)
    
    return hover