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

def tela_loja(tela, relogio, gradiente_loja):
    """
    Exibe a tela da loja onde o jogador pode comprar upgrades.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_loja: Superfície com o gradiente de fundo da loja
        
    Returns:
        "menu" para voltar ao menu principal
    """
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    
    # Inicializar gerenciador de moedas para ter acesso à quantidade
    moeda_manager = MoedaManager()
    
    # Carregar upgrades
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
        
        # Atualizar mensagem de feedback
        if mensagem:
            mensagem_tempo += 1
            if mensagem_tempo >= mensagem_duracao:
                mensagem = ""
                mensagem_tempo = 0
        
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
        
        # Desenhar itens da loja
        y_pos = 250
        
        # Upgrade de vida
        desenhar_texto(tela, "Upgrade de Vida", 36, BRANCO, LARGURA // 2, y_pos)
        desenhar_texto(tela, f"+1 Vida Máxima (Atual: {upgrades['vida']})", 24, BRANCO, LARGURA // 2, y_pos + 40)
        
        # Custo e botão de compra
        custo = 50
        rect_comprar = pygame.Rect(LARGURA // 2 - 120, y_pos + 80, 240, 50)
        botao_ativo = moeda_manager.obter_quantidade() >= custo
        cor_botao = (60, 120, 60) if botao_ativo else (80, 80, 80)
        cor_hover = (80, 180, 80) if botao_ativo else (100, 100, 100)
        
        hover_comprar = criar_botao(tela, f"COMPRAR: {custo} MOEDAS", LARGURA // 2, y_pos + 100, 240, 50, 
                                  cor_botao, cor_hover, BRANCO)
        
        # Verificar clique no botão de compra
        if clique_ocorreu and rect_comprar.collidepoint(pygame.mouse.get_pos()):
            if botao_ativo:
                # Tem moedas suficientes
                moeda_manager.quantidade_moedas -= custo
                moeda_manager.salvar_moedas()
                upgrades["vida"] += 1
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                mensagem = "Upgrade de vida comprado!"
                mensagem_cor = VERDE
                mensagem_tempo = 0
            else:
                # Não tem moedas suficientes
                pygame.mixer.Channel(4).play(som_erro)
                mensagem = "Moedas insuficientes!"
                mensagem_cor = VERMELHO
                mensagem_tempo = 0
        
        # Desenhar botão de voltar
        y_voltar = ALTURA - 80
        rect_voltar = pygame.Rect(LARGURA // 2 - 120, y_voltar - 25, 240, 50)
        hover_voltar = criar_botao(tela, "VOLTAR AO MENU (ESC)", LARGURA // 2, y_voltar, 240, 50, 
                                 (60, 60, 150), (80, 80, 220), BRANCO)
        
        # Verificar clique no botão de voltar
        if clique_ocorreu and rect_voltar.collidepoint(pygame.mouse.get_pos()):
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
            y_mensagem = 180
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

def carregar_upgrades():
    """
    Carrega os upgrades salvos do arquivo.
    Se o arquivo não existir, inicia com valores padrão.
    """
    upgrades_padrao = {
        "vida": 1  # Vida máxima inicial é 1
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