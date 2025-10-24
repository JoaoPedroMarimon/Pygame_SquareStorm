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
from src.utils.visual import criar_estrelas, desenhar_texto, criar_texto_flutuante, desenhar_estrelas, desenhar_grid_consistente, criar_botao
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
from src.weapons.sabre_luz import processar_deflexao_tiros, atualizar_sabre, processar_dano_sabre
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos, desenhar_invocacoes, limpar_invocacoes
from src.items.amuleto import usar_amuleto_para_invocacao
from src.items.ampulheta import usar_ampulheta, desenhar_efeito_tempo_desacelerado


class FaseBase:
    """
    Classe base para todas as fases do jogo.
    Contém toda a lógica compartilhada de controles, combate, renderização, etc.
    """

    def __init__(self, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
        """Inicializa a fase base."""
        self.tela = tela
        self.relogio = relogio
        self.numero_fase = numero_fase
        self.gradiente_jogo = gradiente_jogo
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.fonte_pequena = pygame.font.SysFont("Arial", 18)

        # Criar jogador
        self.jogador = Quadrado(100, ALTURA_JOGO // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)

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

    def _inicializar_ambiente(self):
        """Inicializa elementos visuais do ambiente."""
        self.estrelas = criar_estrelas(NUM_ESTRELAS_JOGO)

    def _inicializar_controles(self):
        """Inicializa sistema de controles."""
        pygame.mouse.set_visible(False)
        self.mira_surface, self.mira_rect = criar_mira(12, BRANCO, AMARELO)
        self.rect_menu_pausado = None
        self.ultimo_clique_mouse = 0
        self.intervalo_minimo_clique = 100

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
        pos_mouse = convert_mouse_position(pygame.mouse.get_pos())

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            # Controles durante o jogo
            if not self.mostrando_inicio and not self.pausado and not self.jogador_morto and not self.em_congelamento:
                resultado = self._processar_controles_jogo(evento, tempo_atual, pos_mouse)
                if resultado:
                    return resultado

            # Controles durante pausa
            elif self.pausado:
                resultado = self._processar_controles_pausa(evento, pos_mouse)
                if resultado:
                    return resultado

        # Tiro contínuo da metralhadora
        if not self.mostrando_inicio and not self.pausado and not self.jogador_morto and not self.em_congelamento:
            self._processar_tiro_continuo_metralhadora(pos_mouse)

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
                self.pausado = True
                pygame.mixer.pause()
                pygame.mouse.set_visible(True)
            elif evento.key == pygame.K_e:
                self._processar_ativacao_arma()
            elif evento.key == pygame.K_q:
                self._processar_ativacao_item()

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
        """Processa ativação de armas (Tecla E)."""
        resultado = self.jogador.ativar_arma_inventario()

        mensagens = {
            "espingarda": ("ESPINGARDA EQUIPADA!", AMARELO, 32),
            "metralhadora": ("METRALHADORA EQUIPADA!", LARANJA, 32),
            "desert_eagle": ("DESERT EAGLE EQUIPADA!", (200, 180, 100), 32),
            "sabre_luz": ("SABRE DE LUZ EQUIPADO!", (150, 150, 255), 32),
            "guardada": ("ARMA GUARDADA!", CINZA_ESCURO, 32),
            "granada_guardada": ("GRANADA GUARDADA!", CINZA_ESCURO, 32),
            "nenhuma_selecionada": ("SELECIONE UMA ARMA NO INVENTÁRIO!", VERMELHO, 32),
            "sem_municao": ("ARMA SEM MUNIÇÃO!", VERMELHO, 32)
        }

        if resultado in mensagens:
            texto, cor, tamanho = mensagens[resultado]
            criar_texto_flutuante(texto, LARGURA // 2, ALTURA_JOGO // 4, cor, self.particulas, 120, tamanho)

    def _processar_ativacao_item(self):
        """Processa ativação de itens (Tecla Q)."""
        resultado = self.jogador.ativar_items_inventario()

        mensagens = {
            "granada_toggle": ("GRANADA ATIVADA!", VERDE, 32),
            "granada_guardada": ("GRANADA GUARDADA!", CINZA_ESCURO, 32),
            "ampulheta_toggle": ("AMPULHETA PRONTA!", (150, 200, 255), 32),
            "ampulheta_guardada": ("AMPULHETA GUARDADA!", CINZA_ESCURO, 32),
            "ampulheta_ja_ativa": ("AMPULHETA JÁ ESTÁ ATIVA!", AMARELO, 32),
            "amuleto_toggle": ("AMULETO MÍSTICO ATIVADO!", (200, 150, 255), 32),
            "amuleto_guardado": ("AMULETO GUARDADO!", CINZA_ESCURO, 32),
            "sem_facas": ("SEM COMBAT KNIFE!", VERMELHO, 32),
            "sem_granadas": ("SEM GRANADAS!", VERMELHO, 32),
            "sem_ampulhetas": ("SEM AMPULHETAS!", VERMELHO, 32),
            "nenhum_item_selecionado": ("SELECIONE UM ITEM NO INVENTÁRIO!", AMARELO, 32)
        }

        if resultado in mensagens:
            texto, cor, tamanho = mensagens[resultado]
            criar_texto_flutuante(texto, LARGURA // 2, ALTURA_JOGO // 4, cor, self.particulas, 120, tamanho)

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

            # PRIORIDADE 3: Ampulheta
            elif hasattr(self.jogador, 'ampulheta_selecionada') and self.jogador.ampulheta_selecionada:
                if usar_ampulheta(self.jogador, self.particulas, self.flashes):
                    criar_texto_flutuante("TEMPO DESACELERADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (150, 200, 255), self.particulas, 180, 48)
                else:
                    if self.jogador.tempo_desacelerado:
                        criar_texto_flutuante("AMPULHETA JÁ ATIVA!", LARGURA // 2, ALTURA_JOGO // 4,
                                             AMARELO, self.particulas, 120, 32)

            # PRIORIDADE 4: Sabre de Luz (ativar/desativar)
            elif hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
                resultado_sabre = self.jogador.ativar_sabre_luz()
                if resultado_sabre == "sabre_ativado":
                    criar_texto_flutuante("SABRE ATIVADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (150, 150, 255), self.particulas, 120, 32)
                elif resultado_sabre == "sabre_desativado":
                    criar_texto_flutuante("SABRE DESATIVADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (100, 100, 150), self.particulas, 120, 32)

            # PRIORIDADE 5: Espingarda
            elif self.jogador.espingarda_ativa and self.jogador.tiros_espingarda > 0:
                atirar_espingarda(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_espingarda <= 0:
                    self.jogador.espingarda_ativa = False
                    criar_texto_flutuante("ESPINGARDA SEM MUNIÇÃO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         VERMELHO, self.particulas, 120, 32)

            # PRIORIDADE 6: Desert Eagle
            elif self.jogador.desert_eagle_ativa and self.jogador.tiros_desert_eagle > 0:
                atirar_desert_eagle(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_desert_eagle <= 0:
                    self.jogador.desert_eagle_ativa = False
                    criar_texto_flutuante("DESERT EAGLE SEM MUNIÇÃO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         VERMELHO, self.particulas, 120, 32)

            # PRIORIDADE 7: Metralhadora
            elif self.jogador.metralhadora_ativa and self.jogador.tiros_metralhadora > 0:
                atirar_metralhadora(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_metralhadora <= 0:
                    self.jogador.metralhadora_ativa = False
                    criar_texto_flutuante("METRALHADORA SEM MUNIÇÃO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         VERMELHO, self.particulas, 120, 32)

            # PRIORIDADE 8: Tiro normal
            else:
                self.jogador.atirar_com_mouse(self.tiros_jogador, pos_mouse)

        elif evento.button == 3:  # Clique direito - Modo defesa do sabre
            if hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
                resultado_defesa = self.jogador.alternar_modo_defesa_sabre()
                if resultado_defesa == "modo_defesa_ativado":
                    criar_texto_flutuante("MODO DEFESA ATIVADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (100, 255, 100), self.particulas, 120, 32)
                elif resultado_defesa == "modo_defesa_desativado":
                    criar_texto_flutuante("MODO DEFESA DESATIVADO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         (150, 150, 255), self.particulas, 120, 32)

    def _processar_tiro_continuo_metralhadora(self, pos_mouse):
        """Processa tiro contínuo quando botão do mouse está pressionado."""
        botoes_mouse = pygame.mouse.get_pressed()
        if botoes_mouse[0]:  # Botão esquerdo pressionado
            if self.jogador.metralhadora_ativa and self.jogador.tiros_metralhadora > 0:
                atirar_metralhadora(self.jogador, self.tiros_jogador, pos_mouse, self.particulas, self.flashes)
                if self.jogador.tiros_metralhadora <= 0:
                    self.jogador.metralhadora_ativa = False
                    criar_texto_flutuante("METRALHADORA SEM MUNIÇÃO!", LARGURA // 2, ALTURA_JOGO // 4,
                                         VERMELHO, self.particulas, 120, 32)

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

            # Atualizar sabre de luz
            if hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado:
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

            # Remover tiros que saíram da tela
            if tiro.fora_da_tela():
                self.tiros_inimigo.remove(tiro)

    def processar_sabre_luz(self, alvos):
        """
        Processa deflexão de tiros e dano do sabre de luz.
        alvos: lista de inimigos/boss para aplicar dano
        """
        if not (hasattr(self.jogador, 'sabre_equipado') and self.jogador.sabre_equipado):
            return

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
        processar_granadas(self.granadas, self.particulas, self.flashes, alvos, self.moeda_manager)

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

        # Estrelas
        for estrela in self.estrelas:
            estrela[0] -= estrela[4]  # Mover com base na velocidade
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA_JOGO)

    def _calcular_moedas_alvo(self, alvo):
        """Calcula quantas moedas um alvo deve dar."""
        # Boss ou entidades sem atributo 'cor' (usam cor_principal)
        if not hasattr(alvo, 'cor'):
            # Boss ou entidade especial - dar moedas baseado em vidas
            if hasattr(alvo, 'vidas_max'):
                return max(10, alvo.vidas_max // 2)  # Boss dá muitas moedas
            return 10

        # Inimigos normais com cor
        if alvo.cor == ROXO:
            return 5
        elif alvo.cor == CIANO:
            return 8
        elif hasattr(alvo, 'vidas_max') and alvo.vidas_max > 1:
            return 2
        return 1

    # ==================== RENDERIZAÇÃO ====================

    def renderizar_fundo(self):
        """Renderiza o fundo do jogo."""
        self.tela.fill((0, 0, 0))
        self.tela.blit(self.gradiente_jogo, (0, 0))
        desenhar_estrelas(self.tela, self.estrelas)
        desenhar_grid_consistente(self.tela)

    def renderizar_objetos_jogo(self, tempo_atual, alvos):
        """
        Renderiza todos os objetos do jogo.
        alvos: lista de inimigos/boss para desenhar
        """
        # Flashes
        for flash in self.flashes:
            if flash['y'] < ALTURA_JOGO:
                pygame.draw.circle(self.tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))

        # Jogador
        if self.jogador.vidas > 0:
            self.jogador.desenhar(self.tela, tempo_atual)

        # Alvos (inimigos/boss)
        for alvo in alvos:
            if alvo.vidas > 0:
                alvo.desenhar(self.tela, tempo_atual)

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

    def renderizar_hud(self, tempo_atual, alvos):
        """Renderiza o HUD."""
        desenhar_hud(self.tela, self.numero_fase, alvos, tempo_atual, self.moeda_manager, self.jogador)

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
        """Retorna a posição do mouse convertida."""
        return convert_mouse_position(pygame.mouse.get_pos())

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
        """Limpa recursos da fase."""
        limpar_invocacoes()
