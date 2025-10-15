#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a lógica das fases do jogo.
Sistema corrigido: E=equipar arma, Q=granada, mouse=tiro com prioridade.
ATUALIZADO: Agora inclui suporte completo ao sistema modular de boss fights.
ATUALIZADO: Ampulheta agora é um item visual (segurar + clicar).
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
from src.ui.hud import desenhar_hud
from src.utils.display_manager import present_frame, convert_mouse_position
# Importações das pastas reorganizadas
from src.entities.inimigo_ia import atualizar_IA_inimigo
from src.items.granada import Granada, lancar_granada, processar_granadas, inicializar_sistema_granadas, obter_intervalo_lancamento
from src.weapons.espingarda import atirar_espingarda, carregar_upgrade_espingarda
from src.weapons.metralhadora import atirar_metralhadora, carregar_upgrade_metralhadora
from src.weapons.sabre_luz import processar_deflexao_tiros, atualizar_sabre, processar_dano_sabre
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos, desenhar_invocacoes, tem_invocacao_ativa, limpar_invocacoes
from src.items.amuleto import usar_amuleto_para_invocacao
from src.utils.visual import desenhar_grid_consistente

# NOVO: Importação do sistema modular de boss fights
from src.game.fase_boss import executar_boss_fight

# NOVO: Importação do sistema de ampulheta visual
from src.items.ampulheta import usar_ampulheta, desenhar_efeito_tempo_desacelerado

