#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a seção de armas da loja do jogo.
Com sistema de preços dinâmicos integrado.
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import desenhar_texto
import json
import os

# Importar o sistema de pricing
from src.game.pricing_system import PricingManager, aplicar_pricing_sistema

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

def desenhar_icone_espingarda(tela, x, y, tempo_atual):
    """
    Desenha um ícone de espingarda com efeitos visuais.
    """
    # Cores para a espingarda
    cor_metal = (180, 180, 190)
    cor_cano = (100, 100, 110)
    cor_madeira = (120, 80, 40)

    # Desenhar espingarda
    comprimento_arma = 30
    for i in range(4):
        offset = i - 1.5
        pygame.draw.line(tela, cor_cano, 
                    (x, y + offset), 
                    (x + comprimento_arma, y + offset), 2)

    # Boca do cano
    ponta_x = x + comprimento_arma
    ponta_y = y
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 4)
    pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 2)

    # Corpo central
    corpo_x = x + 6
    corpo_y = y
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
                    (x + 8, y), 
                    (ponta_x, ponta_y), 2 + int(pulso * 2))

def desenhar_icone_metralhadora(tela, x, y, tempo_atual):
    """
    Desenha um ícone de metralhadora com efeitos visuais.
    """
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
                    (x, y + offset),
                    (x + comprimento_metra, y + offset), espessura)

    # Boca do cano com supressor
    ponta_metra_x = x + comprimento_metra
    ponta_metra_y = y
    pygame.draw.circle(tela, cor_metal_escuro, (int(ponta_metra_x), int(ponta_metra_y)), 6)
    pygame.draw.circle(tela, cor_cano_metra, (int(ponta_metra_x), int(ponta_metra_y)), 3)

    # Corpo principal
    corpo_metra_x = x + 10
    corpo_metra_y = y
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
    punho_x = x - 6
    punho_y = y
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
    pygame.draw.line(tela, cor_laranja, (x, y), (ponta_metra_x, ponta_metra_y), 1)

