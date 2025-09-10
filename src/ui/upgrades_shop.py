#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja de upgrades do jogo.
"""

import pygame
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

def desenhar_upgrades_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro):
    """
    Desenha a seção de upgrades da loja.
    
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
    desenhar_texto(tela, "UPGRADES", 36, (120, 150, 255), LARGURA // 2, area_conteudo.y + 40)
    
    resultado = None
    
    # Item: Upgrade de Vida
    item_y = area_conteudo.y + 120
    item_rect = pygame.Rect(area_conteudo.x + 50, item_y, area_conteudo.width - 100, 120)
    pygame.draw.rect(tela, (30, 30, 60), item_rect, 0, 8)
    pygame.draw.rect(tela, (70, 70, 150), item_rect, 2, 8)
    
    # Desenhar ícone de coração
    coracao_x = item_rect.x + 50
    coracao_y = item_y + 60
    tamanho_coracao = 30
    
    # Base do coração (dois círculos)
    pygame.draw.circle(tela, (220, 50, 50), 
                      (coracao_x - tamanho_coracao//3, coracao_y - tamanho_coracao//6), 
                      tamanho_coracao//2)
    pygame.draw.circle(tela, (220, 50, 50), 
                      (coracao_x + tamanho_coracao//3, coracao_y - tamanho_coracao//6), 
                      tamanho_coracao//2)
    
    # Triângulo para a ponta do coração
    pontos_triangulo = [
        (coracao_x - tamanho_coracao//1.5, coracao_y - tamanho_coracao//6),
        (coracao_x + tamanho_coracao//1.5, coracao_y - tamanho_coracao//6),
        (coracao_x, coracao_y + tamanho_coracao//1.2)
    ]
    pygame.draw.polygon(tela, (220, 50, 50), pontos_triangulo)
    
    # Brilho no coração
    pygame.draw.circle(tela, (255, 150, 150), 
                      (coracao_x - tamanho_coracao//4, coracao_y - tamanho_coracao//3), 
                      tamanho_coracao//6)
                      
    # Nome do item (movido para depois do ícone)
    desenhar_texto(tela, "HEALTH BOOST", 30, (150, 150, 255), item_rect.x + 200, item_y + 30)
    
    # Descrição e status do item
    vida_status = f"+1 Max Health (Current: {upgrades['vida']})"
    desenhar_texto(tela, vida_status, 22, BRANCO, item_rect.x + 200, item_y + 60)
    
    # Custo do upgrade
    custo_vida = 20
    
    # Botão de compra
    botao_compra_x = item_rect.x + item_rect.width - 130
    botao_compra_y = item_y + 60
    botao_compra_largura = 180
    botao_compra_altura = 50
    rect_compra = pygame.Rect(botao_compra_x - botao_compra_largura//2, 
                             botao_compra_y - botao_compra_altura//2,
                             botao_compra_largura, botao_compra_altura)
    
    # Verificar se o jogador tem moedas suficientes
    pode_comprar = moeda_manager.obter_quantidade() >= custo_vida
    
    # Desenhar botão de compra
    cor_botao = (50, 120, 80)
    cor_hover = (70, 180, 100) 
    hover_compra = rect_compra.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover if hover_compra else cor_botao, rect_compra, 0, 8)
    pygame.draw.rect(tela, (100, 255, 150), rect_compra, 2, 8)
    
    # Ícone de moeda e custo
    moeda_mini_x = botao_compra_x - 50
    moeda_mini_y = botao_compra_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini_x, moeda_mini_y), 12)
    
    # Texto de custo
    desenhar_texto(tela, f"{custo_vida}", 24, BRANCO, botao_compra_x, botao_compra_y)
    
    # Verificar clique no botão de compra
    if clique_ocorreu and rect_compra.collidepoint(mouse_pos):
        if pode_comprar:
            # Compra bem-sucedida
            moeda_manager.quantidade_moedas -= custo_vida
            moeda_manager.salvar_moedas()
            upgrades["vida"] += 1
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Health Upgraded!", VERDE)
        else:
            # Não tem moedas suficientes
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Not enough coins!", VERMELHO)
    
    # Exemplo de um segundo upgrade (descomentá-lo quando você quiser adicionar mais upgrades)

    
    return resultado