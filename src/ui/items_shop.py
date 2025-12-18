#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a seção de itens da loja do jogo.
Versão completa com sistema de preços dinâmicos integrado.
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

def desenhar_icone_dimensional_hop(tela, x, y, tempo_atual):
    """
    Desenha um ícone de Dimensional Hop com visual retrofuturístico arcade.

    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores retrofuturísticas (roxo/magenta/ciano neon)
    cor_portal_externo = (200, 50, 255)  # Magenta brilhante
    cor_portal_interno = (100, 200, 255)  # Ciano
    cor_particulas = (255, 150, 255)  # Rosa neon
    cor_grid = (150, 80, 200)  # Roxo

    # Animação de pulsação
    pulso = (math.sin(tempo_atual / 150) + 1) / 2

    # Portal principal (círculo com efeito de distorção espacial)
    raio_portal = 18

    # Desenhar anéis concêntricos do portal (efeito túnel)
    for i in range(4):
        raio_anel = raio_portal - i * 4
        alpha = int(200 - i * 50)
        cor_anel = (
            int(cor_portal_externo[0] * (1 - i/4) + cor_portal_interno[0] * (i/4)),
            int(cor_portal_externo[1] * (1 - i/4) + cor_portal_interno[1] * (i/4)),
            int(cor_portal_externo[2] * (1 - i/4) + cor_portal_interno[2] * (i/4))
        )

        # Efeito de rotação
        offset_rotacao = (tempo_atual / 100 + i * 30) % 360

        pygame.draw.circle(tela, cor_anel, (int(x), int(y)), int(raio_anel + pulso * 2), 2)

    # Núcleo central brilhante
    raio_nucleo = int(6 + pulso * 3)
    pygame.draw.circle(tela, (255, 255, 255), (int(x), int(y)), raio_nucleo)
    pygame.draw.circle(tela, cor_portal_interno, (int(x), int(y)), raio_nucleo - 2)

    # Partículas orbitando (efeito arcade)
    num_particulas = 8
    for i in range(num_particulas):
        angulo = (2 * math.pi * i / num_particulas) + (tempo_atual / 200)
        raio_orbita = 22 + math.sin(tempo_atual / 100 + i) * 3

        part_x = x + math.cos(angulo) * raio_orbita
        part_y = y + math.sin(angulo) * raio_orbita

        # Tamanho variável da partícula
        tamanho_part = 3 + int(pulso * 2)

        # Desenhar partícula pixelada (estilo arcade)
        pygame.draw.rect(tela, cor_particulas,
                        (int(part_x - tamanho_part/2), int(part_y - tamanho_part/2),
                         tamanho_part, tamanho_part))

    # Grid de fundo (efeito retrofuturístico)
    for i in range(3):
        for j in range(3):
            grid_x = x - 12 + i * 12
            grid_y = y - 12 + j * 12

            # Pequenos quadrados do grid
            if (i + j) % 2 == 0:
                pygame.draw.rect(tela, cor_grid, (int(grid_x), int(grid_y), 2, 2))

    # Raios de energia saindo do portal (efeito neon)
    num_raios = 4
    for i in range(num_raios):
        angulo = (2 * math.pi * i / num_raios) + (tempo_atual / 300)
        comprimento_raio = 12 + pulso * 6

        raio_start_x = x + math.cos(angulo) * raio_portal
        raio_start_y = y + math.sin(angulo) * raio_portal
        raio_end_x = x + math.cos(angulo) * (raio_portal + comprimento_raio)
        raio_end_y = y + math.sin(angulo) * (raio_portal + comprimento_raio)

        # Raio com gradiente
        pygame.draw.line(tela, cor_portal_externo,
                        (int(raio_start_x), int(raio_start_y)),
                        (int(raio_end_x), int(raio_end_y)), 2)

def desenhar_icone_faca(tela, x, y, tempo_atual):
    """
    Desenha um ícone de faca de combate com efeitos visuais.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores da faca
    cor_lamina = (200, 200, 220)  # Aço brilhante
    cor_lamina_escura = (150, 150, 170)
    cor_cabo = (139, 69, 19)  # Marrom escuro (cabo de madeira)
    cor_cabo_escura = (101, 51, 14)
    cor_guarda = (169, 169, 169)  # Cinza (metal da guarda)
    
    # Dimensões da faca
    comprimento_lamina = 20
    largura_lamina = 6
    comprimento_cabo = 12
    largura_cabo = 4
    
    # Calcular ângulo de rotação baseado no tempo (faca girando sutilmente)
    angulo_rotacao = math.sin(tempo_atual / 1000) * 5  # Oscila entre -5 e 5 graus
    
    # Função para rotacionar pontos
    def rotacionar_ponto(px, py, cx, cy, angulo):
        rad = math.radians(angulo)
        cos_ang = math.cos(rad)
        sin_ang = math.sin(rad)
        
        # Transladar para origem
        px -= cx
        py -= cy
        
        # Rotacionar
        novo_x = px * cos_ang - py * sin_ang
        novo_y = px * sin_ang + py * cos_ang
        
        # Transladar de volta
        novo_x += cx
        novo_y += cy
        
        return int(novo_x), int(novo_y)
    
    # Pontos da lâmina (triangular com ponta afiada)
    pontos_lamina = [
        (x - comprimento_lamina//2, y - largura_lamina//2),  # base esquerda
        (x - comprimento_lamina//2, y + largura_lamina//2),  # base direita
        (x + comprimento_lamina//2, y)  # ponta
    ]
    
    # Rotacionar pontos da lâmina
    pontos_lamina_rot = [rotacionar_ponto(px, py, x, y, angulo_rotacao) for px, py in pontos_lamina]
    
    # Desenhar lâmina
    pygame.draw.polygon(tela, cor_lamina, pontos_lamina_rot)
    pygame.draw.polygon(tela, cor_lamina_escura, pontos_lamina_rot, 2)
    
    # Pontos do cabo
    cabo_start_x = x - comprimento_lamina//2
    cabo_end_x = cabo_start_x - comprimento_cabo
    
    pontos_cabo = [
        (cabo_start_x, y - largura_cabo//2),
        (cabo_start_x, y + largura_cabo//2),
        (cabo_end_x, y + largura_cabo//2),
        (cabo_end_x, y - largura_cabo//2)
    ]
    
    # Rotacionar pontos do cabo
    pontos_cabo_rot = [rotacionar_ponto(px, py, x, y, angulo_rotacao) for px, py in pontos_cabo]
    
    # Desenhar cabo
    pygame.draw.polygon(tela, cor_cabo, pontos_cabo_rot)
    pygame.draw.polygon(tela, cor_cabo_escura, pontos_cabo_rot, 1)
    
    # Desenhar guarda (separação entre lâmina e cabo)
    guarda_x1, guarda_y1 = rotacionar_ponto(cabo_start_x, y - largura_lamina//2 - 2, x, y, angulo_rotacao)
    guarda_x2, guarda_y2 = rotacionar_ponto(cabo_start_x, y + largura_lamina//2 + 2, x, y, angulo_rotacao)
    
    pygame.draw.line(tela, cor_guarda, (guarda_x1, guarda_y1), (guarda_x2, guarda_y2), 3)
    
    # Efeito de brilho na lâmina
    pulso_brilho = (math.sin(tempo_atual / 400) + 1) / 2
    if pulso_brilho > 0.6:
        # Linha de brilho no meio da lâmina
        meio_lamina_start = rotacionar_ponto(x - comprimento_lamina//2 + 2, y, x, y, angulo_rotacao)
        meio_lamina_end = rotacionar_ponto(x + comprimento_lamina//2 - 2, y, x, y, angulo_rotacao)
        
        cor_brilho = (255, 255, 255, int(150 * (pulso_brilho - 0.6) / 0.4))
        pygame.draw.line(tela, (255, 255, 255), meio_lamina_start, meio_lamina_end, 1)
    
    # Partículas de metal ao redor (efeito de afiação)
    for i in range(3):
        angulo_particula = (tempo_atual / 150 + i * 120) % 360
        raio_particula = 15
        particula_x = x + int(raio_particula * math.cos(math.radians(angulo_particula)))
        particula_y = y + int(raio_particula * math.sin(math.radians(angulo_particula)))
        
        # Pequenas faíscas metálicas
        tamanho_particula = 1 + int(pulso_brilho * 2)
        if tamanho_particula > 1:
            pygame.draw.circle(tela, (255, 255, 200), (particula_x, particula_y), tamanho_particula)

def desenhar_items_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_y=0):
    """
    Desenha a seção de itens da loja com sistema de preços dinâmicos completo.
    
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
    desenhar_texto(tela, "ITEMS", 36, (120, 220, 120), LARGURA // 2, area_conteudo.y + 30)
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # Configurações dos itens - OTIMIZADAS PARA O SISTEMA DE PREÇOS
    altura_item = 125          # Altura suficiente para todas as informações
    espaco_entre_itens = 25    
    margem_superior = 70       
    margem_lateral = 35        
    margem_clipping = 15       
    
    # Lista de itens com configurações completas
    itens_loja = [
        {
            "key": "granada",
            "nome": "GRENADE",
            "descricao": "",
            "instrucoes": "Press Q to select, Mouse to throw",
            "info_extra": "High explosive damage in large area",
            "cor_fundo": (40, 60, 40),
            "cor_borda": (80, 150, 80),
            "cor_botao": (60, 120, 60),
            "cor_hover": (80, 160, 80),
            "cor_texto": (150, 220, 150),
            "cor_resultado": VERDE,
            "icone_func": "granada",
            "dano": 1
        },
        {
            "key": "ampulheta",
            "nome": "HOURGLASS OF BALANCE",
            "descricao": "",
            "instrucoes": "Press Q to activate slow motion",
            "info_extra": "Slows time to 30% for 5 seconds",
            "cor_fundo": (40, 40, 80),
            "cor_borda": (80, 80, 180),
            "cor_botao": (60, 60, 150),
            "cor_hover": (80, 80, 200),
            "cor_texto": (150, 150, 255),
            "cor_resultado": AZUL,
            "icone_func": "ampulheta",
            "dano": 0
        },
        {
            "key": "faca",
            "nome": "KILLER DOLL",
            "descricao": "",
            "instrucoes": "Press Q to equip, be careful, he's fast",
            "info_extra": "Be careful, he's fast",
            "cor_fundo": (60, 40, 40),
            "cor_borda": (150, 80, 80),
            "cor_botao": (120, 60, 60),
            "cor_hover": (160, 80, 80),
            "cor_texto": (220, 150, 150),
            "cor_resultado": (220, 150, 150),
            "icone_func": "faca",
            "dano": 1
        },
        {
            "key": "dimensional_hop",
            "nome": "DIMENSIONAL HOP",
            "descricao": "",
            "instrucoes": "Press Q to hold, Click to teleport",
            "info_extra": "Instant teleportation to cursor position",
            "cor_fundo": (40, 20, 60),
            "cor_borda": (150, 80, 200),
            "cor_botao": (100, 50, 150),
            "cor_hover": (140, 80, 200),
            "cor_texto": (200, 150, 255),
            "cor_resultado": (200, 150, 255),
            "icone_func": "dimensional_hop",
            "dano": 0,
            "custo": 60
        }
    ]
    
    # Aplicar sistema de pricing aos itens
    itens_loja = aplicar_pricing_sistema(itens_loja, pricing_manager)
    
    # Calcular altura total necessária para todos os itens (incluindo margem de clipping)
    altura_total_conteudo = len(itens_loja) * (altura_item + espaco_entre_itens) + espaco_entre_itens + (margem_clipping * 2)
    area_scroll_altura = area_conteudo.height - margem_superior
    max_scroll = max(0, altura_total_conteudo - area_scroll_altura)
    
    # Criar uma superfície para o conteúdo dos itens com clipping
    area_scroll_y = area_conteudo.y + margem_superior
    conteudo_surf = pygame.Surface((area_conteudo.width, area_scroll_altura), pygame.SRCALPHA)
    conteudo_surf.fill((0, 0, 0, 0))  # Transparente
    
    # Desenhar fundo da área de scroll
    pygame.draw.rect(conteudo_surf, (20, 20, 50, 150), (0, 0, area_conteudo.width, area_scroll_altura), 0, 10)
    pygame.draw.rect(conteudo_surf, (70, 70, 130), (0, 0, area_conteudo.width, area_scroll_altura), 2, 10)
    
    # Definir área de clipping para os itens (com margem interna para evitar colagem na borda)
    cliprect = pygame.Rect(margem_clipping, margem_clipping, 
                          area_conteudo.width - (margem_clipping * 2), 
                          area_scroll_altura - (margem_clipping * 2))
    conteudo_surf.set_clip(cliprect)
    
    # Desenhar cada item na superfície de conteúdo
    for i, item in enumerate(itens_loja):
        # Calcular posição Y do item considerando o scroll e margem de clipping
        y_item_relativo = i * (altura_item + espaco_entre_itens) + espaco_entre_itens + margem_clipping - scroll_y
        
        # Se o item está fora da área visível (considerando as margens de clipping), não desenhar
        if (y_item_relativo + altura_item < margem_clipping or 
            y_item_relativo > area_scroll_altura - margem_clipping):
            continue
        
        # Retângulo do item na superfície de conteúdo - COM MARGENS AJUSTADAS
        item_rect = pygame.Rect(margem_lateral, y_item_relativo, 
                               area_conteudo.width - (margem_lateral * 2), altura_item)
        
        # Cor baseada na disponibilidade do sistema de pricing
        if not item.get("pode_comprar", True):
            # Item esgotado
            cor_fundo = (item["cor_fundo"][0]//3, item["cor_fundo"][1]//3, item["cor_fundo"][2]//3)
            cor_borda = (100, 50, 50)  # Vermelho escuro para esgotado
        else:
            cor_fundo = item["cor_fundo"]
            cor_borda = item["cor_borda"]
        
        # Desenhar fundo do item
        pygame.draw.rect(conteudo_surf, cor_fundo, item_rect, 0, 8)
        pygame.draw.rect(conteudo_surf, cor_borda, item_rect, 2, 8)
        
        # Se esgotado, adicionar overlay escuro
        if not item.get("pode_comprar", True):
            overlay_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            overlay_surf.fill((0, 0, 0, 120))
            conteudo_surf.blit(overlay_surf, (item_rect.x, item_rect.y))
        
        # Desenhar ícone do item
        icone_x = item_rect.x + 60
        icone_y = y_item_relativo + altura_item // 2
        
        if item["icone_func"] == "granada":
            # Ícone da granada com efeitos
            tamanho_granada = 22
            cor_granada = (60, 120, 60)
            cor_granada_escura = (40, 80, 40)
            
            # Corpo da granada (esfera)
            pygame.draw.circle(conteudo_surf, cor_granada, (icone_x, icone_y), tamanho_granada)
            
            # Detalhes da granada (linhas cruzadas para textura)
            pygame.draw.line(conteudo_surf, cor_granada_escura, 
                           (icone_x - tamanho_granada + 6, icone_y), 
                           (icone_x + tamanho_granada - 6, icone_y), 3)
            pygame.draw.line(conteudo_surf, cor_granada_escura, 
                           (icone_x, icone_y - tamanho_granada + 6), 
                           (icone_x, icone_y + tamanho_granada - 6), 3)
            
            # Parte superior (bocal)
            pygame.draw.rect(conteudo_surf, (150, 150, 150), 
                           (icone_x - 7, icone_y - tamanho_granada - 10, 14, 10), 0, 3)
            
            # Pino da granada
            pin_x = icone_x + 12
            pin_y = icone_y - tamanho_granada - 5
            pygame.draw.circle(conteudo_surf, (220, 220, 100), (pin_x, pin_y), 8, 3)
            
            # Brilho pulsante
            pulso = (math.sin(tempo_atual / 200) + 1) / 2
            cor_brilho = (100 + int(pulso * 50), 200 + int(pulso * 55), 100 + int(pulso * 50))
            pygame.draw.circle(conteudo_surf, cor_brilho, 
                             (icone_x - tamanho_granada//2, icone_y - tamanho_granada//2), 6)
            
        elif item["icone_func"] == "ampulheta":
            desenhar_icone_ampulheta(conteudo_surf, icone_x, icone_y, tempo_atual)

        elif item["icone_func"] == "faca":
            desenhar_icone_faca(conteudo_surf, icone_x, icone_y, tempo_atual)

        elif item["icone_func"] == "dimensional_hop":
            desenhar_icone_dimensional_hop(conteudo_surf, icone_x, icone_y, tempo_atual)
        
        # Nome do item (ajustado para o novo tamanho)
        cor_texto = item["cor_texto"] if item.get("pode_comprar", True) else (100, 100, 100)
        desenhar_texto(conteudo_surf, item["nome"], 24, cor_texto, 
                      item_rect.x + 170, y_item_relativo + 18)
        
        # Descrição e status do item (espaçamento ajustado)
        if item["key"] not in upgrades or upgrades[item["key"]] == 0:
            status = f"{item['descricao']} (Not owned)"
        else:
            nome_item = "Grenades" if item["key"] == "granada" else \
                        "Time Distortions" if item["key"] == "ampulheta" else \
                        "Combat Dolls"
            status = f"{nome_item}: {upgrades[item['key']]}"
        
        desenhar_texto(conteudo_surf, status, 15, BRANCO if item.get("pode_comprar", True) else (120, 120, 120), 
                      item_rect.x + 170, y_item_relativo + 38)
        
        # Informações de limite do sistema de pricing
        info_limite = item.get("info_limite", "")
        desenhar_texto(conteudo_surf, info_limite, 12, (180, 180, 180),
                      item_rect.x + 170, y_item_relativo + 56)

        # Mostrar dano do item
        if item.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, f"Damage: {item.get('dano', 1)}", 16, (255, 200, 100),
                          item_rect.x + 170, y_item_relativo + 73)
        else:
            desenhar_texto(conteudo_surf, "SOLD OUT", 14, VERMELHO,
                          item_rect.x + 170, y_item_relativo + 73)
        
        # Informações adicionais do item
        desenhar_texto(conteudo_surf, item["info_extra"], 10, (150, 150, 150), 
                      item_rect.x + 170, y_item_relativo + 90)
        
        # Botão de compra (ajustado para o tamanho menor)
        botao_largura = 120
        botao_altura = 35
        botao_x_relativo = item_rect.x + item_rect.width - 70
        botao_y_relativo = y_item_relativo + altura_item // 2
        
        rect_compra_relativo = pygame.Rect(botao_x_relativo - botao_largura//2, 
                                         botao_y_relativo - botao_altura//2,
                                         botao_largura, botao_altura)
        
        # Verificar se o jogador tem moedas suficientes e se pode comprar (sistema de pricing)
        pode_comprar = (moeda_manager.obter_quantidade() >= item["custo"] and 
                       item.get("pode_comprar", True))
        
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
        
        # Cores do botão baseadas na capacidade de compra e disponibilidade
        if not item.get("pode_comprar", True):
            # Esgotado
            cor_botao = (80, 40, 40)
            cor_hover = (80, 40, 40)
        elif pode_comprar:
            # Pode comprar
            cor_botao = (item["cor_botao"][0], item["cor_botao"][1], item["cor_botao"][2])
            cor_hover = (item["cor_hover"][0], item["cor_hover"][1], item["cor_hover"][2])
        else:
            # Sem moedas suficientes
            cor_botao = (item["cor_botao"][0]//3, item["cor_botao"][1]//3, item["cor_botao"][2]//3)
            cor_hover = cor_botao
        
        # Desenhar botão de compra na superfície de conteúdo
        pygame.draw.rect(conteudo_surf, cor_hover if hover_compra else cor_botao, 
                        rect_compra_relativo, 0, 8)
        pygame.draw.rect(conteudo_surf, item["cor_borda"], rect_compra_relativo, 2, 8)
        
        # Ícone de moeda e custo
        moeda_mini_x = botao_x_relativo - 25
        moeda_mini_y = botao_y_relativo
        pygame.draw.circle(conteudo_surf, AMARELO, (moeda_mini_x, moeda_mini_y), 6)
        
        # Texto de custo (preço dinâmico do sistema de pricing)
        desenhar_texto(conteudo_surf, f"{item['custo']}", 16, BRANCO, 
                      botao_x_relativo + 8, botao_y_relativo)
        
        # Verificar clique no botão de compra
        if clique_ocorreu and hover_compra and item.get("pode_comprar", True):
            if pode_comprar:
                # Compra bem-sucedida
                moeda_manager.quantidade_moedas -= item["custo"]
                moeda_manager.salvar_moedas()
                
                # Registrar compra no sistema de pricing
                pricing_manager.realizar_compra(item["key"])
                
                # Atualizar quantidade do item
                quantidade_compra = pricing_manager.dados_pricing[item["key"]]["quantidade_por_compra"]
                if item["key"] in upgrades:
                    upgrades[item["key"]] += quantidade_compra
                else:
                    upgrades[item["key"]] = quantidade_compra
                
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                
                nome_resultado = item["nome"].title() + " Purchased!"
                resultado = (nome_resultado, item["cor_resultado"])
            else:
                # Não tem moedas suficientes
                pygame.mixer.Channel(4).play(som_erro)
                resultado = ("Not enough coins!", VERMELHO)
    
    # Resetar clipping
    conteudo_surf.set_clip(None)
    
    # Aplicar a superfície de conteúdo à tela
    tela.blit(conteudo_surf, (area_conteudo.x, area_scroll_y))
    
    # Desenhar barra de scroll se necessário (mais visível)
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
    
    # Mostrar estatísticas do sistema de pricing na parte inferior (opcional)
    stats = pricing_manager.obter_estatisticas()
    stats_text = f"Available items: {stats['itens_disponiveis']}/{stats['total_itens']} • Total purchases made: {stats['total_compras_realizadas']}"
    desenhar_texto(tela, stats_text, 12, (120, 120, 120), 
                  area_conteudo.x + area_conteudo.width//2, area_conteudo.y + area_conteudo.height - 10)
    
    return (resultado[0] if resultado else None, 
            resultado[1] if resultado else None, 
            max_scroll)