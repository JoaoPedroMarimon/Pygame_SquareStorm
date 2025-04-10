#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para geração e controle de sons.
"""

import pygame
import random

def gerar_som_tiro():
    """
    Gera um som de tiro dinamicamente.
    
    Returns:
        Objeto Sound do pygame
    """
    # Gera um som de tiro dinamicamente usando pygame.mixer
    tamanho_amostra = 11025  # 0.25 segundos a 44.1kHz
    som = pygame.mixer.Sound(bytes(bytearray(random.randint(0, 10) for i in range(tamanho_amostra))))
    # Aumentar volume para o tiro do jogador
    som.set_volume(0.1)  # Volume reduzido para não ser muito alto
    return som

def gerar_som_explosao():
    """
    Gera um som de explosão dinamicamente.
    
    Returns:
        Objeto Sound do pygame
    """
    # Gera um som de explosão dinamicamente
    tamanho_amostra = 22050  # 0.5 segundos a 44.1kHz
    som = pygame.mixer.Sound(bytes(bytearray(random.randint(0, 255) if i % 2 == 0 else 0 for i in range(tamanho_amostra))))
    som.set_volume(0.15)
    return som

def gerar_som_dano():
    """
    Gera um som de dano/impacto dinamicamente.
    
    Returns:
        Objeto Sound do pygame
    """
    # Gera um som de dano dinamicamente
    tamanho_amostra = 5512  # 0.125 segundos a 44.1kHz
    som = pygame.mixer.Sound(bytes(bytearray(random.randint(128, 255) if i < tamanho_amostra // 2 else 0 for i in range(tamanho_amostra))))
    som.set_volume(0.2)
    return som