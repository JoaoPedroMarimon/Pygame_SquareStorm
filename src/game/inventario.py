#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo completo do sistema de inventário do jogo.
Inclui tanto a lógica quanto a interface visual.
"""

import pygame
import json
import os
import random
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
# MoedaManager será importado dentro da função para evitar circular import

class InventarioManager:
    """Gerencia o inventário e a seleção de armas do jogador."""
    
    def __init__(self):
        self.arma_selecionada = "nenhuma"  # Padrão: nenhuma arma especial
        self.arquivo_inventario = "data/inventario.json"
        self.carregar_inventario()
    
    def carregar_inventario(self):
        """Carrega a configuração do inventário do arquivo."""
        try:
            if os.path.exists(self.arquivo_inventario):
                with open(self.arquivo_inventario, "r") as f:
                    data = json.load(f)
                    self.arma_selecionada = data.get("arma_selecionada", "nenhuma")
            else:
                self.salvar_inventario()
        except Exception as e:
            print(f"Erro ao carregar inventário: {e}")
            self.arma_selecionada = "nenhuma"
    
    def salvar_inventario(self):
        """Salva a configuração atual do inventário."""
        try:
            # Criar diretório se não existir
            os.makedirs("data", exist_ok=True)
            
            data = {
                "arma_selecionada": self.arma_selecionada
            }
            
            with open(self.arquivo_inventario, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar inventário: {e}")
    
    def selecionar_arma(self, arma):
        """Seleciona uma arma para usar na partida."""
        self.arma_selecionada = arma
        self.salvar_inventario()
    
    def obter_arma_selecionada(self):
        """Retorna a arma atualmente selecionada."""
        return self.arma_selecionada
    
    def obter_armas_disponiveis(self):
        """Retorna dicionário com as armas disponíveis no inventário."""
        armas = {
            "espingarda": {"nome": "Espingarda", "quantidade": 0, "cor": AMARELO, "descricao": "Disparo múltiplo devastador"},
            "metralhadora": {"nome": "Metralhadora", "quantidade": 0, "cor": LARANJA, "descricao": "Cadência de tiro extrema"}
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

def tela_inventario(tela, relogio, gradiente_inventario, fonte_titulo, fonte_normal):
    """
    Exibe a tela de inventário onde o jogador pode selecionar sua arma.
    
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
    
    # Obter armas disponíveis
    armas_disponiveis = inventario_manager.obter_armas_disponiveis()
    arma_atual = inventario_manager.obter_arma_selecionada()
    
    # Scroll do inventário
    scroll_y = 0
    max_scroll = 0
    
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Clique esquerdo
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Verificar cliques nos botões de arma
                    y_inicial = 200 - scroll_y
                    for i, (arma_key, arma_data) in enumerate(armas_disponiveis.items()):
                        y_arma = y_inicial + i * 120
                        
                        # Verificar se a arma está disponível
                        if arma_data["quantidade"] <= 0:
                            continue
                        
                        # Área clicável da arma
                        rect_arma = pygame.Rect(LARGURA // 2 - 300, y_arma - 40, 600, 80)
                        
                        if rect_arma.collidepoint(mouse_pos) and y_arma > 50 and y_arma < ALTURA - 100:
                            inventario_manager.selecionar_arma(arma_key)
                            arma_atual = arma_key
                    
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
        desenhar_texto(tela, "INVENTÁRIO DE ARMAS", 50, BRANCO, LARGURA // 2, 70)
        desenhar_texto(tela, "Selecione uma arma para equipar (tecla E no jogo)", 28, AMARELO, LARGURA // 2, 120)
        
        # Mostrar moedas
        moeda_size = 12
        pygame.draw.circle(tela, AMARELO, (LARGURA - 100, 30), moeda_size)
        pygame.draw.circle(tela, (255, 215, 0), (LARGURA - 100, 30), moeda_size - 2)
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 24, AMARELO, LARGURA - 70, 30)
        
        # Desenhar armas disponíveis
        y_inicial = 200 - scroll_y
        armas_visiveis = 0
        
        for i, (arma_key, arma_data) in enumerate(armas_disponiveis.items()):
            y_arma = y_inicial + i * 120
            
            # Verificar se a arma está visível na tela
            if y_arma < -100 or y_arma > ALTURA + 100:
                continue
            
            armas_visiveis += 1
            
            # Cor de fundo baseada na disponibilidade e seleção
            if arma_data["quantidade"] <= 0:
                cor_fundo = (60, 40, 40)  # Indisponível
                cor_borda = (100, 60, 60)
                alpha = 100
            elif arma_key == arma_atual:
                cor_fundo = (40, 80, 40)  # Selecionada
                cor_borda = (80, 160, 80)
                alpha = 255
            else:
                cor_fundo = (40, 40, 80)  # Disponível
                cor_borda = (80, 80, 160)
                alpha = 200
            
            # Desenhar fundo da arma
            rect_arma = pygame.Rect(LARGURA // 2 - 300, y_arma - 40, 600, 80)
            pygame.draw.rect(tela, cor_fundo, rect_arma, 0, 10)
            pygame.draw.rect(tela, cor_borda, rect_arma, 3, 10)
            
            # Ícone da arma (quadrado colorido)
            icone_rect = pygame.Rect(LARGURA // 2 - 280, y_arma - 20, 40, 40)
            pygame.draw.rect(tela, arma_data["cor"], icone_rect, 0, 5)
            pygame.draw.rect(tela, BRANCO, icone_rect, 2, 5)
            
            # Nome da arma
            cor_texto = BRANCO if arma_data["quantidade"] > 0 else (150, 150, 150)
            desenhar_texto(tela, arma_data["nome"], 28, cor_texto, LARGURA // 2 - 150, y_arma - 10)
            
            # Quantidade
            quantidade_texto = str(arma_data["quantidade"])
            desenhar_texto(tela, f"Munição: {quantidade_texto}", 22, cor_texto, LARGURA // 2 + 50, y_arma - 15)
            
            # Descrição
            desenhar_texto(tela, arma_data["descricao"], 18, cor_texto, LARGURA // 2 - 150, y_arma + 15)
            
            # Indicador de seleção
            if arma_key == arma_atual:
                pygame.draw.polygon(tela, VERDE, [
                    (LARGURA // 2 + 250, y_arma - 10),
                    (LARGURA // 2 + 270, y_arma),
                    (LARGURA // 2 + 250, y_arma + 10)
                ])
                desenhar_texto(tela, "EQUIPADA", 20, VERDE, LARGURA // 2 + 200, y_arma)
            
            # Status de disponibilidade
            if arma_data["quantidade"] <= 0:
                desenhar_texto(tela, "NÃO COMPRADA", 18, VERMELHO, LARGURA // 2 + 180, y_arma + 15)
        
        # Calcular scroll máximo
        max_scroll = max(0, len(armas_disponiveis) * 120 - (ALTURA - 300))
        
        # Desenhar barra de scroll se necessário
        if max_scroll > 0:
            barra_altura = max(50, int((ALTURA - 200) * (ALTURA - 200) / (len(armas_disponiveis) * 120)))
            barra_y = 150 + int((scroll_y / max_scroll) * (ALTURA - 200 - barra_altura))
            pygame.draw.rect(tela, (100, 100, 100), (LARGURA - 20, 150, 10, ALTURA - 200))
            pygame.draw.rect(tela, (200, 200, 200), (LARGURA - 20, barra_y, 10, barra_altura))
        
        # Instruções
        desenhar_texto(tela, "Clique em uma arma para selecioná-la", 22, CIANO, LARGURA // 2, ALTURA - 120)
        desenhar_texto(tela, "Use a tecla E no jogo para equipar a arma selecionada", 18, (180, 180, 180), LARGURA // 2, ALTURA - 100)
        
        # Botão voltar
        criar_botao(tela, "VOLTAR", 125, ALTURA - 50, 150, 60, (80, 50, 50), (120, 70, 70), BRANCO)
        
        pygame.display.flip()
        relogio.tick(FPS)