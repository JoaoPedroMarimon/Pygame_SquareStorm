#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a seção de armas da loja do jogo.
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
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # ===== ITEM 1: ESPINGARDA =====
    item1_y = area_conteudo.y + 100
    item1_rect = pygame.Rect(area_conteudo.x + 30, item1_y, area_conteudo.width - 60, 100)
    pygame.draw.rect(tela, (50, 30, 30), item1_rect, 0, 8)
    pygame.draw.rect(tela, (150, 70, 70), item1_rect, 2, 8)
    
    # Desenhar ícone de espingarda
    espingarda_x = item1_rect.x + 40
    espingarda_y = item1_y + 50

    # Cores para a espingarda
    cor_metal = (180, 180, 190)
    cor_cano = (100, 100, 110)
    cor_madeira = (120, 80, 40)
    cor_madeira_clara = (150, 100, 50)

    # Desenhar espingarda (mesmo estilo do jogo)
    comprimento_arma = 30
    for i in range(4):
        offset = i - 1.5
        pygame.draw.line(tela, cor_cano, 
                    (espingarda_x, espingarda_y + offset), 
                    (espingarda_x + comprimento_arma, espingarda_y + offset), 2)

    # Boca do cano
    ponta_x = espingarda_x + comprimento_arma
    ponta_y = espingarda_y
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 4)
    pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 2)

    # Corpo central
    corpo_x = espingarda_x + 6
    corpo_y = espingarda_y
    pygame.draw.circle(tela, cor_metal, (int(corpo_x), int(corpo_y)), 6)
    pygame.draw.circle(tela, (50, 50, 55), (int(corpo_x), int(corpo_y)), 3)

    # Coronha
    coronha_base_x = corpo_x - 2
    coronha_base_y = corpo_y
    pygame.draw.polygon(tela, cor_madeira, [
        (coronha_base_x, coronha_base_y - 5),
        (coronha_base_x, coronha_base_y + 5),
        (coronha_base_x - 12, coronha_base_y + 3),
        (coronha_base_x - 12, coronha_base_y - 3)
    ])

    # Efeito de energia
    pulso = (math.sin(tempo_atual / 150) + 1) / 2
    cor_energia = (50 + int(pulso * 200), 50 + int(pulso * 150), 255)
    pygame.draw.line(tela, cor_energia, 
                    (espingarda_x + 8, espingarda_y), 
                    (ponta_x, ponta_y), 2 + int(pulso * 2))
    
    # Nome e descrição da espingarda
    desenhar_texto(tela, "SHOTGUN", 26, (255, 150, 150), item1_rect.x + 140, item1_y + 20)
    shotgun_status = f"Munição: {upgrades.get('espingarda', 0)}"
    desenhar_texto(tela, shotgun_status, 18, BRANCO, item1_rect.x + 140, item1_y + 45)
    desenhar_texto(tela, "Disparo múltiplo devastador", 16, (200, 200, 200), item1_rect.x + 140, item1_y + 65)
    
    # Botão de compra da espingarda
    custo_espingarda = 15
    botao1_x = item1_rect.x + item1_rect.width - 100
    botao1_y = item1_y + 50
    botao1_largura = 150
    botao1_altura = 40
    rect_compra1 = pygame.Rect(botao1_x - botao1_largura//2, 
                              botao1_y - botao1_altura//2,
                              botao1_largura, botao1_altura)
    
    pode_comprar1 = moeda_manager.obter_quantidade() >= custo_espingarda
    cor_botao1 = (180, 100, 50) if pode_comprar1 else (100, 50, 50)
    cor_hover1 = (220, 140, 60) if pode_comprar1 else (130, 60, 60)
    hover_compra1 = rect_compra1.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover1 if hover_compra1 else cor_botao1, rect_compra1, 0, 6)
    pygame.draw.rect(tela, (255, 180, 100), rect_compra1, 2, 6)
    
    # Ícone de moeda e custo
    moeda_mini_x1 = botao1_x - 35
    moeda_mini_y1 = botao1_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini_x1, moeda_mini_y1), 8)
    desenhar_texto(tela, f"{custo_espingarda}", 20, BRANCO, botao1_x, botao1_y)
    
    # Verificar clique na espingarda
    if clique_ocorreu and rect_compra1.collidepoint(mouse_pos):
        if pode_comprar1:
            moeda_manager.quantidade_moedas -= custo_espingarda
            moeda_manager.salvar_moedas()
            
            if 'espingarda' in upgrades:
                upgrades["espingarda"] += 10  # Adiciona 10 tiros
            else:
                upgrades["espingarda"] = 10
            
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Shotgun +10 munição comprada!", VERDE)
        else:
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Moedas insuficientes!", VERMELHO)
    
    # ===== ITEM 2: METRALHADORA =====
    item2_y = area_conteudo.y + 220
    item2_rect = pygame.Rect(area_conteudo.x + 30, item2_y, area_conteudo.width - 60, 100)
    pygame.draw.rect(tela, (60, 35, 20), item2_rect, 0, 8)  # Cor mais escura para metralhadora
    pygame.draw.rect(tela, (255, 140, 70), item2_rect, 2, 8)  # Borda laranja
    
    # Desenhar ícone de metralhadora
    metra_x = item2_rect.x + 40
    metra_y = item2_y + 50

    # Cores da metralhadora
    cor_metal_escuro = (60, 60, 70)
    cor_metal_claro = (120, 120, 130)
    cor_cano_metra = (40, 40, 45)
    cor_laranja = (255, 140, 0)

    # Desenhar metralhadora
    comprimento_metra = 35
    
    # Cano principal (mais grosso, múltiplas linhas)
    for i in range(6):
        offset = (i - 2.5) * 0.6
        espessura = 3 if abs(i - 2.5) < 1 else 2
        cor_linha = cor_cano_metra if abs(i - 2.5) < 1 else cor_metal_escuro
        pygame.draw.line(tela, cor_linha,
                    (metra_x, metra_y + offset),
                    (metra_x + comprimento_metra, metra_y + offset), espessura)

    # Boca do cano com supressor
    ponta_metra_x = metra_x + comprimento_metra
    ponta_metra_y = metra_y
    pygame.draw.circle(tela, cor_metal_escuro, (int(ponta_metra_x), int(ponta_metra_y)), 6)
    pygame.draw.circle(tela, cor_cano_metra, (int(ponta_metra_x), int(ponta_metra_y)), 3)

    # Corpo principal
    corpo_metra_x = metra_x + 10
    corpo_metra_y = metra_y
    corpo_rect = pygame.Rect(corpo_metra_x - 6, corpo_metra_y - 4, 12, 8)
    pygame.draw.rect(tela, cor_metal_escuro, corpo_rect)
    pygame.draw.rect(tela, cor_metal_claro, corpo_rect, 1)

    # Carregador
    carregador_x = corpo_metra_x - 2
    carregador_y = corpo_metra_y + 6
    carregador_rect = pygame.Rect(carregador_x - 3, carregador_y, 6, 12)
    pygame.draw.rect(tela, cor_metal_escuro, carregador_rect)
    pygame.draw.rect(tela, cor_laranja, carregador_rect, 1)

    # Coronha retrátil
    punho_x = metra_x - 6
    punho_y = metra_y
    pygame.draw.line(tela, cor_metal_claro, (corpo_metra_x, corpo_metra_y), (punho_x, punho_y + 8), 4)
    pygame.draw.line(tela, cor_metal_claro, (punho_x, punho_y), (punho_x - 10, punho_y), 3)

    # Efeito de aquecimento/energia
    calor_intensidade = (tempo_atual % 1000) / 1000.0
    cor_calor = (255, int(100 + calor_intensidade * 155), 0)
    
    # Linhas de calor saindo do cano
    for i in range(3):
        heat_x = ponta_metra_x - (5 + i * 3) + random.uniform(-1, 1)
        heat_y = ponta_metra_y + random.uniform(-1, 1)
        pygame.draw.circle(tela, cor_calor, (int(heat_x), int(heat_y)), 1)

    # Brilho no cano
    pygame.draw.line(tela, cor_laranja, (metra_x, metra_y), (ponta_metra_x, ponta_metra_y), 1)
    
    # Nome e descrição da metralhadora
    desenhar_texto(tela, "MACHINE GUN", 26, (255, 180, 70), item2_rect.x + 140, item2_y + 20)
    metra_status = f"Munição: {upgrades.get('metralhadora', 0)}"
    desenhar_texto(tela, metra_status, 18, BRANCO, item2_rect.x + 140, item2_y + 45)
    desenhar_texto(tela, "Cadência de tiro extrema", 16, (200, 200, 200), item2_rect.x + 140, item2_y + 65)
    
    # Botão de compra da metralhadora
    custo_metralhadora = 25  # Mais cara que a espingarda
    botao2_x = item2_rect.x + item2_rect.width - 100
    botao2_y = item2_y + 50
    botao2_largura = 150
    botao2_altura = 40
    rect_compra2 = pygame.Rect(botao2_x - botao2_largura//2, 
                              botao2_y - botao2_altura//2,
                              botao2_largura, botao2_altura)
    
    pode_comprar2 = moeda_manager.obter_quantidade() >= custo_metralhadora
    cor_botao2 = (180, 120, 30) if pode_comprar2 else (100, 60, 20)
    cor_hover2 = (220, 150, 50) if pode_comprar2 else (130, 80, 30)
    hover_compra2 = rect_compra2.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover2 if hover_compra2 else cor_botao2, rect_compra2, 0, 6)
    pygame.draw.rect(tela, (255, 200, 100), rect_compra2, 2, 6)
    
    # Ícone de moeda e custo
    moeda_mini_x2 = botao2_x - 35
    moeda_mini_y2 = botao2_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini_x2, moeda_mini_y2), 8)
    desenhar_texto(tela, f"{custo_metralhadora}", 20, BRANCO, botao2_x, botao2_y)
    
    # Verificar clique na metralhadora
    if clique_ocorreu and rect_compra2.collidepoint(mouse_pos):
        if pode_comprar2:
            moeda_manager.quantidade_moedas -= custo_metralhadora
            moeda_manager.salvar_moedas()
            
            if 'metralhadora' in upgrades:
                upgrades["metralhadora"] += 50  # Adiciona 50 tiros (mais munição)
            else:
                upgrades["metralhadora"] = 50
            
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Machine Gun +50 munição comprada!", VERDE)
        else:
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Moedas insuficientes!", VERMELHO)
    
    # Adicionar instruções na parte inferior
    instrucoes_y = area_conteudo.y + area_conteudo.height - 30
    desenhar_texto(tela, "Clique nos botões para comprar munição para as armas", 16, (180, 180, 180), 
                  area_conteudo.x + area_conteudo.width//2, instrucoes_y)
    
    return resultado