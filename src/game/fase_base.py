#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe base para todas as fases do jogo.
Contém toda a lógica compartilhada entre fases normais e boss fights.
"""

import pygame
import random
import math
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.visual import criar_estrelas, desenhar_texto, criar_texto_flutuante, desenhar_estrelas, criar_botao, criar_relampagos, desenhar_relampago
from src.utils.sound import gerar_som_explosao, gerar_som_dano
from src.game.moeda_manager import MoedaManager
from src.ui.hud import desenhar_hud
from src.utils.display_manager import present_frame, convert_mouse_position
from src.utils.visual import desenhar_mira, criar_mira

# Importações das armas e itens
from src.items.granada import Granada, lancar_granada, processar_granadas, inicializar_sistema_granadas, obter_intervalo_lancamento
from src.weapons.espingarda import atirar_espingarda
from src.weapons.metralhadora import atirar_metralhadora
from src.weapons.desert_eagle import atirar_desert_eagle
from src.weapons.sniper import atirar_sniper
from src.weapons.sabre_luz import processar_deflexao_tiros, atualizar_sabre, processar_dano_sabre
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos, desenhar_invocacoes, desenhar_invocacoes_background, limpar_invocacoes
from src.items.amuleto import usar_amuleto_para_invocacao
from src.items.ampulheta import usar_ampulheta, desenhar_efeito_tempo_desacelerado


class FaseBase:
    """
    Classe base para todas as fases do jogo.
    Contém toda a lógica compartilhada de controles, combate, renderização, etc.
    """

    def __init__(self, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador=None):
        """Inicializa a fase base.

        Args:
            pos_jogador: Tupla (x, y) com a posição inicial do jogador. Se None, usa posição padrão.
        """
        self.tela = tela
        self.relogio = relogio
        self.numero_fase = numero_fase
        self.gradiente_jogo = gradiente_jogo
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.fonte_pequena = pygame.font.SysFont("Arial", 18)

        # Criar jogador na posição especificada ou padrão
        if pos_jogador:
            jogador_x, jogador_y = pos_jogador
        else:
            jogador_x, jogador_y = 100, ALTURA_JOGO // 2

        self.jogador = Quadrado(jogador_x, jogador_y, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)

        # Gerenciador de moedas
        self.moeda_manager = MoedaManager()

        # Sistemas de jogo
        self._inicializar_sistemas_jogo()

        # Estados do jogo
        self._inicializar_estados()

        # Ambiente visual
        self._inicializar_ambiente()

        # Controles
        self._inicializar_controles()

        # Transições
        self._inicializar_transicoes()

    def _inicializar_sistemas_jogo(self):
        """Inicializa todos os sistemas de jogo (tiros, granadas, partículas, etc.)."""
        self.tiros_jogador = []
        self.tiros_inimigo = []
        self.particulas = []
        self.flashes = []

        # Sistema de granadas
        self.granadas, self.tempo_ultimo_lancamento_granada = inicializar_sistema_granadas()
        self.intervalo_lancamento_granada = obter_intervalo_lancamento()

    def _inicializar_estados(self):
        """Inicializa estados do jogo."""
        self.pausado = False
        self.jogador_morto = False
        self.movimento_x = 0
        self.movimento_y = 0
        self.mostrando_inicio = True
        self.contador_inicio = 120  # 2 segundos a 60 FPS
        self.em_congelamento = False
        self.tempo_congelamento = 240  # 4 segundos a 60 FPS
        self.fade_in = 255

        # Sistema de animação dos espinhos
        self.animacao_espinhos_iniciada = False
        self.tempo_inicio_animacao_espinhos = 0
        self.duracao_animacao_espinhos = 240  # 4 segundos a 60 FPS (duração completa do congelamento)

    def _inicializar_ambiente(self):
        """Inicializa elementos visuais do ambiente."""
        if self.numero_fase >= 26:
            # === TEMA AQUÁTICO (fases 26+) ===
            self.tema_aquatico = True
            # Sinalizar ao jogador que está em zona aquática (para máscara de mergulho)
            self.jogador.tema_aquatico = True

            # Peixes decorativos de fundo (usam mesma estrutura das estrelas)
            self.estrelas = self._criar_peixes_fundo()

            # Sistema de bolhas ambiente
            self.bolhas_ambiente = self._criar_bolhas_ambiente()

            # Sem relâmpagos nem espinhos
            self.relampago_ativo = False
            self.proximo_relampago = None
            self.espinhos = []

        elif self.numero_fase >= 11:
            self.tema_aquatico = False
            # Cores tóxicas: roxo, vermelho, verde
            cores_toxicas = [
                (150, 100, 255),  # Roxo
                (255, 100, 100),  # Vermelho
                (100, 255, 150),  # Verde
                (200, 150, 255),  # Roxo claro
                (255, 150, 100),  # Laranja/vermelho
                (150, 255, 100),  # Verde ácido
            ]
            self.estrelas = criar_estrelas(NUM_ESTRELAS_JOGO, cores_tematicas=cores_toxicas)

            # Sistema de relâmpagos para fases tóxicas
            self.relampago_ativo = False
            self.tempo_inicio_relampago = 0
            self.duracao_relampago = 0
            self.proximo_relampago = None

            # Sistema de espinhos para fases 11-20
            from src.entities.espinho import criar_espinhos_bordas
            self.espinhos = criar_espinhos_bordas(espessura=30)
        else:
            self.tema_aquatico = False
            # Estrelas brancas padrão
            self.estrelas = criar_estrelas(NUM_ESTRELAS_JOGO)
            self.relampago_ativo = False
            self.proximo_relampago = None
            self.espinhos = []  # Sem espinhos nas fases 1-10

    def _criar_peixes_fundo(self):
        """Cria peixes triangulares decorativos de fundo para o tema aquático."""
        cores_peixe = [
            (0, 130, 180),    # Azul oceano
            (40, 170, 215),   # Azul claro
            (0, 180, 120),    # Verde-água
            (20, 200, 160),   # Turquesa
            (255, 160, 40),   # Laranja
            (255, 210, 60),   # Amarelo
            (200, 80, 200),   # Roxo
            (220, 50, 50),    # Vermelho
            (60, 200, 80),    # Verde
            (255, 120, 180),  # Rosa
            (160, 100, 255),  # Lilás
            (255, 140, 0),    # Âmbar
        ]
        peixes = []
        for _ in range(NUM_ESTRELAS_JOGO):
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA_JOGO)
            tamanho = random.uniform(4, 9)
            brilho = random.randint(120, 210)
            vel = random.uniform(0.25, 1.1)
            cor = random.choice(cores_peixe)
            peixes.append([x, y, tamanho, brilho, vel, cor])
        return peixes

    def _criar_bolhas_ambiente(self):
        """Cria bolhas decorativas que sobem pelo cenário aquático."""
        bolhas = []
        for _ in range(45):
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA_JOGO)
            raio = random.uniform(2, 9)
            vel_y = random.uniform(0.25, 0.9)
            bolhas.append([x, y, raio, vel_y])
        return bolhas

    def _inicializar_controles(self):
        """Inicializa sistema de controles."""
        pygame.mouse.set_visible(False)
        self.mira_surface, self.mira_rect = criar_mira(12, BRANCO, AMARELO)
        self.rect_menu_pausado = None
        self.ultimo_clique_mouse = 0
        self.intervalo_minimo_clique = 100

        # Joystick (Trimui via Moonlight)
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Mira virtual (unifica mouse e analógico direito)
        self.mira_virtual_x = float(LARGURA // 2)
        self.mira_virtual_y = float(ALTURA_JOGO // 2)
        self.velocidade_mira_joystick = 8
        self.ultimo_disparo_joystick = 0
        self._botao_dash_anterior = False
        self._botao_arma_anterior = False
        self._botao_item_anterior = False
        self._botao_pause_anterior = False

    def _inicializar_transicoes(self):
        """Inicializa transições de vitória/derrota."""
        self.tempo_transicao_vitoria = None
        self.tempo_transicao_derrota = None
        self.duracao_transicao_vitoria = 180  # 3 segundos a 60 FPS
        self.duracao_transicao_derrota = 120  # 2 segundos a 60 FPS

    # ==================== CONTROLES E EVENTOS ====================

    def processar_eventos(self):
        """
        Processa todos os eventos do jogo.
        Retorna: "sair", "menu" ou None
        """
        tempo_atual = pygame.time.get_ticks()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            # Atualiza mira virtual com movimento real do mouse
            if evento.type == pygame.MOUSEMOTION:
                mx, my = convert_mouse_position(evento.pos)
                self.mira_virtual_x = float(mx)
                self.mira_virtual_y = float(my)

            # Controles durante o jogo (permitir movimento durante vitória, bloquear apenas durante derrota)
            if (not self.mostrando_inicio and not self.pausado and not self.jogador_morto and
                not self.em_congelamento and self.tempo_transicao_derrota is None):
                pos_mouse = self.obter_pos_mouse()
                resultado = self._processar_controles_jogo(evento, tempo_atual, pos_mouse)
                if resultado:
                    return resultado

            # Controles durante pausa
            elif self.pausado:
                pos_mouse = self.obter_pos_mouse()
                resultado = self._processar_controles_pausa(evento, pos_mouse)
                if resultado:
                    return resultado

        pos_mouse = self.obter_pos_mouse()

        # Tiro contínuo da metralhadora (permitir durante vitória)
        if (not self.mostrando_inicio and not self.pausado and not self.jogador_morto and
            not self.em_congelamento and self.tempo_transicao_derrota is None):
            self._processar_joystick(tempo_atual)
            self._processar_tiro_continuo_metralhadora(pos_mouse)
            self._processar_mira_sniper()

        return None

    def _processar_controles_jogo(self, evento, tempo_atual, pos_mouse):
        """Processa controles durante o jogo."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_w:
                self.movimento_y = -1
            elif evento.key == pygame.K_s:
                self.movimento_y = 1
            elif evento.key == pygame.K_a:
                self.movimento_x = -1
            elif evento.key == pygame.K_d:
                self.movimento_x = 1
            elif evento.key == pygame.K_ESCAPE:
                # Não permitir pause durante transição de derrota (permitir durante vitória)
                if self.tempo_transicao_derrota is None:
                    self.pausado = True
                    pygame.mixer.pause()
                    pygame.mouse.set_visible(True)
            elif evento.key == pygame.K_e:
                self._processar_ativacao_arma()
            elif evento.key == pygame.K_q:
                self._processar_ativacao_item()
            elif evento.key == pygame.K_SPACE:
                # Executar dash
                if hasattr(self.jogador, 'executar_dash'):
                    if self.jogador.executar_dash():
                        # Dash executado com sucesso
                        criar_texto_flutuante(f"",
                                            LARGURA // 2, ALTURA_JOGO // 4,
                                            (100, 200, 255), self.particulas, 60, 24)
                    elif self.jogador.dash_uses <= 0:
                        criar_texto_flutuante("", LARGURA // 2, ALTURA_JOGO // 4,
                                            VERMELHO, self.particulas, 60, 24)

        elif evento.type == pygame.KEYUP:
            if evento.key == pygame.K_w and self.movimento_y < 0:
                self.movimento_y = 0
            elif evento.key == pygame.K_s and self.movimento_y > 0:
                self.movimento_y = 0
            elif evento.key == pygame.K_a and self.movimento_x < 0:
                self.movimento_x = 0
            elif evento.key == pygame.K_d and self.movimento_x > 0:
                self.movimento_x = 0

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if tempo_atual - self.ultimo_clique_mouse >= self.intervalo_minimo_clique:
                self.ultimo_clique_mouse = tempo_atual
                self._processar_ataques_mouse(evento, pos_mouse, tempo_atual)

        return None

    def _processar_ativacao_arma(self):
        """Processa ativação de armas (Tecla E) - sem feedback visual."""
        resultado = self.jogador.ativar_arma_inventario()
        # Sem mensagens na tela - apenas executa a ação

    def _processar_ativacao_item(self):
        """Processa ativação de itens (Tecla Q) - sem feedback visual."""
        resultado = self.jogador.ativar_items_inventario()
        # Sem mensagens na tela - apenas executa a ação

    def _processar_ataques_mouse(self, evento, pos_mouse, tempo_atual):
        """Processa ataques com mouse (sistema de prioridade)."""
        if evento.button == 1:  # Clique esquerdo
            # PRIORIDADE 1: Invocação do Chucky (amuleto ativo)
            if (hasattr(self.jogador, 'amuleto_ativo') and self.jogador.amuleto_ativo and
                hasattr(self.jogador, 'facas') and self.jogador.facas > 0):
                if usar_amuleto_para_invocacao(pos_mouse, self.jogador):
                    criar_texto_flutuante("CHUCKY INVOCADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (255, 50, 50), self.particulas, 180, 36)
                    if self.jogador.facas <= 0:
                        criar_texto_flutuante("AMULETO SEM ENERGIA!", LARGURA // 2, ALTURA_JOGO // 4 + 50,
                                             VERMELHO, self.particulas, 120, 28)
                else:
                    criar_texto_flutuante("JÁ EXISTE UMA INVOCAÇÃO ATIVA!", LARGURA // 2, ALTURA_JOGO // 4,
                                         AMARELO, self.particulas, 120, 24)

            # PRIORIDADE 2: Granada
            elif self.jogador.granada_selecionada and self.jogador.granadas > 0:
                if tempo_atual - self.tempo_ultimo_lancamento_granada >= self.intervalo_lancamento_granada:
                    self.tempo_ultimo_lancamento_granada = tempo_atual
                    lancar_granada(self.jogador, self.granadas, pos_mouse, self.particulas, self.flashes)

            # PRIORIDADE 3: Dimensional Hop
            elif hasattr(self.jogador, 'dimensional_hop_selecionado') and self.jogador.dimensional_hop_selecionado and self.jogador.dimensional_hop_uses > 0:
                if self.jogador.dimensional_hop_obj:
                    if self.jogador.dimensional_hop_obj.usar(self.jogador, pos_mouse, self.particulas, self.flashes):
                        self.jogador.dimensional_hop_uses -= 1

                        # Desativar se não tiver mais usos
                        if self.jogador.dimensional_hop_uses <= 0:
                            self.jogador.dimensional_hop_selecionado = False
                            if self.jogador.dimensional_hop_obj:
                                self.jogador.dimensional_hop_obj.desativar()

            # PRIORIDADE 4: Ampulheta
            elif hasattr(self.jogador, 'ampulheta_selecionada') and self.jogador.ampulheta_selecionada:
                if usar_ampulheta(self.jogador, self.particulas, self.flashes):
                    criar_texto_flutuante("TEMPO DESACELERADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (150, 200, 255), self.particulas, 180, 48)
                else:
                    if self.jogador.tempo_desacelerado:
                        criar_texto_flutuante("AMPULHETA JÁ ATIVA!", LARGURA // 2, ALTURA_JOGO // 4,
                                             AMARELO, self.particulas, 120, 32)

            # PRIORIDADE 5: Sabre de Luz (ativar, arremessar ou retornar)
            elif hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
                from src.weapons.sabre_luz import arremessar_sabre, forcar_retorno_sabre

                # Se o sabre está arremessado, forçar retorno imediato
                if self.jogador.sabre_info.get('arremessado', False):
                    forcar_retorno_sabre(self.jogador)
                # Se o sabre está ativo mas não arremessado, arremessar
                elif self.jogador.sabre_info.get('ativo', False):
                    arremessar_sabre(self.jogador, pos_mouse)
                # Se o sabre não está ativo, ativar
                else:
                    self.jogador.ativar_sabre_luz()

            # PRIORIDADE 5: Espingarda
            elif self.jogador.espingarda_ativa and self.jogador.tiros_espingarda > 0:
                atirar_espingarda(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_espingarda <= 0:
                    self.jogador.espingarda_ativa = False


            # PRIORIDADE 5.5: SPAS-12
            elif self.jogador.spas12_ativa and self.jogador.tiros_spas12 > 0:
                from src.weapons.spas12 import atirar_spas12
                atirar_spas12(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_spas12 <= 0:
                    self.jogador.spas12_ativa = False


            # PRIORIDADE 6: Desert Eagle
            elif self.jogador.desert_eagle_ativa and self.jogador.tiros_desert_eagle > 0:
                atirar_desert_eagle(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_desert_eagle <= 0:
                    self.jogador.desert_eagle_ativa = False

            # PRIORIDADE 6.5: Sniper
            elif self.jogador.sniper_ativa and self.jogador.tiros_sniper > 0:
                # Sniper usa o estado sniper_mirando para determinar precisão
                atirar_sniper(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes,
                             mirando=self.jogador.sniper_mirando)
                if self.jogador.tiros_sniper <= 0:
                    self.jogador.sniper_ativa = False
                    self.jogador.sniper_mirando = False

            # PRIORIDADE 7: Metralhadora
            elif self.jogador.metralhadora_ativa and self.jogador.tiros_metralhadora > 0:
                atirar_metralhadora(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_metralhadora <= 0:
                    self.jogador.metralhadora_ativa = False


            # PRIORIDADE 8: Tiro normal
            else:
                self.jogador.atirar_com_mouse(self.tiros_jogador, pos_mouse)

        elif evento.button == 3:  # Clique direito - Modo defesa do sabre
            if hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
                resultado_defesa = self.jogador.alternar_modo_defesa_sabre()
            # Nota: Mira da sniper é processada continuamente em _processar_mira_sniper()


    def _processar_tiro_continuo_metralhadora(self, pos_mouse):
        """Processa tiro contínuo quando botão do mouse ou gatilho do joystick está pressionado."""
        botoes_mouse = pygame.mouse.get_pressed()
        gatilho_joystick = False
        if self.joystick and self.joystick.get_numaxes() > 5:
            gatilho_joystick = self.joystick.get_axis(5) > 0.5
        if botoes_mouse[0] or gatilho_joystick:
            if self.jogador.metralhadora_ativa and self.jogador.tiros_metralhadora > 0:
                atirar_metralhadora(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_metralhadora <= 0:
                    self.jogador.metralhadora_ativa = False

    def _processar_mira_sniper(self):
        """Processa mira da sniper - ativa enquanto botão direito ou L1/L2 está pressionado."""
        if hasattr(self.jogador, 'sniper_ativa') and self.jogador.sniper_ativa:
            botoes_mouse = pygame.mouse.get_pressed()
            mirando_mouse = botoes_mouse[2]
            mirando_joystick = False
            if self.joystick:
                gatilho_esq = self.joystick.get_axis(4) if self.joystick.get_numaxes() > 4 else 0
                botao_l1 = self.joystick.get_button(4) if self.joystick.get_numbuttons() > 4 else False
                mirando_joystick = gatilho_esq > 0.5 or botao_l1
            self.jogador.sniper_mirando = mirando_mouse or mirando_joystick

    def _processar_joystick(self, tempo_atual):
        """Processa entrada do controle (Trimui via Moonlight). Coexiste com teclado/mouse."""
        # Tentar conectar joystick se plugado depois
        if not self.joystick:
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
            return

        dead_zone = 0.2

        # === MOVIMENTO (analógico esquerdo) — só aplica se WASD não estiver pressionado ===
        teclas = pygame.key.get_pressed()
        usando_teclado = teclas[pygame.K_w] or teclas[pygame.K_s] or teclas[pygame.K_a] or teclas[pygame.K_d]
        if not usando_teclado:
            eixo_x = self.joystick.get_axis(0)
            eixo_y = self.joystick.get_axis(1)
            self.movimento_x = (1 if eixo_x > dead_zone else -1 if eixo_x < -dead_zone else 0)
            self.movimento_y = (1 if eixo_y > dead_zone else -1 if eixo_y < -dead_zone else 0)

        # === MIRA (analógico direito) ===
        if self.joystick.get_numaxes() > 3:
            eixo_mira_x = self.joystick.get_axis(2)
            eixo_mira_y = self.joystick.get_axis(3)
            if abs(eixo_mira_x) > dead_zone:
                self.mira_virtual_x += eixo_mira_x * self.velocidade_mira_joystick
            if abs(eixo_mira_y) > dead_zone:
                self.mira_virtual_y += eixo_mira_y * self.velocidade_mira_joystick
            self.mira_virtual_x = max(0.0, min(float(LARGURA), self.mira_virtual_x))
            self.mira_virtual_y = max(0.0, min(float(ALTURA_JOGO), self.mira_virtual_y))

        pos_mira = self.obter_pos_mouse()
        num_botoes = self.joystick.get_numbuttons()
        num_eixos = self.joystick.get_numaxes()

        # === ATIRAR (R1=botão 5 ou R2=eixo 5) ===
        gatilho_dir = self.joystick.get_axis(5) if num_eixos > 5 else 0
        botao_r1 = self.joystick.get_button(5) if num_botoes > 5 else False
        if gatilho_dir > 0.5 or botao_r1:
            if tempo_atual - self.ultimo_disparo_joystick >= self.intervalo_minimo_clique:
                self.ultimo_disparo_joystick = tempo_atual
                evento_fake = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_mira)
                self._processar_ataques_mouse(evento_fake, pos_mira, tempo_atual)

        # === DASH (botão Sul/A = 0) — disparo único por pressionamento ===
        botao_dash = self.joystick.get_button(0) if num_botoes > 0 else False
        if botao_dash and not self._botao_dash_anterior:
            if hasattr(self.jogador, 'executar_dash'):
                self.jogador.executar_dash()
        self._botao_dash_anterior = botao_dash

        # === ATIVAR ARMA (botão Leste/B = 1) ===
        botao_arma = self.joystick.get_button(1) if num_botoes > 1 else False
        if botao_arma and not self._botao_arma_anterior:
            self._processar_ativacao_arma()
        self._botao_arma_anterior = botao_arma

        # === ATIVAR ITEM (botão Oeste/X = 2) ===
        botao_item = self.joystick.get_button(2) if num_botoes > 2 else False
        if botao_item and not self._botao_item_anterior:
            self._processar_ativacao_item()
        self._botao_item_anterior = botao_item

        # === PAUSE (Start = botão 9 ou 7) ===
        botao_pause = ((self.joystick.get_button(9) if num_botoes > 9 else False) or
                       (self.joystick.get_button(7) if num_botoes > 7 else False))
        if botao_pause and not self._botao_pause_anterior:
            if self.tempo_transicao_derrota is None:
                self.pausado = True
                pygame.mixer.pause()
                pygame.mouse.set_visible(True)
        self._botao_pause_anterior = botao_pause

    def _processar_controles_pausa(self, evento, pos_mouse):
        """Processa controles durante pausa."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.pausado = False
                pygame.mixer.unpause()
                pygame.mouse.set_visible(False)

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect_menu_pausado and self.rect_menu_pausado.collidepoint(pos_mouse):
                return "menu"

        return None

    # ==================== ATUALIZAÇÃO DO JOGO ====================

    def atualizar_jogador(self, pos_mouse, tempo_atual):
        """Atualiza o jogador."""
        if not self.jogador_morto:
            self.jogador.mover(self.movimento_x, self.movimento_y)
            self.jogador.atualizar()

            # Garantir que o jogador não ultrapasse a área de jogo
            if self.jogador.y + self.jogador.tamanho > ALTURA_JOGO:
                self.jogador.y = ALTURA_JOGO - self.jogador.tamanho
                self.jogador.rect.y = self.jogador.y

            # Verificar colisão com espinhos (dano de 1 vida para fases 11+)
            # Não causar dano durante transição de vitória
            if self.numero_fase >= 11 and not self.jogador.invulneravel and self.tempo_transicao_vitoria is None:
                for espinho in self.espinhos:
                    if self.jogador.rect.colliderect(espinho.rect):
                        # Aplicar dano (usa o sistema de invulnerabilidade do jogador)
                        if self.jogador.tomar_dano():
                            # Efeitos visuais de dano
                            flash = criar_explosao(self.jogador.x + self.jogador.tamanho // 2,
                                                   self.jogador.y + self.jogador.tamanho // 2,
                                                   VERMELHO, self.particulas, 30)
                            self.flashes.append(flash)
                            from src.utils.sound import gerar_som_dano
                            pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                        break

            # Atualizar sabre de luz
            if hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
                from src.weapons.sabre_luz import atualizar_sabre_arremessado

                # Atualizar sabre arremessado (se aplicável)
                atualizar_sabre_arremessado(self.jogador, tempo_atual)

                # Atualizar sabre normal
                atualizar_sabre(self.jogador, pos_mouse, tempo_atual)

    def atualizar_tiros_jogador(self, alvos):
        """
        Atualiza tiros do jogador e verifica colisões.
        alvos: lista de inimigos/boss para verificar colisão
        """
        for tiro in self.tiros_jogador[:]:
            tiro.atualizar()

            # Verificar colisão com os alvos
            for alvo in alvos:
                if alvo.vidas <= 0:
                    continue

                if tiro.rect.colliderect(alvo.rect):
                    # Verificar se o alvo está invulnerável (fantasma invisível)
                    if hasattr(alvo, 'esta_invulneravel') and alvo.esta_invulneravel():
                        continue  # Fantasma invisível é invulnerável, ignorar tiro

                    # Obter dano do tiro (padrão: 1)
                    dano = getattr(tiro, 'dano', 1)
                    dano_causou_morte = (alvo.vidas <= dano)

                    if alvo.tomar_dano(dano):
                        # Se o alvo morreu, adicionar moedas
                        if dano_causou_morte:
                            moedas_bonus = self._calcular_moedas_alvo(alvo)
                            self.moeda_manager.quantidade_moedas += moedas_bonus
                            self.moeda_manager.salvar_moedas()
                            criar_texto_flutuante(f"+{moedas_bonus}", alvo.x + alvo.tamanho//2,
                                                 alvo.y, AMARELO, self.particulas)

                            # Se é um perseguidor, criar explosão grande (como granada)
                            if hasattr(alvo, 'perseguidor') and alvo.perseguidor:
                                import math
                                import random
                                from src.entities.tiro import Tiro

                                centro_explosao_x = alvo.x + alvo.tamanho//2
                                centro_explosao_y = alvo.y + alvo.tamanho//2
                                raio_explosao_dano = 150  # Mesmo raio da granada

                                # Cores da explosão
                                cores = [(255, 100, 0), (255, 200, 0), (255, 50, 0)]

                                # Criar várias explosões em sucessão
                                for i in range(3):
                                    offset_x = random.uniform(-10, 10)
                                    offset_y = random.uniform(-10, 10)
                                    flash = criar_explosao(centro_explosao_x + offset_x,
                                                         centro_explosao_y + offset_y,
                                                         random.choice(cores), self.particulas, 40)
                                    self.flashes.append(flash)

                                # Explosão central maior
                                flash_principal = {
                                    'x': centro_explosao_x,
                                    'y': centro_explosao_y,
                                    'raio': 60,
                                    'vida': 20,
                                    'cor': (255, 255, 200)
                                }
                                self.flashes.append(flash_principal)

                                # Criar projéteis em círculo (como granada)
                                num_projeteis = 8
                                velocidade_projetil = 8

                                for i in range(num_projeteis):
                                    angulo = (2 * math.pi * i) / num_projeteis
                                    dx = math.cos(angulo)
                                    dy = math.sin(angulo)
                                    cor_projetil = (255, 150, 0)  # Laranja fogo
                                    projetil = Tiro(centro_explosao_x, centro_explosao_y, dx, dy, cor_projetil, velocidade_projetil)
                                    self.tiros_inimigo.append(projetil)

                        # Efeitos visuais
                        flash = criar_explosao(tiro.x, tiro.y, VERMELHO, self.particulas, 25)
                        self.flashes.append(flash)
                        pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))

                    self.tiros_jogador.remove(tiro)
                    break

            # Remover tiros que saíram da tela
            if tiro in self.tiros_jogador and tiro.fora_da_tela():
                self.tiros_jogador.remove(tiro)

    def atualizar_tiros_inimigo(self):
        """Atualiza tiros dos inimigos e verifica colisão com jogador."""
        # Obter fator de tempo da ampulheta
        fator_tempo = self.jogador.obter_fator_tempo() if hasattr(self.jogador, 'obter_fator_tempo') else 1.0

        for tiro in self.tiros_inimigo[:]:
            # Aplicar fator de tempo
            velocidade_original = tiro.velocidade
            tiro.velocidade *= fator_tempo

            tiro.atualizar()

            # Restaurar velocidade
            tiro.velocidade = velocidade_original

            # Verificar colisão com jogador
            if not self.jogador_morto and tiro.rect.colliderect(self.jogador.rect):
                if self.jogador.tomar_dano():
                    flash = criar_explosao(tiro.x, tiro.y, AZUL, self.particulas, 25)
                    self.flashes.append(flash)
                    pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                self.tiros_inimigo.remove(tiro)
                continue

            # Ricochete nas paredes (bolhas do peixe)
            if getattr(tiro, 'ricochete', False):
                tiro.vida_ricochete = getattr(tiro, 'vida_ricochete', 420) - 1
                if tiro.vida_ricochete <= 0:
                    self.tiros_inimigo.remove(tiro)
                    continue
                if tiro.x < tiro.raio:
                    tiro.x = tiro.raio
                    tiro.dx = abs(tiro.dx)
                elif tiro.x > LARGURA - tiro.raio:
                    tiro.x = LARGURA - tiro.raio
                    tiro.dx = -abs(tiro.dx)
                if tiro.y < tiro.raio:
                    tiro.y = tiro.raio
                    tiro.dy = abs(tiro.dy)
                elif tiro.y > ALTURA_JOGO - tiro.raio:
                    tiro.y = ALTURA_JOGO - tiro.raio
                    tiro.dy = -abs(tiro.dy)
                tiro.rect.x = tiro.x - tiro.raio
                tiro.rect.y = tiro.y - tiro.raio
                continue

            # Remover tiros que saíram da tela
            if tiro.fora_da_tela():
                self.tiros_inimigo.remove(tiro)

    def processar_sabre_luz(self, alvos):
        """
        Processa deflexão de tiros e dano do sabre de luz (normal e arremessado).
        alvos: lista de inimigos/boss para aplicar dano
        """
        if not (hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado):
            return

        from src.weapons.sabre_luz import processar_dano_sabre_arremessado, processar_deflexao_sabre_arremessado

        # Processar sabre arremessado (dano E deflexão)
        if self.jogador.sabre_info.get('arremessado', False):
            # Deflexão de tiros pelo sabre arremessado
            tiros_refletidos = processar_deflexao_sabre_arremessado(self.jogador, self.tiros_inimigo, self.particulas, self.flashes)
            self.tiros_jogador.extend(tiros_refletidos)

            # Dano nos inimigos
            alvos_cortados = processar_dano_sabre_arremessado(self.jogador, alvos, self.particulas, self.flashes)

            # Adicionar moedas pelos alvos mortos pelo sabre arremessado
            for alvo in alvos_cortados:
                if alvo.vidas <= 0:
                    moedas_bonus = self._calcular_moedas_alvo(alvo)
                    self.moeda_manager.quantidade_moedas += moedas_bonus
                    self.moeda_manager.salvar_moedas()
                    criar_texto_flutuante(f"+{moedas_bonus}", alvo.x + alvo.tamanho//2,
                                         alvo.y, AMARELO, self.particulas)
        else:
            # Sabre normal (não arremessado)
            # Deflexão de tiros
            tiros_refletidos = processar_deflexao_tiros(self.jogador, self.tiros_inimigo, self.particulas, self.flashes)
            self.tiros_jogador.extend(tiros_refletidos)

            # Dano do sabre nos alvos
            alvos_cortados = processar_dano_sabre(self.jogador, alvos, self.particulas, self.flashes)

            # Adicionar moedas pelos alvos mortos
            for alvo in alvos_cortados:
                if alvo.vidas <= 0:
                    moedas_bonus = self._calcular_moedas_alvo(alvo)
                    self.moeda_manager.quantidade_moedas += moedas_bonus
                    self.moeda_manager.salvar_moedas()
                    criar_texto_flutuante(f"+{moedas_bonus}", alvo.x + alvo.tamanho//2,
                                         alvo.y, AMARELO, self.particulas)

    def processar_granadas(self, alvos):
        """Processa granadas."""
        processar_granadas(self.granadas, self.particulas, self.flashes, alvos, self.moeda_manager, self.tiros_jogador, self.jogador, self.tiros_inimigo)

    def atualizar_efeitos_visuais(self):
        """Atualiza partículas, flashes e estrelas."""
        # Partículas
        for particula in self.particulas[:]:
            particula.atualizar()
            if particula.acabou():
                self.particulas.remove(particula)

        # Flashes
        for flash in self.flashes[:]:
            flash['vida'] -= 1
            flash['raio'] += 2
            if flash['vida'] <= 0:
                self.flashes.remove(flash)

        # Estrelas / peixes de fundo
        for estrela in self.estrelas:
            estrela[0] -= estrela[4]  # Mover com base na velocidade
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA_JOGO)

        # Bolhas ambiente (tema aquático)
        if hasattr(self, 'bolhas_ambiente'):
            for bolha in self.bolhas_ambiente:
                bolha[1] -= bolha[3]  # Subir
                if bolha[1] < -bolha[2]:
                    bolha[1] = float(ALTURA_JOGO) + bolha[2]
                    bolha[0] = float(random.randint(0, LARGURA))

    def _calcular_moedas_alvo(self, alvo):
        """Calcula quantas moedas um alvo deve dar."""
        # Boss ou entidades sem atributo 'cor' (usam cor_principal)
        if not hasattr(alvo, 'cor'):
            # Boss ou entidade especial - dar moedas baseado em vidas
            if hasattr(alvo, 'vidas_max'):
                return max(10, alvo.vidas_max // 2)  # Boss dá muitas moedas
            return 10

        # Inimigos especiais
        if hasattr(alvo, 'tipo_mago') and alvo.tipo_mago:
            return 15  # Mago dá 10 moedas
        elif hasattr(alvo, 'tipo_metralhadora') and alvo.tipo_metralhadora:
            return 10  # Inimigo metralhadora dá 7 moedas
        elif hasattr(alvo, 'perseguidor') and alvo.perseguidor:
            return 8  # Perseguidor dá 6 moedas

        # Inimigos normais com cor
        if alvo.cor == ROXO:
            return 5
        elif alvo.cor == CIANO:
            return 8
        elif hasattr(alvo, 'vidas_max') and alvo.vidas_max > 1:
            return 2
        return 1

    # ==================== RENDERIZAÇÃO ====================

    def _desenhar_peixes_fundo(self):
        """Desenha peixes decorativos de fundo no estilo do inimigo peixe."""
        # Ângulo fixo = π (todos nadam para a esquerda)
        # Com cos_a=-1, sin_a=0: pt(fx,fy) = (cx - fx, cy - fy)
        for peixe in self.estrelas:
            x, y, tamanho, cor = peixe[0], peixe[1], peixe[2], peixe[5]
            cx, cy = int(x), int(y)
            if cx < -tamanho * 3 or cx > LARGURA + tamanho * 3:
                continue
            if cy < -tamanho * 2 or cy > ALTURA_JOGO + tamanho * 2:
                continue

            s = float(tamanho)
            esc = tuple(max(0, c - 50) for c in cor)

            # === CAUDA BIFURCADA ===
            cauda_raiz = (cx + s * 0.35, cy)
            cauda_top  = (cx + s * 1.05, cy + s * 0.65)
            cauda_mid  = (cx + s * 0.65, cy)
            cauda_bot  = (cx + s * 1.05, cy - s * 0.65)
            pygame.draw.polygon(self.tela, esc, [cauda_raiz, cauda_top, cauda_mid])
            pygame.draw.polygon(self.tela, esc, [cauda_raiz, cauda_bot, cauda_mid])
            pygame.draw.polygon(self.tela, cor, [
                cauda_raiz, (cx + s * 0.95, cy + s * 0.48), (cx + s * 0.60, cy)])
            pygame.draw.polygon(self.tela, cor, [
                cauda_raiz, (cx + s * 0.95, cy - s * 0.48), (cx + s * 0.60, cy)])

            # === CORPO TRIANGULAR ===
            pygame.draw.polygon(self.tela, esc, [
                (cx - s,       cy),
                (cx + s * 0.4, cy - s * 0.8),
                (cx + s * 0.4, cy + s * 0.8),
            ])
            pygame.draw.polygon(self.tela, cor, [
                (cx - s * 0.82, cy),
                (cx + s * 0.32, cy - s * 0.62),
                (cx + s * 0.32, cy + s * 0.62),
            ])

            # === NADADEIRA DORSAL (só para peixes maiores) ===
            if s >= 9:
                pygame.draw.polygon(self.tela, esc, [
                    (cx - s * 0.1,  cy + s * 0.78),
                    (cx - s * 0.35, cy + s * 1.25),
                    (cx + s * 0.2,  cy + s * 0.78),
                ])
                pygame.draw.polygon(self.tela, cor, [
                    (cx - s * 0.1,  cy + s * 0.78),
                    (cx - s * 0.30, cy + s * 1.1),
                    (cx + s * 0.12, cy + s * 0.78),
                ])

            # === LINHA LATERAL ===
            if s >= 6:
                pygame.draw.line(self.tela, esc,
                                 (int(cx - s * 0.75), cy),
                                 (int(cx + s * 0.3),  cy), 1)

    def _desenhar_bolhas_ambiente(self):
        """Desenha as bolhas decorativas do fundo aquático."""
        for bolha in self.bolhas_ambiente:
            x, y, raio = bolha[0], bolha[1], bolha[2]
            ix, iy, ir = int(x), int(y), max(1, int(raio))
            if 0 <= ix <= LARGURA and 0 <= iy <= ALTURA_JOGO:
                # Anel da bolha
                pygame.draw.circle(self.tela, (160, 215, 250), (ix, iy), ir, 1)
                # Reflexo
                shine_x = ix - max(1, ir // 3)
                shine_y = iy - max(1, ir // 3)
                pygame.draw.circle(self.tela, (220, 245, 255), (shine_x, shine_y), max(1, ir // 4))

    def renderizar_fundo(self):
        """Renderiza o fundo do jogo."""
        self.tela.fill((0, 0, 0))
        self.tela.blit(self.gradiente_jogo, (0, 0))

        # Tema aquático (fases 26+)
        if hasattr(self, 'tema_aquatico') and self.tema_aquatico:
            self._desenhar_peixes_fundo()
            self._desenhar_bolhas_ambiente()
            return

        desenhar_estrelas(self.tela, self.estrelas)

        # Sistema de relâmpagos para fases 11+
        if self.numero_fase >= 11:
            tempo_atual = pygame.time.get_ticks()

            # Verificar se deve criar um novo relâmpago
            if not self.relampago_ativo:
                deve_criar, self.proximo_relampago, duracao = criar_relampagos(
                    tempo_atual, self.proximo_relampago, 3000, 8000
                )
                if deve_criar:
                    self.relampago_ativo = True
                    self.tempo_inicio_relampago = tempo_atual
                    self.duracao_relampago = duracao

            # Desenhar relâmpago se estiver ativo
            if self.relampago_ativo:
                ainda_ativo = desenhar_relampago(
                    self.tela,
                    self.tempo_inicio_relampago,
                    self.duracao_relampago,
                    cor_flash=(200, 255, 200)  # Verde tóxico
                )
                if not ainda_ativo:
                    self.relampago_ativo = False

    def renderizar_objetos_jogo(self, tempo_atual, alvos):
        """
        Renderiza todos os objetos do jogo.
        alvos: lista de inimigos/boss para desenhar
        """
        # Flashes
        for flash in self.flashes:
            if flash['y'] < ALTURA_JOGO:
                pygame.draw.circle(self.tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))

        # Espinhos (desenhar primeiro para ficar no fundo)
        if self.numero_fase >= 11:
            for espinho in self.espinhos:
                espinho.desenhar(self.tela, tempo_atual)

        # Pentagrama e portal das invocações (na camada de fundo, abaixo de tudo)
        desenhar_invocacoes_background(self.tela)

        # Jogador
        if self.jogador.vidas > 0:
            self.jogador.desenhar(self.tela, tempo_atual)

        # Alvos (inimigos/boss)
        for alvo in alvos:
            if alvo.vidas > 0:
                alvo.desenhar(self.tela, tempo_atual)
                # Se for inimigo metralhadora, desenhar a arma
                if hasattr(alvo, 'tipo_metralhadora') and alvo.tipo_metralhadora:
                    alvo.desenhar_metralhadora_inimigo(self.tela, tempo_atual, self.jogador)
                # Se for inimigo mago, desenhar o cajado
                elif hasattr(alvo, 'tipo_mago') and alvo.tipo_mago:
                    alvo.desenhar_cajado(self.tela, tempo_atual, self.jogador)
                # Se for inimigo granada, desenhar o lançador
                elif hasattr(alvo, 'tipo_granada') and alvo.tipo_granada:
                    alvo.desenhar_equipamento_granada(self.tela, tempo_atual, self.jogador)

        # Tiros
        for tiro in self.tiros_jogador:
            tiro.desenhar(self.tela)

        for tiro in self.tiros_inimigo:
            tiro.desenhar(self.tela)

        # Granadas
        for granada in self.granadas:
            granada.desenhar(self.tela)

        # Invocações
        desenhar_invocacoes(self.tela)

        # Partículas
        for particula in self.particulas:
            particula.desenhar(self.tela)

        # Moedas
        self.moeda_manager.desenhar(self.tela)

        # Efeito de tempo desacelerado
        desenhar_efeito_tempo_desacelerado(self.tela, self.jogador.tem_ampulheta_ativa(), tempo_atual)

    def renderizar_hud(self, tempo_atual, alvos, show_content=True):
        """Renderiza o HUD."""
        desenhar_hud(self.tela, self.numero_fase, alvos, tempo_atual, self.moeda_manager, self.jogador,
                     apenas_fundo=(not show_content))

    def renderizar_mira(self, pos_mouse):
        """Renderiza a mira do mouse."""
        if not self.em_congelamento:
            desenhar_mira(self.tela, pos_mouse, (self.mira_surface, self.mira_rect))

    def renderizar_menu_pausa(self):
        """Renderiza o menu de pausa."""
        self.tela.fill((0, 0, 0))
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.fill((0, 0, 20))
        overlay.set_alpha(180)
        self.tela.blit(overlay, (0, 0))

        desenhar_texto(self.tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 - 50)
        desenhar_texto(self.tela, "Pressione ESC para continuar", 30, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 20)

        # Botão de menu
        largura_menu = 250
        altura_menu = 50
        x_menu = LARGURA // 2
        y_menu = ALTURA_JOGO // 2 + 100

        escala_y = ALTURA / 848
        largura_ajustada_menu = int(largura_menu * escala_y)
        altura_ajustada_menu = int(altura_menu * escala_y)
        self.rect_menu_pausado = pygame.Rect(x_menu - largura_ajustada_menu // 2,
                                              y_menu - altura_ajustada_menu // 2,
                                              largura_ajustada_menu,
                                              altura_ajustada_menu)

        criar_botao(self.tela, "VOLTAR AO MENU", x_menu, y_menu,
                   largura_menu, altura_menu,
                   (120, 60, 60), (180, 80, 80), BRANCO)

    # ==================== UTILITÁRIOS ====================

    def obter_tempo_atual(self):
        """Retorna o tempo atual do jogo."""
        return pygame.time.get_ticks()

    def obter_pos_mouse(self):
        """Retorna a posição da mira virtual (unifica mouse e analógico direito do joystick)."""
        return (int(self.mira_virtual_x), int(self.mira_virtual_y))

    def atualizar_moedas(self):
        """Atualiza e verifica coleta de moedas."""
        self.moeda_manager.atualizar(self.jogador)

    def verificar_jogador_morto(self):
        """Verifica se o jogador morreu e inicia transição."""
        if self.jogador.vidas <= 0 and not self.jogador_morto:
            self.jogador_morto = True
            self.movimento_x = 0
            self.movimento_y = 0

            # Explosões quando jogador morrer
            for _ in range(5):
                x = self.jogador.x + random.randint(-30, 30)
                y = self.jogador.y + random.randint(-30, 30)
                flash = criar_explosao(x, y, VERMELHO, self.particulas, 35)
                self.flashes.append(flash)

            pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))

            if self.tempo_transicao_derrota is None:
                self.tempo_transicao_derrota = self.duracao_transicao_derrota

            return True
        return False

    def processar_transicoes(self):
        """
        Processa transições de vitória/derrota.
        Retorna: "vitoria", "derrota" ou None
        """
        if self.tempo_transicao_vitoria is not None:
            self.tempo_transicao_vitoria -= 1
            if self.tempo_transicao_vitoria <= 0:
                return "vitoria"

        if self.tempo_transicao_derrota is not None:
            self.tempo_transicao_derrota -= 1
            if self.tempo_transicao_derrota <= 0:
                return "derrota"

        return None

    def limpar(self):
        """Limpa recursos da fase e salva munições."""
        # Salvar munições atuais do jogador (sistema permanente)
        from src.game.municao_manager import salvar_todas_municoes
        salvar_todas_municoes(self.jogador)

        # Limpar invocações
        limpar_invocacoes()
