#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a seção de itens da loja do jogo.
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import desenhar_texto
import json
import os

def salvar_upgrades(upgrades):
    """
    Salva os upgrades no arquivo.
    """
    try:
        # Criar o diretório de dados se não existir
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Salvar os upgrades no arquivo
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f)
    except Exception as e:
        print(f"Erro ao salvar upgrades: {e}")

def desenhar_items_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro):
    """
    Desenha a seção de itens da loja.
    
    Args:
        tela: Superfície principal do jogo
        area_conteudo: Retângulo definindo a área de conteúdo
        moeda_manager: Gerenciador de moedas
        upgrades: Dicionário com os upgrades do jogador
        mouse_pos: Posição atual do mouse
        clique_ocorreu: Se houve clique neste frame
        som_compra: Som para compra bem-sucedida
        som_erro: Som para erro na compra
        
    Returns:
        Tupla (mensagem, cor) ou None
    """
    # Título da seção
    desenhar_texto(tela, "ITEMS", 36, (120, 220, 120), LARGURA // 2, area_conteudo.y + 40)
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # Item: Granada
    item_y = area_conteudo.y + 120
    item_rect = pygame.Rect(area_conteudo.x + 50, item_y, area_conteudo.width - 100, 120)
    pygame.draw.rect(tela, (40, 60, 40), item_rect, 0, 8)
    pygame.draw.rect(tela, (80, 150, 80), item_rect, 2, 8)
    
    # Desenhar ícone de granada
    granada_x = item_rect.x + 50
    granada_y = item_y + 60
    tamanho_granada = 20

    # Cor base da granada
    cor_granada = (60, 120, 60)
    cor_granada_escura = (40, 80, 40)
    
    # Corpo da granada (esfera)
    pygame.draw.circle(tela, cor_granada, (granada_x, granada_y), tamanho_granada)
    
    # Detalhes da granada (linhas cruzadas para textura)
    pygame.draw.line(tela, cor_granada_escura, (granada_x - tamanho_granada + 4, granada_y), 
                    (granada_x + tamanho_granada - 4, granada_y), 2)
    pygame.draw.line(tela, cor_granada_escura, (granada_x, granada_y - tamanho_granada + 4), 
                    (granada_x, granada_y + tamanho_granada - 4), 2)
    
    # Parte superior (bocal)
    pygame.draw.rect(tela, (150, 150, 150), (granada_x - 5, granada_y - tamanho_granada - 7, 10, 7), 0, 2)
    
    # Pino da granada
    pin_x = granada_x + 8
    pin_y = granada_y - tamanho_granada - 3
    
    # Anel do pino
    pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), 6, 2)
    
    # Animação de pulsação para o efeito de brilho
    pulso = (math.sin(tempo_atual / 200) + 1) / 2  # Valor entre 0 e 1
    cor_brilho = (100 + int(pulso * 50), 200 + int(pulso * 55), 100 + int(pulso * 50))
    
    # Brilho/reflexo na granada
    pygame.draw.circle(tela, cor_brilho, (granada_x - tamanho_granada//2, granada_y - tamanho_granada//2), 4)
    
    # Nome do item
    desenhar_texto(tela, "GRENADE", 30, (150, 220, 150), item_rect.x + 200, item_y + 30)
    
    # Descrição e status do item
    if 'granada' not in upgrades:
        granada_status = "Explosive area damage! (Not owned)"
    else:
        granada_status = f"Grenades: {upgrades['granada']}"
    
    desenhar_texto(tela, granada_status, 22, BRANCO, item_rect.x + 200, item_y + 60)
    
    # Texto de uso
    desenhar_texto(tela, "Press Q to select, Mouse to throw", 18, (200, 200, 200), 
                  item_rect.x + 200, item_y + 85)
    
    # Custo do item
    custo_granada = 25
    
    # Botão de compra
    botao_compra_x = item_rect.x + item_rect.width - 130
    botao_compra_y = item_y + 60
    botao_compra_largura = 180
    botao_compra_altura = 50
    rect_compra = pygame.Rect(botao_compra_x - botao_compra_largura//2, 
                             botao_compra_y - botao_compra_altura//2,
                             botao_compra_largura, botao_compra_altura)
    
    # Verificar se o jogador tem moedas suficientes
    pode_comprar = moeda_manager.obter_quantidade() >= custo_granada
    
    # Desenhar botão de compra
    cor_botao = (60, 120, 60) if pode_comprar else (40, 80, 40)
    cor_hover = (80, 160, 80) if pode_comprar else (50, 90, 50)
    hover_compra = rect_compra.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover if hover_compra else cor_botao, rect_compra, 0, 8)
    pygame.draw.rect(tela, (120, 220, 120), rect_compra, 2, 8)
    
    # Ícone de moeda e custo
    moeda_mini_x = botao_compra_x - 50
    moeda_mini_y = botao_compra_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini_x, moeda_mini_y), 12)
    
    # Texto de custo
    desenhar_texto(tela, f"{custo_granada}", 24, BRANCO, botao_compra_x, botao_compra_y)
    
    # Verificar clique no botão de compra
    if clique_ocorreu and rect_compra.collidepoint(mouse_pos):
        if pode_comprar:
            # Compra bem-sucedida
            moeda_manager.quantidade_moedas -= custo_granada
            moeda_manager.salvar_moedas()
            
            if 'granada' in upgrades:
                upgrades["granada"] += 3  # Adicionar 3 granadas por compra
            else:
                upgrades["granada"] = 3  # Começar com 3 granadas
            
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Grenades Purchased!", VERDE)
        else:
            # Não tem moedas suficientes
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Not enough coins!", VERMELHO)
            
    return resultado