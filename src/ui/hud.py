#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão atualizada do arquivo src/ui/hud.py para separar o HUD da área de jogo.
"""

import pygame
import math
from src.config import LARGURA, ALTURA, LARGURA_JOGO, ALTURA_JOGO, ALTURA_HUD
from src.config import BRANCO, AMARELO, VERDE, VERMELHO, CINZA_ESCURO
from src.utils.visual import desenhar_texto

def desenhar_hud(tela, pontuacao, fase_atual, inimigos, tempo_atual, moeda_manager=None):
    """
    Desenha a interface de usuário durante o jogo.
    Agora o HUD está localizado em uma área separada abaixo da tela de jogo.
    
    Args:
        tela: Superfície onde desenhar
        pontuacao: Pontuação atual do jogador
        fase_atual: Número da fase atual
        inimigos: Lista de inimigos para contar os vivos
        tempo_atual: Tempo atual para efeitos
        moeda_manager: Gerenciador de moedas (opcional)
    """
    # Fundo da barra de HUD (área separada)
    pygame.draw.rect(tela, CINZA_ESCURO, (0, ALTURA_JOGO, LARGURA, ALTURA_HUD))
    pygame.draw.line(tela, (100, 100, 150), (0, ALTURA_JOGO), (LARGURA, ALTURA_JOGO), 2)
    
    # Calcular inimigos restantes
    inimigos_restantes = sum(1 for inimigo in inimigos if inimigo.vidas > 0)
    
    # Posições horizontais para distribuir elementos na barra de HUD
    pos_fase = LARGURA // 5
    pos_pontuacao = LARGURA // 2
    pos_inimigos = 4 * LARGURA // 5
    pos_moedas = 50  # Posição das moedas (lado esquerdo)
    
    # Posição vertical central da barra de HUD
    centro_y = ALTURA_JOGO + ALTURA_HUD // 2
    
    # Indicador de fase atual
    pygame.draw.rect(tela, (40, 80, 40), (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERDE, (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"FASE {fase_atual}", 28, VERDE, pos_fase, centro_y)
    
    # Pontuação com animação
    pulse = (math.sin(tempo_atual / 200) + 1) * 0.5  # Valor entre 0 e 1
    cor_pontuacao = tuple(int(c * (0.7 + 0.3 * pulse)) for c in AMARELO)
    pygame.draw.rect(tela, (80, 80, 40), (pos_pontuacao - 120, ALTURA_JOGO + 10, 240, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, AMARELO, (pos_pontuacao - 120, ALTURA_JOGO + 10, 240, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"Pontuação: {pontuacao}", 28, cor_pontuacao, pos_pontuacao, centro_y)
    
    # Inimigos restantes
    pygame.draw.rect(tela, (80, 40, 40), (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERMELHO, (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"Inimigos: {inimigos_restantes}", 28, VERMELHO, pos_inimigos, centro_y)
    
    # Moedas (se o gerenciador de moedas for fornecido)
    if moeda_manager:
        # Desenhar ícone de moeda
        pygame.draw.circle(tela, AMARELO, (pos_moedas - 25, centro_y), 15)
        pygame.draw.circle(tela, (200, 180, 0), (pos_moedas - 25, centro_y), 15, 2)
        
        # Brilho na moeda
        pygame.draw.circle(tela, BRANCO, (pos_moedas - 30, centro_y - 5), 5)
        
        # Contador de moedas
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 22, AMARELO, pos_moedas + 20, centro_y)

def aplicar_fade(tela, fade_in):
    """
    Aplica um efeito de fade na tela.
    
    Args:
        tela: Superfície onde aplicar o fade
        fade_in: Valor de alpha (0-255)
    """
    if fade_in > 0:
        fade = pygame.Surface((LARGURA, ALTURA))
        fade.fill((0, 0, 0))
        fade.set_alpha(fade_in)
        tela.blit(fade, (0, 0))

def desenhar_transicao_fase(tela, numero_fase, tempo_transicao, fonte_titulo, fonte_normal):
    """
    Desenha a transição entre fases.
    
    Args:
        tela: Superfície onde desenhar
        numero_fase: Número da fase que foi completada
        tempo_transicao: Contador de frames da transição (decrescente)
        fonte_titulo: Fonte para o título
        fonte_normal: Fonte para o texto normal
    """
    # Mensagem de fase completa
    alpha = min(255, (180 - tempo_transicao) * 4)
    texto_surf = fonte_titulo.render(f"FASE {numero_fase} COMPLETA!", True, VERDE)
    texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
    
    # Criar superfície para o fundo semitransparente (apenas área de jogo)
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, min(180, alpha)))
    tela.blit(overlay, (0, 0))
    
    # Ajustar transparência do texto
    texto_surf.set_alpha(alpha)
    tela.blit(texto_surf, texto_rect)
    
    # Texto adicional
    if tempo_transicao < 150:
        subtexto = fonte_normal.render("Preparando próxima fase...", True, BRANCO)
        subtexto.set_alpha(alpha)
        subtexto_rect = subtexto.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2 + 60))
        tela.blit(subtexto, subtexto_rect)

def desenhar_tela_jogo(tela, jogador, inimigos, tiros_jogador, tiros_inimigo, 
                     particulas, flashes, estrelas, gradiente_jogo, pontuacao, fase_atual, fade_in, tempo_atual, moeda_manager=None):
    """
    Desenha todo o conteúdo da tela de jogo.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        inimigos: Lista de inimigos
        tiros_jogador, tiros_inimigo: Listas de tiros
        particulas: Lista de partículas
        flashes: Lista de efeitos de flash
        estrelas: Lista de estrelas do fundo
        gradiente_jogo: Superfície do gradiente de fundo
        pontuacao: Pontuação atual
        fase_atual: Número da fase atual
        fade_in: Valor para efeito de fade (0-255)
        tempo_atual: Tempo atual em ms
        moeda_manager: Gerenciador de moedas (opcional)
    """
    # Desenhar fundo na área de jogo
    tela.blit(gradiente_jogo, (0, 0), (0, 0, LARGURA, ALTURA_JOGO))
    
    # Desenhar estrelas (apenas na área de jogo)
    for estrela in estrelas:
        x, y, tamanho, brilho, _ = estrela
        if y < ALTURA_JOGO:  # Só desenhar estrelas na área de jogo
            pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
    
    # Desenhar um grid de fundo (apenas na área de jogo)
    for i in range(0, LARGURA, 50):
        pygame.draw.line(tela, (30, 30, 50), (i, 0), (i, ALTURA_JOGO), 1)
    for i in range(0, ALTURA_JOGO, 50):
        pygame.draw.line(tela, (30, 30, 50), (0, i), (LARGURA, i), 1)
    
    # Desenhar flashes
    for flash in flashes:
        if flash['y'] < ALTURA_JOGO:  # Só desenhar flashes na área de jogo
            pygame.draw.circle(tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))
    
    # Desenhar objetos do jogo
    jogador.desenhar(tela)
    
    # Desenhar inimigos ativos
    for inimigo in inimigos:
        if inimigo.vidas > 0:
            inimigo.desenhar(tela)
    
    for tiro in tiros_jogador:
        tiro.desenhar(tela)
    
    for tiro in tiros_inimigo:
        tiro.desenhar(tela)
    
    for particula in particulas:
        particula.desenhar(tela)
    
    # Desenhar HUD (pontuação, vidas e fase) na área dedicada
    desenhar_hud(tela, pontuacao, fase_atual, inimigos, tempo_atual, moeda_manager)
    
    # Aplicar efeito de fade-in (em toda a tela)
    aplicar_fade(tela, fade_in)