#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo completo do sistema de inventário do jogo com sistema de abas.
Inclui tanto a lógica quanto a interface visual.
"""

import pygame
import json
import os
import random
import math
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
# MoedaManager será importado dentro da função para evitar circular import

class InventarioManager:
    """Gerencia o inventário e a seleção de armas/itens do jogador."""
    
    def __init__(self):
        self.arma_selecionada = "nenhuma"  # Padrão: nenhuma arma especial
        self.item_selecionado = "nenhum"   # Padrão: nenhum item especial
        self.arquivo_inventario = "data/inventario.json"
        self.carregar_inventario()
    
    def carregar_inventario(self):
        """Carrega a configuração do inventário do arquivo."""
        try:
            if os.path.exists(self.arquivo_inventario):
                with open(self.arquivo_inventario, "r") as f:
                    data = json.load(f)
                    self.arma_selecionada = data.get("arma_selecionada", "nenhuma")
                    self.item_selecionado = data.get("item_selecionado", "nenhum")
            else:
                self.salvar_inventario()
        except Exception as e:
            print(f"Erro ao carregar inventário: {e}")
            self.arma_selecionada = "nenhuma"
            self.item_selecionado = "nenhum"
    
    def salvar_inventario(self):
        """Salva a configuração atual do inventário."""
        try:
            # Criar diretório se não existir
            os.makedirs("data", exist_ok=True)
            
            data = {
                "arma_selecionada": self.arma_selecionada,
                "item_selecionado": self.item_selecionado
            }
            
            with open(self.arquivo_inventario, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar inventário: {e}")
    
    def selecionar_arma(self, arma):
        """Seleciona uma arma para usar na partida."""
        self.arma_selecionada = arma
        self.salvar_inventario()
    
    def selecionar_item(self, item):
        """Seleciona um item para usar na partida."""
        self.item_selecionado = item
        self.salvar_inventario()
    
    def obter_arma_selecionada(self):
        """Retorna a arma atualmente selecionada."""
        return self.arma_selecionada
    
    def obter_item_selecionado(self):
        """Retorna o item atualmente selecionado."""
        return self.item_selecionado
    
    def obter_armas_disponiveis(self):
        """Retorna dicionário com as armas disponíveis no inventário."""
        armas = {
            "espingarda": {
                "nome": "Espingarda", 
                "quantidade": 0, 
                "cor": AMARELO, 
                "descricao": "Disparo múltiplo devastador",
                "tipo": "arma"
            },
            "metralhadora": {
                "nome": "Metralhadora", 
                "quantidade": 0, 
                "cor": LARANJA, 
                "descricao": "Cadência de tiro extrema",
                "tipo": "arma"
            }
        }
        
        # Carregar quantidades dos upgrades
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    armas["espingarda"]["quantidade"] = upgrades.get("espingarda", 0)
                    armas["metralhadora"]["quantidade"] = upgrades.get("metralhadora", 0)
        except Exception as e:
            print(f"Erro ao carregar upgrades para inventário: {e}")
        
        return armas
    
    def obter_itens_disponiveis(self):
        """Retorna dicionário com os itens disponíveis no inventário."""
        itens = {
            "granada": {
                "nome": "Granada", 
                "quantidade": 0, 
                "cor": VERDE, 
                "descricao": "Explosão devastadora em área",
                "tipo": "item",
                "tecla": "Q"
            },
            "ampulheta": {
                "nome": "Hourglass of Balance", 
                "quantidade": 0, 
                "cor": (150, 200, 255), 
                "descricao": "Desacelera o tempo por 5 segundos",
                "tipo": "item",
                "tecla": "Q"
            }
        }
        
        # Carregar quantidades dos upgrades
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    itens["granada"]["quantidade"] = upgrades.get("granada", 0)
                    itens["ampulheta"]["quantidade"] = upgrades.get("ampulheta", 0)
        except Exception as e:
            print(f"Erro ao carregar upgrades para inventário: {e}")
        
        return itens

def desenhar_icone_ampulheta_inventario(tela, x, y, tempo_atual):
    """Desenha ícone da ampulheta no inventário."""
    cor_estrutura = (150, 120, 80)
    cor_areia = (255, 215, 0)
    cor_estrutura_escura = (100, 80, 50)
    
    largura = 16
    altura = 20
    
    # Corpo da ampulheta
    pygame.draw.polygon(tela, cor_estrutura, [
        (x - largura//2, y - altura//2),
        (x + largura//2, y - altura//2),
        (x, y)
    ])
    pygame.draw.polygon(tela, cor_estrutura, [
        (x, y),
        (x - largura//2, y + altura//2),
        (x + largura//2, y + altura//2)
    ])
    
    # Bordas
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x - largura//2, y - altura//2),
        (x + largura//2, y - altura//2),
        (x, y)
    ], 2)
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x, y),
        (x - largura//2, y + altura//2),
        (x + largura//2, y + altura//2)
    ], 2)
    
    # Areia animada
    pulso = (math.sin(tempo_atual / 300) + 1) / 2
    for i in range(2):
        areia_y = y + (i - 0.5) * 3
        cor_areia_atual = (255, 215, int(100 + pulso * 155))
        pygame.draw.circle(tela, cor_areia_atual, (x, int(areia_y)), 2)
    
    # Suportes
    pygame.draw.rect(tela, cor_estrutura_escura, (x - largura//2 - 2, y - altura//2 - 3, largura + 4, 3))
    pygame.draw.rect(tela, cor_estrutura_escura, (x - largura//2 - 2, y + altura//2, largura + 4, 3))

def desenhar_icone_granada_inventario(tela, x, y, tempo_atual):
    """Desenha ícone da granada no inventário."""
    tamanho_granada = 16
    cor_granada = (60, 120, 60)
    cor_granada_escura = (40, 80, 40)
    
    # Corpo da granada
    pygame.draw.circle(tela, cor_granada, (x, y), tamanho_granada)
    
    # Detalhes da granada
    pygame.draw.line(tela, cor_granada_escura, (x - tamanho_granada + 4, y), 
                    (x + tamanho_granada - 4, y), 2)
    pygame.draw.line(tela, cor_granada_escura, (x, y - tamanho_granada + 4), 
                    (x, y + tamanho_granada - 4), 2)
    
    # Parte superior
    pygame.draw.rect(tela, (150, 150, 150), (x - 5, y - tamanho_granada - 7, 10, 7), 0, 2)
    
    # Pino da granada
    pin_x = x + 8
    pin_y = y - tamanho_granada - 3
    pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), 6, 2)
    
    # Brilho pulsante
    pulso = (math.sin(tempo_atual / 200) + 1) / 2
    cor_brilho = (100 + int(pulso * 50), 200 + int(pulso * 55), 100 + int(pulso * 50))
    pygame.draw.circle(tela, cor_brilho, (x - tamanho_granada//2, y - tamanho_granada//2), 4)

def tela_inventario(tela, relogio, gradiente_inventario, fonte_titulo, fonte_normal):
    """
    Exibe a tela de inventário com sistema de abas.
    
    Returns:
        None (volta ao menu principal)
    """
    pygame.mouse.set_visible(True)
    
    # Importação tardia para evitar circular import
    from src.game.moeda_manager import MoedaManager
    
    # Inicializar managers
    inventario_manager = InventarioManager()
    moeda_manager = MoedaManager()
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    
    # Scroll do inventário
    scroll_y = 0
    max_scroll = 0
    
    # Sistema de abas
    aba_ativa = 0  # 0 = Armas, 1 = Itens
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
                # Teclas numéricas para trocar de aba
                if evento.key == pygame.K_1:
                    aba_ativa = 0
                    scroll_y = 0
                if evento.key == pygame.K_2:
                    aba_ativa = 1
                    scroll_y = 0
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Clique esquerdo
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Verificar cliques nas abas
                    aba_largura = 200
                    aba_altura = 50
                    aba1_x = LARGURA // 2 - 100
                    aba2_x = LARGURA // 2 + 100
                    aba_y = 150
                    
                    rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
                    rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
                    
                    if rect_aba1.collidepoint(mouse_pos):
                        aba_ativa = 0
                        scroll_y = 0
                    elif rect_aba2.collidepoint(mouse_pos):
                        aba_ativa = 1
                        scroll_y = 0
                    
                    # Verificar cliques nos itens baseado na aba ativa
                    y_inicial = 220 - scroll_y
                    
                    if aba_ativa == 0:  # Aba de Armas
                        armas_disponiveis = inventario_manager.obter_armas_disponiveis()
                        arma_atual = inventario_manager.obter_arma_selecionada()
                        
                        for i, (arma_key, arma_data) in enumerate(armas_disponiveis.items()):
                            y_item = y_inicial + i * 100
                            
                            if arma_data["quantidade"] <= 0:
                                continue
                            
                            rect_item = pygame.Rect(LARGURA // 2 - 300, y_item - 35, 600, 70)
                            
                            if rect_item.collidepoint(mouse_pos) and y_item > 50 and y_item < ALTURA - 100:
                                inventario_manager.selecionar_arma(arma_key if arma_key != arma_atual else "nenhuma")
                    
                    else:  # Aba de Itens
                        itens_disponiveis = inventario_manager.obter_itens_disponiveis()
                        item_atual = inventario_manager.obter_item_selecionado()
                        
                        for i, (item_key, item_data) in enumerate(itens_disponiveis.items()):
                            y_item = y_inicial + i * 100
                            
                            if item_data["quantidade"] <= 0:
                                continue
                            
                            rect_item = pygame.Rect(LARGURA // 2 - 300, y_item - 35, 600, 70)
                            
                            if rect_item.collidepoint(mouse_pos) and y_item > 50 and y_item < ALTURA - 100:
                                inventario_manager.selecionar_item(item_key if item_key != item_atual else "nenhum")
                    
                    # Verificar clique no botão voltar
                    rect_voltar = pygame.Rect(50, ALTURA - 80, 150, 60)
                    if rect_voltar.collidepoint(mouse_pos):
                        return None
                
                elif evento.button == 4:  # Scroll up
                    scroll_y = max(0, scroll_y - 30)
                elif evento.button == 5:  # Scroll down
                    scroll_y = min(max_scroll, scroll_y + 30)
        
        # Atualizar estrelas
        for estrela in estrelas:
            estrela[0] -= estrela[4]
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        
        # Desenhar fundo
        tela.blit(gradiente_inventario, (0, 0))
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar grid sutil
        for i in range(0, LARGURA, 60):
            pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA), 1)
        for i in range(0, ALTURA, 60):
            pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
        
        # Título
        desenhar_texto(tela, "INVENTÁRIO", 50, BRANCO, LARGURA // 2, 70)
        desenhar_texto(tela, "Selecione seus equipamentos para a partida", 28, AMARELO, LARGURA // 2, 110)
        
        # Mostrar moedas
        moeda_size = 12
        pygame.draw.circle(tela, AMARELO, (LARGURA - 100, 30), moeda_size)
        pygame.draw.circle(tela, (255, 215, 0), (LARGURA - 100, 30), moeda_size - 2)
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 24, AMARELO, LARGURA - 70, 30)
        
        # Desenhar sistema de abas
        aba_largura = 200
        aba_altura = 50
        aba1_x = LARGURA // 2 - 100
        aba2_x = LARGURA // 2 + 100
        aba_y = 150
        
        # Aba 1 (Armas)
        cor_aba1 = (80, 50, 50) if aba_ativa == 0 else (50, 30, 30)
        cor_hover_aba1 = (120, 70, 70) if aba_ativa == 0 else (70, 40, 40)
        
        rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
        hover_aba1 = rect_aba1.collidepoint(pygame.mouse.get_pos())
        
        pygame.draw.rect(tela, cor_hover_aba1 if hover_aba1 else cor_aba1, rect_aba1, 0, 10)
        pygame.draw.rect(tela, (200, 100, 100), rect_aba1, 3 if aba_ativa == 0 else 1, 10)
        desenhar_texto(tela, "ARMAS (1)", 24, BRANCO, aba1_x, aba_y)
        
        # Aba 2 (Itens)
        cor_aba2 = (50, 80, 50) if aba_ativa == 1 else (30, 50, 30)
        cor_hover_aba2 = (70, 120, 70) if aba_ativa == 1 else (40, 70, 40)
        
        rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
        hover_aba2 = rect_aba2.collidepoint(pygame.mouse.get_pos())
        
        pygame.draw.rect(tela, cor_hover_aba2 if hover_aba2 else cor_aba2, rect_aba2, 0, 10)
        pygame.draw.rect(tela, (100, 200, 100), rect_aba2, 3 if aba_ativa == 1 else 1, 10)
        desenhar_texto(tela, "ITENS (2)", 24, BRANCO, aba2_x, aba_y)
        
        # Desenhar conteúdo da aba ativa
        y_inicial = 220 - scroll_y
        
        if aba_ativa == 0:  # Aba de Armas
            armas_disponiveis = inventario_manager.obter_armas_disponiveis()
            arma_atual = inventario_manager.obter_arma_selecionada()
            
            for i, (arma_key, arma_data) in enumerate(armas_disponiveis.items()):
                y_item = y_inicial + i * 100
                
                if y_item < -100 or y_item > ALTURA + 100:
                    continue
                
                # Cor de fundo baseada na disponibilidade e seleção
                if arma_data["quantidade"] <= 0:
                    cor_fundo = (60, 40, 40)
                    cor_borda = (100, 60, 60)
                elif arma_key == arma_atual:
                    cor_fundo = (40, 80, 40)
                    cor_borda = (80, 160, 80)
                else:
                    cor_fundo = (40, 40, 80)
                    cor_borda = (80, 80, 160)
                
                # Desenhar fundo do item
                rect_item = pygame.Rect(LARGURA // 2 - 300, y_item - 35, 600, 70)
                pygame.draw.rect(tela, cor_fundo, rect_item, 0, 10)
                pygame.draw.rect(tela, cor_borda, rect_item, 3, 10)
                
                # Ícone da arma
                icone_rect = pygame.Rect(LARGURA // 2 - 280, y_item - 15, 30, 30)
                pygame.draw.rect(tela, arma_data["cor"], icone_rect, 0, 5)
                pygame.draw.rect(tela, BRANCO, icone_rect, 2, 5)
                
                # Informações da arma
                cor_texto = BRANCO if arma_data["quantidade"] > 0 else (150, 150, 150)
                desenhar_texto(tela, arma_data["nome"], 26, cor_texto, LARGURA // 2 - 150, y_item - 10)
                desenhar_texto(tela, f"Munição: {arma_data['quantidade']}", 20, cor_texto, LARGURA // 2 + 50, y_item - 10)
                desenhar_texto(tela, arma_data["descricao"], 16, cor_texto, LARGURA // 2 - 150, y_item + 10)
                
                # Status de seleção
                if arma_key == arma_atual:
                    pygame.draw.polygon(tela, VERDE, [
                        (LARGURA // 2 + 250, y_item - 8),
                        (LARGURA // 2 + 270, y_item),
                        (LARGURA // 2 + 250, y_item + 8)
                    ])
                    desenhar_texto(tela, "EQUIPADA", 18, VERDE, LARGURA // 2 + 200, y_item)
                elif arma_data["quantidade"] <= 0:
                    desenhar_texto(tela, "NÃO COMPRADA", 16, VERMELHO, LARGURA // 2 + 180, y_item + 10)
                else:
                    desenhar_texto(tela, "Clique para equipar", 16, CIANO, LARGURA // 2 + 180, y_item + 10)
            
            max_scroll = max(0, len(armas_disponiveis) * 100 - (ALTURA - 300))
            
        else:  # Aba de Itens
            itens_disponiveis = inventario_manager.obter_itens_disponiveis()
            item_atual = inventario_manager.obter_item_selecionado()
            
            for i, (item_key, item_data) in enumerate(itens_disponiveis.items()):
                y_item = y_inicial + i * 100
                
                if y_item < -100 or y_item > ALTURA + 100:
                    continue
                
                # Cor de fundo baseada na disponibilidade e seleção
                if item_data["quantidade"] <= 0:
                    cor_fundo = (60, 40, 40)
                    cor_borda = (100, 60, 60)
                elif item_key == item_atual:
                    cor_fundo = (40, 80, 40)
                    cor_borda = (80, 160, 80)
                else:
                    cor_fundo = (60, 40, 80)
                    cor_borda = (120, 80, 160)
                
                # Desenhar fundo do item
                rect_item = pygame.Rect(LARGURA // 2 - 300, y_item - 35, 600, 70)
                pygame.draw.rect(tela, cor_fundo, rect_item, 0, 10)
                pygame.draw.rect(tela, cor_borda, rect_item, 3, 10)
                
                # Ícone especial baseado no item
                if item_key == "ampulheta":
                    desenhar_icone_ampulheta_inventario(tela, LARGURA // 2 - 265, y_item, tempo_atual)
                elif item_key == "granada":
                    desenhar_icone_granada_inventario(tela, LARGURA // 2 - 265, y_item, tempo_atual)
                
                # Informações do item
                cor_texto = BRANCO if item_data["quantidade"] > 0 else (150, 150, 150)
                desenhar_texto(tela, item_data["nome"], 26, cor_texto, LARGURA // 2 - 150, y_item - 10)
                desenhar_texto(tela, f"Usos: {item_data['quantidade']}", 20, cor_texto, LARGURA // 2 + 50, y_item - 10)
                desenhar_texto(tela, item_data["descricao"], 16, cor_texto, LARGURA // 2 - 150, y_item + 10)
                
                # Status de seleção
                if item_key == item_atual:
                    pygame.draw.polygon(tela, VERDE, [
                        (LARGURA // 2 + 250, y_item - 8),
                        (LARGURA // 2 + 270, y_item),
                        (LARGURA // 2 + 250, y_item + 8)
                    ])
                    desenhar_texto(tela, "EQUIPADO", 18, VERDE, LARGURA // 2 + 200, y_item)
                    desenhar_texto(tela, f"Tecla {item_data['tecla']}", 14, VERDE, LARGURA // 2 + 200, y_item + 15)
                elif item_data["quantidade"] <= 0:
                    desenhar_texto(tela, "NÃO COMPRADA", 16, VERMELHO, LARGURA // 2 + 180, y_item + 10)
                else:
                    desenhar_texto(tela, "Clique para equipar", 16, CIANO, LARGURA // 2 + 180, y_item + 10)
            
            max_scroll = max(0, len(itens_disponiveis) * 100 - (ALTURA - 300))
        
        # Desenhar barra de scroll se necessário
        if max_scroll > 0:
            barra_altura = max(50, int((ALTURA - 250) * (ALTURA - 250) / max_scroll))
            barra_y = 200 + int((scroll_y / max_scroll) * (ALTURA - 250 - barra_altura))
            pygame.draw.rect(tela, (100, 100, 100), (LARGURA - 20, 200, 10, ALTURA - 250))
            pygame.draw.rect(tela, (200, 200, 200), (LARGURA - 20, barra_y, 10, barra_altura))
        
        # Instruções
        if aba_ativa == 0:
            desenhar_texto(tela, "Press E to use weapon", 22, CIANO, LARGURA // 2, ALTURA - 120)
        else:
            desenhar_texto(tela, "Press Q to use items", 22, CIANO, LARGURA // 2, ALTURA - 120)
        
        desenhar_texto(tela, "Use as teclas 1 e 2 ou clique nas abas para navegar", 18, (180, 180, 180), LARGURA // 2, ALTURA - 100)
        
        # Botão voltar
        criar_botao(tela, "VOLTAR", 125, ALTURA - 50, 150, 60, (80, 50, 50), (120, 70, 70), BRANCO)
        
        pygame.display.flip()
        relogio.tick(FPS)


