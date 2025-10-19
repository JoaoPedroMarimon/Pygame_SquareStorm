#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema modular para fases com boss fights melhorado.
Gerencia cutscenes, boss fights e mecânicas especiais com movimentação dinâmica e novos ataques.
COM CONTROLE ADEQUADO DA MÚSICA DO BOSS.
"""

import pygame
import random
import math
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.visual import criar_estrelas, desenhar_texto, criar_texto_flutuante, desenhar_estrelas, desenhar_grid_consistente
from src.utils.sound import gerar_som_explosao, gerar_som_dano
from src.game.moeda_manager import MoedaManager
from src.ui.hud import desenhar_hud
from src.utils.display_manager import present_frame, convert_mouse_position

# Importar classes específicas do boss
from src.entities.boss_fusion import BossFusion
from src.entities.fusion_cutscene import FusionCutscene

# Importações das armas e itens
from src.items.granada import Granada, lancar_granada, processar_granadas, inicializar_sistema_granadas, obter_intervalo_lancamento
from src.weapons.espingarda import atirar_espingarda
from src.weapons.metralhadora import atirar_metralhadora
from src.weapons.sabre_luz import processar_deflexao_tiros, atualizar_sabre, processar_dano_sabre
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos, desenhar_invocacoes, limpar_invocacoes
from src.items.amuleto import usar_amuleto_para_invocacao

class BossDifficultyManager:
    """Gerencia a dificuldade adaptativa do boss."""
    
    def __init__(self):
        self.tempo_sobrevivencia = 0
        self.danos_tomados_jogador = 0
        self.danos_dados_boss = 0
        self.multiplicador_dificuldade = 1.0
    
    def atualizar_dificuldade(self, tempo_atual, jogador, boss):
        """Ajusta dificuldade baseada na performance do jogador."""
        self.tempo_sobrevivencia = tempo_atual
        
        # Se jogador está indo muito bem, aumentar dificuldade
        if self.tempo_sobrevivencia > 30000 and boss and boss.vidas > boss.vidas_max * 0.8:
            self.multiplicador_dificuldade = 1.2
            boss.cooldown_ataque = int(boss.cooldown_ataque * 0.8)
        
        # Se jogador está com dificuldade, diminuir um pouco
        elif jogador.vidas <= 1 and boss and boss.vidas > boss.vidas_max * 0.5:
            self.multiplicador_dificuldade = 0.9
            boss.cooldown_ataque = int(boss.cooldown_ataque * 1.1)
    
    def aplicar_modificadores_ataque(self, boss):
        """Aplica modificadores baseados na dificuldade."""
        if self.multiplicador_dificuldade > 1.0:
            return {
                'tiros_extras': True,
                'velocidade_aumentada': True,
                'combo_chance': 0.3
            }
        elif self.multiplicador_dificuldade < 1.0:
            return {
                'tiros_reduzidos': True,
                'velocidade_reduzida': True,
                'combo_chance': 0.1
            }
        return {}

class BossFightManager:
    """
    Gerenciador central para boss fights melhorado.
    Coordena cutscenes, boss e mecânicas especiais.
    """
    
    def __init__(self):
        self.boss_types = {
            'fusion': {
                'cutscene_class': FusionCutscene,
                'boss_class': BossFusion,
                'recompensa_base': 200,
                'nome': 'Boss Fusion'
            }
        }
        
        # Referência para a cutscene ativa (para controlar música)
        self.cutscene_ativa = None
    
    def parar_musica_boss(self):
        """Para a música do boss em qualquer situação."""
        try:
            if self.cutscene_ativa and hasattr(self.cutscene_ativa, 'parar_musica_definitivamente'):
                self.cutscene_ativa.parar_musica_definitivamente()
            else:
                # Fallback - parar música diretamente via pygame
                pygame.mixer.music.stop()
            print("Música do boss parada!")
        except Exception as e:
            print(f"Erro ao parar música do boss: {e}")
    
    def criar_boss_fight(self, tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
        """
        Cria e executa um boss fight do tipo especificado.
        """
        if tipo_boss not in self.boss_types:
            print(f"Tipo de boss '{tipo_boss}' não encontrado!")
            return False
        
        boss_info = self.boss_types[tipo_boss]
        
        # IMPORTANTE: Tentar parar qualquer música anterior antes de começar
        try:
            pygame.mixer.music.stop()
        except:
            pass
        
        if tipo_boss == 'fusion':
            resultado = self.executar_boss_fusion(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, boss_info)
            
            # SEMPRE parar a música no final, independente do resultado
            self.parar_musica_boss()
            
            return resultado
        
        return False
    
    def executar_boss_fusion(self, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, boss_info):
        """
        Executa o boss fight do Boss Fusion com cutscene e melhorias.
        """
        print(f"Boss Fusion melhorado iniciado - Fase {numero_fase}")
        
        # Inicializar componentes
        jogador = Quadrado(100, ALTURA_JOGO // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)
        moeda_manager = MoedaManager()
        
        # Sistema de dificuldade adaptativa
        difficulty_manager = BossDifficultyManager()
        
        # Sistema de cutscene
        cutscene = boss_info['cutscene_class']()
        self.cutscene_ativa = cutscene  # GUARDAR REFERÊNCIA PARA CONTROLE DE MÚSICA
        cutscene_ativa = True
        
        boss = None
        inimigos = []
        
        # Sistemas de jogo expandidos
        game_systems = self._inicializar_sistemas_jogo()
        game_systems['efeitos_especiais'] = []
        game_systems['difficulty_manager'] = difficulty_manager
        
        # Estados expandidos
        estados = {
            'pausado': False,
            'jogador_morto': False,
            'boss_derrotado': False,
            'movimento_x': 0,
            'movimento_y': 0,
            'boss_modo_desespero': False,
            'combo_counter': 0
        }
        
        # Ambiente visual
        ambiente = self._inicializar_ambiente()
        
        # Controles
        controles = self._inicializar_controles()
        
        # Transições
        transicoes = {
            'tempo_transicao_vitoria': None,
            'tempo_transicao_derrota': None,
            'duracao_transicao_vitoria': 360,
            'duracao_transicao_derrota': 240
        }
        
        # Iniciar cutscene
        tempo_atual = pygame.time.get_ticks()
        cutscene.iniciar(tempo_atual)
        
        print("Cutscene de fusão melhorada iniciada...")
        
        # Loop principal do boss fight
        rodando = True
        frames_contador = 0
        
        try:
            while rodando:
                tempo_atual = pygame.time.get_ticks()
                pos_mouse = convert_mouse_position(pygame.mouse.get_pos())
                frames_contador += 1
                
                # Processar eventos
                evento_resultado = self._processar_eventos(cutscene_ativa, estados, jogador, pos_mouse, 
                                                         tempo_atual, controles, boss, game_systems)
                
                if evento_resultado == "sair":
                    # PARAR MÚSICA ANTES DE SAIR
                    self.parar_musica_boss()
                    limpar_invocacoes()
                    return False
                elif evento_resultado == "menu":
                    # PARAR MÚSICA ANTES DE VOLTAR AO MENU
                    self.parar_musica_boss()
                    limpar_invocacoes()
                    return "menu"
                elif evento_resultado == "pular_cutscene":
                    cutscene_ativa = False
                    boss_x, boss_y = cutscene.get_boss_spawn_position()
                    boss = boss_info['boss_class'](boss_x, boss_y)
                    print("Cutscene pulada - Boss apareceu!")
                
                # Executar cutscene
                if cutscene_ativa:
                    cutscene_terminada = self._executar_cutscene(cutscene, tela, tempo_atual, relogio, 
                                                               gradiente_jogo, ambiente, jogador, game_systems)
                    if cutscene_terminada:
                        cutscene_ativa = False
                        boss_x, boss_y = cutscene.get_boss_spawn_position()
                        boss = boss_info['boss_class'](boss_x, boss_y)
                        self._criar_efeito_aparicao_boss(boss_x, boss_y, game_systems['particulas'], game_systems['flashes'])
                        print("Boss melhorado surgiu da fusão!")
                    continue
                
                # Lógica principal do jogo quando não pausado
                if not estados['pausado']:
                    # Atualizar dificuldade adaptativa
                    game_systems['difficulty_manager'].atualizar_dificuldade(tempo_atual, jogador, boss)
                    
                    # Verificar modo desespero
                    if boss and boss.vidas <= 5 and not estados['boss_modo_desespero']:
                        estados['boss_modo_desespero'] = True
                        boss.cooldown_ataque = int(boss.cooldown_ataque * 0.6)
                    
                    resultado_jogo = self._atualizar_jogo_melhorado(jogador, boss, inimigos, game_systems, estados, 
                                                                  tempo_atual, pos_mouse, moeda_manager, boss_info)
                    
                    if resultado_jogo == "boss_derrotado":
                        if transicoes['tempo_transicao_vitoria'] is None:
                            transicoes['tempo_transicao_vitoria'] = transicoes['duracao_transicao_vitoria']
                    elif resultado_jogo == "jogador_morto":
                        if transicoes['tempo_transicao_derrota'] is None:
                            transicoes['tempo_transicao_derrota'] = transicoes['duracao_transicao_derrota']
                
                # Processar transições
                resultado_transicao = self._processar_transicoes(transicoes)
                if resultado_transicao == "vitoria":
                    # PARAR MÚSICA ANTES DE RETORNAR VITÓRIA
                    self.parar_musica_boss()
                    limpar_invocacoes()
                    return True
                elif resultado_transicao == "derrota":
                    # PARAR MÚSICA ANTES DE RETORNAR DERROTA
                    self.parar_musica_boss()
                    limpar_invocacoes()
                    return False
                
                # Renderização melhorada
                self._renderizar_boss_fight_melhorado(tela, estados, gradiente_jogo, ambiente, jogador, boss, 
                                                    inimigos, game_systems, numero_fase, tempo_atual, 
                                                    moeda_manager, transicoes, pos_mouse, controles, frames_contador)
                
                present_frame()
                relogio.tick(FPS)
        
        except KeyboardInterrupt:
            # Se usuário pressionar Ctrl+C, parar música
            print("Interrupção detectada - parando música...")
            self.parar_musica_boss()
            limpar_invocacoes()
            return False
        
        except Exception as e:
            # Em caso de erro inesperado, parar música
            print(f"Erro inesperado no boss fight: {e}")
            self.parar_musica_boss()
            limpar_invocacoes()
            return False
        
        # Fallback final - sempre parar música
        self.parar_musica_boss()
        limpar_invocacoes()
        return False
    
    def _inicializar_sistemas_jogo(self):
        """Inicializa todos os sistemas de jogo."""
        granadas, tempo_ultimo_lancamento_granada = inicializar_sistema_granadas()
        
        return {
            'tiros_jogador': [],
            'tiros_inimigo': [],
            'particulas': [],
            'flashes': [],
            'granadas': granadas,
            'tempo_ultimo_lancamento_granada': tempo_ultimo_lancamento_granada,
            'intervalo_lancamento_granada': obter_intervalo_lancamento()
        }
    
    def _inicializar_ambiente(self):
        """Inicializa elementos visuais do ambiente."""
        return {
            'estrelas': criar_estrelas(NUM_ESTRELAS_JOGO)
        }
    
    def _inicializar_controles(self):
        """Inicializa sistema de controles."""
        pygame.mouse.set_visible(False)
        return {
            'rect_menu_pausado': None,
            'ultimo_clique_mouse': 0,
            'intervalo_minimo_clique': 100
        }
    
    def _processar_eventos(self, cutscene_ativa, estados, jogador, pos_mouse, tempo_atual, controles, boss, game_systems):
        """Processa todos os eventos do jogo."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"
            
            # Durante cutscene
            if cutscene_ativa:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    return "pular_cutscene"
                continue
            
            # Jogo normal
            if not estados['pausado'] and not estados['jogador_morto'] and not estados['boss_derrotado']:
                resultado_controles = self._processar_controles_jogo(evento, estados, jogador, pos_mouse, 
                                                                   tempo_atual, controles, game_systems)
                if resultado_controles:
                    return resultado_controles
            
            # Menu de pausa
            elif estados['pausado']:
                resultado_pausa = self._processar_controles_pausa(evento, controles, pos_mouse, estados)
                if resultado_pausa:
                    return resultado_pausa
        
        return None
    
    def _processar_controles_jogo(self, evento, estados, jogador, pos_mouse, tempo_atual, controles, game_systems):
        """Processa controles durante o jogo."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_w:
                estados['movimento_y'] = -1
            elif evento.key == pygame.K_s:
                estados['movimento_y'] = 1
            elif evento.key == pygame.K_a:
                estados['movimento_x'] = -1
            elif evento.key == pygame.K_d:
                estados['movimento_x'] = 1
            elif evento.key == pygame.K_ESCAPE:
                estados['pausado'] = True
                pygame.mixer.pause()
                pygame.mouse.set_visible(True)
            elif evento.key == pygame.K_e:
                self._processar_ativacao_arma(jogador, game_systems['particulas'])
            elif evento.key == pygame.K_q:
                self._processar_ativacao_item(jogador, game_systems['particulas'])
        
        elif evento.type == pygame.KEYUP:
            if evento.key == pygame.K_w and estados['movimento_y'] < 0:
                estados['movimento_y'] = 0
            elif evento.key == pygame.K_s and estados['movimento_y'] > 0:
                estados['movimento_y'] = 0
            elif evento.key == pygame.K_a and estados['movimento_x'] < 0:
                estados['movimento_x'] = 0
            elif evento.key == pygame.K_d and estados['movimento_x'] > 0:
                estados['movimento_x'] = 0
        
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if tempo_atual - controles['ultimo_clique_mouse'] >= controles['intervalo_minimo_clique']:
                controles['ultimo_clique_mouse'] = tempo_atual
                self._processar_ataques_mouse(evento, jogador, pos_mouse, tempo_atual, game_systems)
        
        return None
    
    def _processar_ativacao_arma(self, jogador, particulas):
        """Processa ativação de armas."""
        resultado = jogador.ativar_arma_inventario()
        
        mensagens = {
            "espingarda": ("ESPINGARDA EQUIPADA!", AMARELO),
            "metralhadora": ("METRALHADORA EQUIPADA!", LARANJA),
            "sabre_luz": ("SABRE DE LUZ EQUIPADO!", (150, 150, 255)),
            "guardada": ("ARMA GUARDADA!", CINZA_ESCURO)
        }
        
        if resultado in mensagens:
            texto, cor = mensagens[resultado]
            criar_texto_flutuante(texto, LARGURA // 2, ALTURA_JOGO // 4, cor, particulas, 120, 32)
    
    def _processar_ativacao_item(self, jogador, particulas):
        """Processa ativação de itens."""
        resultado = jogador.ativar_items_inventario()
        
        mensagens = {
            "granada_toggle": ("GRANADA ATIVADA!", VERDE),
            "ampulheta_ativada": ("AMPULHETA ATIVADA!", (150, 200, 255)),
            "amuleto_toggle": ("AMULETO MÍSTICO ATIVADO!", (200, 150, 255))
        }
        
        if resultado in mensagens:
            texto, cor = mensagens[resultado]
            criar_texto_flutuante(texto, LARGURA // 2, ALTURA_JOGO // 4, cor, particulas, 120, 32)
    
    def _processar_ataques_mouse(self, evento, jogador, pos_mouse, tempo_atual, game_systems):
        """Processa ataques com mouse."""
        if evento.button == 1:  # Clique esquerdo
            # Sistema de prioridade de ataques
            if (hasattr(jogador, 'amuleto_ativo') and jogador.amuleto_ativo and 
                hasattr(jogador, 'facas') and jogador.facas > 0):
                if usar_amuleto_para_invocacao(pos_mouse, jogador):
                    criar_texto_flutuante("CHUCKY INVOCADO!", LARGURA // 2, ALTURA_JOGO // 4, 
                                         (255, 50, 50), game_systems['particulas'], 180, 36)
            
            elif jogador.granada_selecionada and jogador.granadas > 0:
                if tempo_atual - game_systems['tempo_ultimo_lancamento_granada'] >= game_systems['intervalo_lancamento_granada']:
                    game_systems['tempo_ultimo_lancamento_granada'] = tempo_atual
                    lancar_granada(jogador, game_systems['granadas'], pos_mouse, 
                                 game_systems['particulas'], game_systems['flashes'])
            
            elif hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                resultado_sabre = jogador.ativar_sabre_luz()
                if resultado_sabre == "sabre_ativado":
                    criar_texto_flutuante("SABRE ATIVADO!", LARGURA // 2, ALTURA_JOGO // 4, 
                                         (150, 150, 255), game_systems['particulas'], 120, 32)
            
            elif jogador.espingarda_ativa and jogador.tiros_espingarda > 0:
                atirar_espingarda(jogador, game_systems['tiros_jogador'], pos_mouse, 
                                game_systems['particulas'], game_systems['flashes'])
                if jogador.tiros_espingarda <= 0:
                    jogador.espingarda_ativa = False
            
            elif jogador.metralhadora_ativa and jogador.tiros_metralhadora > 0:
                atirar_metralhadora(jogador, game_systems['tiros_jogador'], pos_mouse, 
                                  game_systems['particulas'], game_systems['flashes'])
                if jogador.tiros_metralhadora <= 0:
                    jogador.metralhadora_ativa = False
            else:
                jogador.atirar_com_mouse(game_systems['tiros_jogador'], pos_mouse)
        
        elif evento.button == 3:  # Clique direito - Modo defesa do sabre
            if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                resultado_defesa = jogador.alternar_modo_defesa_sabre()
                if resultado_defesa == "modo_defesa_ativado":
                    criar_texto_flutuante("MODO DEFESA ATIVADO!", LARGURA // 2, ALTURA_JOGO // 4, 
                                         (100, 255, 100), game_systems['particulas'], 120, 32)
    
    def _processar_controles_pausa(self, evento, controles, pos_mouse, estados):
        """Processa controles durante pausa."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                estados['pausado'] = False
                pygame.mixer.unpause()
                pygame.mouse.set_visible(False)
                return None
        
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if controles['rect_menu_pausado'] and controles['rect_menu_pausado'].collidepoint(pos_mouse):
                return "menu"
        
        return None
    
    def _executar_cutscene(self, cutscene, tela, tempo_atual, relogio, gradiente_jogo, ambiente, jogador, game_systems):
        """Executa a cutscene com fundo preto."""
        return cutscene.atualizar(tempo_atual, tela, relogio)
    
    def _criar_efeito_aparicao_boss(self, boss_x, boss_y, particulas, flashes):
        """Cria efeito visual quando boss aparece."""
        for _ in range(15):
            x = boss_x + random.randint(-100, 100)
            y = boss_y + random.randint(-100, 100)
            flash = criar_explosao(x, y, (120, 0, 120), particulas, 40)
            flashes.append(flash)
    
    def _atualizar_jogo_melhorado(self, jogador, boss, inimigos, game_systems, estados, 
                                tempo_atual, pos_mouse, moeda_manager, boss_info):
        """Atualiza toda a lógica do jogo com melhorias."""
        # Tiro contínuo da metralhadora
        botoes_mouse = pygame.mouse.get_pressed()
        if (botoes_mouse[0] and not estados['jogador_morto'] and not estados['boss_derrotado'] and
            jogador.metralhadora_ativa and jogador.tiros_metralhadora > 0):
            atirar_metralhadora(jogador, game_systems['tiros_jogador'], pos_mouse, 
                              game_systems['particulas'], game_systems['flashes'])
            if jogador.tiros_metralhadora <= 0:
                jogador.metralhadora_ativa = False
        
        # Atualizar jogador
        if not estados['jogador_morto']:
            jogador.mover(estados['movimento_x'], estados['movimento_y'])
            jogador.atualizar()
            
            if jogador.y + jogador.tamanho > ALTURA_JOGO:
                jogador.y = ALTURA_JOGO - jogador.tamanho
                jogador.rect.y = jogador.y
            
            if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
                atualizar_sabre(jogador, pos_mouse, tempo_atual)
            
            atualizar_invocacoes_com_inimigos(inimigos + ([boss] if boss else []), 
                                            game_systems['particulas'], game_systems['flashes'])
        
        # Atualizar boss com sistemas melhorados
        if boss and not estados['boss_derrotado']:
            boss.atualizar(tempo_atual, jogador, inimigos)
            
            # Sistema de ataques especiais
            if estados['boss_modo_desespero'] and random.random() < 0.001:  # 0.1% chance por frame
                self._boss_ataque_desespero(boss, boss.x + boss.tamanho//2, boss.y + boss.tamanho//2, 
                                          game_systems['tiros_inimigo'], jogador)
            
            # Ataque final quando quase morto
            if boss.vidas <= 5 and not hasattr(boss, 'ataque_final_usado'):
                self._boss_ataque_fase_final(boss, boss.x + boss.tamanho//2, boss.y + boss.tamanho//2,
                                           game_systems['tiros_inimigo'], jogador, game_systems['particulas'])
                boss.ataque_final_usado = True
            
            # Atualizar presas ativas
            if hasattr(boss, 'presas_ativas') and boss.presas_ativas:
                boss.atualizar_presas_ativas(game_systems['tiros_inimigo'], 
                                            game_systems['particulas'], 
                                            game_systems['flashes'])
            
            if boss.carregando_ataque:
                if boss.desenhar_carregamento_ataque(None, tempo_atual):
                    boss.executar_ataque(game_systems['tiros_inimigo'], jogador, 
                                       game_systems['particulas'], game_systems['flashes'])
        
        # Processar tiros especiais
        self._processar_tiros_especiais_boss(game_systems['tiros_inimigo'], tempo_atual)
        
        # Atualizar inimigos invocados COM IA
        tempo_movimento_inimigos = getattr(self, '_tempo_movimento_inimigos', [])
        
        while len(tempo_movimento_inimigos) < len(inimigos):
            tempo_movimento_inimigos.append(0)
        
        for idx, inimigo in enumerate(inimigos[:]):
            if inimigo.vidas <= 0:
                inimigos.remove(inimigo)
                if idx < len(tempo_movimento_inimigos):
                    tempo_movimento_inimigos.pop(idx)
            else:
                from src.entities.inimigo_ia import atualizar_IA_inimigo
                
                intervalo_movimento = 400
                numero_fase_simulada = 10
                
                fator_tempo = jogador.obter_fator_tempo() if hasattr(jogador, 'obter_fator_tempo') else 1.0
                velocidade_original = inimigo.velocidade
                inimigo.velocidade *= fator_tempo
                
                if idx < len(tempo_movimento_inimigos):
                    tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                        inimigo, idx, jogador, game_systems['tiros_jogador'], 
                        inimigos + ([boss] if boss and not estados['boss_derrotado'] else []), 
                        tempo_atual, tempo_movimento_inimigos, intervalo_movimento, 
                        numero_fase_simulada, game_systems['tiros_inimigo'], 
                        estados['movimento_x'], estados['movimento_y'],
                        game_systems['particulas'], game_systems['flashes']
                    )
                
                inimigo.velocidade = velocidade_original
                
                if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                    inimigo.y = ALTURA_JOGO - inimigo.tamanho
                    inimigo.rect.y = inimigo.y
        
        self._tempo_movimento_inimigos = tempo_movimento_inimigos
        
        # Atualizar moedas
        moeda_manager.atualizar(jogador)
        
        # Processar tiros e colisões
        self._processar_tiros_e_colisoes(jogador, boss, inimigos, game_systems, estados, moeda_manager, boss_info)
        
        # Processar granadas e outros sistemas
        processar_granadas(game_systems['granadas'], game_systems['particulas'], game_systems['flashes'], 
                          inimigos + ([boss] if boss and not estados['boss_derrotado'] else []), moeda_manager)
        
        # Processar deflexão do sabre
        if hasattr(jogador, 'sabre_equipado') and jogador.sabre_equipado:
            tiros_refletidos = processar_deflexao_tiros(jogador, game_systems['tiros_inimigo'], 
                                                       game_systems['particulas'], game_systems['flashes'])
            game_systems['tiros_jogador'].extend(tiros_refletidos)
            
            alvos_sabre = inimigos + ([boss] if boss and not estados['boss_derrotado'] else [])
            alvos_cortados = processar_dano_sabre(jogador, alvos_sabre, 
                                                 game_systems['particulas'], game_systems['flashes'])
            
            for alvo in alvos_cortados:
                if hasattr(alvo, 'vidas') and alvo.vidas <= 0:
                    if alvo == boss:
                        moeda_manager.quantidade_moedas += 50
                    else:
                        moeda_manager.quantidade_moedas += 5
                    moeda_manager.salvar_moedas()
        
        # Atualizar efeitos visuais
        self._atualizar_efeitos_visuais(game_systems)
        
        # Verificar condições de vitória/derrota
        return self._verificar_condicoes_fim_jogo(jogador, boss, estados, game_systems, moeda_manager, boss_info)
    
    def _boss_ataque_desespero(self, boss, centro_x, centro_y, tiros_inimigo, jogador):
        """Ataque de desespero quando boss está com pouca vida."""
        print("BOSS ENTROU EM MODO DESESPERO!")
        
        # Ataque massivo em todas as direções
        for i in range(40):
            angulo = (2 * math.pi * i) / 40
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            # Múltiplas ondas
            for onda in range(3):
                velocidade = 4 + onda * 2
                start_x = centro_x + dx * onda * 30
                start_y = centro_y + dy * onda * 30
                
                from src.entities.tiro import Tiro
                tiro = Tiro(start_x, start_y, dx, dy, (255, 0, 0), velocidade)
                tiros_inimigo.append(tiro)
    
    def _boss_ataque_fase_final(self, boss, centro_x, centro_y, tiros_inimigo, jogador, particulas):
        """Ataque épico da fase final."""
        print("ATAQUE FINAL DEVASTADOR!")
        
        from src.entities.tiro import Tiro
        
        # Combinação de múltiplos ataques
        # 1. Rajada circular massiva
        for i in range(50):
            angulo = (2 * math.pi * i) / 50
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            tiro = Tiro(centro_x, centro_y, dx, dy, (255, 255, 255), 7)
            tiros_inimigo.append(tiro)
        
        # 2. Meteoros em posições estratégicas
        posicoes_meteoro = [
            (jogador.x - 50, -30), (jogador.x, -30), (jogador.x + 50, -30),
            (jogador.x - 100, -30), (jogador.x + 100, -30)
        ]
        
        for pos in posicoes_meteoro:
            meteoro = Tiro(pos[0], pos[1], 0, 1, (255, 100, 0), 8)
            meteoro.raio = 20
            tiros_inimigo.append(meteoro)
        
        # 3. Efeitos visuais épicos
        for _ in range(20):
            particula = {
                'x': centro_x + random.uniform(-100, 100),
                'y': centro_y + random.uniform(-100, 100),
                'dx': random.uniform(-5, 5),
                'dy': random.uniform(-5, 5),
                'vida': 60,
                'cor': (255, 255, 255),
                'tamanho': random.uniform(8, 15)
            }
            particulas.append(particula)
    
    def _processar_tiros_especiais_boss(self, tiros_inimigo, tempo_atual):
        """Processa tiros especiais do boss com comportamentos únicos."""
        
        for tiro in tiros_inimigo[:]:
            # Tiros orbitais (barreira de espinhos)
            if hasattr(tiro, 'orbital') and tiro.orbital:
                if hasattr(tiro, 'angulo_orbital'):
                    tiro.angulo_orbital += 0.05  # Velocidade orbital
                    tiro.x = tiro.centro_x + math.cos(tiro.angulo_orbital) * tiro.raio_orbital - tiro.raio
                    tiro.y = tiro.centro_y + math.sin(tiro.angulo_orbital) * tiro.raio_orbital - tiro.raio
                    tiro.rect.x = tiro.x
                    tiro.rect.y = tiro.y
            
            # Tiros com pulso magnético
            elif hasattr(tiro, 'pulso_magnetico') and tiro.pulso_magnetico:
                # Expandir como onda
                tiro.raio += 0.5
                if tiro.raio > 100:  # Remover quando muito grande
                    if tiro in tiros_inimigo:
                        tiros_inimigo.remove(tiro)
                    continue
            
            # Meteoros com rastro de fogo
            elif hasattr(tiro, 'raio') and tiro.raio > 10:  # Meteoros
                # Criar rastro de partículas seria implementado no sistema principal
                pass
    
    def _processar_tiros_e_colisoes(self, jogador, boss, inimigos, game_systems, estados, moeda_manager, boss_info):
        """Processa todos os tiros e colisões."""
        # Tiros do jogador
        for tiro in game_systems['tiros_jogador'][:]:
            tiro.atualizar()
            
            # Colisão com boss
            if boss and not estados['boss_derrotado'] and tiro.rect.colliderect(boss.rect):
                if boss.tomar_dano():
                    flash = criar_explosao(tiro.x, tiro.y, VERMELHO, game_systems['particulas'], 30)
                    game_systems['flashes'].append(flash)
                    pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
                    
                    moeda_manager.quantidade_moedas += 2
                    criar_texto_flutuante("+2", boss.x + boss.tamanho//2, boss.y, AMARELO, game_systems['particulas'])
                
                game_systems['tiros_jogador'].remove(tiro)
                continue
            
            # Colisão com inimigos
            for inimigo in inimigos:
                if inimigo.vidas > 0 and tiro.rect.colliderect(inimigo.rect):
                    if inimigo.tomar_dano():
                        if inimigo.vidas <= 0:
                            moeda_manager.quantidade_moedas += 3
                            moeda_manager.salvar_moedas()
                            criar_texto_flutuante("+3", inimigo.x + inimigo.tamanho//2, 
                                                inimigo.y, AMARELO, game_systems['particulas'])
                        
                        flash = criar_explosao(tiro.x, tiro.y, VERMELHO, game_systems['particulas'], 25)
                        game_systems['flashes'].append(flash)
                        pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
                    
                    game_systems['tiros_jogador'].remove(tiro)
                    break
            
            if tiro in game_systems['tiros_jogador'] and tiro.fora_da_tela():
                game_systems['tiros_jogador'].remove(tiro)
        
        # Tiros dos inimigos
        for tiro in game_systems['tiros_inimigo'][:]:
            tiro.atualizar()
            
            if not estados['jogador_morto'] and tiro.rect.colliderect(jogador.rect):
                if jogador.tomar_dano():
                    flash = criar_explosao(tiro.x, tiro.y, AZUL, game_systems['particulas'], 25)
                    game_systems['flashes'].append(flash)
                    pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                game_systems['tiros_inimigo'].remove(tiro)
                continue
            
            if tiro.fora_da_tela():
                game_systems['tiros_inimigo'].remove(tiro)
    
    def _atualizar_efeitos_visuais(self, game_systems):
        """Atualiza partículas e efeitos visuais."""
        for particula in game_systems['particulas'][:]:
            if hasattr(particula, 'atualizar'):
                if not particula.atualizar():
                    game_systems['particulas'].remove(particula)
            elif hasattr(particula, 'acabou'):
                particula.atualizar()
                if particula.acabou():
                    game_systems['particulas'].remove(particula)
        
        for flash in game_systems['flashes'][:]:
            flash['vida'] -= 1
            flash['raio'] += 2
            if flash['vida'] <= 0:
                game_systems['flashes'].remove(flash)
        
        # Atualizar efeitos especiais
        for efeito in game_systems.get('efeitos_especiais', [])[:]:
            if efeito['tipo'] == 'onda_choque':
                efeito['raio'] += efeito['velocidade']
                efeito['vida'] -= 1
                if efeito['vida'] <= 0:
                    game_systems['efeitos_especiais'].remove(efeito)
    
    def _verificar_condicoes_fim_jogo(self, jogador, boss, estados, game_systems, moeda_manager, boss_info):
        """Verifica condições de fim de jogo."""
        # Boss derrotado
        if boss and boss.vidas <= 0 and not estados['boss_derrotado']:
            estados['boss_derrotado'] = True
            jogador.invulneravel = True
            jogador.duracao_invulneravel = float('inf')
            
            # Explosões épicas
            for _ in range(10):
                x = boss.x + random.randint(-50, boss.tamanho + 50)
                y = boss.y + random.randint(-50, boss.tamanho + 50)
                flash = criar_explosao(x, y, random.choice([VERMELHO, AMARELO, LARANJA]), 
                                     game_systems['particulas'], 50)
                game_systems['flashes'].append(flash)
            
            # Mega recompensa
            moeda_manager.quantidade_moedas += boss_info['recompensa_base']
            moeda_manager.salvar_moedas()
            criar_texto_flutuante(f"{boss_info['nome'].upper()} DERROTADO! +{boss_info['recompensa_base']} MOEDAS!", 
                                 LARGURA // 2, ALTURA_JOGO // 2, 
                                 AMARELO, game_systems['particulas'], 300, 48)
            
            print(f"{boss_info['nome']} DERROTADO!")
            return "boss_derrotado"
        
        # Jogador morreu
        if jogador.vidas <= 0 and not estados['jogador_morto']:
            estados['jogador_morto'] = True
            
            # Explosões quando jogador morre
            for _ in range(5):
                x = jogador.x + random.randint(-30, 30)
                y = jogador.y + random.randint(-30, 30)
                flash = criar_explosao(x, y, VERMELHO, game_systems['particulas'], 35)
                game_systems['flashes'].append(flash)
            
            return "jogador_morto"
        
        return None
    
    def _processar_transicoes(self, transicoes):
        """Processa transições de vitória/derrota."""
        if transicoes['tempo_transicao_vitoria'] is not None:
            transicoes['tempo_transicao_vitoria'] -= 1
            if transicoes['tempo_transicao_vitoria'] <= 0:
                return "vitoria"
        
        if transicoes['tempo_transicao_derrota'] is not None:
            transicoes['tempo_transicao_derrota'] -= 1
            if transicoes['tempo_transicao_derrota'] <= 0:
                return "derrota"
        
        return None
    
    def _renderizar_boss_fight_melhorado(self, tela, estados, gradiente_jogo, ambiente, jogador, boss, 
                                       inimigos, game_systems, numero_fase, tempo_atual, moeda_manager, 
                                       transicoes, pos_mouse, controles, frames_contador):
        """Renderiza o boss fight completo com melhorias."""
        if estados['pausado']:
            self._renderizar_menu_pausa(tela, controles)
        else:
            # Fundo com efeitos especiais
            tela.fill((0, 0, 0))
            
            # Efeito de modo desespero
            if estados.get('boss_modo_desespero', False):
                # Tela vermelha pulsante
                alpha = int(50 + 30 * math.sin(frames_contador * 0.2))
                overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
                overlay.fill((100, 0, 0))
                overlay.set_alpha(alpha)
                tela.blit(overlay, (0, 0))
            
            tela.blit(gradiente_jogo, (0, 0))
            
            # Estrelas com movimento mais dinâmico
            for estrela in ambiente['estrelas']:
                velocidade_estrela = estrela[4]
                if estados.get('boss_modo_desespero', False):
                    velocidade_estrela *= 2  # Estrelas mais rápidas no modo desespero
                
                estrela[0] -= velocidade_estrela
                if estrela[0] < 0:
                    estrela[0] = LARGURA
                    estrela[1] = random.randint(0, ALTURA_JOGO)
            
            desenhar_estrelas(tela, ambiente['estrelas'])
            desenhar_grid_consistente(tela)
            
            # Efeitos especiais expandidos
            for efeito in game_systems.get('efeitos_especiais', []):
                if efeito['tipo'] == 'onda_choque':
                    pygame.draw.circle(tela, efeito['cor'], 
                                     (int(efeito['x']), int(efeito['y'])), 
                                     int(efeito['raio']), 3)
            
            # Desenhar flashes melhorados
            for flash in game_systems['flashes']:
                if flash['y'] < ALTURA_JOGO:
                    # Efeito de brilho adicional
                    for i in range(3):
                        alpha = max(0, 255 - i * 80)
                        raio_atual = int(flash['raio'] + i * 5)
                        if raio_atual > 0:
                            flash_surface = pygame.Surface((raio_atual * 2, raio_atual * 2))
                            flash_surface.set_alpha(alpha // 3)
                            flash_surface.fill(flash['cor'])
                            tela.blit(flash_surface, (flash['x'] - raio_atual, flash['y'] - raio_atual))
            
            # Desenhar jogador
            if jogador.vidas > 0:
                jogador.desenhar(tela, tempo_atual)
            
            # Desenhar boss
            if boss and not (hasattr(boss, 'vidas') and boss.vidas <= 0):
                boss.desenhar(tela, tempo_atual)
                
                # Desenhar indicador de carregamento se estiver carregando
                if hasattr(boss, 'carregando_ataque') and boss.carregando_ataque:
                    boss.desenhar_carregamento_ataque(tela, tempo_atual)
            
            # Desenhar inimigos invocados
            for inimigo in inimigos:
                if inimigo.vidas > 0:
                    inimigo.desenhar(tela, tempo_atual)
            
            # Desenhar tiros
            for tiro in game_systems['tiros_jogador']:
                tiro.desenhar(tela)
            
            for tiro in game_systems['tiros_inimigo']:
                # Desenho especial para tiros orbitais
                if hasattr(tiro, 'orbital') and tiro.orbital:
                    pygame.draw.circle(tela, (150, 150, 150), (int(tiro.x), int(tiro.y)), tiro.raio + 2)
                tiro.desenhar(tela)
            
            # Desenhar granadas
            for granada in game_systems['granadas']:
                granada.desenhar(tela)
            
            # Desenhar invocações
            desenhar_invocacoes(tela)
            
            # Desenhar partículas
            for particula in game_systems['particulas']:
                if hasattr(particula, 'desenhar'):
                    particula.desenhar(tela)
            
            # Desenhar moedas
            moeda_manager.desenhar(tela)
            
            # Desenhar efeito de tempo desacelerado
            if jogador.tem_ampulheta_ativa():
                from src.game.fase import desenhar_efeito_tempo_desacelerado
                desenhar_efeito_tempo_desacelerado(tela, True, tempo_atual)
            
            # Desenhar HUD
            inimigos_para_hud = inimigos + ([boss] if boss and hasattr(boss, 'vidas') and boss.vidas > 0 else [])
            desenhar_hud(tela, numero_fase, inimigos_para_hud, tempo_atual, moeda_manager, jogador)
            
            # Indicadores especiais
            if estados.get('boss_modo_desespero', False):
                desenhar_texto(tela, "MODO DESESPERO!", 36, (255, 0, 0), LARGURA // 2, 150)
            
            # Mensagens de transição melhoradas
            self._desenhar_mensagens_transicao_melhoradas(tela, transicoes, game_systems, estados)
            
            # Desenhar mira do mouse
            from src.utils.visual import desenhar_mira
            desenhar_mira(tela, pos_mouse)
    
    def _renderizar_menu_pausa(self, tela, controles):
        """Renderiza o menu de pausa."""
        tela.fill((0, 0, 0))
        overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
        overlay.fill((0, 0, 20))
        overlay.set_alpha(180)
        tela.blit(overlay, (0, 0))
        
        desenhar_texto(tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 - 50)
        desenhar_texto(tela, "Pressione ESC para continuar", 30, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 20)
        
        # Botão de menu
        from src.utils.visual import criar_botao
        largura_menu = 250
        altura_menu = 50
        x_menu = LARGURA // 2
        y_menu = ALTURA_JOGO // 2 + 100
        
        escala_y = ALTURA / 848
        largura_ajustada_menu = int(largura_menu * escala_y)
        altura_ajustada_menu = int(altura_menu * escala_y)
        controles['rect_menu_pausado'] = pygame.Rect(x_menu - largura_ajustada_menu // 2, 
                                                    y_menu - altura_ajustada_menu // 2, 
                                                    largura_ajustada_menu, 
                                                    altura_ajustada_menu)
        
        criar_botao(tela, "VOLTAR AO MENU", x_menu, y_menu, 
                   largura_menu, altura_menu, 
                   (120, 60, 60), (180, 80, 80), BRANCO)
    
    def _desenhar_mensagens_transicao_melhoradas(self, tela, transicoes, game_systems, estados):
        """Mensagens de transição com mais efeitos."""
        
        if transicoes['tempo_transicao_vitoria'] is not None:
            # Múltiplas mensagens de vitória
            mensagens = [
                "BOSS FUSION DESTRUÍDO!",
                "VOCÊ DOMINOU A FUSÃO!",
                "CAMPEÃO SUPREMO!"
            ]
            
            tempo_restante = transicoes['tempo_transicao_vitoria']
            duracao_total = transicoes['duracao_transicao_vitoria']
            progresso = (duracao_total - tempo_restante) / duracao_total
            
            # Mostrar mensagens em sequência
            if progresso < 0.3:
                desenhar_texto(tela, mensagens[0], 72, (0, 255, 0), LARGURA // 2, ALTURA_JOGO // 2)
            elif progresso < 0.6:
                desenhar_texto(tela, mensagens[1], 60, (255, 255, 0), LARGURA // 2, ALTURA_JOGO // 2)
            else:
                desenhar_texto(tela, mensagens[2], 84, (255, 200, 0), LARGURA // 2, ALTURA_JOGO // 2)
            
            # Fogos de artifício aleatórios
            if random.random() < 0.4:
                for _ in range(3):
                    x = random.randint(0, LARGURA)
                    y = random.randint(0, ALTURA_JOGO)
                    cor = random.choice([(0, 255, 0), (255, 255, 0), (0, 255, 255), (255, 0, 255)])
                    flash = criar_explosao(x, y, cor, game_systems['particulas'], 30)
                    game_systems['flashes'].append(flash)

        if transicoes['tempo_transicao_derrota'] is not None:
            desenhar_texto(tela, "O BOSS FUSION VENCEU!", 60, (255, 0, 0), LARGURA // 2, ALTURA_JOGO // 2)
            desenhar_texto(tela, "A fusão foi muito poderosa...", 36, (200, 0, 0), LARGURA // 2, ALTURA_JOGO // 2 + 60)
            
            # Efeito de tela escura
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
            overlay.fill((20, 0, 0))
            duracao = transicoes['duracao_transicao_derrota']
            tempo_restante = transicoes['tempo_transicao_derrota']
            alpha = int(100 * (duracao - tempo_restante) / duracao)
            overlay.set_alpha(alpha)
            tela.blit(overlay, (0, 0))


# Função de conveniência para usar o sistema
def executar_boss_fight(tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
    """
    Função de conveniência para executar um boss fight.
    """
    manager = BossFightManager()
    try:
        return manager.criar_boss_fight(tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal)
    except Exception as e:
        print(f"Erro no boss fight: {e}")
        # Garantir que música para mesmo em caso de erro
        manager.parar_musica_boss()
        return False