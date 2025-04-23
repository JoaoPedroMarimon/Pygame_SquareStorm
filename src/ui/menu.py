#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções para gerenciar as telas de menu, início de jogo e fim de jogo.
"""
from src.game.moeda_manager import MoedaManager
import random
import math
import sys
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.utils.sound import gerar_som_explosao
from src.entities.particula import criar_explosao, Particula
import pygame

# Modificar a função tela_inicio para incluir o botão da loja:

def tela_inicio(tela, relogio, gradiente_menu, fonte_titulo):
    """
    Exibe a tela de início do jogo.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_menu: Superfície com o gradiente de fundo do menu
        fonte_titulo: Fonte para o título
        
    Returns:
        "jogar" para iniciar o jogo
        "loja" para ir para a loja
        False para sair
    """
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    particulas = []
    flashes = []
    tempo_ultimo_efeito = 0
    
    # Animação de título
    titulo_escala = 0
    titulo_alvo = 1.0
    
    # Inicializar moeda_manager para mostrar quantidade de moedas
    moeda_manager = MoedaManager()
    
    # Loop principal
    while True:
        tempo_atual = pygame.time.get_ticks()
        
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    return "jogar"  # Iniciar o jogo
                if evento.key == pygame.K_l:
                    return "loja"  # Ir para a loja
                if evento.key == pygame.K_ESCAPE:
                    return False  # Sair do jogo
            # Verificação explícita de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:  # Botão esquerdo do mouse
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
        
        # Atualizar partículas - Parte importante corrigida
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
        
        # Atualizar estrelas
        for estrela in estrelas:
            estrela[0] -= estrela[4]  # Mover com base na velocidade
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        
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
        
        # Mostrar quantidade de moedas
        cor_moeda = AMARELO
        pygame.draw.circle(tela, cor_moeda, (30, 30), 10)  # Ícone de moeda
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 20, cor_moeda, 60, 30)
        
        # Desenhar controles
        desenhar_texto(tela, "Use as teclas WASD para mover", 24, BRANCO, LARGURA // 2, ALTURA // 2 - 50)
        desenhar_texto(tela, "Teclas SETAS para atirar em todas direções", 24, BRANCO, LARGURA // 2, ALTURA // 2)
        
        # Desenhar botões e verificar interação - AGORA COM TRÊS BOTÕES
        
        # 1. Botão de Jogar (aumentado para acomodar o texto)
        rect_jogar = pygame.Rect(LARGURA // 2 - 150, ALTURA * 3 // 4 - 60, 300, 60)
        botao_jogar = criar_botao(tela, "JOGAR (ENTER)", LARGURA // 2, ALTURA * 3 // 4 - 60, 300, 60, 
                                 (60, 60, 180), (80, 80, 220), BRANCO)
        
        # 2. Botão da Loja (aumentado para acomodar o texto)
        rect_loja = pygame.Rect(LARGURA // 2 - 150, ALTURA * 3 // 4 + 20, 300, 60)
        botao_loja = criar_botao(tela, "LOJA (L)", LARGURA // 2, ALTURA * 3 // 4 + 20, 300, 60, 
                                (120, 60, 180), (150, 80, 220), BRANCO)
        
        # 3. Botão de Sair
        rect_sair = pygame.Rect(LARGURA // 2 - 100, ALTURA * 3 // 4 + 100, 200, 50)
        botao_sair = criar_botao(tela, "SAIR (ESC)", LARGURA // 2, ALTURA * 3 // 4 + 100, 200, 50, 
                               (180, 60, 60), (220, 80, 80), BRANCO)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            mouse_pos = pygame.mouse.get_pos()
            
            # Verificar botão iniciar jogo
            if rect_jogar.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    pygame.display.flip()
                    pygame.time.delay(20)
                return "jogar"
            
            # Verificar botão da loja
            if rect_loja.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    pygame.display.flip()
                    pygame.time.delay(20)
                return "loja"
            
            # Verificar botão sair
            if rect_sair.collidepoint(mouse_pos):
                return False
        
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

# Modificação na função tela_vitoria_fase para adicionar atalhos de teclado:

def tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual, pontuacao):
    """
    Exibe uma tela de vitória após completar uma fase, com opções para continuar ou voltar ao menu.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_vitoria: Superfície com o gradiente de fundo da vitória
        fase_atual: Número da fase que acabou de ser completada
        pontuacao: Pontuação atual do jogador
        
    Returns:
        "proximo" para avançar à próxima fase
        "menu" para voltar ao menu principal
        "sair" para sair do jogo
    """
    # Criar efeitos visuais
    estrelas = criar_estrelas(100)
    particulas = []
    
    # Gerar explosões de celebração
    for _ in range(8):
        x = random.randint(50, LARGURA - 50)
        y = random.randint(50, ALTURA - 50)
        criar_explosao(x, y, VERDE, particulas, 10)
    
    # Som de vitória
    pygame.mixer.Channel(0).play(pygame.mixer.Sound(gerar_som_explosao()))
    
    # Animação de texto
    escala_texto = 0
    escala_alvo = 1.2
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"
            if evento.type == pygame.KEYDOWN:
                # Tecla Enter ou Espaço para próxima fase
                if evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE:
                    return "proximo"  # Avançar para próxima fase
                
                # Tecla Backspace ou M para menu
                if evento.key == pygame.K_BACKSPACE or evento.key == pygame.K_m:
                    return "menu"  # Voltar ao menu
                
                # Tecla ESC para sair
                if evento.key == pygame.K_ESCAPE:
                    return "sair"  # Sair do jogo
                
            # Verificação de clique do mouse
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
            criar_explosao(x, y, VERDE, particulas, 5)
        
        # Animar texto
        escala_texto += (escala_alvo - escala_texto) * 0.05
        if escala_texto > escala_alvo - 0.05:
            escala_alvo = 1.0 if escala_alvo > 1.1 else 1.2
        
        # Desenhar fundo
        tela.blit(gradiente_vitoria, (0, 0))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar texto com efeito pulsante
        tamanho_texto = int(70 * escala_texto)
        desenhar_texto(tela, f"FASE {fase_atual} COMPLETA!", tamanho_texto, VERDE, LARGURA // 2, ALTURA // 3)
        
        # Mostrar número de inimigos derrotados e pontuação
        desenhar_texto(tela, f"Inimigos derrotados: {fase_atual if fase_atual < 3 else 1}", 30, 
                      BRANCO, LARGURA // 2, ALTURA // 3 + 80)
        desenhar_texto(tela, f"Pontuação: {pontuacao}", 30, AMARELO, LARGURA // 2, ALTURA // 3 + 130)
        
        # Desenhar botão para próxima fase (com indicação de tecla)
        rect_proximo = pygame.Rect(LARGURA // 2 - 150, ALTURA // 2 + 50, 300, 60)
        hover_proximo = criar_botao(tela, "PRÓXIMA FASE (ENTER)", LARGURA // 2, ALTURA // 2 + 50, 300, 60, 
                                  (60, 120, 60), (80, 180, 80), BRANCO)
        
        # Desenhar botão para voltar ao menu (com indicação de tecla)
        rect_menu = pygame.Rect(LARGURA // 2 - 150, ALTURA // 2 + 130, 300, 60)
        hover_menu = criar_botao(tela, "VOLTAR AO MENU (M)", LARGURA // 2, ALTURA // 2 + 130, 300, 60, 
                              (60, 60, 150), (80, 80, 200), BRANCO)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            mouse_pos = pygame.mouse.get_pos()
            
            if rect_proximo.collidepoint(mouse_pos):
                return "proximo"
            
            if rect_menu.collidepoint(mouse_pos):
                return "menu"
        
        pygame.display.flip()
        relogio.tick(FPS)