#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão atualizada do arquivo src/ui/hud.py para incluir o sistema de inventário.
Agora mostra a arma selecionada no inventário e sua munição restante.
Inclui suporte completo ao sistema de amuleto da Combat Knife.
"""

import pygame
import math
from src.config import LARGURA, ALTURA, LARGURA_JOGO, ALTURA_JOGO, ALTURA_HUD
from src.config import BRANCO, AMARELO, VERDE, VERMELHO, CINZA_ESCURO, AZUL, ROXO, LARANJA
from src.utils.visual import desenhar_texto
from src.weapons.espingarda import desenhar_espingarda
from src.weapons.metralhadora import desenhar_metralhadora
from src.items.granada import desenhar_granada_selecionada


def desenhar_hud(tela, fase_atual, inimigos, tempo_atual, moeda_manager=None, jogador=None):
    """
    Desenha a interface de usuário durante o jogo.
    Agora inclui indicador da arma selecionada no sistema de inventário, ampulheta e amuleto.
    
    Args:
        tela: Superfície onde desenhar
        fase_atual: Número da fase atual
        inimigos: Lista de inimigos para contar os vivos
        tempo_atual: Tempo atual para efeitos
        moeda_manager: Gerenciador de moedas (opcional)
        jogador: Objeto do jogador para mostrar arma equipada (opcional)
    """
    # Fundo da barra de HUD (área separada)
    pygame.draw.rect(tela, CINZA_ESCURO, (0, ALTURA_JOGO, LARGURA, ALTURA_HUD))
    pygame.draw.line(tela, (100, 100, 150), (0, ALTURA_JOGO), (LARGURA, ALTURA_JOGO), 2)
    
    # Calcular inimigos restantes
    inimigos_restantes = sum(1 for inimigo in inimigos if inimigo.vidas > 0)
    
    # Posições horizontais para distribuir elementos na barra de HUD
    pos_moedas = LARGURA // 8        # 1/8 da largura
    pos_fase = 3 * LARGURA // 8      # 3/8 da largura  
    pos_equipamento = 5 * LARGURA // 8  # 5/8 da largura
    pos_inimigos = 7 * LARGURA // 8     # 7/8 da largura
    
    # Posição vertical central da barra de HUD
    centro_y = ALTURA_JOGO + ALTURA_HUD // 2
    
    # Indicador de moedas
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
    

    # NOVO: Indicador de arma atual baseado no sistema de inventário
    if jogador and jogador.cor == AZUL:  # Só para o jogador
        arma_ativa = "TIRO NORMAL"
        cor_fundo = (40, 40, 80)
        cor_borda = AZUL
        municao = "∞"
        cor_texto = BRANCO
        tem_arma_especial = False
        
        # Verificar qual arma está ativa baseado no novo sistema
        if hasattr(jogador, 'metralhadora_ativa') and jogador.metralhadora_ativa and hasattr(jogador, 'tiros_metralhadora') and jogador.tiros_metralhadora > 0:
            arma_ativa = "METRALHADORA"
            cor_fundo = (80, 40, 20)
            cor_borda = LARANJA
            municao = str(jogador.tiros_metralhadora)
            tem_arma_especial = True
            
        elif hasattr(jogador, 'espingarda_ativa') and jogador.espingarda_ativa and hasattr(jogador, 'tiros_espingarda') and jogador.tiros_espingarda > 0:
            arma_ativa = "ESPINGARDA"
            cor_fundo = (80, 60, 20)
            cor_borda = AMARELO
            municao = str(jogador.tiros_espingarda)
            tem_arma_especial = True
            
        elif hasattr(jogador, 'granada_selecionada') and jogador.granada_selecionada and hasattr(jogador, 'granadas') and jogador.granadas > 0:
            arma_ativa = "GRANADA"
            cor_fundo = (80, 40, 40)
            cor_borda = VERMELHO
            municao = str(jogador.granadas)
            tem_arma_especial = True
            
        # NOVO: Suporte ao amuleto da Combat Knife
        elif (hasattr(jogador, 'amuleto_ativo') and jogador.amuleto_ativo and 
              hasattr(jogador, 'facas') and jogador.facas > 0):
            arma_ativa = "AMULETO MÍSTICO"
            cor_fundo = (50, 30, 80)
            cor_borda = (200, 150, 255)
            municao = str(jogador.facas)
            tem_arma_especial = True
        
        # Desenhar fundo do indicador de arma
        pygame.draw.rect(tela, cor_fundo, (pos_equipamento - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
        pygame.draw.rect(tela, cor_borda, (pos_equipamento - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
        
        # Se tem arma especial, desenhar ícone
        if tem_arma_especial:
            # Criar uma superfície temporária para desenhar o ícone da arma
            icone_surface = pygame.Surface((60, 40), pygame.SRCALPHA)
            
            if hasattr(jogador, 'metralhadora_ativa') and jogador.metralhadora_ativa:
                # Desenhar ícone da metralhadora
                desenhar_icone_metralhadora(icone_surface, 30, 20, tempo_atual)
                
            elif hasattr(jogador, 'espingarda_ativa') and jogador.espingarda_ativa:
                # Desenhar ícone da espingarda
                desenhar_icone_espingarda(icone_surface, 30, 20, tempo_atual)
                
            elif hasattr(jogador, 'granada_selecionada') and jogador.granada_selecionada:
                # Desenhar ícone da granada
                desenhar_icone_granada(icone_surface, 30, 20)
                
            # NOVO: Ícone do amuleto
            elif hasattr(jogador, 'amuleto_ativo') and jogador.amuleto_ativo:
                # Desenhar ícone do amuleto
                desenhar_icone_amuleto_hud(icone_surface, 30, 20, tempo_atual)
            
            # Aplicar o ícone na posição correta do HUD
            tela.blit(icone_surface, (pos_equipamento - 30, centro_y - 20))
        else:
            # Desenhar ícone de tiro normal (quadrado simples)
            pygame.draw.rect(tela, AZUL, (pos_equipamento - 8, centro_y - 8, 16, 16), 0, 3)
            pygame.draw.rect(tela, BRANCO, (pos_equipamento - 8, centro_y - 8, 16, 16), 2, 3)
        
        # Texto da arma e munição
        desenhar_texto(tela, arma_ativa, 18, cor_texto, pos_equipamento, centro_y + 12)
        desenhar_texto(tela, f"Munição: {municao}", 14, cor_borda, pos_equipamento, centro_y + 28)
    
    # Ajustar posição dos inimigos baseado na presença de ampulheta
    if (jogador and hasattr(jogador, 'ampulheta_uses') and 
        (jogador.ampulheta_uses > 0 or jogador.tem_ampulheta_ativa())):
        pos_inimigos_final = 7.2 * LARGURA // 8  # Mais à direita
    else:
        pos_inimigos_final = pos_inimigos  # Posição original
    
    # Inimigos restantes
    pygame.draw.rect(tela, (80, 40, 40), (pos_inimigos_final - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 0, 10)
    pygame.draw.rect(tela, VERMELHO, (pos_inimigos_final - 100, ALTURA_JOGO + 10, 200, ALTURA_HUD - 20), 2, 10)
    desenhar_texto(tela, f"Inimigos: {inimigos_restantes}", 28, VERMELHO, pos_inimigos_final, centro_y)


def desenhar_icone_espingarda(tela, x, y, tempo_atual):
    """
    Desenha um ícone simplificado de espingarda para o HUD.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores da espingarda (menores e simplificadas)
    cor_metal = (120, 120, 130)
    cor_cano = (80, 80, 90)
    cor_madeira = (100, 70, 35)
    
    # Desenhar cano
    pygame.draw.line(tela, cor_cano, (x - 15, y), (x + 15, y), 4)
    
    # Corpo central
    pygame.draw.circle(tela, cor_metal, (x, y), 6)
    pygame.draw.circle(tela, (40, 40, 50), (x, y), 3)
    
    # Coronha
    pygame.draw.polygon(tela, cor_madeira, [
        (x - 8, y - 4),
        (x - 8, y + 4),
        (x - 20, y + 3),
        (x - 20, y - 3)
    ])
    
    # Efeito de energia
    pulso = (math.sin(tempo_atual / 150) + 1) / 2
    cor_energia = (50 + int(pulso * 100), 50 + int(pulso * 75), 200)
    pygame.draw.line(tela, cor_energia, (x - 5, y), (x + 15, y), 2)


