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
    
    # Item: Espingarda
    item_y = area_conteudo.y + 120
    item_rect = pygame.Rect(area_conteudo.x + 50, item_y, area_conteudo.width - 100, 120)
    pygame.draw.rect(tela, (50, 30, 30), item_rect, 0, 8)
    pygame.draw.rect(tela, (150, 70, 70), item_rect, 2, 8)
    
    # Desenhar ícone de espingarda com o mesmo estilo do jogo
    espingarda_x = item_rect.x + 50
    espingarda_y = item_y + 60

    # Cores para a espingarda - correspondendo à espingarda do jogador
    cor_metal = (180, 180, 190)  # Metal prateado
    cor_cano = (100, 100, 110)   # Cano escuro
    cor_madeira = (120, 80, 40)  # Madeira escura
    cor_madeira_clara = (150, 100, 50)  # Madeira clara

    # Desenhar a espingarda com o mesmo estilo usado na partida
    # Direção da espingarda (apontando para a direita)
    dx = 1
    dy = 0

    # DESENHO COMPLETO DA ESPINGARDA 

    # 1. Cano principal (mais grosso e com gradiente)
    comprimento_arma = 35
    for i in range(4):
        offset = i - 1.5
        pygame.draw.line(tela, cor_cano, 
                    (espingarda_x, espingarda_y + offset), 
                    (espingarda_x + comprimento_arma, espingarda_y + offset), 3)

    # 2. Boca do cano com destaque
    ponta_x = espingarda_x + comprimento_arma
    ponta_y = espingarda_y
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 5)
    pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 3)

    # 3. Suporte sob o cano
    meio_cano_x = espingarda_x + (comprimento_arma * 0.6)
    meio_cano_y = espingarda_y
    pygame.draw.line(tela, cor_metal, 
                    (meio_cano_x, meio_cano_y + 3), 
                    (meio_cano_x, meio_cano_y - 3), 3)

    # 4. Corpo central / Mecanismo (mais detalhado)
    corpo_x = espingarda_x + 8
    corpo_y = espingarda_y
    # Base do corpo
    pygame.draw.circle(tela, cor_metal, (int(corpo_x), int(corpo_y)), 7)
    # Detalhes do mecanismo
    pygame.draw.circle(tela, (50, 50, 55), (int(corpo_x), int(corpo_y)), 4)
    # Reflete mecanismo (brilho)
    brilho_x = corpo_x - dx + 1
    brilho_y = corpo_y - dy + 1
    pygame.draw.circle(tela, (220, 220, 230), (int(brilho_x), int(brilho_y)), 2)

    # 5. Coronha mais elegante (formato mais curvado)
    # Pontos para a coronha em formato mais curvo
    # Base conectando ao corpo
    coronha_base_x = corpo_x - 2
    coronha_base_y = corpo_y

    # Pontos superiores e inferiores no início da coronha
    sup_inicio_x = coronha_base_x
    sup_inicio_y = coronha_base_y - 6
    inf_inicio_x = coronha_base_x
    inf_inicio_y = coronha_base_y + 6

    # Pontos do final da coronha (mais estreitos)
    sup_fim_x = coronha_base_x - 15
    sup_fim_y = coronha_base_y - 4
    inf_fim_x = coronha_base_x - 15
    inf_fim_y = coronha_base_y + 4

    # Desenhar coronha principal
    pygame.draw.polygon(tela, cor_madeira, [
        (sup_inicio_x, sup_inicio_y),
        (inf_inicio_x, inf_inicio_y),
        (inf_fim_x, inf_fim_y),
        (sup_fim_x, sup_fim_y)
    ])

    # 6. Detalhes da coronha (linhas de madeira)
    for i in range(1, 4):
        linha_x1 = coronha_base_x - (i * 3)
        linha_y1 = coronha_base_y - (6 - i * 0.5)
        linha_x2 = coronha_base_x - (i * 3)
        linha_y2 = coronha_base_y + (6 - i * 0.5)
        pygame.draw.line(tela, cor_madeira_clara, 
                        (linha_x1, linha_y1), 
                        (linha_x2, linha_y2), 1)

    # 7. Gatilho e proteção (mais detalhados)
    # Base do gatilho
    gatilho_base_x = corpo_x - 3
    gatilho_base_y = corpo_y

    # Proteção do gatilho (arco)
    pygame.draw.arc(tela, cor_metal, 
                [gatilho_base_x - 5, gatilho_base_y - 5, 10, 10],
                math.pi/2, math.pi * 1.5, 2)

    # Gatilho (linha curva)
    gatilho_x = gatilho_base_x
    gatilho_y = gatilho_base_y + 2
    pygame.draw.line(tela, (40, 40, 40), 
                    (gatilho_base_x, gatilho_base_y), 
                    (gatilho_x, gatilho_y), 2)

    # 8. Efeito de brilho no metal
    pygame.draw.line(tela, (220, 220, 230), 
                    (espingarda_x, espingarda_y + 2), 
                    (corpo_x, corpo_y + 2), 1)

    # 9. Efeito de energia/carregamento
    # Pulsar baseado no tempo atual
    pulso = (math.sin(tempo_atual / 150) + 1) / 2  # Valor entre 0 e 1
    cor_energia = (50 + int(pulso * 200), 50 + int(pulso * 150), 255)

    # Linha de energia ao longo do cano
    energia_width = 2 + int(pulso * 2)
    meio_cano2_x = espingarda_x + (comprimento_arma * 0.3)
    meio_cano2_y = espingarda_y
    pygame.draw.line(tela, cor_energia, 
                    (meio_cano2_x, meio_cano2_y), 
                    (ponta_x, ponta_y), energia_width)
    
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