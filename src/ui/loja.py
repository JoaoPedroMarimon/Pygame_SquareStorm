#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja do jogo, onde o jogador pode comprar upgrades.
Redesenhado com base no novo layout Figma.
"""

import pygame
import math
import json
import os
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.game.moeda_manager import MoedaManager
import sys
from src.ui.weapons_shop import desenhar_weapons_shop
from src.ui.upgrades_shop import desenhar_upgrades_shop
from src.ui.items_shop import desenhar_items_shop
from src.utils.display_manager import present_frame,convert_mouse_position



def tela_loja(tela, relogio, gradiente_loja):
    """
    Exibe a tela principal da loja onde o jogador pode escolher entre upgrades e armas.
    Design baseado no layout Figma.
    
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
    upgrades = carregar_upgrades()
    
    # Som de compra (um som de "ca-ching" ou campainha)
    som_compra = pygame.mixer.Sound(bytes(bytearray(
        int(127 + 127 * math.sin(i / 10) * (1.0 - i/4000)) 
        for i in range(8000)
    )))
    som_compra.set_volume(0.2)
    
    # Som de erro (quando não tem moedas suficientes)
    som_erro = pygame.mixer.Sound(bytes(bytearray(
        int(127 + 127 * math.sin(i / 5) * (1.0 - i/2000)) 
        for i in range(4000)
    )))
    som_erro.set_volume(0.15)
    
    # Variáveis para mensagens de feedback
    mensagem = ""
    mensagem_tempo = 0
    mensagem_duracao = 120  # Duração da mensagem em frames
    mensagem_cor = BRANCO
    
    # Efeito de transição ao entrar
    fade_in = 255
    
    # Variável para controlar qual aba da loja está ativa (0: armas, 1: upgrades, 2: items)
    aba_ativa = 0
    
    # Variáveis de scroll para cada aba
    scroll_weapons = 0      # NOVO: scroll para aba de armas
    scroll_upgrades = 0     # scroll para aba de upgrades (se necessário)
    scroll_items = 0        # scroll para aba de items
    max_scroll_weapons = 0  # NOVO: máximo scroll para armas
    max_scroll_upgrades = 0 # máximo scroll para upgrades
    max_scroll_items = 0    # máximo scroll para items
    
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
                        present_frame()
                        pygame.time.delay(5)
                    return "menu"
                # Teclas numéricas para trocar de categoria
                if evento.key == pygame.K_1:
                    aba_ativa = 0  # Armas
                if evento.key == pygame.K_2:
                    aba_ativa = 1  # Upgrades
                if evento.key == pygame.K_3:
                    aba_ativa = 2  # Items
            # Verificação de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
            # Scroll do mouse - ATUALIZADO para funcionar em todas as abas
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 4:  # Scroll up
                    if aba_ativa == 0:  # Armas
                        scroll_weapons = max(0, scroll_weapons - 30)
                    elif aba_ativa == 1:  # Upgrades
                        scroll_upgrades = max(0, scroll_upgrades - 30)
                    elif aba_ativa == 2:  # Items
                        scroll_items = max(0, scroll_items - 30)
                elif evento.button == 5:  # Scroll down
                    if aba_ativa == 0:  # Armas
                        scroll_weapons = min(max_scroll_weapons, scroll_weapons + 30)
                    elif aba_ativa == 1:  # Upgrades
                        scroll_upgrades = min(max_scroll_upgrades, scroll_upgrades + 30)
                    elif aba_ativa == 2:  # Items
                        scroll_items = min(max_scroll_items, scroll_items + 30)
        
        # Atualizar mensagem de feedback
        if mensagem:
            mensagem_tempo += 1
            if mensagem_tempo >= mensagem_duracao:
                mensagem = ""
                mensagem_tempo = 0
                
        # Efeito de fade in ao entrar
        if fade_in > 0:
            fade_in = max(0, fade_in - 10)
        
        # Desenhar fundo com gradiente
        tela.blit(gradiente_loja, (0, 0))
        
        # Desenhar estrelas animadas no fundo
        desenhar_estrelas(tela, estrelas)
        
        # Primeiro criar uma superfície com transparência
        s = pygame.Surface((LARGURA - 200, ALTURA - 200), pygame.SRCALPHA)
        
        # Desenhar retângulo preenchido com cantos arredondados diretamente na superfície
        pygame.draw.rect(s, (10, 10, 30, 200), (0, 0, LARGURA - 200, ALTURA - 200), 0, 15)
        
        # Aplicar a superfície com o retângulo na tela
        tela.blit(s, (100, 100))
        
        # Desenhar borda brilhante
        pygame.draw.rect(tela, (100, 100, 255), (100, 100, LARGURA - 200, ALTURA - 200), 3, 15)
        
        # Desenhar título da loja
        desenhar_texto(tela, "SHOP", 80, (200, 200, 255), LARGURA // 2, 140)
        
        # Mostrar quantidade de moedas - design simplificado
        moedas_x = LARGURA // 2
        moedas_y = 210
        
        # Desenhar uma única moeda circular
        moeda_cor = AMARELO
        
        # Moeda simples
        pygame.draw.circle(tela, moeda_cor, (moedas_x - 50, moedas_y), 20)
        
        # Mostrar quantidade de moedas
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 45, moeda_cor, moedas_x + 50, moedas_y)
        
        # Definir dimensões e posições para as abas
        aba_largura = 250
        aba_altura = 60
        espaco_entre_abas = 15
        altura_aba_y = 280
        
        # Calcular posições das abas (centralizadas)
        aba1_x = LARGURA // 2 - aba_largura - espaco_entre_abas
        aba2_x = LARGURA // 2 
        aba3_x = LARGURA // 2 + aba_largura + espaco_entre_abas
        
        # Desenhar as abas (botões de categoria)
        rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, altura_aba_y - aba_altura//2, aba_largura, aba_altura)
        rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, altura_aba_y - aba_altura//2, aba_largura, aba_altura)
        rect_aba3 = pygame.Rect(aba3_x - aba_largura//2, altura_aba_y - aba_altura//2, aba_largura, aba_altura)
        
        # Verificar hover para as abas
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        hover_aba1 = rect_aba1.collidepoint(mouse_pos)
        hover_aba2 = rect_aba2.collidepoint(mouse_pos)
        hover_aba3 = rect_aba3.collidepoint(mouse_pos)
        
        # Desenhar aba 1 (Armas)
        cor_aba1 = (150, 50, 50) if aba_ativa == 0 else (80, 30, 30)
        cor_hover_aba1 = (200, 70, 70) if aba_ativa == 0 else (100, 40, 40)
        pygame.draw.rect(tela, cor_hover_aba1 if hover_aba1 else cor_aba1, rect_aba1, 0, 10)
        pygame.draw.rect(tela, (255, 100, 100), rect_aba1, 3 if aba_ativa == 0 else 1, 10)
        
        # Ícone de arma para aba 1 (código do ícone mantido igual)
        arma_x = aba1_x - 100
        arma_y = altura_aba_y
        arma_cor = (255, 100, 100)
        arma_cor_escura = (200, 80, 80)
        
        tempo_pulso = (pygame.time.get_ticks() % 1000) / 1000.0
        tiro_visivel = tempo_pulso > 0.7
        
        if tiro_visivel:
            pygame.draw.circle(tela, (255, 255, 100), (arma_x - 22, arma_y), 7)
            pygame.draw.circle(tela, (255, 200, 50), (arma_x - 22, arma_y), 4)
        
        pygame.draw.rect(tela, arma_cor, (arma_x - 20, arma_y - 5, 25, 10), 0, 3)
        pygame.draw.rect(tela, arma_cor_escura, (arma_x - 18, arma_y - 7, 3, 3), 0, 1)
        pygame.draw.rect(tela, arma_cor, (arma_x - 2, arma_y - 5, 14, 20), 0, 3)
        pygame.draw.rect(tela, arma_cor_escura, (arma_x + 9, arma_y - 5, 3, 6), 0, 1)
        pygame.draw.rect(tela, arma_cor_escura, (arma_x + 3, arma_y + 6, 4, 8), 0, 1)
        pygame.draw.rect(tela, arma_cor, (arma_x + 2, arma_y + 12, 7, 12), 0, 3)
        
        desenhar_texto(tela, "WEAPONS", 28, BRANCO, aba1_x, altura_aba_y)
        
        # Desenhar aba 2 (Upgrades) - código mantido igual
        cor_aba2 = (50, 80, 150) if aba_ativa == 1 else (30, 50, 80)
        cor_hover_aba2 = (70, 100, 200) if aba_ativa == 1 else (40, 60, 100)
        pygame.draw.rect(tela, cor_hover_aba2 if hover_aba2 else cor_aba2, rect_aba2, 0, 10)
        pygame.draw.rect(tela, (100, 150, 255), rect_aba2, 3 if aba_ativa == 1 else 1, 10)
        
        upgrade_x = aba2_x - 100
        upgrade_y = altura_aba_y
        upgrade_cor = (100, 150, 255)
        
        tempo_anim = pygame.time.get_ticks() / 1000.0
        offset_y = math.sin(tempo_anim * 3) * 5
        
        ponta_x = upgrade_x
        ponta_y = upgrade_y - 10 + offset_y
        base_esq_x = upgrade_x - 10
        base_esq_y = upgrade_y + 5 + offset_y
        base_dir_x = upgrade_x + 10
        base_dir_y = upgrade_y + 5 + offset_y
        
        cor_pulso = (
            int(100 + 50 * math.sin(tempo_anim * 5)), 
            int(150 + 50 * math.sin(tempo_anim * 5)), 
            255
        )
        
        pygame.draw.polygon(tela, cor_pulso, [(ponta_x, ponta_y), (base_esq_x, base_esq_y), (base_dir_x, base_dir_y)])
        pygame.draw.rect(tela, cor_pulso, (upgrade_x - 3, upgrade_y + 5 + offset_y, 6, 10))
        
        alpha_brilho = int(128 + 127 * math.sin(tempo_anim * 6))
        if alpha_brilho > 50:
            brilho_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            cor_brilho = (150, 200, 255, alpha_brilho)
            pygame.draw.polygon(brilho_surf, cor_brilho, [(15, 5), (5, 20), (25, 20)])
            tela.blit(brilho_surf, (upgrade_x - 15, upgrade_y - 15 + offset_y))
        
        desenhar_texto(tela, "UPGRADES", 28, BRANCO, aba2_x, altura_aba_y)
        
        # Desenhar aba 3 (Items) - código mantido igual
        cor_aba3 = (50, 120, 50) if aba_ativa == 2 else (30, 70, 30)
        cor_hover_aba3 = (70, 160, 70) if aba_ativa == 2 else (40, 90, 40)
        pygame.draw.rect(tela, cor_hover_aba3 if hover_aba3 else cor_aba3, rect_aba3, 0, 10)
        pygame.draw.rect(tela, (120, 220, 120), rect_aba3, 3 if aba_ativa == 2 else 1, 10)
        
        item_x = aba3_x - 100
        item_y = altura_aba_y
        
        cor_granada = (100, 180, 100)
        tamanho_granada = 12
        
        pygame.draw.circle(tela, cor_granada, (item_x, item_y), tamanho_granada)
        pygame.draw.rect(tela, (150, 150, 150), (item_x - 4, item_y - tamanho_granada - 5, 8, 5), 0, 2)
        
        pin_x = item_x + 7
        pin_y = item_y - tamanho_granada - 2
        pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), 5, 2)
        
        tempo_pulso = (pygame.time.get_ticks() % 2000) / 2000.0
        if tempo_pulso > 0.7:
            pygame.draw.circle(tela, (150, 255, 150), (item_x, item_y), tamanho_granada+3, 2)
        
        desenhar_texto(tela, "ITEMS", 28, BRANCO, aba3_x, altura_aba_y)
        
        # Verificar cliques nas abas
        if clique_ocorreu:
            if rect_aba1.collidepoint(mouse_pos):
                aba_ativa = 0  # Armas
            elif rect_aba2.collidepoint(mouse_pos):
                aba_ativa = 1  # Upgrades
            elif rect_aba3.collidepoint(mouse_pos):
                aba_ativa = 2  # Items
        
        # Área de conteúdo da aba ativa - movida para cima
        area_conteudo = pygame.Rect(150, 330, LARGURA - 300, ALTURA - 450)
        pygame.draw.rect(tela, (20, 20, 50, 150), area_conteudo, 0, 10)
        pygame.draw.rect(tela, (70, 70, 130), area_conteudo, 2, 10)
        
        if aba_ativa == 0:  # Armas - ATUALIZADO para usar scroll
            resultado = desenhar_weapons_shop(tela, area_conteudo, moeda_manager, upgrades, 
                                            mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_weapons)
            if resultado and resultado[0]:  # Se há mensagem
                mensagem, mensagem_cor, max_scroll_weapons = resultado
                mensagem_tempo = 0
            elif resultado:  # Só atualizar max_scroll se não houver mensagem
                _, _, max_scroll_weapons = resultado

        elif aba_ativa == 1:  # Upgrades
            resultado = desenhar_upgrades_shop(tela, area_conteudo, moeda_manager, upgrades, 
                                             mouse_pos, clique_ocorreu, som_compra, som_erro)
            if resultado and resultado[0]:  # Se há mensagem
                mensagem, mensagem_cor, _ = resultado
                mensagem_tempo = 0

        else:  # Items (aba 2)
            resultado = desenhar_items_shop(tela, area_conteudo, moeda_manager, upgrades, 
                                          mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_items)
            if resultado and resultado[0]:  # Verificar se há mensagem
                mensagem, mensagem_cor, max_scroll_items = resultado
                mensagem_tempo = 0
            elif resultado:  # Só atualizar max_scroll se não houver mensagem
                _, _, max_scroll_items = resultado
        
        # Desenhar botão de voltar (ajustado para ficar mais abaixo)
        botao_voltar_largura = 240
        botao_voltar_altura = 50
        botao_voltar_x = LARGURA // 2
        botao_voltar_y = ALTURA - 50
        rect_voltar = pygame.Rect(botao_voltar_x - botao_voltar_largura//2, 
                               botao_voltar_y - botao_voltar_altura//2, 
                               botao_voltar_largura, botao_voltar_altura)
        
        # Verificar hover para o botão voltar
        hover_voltar = rect_voltar.collidepoint(mouse_pos)
        
        # Desenhar o botão voltar com estilo Figma
        cor_voltar = (80, 80, 220) if hover_voltar else (60, 60, 150)
        pygame.draw.rect(tela, cor_voltar, rect_voltar, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_voltar, 2, 10)
        
        # Texto do botão voltar
        texto_voltar = pygame.font.SysFont("Arial", 26).render("BACK TO MENU", True, BRANCO)
        texto_rect_voltar = texto_voltar.get_rect(center=(botao_voltar_x, botao_voltar_y))
        tela.blit(texto_voltar, texto_rect_voltar)
        
        # Verificar clique no botão de voltar
        if clique_ocorreu and rect_voltar.collidepoint(mouse_pos):
            # Efeito de fade out ao sair
            for i in range(30):
                fade = pygame.Surface((LARGURA, ALTURA))
                fade.fill((0, 0, 0))
                fade.set_alpha(i * 8)
                tela.blit(fade, (0, 0))
                present_frame()
                pygame.time.delay(5)
            return "menu"
        
        # Mostrar mensagem de feedback se existir
        if mensagem:
            # Fazer a mensagem pulsar
            alpha = int(255 * (1.0 - mensagem_tempo / mensagem_duracao))
            y_mensagem = area_conteudo.y - 20
            fonte = pygame.font.SysFont("Arial", 30, True)
            texto_surf = fonte.render(mensagem, True, mensagem_cor)
            texto_surf.set_alpha(alpha)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, y_mensagem))
            tela.blit(texto_surf, texto_rect)
        
        # Aplicar efeito de fade-in
        if fade_in > 0:
            fade = pygame.Surface((LARGURA, ALTURA))
            fade.fill((0, 0, 0))
            fade.set_alpha(fade_in)
            tela.blit(fade, (0, 0))
        
        present_frame()
        relogio.tick(FPS)
    
    return "menu"
        

# Update in src/ui/loja.py - carregar_upgrades function
# Substitua a função carregar_upgrades() no arquivo src/ui/loja.py por esta versão:

def carregar_upgrades():
    """
    Carrega os upgrades salvos do arquivo.
    Se o arquivo não existir, inicia com valores padrão.
    """
    upgrades_padrao = {
        "vida": 1,
        "desert_eagle": 0,
        "espingarda": 0,
        "metralhadora": 0,
        "sabre_luz": 0,
        "granada": 0,
        "ampulheta": 0,
        "faca": 0
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