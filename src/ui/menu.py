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
from ..utils.progress import ProgressManager

import pygame

# Modificar a função tela_inicio para incluir o botão da loja:

def tela_inicio(tela, relogio, gradiente_menu, fonte_titulo):
    """
    Exibe a tela de início do jogo SquareStorm.
    """
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    particulas = []
    flashes = []
    tempo_ultimo_efeito = 0
    
    # Animação de título
    titulo_escala = 0
    titulo_alvo = 1.0
    titulo_y = ALTURA // 5  # Posição Y inicial do título
    subtitulo_alpha = 0
    
    # Efeito de névoa colorida
    nevoa_offset = 0
    
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
                    return "jogar"
                if evento.key == pygame.K_l:
                    return "loja"
                if evento.key == pygame.K_ESCAPE:
                    return False
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
        # Adicionar efeitos visuais aleatórios
        if tempo_atual - tempo_ultimo_efeito > 1500:
            tempo_ultimo_efeito = tempo_atual
            x = random.randint(100, LARGURA - 100)
            y = random.randint(100, ALTURA - 100)
            cor = random.choice([AZUL, CIANO, ROXO])
            flash = criar_explosao(x, y, cor, particulas, 12)
            flashes.append(flash)
            
            # Som suave
            som = pygame.mixer.Sound(gerar_som_explosao())
            som.set_volume(0.3)
            pygame.mixer.Channel(0).play(som)
        
        # Atualizar partículas e flashes
        for particula in particulas[:]:
            particula.atualizar()
            if particula.acabou():
                particulas.remove(particula)
        
        for flash in flashes[:]:
            flash['vida'] -= 1
            flash['raio'] += 3
            if flash['vida'] <= 0:
                flashes.remove(flash)
        
        # Atualizar estrelas
        for estrela in estrelas:
            estrela[0] -= estrela[4]
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        
        # Animar título
        titulo_escala += (titulo_alvo - titulo_escala) * 0.05
        subtitulo_alpha = min(255, subtitulo_alpha + 3)
        nevoa_offset = (nevoa_offset + 1) % 360
        
        # Desenhar fundo
        tela.blit(gradiente_menu, (0, 0))
        
        # Desenhar névoa colorida ondulante
        for y in range(0, ALTURA, 20):
            wave_offset = math.sin((y + nevoa_offset) / 30) * 10
            alpha = int(20 + 15 * math.sin((y + nevoa_offset) / 50))
            linha_surf = pygame.Surface((LARGURA, 2), pygame.SRCALPHA)
            linha_surf.fill((100, 200, 255, alpha))
            tela.blit(linha_surf, (wave_offset, y))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar flashes
        for flash in flashes:
            pygame.draw.circle(tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar grid sutil
        for i in range(0, LARGURA, 60):
            pygame.draw.line(tela, (30, 30, 60, 100), (i, 0), (i, ALTURA), 1)
        for i in range(0, ALTURA, 60):
            pygame.draw.line(tela, (30, 30, 60, 100), (0, i), (LARGURA, i), 1)
        
        # Desenhar título SquareStorm com efeito metálico
        tamanho_titulo = int(90 * titulo_escala)
        if tamanho_titulo > 10:
            # Sombra profunda
            desenhar_texto(tela, "SQUARESTORM", tamanho_titulo, (0, 0, 50), 
                         LARGURA // 2 + 4, titulo_y + 4, fonte_titulo)
            
            # Contorno
            desenhar_texto(tela, "SQUARESTORM", tamanho_titulo, (100, 150, 255), 
                         LARGURA // 2 + 2, titulo_y + 2, fonte_titulo)
            
            # Texto principal com brilho pulsante
            pulse = (math.sin(tempo_atual / 500) + 1) * 0.5
            cor_principal = tuple(int(c * (0.8 + 0.2 * pulse)) for c in BRANCO)
            desenhar_texto(tela, "SQUARESTORM", tamanho_titulo, cor_principal, 
                         LARGURA // 2, titulo_y, fonte_titulo)
            
            # Subtítulo estilizado
            subtitulo_surf = fonte_titulo.render("THE GEOMETRY BATTLE ARENA", True, CIANO)
            subtitulo_surf.set_alpha(subtitulo_alpha)
            subtitulo_rect = subtitulo_surf.get_rect(center=(LARGURA // 2, titulo_y + 90))
            tela.blit(subtitulo_surf, subtitulo_rect)
        
        # Exibir quantidade de moedas com estilo
        moeda_size = 12
        pygame.draw.circle(tela, AMARELO, (30, 30), moeda_size)
        pygame.draw.circle(tela, (255, 215, 0), (30, 30), moeda_size - 2)
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 24, AMARELO, 60, 30)
        
        # Controles com design mais clean
        controles_y = ALTURA // 2 + 20
        fonte_controles = pygame.font.SysFont("Arial", 22, False)
        
        # Icones de teclas
        # WASD
        pygame.draw.rect(tela, (50, 50, 80), (LARGURA//2 - 80, controles_y - 40, 30, 30), 0, 3)
        desenhar_texto(tela, "W", 18, BRANCO, LARGURA//2 - 65, controles_y - 25)
        
        pygame.draw.rect(tela, (50, 50, 80), (LARGURA//2 - 115, controles_y - 5, 30, 30), 0, 3)
        desenhar_texto(tela, "A", 18, BRANCO, LARGURA//2 - 100, controles_y + 10)
        
        pygame.draw.rect(tela, (50, 50, 80), (LARGURA//2 - 80, controles_y - 5, 30, 30), 0, 3)
        desenhar_texto(tela, "S", 18, BRANCO, LARGURA//2 - 65, controles_y + 10)
        
        pygame.draw.rect(tela, (50, 50, 80), (LARGURA//2 - 45, controles_y - 5, 30, 30), 0, 3)
        desenhar_texto(tela, "D", 18, BRANCO, LARGURA//2 - 30, controles_y + 10)
        
        # Texto de movimento
        desenhar_texto(tela, "Mover", 20, BRANCO, LARGURA//2 - 80, controles_y + 40)
        
        # Mouse (versão mais detalhada)
        mouse_x = LARGURA//2 + 70
        mouse_y = controles_y
        
        # Sombra do mouse
        pygame.draw.ellipse(tela, (20, 20, 40), (mouse_x - 14, mouse_y + 10, 28, 8))
        
        # Corpo do mouse
        pygame.draw.rect(tela, (80, 80, 120), (mouse_x - 12, mouse_y - 18, 24, 30), 0, 12)
        
        # Brilho no corpo
        pygame.draw.rect(tela, (120, 120, 160), (mouse_x - 8, mouse_y - 16, 4, 20), 0, 4)
        
        # Divisão dos botões
        pygame.draw.line(tela, (50, 50, 70), (mouse_x, mouse_y - 18), (mouse_x, mouse_y - 3), 2)
        
        # Botão esquerdo (destacado para indicar que é o botão de atirar)
        pygame.draw.rect(tela, (200, 50, 50), (mouse_x - 12, mouse_y - 18, 12, 12), 0, 8)
        pygame.draw.rect(tela, (255, 80, 80), (mouse_x - 10, mouse_y - 16, 8, 8), 0, 4)
        
        # Scroll wheel
        pygame.draw.rect(tela, (200, 200, 220), (mouse_x - 3, mouse_y - 13, 6, 8), 0, 3)
        pygame.draw.line(tela, (150, 150, 170), (mouse_x, mouse_y - 11), (mouse_x, mouse_y - 7), 1)
        
        # Indicador de clique (animado)
        if tempo_atual % 1000 < 500:  # Pisca a cada 0.5 segundos
            pygame.draw.circle(tela, (255, 50, 50), (mouse_x - 6, mouse_y - 12), 3)
        
        # Texto de atirar
        desenhar_texto(tela, "Atirar", 20, BRANCO, LARGURA//2 + 70, controles_y + 40)
        
        # Ajustar dimensões para a resolução atual
        escala_y = ALTURA / 848
        
        # Definir botões estilizados
        largura_botao = 320
        altura_botao = 65
        espacamento = 85
        y_inicial = ALTURA * 3 // 4 - 40
        
        # Botão Jogar
        x_jogar = LARGURA // 2
        y_jogar = y_inicial
        largura_ajustada_jogar = int(largura_botao * escala_y)
        altura_ajustada_jogar = int(altura_botao * escala_y)
        rect_jogar = pygame.Rect(x_jogar - largura_ajustada_jogar // 2, 
                                y_jogar - altura_ajustada_jogar // 2, 
                                largura_ajustada_jogar, 
                                altura_ajustada_jogar)
        
        # Botão Loja
        x_loja = LARGURA // 2
        y_loja = y_inicial + espacamento
        largura_ajustada_loja = int(largura_botao * escala_y)
        altura_ajustada_loja = int(altura_botao * escala_y)
        rect_loja = pygame.Rect(x_loja - largura_ajustada_loja // 2, 
                               y_loja - altura_ajustada_loja // 2, 
                               largura_ajustada_loja, 
                               altura_ajustada_loja)
        
        # Botão Sair
        x_sair = LARGURA // 2
        y_sair = y_inicial + espacamento * 2
        largura_ajustada_sair = int(largura_botao * 0.7 * escala_y)  # Botão menor
        altura_ajustada_sair = int(altura_botao * 0.8 * escala_y)
        rect_sair = pygame.Rect(x_sair - largura_ajustada_sair // 2, 
                               y_sair - altura_ajustada_sair // 2, 
                               largura_ajustada_sair, 
                               altura_ajustada_sair)
        
        # Botão de Seleção de Fase
        largura_selecao = 100  # Aumentado de 60 para 100
        altura_selecao = 50   # Ajustado de 60 para 50 para ficar mais retangular
        x_selecao = LARGURA - 80  # Canto direito da tela
        y_selecao = 80  # Canto superior
        largura_ajustada_selecao = int(largura_selecao * escala_y)
        altura_ajustada_selecao = int(altura_selecao * escala_y)
        rect_selecao = pygame.Rect(x_selecao - largura_ajustada_selecao // 2, 
                                y_selecao - altura_ajustada_selecao // 2, 
                                largura_ajustada_selecao, 
                                altura_ajustada_selecao)
                
        # Desenhar botões com novo estilo
        botao_jogar = criar_botao(tela, "PLAY GAME", x_jogar, y_jogar, largura_botao, altura_botao, 
                                 (0, 100, 200), (0, 150, 255), BRANCO)
        
        botao_loja = criar_botao(tela, "SHOP", x_loja, y_loja, largura_botao, altura_botao, 
                                (150, 100, 0), (255, 180, 0), BRANCO)
        
        botao_sair = criar_botao(tela, "EXIT", x_sair, y_sair, largura_botao * 0.7, altura_botao * 0.8, 
                               (150, 50, 50), (200, 80, 80), BRANCO)
        
        # Desenhar botão de seleção de fase com ícone de menu
        mouse_pos = pygame.mouse.get_pos()
        hover_selecao = rect_selecao.collidepoint(mouse_pos)
        cor_botao_selecao = (70, 70, 200) if hover_selecao else (50, 50, 150)
        pygame.draw.rect(tela, cor_botao_selecao, rect_selecao, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_selecao, 2, 10)

        # Desenhar texto "LEVELS" no botão
        fonte_levels = pygame.font.SysFont("Arial", 18, True)
        texto_levels = fonte_levels.render("LEVELS", True, BRANCO)
        texto_rect = texto_levels.get_rect(center=rect_selecao.center)
        tela.blit(texto_levels, texto_rect)
        
        # Desenhar ícone de menu (três linhas)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            if rect_jogar.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    pygame.display.flip()
                    pygame.time.delay(20)
                return "jogar"
            
            if rect_loja.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    pygame.display.flip()
                    pygame.time.delay(20)
                return "loja"
            
            if rect_sair.collidepoint(mouse_pos):
                return False
            
            if rect_selecao.collidepoint(mouse_pos):
                return "selecao_fase"
        
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
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
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
        
        # Ajustar dimensões para a resolução atual
        escala_y = ALTURA / 848
        
        # Definir posição e tamanho do botão JOGAR NOVAMENTE (centralizado)
        largura_jogar_novamente = 300
        altura_jogar_novamente = 60
        x_jogar_novamente = LARGURA // 2
        y_jogar_novamente = ALTURA // 2 + 140  # Ajustado para ficar mais centralizado
        largura_ajustada_jogar = int(largura_jogar_novamente * escala_y)
        altura_ajustada_jogar = int(altura_jogar_novamente * escala_y)
        rect_jogar_novamente = pygame.Rect(x_jogar_novamente - largura_ajustada_jogar // 2, 
                                         y_jogar_novamente - altura_ajustada_jogar // 2, 
                                         largura_ajustada_jogar, 
                                         altura_ajustada_jogar)
        
        # Desenhar apenas o botão JOGAR NOVAMENTE
        hover_jogar = criar_botao(tela, "MENU", x_jogar_novamente, y_jogar_novamente, 
                                 largura_jogar_novamente, altura_jogar_novamente, 
                                 (60, 120, 60), (80, 180, 80), BRANCO)
        
        # Verificar cliques no botão
        if clique_ocorreu:
            mouse_pos = pygame.mouse.get_pos()
            
            if rect_jogar_novamente.collidepoint(mouse_pos):
                return True
        
        pygame.display.flip()
        relogio.tick(FPS)
def tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual):
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
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
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
        
        
        # Ajustar dimensões para a resolução atual
        escala_y = ALTURA / 848
        
        # Desenhar botão para próxima fase
        largura_proximo = 300
        altura_proximo = 60
        x_proximo = LARGURA // 2
        y_proximo = ALTURA // 2 + 50
        largura_ajustada_proximo = int(largura_proximo * escala_y)
        altura_ajustada_proximo = int(altura_proximo * escala_y)
        rect_proximo = pygame.Rect(x_proximo - largura_ajustada_proximo // 2, 
                                  y_proximo - altura_ajustada_proximo // 2, 
                                  largura_ajustada_proximo, 
                                  altura_ajustada_proximo)
        
        # Desenhar botão para voltar ao menu
        largura_menu = 300
        altura_menu = 60
        x_menu = LARGURA // 2
        y_menu = ALTURA // 2 + 130
        largura_ajustada_menu = int(largura_menu * escala_y)
        altura_ajustada_menu = int(altura_menu * escala_y)
        rect_menu = pygame.Rect(x_menu - largura_ajustada_menu // 2, 
                               y_menu - altura_ajustada_menu // 2, 
                               largura_ajustada_menu, 
                               altura_ajustada_menu)
        
        # Desenhar os botões
        hover_proximo = criar_botao(tela, "PRÓXIMA FASE (ENTER)", x_proximo, y_proximo, 
                                  largura_proximo, altura_proximo, 
                                  (60, 120, 60), (80, 180, 80), BRANCO)
        
        hover_menu = criar_botao(tela, "VOLTAR AO MENU (M)", x_menu, y_menu, 
                              largura_menu, altura_menu, 
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