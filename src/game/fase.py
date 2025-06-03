#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a lógica das fases do jogo.
"""

import pygame
import random
import math
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.visual import criar_estrelas, desenhar_texto
from src.utils.sound import gerar_som_explosao, gerar_som_dano
from src.game.nivel_factory import NivelFactory
from src.game.moeda_manager import MoedaManager
from src.config import ALTURA_JOGO
from src.utils.visual import desenhar_mira, criar_mira
from src.utils.visual import desenhar_texto, criar_texto_flutuante, criar_botao
from src.utils.visual import desenhar_estrelas, criar_estrelas
from src.ui import desenhar_hud

# Novas importações das pastas reorganizadas
from src.entities.inimigo_ia import atualizar_IA_inimigo
from src.items.granada import Granada, lancar_granada, processar_granadas, inicializar_sistema_granadas, obter_intervalo_lancamento
from src.weapons.espingarda import atirar_espingarda, carregar_upgrade_espingarda

def jogar_fase(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
    """
    Executa uma fase específica do jogo.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        numero_fase: Número da fase a jogar
        gradiente_jogo: Superfície com o gradiente de fundo do jogo
        fonte_titulo: Fonte para títulos
        fonte_normal: Fonte para textos normais
        
    Returns:
        Tupla (resultado, pontuacao):
            - resultado: True se a fase foi completada, False se o jogador perdeu
            - pontuacao: Pontuação obtida nessa fase
    """
    # Criar jogador
    jogador = Quadrado(100, ALTURA_JOGO // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)
    
    # Criar fontes
    fonte_pequena = pygame.font.SysFont("Arial", 18)  # Fonte pequena para o HUD
    
    # Criar inimigos
    inimigos = NivelFactory.criar_fase(numero_fase)    
    moeda_manager = MoedaManager()

    # Listas para tiros, granadas e partículas
    tiros_jogador = []
    tiros_inimigo = []
    particulas = []     
    flashes = []
    
    # Inicializar sistema de granadas
    granadas, tempo_ultimo_lancamento_granada = inicializar_sistema_granadas()
    intervalo_lancamento_granada = obter_intervalo_lancamento()
    
    # Flag para pausa
    pausado = False
    
    # Flag para controle de morte
    jogador_morto = False
    
    # Controles de movimento
    movimento_x = 0
    movimento_y = 0
    
    # Tempos para a IA dos inimigos
    tempo_movimento_inimigos = [0] * len(inimigos)
    intervalo_movimento = max(300, 600 - numero_fase * 30)  # Reduz com a fase
    
    # Criar estrelas para o fundo
    estrelas = criar_estrelas(NUM_ESTRELAS_JOGO)
    
    # Efeito de início de fase
    fade_in = 255
    
    # Mostrar texto de início de fase
    mostrando_inicio = True
    contador_inicio = 120  # 2 segundos a 60 FPS
    
    # Atraso para tela de vitória
    tempo_transicao_vitoria = None  # Será definido quando o último inimigo for derrotado
    duracao_transicao_vitoria = 180  # 3 segundos a 60 FPS
    
    # Atraso para tela de derrota
    tempo_transicao_derrota = None  # Será definido quando o jogador perder
    duracao_transicao_derrota = 120  # 2 segundos a 60 FPS
    
    # Tempo de congelamento no início da fase (IMPORTANTE: Definir isso ANTES de usar)
    tempo_congelamento = 240  # 4 segundos a 60 FPS
    em_congelamento = False  # Será ativado após a introdução
    
    # Cursor do mouse visível durante o jogo
    pygame.mouse.set_visible(False)  # Esconder o cursor padrão do sistema

    # Criar mira personalizada
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)
    intervalo_minimo_clique = 100  # milissegundos

    # Rectangle for pause menu button
    rect_menu_pausado = None
    ultimo_clique_mouse = 0

# Loop principal da fase
    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()
        
        # Mostrar/ocultar cursor dependendo do estado
        if not mostrando_inicio and not pausado:
            pygame.mouse.set_visible(False)  # Ocultar apenas durante o jogo ativo
        else:
            pygame.mouse.set_visible(True)   # Mostrar nos menus/pausa/início
        
        # Obter a posição atual do mouse para o sistema de mira
        pos_mouse = pygame.mouse.get_pos()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            
            # Controles do teclado para o jogador (quando não estiver na introdução, pausado, morto ou congelado)
            if not mostrando_inicio and not pausado and not jogador_morto and not em_congelamento:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_w:
                        movimento_y = -1
                    if evento.key == pygame.K_s:
                        movimento_y = 1
                    if evento.key == pygame.K_a:
                        movimento_x = -1
                    if evento.key == pygame.K_d:
                        movimento_x = 1

                    if evento.key == pygame.K_ESCAPE:
                        pausado = True
                        pygame.mixer.pause()
                        pygame.mouse.set_visible(True)
               
                # Parar o movimento quando soltar as teclas
                if evento.type == pygame.KEYUP:
                    if evento.key == pygame.K_w and movimento_y < 0:
                        movimento_y = 0
                    if evento.key == pygame.K_s and movimento_y > 0:
                        movimento_y = 0
                    if evento.key == pygame.K_a and movimento_x < 0:
                        movimento_x = 0
                    if evento.key == pygame.K_d and movimento_x > 0:
                        movimento_x = 0

# Tecla para ativar/desativar espingarda (E)
                    if evento.key == pygame.K_e:
                        # Verificar se o jogador já comprou o upgrade da espingarda
                        if hasattr(jogador, 'tiros_espingarda'):
                            if jogador.tiros_espingarda > 0:
                                jogador.espingarda_ativa = not jogador.espingarda_ativa
                                print(f"DEBUG: Espingarda ativada: {jogador.espingarda_ativa}, Tiros: {jogador.tiros_espingarda}")
                                
                                jogador.granada_selecionada = False  # Desativar granada ao selecionar espingarda
                                # Adicionar feedback visual

                            elif carregar_upgrade_espingarda() > 0:  # Use a função importada
                                # Jogador comprou o upgrade, mas já usou todos os tiros desta partida
                                criar_texto_flutuante("SEM TIROS DE ESPINGARDA RESTANTES!", 
                                                    LARGURA // 2, ALTURA // 4, 
                                                    VERMELHO, particulas, 120, 32)
                    
                    # Tecla para ativar/desativar granada (Q)
                    if evento.key == pygame.K_q:
                        # Alternar modo de granada
                        if hasattr(jogador, 'granadas'):
                            if jogador.granadas > 0:
                                jogador.granada_selecionada = not jogador.granada_selecionada
                                jogador.espingarda_ativa = False  # Desativar espingarda ao selecionar granada
                                
                                # Mostrar mensagem de ativação/desativação


# Tiro com o botão esquerdo do mouse (apenas se não estiver morto ou congelado)
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Verificar se passou tempo suficiente desde o último clique
                    if tempo_atual - ultimo_clique_mouse >= intervalo_minimo_clique:
                        ultimo_clique_mouse = tempo_atual
                        
                        if jogador.granada_selecionada and jogador.granadas > 0:
                            # Verificar intervalo entre lançamentos de granadas
                            if tempo_atual - tempo_ultimo_lancamento_granada >= intervalo_lancamento_granada:
                                tempo_ultimo_lancamento_granada = tempo_atual
                                lancar_granada(jogador, granadas, pos_mouse, particulas, flashes)
                        elif jogador.espingarda_ativa and jogador.tiros_espingarda > 0:
                            atirar_espingarda(jogador, tiros_jogador, pos_mouse, particulas, flashes)
                            if jogador.tiros_espingarda <= 0:
                                jogador.espingarda_ativa = False
                                criar_texto_flutuante("SEM TIROS DE ESPINGARDA!", 
                                                    LARGURA // 2, ALTURA // 4, 
                                                    VERMELHO, particulas, 120, 32)
                        else:
                            # Atirar normal (já tem verificação de cooldown na função)
                            jogador.atirar_com_mouse(tiros_jogador, pos_mouse)
            
            # Handle pause menu controls
            elif pausado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        pausado = False
                        pygame.mixer.unpause()
                        pygame.mouse.set_visible(False)

                
                # Handle mouse clicks while paused
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if rect_menu_pausado and rect_menu_pausado.collidepoint(mouse_pos):
                        return "menu"
                    
# Atualizar contador de introdução
        if mostrando_inicio:
            contador_inicio -= 1
            if contador_inicio <= 0:
                mostrando_inicio = False
                em_congelamento = True  # Inicia o congelamento após a introdução
            
            # Preencher toda a tela com preto antes de desenhar qualquer coisa
            tela.fill((0, 0, 0))
            
            # Desenhar tela de introdução
            tela.blit(gradiente_jogo, (0, 0))
            
            # Desenhar estrelas
            for estrela in estrelas:
                x, y, tamanho, brilho, _ = estrela
                pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
            
            # Texto de introdução com efeito
            tamanho = 70 + int(math.sin(tempo_atual / 200) * 5)
            desenhar_texto(tela, f"FASE {numero_fase}", tamanho, BRANCO, LARGURA // 2, ALTURA_JOGO // 3)
            desenhar_texto(tela, f"{len(inimigos)} inimigo{'s' if len(inimigos) > 1 else ''} para derrotar", 36, 
                        AMARELO, LARGURA // 2, ALTURA_JOGO // 2)
            desenhar_texto(tela, "Preparado?", 30, BRANCO, LARGURA // 2, ALTURA_JOGO * 2 // 3)            
            pygame.display.flip()
            relogio.tick(FPS)
            continue

# Lógica de congelamento
        if em_congelamento:
            tempo_congelamento -= 1
            
            # Durante o congelamento, apenas desenha sem atualizar
            tela.fill((0, 0, 0))
            tela.blit(gradiente_jogo, (0, 0))
            
            # Desenhar estrelas (paradas)
            desenhar_estrelas(tela, estrelas)
            
            # Desenhar grid de fundo
            for i in range(0, LARGURA, 50):
                pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA_JOGO), 1)
            for i in range(0, ALTURA_JOGO, 50):
                pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
            
            # Desenhar jogador e inimigos (sem movimento)
            if jogador.vidas > 0:
                jogador.desenhar(tela, tempo_atual)
            for inimigo in inimigos:
                if inimigo.vidas > 0:
                    inimigo.desenhar(tela, tempo_atual)
            
            # Desenhar timer de congelamento
            segundos_restantes = max(0, tempo_congelamento // FPS)
            cor_timer = AMARELO if segundos_restantes > 0 else VERDE
            desenhar_texto(tela, f"PREPARAR: {segundos_restantes}", 50, cor_timer, 
                          LARGURA // 2, ALTURA_JOGO // 2)
            
            # Desenhar HUD
            desenhar_hud(tela, numero_fase, inimigos, tempo_atual, moeda_manager, jogador)            
            # Quando o congelamento terminar
            if tempo_congelamento <= 0:
                em_congelamento = False
            
            pygame.display.flip()
            relogio.tick(FPS)
            continue

# Efeito de fade in no início da fase
        if fade_in > 0:
            fade_in = max(0, fade_in - 10)
        
        # Se o jogo estiver pausado, pular a atualização
        if pausado:
            # Preencher toda a tela com preto antes de desenhar qualquer coisa
            tela.fill((0, 0, 0))
            
            # Desenhar mensagem de pausa com efeito transparente
            overlay = pygame.Surface((LARGURA, ALTURA))
            overlay.fill((0, 0, 20))
            overlay.set_alpha(180)
            tela.blit(overlay, (0, 0))
            
            # Desenhar PAUSADO
            desenhar_texto(tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 - 50)
            desenhar_texto(tela, "Pressione ESC para continuar", 30, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 20)
            
            # Create Menu button
            largura_menu = 250
            altura_menu = 50
            x_menu = LARGURA // 2
            y_menu = ALTURA_JOGO // 2 + 100
            
            # Scale adjustments
            escala_y = ALTURA / 848
            largura_ajustada_menu = int(largura_menu * escala_y)
            altura_ajustada_menu = int(altura_menu * escala_y)
            rect_menu_pausado = pygame.Rect(x_menu - largura_ajustada_menu // 2, 
                                           y_menu - altura_ajustada_menu // 2, 
                                           largura_ajustada_menu, 
                                           altura_ajustada_menu)
            
            # Draw the menu button
            hover_menu = criar_botao(tela, "VOLTAR AO MENU", x_menu, y_menu, 
                                    largura_menu, altura_menu, 
                                    (120, 60, 60), (180, 80, 80), BRANCO)
            
            pygame.display.flip()
            relogio.tick(FPS)
            continue

# Só atualiza se não estiver congelado
        if not em_congelamento:
            # Atualizar posição do jogador apenas se não estiver morto
            if not jogador_morto:
                jogador.mover(movimento_x, movimento_y)
                jogador.atualizar()
                
                # Garantir que o jogador não ultrapasse a área de jogo
                if jogador.y + jogador.tamanho > ALTURA_JOGO:
                    jogador.y = ALTURA_JOGO - jogador.tamanho
                    jogador.rect.y = jogador.y
            
            # Atualizar moedas e verificar colisões
            moeda_coletada = moeda_manager.atualizar(jogador)

                
            # Atualizar IA para cada inimigo
            for idx, inimigo in enumerate(inimigos):
                tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                    inimigo, idx, jogador, tiros_jogador, inimigos, tempo_atual, 
                    tempo_movimento_inimigos, intervalo_movimento, numero_fase, 
                    tiros_inimigo, movimento_x, movimento_y,
                    particulas, flashes  # Passando as listas como parâmetros
                )
                
                # Garantir que os inimigos não ultrapassem a área de jogo
                if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                    inimigo.y = ALTURA_JOGO - inimigo.tamanho
                    inimigo.rect.y = inimigo.y

            # Atualizar tiros do jogador
            for tiro in tiros_jogador[:]:
                tiro.atualizar()
                
                # Verificar colisão com os inimigos
                for inimigo in inimigos:
                    if inimigo.vidas <= 0:
                        continue  # Ignorar inimigos derrotados
                    
                    if tiro.rect.colliderect(inimigo.rect):
                        dano_causou_morte = False
                        
                        # Verificar se este dano vai matar o inimigo
                        if inimigo.vidas == 1:
                            dano_causou_morte = True
                        
                        # Aplicar o dano
                        if inimigo.tomar_dano():
                            # Se o inimigo morreu, adicionar moedas
                            if dano_causou_morte:
                                # Determinar quantidade de moedas com base no tipo de inimigo
                                moedas_bonus = 1  # Valor padrão para inimigos básicos
                                
                                # Inimigos com mais vida ou especiais dão mais moedas
                                if inimigo.cor == ROXO:  # Inimigo roxo (especial)
                                    moedas_bonus = 5
                                elif inimigo.cor == CIANO:  # Inimigo ciano
                                    moedas_bonus = 8
                                elif inimigo.vidas_max > 1:  # Inimigos com múltiplas vidas
                                    moedas_bonus = 2
                                
                                # Adicionar moedas ao contador
                                moeda_manager.quantidade_moedas += moedas_bonus
                                moeda_manager.salvar_moedas()  # Salvar as moedas no arquivo
                                
                                # Criar animação de pontuação no local da morte
                                criar_texto_flutuante(f"+{moedas_bonus}", inimigo.x + inimigo.tamanho//5, 
                                                    inimigo.y, AMARELO, particulas)
                            
                            # Efeitos visuais de explosão
                            flash = criar_explosao(tiro.x, tiro.y, VERMELHO, particulas, 25)
                            flashes.append(flash)
                            pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
                        
                        tiros_jogador.remove(tiro)
                        break  # Sair do loop de inimigos após uma colisão
                
                # Se o tiro ainda existe, verificar se saiu da tela
                if tiro in tiros_jogador and tiro.fora_da_tela():
                    tiros_jogador.remove(tiro)
            
            # Atualizar tiros do inimigo
            for tiro in tiros_inimigo[:]:
                tiro.atualizar()
                
                # Verificar colisão com o jogador apenas se ele não estiver morto
                if not jogador_morto and tiro.rect.colliderect(jogador.rect):
                    if jogador.tomar_dano():
                        flash = criar_explosao(tiro.x, tiro.y, AZUL, particulas, 25)
                        flashes.append(flash)
                        pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                    tiros_inimigo.remove(tiro)
                    continue
                
                # Remover tiros que saíram da tela
                if tiro.fora_da_tela():
                    tiros_inimigo.remove(tiro)

            # Processar granadas usando a função centralizada
            processar_granadas(granadas, particulas, flashes, inimigos, moeda_manager)
            
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
            
            # Atualizar estrelas
            for estrela in estrelas:
                estrela[0] -= estrela[4]  # Mover com base na velocidade
                if estrela[0] < 0:
                    estrela[0] = LARGURA
                    estrela[1] = random.randint(0, ALTURA_JOGO) 

# Verificar se todos os inimigos foram derrotados e tratar transição de vitória
        todos_derrotados = all(inimigo.vidas <= 0 for inimigo in inimigos)
        
        # Se todos os inimigos foram derrotados, tornar o jogador invulnerável
        if todos_derrotados:
            # Tornar o jogador invulnerável permanentemente
            jogador.invulneravel = True
            jogador.duracao_invulneravel = float('inf')  # Invulnerabilidade infinita
            
            # Iniciar contagem para transição se ainda não iniciou
            if tempo_transicao_vitoria is None:
                tempo_transicao_vitoria = duracao_transicao_vitoria
        
        # Se a contagem regressiva de vitória está ativa, decrementá-la
        if tempo_transicao_vitoria is not None:
            tempo_transicao_vitoria -= 1
            
            # Quando a contagem chegar a zero, concluir a fase
            if tempo_transicao_vitoria <= 0:
                return True  # Fase concluída com sucesso
        
        # Verificar condições de fim de fase
        if jogador.vidas <= 0:
            # Marcar o jogador como morto
            jogador_morto = True
            for inimigo in inimigos:
                inimigo.invulneravel = True
                inimigo.duracao_invulneravel = float('inf')
            # Iniciar contagem para transição de derrota se ainda não iniciou
            if tempo_transicao_derrota is None:
                tempo_transicao_derrota = duracao_transicao_derrota
                
                # Parar movimento do jogador
                movimento_x = 0
                movimento_y = 0
                
                # Criar explosões quando o jogador morrer
                for _ in range(5):
                    x = jogador.x + random.randint(-30, 30)
                    y = jogador.y + random.randint(-30, 30)
                    flash = criar_explosao(x, y, VERMELHO, particulas, 35)
                    flashes.append(flash)
                
                # Som de derrota
                pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
        
        # Se a contagem regressiva de derrota está ativa, decrementá-la
        if tempo_transicao_derrota is not None:
            tempo_transicao_derrota -= 1
            
            # Quando a contagem chegar a zero, ir para a tela de game over
            if tempo_transicao_derrota <= 0:
                return False # Jogador perdeu
            
# Desenhar fundo
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
            
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar grid de fundo
        for i in range(0, LARGURA, 50):
            pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA_JOGO), 1)
        for i in range(0, ALTURA_JOGO, 50):
            pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
        
        # Desenhar flashes
        for flash in flashes:
            if flash['y'] < ALTURA_JOGO:  # Só desenhar flashes na área de jogo
                pygame.draw.circle(tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))
        
        # Desenhar objetos do jogo - IMPORTANTE: Passar tempo_atual para a função desenhar
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
        
        # Desenhar granadas
        for granada in granadas:
            granada.desenhar(tela)
        
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar moedas
        moeda_manager.desenhar(tela)
        
        # Desenhar HUD (pontuação, vidas e fase) na área dedicada
        desenhar_hud(tela, numero_fase, inimigos, tempo_atual, moeda_manager, jogador)        
        # Aplicar efeito de fade-in (em toda a tela)
        if fade_in > 0:
            fade = pygame.Surface((LARGURA, ALTURA))
            fade.fill((0, 0, 0))
            fade.set_alpha(fade_in)
            tela.blit(fade, (0, 0))

# Desenhar mensagem de vitória durante a transição
        if tempo_transicao_vitoria is not None:
            # Criar um efeito de fade ou texto pulsante
            alpha = int(255 * (duracao_transicao_vitoria - tempo_transicao_vitoria) / duracao_transicao_vitoria)
            texto_surf = fonte_titulo.render("FASE CONCLUÍDA!", True, VERDE)
            texto_surf.set_alpha(alpha)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
            tela.blit(texto_surf, texto_rect)
            
            # Adicionar partículas de celebração aleatórias
            if random.random() < 0.2:  # 20% de chance por frame
                x = random.randint(0, LARGURA)
                y = random.randint(0, ALTURA_JOGO)
                cor = random.choice([VERDE, AMARELO, AZUL])
                flash = criar_explosao(x, y, cor, particulas, 15)
                flashes.append(flash)
        
        # Desenhar mensagem de derrota durante a transição
        if tempo_transicao_derrota is not None:
            # Criar um efeito de fade ou texto pulsante
            alpha = int(255 * (duracao_transicao_derrota - tempo_transicao_derrota) / duracao_transicao_derrota)
            texto_surf = fonte_titulo.render("DERROTADO!", True, VERMELHO)
            texto_surf.set_alpha(alpha)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
            tela.blit(texto_surf, texto_rect)
            
            # Adicionar efeito de tela vermelha
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
            overlay.fill(VERMELHO)
            overlay.set_alpha(int(50 * (duracao_transicao_derrota - tempo_transicao_derrota) / duracao_transicao_derrota))
            tela.blit(overlay, (0, 0))
            
            # Adicionar mais partículas de derrota
            if random.random() < 0.3:  # 30% de chance por frame
                x = jogador.x + random.randint(-50, 50)
                y = jogador.y + random.randint(-50, 50)
                criar_explosao(x, y, VERMELHO, particulas, 20)

# Desenhar mira personalizada do mouse apenas se não estiver congelado
        if not em_congelamento:
            desenhar_mira(tela, pos_mouse, (mira_surface, mira_rect))
        
        pygame.display.flip()
        relogio.tick(FPS)
    
    return False # Padrão: jogador