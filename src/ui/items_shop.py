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

def desenhar_icone_ampulheta(tela, x, y, tempo_atual):
    """
    Desenha um ícone de ampulheta com efeitos visuais animados.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores da ampulheta
    cor_estrutura = (150, 120, 80)  # Bronze/dourado
    cor_estrutura_escura = (100, 80, 50)
    cor_areia = (255, 215, 0)  # Dourado brilhante
    cor_areia_escura = (200, 165, 0)
    cor_cristal = (220, 220, 255, 100)  # Azul cristalino transparente
    
    # Tamanhos
    largura_ampulheta = 16
    altura_ampulheta = 24
    espessura_borda = 2
    
    # Corpo da ampulheta (formato de dois triângulos)
    # Triângulo superior
    pygame.draw.polygon(tela, cor_estrutura, [
        (x - largura_ampulheta//2, y - altura_ampulheta//2),  # topo esquerdo
        (x + largura_ampulheta//2, y - altura_ampulheta//2),  # topo direito
        (x, y)  # centro
    ])
    
    # Triângulo inferior
    pygame.draw.polygon(tela, cor_estrutura, [
        (x, y),  # centro
        (x - largura_ampulheta//2, y + altura_ampulheta//2),  # base esquerda
        (x + largura_ampulheta//2, y + altura_ampulheta//2)   # base direita
    ])
    
    # Bordas da estrutura
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x - largura_ampulheta//2, y - altura_ampulheta//2),
        (x + largura_ampulheta//2, y - altura_ampulheta//2),
        (x, y)
    ], espessura_borda)
    
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x, y),
        (x - largura_ampulheta//2, y + altura_ampulheta//2),
        (x + largura_ampulheta//2, y + altura_ampulheta//2)
    ], espessura_borda)
    
    # Animação da areia caindo
    tempo_ciclo = (tempo_atual % 4000) / 4000.0  # Ciclo de 4 segundos
    
    # Areia na parte superior (diminuindo com o tempo)
    altura_areia_superior = int((altura_ampulheta//2 - 4) * (1 - tempo_ciclo))
    if altura_areia_superior > 0:
        # Triângulo de areia superior
        areia_topo = y - altura_ampulheta//2 + 2
        areia_base = areia_topo + altura_areia_superior
        largura_areia_topo = largura_ampulheta - 6
        largura_areia_base = int(largura_areia_topo * (altura_areia_superior / (altura_ampulheta//2 - 4)))
        
        pygame.draw.polygon(tela, cor_areia, [
            (x - largura_areia_topo//2, areia_topo),
            (x + largura_areia_topo//2, areia_topo),
            (x - largura_areia_base//2, areia_base),
            (x + largura_areia_base//2, areia_base)
        ])
    
    # Areia na parte inferior (aumentando com o tempo)
    altura_areia_inferior = int((altura_ampulheta//2 - 4) * tempo_ciclo)
    if altura_areia_inferior > 0:
        # Triângulo de areia inferior
        areia_base = y + altura_ampulheta//2 - 2
        areia_topo = areia_base - altura_areia_inferior
        largura_areia_base = largura_ampulheta - 6
        largura_areia_topo = int(largura_areia_base * (altura_areia_inferior / (altura_ampulheta//2 - 4)))
        
        pygame.draw.polygon(tela, cor_areia_escura, [
            (x - largura_areia_base//2, areia_base),
            (x + largura_areia_base//2, areia_base),
            (x - largura_areia_topo//2, areia_topo),
            (x + largura_areia_topo//2, areia_topo)
        ])
    
    # Partículas de areia caindo (no meio)
    if tempo_ciclo > 0.1:  # Só mostrar partículas quando há areia caindo
        for i in range(3):
            particula_y = y + (i - 1) * 2
            if i == 1:  # Partícula central mais brilhante
                pygame.draw.circle(tela, cor_areia, (x, particula_y), 1)
            else:
                pygame.draw.circle(tela, cor_areia_escura, (x, particula_y), 1)
    
    # Suportes da ampulheta (topo e base)
    pygame.draw.rect(tela, cor_estrutura_escura, 
                    (x - largura_ampulheta//2 - 2, y - altura_ampulheta//2 - 3, 
                     largura_ampulheta + 4, 3))
    pygame.draw.rect(tela, cor_estrutura_escura, 
                    (x - largura_ampulheta//2 - 2, y + altura_ampulheta//2, 
                     largura_ampulheta + 4, 3))
    
    # Efeito de brilho temporal (pulsação azul)
    pulso_temporal = (math.sin(tempo_atual / 300) + 1) / 2
    if pulso_temporal > 0.7:
        # Criar superfície temporária para efeito de brilho
        brilho_surf = pygame.Surface((largura_ampulheta + 8, altura_ampulheta + 8), pygame.SRCALPHA)
        alpha_brilho = int(100 * (pulso_temporal - 0.7) / 0.3)
        
        # Contorno brilhante azul
        pygame.draw.polygon(brilho_surf, (100, 150, 255, alpha_brilho), [
            (4, 4),  # topo esquerdo
            (largura_ampulheta + 4, 4),  # topo direito
            (largura_ampulheta//2 + 4, altura_ampulheta//2 + 4),  # centro
            (4, altura_ampulheta + 4),  # base esquerda
            (largura_ampulheta + 4, altura_ampulheta + 4)  # base direita
        ], 2)
        
        # Aplicar o brilho
        tela.blit(brilho_surf, (x - largura_ampulheta//2 - 4, y - altura_ampulheta//2 - 4))
    
    # Pequenos cristais de tempo ao redor (efeito mágico)
    for i in range(4):
        angulo = (tempo_atual / 200 + i * 90) % 360
        raio_cristal = 20
        cristal_x = x + int(raio_cristal * math.cos(math.radians(angulo)))
        cristal_y = y + int(raio_cristal * math.sin(math.radians(angulo)))
        
        # Pequenos diamantes cristalinos
        tamanho_cristal = 2 + int(pulso_temporal * 2)
        pygame.draw.polygon(tela, (150, 200, 255), [
            (cristal_x, cristal_y - tamanho_cristal),
            (cristal_x + tamanho_cristal, cristal_y),
            (cristal_x, cristal_y + tamanho_cristal),
            (cristal_x - tamanho_cristal, cristal_y)
        ])

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
    
    # Item 1: Granada
    item1_y = area_conteudo.y + 100
    item1_rect = pygame.Rect(area_conteudo.x + 30, item1_y, area_conteudo.width - 60, 100)
    pygame.draw.rect(tela, (40, 60, 40), item1_rect, 0, 8)
    pygame.draw.rect(tela, (80, 150, 80), item1_rect, 2, 8)
    
    # Desenhar ícone de granada
    granada_x = item1_rect.x + 40
    granada_y = item1_y + 50
    tamanho_granada = 16

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
    desenhar_texto(tela, "GRENADE", 26, (150, 220, 150), item1_rect.x + 150, item1_y + 25)
    
    # Descrição e status do item
    if 'granada' not in upgrades:
        granada_status = "Explosive area damage! (Not owned)"
    else:
        granada_status = f"Grenades: {upgrades['granada']}"
    
    desenhar_texto(tela, granada_status, 18, BRANCO, item1_rect.x + 150, item1_y + 50)
    desenhar_texto(tela, "Press Q to select, Mouse to throw", 14, (200, 200, 200), 
                  item1_rect.x + 150, item1_y + 70)
    
    # Custo do item
    custo_granada = 25
    
    # Botão de compra
    botao_compra1_x = item1_rect.x + item1_rect.width - 100
    botao_compra1_y = item1_y + 50
    botao_compra1_largura = 120
    botao_compra1_altura = 40
    rect_compra1 = pygame.Rect(botao_compra1_x - botao_compra1_largura//2, 
                              botao_compra1_y - botao_compra1_altura//2,
                              botao_compra1_largura, botao_compra1_altura)
    
    # Verificar se o jogador tem moedas suficientes
    pode_comprar1 = moeda_manager.obter_quantidade() >= custo_granada
    
    # Desenhar botão de compra
    cor_botao1 = (60, 120, 60) if pode_comprar1 else (40, 80, 40)
    cor_hover1 = (80, 160, 80) if pode_comprar1 else (50, 90, 50)
    hover_compra1 = rect_compra1.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover1 if hover_compra1 else cor_botao1, rect_compra1, 0, 8)
    pygame.draw.rect(tela, (120, 220, 120), rect_compra1, 2, 8)
    
    # Ícone de moeda e custo
    moeda_mini1_x = botao_compra1_x - 30
    moeda_mini1_y = botao_compra1_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini1_x, moeda_mini1_y), 8)
    
    # Texto de custo
    desenhar_texto(tela, f"{custo_granada}", 20, BRANCO, botao_compra1_x + 10, botao_compra1_y)
    
    # Verificar clique no botão de compra da granada
    if clique_ocorreu and rect_compra1.collidepoint(mouse_pos):
        if pode_comprar1:
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
    
    # Item 2: Hourglass of Balance
    item2_y = area_conteudo.y + 220
    item2_rect = pygame.Rect(area_conteudo.x + 30, item2_y, area_conteudo.width - 60, 100)
    pygame.draw.rect(tela, (40, 40, 80), item2_rect, 0, 8)
    pygame.draw.rect(tela, (80, 80, 180), item2_rect, 2, 8)
    
    # Desenhar ícone da ampulheta
    ampulheta_x = item2_rect.x + 40
    ampulheta_y = item2_y + 50
    desenhar_icone_ampulheta(tela, ampulheta_x, ampulheta_y, tempo_atual)
    
    # Nome do item
    desenhar_texto(tela, "HOURGLASS OF BALANCE", 26, (150, 150, 255), item2_rect.x + 180, item2_y + 25)
    
    # Descrição e status do item
    if 'ampulheta' not in upgrades:
        ampulheta_status = "Slows down time for precision! (Not owned)"
    else:
        ampulheta_status = f"Time Distortions: {upgrades['ampulheta']}"
    
    desenhar_texto(tela, ampulheta_status, 18, BRANCO, item2_rect.x + 180, item2_y + 50)
    desenhar_texto(tela, "Press Q to activate slow motion", 14, (200, 200, 200), 
                  item2_rect.x + 180, item2_y + 70)
    
    # Custo da ampulheta
    custo_ampulheta = 40
    
    # Botão de compra
    botao_compra2_x = item2_rect.x + item2_rect.width - 100
    botao_compra2_y = item2_y + 50
    botao_compra2_largura = 120
    botao_compra2_altura = 40
    rect_compra2 = pygame.Rect(botao_compra2_x - botao_compra2_largura//2, 
                              botao_compra2_y - botao_compra2_altura//2,
                              botao_compra2_largura, botao_compra2_altura)
    
    # Verificar se o jogador tem moedas suficientes
    pode_comprar2 = moeda_manager.obter_quantidade() >= custo_ampulheta
    
    # Desenhar botão de compra
    cor_botao2 = (60, 60, 150) if pode_comprar2 else (40, 40, 80)
    cor_hover2 = (80, 80, 200) if pode_comprar2 else (50, 50, 100)
    hover_compra2 = rect_compra2.collidepoint(mouse_pos)
    
    pygame.draw.rect(tela, cor_hover2 if hover_compra2 else cor_botao2, rect_compra2, 0, 8)
    pygame.draw.rect(tela, (120, 120, 255), rect_compra2, 2, 8)
    
    # Ícone de moeda e custo
    moeda_mini2_x = botao_compra2_x - 30
    moeda_mini2_y = botao_compra2_y
    pygame.draw.circle(tela, AMARELO, (moeda_mini2_x, moeda_mini2_y), 8)
    
    # Texto de custo
    desenhar_texto(tela, f"{custo_ampulheta}", 20, BRANCO, botao_compra2_x + 10, botao_compra2_y)
    
    # Verificar clique no botão de compra da ampulheta
    if clique_ocorreu and rect_compra2.collidepoint(mouse_pos):
        if pode_comprar2:
            # Compra bem-sucedida
            moeda_manager.quantidade_moedas -= custo_ampulheta
            moeda_manager.salvar_moedas()
            
            if 'ampulheta' in upgrades:
                upgrades["ampulheta"] += 2  # Adicionar 2 usos por compra
            else:
                upgrades["ampulheta"] = 2  # Começar com 2 usos
            
            salvar_upgrades(upgrades)
            pygame.mixer.Channel(4).play(som_compra)
            resultado = ("Hourglass of Balance Purchased!", AZUL)
        else:
            # Não tem moedas suficientes
            pygame.mixer.Channel(4).play(som_erro)
            resultado = ("Not enough coins!", VERMELHO)
            
    return resultado