#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções para gerenciar as telas de menu, início de jogo e fim de jogo.
Versão corrigida com tela de game over simplificada.
"""
from src.game.moeda_manager import MoedaManager
import random
import math
import sys
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.utils.sound import gerar_som_explosao
from src.entities.particula import criar_explosao, Particula
from src.utils.progress import ProgressManager
from src.utils.display_manager import present_frame,convert_mouse_position
import pygame
from src.utils.visual import desenhar_grid_consistente

# IMPORTAÇÃO CORRIGIDA: agora do local correto
from src.game.inventario import tela_inventario

def tela_inicio(tela, relogio, gradiente_menu, fonte_titulo):
    """
    Exibe a tela de início do jogo SquareStorm.
    """
    
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
    # Criar efeitos visuais
    try:
        estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    except Exception as e:
        estrelas = []
    
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
    try:
        moeda_manager = MoedaManager()
    except Exception as e:
        return False
    
    # Loop principal
    frame_count = 0
    while True:
        frame_count += 1

        
        tempo_atual = pygame.time.get_ticks()
        
        clique_ocorreu = False
        
        try:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RETURN:
                        return "jogar"
                    if evento.key == pygame.K_l:
                        return "loja"
                    if evento.key == pygame.K_i:  # NOVO - tecla I para inventário
                        return "inventario"

                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    clique_ocorreu = True
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # Adicionar efeitos visuais aleatórios
        if tempo_atual - tempo_ultimo_efeito > 1500:
            tempo_ultimo_efeito = tempo_atual
            x = random.randint(100, LARGURA - 100)
            y = random.randint(100, ALTURA - 100)
            cor = random.choice([AZUL, CIANO, ROXO])
            flash = criar_explosao(x, y, cor, particulas, 12)
            flashes.append(flash)
            
            # Som suave
            try:
                som = pygame.mixer.Sound(gerar_som_explosao())
                som.set_volume(0.3)
                pygame.mixer.Channel(0).play(som)
            except:
                pass  # Ignorar erros de som
        
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
        try:
            tela.blit(gradiente_menu, (0, 0))
        except Exception as e:
            tela.fill((30, 0, 60))  # Cor de fallback
        
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
        try:
            desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 24, AMARELO, 60, 30)
        except:
            desenhar_texto(tela, "0", 24, AMARELO, 60, 30)
        
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
        
        # Botão Inventário
        x_inventario = LARGURA // 2
        y_inventario = y_inicial + espacamento * 2  # Posicionar entre Loja e Sair
        largura_ajustada_inventario = int(largura_botao * escala_y)
        altura_ajustada_inventario = int(altura_botao * escala_y)
        rect_inventario = pygame.Rect(x_inventario - largura_ajustada_inventario // 2, 
                                    y_inventario - altura_ajustada_inventario // 2, 
                                    largura_ajustada_inventario, 
                                    altura_ajustada_inventario)
        
        # Botão Sair (ajustado para baixo)
        x_sair = LARGURA // 2
        y_sair = y_inicial + espacamento * 3  # Em vez de espacamento * 2
        largura_ajustada_sair = int(largura_botao * 0.7 * escala_y)
        altura_ajustada_sair = int(altura_botao * 0.8 * escala_y)
        rect_sair = pygame.Rect(x_sair - largura_ajustada_sair // 2, 
                               y_sair - altura_ajustada_sair // 2, 
                               largura_ajustada_sair, 
                               altura_ajustada_sair)
        
        # Botão de Seleção de Fase
        largura_selecao = 100
        altura_selecao = 50
        x_selecao = LARGURA - 80
        y_selecao = 80
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
        
        botao_inventario = criar_botao(tela, "INVENTORY", x_inventario, y_inventario, largura_botao, altura_botao, 
                                      (100, 50, 150), (150, 80, 200), BRANCO)
        
        botao_sair = criar_botao(tela, "EXIT", x_sair, y_sair, largura_botao * 0.7, altura_botao * 0.8, 
                               (150, 50, 50), (200, 80, 80), BRANCO)
        
        # Desenhar botão de seleção de fase com ícone de menu
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        hover_selecao = rect_selecao.collidepoint(mouse_pos)
        cor_botao_selecao = (70, 70, 200) if hover_selecao else (50, 50, 150)
        pygame.draw.rect(tela, cor_botao_selecao, rect_selecao, 0, 10)
        pygame.draw.rect(tela, BRANCO, rect_selecao, 2, 10)

        # Desenhar texto "LEVELS" no botão
        fonte_levels = pygame.font.SysFont("Arial", 18, True)
        texto_levels = fonte_levels.render("LEVELS", True, BRANCO)
        texto_rect = texto_levels.get_rect(center=rect_selecao.center)
        tela.blit(texto_levels, texto_rect)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            if rect_jogar.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    present_frame()
                    pygame.time.delay(20)
                return "jogar"
            
            if rect_loja.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    present_frame()
                    pygame.time.delay(20)
                return "loja"
            
            if rect_inventario.collidepoint(mouse_pos):
                # Efeito de transição
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    present_frame()
                    pygame.time.delay(20)
                return "inventario"
            
            if rect_sair.collidepoint(mouse_pos):
                return False
            
            if rect_selecao.collidepoint(mouse_pos):
                return "selecao_fase"
        
        present_frame()
        relogio.tick(FPS)

def tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, vitoria, fase_atual):
    """
    Exibe a tela de fim de jogo (apenas derrota).
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_vitoria: Gradiente para tela de vitória (não usado, mantido por compatibilidade)
        gradiente_derrota: Gradiente para tela de derrota
        vitoria: Parâmetro não usado (mantido por compatibilidade)
        fase_atual: Número da fase em que o jogo terminou
        
    Returns:
        True para voltar ao menu, False para sair
    """
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(100)
    particulas = []
    flashes = []
    tempo_ultimo_efeito = 0
    
    # Gerar explosões iniciais de derrota
    for _ in range(8):
        x = random.randint(50, LARGURA - 50)
        y = random.randint(50, ALTURA - 50)
        cor = random.choice([VERMELHO, (150, 50, 50), (200, 100, 100)])
        criar_explosao(x, y, cor, particulas, 12)
    
    # Som de derrota
    som = pygame.mixer.Sound(gerar_som_explosao())
    som.set_volume(0.7)
    pygame.mixer.Channel(0).play(som)
    
    # Animação de texto
    escala_texto = 0
    escala_alvo = 1.3
    alpha_texto = 0
    shake_offset = 0
    
    # Efeito de rachadura na tela
    rachaduras = []
    for _ in range(5):
        x1, y1 = random.randint(0, LARGURA), random.randint(0, ALTURA)
        x2, y2 = random.randint(0, LARGURA), random.randint(0, ALTURA)
        rachaduras.append(((x1, y1), (x2, y2)))
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN or evento.key == pygame.K_ESCAPE:
                    return True  # Voltar ao menu

            # Verificação de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
        # Adicionar efeitos visuais aleatórios (menos frequentes)
        if tempo_atual - tempo_ultimo_efeito > 2000:
            tempo_ultimo_efeito = tempo_atual
            x = random.randint(100, LARGURA - 100)
            y = random.randint(100, ALTURA - 100)
            cor = random.choice([VERMELHO, (150, 50, 50)])
            flash = criar_explosao(x, y, cor, particulas, 8)
            flashes.append({
                'x': x, 'y': y, 'cor': cor, 
                'raio': 5, 'vida': 20
            })
        
        # Atualizar partículas
        for particula in particulas[:]:
            particula.atualizar()
            if particula.acabou():
                particulas.remove(particula)
        
        # Atualizar flashes
        for flash in flashes[:]:
            flash['vida'] -= 1
            flash['raio'] += 2
            if flash['vida'] <= 0:
                flashes.remove(flash)
        
        # Adicionar novas partículas de fumaça ocasionalmente
        if random.random() < 0.03:
            x = random.randint(0, LARGURA)
            y = random.randint(ALTURA // 2, ALTURA)
            cor = random.choice([(80, 80, 80), (60, 60, 60), (100, 50, 50)])
            criar_explosao(x, y, cor, particulas, 3)
        
        # Animar texto com tremor
        escala_texto += (escala_alvo - escala_texto) * 0.08
        alpha_texto = min(255, alpha_texto + 5)
        shake_offset = random.randint(-2, 2) if tempo_atual % 100 < 50 else 0
        
        # Pulsar escala
        if escala_texto > escala_alvo - 0.05:
            escala_alvo = 1.0 if escala_alvo > 1.2 else 1.3
        
        # Desenhar fundo
        tela.blit(gradiente_derrota, (0, 0))
        
        # Desenhar overlay escuro pulsante
        overlay_alpha = int(30 + 20 * math.sin(tempo_atual / 300))
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        tela.blit(overlay, (0, 0))
        
        # Desenhar estrelas (mais lentas)
        for estrela in estrelas:
            estrela[0] -= estrela[4] * 0.5  # Movimento mais lento
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar rachaduras na tela
        for rachadura in rachaduras:
            pygame.draw.line(tela, (100, 30, 30), rachadura[0], rachadura[1], 2)
            # Brilho da rachadura
            pygame.draw.line(tela, (150, 50, 50), rachadura[0], rachadura[1], 1)
        
        # Desenhar flashes
        for flash in flashes:
            s = pygame.Surface((flash['raio'] * 2, flash['raio'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*flash['cor'], flash['vida'] * 10), 
                             (flash['raio'], flash['raio']), flash['raio'])
            tela.blit(s, (flash['x'] - flash['raio'], flash['y'] - flash['raio']))
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar texto GAME OVER com efeito dramático
        tamanho_texto = int(80 * escala_texto)
        if tamanho_texto > 10:
            # Sombra profunda com multiple layers
            for offset in range(6, 0, -1):
                cor_sombra = (offset * 10, 0, 0)
                desenhar_texto(tela, "GAME OVER", tamanho_texto, cor_sombra, 
                             LARGURA // 2 + offset + shake_offset, 
                             ALTURA // 3 + offset)
            
            # Texto principal com brilho pulsante
            pulse = (math.sin(tempo_atual / 200) + 1) * 0.5
            cor_principal = tuple(int(c * (0.7 + 0.3 * pulse)) for c in VERMELHO)
            texto_surf = pygame.font.SysFont("Arial", tamanho_texto, True).render("GAME OVER", True, cor_principal)
            texto_surf.set_alpha(alpha_texto)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2 + shake_offset, ALTURA // 3))
            tela.blit(texto_surf, texto_rect)
            

        
        # Mensagem de fase com estilo
        if fase_atual > 1:
            msg = f"Você chegou até a fase {fase_atual}"
        else:
            msg = "O inimigo te derrotou!"
            
        msg_surf = pygame.font.SysFont("Arial", 28).render(msg, True, (200, 200, 200))
        msg_surf.set_alpha(min(200, alpha_texto - 50))
        msg_rect = msg_surf.get_rect(center=(LARGURA // 2, ALTURA // 3 + 100))
        tela.blit(msg_surf, msg_rect)
        
        # Ajustar dimensões para a resolução atual
        escala_y = ALTURA / 848
        
        # Definir posição e tamanho do botão VOLTAR AO MENU
        largura_menu = 320
        altura_menu = 65
        x_menu = LARGURA // 2
        y_menu = ALTURA // 2 + 120
        largura_ajustada = int(largura_menu * escala_y)
        altura_ajustada = int(altura_menu * escala_y)
        rect_menu = pygame.Rect(x_menu - largura_ajustada // 2, 
                               y_menu - altura_ajustada // 2, 
                               largura_ajustada, 
                               altura_ajustada)
        
        # Desenhar botão com efeito hover
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        hover = rect_menu.collidepoint(mouse_pos)
        
        # Botão com gradiente vermelho
        cor_base = (120, 40, 40) if not hover else (150, 60, 60)
        cor_borda = (180, 80, 80) if not hover else (220, 100, 100)
        
        criar_botao(tela, "VOLTAR AO MENU (ENTER)", x_menu, y_menu, 
                   largura_menu, altura_menu, cor_base, cor_borda, BRANCO)
        
        # Verificar cliques no botão
        if clique_ocorreu:
            if rect_menu.collidepoint(mouse_pos):
                # Efeito de fade out
                for i in range(20):
                    fade_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                    fade_surf.fill((0, 0, 0, i * 12))
                    tela.blit(fade_surf, (0, 0))
                    present_frame()
                    pygame.time.delay(30)
                return True
        
        present_frame()
        relogio.tick(FPS)

def tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual):
    """
    Exibe uma tela de vitória após completar uma fase, com opções para continuar ou voltar ao menu.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        gradiente_vitoria: Superfície com o gradiente de fundo da vitória
        fase_atual: Número da fase que acabou de ser completada
        
    Returns:
        "proximo" para avançar à próxima fase
        "menu" para voltar ao menu principal
        "sair" para sair do jogo
    """
    # Mostrar cursor
    pygame.mouse.set_visible(True)
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(120)
    particulas = []
    confetes = []
    tempo_ultimo_efeito = 0
    
    # Gerar explosões de celebração inicial
    for _ in range(12):
        x = random.randint(50, LARGURA - 50)
        y = random.randint(50, ALTURA - 50)
        cor = random.choice([VERDE, AMARELO, CIANO, (0, 255, 150)])
        criar_explosao(x, y, cor, particulas, 15)
    
    # Criar confetes iniciais
    for _ in range(50):
        confetes.append({
            'x': random.randint(0, LARGURA),
            'y': random.randint(-100, 0),
            'vx': random.randint(-2, 2),
            'vy': random.randint(2, 6),
            'cor': random.choice([AMARELO, VERDE, CIANO, ROXO, (255, 150, 0)]),
            'tamanho': random.randint(3, 8),
            'rotacao': random.randint(0, 360),
            'vel_rotacao': random.randint(-10, 10)
        })
    
    # Som de vitória
    som = pygame.mixer.Sound(gerar_som_explosao())
    som.set_volume(0.8)
    pygame.mixer.Channel(0).play(som)
    
    # Animação de texto
    escala_texto = 0
    escala_alvo = 1.2
    alpha_texto = 0
    brilho_offset = 0
    
    # Efeito de raios de luz
    raios = []
    for i in range(8):
        angulo = i * 45
        raios.append({
            'angulo': angulo,
            'comprimento': 0,
            'alpha': 255
        })
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"
            if evento.type == pygame.KEYDOWN:
                # Tecla Enter ou Espaço para próxima fase
                if evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE:
                    return "proximo"
                
                # Tecla Backspace ou M para menu
                if evento.key == pygame.K_BACKSPACE or evento.key == pygame.K_m:
                    return "menu"
                
            # Verificação de clique do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
        # Adicionar novos efeitos visuais periodicamente
        if tempo_atual - tempo_ultimo_efeito > 1200:
            tempo_ultimo_efeito = tempo_atual
            
            # Explosão de celebração
            x = random.randint(100, LARGURA - 100)
            y = random.randint(100, ALTURA - 100)
            cor = random.choice([VERDE, AMARELO, CIANO, (0, 255, 150)])
            criar_explosao(x, y, cor, particulas, 10)
            
            # Novos confetes
            for _ in range(10):
                confetes.append({
                    'x': random.randint(0, LARGURA),
                    'y': -20,
                    'vx': random.randint(-3, 3),
                    'vy': random.randint(3, 7),
                    'cor': random.choice([AMARELO, VERDE, CIANO, ROXO, (255, 150, 0)]),
                    'tamanho': random.randint(4, 10),
                    'rotacao': random.randint(0, 360),
                    'vel_rotacao': random.randint(-15, 15)
                })
        
        # Atualizar partículas
        for particula in particulas[:]:
            particula.atualizar()
            if particula.acabou():
                particulas.remove(particula)
        
        # Atualizar confetes
        for confete in confetes[:]:
            confete['x'] += confete['vx']
            confete['y'] += confete['vy']
            confete['vy'] += 0.2  # Gravidade
            confete['rotacao'] += confete['vel_rotacao']
            
            # Remover confetes que saíram da tela
            if confete['y'] > ALTURA + 50:
                confetes.remove(confete)
        
        # Adicionar partículas brilhantes ocasionalmente
        if random.random() < 0.08:
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA // 2)
            cor = random.choice([AMARELO, (255, 255, 150), CIANO])
            criar_explosao(x, y, cor, particulas, 4)
        
        # Animar texto
        escala_texto += (escala_alvo - escala_texto) * 0.08
        alpha_texto = min(255, alpha_texto + 6)
        brilho_offset = math.sin(tempo_atual / 300) * 20
        
        # Pulsar escala suavemente
        if escala_texto > escala_alvo - 0.05:
            escala_alvo = 1.0 if escala_alvo > 1.1 else 1.2
        
        # Atualizar raios de luz
        for raio in raios:
            raio['comprimento'] = min(200, raio['comprimento'] + 3)
            raio['angulo'] += 0.5
        
        # Desenhar fundo
        tela.blit(gradiente_vitoria, (0, 0))
        
        # Desenhar overlay dourado pulsante
        overlay_alpha = int(15 + 10 * math.sin(tempo_atual / 400))
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((255, 215, 0, overlay_alpha))
        tela.blit(overlay, (0, 0))
        
        # Desenhar raios de luz atrás do texto
        centro_x, centro_y = LARGURA // 2, ALTURA // 3
        for raio in raios:
            if raio['comprimento'] > 50:
                end_x = centro_x + math.cos(math.radians(raio['angulo'])) * raio['comprimento']
                end_y = centro_y + math.sin(math.radians(raio['angulo'])) * raio['comprimento']
                
                # Desenhar múltiplas linhas para efeito de brilho
                for width in range(5, 0, -1):
                    alpha = raio['alpha'] // width
                    cor_raio = (*AMARELO, alpha)
                    linha_surf = pygame.Surface((2, 2), pygame.SRCALPHA)
                    pygame.draw.line(linha_surf, cor_raio, (centro_x, centro_y), (end_x, end_y), width)
                    # Nota: pygame.draw.line não aceita RGBA diretamente, então usamos uma abordagem alternativa
                    pygame.draw.line(tela, AMARELO, (centro_x, centro_y), (end_x, end_y), width)
        
        # Desenhar estrelas (movimento mais rápido para celebração)
        for estrela in estrelas:
            estrela[0] -= estrela[4] * 1.5
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar confetes
        for confete in confetes:
            # Desenhar confete como um pequeno retângulo rotacionado
            surf = pygame.Surface((confete['tamanho'], confete['tamanho'] // 2), pygame.SRCALPHA)
            surf.fill(confete['cor'])
            
            # Rotacionar
            surf_rot = pygame.transform.rotate(surf, confete['rotacao'])
            rect = surf_rot.get_rect(center=(confete['x'], confete['y']))
            tela.blit(surf_rot, rect)
        
        # Desenhar partículas
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar texto principal com efeitos especiais
        tamanho_texto = int(75 * escala_texto)
        if tamanho_texto > 10:
            texto = f"FASE {fase_atual} COMPLETA!"
            
            # Sombra colorida em múltiplas camadas
            for offset in range(8, 0, -1):
                cor_sombra = (0, offset * 15, 0)
                desenhar_texto(tela, texto, tamanho_texto, cor_sombra, 
                             LARGURA // 2 + offset, ALTURA // 3 + offset)
            
            # Contorno dourado
            desenhar_texto(tela, texto, tamanho_texto, AMARELO, 
                         LARGURA // 2 + 2, ALTURA // 3 + 2)
            
            # Texto principal com brilho pulsante
            pulse = (math.sin(tempo_atual / 250) + 1) * 0.5
            cor_principal = tuple(int(c * (0.8 + 0.2 * pulse)) for c in VERDE)
            texto_surf = pygame.font.SysFont("Arial", tamanho_texto, True).render(texto, True, cor_principal)
            texto_surf.set_alpha(alpha_texto)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA // 3))
            tela.blit(texto_surf, texto_rect)
            
            # Brilho ao redor do texto
            for i in range(3):
                brilho_surf = pygame.Surface((tamanho_texto * 6, tamanho_texto), pygame.SRCALPHA)
                brilho_alpha = int(30 - i * 10 + brilho_offset)
                if brilho_alpha > 0:
                    pygame.draw.ellipse(brilho_surf, (255, 255, 150, brilho_alpha), 
                                      (0, 0, tamanho_texto * 6, tamanho_texto))
                    brilho_rect = brilho_surf.get_rect(center=(LARGURA // 2, ALTURA // 3))
                    tela.blit(brilho_surf, brilho_rect)
        
        # Mensagem de inimigos derrotados com estilo
        msg = f"Inimigos derrotados: {fase_atual if fase_atual < 3 else 1}"
        msg_surf = pygame.font.SysFont("Arial", 26, True).render(msg, True, CIANO)
        msg_surf.set_alpha(min(220, alpha_texto - 30))
        msg_rect = msg_surf.get_rect(center=(LARGURA // 2, ALTURA // 3 + 90))
        tela.blit(msg_surf, msg_rect)
        
        # Ajustar dimensões para a resolução atual
        escala_y = ALTURA / 848
        
        # Desenhar botão para próxima fase
        largura_proximo = 320
        altura_proximo = 65
        x_proximo = LARGURA // 2
        y_proximo = ALTURA // 2 + 60
        largura_ajustada_proximo = int(largura_proximo * escala_y)
        altura_ajustada_proximo = int(altura_proximo * escala_y)
        rect_proximo = pygame.Rect(x_proximo - largura_ajustada_proximo // 2, 
                                  y_proximo - altura_ajustada_proximo // 2, 
                                  largura_ajustada_proximo, 
                                  altura_ajustada_proximo)
        
        # Desenhar botão para voltar ao menu
        largura_menu = 320
        altura_menu = 65
        x_menu = LARGURA // 2
        y_menu = ALTURA // 2 + 140
        largura_ajustada_menu = int(largura_menu * escala_y)
        altura_ajustada_menu = int(altura_menu * escala_y)
        rect_menu = pygame.Rect(x_menu - largura_ajustada_menu // 2, 
                               y_menu - altura_ajustada_menu // 2, 
                               largura_ajustada_menu, 
                               altura_ajustada_menu)
        
        # Desenhar os botões com gradientes verdes
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        
        hover_proximo = rect_proximo.collidepoint(mouse_pos)
        cor_base_proximo = (40, 150, 40) if not hover_proximo else (60, 200, 60)
        cor_borda_proximo = (80, 220, 80) if not hover_proximo else (100, 255, 100)
        
        hover_menu = rect_menu.collidepoint(mouse_pos)
        cor_base_menu = (40, 100, 150) if not hover_menu else (60, 130, 200)
        cor_borda_menu = (80, 150, 220) if not hover_menu else (100, 180, 255)
        
        criar_botao(tela, "PRÓXIMA FASE (ENTER)", x_proximo, y_proximo, 
                   largura_proximo, altura_proximo, cor_base_proximo, cor_borda_proximo, BRANCO)
        
        criar_botao(tela, "VOLTAR AO MENU (M)", x_menu, y_menu, 
                   largura_menu, altura_menu, cor_base_menu, cor_borda_menu, BRANCO)
        
        # Verificar cliques nos botões
        if clique_ocorreu:
            if rect_proximo.collidepoint(mouse_pos):
                # Efeito de transição dourada
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    present_frame()
                    pygame.time.delay(20)
                return "proximo"
            
            if rect_menu.collidepoint(mouse_pos):
                # Efeito de fade out azul
                for i in range(30):
                    tela.fill((0, 0, 0, 10), special_flags=pygame.BLEND_RGBA_MULT)
                    present_frame()
                    pygame.time.delay(20)
                return "menu"
        
        present_frame()
        relogio.tick(FPS)