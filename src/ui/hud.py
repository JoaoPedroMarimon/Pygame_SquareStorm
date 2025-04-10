#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções para desenhar a interface do usuário durante o jogo.
"""

import pygame
import math
from src.config import LARGURA, ALTURA, BRANCO, AMARELO, VERDE, VERMELHO
from src.utils.visual import desenhar_texto

def desenhar_hud(tela, pontuacao, fase_atual, inimigos, tempo_atual):
    """
    Desenha a interface de usuário durante o jogo.
    
    Args:
        tela: Superfície onde desenhar
        pontuacao: Pontuação atual do jogador
        fase_atual: Número da fase atual
        inimigos: Lista de inimigos para contar os vivos
        tempo_atual: Tempo atual para efeitos
    """
    # Fundo do painel de status
    pygame.draw.rect(tela, (0, 0, 30), (10, 10, LARGURA - 20, 50), 0, 10)
    pygame.draw.rect(tela, (50, 50, 80), (10, 10, LARGURA - 20, 50), 2, 10)
    
    # Pontuação com animação
    pulse = (math.sin(tempo_atual / 200) + 1) * 0.5  # Valor entre 0 e 1
    cor_pontuacao = tuple(int(c * (0.7 + 0.3 * pulse)) for c in AMARELO)
    desenhar_texto(tela, f"Pontuação: {pontuacao}", 28, cor_pontuacao, LARGURA // 2, 35)
    
    # Indicador de fase atual
    desenhar_texto(tela, f"FASE {fase_atual}", 24, VERDE, LARGURA - 100, 35)
    
    # Inimigos restantes
    inimigos_restantes = sum(1 for inimigo in inimigos if inimigo.vidas > 0)
    desenhar_texto(tela, f"Inimigos: {inimigos_restantes}", 24, VERMELHO, 100, 35)

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
    texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA // 2))
    
    # Criar superfície para o fundo semitransparente
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, min(180, alpha)))
    tela.blit(overlay, (0, 0))
    
    # Ajustar transparência do texto
    texto_surf.set_alpha(alpha)
    tela.blit(texto_surf, texto_rect)
    
    # Texto adicional
    if tempo_transicao < 150:
        subtexto = fonte_normal.render("Preparando próxima fase...", True, BRANCO)
        subtexto.set_alpha(alpha)
        subtexto_rect = subtexto.get_rect(center=(LARGURA // 2, ALTURA // 2 + 60))
        tela.blit(subtexto, subtexto_rect)

def desenhar_tela_jogo(tela, jogador, inimigos, tiros_jogador, tiros_inimigo, 
                     particulas, flashes, estrelas, gradiente_jogo, pontuacao, fase_atual, fade_in, tempo_atual):
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
    """
    # Desenhar fundo
    tela.blit(gradiente_jogo, (0, 0))
    
    # Desenhar estrelas
    for estrela in estrelas:
        x, y, tamanho, brilho, _ = estrela
        pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
    
    # Desenhar um grid de fundo
    for i in range(0, LARGURA, 50):
        pygame.draw.line(tela, (30, 30, 50), (i, 0), (i, ALTURA), 1)
    for i in range(0, ALTURA, 50):
        pygame.draw.line(tela, (30, 30, 50), (0, i), (LARGURA, i), 1)
    
    # Desenhar flashes
    for flash in flashes:
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
    
    # Desenhar HUD (pontuação, vidas e fase)
    desenhar_hud(tela, pontuacao, fase_atual, inimigos, tempo_atual)
    
    # Aplicar efeito de fade-in
    aplicar_fade(tela, fade_in)