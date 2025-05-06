#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão atualizada do arquivo src/ui/hud.py para separar o HUD da área de jogo.
"""

import pygame
import math
from src.config import LARGURA, ALTURA, LARGURA_JOGO, ALTURA_JOGO, ALTURA_HUD
from src.config import BRANCO, AMARELO, VERDE, VERMELHO, CINZA_ESCURO, AZUL, ROXO
from src.utils.visual import desenhar_texto

def desenhar_hud(tela, fase_atual, inimigos, tempo_atual, moeda_manager=None):
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
    pos_inimigos = 4 * LARGURA // 5
    pos_moedas = 50  # Posição das moedas (lado esquerdo)
    
    # Posição vertical central da barra de HUD
    centro_y = ALTURA_JOGO + ALTURA_HUD // 2
    
    # Indicador de fase atual
    pygame.draw.rect(tela, (40, 80, 40), (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERDE, (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"FASE {fase_atual}", 28, VERDE, pos_fase, centro_y)
    

    
    # Inimigos restantes
    pygame.draw.rect(tela, (80, 40, 40), (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERMELHO, (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"Inimigos: {inimigos_restantes}", 28, VERMELHO, pos_inimigos, centro_y)
    
    # Moedas (se o gerenciador de moedas for fornecido)
# Adicionar ao desenhar_hud em src/ui/hud.py
# Se o jogador tem espingarda, mostrar status
# Se inimigos for uma lista e o jogador estiver nela:
    if moeda_manager:  # Certifique-se que o manager existe
        # Posição para o indicador de espingarda
        pos_espingarda = LARGURA - 200
        
        # Encontrar o jogador na lista de inimigos (se for uma lista)
        jogador = None
        if isinstance(inimigos, list):
            for obj in inimigos:
                if hasattr(obj, 'cor') and obj.cor == AZUL:
                    jogador = obj
                    break
        else:
            # Se inimigos já for o jogador
            jogador = inimigos
        
        if jogador and hasattr(jogador, 'tiros_espingarda') and jogador.tiros_espingarda > 0:
            # Desenhar fundo para o indicador de espingarda
            pygame.draw.rect(tela, (60, 60, 80), 
                        (pos_espingarda - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 0, 10)
            pygame.draw.rect(tela, ROXO, 
                        (pos_espingarda - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 2, 10)
            
            # Texto informativo
            texto_espingarda = f"E: ESPINGARDA ({jogador.tiros_espingarda})"
            if hasattr(jogador, 'espingarda_ativa') and jogador.espingarda_ativa:
                texto_espingarda = f"ESPINGARDA ATIVA! ({jogador.tiros_espingarda})"
                cor_texto = VERDE
            else:
                cor_texto = BRANCO
                
            desenhar_texto(tela, texto_espingarda, 22, cor_texto, pos_espingarda, centro_y)

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
                     particulas, flashes, estrelas, gradiente_jogo,fase_atual, fade_in, tempo_atual, moeda_manager=None):
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
    if jogador.vidas > 0:
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
    desenhar_hud(tela,  fase_atual, inimigos, tempo_atual, moeda_manager)
    
    # Aplicar efeito de fade-in (em toda a tela)
    aplicar_fade(tela, fade_in)