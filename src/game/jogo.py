#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal do jogo, gerencia o loop de jogo e a progressão das fases.
"""

import pygame
import sys
from src.config import *
from src.ui.menu import tela_inicio, tela_game_over
from src.game.fase import jogar_fase
from src.utils.visual import criar_gradiente

def main_game():
    """
    Função principal de controle do jogo.
    Gerencia o loop de jogo, menus e progressão de fases.
    """
    # Configuração da tela
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption(TITULO)
    relogio = pygame.time.Clock()

    # Adicionar um ícone para a janela
    icon_surf = pygame.Surface((32, 32))
    icon_surf.fill(PRETO)
    pygame.draw.rect(icon_surf, AZUL, (5, 5, 22, 22))
    pygame.display.set_icon(icon_surf)

    # Carregar ou criar fontes
    try:
        fonte_titulo = pygame.font.Font(None, 60)  # None usa a fonte padrão
        fonte_normal = pygame.font.Font(None, 36)
        fonte_pequena = pygame.font.Font(None, 24)
    except:
        fonte_titulo = pygame.font.SysFont("Arial", 60, True)
        fonte_normal = pygame.font.SysFont("Arial", 36, True)
        fonte_pequena = pygame.font.SysFont("Arial", 24)

    # Criar gradientes para diferentes telas
    gradiente_jogo = criar_gradiente((0, 0, 30), (0, 0, 60))
    gradiente_menu = criar_gradiente((30, 0, 60), (10, 0, 30))
    gradiente_vitoria = criar_gradiente((0, 50, 0), (0, 20, 40))
    gradiente_derrota = criar_gradiente((50, 0, 0), (20, 0, 40))

    # Loop principal
    jogar_novamente = True
    while jogar_novamente:
        # Mostrar tela de início
        if not tela_inicio(tela, relogio, gradiente_menu, fonte_titulo):
            return
        
        # Variáveis de fase
        fase_atual = 1
        
        # Loop de fases
        while fase_atual <= MAX_FASES:
            if not jogar_fase(tela, relogio, fase_atual, gradiente_jogo, fonte_titulo, fonte_normal):
                # Se retornar False, o jogador perdeu
                jogar_novamente = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, False, fase_atual)
                break
            
            fase_atual += 1
            
            # Se completou todas as fases, mostrar tela de vitória final
            if fase_atual > MAX_FASES:
                jogar_novamente = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, True, MAX_FASES)