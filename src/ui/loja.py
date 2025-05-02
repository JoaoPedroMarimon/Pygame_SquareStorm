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
        
        # Configurações dos painéis de itens
        painel_item_largura = 450
        painel_item_altura = 160
        espaco_entre_itens = 30
        
        # ==== ITEM 1: UPGRADE DE VIDA ====
        y_pos = 280
        
        # Desenhar painel do item
        painel_rect = pygame.Rect(LARGURA//2 - painel_item_largura//2, 
                                y_pos - painel_item_altura//2,
                                painel_item_largura, painel_item_altura)
        
        # Fundo do painel
        pygame.draw.rect(tela, (60, 20, 20), painel_rect, 0, 15)
        # Borda do painel
        pygame.draw.rect(tela, (200, 60, 60), painel_rect, 3, 15)
        
        # Título do item
        desenhar_texto(tela, "Upgrade de Vida", 32, (255, 100, 100), 
                     LARGURA // 2, y_pos - painel_item_altura//2 + 25)
        
        # Descrição do item
        desenhar_texto(tela, f"+1 Vida Máxima (Atual: {upgrades['vida']})", 22, BRANCO, 
                     LARGURA // 2, y_pos)
        
        # Desenhar ícone de coração
        coracao_x = LARGURA//2 - painel_item_largura//2 + 60
        coracao_y = y_pos
        tamanho_coracao = 30
        
        # Base do coração (dois círculos)
        pygame.draw.circle(tela, (220, 50, 50), 
                         (coracao_x - tamanho_coracao//3, coracao_y - tamanho_coracao//6), 
                         tamanho_coracao//2)
        pygame.draw.circle(tela, (220, 50, 50), 
                         (coracao_x + tamanho_coracao//3, coracao_y - tamanho_coracao//6), 
                         tamanho_coracao//2)
        
        # Triângulo para a ponta do coração
        pontos_triangulo = [
            (coracao_x - tamanho_coracao//1.5, coracao_y - tamanho_coracao//6),
            (coracao_x + tamanho_coracao//1.5, coracao_y - tamanho_coracao//6),
            (coracao_x, coracao_y + tamanho_coracao//1.2)
        ]
        pygame.draw.polygon(tela, (220, 50, 50), pontos_triangulo)
        
        # Brilho no coração
        pygame.draw.circle(tela, (255, 150, 150), 
                         (coracao_x - tamanho_coracao//4, coracao_y - tamanho_coracao//3), 
                         tamanho_coracao//6)
        
        # Custo e botão de compra
        custo = 50
        botao_largura = 240
        botao_altura = 50
        botao_x = LARGURA // 2
        botao_y = y_pos + painel_item_altura//2 - 30
        
        # Criar retângulo para o botão - IMPORTANTE: usamos as mesmas dimensões para visual e colisão
        rect_comprar = pygame.Rect(botao_x - botao_largura//2, botao_y - botao_altura//2, 
                                 botao_largura, botao_altura)
        
        botao_ativo = moeda_manager.obter_quantidade() >= custo
        cor_botao = (60, 120, 60) if botao_ativo else (80, 80, 80)
        cor_hover = (80, 180, 80) if botao_ativo else (100, 100, 100)
        
        # Verificar hover
        mouse_pos = pygame.mouse.get_pos()
        hover = rect_comprar.collidepoint(mouse_pos)
        
        # Desenhar o botão manualmente para garantir que coincida com o rect_comprar
        cor_atual = cor_hover if hover else cor_botao
        pygame.draw.rect(tela, cor_atual, rect_comprar, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_comprar, 2, 10)
        
        # Texto do botão
        fonte_botao = pygame.font.SysFont("Arial", 26)
        texto_botao = fonte_botao.render(f"{custo} MOEDAS", True, BRANCO)
        texto_rect = texto_botao.get_rect(center=(botao_x, botao_y))
        tela.blit(texto_botao, texto_rect)
        
        # ==== ITEM 2: UPGRADE DE ESPINGARDA ====
        y_pos += painel_item_altura + espaco_entre_itens
        
        # Desenhar painel da espingarda
        painel_rect = pygame.Rect(LARGURA//2 - painel_item_largura//2, 
                                y_pos - painel_item_altura//2,
                                painel_item_largura, painel_item_altura)
        
        # Fundo do painel
        pygame.draw.rect(tela, (40, 40, 60), painel_rect, 0, 15)
        # Borda do painel
        pygame.draw.rect(tela, (100, 100, 180), painel_rect, 3, 15)
        
        # Título do item
        desenhar_texto(tela, "Upgrade de Espingarda", 32, (150, 150, 255), 
                     LARGURA // 2, y_pos - painel_item_altura//2 + 25)
        
        # Descrição do item
        desenhar_texto(tela, f"Tiros por partida: {upgrades.get('espingarda', 0)}", 22, BRANCO, 
                     LARGURA // 2, y_pos)
        
        # Desenhar ícone de espingarda
        espingarda_x = LARGURA//2 - painel_item_largura//2 + 60
        espingarda_y = y_pos
        
        # Calcular ângulo para a espingarda (apontando para a direita)
        angulo_espingarda = -10  # Ligeiramente para cima
        # Converter para radianos
        angulo_rad = math.radians(angulo_espingarda)
        dx = math.cos(angulo_rad)
        dy = math.sin(angulo_rad)
        
        # Comprimento da espingarda
        comprimento_arma = 35
        
        # Posição da ponta da arma
        ponta_x = espingarda_x + dx * comprimento_arma
        ponta_y = espingarda_y + dy * comprimento_arma
        
        # Vetor perpendicular
        perp_x = -dy
        perp_y = dx
        
        # Cores
        cor_metal = (180, 180, 190)
        cor_cano = (100, 100, 110)
        cor_madeira = (120, 80, 40)
        cor_madeira_clara = (150, 100, 50)
        
        # Desenhar cano
        for i in range(4):
            offset = i - 1.5
            pygame.draw.line(tela, cor_cano, 
                           (espingarda_x + perp_x * offset, espingarda_y + perp_y * offset), 
                           (ponta_x + perp_x * offset, ponta_y + perp_y * offset), 3)
        
        # Boca do cano
        pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 5)
        pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 3)
        
        # Suporte sob o cano
        meio_cano_x = espingarda_x + dx * (comprimento_arma * 0.6)
        meio_cano_y = espingarda_y + dy * (comprimento_arma * 0.6)
        pygame.draw.line(tela, cor_metal, 
                        (meio_cano_x + perp_x * 3, meio_cano_y + perp_y * 3), 
                        (meio_cano_x - perp_x * 3, meio_cano_y - perp_y * 3), 3)
        
        # Corpo central
        corpo_x = espingarda_x + dx * 8
        corpo_y = espingarda_y + dy * 8
        pygame.draw.circle(tela, cor_metal, (int(corpo_x), int(corpo_y)), 7)
        pygame.draw.circle(tela, (50, 50, 55), (int(corpo_x), int(corpo_y)), 4)
        brilho_x = corpo_x - dx + perp_x
        brilho_y = corpo_y - dy + perp_y
        pygame.draw.circle(tela, (220, 220, 230), (int(brilho_x), int(brilho_y)), 2)
        
        # Coronha
        coronha_base_x = corpo_x - dx * 2
        coronha_base_y = corpo_y - dy * 2
        
        sup_inicio_x = coronha_base_x + perp_x * 6
        sup_inicio_y = coronha_base_y + perp_y * 6
        inf_inicio_x = coronha_base_x - perp_x * 6
        inf_inicio_y = coronha_base_y - perp_y * 6
        
        sup_fim_x = coronha_base_x - dx * 15 + perp_x * 4
        sup_fim_y = coronha_base_y - dy * 15 + perp_y * 4
        inf_fim_x = coronha_base_x - dx * 15 - perp_x * 4
        inf_fim_y = coronha_base_y - dy * 15 - perp_y * 4
        
        pygame.draw.polygon(tela, cor_madeira, [
            (sup_inicio_x, sup_inicio_y),
            (inf_inicio_x, inf_inicio_y),
            (inf_fim_x, inf_fim_y),
            (sup_fim_x, sup_fim_y)
        ])
        
        # Detalhes da coronha
        for i in range(1, 4):
            linha_x1 = sup_inicio_x - dx * (i * 3) + perp_x * (6 - i * 0.5)
            linha_y1 = sup_inicio_y - dy * (i * 3) + perp_y * (6 - i * 0.5)
            linha_x2 = inf_inicio_x - dx * (i * 3) - perp_x * (6 - i * 0.5)
            linha_y2 = inf_inicio_y - dy * (i * 3) - perp_y * (6 - i * 0.5)
            pygame.draw.line(tela, cor_madeira_clara, 
                           (linha_x1, linha_y1), 
                           (linha_x2, linha_y2), 1)
        
        # Custo e botão de compra da espingarda
        custo_espingarda = 100
        botao_espingarda_x = LARGURA // 2
        botao_espingarda_y = y_pos + painel_item_altura//2 - 30
        
        # Criar retângulo para o botão da espingarda
        rect_espingarda = pygame.Rect(botao_espingarda_x - botao_largura//2, 
                                   botao_espingarda_y - botao_altura//2,
                                   botao_largura, botao_altura)
        
        botao_espingarda_ativo = moeda_manager.obter_quantidade() >= custo_espingarda
        cor_botao_espingarda = (60, 60, 120) if botao_espingarda_ativo else (80, 80, 80)
        cor_hover_espingarda = (80, 80, 180) if botao_espingarda_ativo else (100, 100, 100)
        
        # Verificar hover para o botão da espingarda
        hover_espingarda = rect_espingarda.collidepoint(mouse_pos)
        
        # Desenhar o botão manualmente
        cor_atual_espingarda = cor_hover_espingarda if hover_espingarda else cor_botao_espingarda
        pygame.draw.rect(tela, cor_atual_espingarda, rect_espingarda, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_espingarda, 2, 10)
        
        # Texto do botão
        texto_botao_espingarda = fonte_botao.render(f"{custo_espingarda} MOEDAS", True, BRANCO)
        texto_rect_espingarda = texto_botao_espingarda.get_rect(center=(botao_espingarda_x, botao_espingarda_y))
        tela.blit(texto_botao_espingarda, texto_rect_espingarda)
        
        # Desenhar botão de voltar
        botao_voltar_x = LARGURA // 2
        botao_voltar_y = ALTURA - 80
        rect_voltar = pygame.Rect(botao_voltar_x - botao_largura//2, 
                               botao_voltar_y - botao_altura//2, 
                               botao_largura, botao_altura)
        
        # Verificar hover para o botão voltar
        hover_voltar = rect_voltar.collidepoint(mouse_pos)
        
        # Desenhar o botão voltar manualmente
        cor_voltar = (80, 80, 220) if hover_voltar else (60, 60, 150)
        pygame.draw.rect(tela, cor_voltar, rect_voltar, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_voltar, 2, 10)
        
        # Texto do botão voltar
        texto_voltar = fonte_botao.render("MENU (ESC)", True, BRANCO)
        texto_rect_voltar = texto_voltar.get_rect(center=(botao_voltar_x, botao_voltar_y))
        tela.blit(texto_voltar, texto_rect_voltar)
        
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
        
        # Verificar clique no botão de compra da espingarda
        if clique_ocorreu and rect_espingarda.collidepoint(pygame.mouse.get_pos()):
            if botao_espingarda_ativo:
                # Tem moedas suficientes
                moeda_manager.quantidade_moedas -= custo_espingarda
                moeda_manager.salvar_moedas()
                if 'espingarda' in upgrades:
                    upgrades["espingarda"] += 1
                else:
                    upgrades["espingarda"] = 1
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                mensagem = "Upgrade de espingarda comprado!"
                mensagem_cor = VERDE
                mensagem_tempo = 0
            else:
                # Não tem moedas suficientes
                pygame.mixer.Channel(4).play(som_erro)
                mensagem = "Moedas insuficientes!"
                mensagem_cor = VERMELHO
                mensagem_tempo = 0
        
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