def desenhar_weapons_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_y=0):
    """
    Desenha a seção de armas da loja com sistema de preços dinâmicos e scroll.
    
    Args:
        tela: Superfície principal do jogo
        area_conteudo: Retângulo definindo a área de conteúdo
        moeda_manager: Gerenciador de moedas
        upgrades: Dicionário com os upgrades do jogador
        mouse_pos: Posição atual do mouse
        clique_ocorreu: Se houve clique neste frame
        som_compra: Som para compra bem-sucedida
        som_erro: Som para erro na compra
        scroll_y: Posição atual do scroll (padrão: 0)
        
    Returns:
        Tupla (mensagem, cor, max_scroll) ou (None, None, max_scroll)
    """
    # Inicializar sistema de pricing
    pricing_manager = PricingManager()
    
    # Título da seção
    desenhar_texto(tela, "WEAPONS", 36, (255, 120, 120), LARGURA // 2, area_conteudo.y + 30)
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # Configurações dos itens
    altura_item = 120
    espaco_entre_itens = 30
    margem_superior = 70
    margem_lateral = 35
    margem_clipping = 15
    
    # Lista de armas para facilitar a adição de novas armas
    armas_loja = [
        {
            "key": "espingarda",
            "nome": "SHOTGUN",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "High damage spread shot",
            "cor_fundo": (50, 30, 30),
            "cor_borda": (150, 70, 70),
            "cor_botao": (180, 100, 50),
            "cor_hover": (220, 140, 60),
            "cor_texto": (255, 150, 150),
            "cor_resultado": VERDE,
            "icone_func": "espingarda"
        },
        {
            "key": "metralhadora",
            "nome": "MACHINE GUN",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Rapid fire with high capacity",
            "cor_fundo": (60, 35, 20),
            "cor_borda": (255, 140, 70),
            "cor_botao": (180, 120, 30),
            "cor_hover": (220, 150, 50),
            "cor_texto": (255, 180, 70),
            "cor_resultado": VERDE,
            "icone_func": "metralhadora"
        }
        
    ]
    
    # Aplicar sistema de pricing às armas
    armas_loja = aplicar_pricing_sistema(armas_loja, pricing_manager)
    
    # Calcular altura total necessária para todos os itens
    altura_total_conteudo = len(armas_loja) * (altura_item + espaco_entre_itens) + espaco_entre_itens + (margem_clipping * 2)
    area_scroll_altura = area_conteudo.height - margem_superior
    max_scroll = max(0, altura_total_conteudo - area_scroll_altura)
    
    # Criar uma superfície para o conteúdo dos itens com clipping
    area_scroll_y = area_conteudo.y + margem_superior
    conteudo_surf = pygame.Surface((area_conteudo.width, area_scroll_altura), pygame.SRCALPHA)
    conteudo_surf.fill((0, 0, 0, 0))  # Transparente
    
    # Desenhar fundo da área de scroll
    pygame.draw.rect(conteudo_surf, (20, 20, 50, 150), (0, 0, area_conteudo.width, area_scroll_altura), 0, 10)
    pygame.draw.rect(conteudo_surf, (70, 70, 130), (0, 0, area_conteudo.width, area_scroll_altura), 2, 10)
    
    # Definir área de clipping para os itens
    cliprect = pygame.Rect(margem_clipping, margem_clipping, 
                          area_conteudo.width - (margem_clipping * 2), 
                          area_scroll_altura - (margem_clipping * 2))
    conteudo_surf.set_clip(cliprect)
    
    # Desenhar cada arma na superfície de conteúdo
    for i, arma in enumerate(armas_loja):
        # Calcular posição Y do item considerando o scroll e margem de clipping
        y_item_relativo = i * (altura_item + espaco_entre_itens) + espaco_entre_itens + margem_clipping - scroll_y
        
        # Se o item está fora da área visível, não desenhar
        if (y_item_relativo + altura_item < margem_clipping or 
            y_item_relativo > area_scroll_altura - margem_clipping):
            continue
        
        # Retângulo do item na superfície de conteúdo
        item_rect = pygame.Rect(margem_lateral, y_item_relativo, 
                               area_conteudo.width - (margem_lateral * 2), altura_item)
        
        # Cor baseada na disponibilidade
        if not arma.get("pode_comprar", True):
            # Arma esgotada
            cor_fundo = (arma["cor_fundo"][0]//3, arma["cor_fundo"][1]//3, arma["cor_fundo"][2]//3)
            cor_borda = (100, 50, 50)  # Vermelho escuro para esgotado
        else:
            cor_fundo = arma["cor_fundo"]
            cor_borda = arma["cor_borda"]
        
        # Desenhar fundo do item
        pygame.draw.rect(conteudo_surf, cor_fundo, item_rect, 0, 8)
        pygame.draw.rect(conteudo_surf, cor_borda, item_rect, 2, 8)
        
        # Se esgotado, adicionar overlay
        if not arma.get("pode_comprar", True):
            overlay_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            overlay_surf.fill((0, 0, 0, 120))
            conteudo_surf.blit(overlay_surf, (item_rect.x, item_rect.y))
        
        # Desenhar ícone da arma
        icone_x = item_rect.x + 60
        icone_y = y_item_relativo + altura_item // 2
        
        if arma["icone_func"] == "espingarda":
            desenhar_icone_espingarda(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "metralhadora":
            desenhar_icone_metralhadora(conteudo_surf, icone_x, icone_y, tempo_atual)
        
        # Nome da arma
        cor_texto = arma["cor_texto"] if arma.get("pode_comprar", True) else (100, 100, 100)
        desenhar_texto(conteudo_surf, arma["nome"], 24, cor_texto, 
                      item_rect.x + 170, y_item_relativo + 20)
        
        # Descrição e status da arma
        if arma["key"] not in upgrades or upgrades[arma["key"]] == 0:
            status = f"{arma['descricao']} (No ammo)"
        else:
            status = f"Ammunition: {upgrades[arma['key']]}"
        
        desenhar_texto(conteudo_surf, status, 15, BRANCO if arma.get("pode_comprar", True) else (120, 120, 120), 
                      item_rect.x + 170, y_item_relativo + 40)
        
        # Informações de limite e próximo preço
        info_limite = arma.get("info_limite", "")
        desenhar_texto(conteudo_surf, info_limite, 12, (180, 180, 180), 
                      item_rect.x + 170, y_item_relativo + 58)
        
        # Próximo preço (se houver)
        if arma.get("proximo_preco") and arma.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, f"Next: {arma['proximo_preco']} coins", 11, (200, 200, 100), 
                          item_rect.x + 170, y_item_relativo + 75)
        elif not arma.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, "SOLD OUT", 14, VERMELHO, 
                          item_rect.x + 170, y_item_relativo + 75)
        
        # Informações adicionais da arma
        desenhar_texto(conteudo_surf, arma["info_extra"], 10, (150, 150, 150), 
                      item_rect.x + 170, y_item_relativo + 92)
        
        # Botão de compra
        botao_largura = 120
        botao_altura = 35
        botao_x_relativo = item_rect.x + item_rect.width - 70
        botao_y_relativo = y_item_relativo + altura_item // 2
        
        rect_compra_relativo = pygame.Rect(botao_x_relativo - botao_largura//2, 
                                         botao_y_relativo - botao_altura//2,
                                         botao_largura, botao_altura)
        
        # Verificar se o jogador tem moedas suficientes e se pode comprar
        pode_comprar = (moeda_manager.obter_quantidade() >= arma["custo"] and 
                       arma.get("pode_comprar", True))
        
        # Calcular posição real do botão na tela para verificar hover e clique
        botao_x_real = area_conteudo.x + botao_x_relativo
        botao_y_real = area_scroll_y + botao_y_relativo
        rect_compra_real = pygame.Rect(botao_x_real - botao_largura//2, 
                                      botao_y_real - botao_altura//2,
                                      botao_largura, botao_altura)
        
        # Verificar hover
        hover_compra = (rect_compra_real.collidepoint(mouse_pos) and 
                       area_scroll_y <= botao_y_real <= area_scroll_y + area_scroll_altura and
                       pode_comprar)
        
        # Cores do botão baseadas na capacidade de compra
        if not arma.get("pode_comprar", True):
            # Esgotado
            cor_botao = (80, 40, 40)
            cor_hover = (80, 40, 40)
        elif pode_comprar:
            # Pode comprar
            cor_botao = arma["cor_botao"]
            cor_hover = arma["cor_hover"]
        else:
            # Sem moedas suficientes
            cor_botao = (arma["cor_botao"][0]//3, arma["cor_botao"][1]//3, arma["cor_botao"][2]//3)
            cor_hover = cor_botao
        
        # Desenhar botão de compra na superfície de conteúdo
        pygame.draw.rect(conteudo_surf, cor_hover if hover_compra else cor_botao, 
                        rect_compra_relativo, 0, 6)
        pygame.draw.rect(conteudo_surf, arma["cor_borda"], rect_compra_relativo, 2, 6)
        
        # Ícone de moeda e custo
        moeda_mini_x = botao_x_relativo - 25
        moeda_mini_y = botao_y_relativo
        pygame.draw.circle(conteudo_surf, AMARELO, (moeda_mini_x, moeda_mini_y), 6)
        
        # Texto de custo
        desenhar_texto(conteudo_surf, f"{arma['custo']}", 16, BRANCO, 
                      botao_x_relativo + 8, botao_y_relativo)
        
        # Verificar clique no botão de compra
        if clique_ocorreu and hover_compra and arma.get("pode_comprar", True):
            if pode_comprar:
                # Compra bem-sucedida
                moeda_manager.quantidade_moedas -= arma["custo"]
                moeda_manager.salvar_moedas()
                
                # Registrar compra no sistema de pricing
                pricing_manager.realizar_compra(arma["key"])
                
                # Atualizar quantidade da arma
                quantidade_compra = pricing_manager.dados_pricing[arma["key"]]["quantidade_por_compra"]
                if arma["key"] in upgrades:
                    upgrades[arma["key"]] += quantidade_compra
                else:
                    upgrades[arma["key"]] = quantidade_compra
                
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                
                nome_resultado = f"{arma['nome']} +{quantidade_compra} ammo purchased!"
                resultado = (nome_resultado, arma["cor_resultado"])
            else:
                # Não tem moedas suficientes
                pygame.mixer.Channel(4).play(som_erro)
                resultado = ("Not enough coins!", VERMELHO)
    
    # Resetar clipping
    conteudo_surf.set_clip(None)
    
    # Aplicar a superfície de conteúdo à tela
    tela.blit(conteudo_surf, (area_conteudo.x, area_scroll_y))
    
    # Desenhar barra de scroll se necessário
    if max_scroll > 0:
        barra_largura = 12
        barra_x = area_conteudo.x + area_conteudo.width - barra_largura - 8
        barra_y = area_scroll_y
        barra_altura = area_scroll_altura
        
        # Fundo da barra de scroll
        pygame.draw.rect(tela, (50, 50, 50), (barra_x, barra_y, barra_largura, barra_altura), 0, 6)
        
        # Calcular posição e tamanho do indicador
        handle_ratio = min(1.0, area_scroll_altura / altura_total_conteudo)
        indicador_altura = max(30, int(barra_altura * handle_ratio))
        scroll_ratio = scroll_y / max_scroll if max_scroll > 0 else 0
        indicador_y = barra_y + int((barra_altura - indicador_altura) * scroll_ratio)
        
        pygame.draw.rect(tela, (180, 180, 180), (barra_x, indicador_y, barra_largura, indicador_altura), 0, 6)
    
    # Adicionar instruções na parte inferior
    instrucoes_y = area_conteudo.y + area_conteudo.height - 30
    desenhar_texto(tela, "Click buttons to buy ammunition for weapons", 16, (180, 180, 180), 
                  area_conteudo.x + area_conteudo.width//2, instrucoes_y)
    
    return (resultado[0] if resultado else None, 
            resultado[1] if resultado else None, 
            max_scroll)