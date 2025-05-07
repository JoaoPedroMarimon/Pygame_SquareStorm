#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a loja do jogo, onde o jogador pode comprar upgrades.
Redesenhado com base no novo layout Figma.
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
from src.ui.weapons_shop import desenhar_weapons_shop
from src.ui.upgrades_shop import desenhar_upgrades_shop

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
    
    # Variável para controlar qual aba da loja está ativa (0: armas, 1: upgrades)
    aba_ativa = 0
    
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
                # Teclas numéricas para trocar de categoria
                if evento.key == pygame.K_1:
                    aba_ativa = 0  # Armas
                if evento.key == pygame.K_2:
                    aba_ativa = 1  # Upgrades
            # Verificação de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
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
        aba_largura = 300
        aba_altura = 60
        espaco_entre_abas = 20
        altura_aba_y = 280
        
        # Calcular posições das abas (centralizadas)
        aba1_x = LARGURA // 2 - aba_largura - espaco_entre_abas // 2
        aba2_x = LARGURA // 2 + espaco_entre_abas // 2
        
        # Desenhar as abas (botões de categoria)
        rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, altura_aba_y - aba_altura//2, aba_largura, aba_altura)
        rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, altura_aba_y - aba_altura//2, aba_largura, aba_altura)
        
        # Verificar hover para as abas
        mouse_pos = pygame.mouse.get_pos()
        hover_aba1 = rect_aba1.collidepoint(mouse_pos)
        hover_aba2 = rect_aba2.collidepoint(mouse_pos)
        
        # Desenhar aba 1 (Armas)
        cor_aba1 = (150, 50, 50) if aba_ativa == 0 else (80, 30, 30)
        cor_hover_aba1 = (200, 70, 70) if aba_ativa == 0 else (100, 40, 40)
        pygame.draw.rect(tela, cor_hover_aba1 if hover_aba1 else cor_aba1, rect_aba1, 0, 10)
        pygame.draw.rect(tela, (255, 100, 100), rect_aba1, 3 if aba_ativa == 0 else 1, 10)
        
        # Ícone de arma para aba 1
        arma_x = aba1_x - 100
        arma_y = altura_aba_y
        arma_cor = (255, 100, 100)
        arma_cor_escura = (200, 80, 80)  # Cor mais escura para detalhes
        
        # Tempo pulsante para animar o tiro
        tempo_pulso = (pygame.time.get_ticks() % 1000) / 1000.0
        tiro_visivel = tempo_pulso > 0.7  # Pisca periodicamente
        
        # Desenhar o efeito de tiro (flash na ponta do cano)
        if tiro_visivel:
            # Flash do tiro
            pygame.draw.circle(tela, (255, 255, 100), (arma_x - 22, arma_y), 7)  # Flash amarelo
            pygame.draw.circle(tela, (255, 200, 50), (arma_x - 22, arma_y), 4)   # Centro do flash (laranja)
        
        # Desenhar uma pistola com mais detalhes
        # Cano
        pygame.draw.rect(tela, arma_cor, (arma_x - 20, arma_y - 5, 25, 10), 0, 3)
        
        # Detalhe da mira no cano
        pygame.draw.rect(tela, arma_cor_escura, (arma_x - 18, arma_y - 7, 3, 3), 0, 1)
        
        # Corpo principal
        pygame.draw.rect(tela, arma_cor, (arma_x - 2, arma_y - 5, 14, 20), 0, 3)
        
        # Detalhe do corpo (parte traseira)
        pygame.draw.rect(tela, arma_cor_escura, (arma_x + 9, arma_y - 5, 3, 6), 0, 1)
        
        # Gatilho (mais detalhado)
        pygame.draw.rect(tela, arma_cor_escura, (arma_x + 3, arma_y + 6, 4, 8), 0, 1)
        
        # Cabo/empunhadura (mais fino)
        pygame.draw.rect(tela, arma_cor, (arma_x + 2, arma_y + 12, 7, 12), 0, 3)
        
        # Texto da aba 1
        desenhar_texto(tela, "WEAPONS", 28, BRANCO, aba1_x, altura_aba_y)
        
        # Desenhar aba 2 (Upgrades)
        cor_aba2 = (50, 80, 150) if aba_ativa == 1 else (30, 50, 80)
        cor_hover_aba2 = (70, 100, 200) if aba_ativa == 1 else (40, 60, 100)
        pygame.draw.rect(tela, cor_hover_aba2 if hover_aba2 else cor_aba2, rect_aba2, 0, 10)
        pygame.draw.rect(tela, (100, 150, 255), rect_aba2, 3 if aba_ativa == 1 else 1, 10)
        
        # Ícone de upgrade para aba 2
        upgrade_x = aba2_x - 100
        upgrade_y = altura_aba_y
        upgrade_cor = (100, 150, 255)
        
        # Tempo para animação do símbolo de upgrade
        tempo_anim = pygame.time.get_ticks() / 1000.0
        
        # Animação de movimento para cima e para baixo
        offset_y = math.sin(tempo_anim * 3) * 5  # Movimento suave para cima e para baixo
        
        # Desenhar um ícone de seta para cima com animação
        ponta_x = upgrade_x
        ponta_y = upgrade_y - 10 + offset_y  # A seta sobe e desce
        base_esq_x = upgrade_x - 10
        base_esq_y = upgrade_y + 5 + offset_y
        base_dir_x = upgrade_x + 10
        base_dir_y = upgrade_y + 5 + offset_y
        
        # Cores que pulsam (de azul claro para azul mais brilhante)
        cor_pulso = (
            int(100 + 50 * math.sin(tempo_anim * 5)), 
            int(150 + 50 * math.sin(tempo_anim * 5)), 
            255
        )
        
        # Desenhar a seta que pulsa de cor
        pygame.draw.polygon(tela, cor_pulso, [(ponta_x, ponta_y), (base_esq_x, base_esq_y), (base_dir_x, base_dir_y)])
        pygame.draw.rect(tela, cor_pulso, (upgrade_x - 3, upgrade_y + 5 + offset_y, 6, 10))
        
        # Efeito de brilho ao redor da seta (aparece e desaparece)
        alpha_brilho = int(128 + 127 * math.sin(tempo_anim * 6))
        if alpha_brilho > 50:  # Só mostrar quando o brilho for significativo
            # Criar superfície com transparência para o brilho
            brilho_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            cor_brilho = (150, 200, 255, alpha_brilho)
            
            # Desenhar brilho maior ao redor da seta
            pygame.draw.polygon(brilho_surf, cor_brilho, [
                (15, 5), 
                (5, 20), 
                (25, 20)
            ])
            
            # Desenhar o brilho na tela
            tela.blit(brilho_surf, (upgrade_x - 15, upgrade_y - 15 + offset_y))
        
        # Texto da aba 2
        desenhar_texto(tela, "UPGRADES", 28, BRANCO, aba2_x, altura_aba_y)
        
        # Verificar cliques nas abas
        if clique_ocorreu:
            if rect_aba1.collidepoint(mouse_pos):
                aba_ativa = 0  # Armas
            elif rect_aba2.collidepoint(mouse_pos):
                aba_ativa = 1  # Upgrades
        
        # Área de conteúdo da aba ativa - movida para cima
        area_conteudo = pygame.Rect(150, 330, LARGURA - 300, ALTURA - 450)
        pygame.draw.rect(tela, (20, 20, 50, 150), area_conteudo, 0, 10)
        pygame.draw.rect(tela, (70, 70, 130), area_conteudo, 2, 10)
        
        # Desenhar itens baseados na aba ativa
        if aba_ativa == 0:  # Armas
            resultado = desenhar_weapons_shop(tela, area_conteudo, moeda_manager, upgrades, 
                                          mouse_pos, clique_ocorreu, som_compra, som_erro)
            if resultado:
                mensagem, mensagem_cor = resultado
                mensagem_tempo = 0
        else:  # Upgrades
            resultado = desenhar_upgrades_shop(tela, area_conteudo, moeda_manager, upgrades, 
                                          mouse_pos, clique_ocorreu, som_compra, som_erro)
            if resultado:
                mensagem, mensagem_cor = resultado
                mensagem_tempo = 0
        
        # Desenhar botão de voltar (ajustado para ficar mais abaixo)
        botao_voltar_largura = 240
        botao_voltar_altura = 50
        botao_voltar_x = LARGURA // 2
        botao_voltar_y = ALTURA - 50  # Ajustado de 80 para 50 (mais próximo do fundo)
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
        texto_voltar = pygame.font.SysFont("Arial", 26).render("BACK TO MENU (ESC)", True, BRANCO)
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
                pygame.display.flip()
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