#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão atualizada do arquivo src/ui/hud.py para separar o HUD da área de jogo.
Agora inclui indicador visual da arma/item equipado entre "FASE" e "INIMIGOS".
"""

import pygame
import math
from src.config import LARGURA, ALTURA, LARGURA_JOGO, ALTURA_JOGO, ALTURA_HUD
from src.config import BRANCO, AMARELO, VERDE, VERMELHO, CINZA_ESCURO, AZUL, ROXO
from src.utils.visual import desenhar_texto
from src.weapons.espingarda import desenhar_espingarda
from src.items.granada import desenhar_granada_selecionada


def desenhar_hud(tela, fase_atual, inimigos, tempo_atual, moeda_manager=None, jogador=None):
    """
    Desenha a interface de usuário durante o jogo.
    Agora o HUD está localizado em uma área separada abaixo da tela de jogo.
    
    Args:
        tela: Superfície onde desenhar
        fase_atual: Número da fase atual
        inimigos: Lista de inimigos para contar os vivos
        tempo_atual: Tempo atual para efeitos
        moeda_manager: Gerenciador de moedas (opcional)
        jogador: Objeto do jogador para mostrar arma/item equipado (opcional)
    """
    # Fundo da barra de HUD (área separada)
    pygame.draw.rect(tela, CINZA_ESCURO, (0, ALTURA_JOGO, LARGURA, ALTURA_HUD))
    pygame.draw.line(tela, (100, 100, 150), (0, ALTURA_JOGO), (LARGURA, ALTURA_JOGO), 2)
    
    # Calcular inimigos restantes
    inimigos_restantes = sum(1 for inimigo in inimigos if inimigo.vidas > 0)
    
    # Posições horizontais para distribuir elementos na barra de HUD
    # Agora com 4 elementos: moedas, fase, equipamento, inimigos
    pos_moedas = LARGURA // 8        # 1/8 da largura
    pos_fase = 3 * LARGURA // 8      # 3/8 da largura  
    pos_equipamento = 5 * LARGURA // 8  # 5/8 da largura (novo)
    pos_inimigos = 7 * LARGURA // 8     # 7/8 da largura
    
    # Posição vertical central da barra de HUD
    centro_y = ALTURA_JOGO + ALTURA_HUD // 2
    
    # Indicador de moedas (se o gerenciador de moedas for fornecido)
    if moeda_manager:
        pygame.draw.rect(tela, (80, 80, 40), (pos_moedas - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 0, 10)
        pygame.draw.rect(tela, AMARELO, (pos_moedas - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 2, 10)
        
        # Ícone de moeda pequeno
        pygame.draw.circle(tela, AMARELO, (pos_moedas - 30, centro_y), 8)
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 24, AMARELO, pos_moedas + 20, centro_y)
    
    # Indicador de fase atual
    pygame.draw.rect(tela, (40, 80, 40), (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERDE, (pos_fase - 80, ALTURA_JOGO + 10, 160, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"FASE {fase_atual}", 28, VERDE, pos_fase, centro_y)
    
    # Indicador de equipamento (arma/item equipado) - NOVO
    if jogador:
        equipamento_ativo = False
        cor_fundo = (40, 40, 80)
        cor_borda = (80, 80, 150)
        texto_equipamento = "NENHUM"
        cor_texto = (150, 150, 150)
        
        # Verificar se tem espingarda ativa
        if hasattr(jogador, 'espingarda_ativa') and jogador.espingarda_ativa and hasattr(jogador, 'tiros_espingarda') and jogador.tiros_espingarda > 0:
            equipamento_ativo = True
            cor_fundo = (80, 40, 80)
            cor_borda = ROXO
            texto_equipamento = f"SHOTGUN ({jogador.tiros_espingarda})"
            cor_texto = BRANCO
            
        # Verificar se tem granada ativa
        elif hasattr(jogador, 'granada_selecionada') and jogador.granada_selecionada and hasattr(jogador, 'granadas') and jogador.granadas > 0:
            equipamento_ativo = True
            cor_fundo = (40, 80, 40)
            cor_borda = (100, 200, 100)
            texto_equipamento = f"GRENADE ({jogador.granadas})"
            cor_texto = BRANCO
        
        # Desenhar fundo do indicador de equipamento
        pygame.draw.rect(tela, cor_fundo, (pos_equipamento - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
        pygame.draw.rect(tela, cor_borda, (pos_equipamento - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
        
        # Se tem equipamento ativo, desenhar ícone
        if equipamento_ativo:
            # Criar uma superfície temporária para desenhar o ícone da arma/item
            icone_surface = pygame.Surface((60, 40), pygame.SRCALPHA)
            
            if hasattr(jogador, 'espingarda_ativa') and jogador.espingarda_ativa:
                # Desenhar ícone da espingarda usando a função existente
                # Criar um jogador temporário centralizado na superfície do ícone
                class JogadorTemp:
                    def __init__(self):
                        self.x = 15  # Centralizar na superfície 60x40
                        self.y = 15
                        self.tamanho = 10
                
                jogador_temp = JogadorTemp()
                
                # Simular posição do mouse para apontar para a direita
                pos_mouse = (45, 20)  # Apontar para a direita na superfície
                
                # Desenhar espingarda menor na superfície temporária
                desenhar_espingarda(icone_surface, jogador_temp, tempo_atual,pos_mouse)
                
            elif hasattr(jogador, 'granada_selecionada') and jogador.granada_selecionada:
                # Desenhar ícone da granada
                desenhar_icone_granada(icone_surface, 30, 20)
            
            # Aplicar o ícone na posição correta do HUD
            tela.blit(icone_surface, (pos_equipamento - 30, centro_y - 20))
        
        # Texto do equipamento (menor para não sobrepor o ícone)
        desenhar_texto(tela, texto_equipamento, 18, cor_texto, pos_equipamento, centro_y + 15)
    
    # Inimigos restantes
    pygame.draw.rect(tela, (80, 40, 40), (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERMELHO, (pos_inimigos - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"Inimigos: {inimigos_restantes}", 28, VERMELHO, pos_inimigos, centro_y)


def desenhar_icone_granada(tela, x, y):
    """
    Desenha um ícone simplificado de granada para o HUD.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
    """
    tamanho_granada = 8
    
    # Cor base da granada
    cor_granada = (60, 120, 60)
    cor_granada_escura = (40, 80, 40)
    
    # Corpo da granada (círculo)
    pygame.draw.circle(tela, cor_granada, (x, y), tamanho_granada)
    
    # Detalhes da granada (linhas cruzadas para textura)
    pygame.draw.line(tela, cor_granada_escura, (x - tamanho_granada + 2, y), 
                    (x + tamanho_granada - 2, y), 1)
    pygame.draw.line(tela, cor_granada_escura, (x, y - tamanho_granada + 2), 
                    (x, y + tamanho_granada - 2), 1)
    
    # Parte superior (bocal)
    pygame.draw.rect(tela, (150, 150, 150), (x - 3, y - tamanho_granada - 4, 6, 4), 0, 1)
    
    # Pino da granada
    pin_x = x + 5
    pin_y = y - tamanho_granada - 2
    
    # Anel do pino
    pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), 3, 1)

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
                     particulas, flashes, estrelas, gradiente_jogo, fase_atual, fade_in, tempo_atual, moeda_manager=None, granadas=None):
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
        fase_atual: Número da fase atual
        fade_in: Valor para efeito de fade (0-255)
        tempo_atual: Tempo atual em ms
        moeda_manager: Gerenciador de moedas (opcional)
        granadas: Lista de granadas (opcional)
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
        jogador.desenhar(tela, tempo_atual)
    
    # Desenhar inimigos ativos
    for inimigo in inimigos:
        if inimigo.vidas > 0:
            inimigo.desenhar(tela, tempo_atual)
    
    for tiro in tiros_jogador:
        tiro.desenhar(tela)
    
    for tiro in tiros_inimigo:
        tiro.desenhar(tela)
    
    # Desenhar granadas se existirem
    if granadas is not None:
        for granada in granadas:
            granada.desenhar(tela)
    
    for particula in particulas:
        particula.desenhar(tela)
    
    # Desenhar HUD (pontuação, vidas e fase) na área dedicada
    # IMPORTANTE: Agora passamos o jogador para mostrar equipamento
    desenhar_hud(tela, fase_atual, inimigos, tempo_atual, moeda_manager, jogador)
    
    # Aplicar efeito de fade-in (em toda a tela)
    aplicar_fade(tela, fade_in)