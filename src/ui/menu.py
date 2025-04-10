#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções para gerenciar as telas de menu, início de jogo e fim de jogo.
"""

import pygame
import random
import math
import sys
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.utils.sound import gerar_som_explosao
from src.entities.particula import criar_explosao, Particula

def tela_inicio(tela, relogio, gradiente_menu, fonte_titulo):
    """
    Exibe a tela de início do jogo.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_menu: Superfície com o gradiente de fundo do menu
        fonte_titulo: Fonte para o título
        
    Returns:
        True se o jogador escolher iniciar, False para sair
    """
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    particulas = []
    flashes = []
    tempo_ultimo_efeito = 0
    
    # Animação de título
    titulo_escala = 0
    titulo_alvo = 1.0
    
    # Loop da tela de início
    while True:
        tempo_atual = pygame.time.get_ticks()
        
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    return True  # Iniciar o jogo
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            # Verificação explícita de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:  
                clique_ocorreu = True
        
        # Adicionar efeitos visuais aleatórios
        if tempo_atual - tempo_ultimo_efeito > 2000:  # A cada 2 segundos
            tempo_ultimo_efeito = tempo_atual
            x = random.randint(100, LARGURA - 100)
            y = random.randint(100, ALTURA - 100)
            cor = random.choice([VERMELHO, AZUL, VERDE, AMARELO, ROXO, CIANO])
            flash = criar_explosao(x, y, cor, particulas, 15)
            flashes.append(flash)
            
            # Som aleatório
            pygame.mixer.Channel(0).play(pygame.mixer.Sound(gerar_som_explosao()))
        
        # Atualizar partículas
        for particula in particulas[:]:
            particula.atualizar()
            if particula.acabou():
                particulas.remove(particula)
        
        # Atualizar flashes
        for flash in flashes[:]:
            flash['vida'] -= 1
            flash['raio'] += 3
            if flash['vida'] <= 0:
                flashes.remove(flash)
        
        # Animar título
        titulo_escala += (titulo_alvo - titulo_escala) * 0.05
        
        # Desenhar fundo
        tela.blit(gradiente_menu, (0, 0))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar flashes
        for flash in flashes:
            pygame.draw.circle(tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar grid de fundo
        for i in range(0, LARGURA, 50):
            pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA), 1)
        for i in range(0, ALTURA, 50):
            pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
        
        # Desenhar título com animação
        tamanho_titulo = int(60 * titulo_escala)
        if tamanho_titulo > 10:
            desenhar_texto(tela, "QUADRADO VERSUS QUADRADO", tamanho_titulo, 
                           BRANCO, LARGURA // 2, ALTURA // 4, fonte_titulo)
            
            # Desenhar subtítulo com efeito pulsante
            pulse = (math.sin(tempo_atual / 200) + 1) * 0.5  # Valor entre 0 e 1
            cor_pulse = tuple(int(c * (0.7 + 0.3 * pulse)) for c in AZUL)
            desenhar_texto(tela, "Uma batalha épica de formas geométricas", 28, 
                           cor_pulse, LARGURA // 2, ALTURA // 4 + 70)
            
            # Adicionar subtítulo para o sistema de fases
            cor_pulse2 = tuple(int(c * (0.7 + 0.3 * pulse)) for c in VERDE)
            desenhar_texto(tela, "MODO SOBREVIVÊNCIA: Múltiplas Fases!", 26, 
                          cor_pulse2, LARGURA // 2, ALTURA // 4 + 110)
        
        # Desenhar controles
        desenhar_texto(tela, "Use as teclas WASD para mover", 24, BRANCO, LARGURA // 2, ALTURA // 2 - 50)
        desenhar_texto(tela, "Tecla ESPAÇO para atirar", 24, BRANCO, LARGURA // 2, ALTURA // 2)
        desenhar_texto(tela, "Teclas SETAS para atirar em diagonais", 24, BRANCO, LARGURA // 2, ALTURA // 2 + 50)
        
        # Desenhar informações do modo de jogo
        desenhar_texto(tela, "A cada fase, um novo inimigo aparece!", 20, AMARELO, LARGURA // 2, ALTURA // 2 + 90)
        desenhar_texto(tela, "Derrote todos os inimigos para avançar", 20, AMARELO, LARGURA // 2, ALTURA // 2 + 120)
        
        # Desenhar botões e verificar interação
        botao_jogar = criar_botao(tela, "INICIAR JOGO", LARGURA // 2, ALTURA * 3 // 4, 250, 60, 
                                 (60, 60, 180), (80, 80, 220), BRANCO)
        
        botao_sair = criar_botao(tela, "SAIR", LARGURA // 2, ALTURA * 3 // 4 + 80, 200, 50, 
                               (180, 60, 60), (220, 80, 80), BRANCO)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            mouse_pos = pygame.mouse.get_pos()
            
            # Verificar botão iniciar jogo
            rect_jogar = pygame.Rect(LARGURA // 2 - 125, ALTURA * 3 // 4 - 30, 250, 60)
            if rect_jogar.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    pygame.display.flip()
                    pygame.time.delay(20)
                return True
            
            # Verificar botão sair
            rect_sair = pygame.Rect(LARGURA // 2 - 100, ALTURA * 3 // 4 + 80 - 25, 200, 50)
            if rect_sair.collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()
        
        pygame.display.flip()
        relogio.tick(FPS)

def tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, vitoria, fase_atual):
    """
    Exibe a tela de fim de jogo (vitória ou derrota).
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_vitoria: Gradiente para tela de vitória
        gradiente_derrota: Gradiente para tela de derrota
        vitoria: True se foi vitória, False se foi derrota
        fase_atual: Número da fase em que o jogo terminou
        
    Returns:
        True para jogar novamente, False para sair
    """
    # Criar efeitos visuais
    estrelas = criar_estrelas(100)
    particulas = []
    
    # Gerar explosões iniciais
    for _ in range(10):
        x = random.randint(50, LARGURA - 50)
        y = random.randint(50, ALTURA - 50)
        cor = VERDE if vitoria else VERMELHO
        criar_explosao(x, y, cor, particulas, 10)
    
    # Som de vitória/derrota
    pygame.mixer.Channel(0).play(pygame.mixer.Sound(gerar_som_explosao()))
    
    # Animação de texto
    escala_texto = 0
    escala_alvo = 1.2
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    return True  # Jogar novamente
                if evento.key == pygame.K_ESCAPE:
                    return False  # Sair do jogo
            # Verificação explícita de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
        # Atualizar partículas
        for particula in particulas[:]:
            particula.atualizar()
            if particula.acabou():
                particulas.remove(particula)
        
        # Adicionar novas partículas ocasionalmente
        if random.random() < 0.05:
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA)
            cor = VERDE if vitoria else VERMELHO
            criar_explosao(x, y, cor, particulas, 5)
        
        # Animar texto
        escala_texto += (escala_alvo - escala_texto) * 0.05
        if escala_texto > escala_alvo - 0.05:
            escala_alvo = 1.0 if escala_alvo > 1.1 else 1.2
        
        # Desenhar fundo
        if vitoria:
            tela.blit(gradiente_vitoria, (0, 0))
        else:
            tela.blit(gradiente_derrota, (0, 0))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar texto com efeito pulsante
        tamanho_texto = int(70 * escala_texto)
        if vitoria:
            # Se completou todas as fases
            desenhar_texto(tela, "VITÓRIA TOTAL!", tamanho_texto, VERDE, LARGURA // 2, ALTURA // 3)
            desenhar_texto(tela, "Você derrotou todos os inimigos!", 30, BRANCO, LARGURA // 2, ALTURA // 3 + 80)
            desenhar_texto(tela, f"Todas as {fase_atual} fases concluídas!", 28, AMARELO, LARGURA // 2, ALTURA // 3 + 130)
        else:
            desenhar_texto(tela, "GAME OVER", tamanho_texto, VERMELHO, LARGURA // 2, ALTURA // 3)
            if fase_atual > 1:
                desenhar_texto(tela, f"Você chegou até a fase {fase_atual}", 30, BRANCO, LARGURA // 2, ALTURA // 3 + 80)
            else:
                desenhar_texto(tela, "O quadrado inimigo te derrotou!", 30, BRANCO, LARGURA // 2, ALTURA // 3 + 80)
        
        # Definir posição e tamanho dos botões 
        rect_jogar_novamente = pygame.Rect(LARGURA // 2 - 150, ALTURA // 2 + 100 - 30, 300, 60)
        rect_sair = pygame.Rect(LARGURA // 2 - 100, ALTURA // 2 + 180 - 25, 200, 50)
        
        # Desenhar botões
        hover_jogar = criar_botao(tela, "JOGAR NOVAMENTE", LARGURA // 2, ALTURA // 2 + 100, 300, 60, 
                                 (60, 120, 60), (80, 180, 80), BRANCO)
        
        hover_sair = criar_botao(tela, "SAIR", LARGURA // 2, ALTURA // 2 + 180, 200, 50, 
                               (120, 60, 60), (180, 80, 80), BRANCO)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            mouse_pos = pygame.mouse.get_pos()
            
            if rect_jogar_novamente.collidepoint(mouse_pos):
                return True
            
            if rect_sair.collidepoint(mouse_pos):
                return False
        
        pygame.display.flip()
        relogio.tick(FPS)