def desenhar_icone_metralhadora(tela, x, y, tempo_atual):
    """
    Desenha um ícone simplificado de metralhadora para o HUD.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores da metralhadora
    cor_metal_escuro = (50, 50, 60)
    cor_metal_claro = (100, 100, 110)
    cor_laranja = (200, 100, 0)
    
    # Cano principal (mais grosso)
    pygame.draw.line(tela, cor_metal_escuro, (x - 12, y), (x + 18, y), 6)
    pygame.draw.line(tela, cor_metal_claro, (x - 12, y - 1), (x + 18, y - 1), 2)
    
    # Supressor na ponta
    pygame.draw.circle(tela, cor_metal_escuro, (x + 18, y), 4)
    pygame.draw.circle(tela, (30, 30, 35), (x + 18, y), 2)
    
    # Corpo retangular
    pygame.draw.rect(tela, cor_metal_escuro, (x - 6, y - 4, 12, 8))
    pygame.draw.rect(tela, cor_metal_claro, (x - 6, y - 4, 12, 8), 1)
    
    # Carregador
    pygame.draw.rect(tela, cor_metal_escuro, (x - 3, y + 4, 6, 10))
    pygame.draw.rect(tela, cor_laranja, (x - 3, y + 4, 6, 10), 1)
    
    # Coronha
    pygame.draw.line(tela, cor_metal_claro, (x - 6, y), (x - 18, y + 6), 3)
    pygame.draw.line(tela, cor_metal_claro, (x - 18, y + 6), (x - 20, y + 6), 2)
    
    # Efeito de calor
    calor_intensidade = (tempo_atual % 1000) / 1000.0
    cor_calor = (255, int(100 + calor_intensidade * 100), 0)
    
    # Pequenos pontos de calor
    if calor_intensidade > 0.5:
        pygame.draw.circle(tela, cor_calor, (x + 15, y - 2), 1)
        pygame.draw.circle(tela, cor_calor, (x + 13, y + 1), 1)


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


def desenhar_icone_amuleto_hud(tela, x, y, tempo_atual):
    """
    Desenha um ícone simplificado do amuleto para o HUD.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores místicas
    cor_base = (100, 50, 150)
    cor_brilho = (200, 150, 255)
    cor_centro = (255, 200, 100)
    
    # Animação de brilho
    intensidade = (math.sin(tempo_atual / 200) + 1) / 2
    
    # Desenhar hexágono pequeno
    pontos_hex = []
    raio = 8
    for i in range(6):
        angulo = i * math.pi / 3 + tempo_atual / 1000
        px = x + math.cos(angulo) * raio
        py = y + math.sin(angulo) * raio
        pontos_hex.append((px, py))
    
    pygame.draw.polygon(tela, cor_base, pontos_hex)
    pygame.draw.polygon(tela, cor_brilho, pontos_hex, 1)
    
    # Centro dourado
    pygame.draw.circle(tela, cor_centro, (int(x), int(y)), 4)
    pygame.draw.circle(tela, (255, 255, 200), (int(x), int(y)), 2)
    
    # Brilho pulsante
    if intensidade > 0.7:
        pygame.draw.circle(tela, cor_brilho, (int(x), int(y)), int(raio + 3), 1)
        
    # Partículas pequenas orbitando
    for i in range(2):
        part_angle = tempo_atual / 300 + i * math.pi
        part_x = x + math.cos(part_angle) * 12
        part_y = y + math.sin(part_angle) * 12
        pygame.draw.circle(tela, cor_brilho, (int(part_x), int(part_y)), 1)


