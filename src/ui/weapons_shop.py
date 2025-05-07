#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja de armas do jogo.
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

def desenhar_weapons_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro):
    """
    Desenha a seção de armas da loja.
    
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
    desenhar_texto(tela, "WEAPONS", 36, (255, 120, 120), LARGURA // 2, area_conteudo.y + 40)
    
    resultado = None
    
    # Item: Espingarda
    item_y = area_conteudo.y + 120
    item_rect = pygame.Rect(area_conteudo.x + 50, item_y, area_conteudo.width - 100, 120)
    pygame.draw.rect(tela, (50, 30, 30), item_rect, 0, 8)
    pygame.draw.rect(tela, (150, 70, 70), item_rect, 2, 8)
    
    # Desenhar ícone de espingarda
    espingarda_x = item_rect.x + 50
    espingarda_y = item_y + 60
    
    # Desenhar uma espingarda estilizada
    # Cano
    pygame.draw.rect(tela, (180, 180, 190), (espingarda_x - 20, espingarda_y - 5, 40, 10), 0, 3)
    # Corpo
    pygame.draw.rect(tela, (120, 80, 40), (espingarda_x, espingarda_y - 8, 20, 25), 0, 3)
    # Coronha
    pontos_coronha = [
        (espingarda_x + 20, espingarda_y - 3),
        (espingarda_x + 45, espingarda_y - 8),
        (espingarda_x + 45, espingarda_y + 12),
        (espingarda_x + 20, espingarda_y + 7)
    ]
    pygame.draw.polygon(tela, (150, 100, 50), pontos_coronha)
    
    # Nome do item (movido para depois do ícone)
    desenhar_texto(tela, "SHOTGUN", 30, (255, 150, 150), item_rect.x + 200, item_y + 30)
    
    # Descrição e status do item
    shotgun_status = f"Tiros por partida: {upgrades.get('espingarda', 0)}"
    desenhar_texto(tela, shotgun_status, 22, BRANCO, item_rect.x + 200, item_y + 60)
    
    # Custo do upgrade
    custo_espingarda = 15
    
    # Botão de compra
    botao_compra_x = item_rect.x + item_rect.width - 130
    botao_compra_y = item_y + 60
    botao_compra_largura = 180
    botao_compra_altura = 50
    rect_compra = pygame.Rect(botao_compra_x - botao_compra_largura//2, 
                             botao_compra_y - botao_compra_altura//2,
                             botao_compra_largura, botao_compra_altura)
    
    # Verificar se o jogador tem moedas suficientes
    pode_comprar = moeda_manager.obter_quantidade() >= custo_espingarda
    
    # Desenhar botão de compra
    cor_botao = (180, 100, 50) if pode_comprar else (100, 50, 50)
    cor_hover = (220, 140, 60) if pode_comprar else (130, 60, 60)
    hover_compra = rect_compra.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover if hover_compra else cor_botao, rect_compra, 0, 8)
    pygame.draw.rect(tela, (255, 180, 100), rect_compra, 2, 8)
    
    # Ícone de moeda e custo
    moeda_mini_x = botao_compra_x - 50
    moeda_mini_y = botao_compra_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini_x, moeda_mini_y), 12)
    
    # Texto de custo
    desenhar_texto(tela, f"{custo_espingarda}", 24, BRANCO, botao_compra_x, botao_compra_y)
    
    # Verificar clique no botão de compra
    if clique_ocorreu and rect_compra.collidepoint(mouse_pos):
        if pode_comprar:
            # Compra bem-sucedida
            moeda_manager.quantidade_moedas -= custo_espingarda
            moeda_manager.salvar_moedas()
            
            if 'espingarda' in upgrades:
                upgrades["espingarda"] += 1
            else:
                upgrades["espingarda"] = 1
            
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Shotgun Upgraded!", VERDE)
        else:
            # Não tem moedas suficientes
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Not enough coins!", VERMELHO)
    
    # Exemplo de um segundo item de arma (descomentá-lo quando você quiser adicionar mais armas)

    
    return resultado