def jogar_fase(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
    """
    Executa uma fase específica do jogo com sistema corrigido:
    - E: Equipa arma do inventário (incluindo sabre de luz)
    - Q: Liga/desliga item (granada, ampulheta, amuleto)
    - Mouse: Tiro com prioridade (amuleto > granada > ampulheta > arma especial > sabre > tiro normal)
    - Clique direito: Modo defesa do sabre (quando equipado)
    
    ATUALIZADO: Agora detecta e executa boss fights usando sistema modular.
    ATUALIZADO: Ampulheta agora funciona como item visual (segurar + clicar).
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        numero_fase: Número da fase a jogar
        gradiente_jogo: Superfície com o gradiente de fundo do jogo
        fonte_titulo: Fonte para títulos
        fonte_normal: Fonte para textos normais
        
    Returns:
        Resultado da fase:
            - True: fase completada com sucesso
            - False: jogador perdeu
            - "menu": voltar ao menu (quando pausado)
    """
    # NOVA VERIFICAÇÃO PARA BOSS FIGHTS
    print(f"🎯 Iniciando fase {numero_fase}...")
    
    # Criar a fase
    resultado_fase = NivelFactory.criar_fase(numero_fase)
    
    # Verificar se é boss fight
    if NivelFactory.e_boss_fight(resultado_fase):
        info_boss = NivelFactory.obter_info_boss(resultado_fase)
        print(f"🔥 DETECTADO: {info_boss['mensagem']}")
        
        # Executar boss fight usando sistema modular
        if info_boss['boss'] == 'fusion':
            return executar_boss_fight('fusion', tela, relogio, numero_fase, 
                                     gradiente_jogo, fonte_titulo, fonte_normal)
        
        # Futuro: adicionar outros tipos de boss aqui
        # elif info_boss['boss'] == 'outro_boss':
        #     return executar_boss_fight('outro_boss', tela, relogio, numero_fase, 
        #                              gradiente_jogo, fonte_titulo, fonte_normal)
        
        # Se tipo de boss não reconhecido, fallback para fase normal
        print(f"⚠️ Tipo de boss '{info_boss['boss']}' não reconhecido, executando fase normal")
        inimigos = NivelFactory.criar_fase_generica(numero_fase)
    else:
        # Se não for boss fight, usar resultado normal
        inimigos = resultado_fase
    
    # --- LÓGICA NORMAL DA FASE (para fases não-boss) ---
    
    # Defensive checks: garantir que 'inimigos' seja um iterável/lista válida
    if inimigos is None:
        print(f"[ERROR] NivelFactory.criar_fase({numero_fase}) retornou None. Abortando fase e voltando ao menu.")
        limpar_invocacoes()
        return "menu"

    # Se a fábrica retornou um iterável que não é lista (ex.: generator), converte para lista
    if not isinstance(inimigos, (list, tuple)):
        try:
            inimigos = list(inimigos)
        except Exception:
            print(f"[ERROR] NivelFactory.criar_fase({numero_fase}) retornou um tipo inválido: {type(inimigos)}. Voltando ao menu.")
            limpar_invocacoes()
            return "menu"
    
    # Criar jogador com sistema corrigido
    jogador = Quadrado(100, ALTURA_JOGO // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)
    
    # Criar fontes
    fonte_pequena = pygame.font.SysFont("Arial", 18)  # Fonte pequena para o HUD
    
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
    
    # Tempo de congelamento no início da fase
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
        pos_mouse = convert_mouse_position(pygame.mouse.get_pos())
        
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

                    # SISTEMA CORRIGIDO: Tecla E para equipar/guardar arma do inventário (incluindo sabre)
                    if evento.key == pygame.K_e:
                        resultado = jogador.ativar_arma_inventario()
                        print(resultado)
                        if resultado == "espingarda":
                            criar_texto_flutuante("ESPINGARDA EQUIPADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                AMARELO, particulas, 120, 32)
                        elif resultado == "metralhadora":
                            criar_texto_flutuante("METRALHADORA EQUIPADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                LARANJA, particulas, 120, 32)
                        elif resultado == "sabre_luz":
                            criar_texto_flutuante("SABRE DE LUZ EQUIPADO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                (150, 150, 255), particulas, 120, 32)
                        elif resultado == "guardada":
                            criar_texto_flutuante("ARMA GUARDADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                CINZA_ESCURO, particulas, 120, 32)
                        elif resultado == "granada_guardada":
                            criar_texto_flutuante("GRANADA GUARDADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                CINZA_ESCURO, particulas, 120, 32)
                        elif resultado == "nenhuma_selecionada":
                            criar_texto_flutuante("SELECIONE UMA ARMA NO INVENTÁRIO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERMELHO, particulas, 120, 32)
                        elif resultado == "sem_municao":
                            criar_texto_flutuante("ARMA SEM MUNIÇÃO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERMELHO, particulas, 120, 32)
                            

                    # SISTEMA CORRIGIDO: Tecla Q para ativar/desativar items
                    if evento.key == pygame.K_q:
                        resultado = jogador.ativar_items_inventario()
                        print(resultado)
                        if resultado == "granada_toggle":
                            criar_texto_flutuante("GRANADA ATIVADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERDE, particulas, 120, 32)       
                        elif resultado == "granada_guardada":
                            criar_texto_flutuante("GRANADA GUARDADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                CINZA_ESCURO, particulas, 120, 32)
                        # AMPULHETA - NOVO: Toggle visual (não ativa ainda)
                        elif resultado == "ampulheta_toggle":
                            criar_texto_flutuante("AMPULHETA PRONTA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                (150, 200, 255), particulas, 120, 32)
                        elif resultado == "ampulheta_guardada":
                            criar_texto_flutuante("AMPULHETA GUARDADA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                CINZA_ESCURO, particulas, 120, 32)
                        elif resultado == "ampulheta_ja_ativa":
                            criar_texto_flutuante("AMPULHETA JÁ ESTÁ ATIVA!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                AMARELO, particulas, 120, 32)
                        # AMULETO
                        elif resultado == "amuleto_toggle":
                            criar_texto_flutuante("AMULETO MÍSTICO ATIVADO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                (200, 150, 255), particulas, 120, 32)
                        elif resultado == "amuleto_guardado":
                            criar_texto_flutuante("AMULETO GUARDADO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                CINZA_ESCURO, particulas, 120, 32)
                        elif resultado == "sem_facas":
                            criar_texto_flutuante("SEM COMBAT KNIFE!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERMELHO, particulas, 120, 32)
                        elif resultado == "sem_granadas":
                            criar_texto_flutuante("SEM GRANADAS!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERMELHO, particulas, 120, 32)
                        elif resultado == "sem_ampulhetas":
                            criar_texto_flutuante("SEM AMPULHETAS!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                VERMELHO, particulas, 120, 32)
                        elif resultado == "nenhum_item_selecionado":
                            criar_texto_flutuante("SELECIONE UM ITEM NO INVENTÁRIO!", 
                                                LARGURA // 2, ALTURA // 4, 
                                                AMARELO, particulas, 120, 32) 
                                
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

                # SISTEMA CORRIGIDO: Tiro com prioridade (Amuleto > Granada > Ampulheta > Arma > Sabre > Normal)
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if tempo_atual - ultimo_clique_mouse >= intervalo_minimo_clique:
                        ultimo_clique_mouse = tempo_atual
                        
                        if evento.button == 1:  # Clique esquerdo
                            # PRIORIDADE 1: Invocação do Chucky (amuleto ativo)
                            if (hasattr(jogador, 'amuleto_ativo') and jogador.amuleto_ativo and 
                                hasattr(jogador, 'facas') and jogador.facas > 0):
                                
                                if usar_amuleto_para_invocacao(pos_mouse, jogador):
                                    criar_texto_flutuante("CHUCKY INVOCADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (255, 50, 50), particulas, 180, 36)
                                    if jogador.facas <= 0:
                                        criar_texto_flutuante("AMULETO SEM ENERGIA!", 
                                                            LARGURA // 2, ALTURA // 4 + 50, 
                                                            VERMELHO, particulas, 120, 28)
                                else:
                                    criar_texto_flutuante("JÁ EXISTE UMA INVOCAÇÃO ATIVA!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        AMARELO, particulas, 120, 24)
                            
                            # PRIORIDADE 2: Granada
                            elif jogador.granada_selecionada and jogador.granadas > 0:
                                if tempo_atual - tempo_ultimo_lancamento_granada >= intervalo_lancamento_granada:
                                    tempo_ultimo_lancamento_granada = tempo_atual
                                    lancar_granada(jogador, granadas, pos_mouse, particulas, flashes)
                            
                            # PRIORIDADE 3: Ampulheta (NOVO!)
                            elif hasattr(jogador, 'ampulheta_selecionada') and jogador.ampulheta_selecionada:
                                if usar_ampulheta(jogador, particulas, flashes):
                                    criar_texto_flutuante("TEMPO DESACELERADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (150, 200, 255), particulas, 180, 48)
                                else:
                                    if jogador.tempo_desacelerado:
                                        criar_texto_flutuante("AMPULHETA JÁ ATIVA!", 
                                                            LARGURA // 2, ALTURA // 4, 
                                                            AMARELO, particulas, 120, 32)
                            
                            # PRIORIDADE 4: Sabre de Luz (ativar/desativar)
                            elif hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                                resultado_sabre = jogador.ativar_sabre_luz()
                                if resultado_sabre == "sabre_ativado":
                                    criar_texto_flutuante("SABRE ATIVADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (150, 150, 255), particulas, 120, 32)
                                elif resultado_sabre == "sabre_desativado":
                                    criar_texto_flutuante("SABRE DESATIVADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (100, 100, 150), particulas, 120, 32)
                            
                            # PRIORIDADE 5: Espingarda
                            elif jogador.espingarda_ativa and jogador.tiros_espingarda > 0:
                                atirar_espingarda(jogador, tiros_jogador, pos_mouse, particulas, flashes)
                                if jogador.tiros_espingarda <= 0:
                                    jogador.espingarda_ativa = False
                                    criar_texto_flutuante("ESPINGARDA SEM MUNIÇÃO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        VERMELHO, particulas, 120, 32)
                            
                            # PRIORIDADE 6: Metralhadora
                            elif jogador.metralhadora_ativa and jogador.tiros_metralhadora > 0:
                                atirar_metralhadora(jogador, tiros_jogador, pos_mouse, particulas, flashes)
                                if jogador.tiros_metralhadora <= 0:
                                    jogador.metralhadora_ativa = False
                                    criar_texto_flutuante("METRALHADORA SEM MUNIÇÃO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        VERMELHO, particulas, 120, 32)
                            else:
                                # PRIORIDADE 7: Tiro normal
                                jogador.atirar_com_mouse(tiros_jogador, pos_mouse)
                        
                        elif evento.button == 3:  # Clique direito - Modo defesa do sabre
                            if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                                resultado_defesa = jogador.alternar_modo_defesa_sabre()
                                if resultado_defesa == "modo_defesa_ativado":
                                    criar_texto_flutuante("MODO DEFESA ATIVADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (100, 255, 100), particulas, 120, 32)
                                elif resultado_defesa == "modo_defesa_desativado":
                                    criar_texto_flutuante("MODO DEFESA DESATIVADO!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        (150, 150, 255), particulas, 120, 32)
            
            # Handle pause menu controls
            elif pausado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        pausado = False
                        pygame.mixer.unpause()
                        pygame.mouse.set_visible(False)

                # Handle mouse clicks while paused
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
                    if rect_menu_pausado and rect_menu_pausado.collidepoint(mouse_pos):
                        limpar_invocacoes()
                        return "menu"

        # Tiro contínuo da metralhadora (quando botão esquerdo está pressionado)
        if not mostrando_inicio and not pausado and not jogador_morto and not em_congelamento:
            botoes_mouse = pygame.mouse.get_pressed()
            if botoes_mouse[0]:  # Botão esquerdo pressionado
                if jogador.metralhadora_ativa and jogador.tiros_metralhadora > 0:
                    # Atirar continuamente com a metralhadora
                    atirar_metralhadora(jogador, tiros_jogador, pos_mouse, particulas, flashes)
                    if jogador.tiros_metralhadora <= 0:
                        jogador.metralhadora_ativa = False  # Desativar quando acabar
                        criar_texto_flutuante("METRALHADORA SEM MUNIÇÃO!", 
                                            LARGURA // 2, ALTURA // 4, 
                                            VERMELHO, particulas, 120, 32)
                    
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
            present_frame()
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
            
            present_frame()
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
            
            present_frame()
            relogio.tick(FPS)
            continue

        # NOVO: Obter fator de tempo do jogador
        fator_tempo = jogador.obter_fator_tempo()

        # Só atualiza se não estiver congelado
        if not em_congelamento:
            # Atualizar posição do jogador apenas se não estiver morto
            if not jogador_morto:
                jogador.mover(movimento_x, movimento_y)
                jogador.atualizar()
                atualizar_invocacoes_com_inimigos(inimigos, particulas, flashes)

                # Garantir que o jogador não ultrapasse a área de jogo
                if jogador.y + jogador.tamanho > ALTURA_JOGO:
                    jogador.y = ALTURA_JOGO - jogador.tamanho
                    jogador.rect.y = jogador.y

                # NOVO: Atualizar sistema do sabre de luz
                if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                    atualizar_sabre(jogador, pos_mouse, tempo_atual)
            
            # Atualizar moedas e verificar colisões
            moeda_coletada = moeda_manager.atualizar(jogador)

            # MODIFICADO: Atualizar IA para cada inimigo com fator tempo
            for idx, inimigo in enumerate(inimigos):
                # Aplicar fator de tempo ao inimigo
                inimigo_velocidade_original = inimigo.velocidade
                inimigo.velocidade *= fator_tempo
                
                tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                    inimigo, idx, jogador, tiros_jogador, inimigos, tempo_atual, 
                    tempo_movimento_inimigos, intervalo_movimento, numero_fase, 
                    tiros_inimigo, movimento_x, movimento_y,
                    particulas, flashes  # Passando as listas como parâmetros
                )
                
                # Restaurar velocidade original
                inimigo.velocidade = inimigo_velocidade_original
                
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
            
            # MODIFICADO: Atualizar tiros do inimigo com fator tempo
            for tiro in tiros_inimigo[:]:
                # Aplicar fator de tempo aos tiros dos inimigos
                tiro_velocidade_original = tiro.velocidade
                tiro.velocidade *= fator_tempo
                
                tiro.atualizar()
                
                # Restaurar velocidade original
                tiro.velocidade = tiro_velocidade_original
                
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

            # NOVO: Processar deflexão de tiros pelo sabre de luz
            if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                tiros_refletidos = processar_deflexao_tiros(jogador, tiros_inimigo, particulas, flashes)
                # Adicionar tiros refletidos à lista de tiros do jogador
                tiros_jogador.extend(tiros_refletidos)
                
                # NOVO: Processar dano do sabre nos inimigos
                inimigos_cortados = processar_dano_sabre(jogador, inimigos, particulas, flashes)
                
                # Adicionar moedas pelos inimigos mortos pelo sabre
                for inimigo in inimigos_cortados:
                    if inimigo.vidas <= 0:
                        # Determinar quantidade de moedas
                        moedas_bonus = 1
                        if inimigo.cor == ROXO:
                            moedas_bonus = 5
                        elif inimigo.cor == CIANO:
                            moedas_bonus = 8
                        elif inimigo.vidas_max > 1:
                            moedas_bonus = 2
                        
                        # Adicionar moedas
                        moeda_manager.quantidade_moedas += moedas_bonus
                        moeda_manager.salvar_moedas()
                        
                        # Animação de pontuação
                        criar_texto_flutuante(f"+{moedas_bonus}", 
                                            inimigo.x + inimigo.tamanho//2, 
                                            inimigo.y, AMARELO, particulas)

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
                limpar_invocacoes()
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
                limpar_invocacoes()
                return False # Jogador perdeu
            
        # Desenhar fundo
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
            
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar grid de fundo
        desenhar_grid_consistente(tela)
        
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
        
        desenhar_invocacoes(tela)

        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar moedas
        moeda_manager.desenhar(tela)
        
        # NOVO: Desenhar efeito de tempo desacelerado (da ampulheta)
        desenhar_efeito_tempo_desacelerado(tela, jogador.tem_ampulheta_ativa(), tempo_atual)
        
        # Desenhar HUD atualizado com sistema corrigido
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
        
        present_frame()
        relogio.tick(FPS)
    
    limpar_invocacoes()
    return False  # Padrão: jogador perdeu