def desenhar_icone_ampulheta_hud(tela, x, y, tempo_atual):
    """
    Desenha um ícone simplificado de ampulheta para o HUD (versão ativa).
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores da ampulheta (sempre no estado ativo quando chamada)
    cor_estrutura = (200, 150, 100)  # Dourado brilhante
    cor_areia = (255, 255, 100)     # Areia brilhante
    cor_brilho = (150, 200, 255)    # Brilho azul temporal
    cor_estrutura_escura = (80, 65, 45)
    
    # Tamanhos reduzidos para o HUD
    largura = 12
    altura = 16
    
    # Corpo da ampulheta (dois triângulos)
    # Triângulo superior
    pygame.draw.polygon(tela, cor_estrutura, [
        (x - largura//2, y - altura//2),  # topo esquerdo
        (x + largura//2, y - altura//2),  # topo direito
        (x, y)  # centro
    ])
    
    # Triângulo inferior  
    pygame.draw.polygon(tela, cor_estrutura, [
        (x, y),  # centro
        (x - largura//2, y + altura//2),  # base esquerda
        (x + largura//2, y + altura//2)   # base direita
    ])
    
    # Bordas
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x - largura//2, y - altura//2),
        (x + largura//2, y - altura//2),
        (x, y)
    ], 1)
    
    pygame.draw.polygon(tela, cor_estrutura_escura, [
        (x, y),
        (x - largura//2, y + altura//2),
        (x + largura//2, y + altura//2)
    ], 1)
    
    # Areia flutuando no meio (efeito ativo)
    for i in range(2):
        areia_y = y + (i - 0.5) * 2
        pygame.draw.circle(tela, cor_areia, (x, int(areia_y)), 1)
    
    # Suportes (topo e base)
    pygame.draw.rect(tela, cor_estrutura_escura, 
                    (x - largura//2 - 1, y - altura//2 - 2, largura + 2, 2))
    pygame.draw.rect(tela, cor_estrutura_escura, 
                    (x - largura//2 - 1, y + altura//2, largura + 2, 2))
    
    # Efeito de brilho pulsante
    pulso = (math.sin(tempo_atual / 150) + 1) / 2
    if pulso > 0.5:
        # Brilho ao redor
        pygame.draw.circle(tela, cor_brilho, (x, y), largura, 1)


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
    
    # Desenhar HUD atualizado com sistema de inventário
    desenhar_hud(tela, fase_atual, inimigos, tempo_atual, moeda_manager, jogador)
    
    # Aplicar efeito de fade-in (em toda a tela)
    aplicar_fade(tela, fade_in)