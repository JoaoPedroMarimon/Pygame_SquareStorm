#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja do jogo, onde o jogador pode comprar upgrades.
"""

import pygame
import math
import random
import json
import os
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.game.moeda_manager import MoedaManager
import sys
from src.ui.tela_upgrades import tela_upgrades
from src.ui.tela_armas import tela_armas

def tela_loja(tela, relogio, gradiente_loja):
    """
    Exibe a tela principal da loja onde o jogador pode escolher entre upgrades e armas.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_loja: Superfície com o gradiente de fundo da loja
        
    Returns:
        "menu" para voltar ao menu principal
    """
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    
    # Inicializar gerenciador de moedas para ter acesso à quantidade
    moeda_manager = MoedaManager()
    
    # Efeito de transição ao entrar
    fade_in = 255
    
    # Loop principal da loja
    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                # Tecla ESC, Backspace ou M para voltar ao menu
                if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_BACKSPACE or evento.key == pygame.K_m:
                    # Efeito de fade out ao sair
                    for i in range(30):
                        fade = pygame.Surface((LARGURA, ALTURA))
                        fade.fill((0, 0, 0))
                        fade.set_alpha(i * 8)
                        tela.blit(fade, (0, 0))
                        pygame.display.flip()
                        pygame.time.delay(5)
                    return "menu"
            # Verificação de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
        # Efeito de fade in ao entrar
        if fade_in > 0:
            fade_in = max(0, fade_in - 10)
        
        # Desenhar fundo
        tela.blit(gradiente_loja, (0, 0))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar título
        desenhar_texto(tela, "LOJA", 70, BRANCO, LARGURA // 2, 80)
        
        # Mostrar quantidade de moedas
        cor_moeda = AMARELO
        pygame.draw.circle(tela, cor_moeda, (LARGURA // 2 - 100, 150), 15)  # Ícone de moeda maior
        desenhar_texto(tela, f"Suas moedas: {moeda_manager.obter_quantidade()}", 28, cor_moeda, LARGURA // 2 + 50, 150)
        
        # Desenhar divisória
        pygame.draw.line(tela, (100, 100, 150), (LARGURA // 4, 180), (3 * LARGURA // 4, 180), 2)
        
        # Configurações dos botões (LADO A LADO e MAIORES)
        botao_largura = 350  # Aumentado de 240 para 350
        botao_altura = 200   # Aumentado de 65 para 200
        espacamento = 80     # Espaço entre os botões
        
        # Calcular posições X para os dois botões lado a lado
        pos_x_upgrades = LARGURA // 2 - (botao_largura + espacamento) // 2
        pos_x_armas = LARGURA // 2 + (botao_largura + espacamento) // 2
        
        # Posição Y comum para ambos os botões
        pos_y = ALTURA // 2
        
        # ==== BOTÃO DE UPGRADES (ESQUERDA) ====
        # Criar retângulo para o botão de upgrades
# ==== BOTÃO DE UPGRADES (ESQUERDA) ====
# Criar retângulo para o botão de upgrades
        rect_upgrades = pygame.Rect(pos_x_upgrades - botao_largura // 2, 
                                pos_y - botao_altura // 2, 
                                botao_largura, botao_altura)

        # Verificar hover
        mouse_pos = pygame.mouse.get_pos()
        hover_upgrades = rect_upgrades.collidepoint(mouse_pos)

        # Desenhar o botão
        cor_upgrades = (80, 180, 80) if hover_upgrades else (60, 120, 60)
        pygame.draw.rect(tela, cor_upgrades, rect_upgrades, 0, 15)
        pygame.draw.rect(tela, BRANCO, rect_upgrades, 3, 15)  

        # Desenhar símbolo de seta para cima (estilo mais próximo da imagem)
        centro_x = pos_x_upgrades
        centro_y = pos_y - 20

        # Primeira seta (maior, em baixo)
        tamanho_seta1 = 80
        espessura_seta = 8

        # Pontos para a primeira seta (formato de "v" invertido)
        pontos_seta1 = [
            (centro_x - tamanho_seta1//2, centro_y + tamanho_seta1//3),  # Ponta esquerda
            (centro_x, centro_y - tamanho_seta1//3),                     # Ponta superior
            (centro_x + tamanho_seta1//2, centro_y + tamanho_seta1//3)   # Ponta direita
        ]

        # Desenhar a primeira seta com gradiente rosa
        pygame.draw.lines(tela, (255, 50, 140), False, pontos_seta1, espessura_seta)
        # Adicionar brilho cyan na borda
        pygame.draw.lines(tela, (100, 255, 255), False, pontos_seta1, 2)

        # Segunda seta (menor, em cima)
        tamanho_seta2 = 60
        offset_y = -25  # Deslocamento para cima

        # Pontos para a segunda seta
        pontos_seta2 = [
            (centro_x - tamanho_seta2//2, centro_y + tamanho_seta2//3 + offset_y),  # Ponta esquerda
            (centro_x, centro_y - tamanho_seta2//3 + offset_y),                     # Ponta superior
            (centro_x + tamanho_seta2//2, centro_y + tamanho_seta2//3 + offset_y)   # Ponta direita
        ]

        # Desenhar a segunda seta com cor mais clara
        pygame.draw.lines(tela, (200, 100, 255), False, pontos_seta2, espessura_seta)
        # Adicionar brilho cyan na borda
        pygame.draw.lines(tela, (120, 255, 255), False, pontos_seta2, 2)

        # Adicionar brilho na junção das setas

        # Texto do botão
        fonte_botao = pygame.font.SysFont("Arial", 32, True)
        texto_upgrades = fonte_botao.render("UPGRADES", True, BRANCO)
        texto_rect_upgrades = texto_upgrades.get_rect(center=(pos_x_upgrades, pos_y + botao_altura//3))
        tela.blit(texto_upgrades, texto_rect_upgrades)
        
        # ==== BOTÃO DE ARMAS (DIREITA) ====
        # Criar retângulo para o botão de armas
        rect_armas = pygame.Rect(pos_x_armas - botao_largura // 2, 
                                pos_y - botao_altura // 2, 
                                botao_largura, botao_altura)
        
        # Verificar hover
        hover_armas = rect_armas.collidepoint(mouse_pos)
        
        # Desenhar o botão
        cor_armas = (80, 80, 220) if hover_armas else (60, 60, 150)
        pygame.draw.rect(tela, cor_armas, rect_armas, 0, 15)  # Raio do arredondamento aumentado para 15
        pygame.draw.rect(tela, BRANCO, rect_armas, 3, 15)  # Bordas mais grossas (3px)
        
        # Desenhar símbolo de mira
        tamanho_mira = 80  # Tamanho do símbolo
        centro_x = pos_x_armas
        centro_y = pos_y - 20
        raio_externo = tamanho_mira // 2
        espessura = 8
        
        # Círculo externo
        pygame.draw.circle(tela, PRETO, (centro_x, centro_y), raio_externo, espessura)
        
        # Marcas de posição (cima, baixo, esquerda, direita)
        comprimento_marca = raio_externo // 2
        
        # Marca superior
        pygame.draw.rect(tela, PRETO, 
                       (centro_x - espessura//2, centro_y - raio_externo, 
                        espessura, comprimento_marca))
        
        # Marca inferior
        pygame.draw.rect(tela, PRETO, 
                       (centro_x - espessura//2, centro_y + raio_externo - comprimento_marca, 
                        espessura, comprimento_marca))
        
        # Marca esquerda
        pygame.draw.rect(tela, PRETO, 
                       (centro_x - raio_externo, centro_y - espessura//2, 
                        comprimento_marca, espessura))
        
        # Marca direita
        pygame.draw.rect(tela, PRETO, 
                       (centro_x + raio_externo - comprimento_marca, centro_y - espessura//2, 
                        comprimento_marca, espessura))
        
        # Texto do botão
        texto_armas = fonte_botao.render("ARMAS", True, BRANCO)
        texto_rect_armas = texto_armas.get_rect(center=(pos_x_armas, pos_y + botao_altura//3))
        tela.blit(texto_armas, texto_rect_armas)
        
        # Desenhar botão de voltar
        botao_voltar_largura = 240
        botao_voltar_altura = 50
        botao_voltar_x = LARGURA // 2
        botao_voltar_y = ALTURA - 80
        rect_voltar = pygame.Rect(botao_voltar_x - botao_voltar_largura//2, 
                               botao_voltar_y - botao_voltar_altura//2, 
                               botao_voltar_largura, botao_voltar_altura)
        
        # Verificar hover para o botão voltar
        hover_voltar = rect_voltar.collidepoint(mouse_pos)
        
        # Desenhar o botão voltar
        cor_voltar = (80, 80, 220) if hover_voltar else (60, 60, 150)
        pygame.draw.rect(tela, cor_voltar, rect_voltar, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_voltar, 2, 10)
        
        # Texto do botão voltar
        texto_voltar = pygame.font.SysFont("Arial", 26).render("MENU (ESC)", True, BRANCO)
        texto_rect_voltar = texto_voltar.get_rect(center=(botao_voltar_x, botao_voltar_y))
        tela.blit(texto_voltar, texto_rect_voltar)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            # Clique no botão de upgrades
            if rect_upgrades.collidepoint(mouse_pos):
                tela_upgrades(tela, relogio, gradiente_loja)
                
            # Clique no botão de armas
            elif rect_armas.collidepoint(mouse_pos):
                tela_armas(tela, relogio, gradiente_loja)
                
            # Clique no botão de voltar
            elif rect_voltar.collidepoint(mouse_pos):
                # Efeito de fade out ao sair
                for i in range(30):
                    fade = pygame.Surface((LARGURA, ALTURA))
                    fade.fill((0, 0, 0))
                    fade.set_alpha(i * 8)
                    tela.blit(fade, (0, 0))
                    pygame.display.flip()
                    pygame.time.delay(5)
                return "menu"
        
        # Aplicar efeito de fade-in
        if fade_in > 0:
            fade = pygame.Surface((LARGURA, ALTURA))
            fade.fill((0, 0, 0))
            fade.set_alpha(fade_in)
            tela.blit(fade, (0, 0))
        
        pygame.display.flip()
        relogio.tick(FPS)
    
    return "menu"
        

# Update in src/ui/loja.py - carregar_upgrades function
def carregar_upgrades():
    """
    Carrega os upgrades salvos do arquivo.
    Se o arquivo não existir, inicia com valores padrão.
    """
    upgrades_padrao = {
        "vida": 1,  # Vida máxima inicial é 1
        "espingarda": 0  # Tiros de espingarda disponíveis (0 = não tem)
    }
    
    try:
        # Criar o diretório de dados se não existir
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Tentar carregar o arquivo de upgrades
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                # Verificar se todas as chaves existem
                for chave in upgrades_padrao:
                    if chave not in upgrades:
                        upgrades[chave] = upgrades_padrao[chave]
                return upgrades
        
        # Se o arquivo não existir, criar com valores padrão e retornar
        salvar_upgrades(upgrades_padrao)
        return upgrades_padrao
    except Exception as e:
        print(f"Erro ao carregar upgrades: {e}")
        return upgrades_padrao

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