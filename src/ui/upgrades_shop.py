#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja de upgrades do jogo.
Com sistema de preços dinâmicos e scroll integrados.
"""

import pygame
import math
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

def desenhar_icone_coracao(tela, x, y, tempo_atual):
    """
    Desenha um ícone de coração com efeitos visuais animados.
    """
    tamanho_coracao = 28

    # Efeito de pulsação
    pulso = (math.sin(tempo_atual / 300) + 1) / 2
    cor_coracao = (220 + int(pulso * 35), 50 + int(pulso * 30), 50 + int(pulso * 30))

    # Base do coração (dois círculos)
    pygame.draw.circle(tela, cor_coracao,
                      (x - tamanho_coracao//3, y - tamanho_coracao//6),
                      tamanho_coracao//2)
    pygame.draw.circle(tela, cor_coracao,
                      (x + tamanho_coracao//3, y - tamanho_coracao//6),
                      tamanho_coracao//2)

    # Triângulo para a ponta do coração
    pontos_triangulo = [
        (x - tamanho_coracao//1.5, y - tamanho_coracao//6),
        (x + tamanho_coracao//1.5, y - tamanho_coracao//6),
        (x, y + tamanho_coracao//1.2)
    ]
    pygame.draw.polygon(tela, cor_coracao, pontos_triangulo)

    # Brilho no coração
    brilho_intensidade = int(255 * (pulso * 0.5 + 0.5))
    pygame.draw.circle(tela, (brilho_intensidade, 150, 150),
                      (x - tamanho_coracao//4, y - tamanho_coracao//3),
                      tamanho_coracao//6)

    # Partículas de vida ao redor
    for i in range(4):
        angulo = (tempo_atual / 400 + i * 90) % 360
        raio_particula = 25
        particula_x = x + int(raio_particula * math.cos(math.radians(angulo)))
        particula_y = y + int(raio_particula * math.sin(math.radians(angulo)))

        # Pequenos corações
        tamanho_mini = 3 + int(pulso * 2)
        pygame.draw.circle(tela, (255, 100, 100), (particula_x, particula_y), tamanho_mini)

def desenhar_icone_dash(tela, x, y, tempo_atual):
    """
    Desenha um ícone de dash com um quadrado idêntico ao do jogador + efeitos de velocidade.
    """
    # Animação de movimento horizontal (vai e volta)
    offset_x = int(math.sin(tempo_atual / 150) * 10)

    # Tamanho do quadrado
    tamanho_quad = 28

    # Cores do quadrado (azul do jogador)
    cor_azul = AZUL
    cor_escura = tuple(max(0, c - 50) for c in cor_azul)
    cor_brilhante = tuple(min(255, c + 70) for c in cor_azul)

    # Posição do quadrado com offset de movimento
    quad_x = x - tamanho_quad // 2 + offset_x
    quad_y = y - tamanho_quad // 2

    # Efeito de pulsação
    pulso = (math.sin(tempo_atual / 200) + 1) / 2
    mod_tamanho = int(pulso * 4)

    # Rastro de movimento (múltiplos quadrados atrás)
    for i in range(3):
        rastro_offset = -15 * (i + 1) + offset_x
        alpha_factor = 1 - (i / 3)

        # Cores do rastro mais escuras
        cor_rastro = tuple(int(c * alpha_factor * 0.5) for c in cor_azul)

        rastro_x = x - tamanho_quad // 2 + rastro_offset
        rastro_tam = tamanho_quad - (i * 4)

        # Sombra do rastro
        pygame.draw.rect(tela, (10, 10, 10),
                        (rastro_x + 2, quad_y + 2, rastro_tam, rastro_tam), 0, 3)

        # Quadrado do rastro
        pygame.draw.rect(tela, cor_rastro,
                        (rastro_x, quad_y, rastro_tam, rastro_tam), 0, 3)

    # Partículas de energia cyan ao redor do quadrado
    for i in range(8):
        angulo = (tempo_atual * 5 + i * 45) % 360
        raio = 25 + math.sin(tempo_atual / 100 + i) * 3
        particula_x = x + int(raio * math.cos(math.radians(angulo)))
        particula_y = y + int(raio * math.sin(math.radians(angulo)))

        cor_particula = (100, 200, 255)
        pygame.draw.circle(tela, cor_particula, (particula_x, particula_y), 2)

    # Sombra do quadrado principal
    pygame.draw.rect(tela, (20, 20, 20),
                    (quad_x + 3, quad_y + 3,
                     tamanho_quad + mod_tamanho, tamanho_quad + mod_tamanho), 0, 3)

    # Quadrado principal - camada escura
    pygame.draw.rect(tela, cor_escura,
                    (quad_x, quad_y,
                     tamanho_quad + mod_tamanho, tamanho_quad + mod_tamanho), 0, 5)

    # Quadrado principal - camada azul
    pygame.draw.rect(tela, cor_azul,
                    (quad_x + 3, quad_y + 3,
                     tamanho_quad + mod_tamanho - 6, tamanho_quad + mod_tamanho - 6), 0, 3)

    # Brilho no canto superior esquerdo
    pygame.draw.rect(tela, cor_brilhante,
                    (quad_x + 5, quad_y + 5, 8, 8), 0, 2)

    # Linhas de velocidade à direita
    cor_velocidade = (100, 200, 255)
    for i in range(4):
        linha_x = x + tamanho_quad // 2 + 10
        linha_y = y - 12 + i * 8
        linha_comprimento = 12 + int(pulso * 6)
        pygame.draw.line(tela, cor_velocidade,
                        (linha_x, linha_y),
                        (linha_x + linha_comprimento, linha_y), 3)

def desenhar_upgrades_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_y=0):
    """
    Desenha a seção de upgrades da loja com sistema de preços dinâmicos e scroll.
    
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
    desenhar_texto(tela, "UPGRADES", 36, (120, 150, 255), LARGURA // 2, area_conteudo.y + 30)
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # Configurações dos itens
    altura_item = 120
    espaco_entre_itens = 30
    margem_superior = 70
    margem_lateral = 35
    margem_clipping = 15
    
    # Lista de upgrades para facilitar a adição de novos upgrades
    upgrades_loja = [
        {
            "key": "vida",
            "nome": "HEALTH BOOST",
            "descricao": "",
            "instrucoes": "Passive upgrade - always active",
            "info_extra": "Adds +1 maximum health point",
            "cor_fundo": (30, 30, 60),
            "cor_borda": (70, 70, 150),
            "cor_botao": (50, 120, 80),
            "cor_hover": (70, 180, 100),
            "cor_texto": (150, 150, 255),
            "cor_resultado": VERDE,
            "icone_func": "coracao",
            "mostrar_quantidade": True
        },
        {
            "key": "dash",
            "nome": "DASH",
            "descricao": "",
            "instrucoes": "Press SPACE to dash forward",
            "info_extra": "Quick dash in movement direction - Invulnerable during dash",
            "cor_fundo": (20, 40, 60),
            "cor_borda": (100, 200, 255),
            "cor_botao": (50, 100, 180),
            "cor_hover": (80, 150, 255),
            "cor_texto": (150, 220, 255),
            "cor_resultado": (100, 200, 255),
            "icone_func": "dash",
            "mostrar_quantidade": True
        }

    ]
    
    # Aplicar sistema de pricing aos upgrades
    upgrades_loja = aplicar_pricing_sistema(upgrades_loja, pricing_manager)
    
    # Calcular altura total necessária para todos os itens
    altura_total_conteudo = len(upgrades_loja) * (altura_item + espaco_entre_itens) + espaco_entre_itens + (margem_clipping * 2)
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
    
    # Desenhar cada upgrade na superfície de conteúdo
    for i, upgrade in enumerate(upgrades_loja):
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
        if not upgrade.get("pode_comprar", True):
            # Upgrade esgotado
            cor_fundo = (upgrade["cor_fundo"][0]//3, upgrade["cor_fundo"][1]//3, upgrade["cor_fundo"][2]//3)
            cor_borda = (100, 50, 50)  # Vermelho escuro para esgotado
        else:
            cor_fundo = upgrade["cor_fundo"]
            cor_borda = upgrade["cor_borda"]
        
        # Desenhar fundo do item
        pygame.draw.rect(conteudo_surf, cor_fundo, item_rect, 0, 8)
        pygame.draw.rect(conteudo_surf, cor_borda, item_rect, 2, 8)
        
        # Se esgotado, adicionar overlay
        if not upgrade.get("pode_comprar", True):
            overlay_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            overlay_surf.fill((0, 0, 0, 120))
            conteudo_surf.blit(overlay_surf, (item_rect.x, item_rect.y))
        
        # Desenhar ícone do upgrade
        icone_x = item_rect.x + 60
        icone_y = y_item_relativo + altura_item // 2

        if upgrade["icone_func"] == "coracao":
            desenhar_icone_coracao(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif upgrade["icone_func"] == "dash":
            desenhar_icone_dash(conteudo_surf, icone_x, icone_y, tempo_atual)
        # Aqui você pode adicionar mais ícones conforme necessário
        
        # Nome do upgrade
        cor_texto = upgrade["cor_texto"] if upgrade.get("pode_comprar", True) else (100, 100, 100)
        desenhar_texto(conteudo_surf, upgrade["nome"], 24, cor_texto, 
                      item_rect.x + 170, y_item_relativo + 20)
        
        # Descrição e status do upgrade
        if upgrade.get("mostrar_quantidade", False):
            status = f"{upgrade['descricao']} (Current: {upgrades.get(upgrade['key'], 0)})"
        else:
            if upgrade["key"] not in upgrades or upgrades[upgrade["key"]] == 0:
                status = f"{upgrade['descricao']} (Not purchased)"
            else:
                status = f"{upgrade['descricao']} (Active)"
        
        desenhar_texto(conteudo_surf, status, 15, BRANCO if upgrade.get("pode_comprar", True) else (120, 120, 120), 
                      item_rect.x + 170, y_item_relativo + 40)
        
        # Informações de limite e próximo preço
        info_limite = upgrade.get("info_limite", "")
        desenhar_texto(conteudo_surf, info_limite, 12, (180, 180, 180), 
                      item_rect.x + 170, y_item_relativo + 58)
        
        # Próximo preço (se houver)
        if upgrade.get("proximo_preco") and upgrade.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, f"Next: {upgrade['proximo_preco']} coins", 11, (200, 200, 100), 
                          item_rect.x + 170, y_item_relativo + 75)
        elif not upgrade.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, "MAXED OUT", 14, VERMELHO, 
                          item_rect.x + 170, y_item_relativo + 75)
        
        # Informações adicionais do upgrade
        desenhar_texto(conteudo_surf, upgrade["info_extra"], 10, (150, 150, 150), 
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
        pode_comprar = (moeda_manager.obter_quantidade() >= upgrade["custo"] and 
                       upgrade.get("pode_comprar", True))
        
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
        if not upgrade.get("pode_comprar", True):
            # Esgotado
            cor_botao = (80, 40, 40)
            cor_hover = (80, 40, 40)
        elif pode_comprar:
            # Pode comprar
            cor_botao = upgrade["cor_botao"]
            cor_hover = upgrade["cor_hover"]
        else:
            # Sem moedas suficientes
            cor_botao = (upgrade["cor_botao"][0]//3, upgrade["cor_botao"][1]//3, upgrade["cor_botao"][2]//3)
            cor_hover = cor_botao
        
        # Desenhar botão de compra na superfície de conteúdo
        pygame.draw.rect(conteudo_surf, cor_hover if hover_compra else cor_botao, 
                        rect_compra_relativo, 0, 8)
        pygame.draw.rect(conteudo_surf, upgrade["cor_borda"], rect_compra_relativo, 2, 8)
        
        # Ícone de moeda e custo
        moeda_mini_x = botao_x_relativo - 25
        moeda_mini_y = botao_y_relativo
        pygame.draw.circle(conteudo_surf, AMARELO, (moeda_mini_x, moeda_mini_y), 6)
        
        # Texto de custo
        desenhar_texto(conteudo_surf, f"{upgrade['custo']}", 16, BRANCO, 
                      botao_x_relativo + 8, botao_y_relativo)
        
        # Verificar clique no botão de compra
        if clique_ocorreu and hover_compra and upgrade.get("pode_comprar", True):
            if pode_comprar:
                # Compra bem-sucedida
                moeda_manager.quantidade_moedas -= upgrade["custo"]
                moeda_manager.salvar_moedas()
                
                # Registrar compra no sistema de pricing
                pricing_manager.realizar_compra(upgrade["key"])
                
                # Atualizar quantidade do upgrade
                quantidade_compra = pricing_manager.dados_pricing[upgrade["key"]]["quantidade_por_compra"]
                if upgrade["key"] in upgrades:
                    upgrades[upgrade["key"]] += quantidade_compra
                else:
                    upgrades[upgrade["key"]] = quantidade_compra
                
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                
                nome_resultado = f"{upgrade['nome']} Purchased!"
                resultado = (nome_resultado, upgrade["cor_resultado"])
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
    desenhar_texto(tela, "Click buttons to purchase permanent upgrades", 16, (180, 180, 180), 
                  area_conteudo.x + area_conteudo.width//2, instrucoes_y)
    
    return (resultado[0] if resultado else None, 
            resultado[1] if resultado else None, 
            max_scroll)