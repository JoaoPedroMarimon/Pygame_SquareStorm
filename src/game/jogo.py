#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal do jogo, gerencia o loop de jogo e a progressão das fases.
"""

import pygame
import sys
from src.config import *
from src.ui.menu import tela_inicio, tela_game_over, tela_vitoria_fase
from src.game.fase import jogar_fase
from src.utils.visual import criar_gradiente
from src.ui.loja import tela_loja
import os

def main_game():
    """
    Função principal de controle do jogo.
    Gerencia o loop de jogo, menus e progressão de fases.
    Ajustada para a nova configuração de tela.
    """
    os.environ['SDL_VIDEO_CENTERED'] = '1'
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
    gradiente_loja = criar_gradiente(ROXO_CLARO, ROXO_ESCURO)

    # O resto da função permanece igual
    # ...
    
    # Loop principal
    while True:
        # Mostrar tela de início
        opcao_menu = tela_inicio(tela, relogio, gradiente_menu, fonte_titulo)
        
        if opcao_menu == "loja":
            # O jogador escolheu ir para a loja
            tela_loja(tela, relogio, gradiente_loja)
            continue  # Volta para o menu principal
        
        if opcao_menu == False:  # Sair do jogo
            return
        
        # Se não foi para a loja nem saiu, então o jogador quer jogar
        # Variáveis de fase
        fase_atual = 1
        pontuacao_total = 0
        
        # Loop de fases
        while fase_atual <= MAX_FASES:
            # Jogar a fase atual
            resultado, pontuacao = jogar_fase(tela, relogio, fase_atual, gradiente_jogo, fonte_titulo, fonte_normal)
            pontuacao_total += pontuacao
            
            if not resultado:
                # Se o jogador perdeu
                opcao = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, False, fase_atual)
                if opcao:  # True = jogar de novo
                    break  # Sai do loop de fases para reiniciar do menu
                else:
                    return  # False = sair do jogo
            
            # Jogador completou a fase
            if fase_atual < MAX_FASES:
                # Se não for a última fase, mostra tela de vitória intermediária
                opcao = tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual, pontuacao_total)
                
                if opcao == "proximo":
                    # Avançar para próxima fase
                    fase_atual += 1
                elif opcao == "menu":
                    # Voltar ao menu principal
                    break
                else:  # "sair"
                    # Sair do jogo
                    return
            else:
                # Jogador completou a última fase
                opcao = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, True, MAX_FASES)
                if not opcao:  # False = sair do jogo
                    return
                break  # Sai do loop de fases para reiniciar do menu