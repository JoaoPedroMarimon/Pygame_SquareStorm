#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema modular para fases com boss fights melhorado.
Gerencia cutscenes, boss fights e mecânicas especiais com movimentação dinâmica e novos ataques.
COM CONTROLE ADEQUADO DA MÚSICA DO BOSS.
REFATORADO: Agora herda de FaseBase para eliminar duplicação de código.
"""

import pygame
import random
import math
from src.config import *
from src.game.fase_base import FaseBase
from src.entities.particula import criar_explosao
from src.utils.visual import desenhar_texto
from src.utils.display_manager import present_frame
from src.entities.tiro import Tiro
from src.entities.inimigo_ia import atualizar_IA_inimigo
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos

# Importar classes específicas do boss
from src.entities.boss_fusion import BossFusion
from src.entities.fusion_cutscene import FusionCutscene
from src.entities.misterioso_cutscene import executar_cutscene_misterioso


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


class FaseBoss(FaseBase):
    """
    Classe para fases de boss fights.
    Herda toda a lógica comum de FaseBase e adiciona lógica específica de boss.
    """

    def __init__(self, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, boss_info, pos_jogador=None):
        """Inicializa a fase de boss.

        Args:
            pos_jogador: Tupla (x, y) com a posição inicial do jogador. Se None, usa posição padrão.
        """
        super().__init__(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador)

        self.boss_info = boss_info
        self.boss = None
        self.inimigos = []  # Inimigos invocados pelo boss

        # Sistema de cutscene
        self.cutscene = boss_info['cutscene_class']()
        self.cutscene_ativa = True

        # Sistema de dificuldade adaptativa
        self.difficulty_manager = BossDifficultyManager()

        # Estados específicos do boss
        self.boss_derrotado = False
        self.boss_modo_desespero = False
        self.combo_counter = 0

        # Gerenciamento de inimigos invocados
        self.tempo_movimento_inimigos = []

        # Configurar transições diferentes para boss
        self.duracao_transicao_vitoria = 360  # 6 segundos
        self.duracao_transicao_derrota = 240  # 4 segundos

    def executar(self):
        """
        Loop principal da fase de boss.
        Retorna: True (vitória), False (derrota) ou "menu"
        """
        tempo_atual = pygame.time.get_ticks()
        self.cutscene.iniciar(tempo_atual)

        print("Cutscene de fusão melhorada iniciada...")

        rodando = True
        frames_contador = 0

        try:
            while rodando:
                tempo_atual = self.obter_tempo_atual()
                pos_mouse = self.obter_pos_mouse()
                frames_contador += 1

                # Processar eventos
                resultado = self._processar_eventos_boss(tempo_atual, pos_mouse)
                if resultado == "sair":
                    self._parar_musica_boss()
                    self.limpar()
                    return False
                elif resultado == "menu":
                    self._parar_musica_boss()
                    self.limpar()
                    return "menu"
                elif resultado == "pular_cutscene":
                    self._terminar_cutscene()

                # Executar cutscene
                if self.cutscene_ativa:
                    if self._executar_cutscene(tempo_atual):
                        self._terminar_cutscene()
                    continue

                # Lógica principal do jogo quando não pausado
                if self.pausado:
                    self.renderizar_menu_pausa()
                    present_frame()
                    self.relogio.tick(FPS)
                    continue

                # Atualizar dificuldade adaptativa
                self.difficulty_manager.atualizar_dificuldade(tempo_atual, self.jogador, self.boss)

                # Verificar modo desespero
                if self.boss and self.boss.vidas <= 1 and not self.boss_modo_desespero:
                    self.boss_modo_desespero = True
                    self.boss.cooldown_ataque = int(self.boss.cooldown_ataque * 0.6)

                # Atualizar jogo
                resultado_jogo = self._atualizar_jogo_boss(tempo_atual, pos_mouse)

                if resultado_jogo == "boss_derrotado":
                    if self.tempo_transicao_vitoria is None:
                        self.tempo_transicao_vitoria = self.duracao_transicao_vitoria
                elif resultado_jogo == "jogador_morto":
                    if self.tempo_transicao_derrota is None:
                        self.tempo_transicao_derrota = self.duracao_transicao_derrota

                # Processar transições
                resultado_transicao = self.processar_transicoes()
                if resultado_transicao == "vitoria":
                    self._parar_musica_boss()

                    # CUTSCENE DO MISTERIOSO (apenas na fase 10 - Boss Fusion)
                    if self.numero_fase == 10:
                        print("🎬 Executando cutscene do inimigo misterioso...")
                        # Usar posição padrão de spawn do jogador
                        jogador_pos_spawn = (100, ALTURA_JOGO // 2)
                        executar_cutscene_misterioso(
                            self.tela, self.relogio, self.gradiente_jogo,
                            self.estrelas, jogador_pos_spawn
                        )

                    self.limpar()
                    return True
                elif resultado_transicao == "derrota":
                    self._parar_musica_boss()
                    self.limpar()
                    return False

                # Renderização
                self._renderizar_boss_fight(tempo_atual, pos_mouse, frames_contador)

                present_frame()
                self.relogio.tick(FPS)

        except KeyboardInterrupt:
            print("Interrupção detectada - parando música...")
            self._parar_musica_boss()
            self.limpar()
            return False

        except Exception as e:
            print(f"Erro inesperado no boss fight: {e}")
            self._parar_musica_boss()
            self.limpar()
            return False

        # Fallback final
        self._parar_musica_boss()
        self.limpar()
        return False

    def _processar_eventos_boss(self, tempo_atual, pos_mouse):
        """Processa eventos específicos do boss fight."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            # Durante cutscene
            if self.cutscene_ativa:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    return "pular_cutscene"
                continue

            # Jogo normal
            if not self.pausado and not self.jogador_morto and not self.boss_derrotado:
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

            # Menu de pausa
            elif self.pausado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        self.pausado = False
                        pygame.mixer.unpause()
                        pygame.mouse.set_visible(False)

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.rect_menu_pausado and self.rect_menu_pausado.collidepoint(pos_mouse):
                        return "menu"

        # Tiro contínuo da metralhadora
        if not self.pausado and not self.jogador_morto and not self.boss_derrotado:
            self._processar_tiro_continuo_metralhadora(pos_mouse)

        return None

    def _executar_cutscene(self, tempo_atual):
        """Executa a cutscene. Retorna True quando terminada."""
        return self.cutscene.atualizar(tempo_atual, self.tela, self.relogio)

    def _terminar_cutscene(self):
        """Finaliza a cutscene e cria o boss."""
        self.cutscene_ativa = False
        boss_x, boss_y = self.cutscene.get_boss_spawn_position()
        self.boss = self.boss_info['boss_class'](boss_x, boss_y)

        # BUGFIX: Garantir que boss começa ativo (resetar qualquer flag de congelamento)
        self.boss.congelado_por_morte_jogador = False
        self.boss.invulneravel = False
        self.boss.carregando_ataque = False

        # Efeito de aparição
        for _ in range(15):
            x = boss_x + random.randint(-100, 100)
            y = boss_y + random.randint(-100, 100)
            flash = criar_explosao(x, y, (120, 0, 120), self.particulas, 40)
            self.flashes.append(flash)

        print("Boss melhorado surgiu da fusão!")

    def _atualizar_jogo_boss(self, tempo_atual, pos_mouse):
        """Atualiza toda a lógica do boss fight."""
        # Obter fator de tempo da ampulheta
        fator_tempo = self.jogador.obter_fator_tempo()

        # Atualizar jogador
        self.atualizar_jogador(pos_mouse, tempo_atual)

        # Atualizar invocações com todos os alvos (boss + inimigos)
        alvos_totais = self.inimigos + ([self.boss] if self.boss and not self.boss_derrotado else [])
        atualizar_invocacoes_com_inimigos(alvos_totais, self.particulas, self.flashes)

        # Atualizar boss
        if self.boss and not self.boss_derrotado:
            self._atualizar_boss(tempo_atual, fator_tempo)

        # Atualizar inimigos invocados
        self._atualizar_inimigos_invocados(tempo_atual, fator_tempo)

        # Atualizar moedas
        self.atualizar_moedas()

        # Atualizar tiros
        self.atualizar_tiros_jogador(alvos_totais)
        self.atualizar_tiros_inimigo()

        # Processar sabre de luz
        self.processar_sabre_luz(alvos_totais)

        # Processar granadas
        self.processar_granadas(alvos_totais)

        # Atualizar efeitos visuais
        self.atualizar_efeitos_visuais()

        # Verificar condições de fim
        return self._verificar_condicoes_fim_boss()

    def _atualizar_boss(self, tempo_atual, fator_tempo):
        """Atualiza o boss."""
        # Aplicar fator de tempo
        velocidade_original = self.boss.velocidade
        self.boss.velocidade *= fator_tempo

        self.boss.atualizar(tempo_atual, self.jogador, self.inimigos)

        # Restaurar velocidade
        self.boss.velocidade = velocidade_original

        # Sistema de ataques especiais
        if self.boss_modo_desespero and random.random() < 0.001:
            self._boss_ataque_desespero()

        # Ataque final quando quase morto
        if self.boss.vidas <= 5 and not hasattr(self.boss, 'ataque_final_usado'):
            self._boss_ataque_fase_final()
            self.boss.ataque_final_usado = True

        # Atualizar presas ativas
        if hasattr(self.boss, 'presas_ativas') and self.boss.presas_ativas:
            self.boss.atualizar_presas_ativas(self.tiros_inimigo, self.particulas, self.flashes)

        # Sistema de carregamento de ataque
        if self.boss.carregando_ataque:
            if self.boss.desenhar_carregamento_ataque(None, tempo_atual):
                self.boss.executar_ataque(self.tiros_inimigo, self.jogador, self.particulas, self.flashes)

    def _atualizar_inimigos_invocados(self, tempo_atual, fator_tempo):
        """Atualiza inimigos invocados pelo boss com IA."""
        # Ajustar lista de tempos de movimento
        while len(self.tempo_movimento_inimigos) < len(self.inimigos):
            self.tempo_movimento_inimigos.append(0)

        for idx, inimigo in enumerate(self.inimigos[:]):
            if inimigo.vidas <= 0:
                self.inimigos.remove(inimigo)
                if idx < len(self.tempo_movimento_inimigos):
                    self.tempo_movimento_inimigos.pop(idx)
            else:
                # Aplicar fator de tempo
                velocidade_original = inimigo.velocidade
                inimigo.velocidade *= fator_tempo

                intervalo_movimento = 400
                numero_fase_simulada = 10

                alvos_totais = self.inimigos + ([self.boss] if self.boss and not self.boss_derrotado else [])

                if idx < len(self.tempo_movimento_inimigos):
                    self.tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                        inimigo, idx, self.jogador, self.tiros_jogador,
                        alvos_totais, tempo_atual, self.tempo_movimento_inimigos,
                        intervalo_movimento, numero_fase_simulada,
                        self.tiros_inimigo, self.movimento_x, self.movimento_y,
                        self.particulas, self.flashes
                    )

                # Restaurar velocidade
                inimigo.velocidade = velocidade_original

                # Limitar área de jogo
                if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                    inimigo.y = ALTURA_JOGO - inimigo.tamanho
                    inimigo.rect.y = inimigo.y

    def _boss_ataque_desespero(self):
        """Ataque de desespero quando boss está com pouca vida."""
        print("BOSS ENTROU EM MODO DESESPERO!")

        centro_x = self.boss.x + self.boss.tamanho // 2
        centro_y = self.boss.y + self.boss.tamanho // 2

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

                tiro = Tiro(start_x, start_y, dx, dy, (255, 0, 0), velocidade)
                self.tiros_inimigo.append(tiro)

    def _boss_ataque_fase_final(self):
        """Ataque épico da fase final."""
        print("ATAQUE FINAL DEVASTADOR!")

        centro_x = self.boss.x + self.boss.tamanho // 2
        centro_y = self.boss.y + self.boss.tamanho // 2

        # 1. Rajada circular massiva
        for i in range(50):
            angulo = (2 * math.pi * i) / 50
            dx = math.cos(angulo)
            dy = math.sin(angulo)

            tiro = Tiro(centro_x, centro_y, dx, dy, (255, 255, 255), 7)
            self.tiros_inimigo.append(tiro)

        # 2. Meteoros em posições estratégicas
        posicoes_meteoro = [
            (self.jogador.x - 50, -30), (self.jogador.x, -30), (self.jogador.x + 50, -30),
            (self.jogador.x - 100, -30), (self.jogador.x + 100, -30)
        ]

        for pos in posicoes_meteoro:
            meteoro = Tiro(pos[0], pos[1], 0, 1, (255, 100, 0), 8)
            meteoro.raio = 20
            self.tiros_inimigo.append(meteoro)

    def _verificar_condicoes_fim_boss(self):
        """Verifica condições de fim do boss fight."""
        # Jogador morreu - VERIFICAR PRIMEIRO para tornar boss imune
        if self.verificar_jogador_morto():
            # BUGFIX: Congelar boss temporariamente (será resetado ao reiniciar fase)
            if self.boss and not self.boss_derrotado:
                self.boss.congelado_por_morte_jogador = True
                self.boss.invulneravel = True
                # Marcar para que não possa mais morrer
                self.boss.vidas = max(self.boss.vidas, 1)  # Garantir pelo menos 1 vida
            return "jogador_morto"

        # Boss derrotado
        if self.boss and self.boss.vidas <= 0 and not self.boss_derrotado:
            self.boss_derrotado = True
            self.jogador.invulneravel = True
            self.jogador.duracao_invulneravel = float('inf')

            # Explosões épicas
            for _ in range(10):
                x = self.boss.x + random.randint(-50, self.boss.tamanho + 50)
                y = self.boss.y + random.randint(-50, self.boss.tamanho + 50)
                flash = criar_explosao(x, y, random.choice([VERMELHO, AMARELO, LARANJA]),
                                      self.particulas, 50)
                self.flashes.append(flash)

            # Mega recompensa
            from src.utils.visual import criar_texto_flutuante
            self.moeda_manager.quantidade_moedas += self.boss_info['recompensa_base']
            self.moeda_manager.salvar_moedas()
            criar_texto_flutuante(f"{self.boss_info['nome'].upper()} DERROTADO! +{self.boss_info['recompensa_base']} MOEDAS!",
                                 LARGURA // 2, ALTURA_JOGO // 2,
                                 AMARELO, self.particulas, 300, 48)

            print(f"{self.boss_info['nome']} DERROTADO!")
            return "boss_derrotado"

        return None

    def _renderizar_boss_fight(self, tempo_atual, pos_mouse, frames_contador):
        """Renderiza o boss fight completo."""
        # Fundo com efeitos especiais
        self.tela.fill((0, 0, 0))

        # Efeito de modo desespero
        if self.boss_modo_desespero:
            alpha = int(50 + 30 * math.sin(frames_contador * 0.2))
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
            overlay.fill((100, 0, 0))
            overlay.set_alpha(alpha)
            self.tela.blit(overlay, (0, 0))

        self.renderizar_fundo()

        # Alvos para desenhar
        alvos = self.inimigos + ([self.boss] if self.boss and self.boss.vidas > 0 else [])

        # Flashes melhorados
        self._desenhar_flashes_melhorados()

        # Objetos do jogo
        self.renderizar_objetos_jogo(tempo_atual, alvos)

        # Boss com carregamento de ataque
        if self.boss and self.boss.vidas > 0:
            if hasattr(self.boss, 'carregando_ataque') and self.boss.carregando_ataque:
                self.boss.desenhar_carregamento_ataque(self.tela, tempo_atual)

        # HUD
        self.renderizar_hud(tempo_atual, alvos)

        # Indicadores especiais

        # Mensagens de transição
        self._desenhar_mensagens_transicao_boss()

        # Mira
        self.renderizar_mira(pos_mouse)

    def _desenhar_flashes_melhorados(self):
        """Desenha flashes com efeito de brilho adicional."""
        for flash in self.flashes:
            if flash['y'] < ALTURA_JOGO:
                for i in range(3):
                    alpha = max(0, 255 - i * 80)
                    raio_atual = int(flash['raio'] + i * 5)
                    if raio_atual > 0:
                        flash_surface = pygame.Surface((raio_atual * 2, raio_atual * 2))
                        flash_surface.set_alpha(alpha // 3)
                        flash_surface.fill(flash['cor'])
                        self.tela.blit(flash_surface, (flash['x'] - raio_atual, flash['y'] - raio_atual))

    def _desenhar_mensagens_transicao_boss(self):
        """Desenha mensagens de transição específicas do boss."""
        if self.tempo_transicao_vitoria is not None:
            mensagens = [
                "BOSS FUSION DESTRUÍDO!",
                "VOCÊ DOMINOU A FUSÃO!",
                "CAMPEÃO SUPREMO!"
            ]

            tempo_restante = self.tempo_transicao_vitoria
            duracao_total = self.duracao_transicao_vitoria
            progresso = (duracao_total - tempo_restante) / duracao_total

            # Mostrar mensagens em sequência
            if progresso < 0.3:
                desenhar_texto(self.tela, mensagens[0], 72, (0, 255, 0), LARGURA // 2, ALTURA_JOGO // 2)
            elif progresso < 0.6:
                desenhar_texto(self.tela, mensagens[1], 60, (255, 255, 0), LARGURA // 2, ALTURA_JOGO // 2)
            else:
                desenhar_texto(self.tela, mensagens[2], 84, (255, 200, 0), LARGURA // 2, ALTURA_JOGO // 2)

            # Fogos de artifício
            if random.random() < 0.4:
                for _ in range(3):
                    x = random.randint(0, LARGURA)
                    y = random.randint(0, ALTURA_JOGO)
                    cor = random.choice([(0, 255, 0), (255, 255, 0), (0, 255, 255), (255, 0, 255)])
                    flash = criar_explosao(x, y, cor, self.particulas, 30)
                    self.flashes.append(flash)

        if self.tempo_transicao_derrota is not None:
            desenhar_texto(self.tela, "O BOSS FUSION VENCEU!", 60, (255, 0, 0), LARGURA // 2, ALTURA_JOGO // 2)
            desenhar_texto(self.tela, "A fusão foi muito poderosa...", 36, (200, 0, 0), LARGURA // 2, ALTURA_JOGO // 2 + 60)

            # Efeito de tela escura
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
            overlay.fill((20, 0, 0))
            duracao = self.duracao_transicao_derrota
            tempo_restante = self.tempo_transicao_derrota
            alpha = int(100 * (duracao - tempo_restante) / duracao)
            overlay.set_alpha(alpha)
            self.tela.blit(overlay, (0, 0))

    def _parar_musica_boss(self):
        """Para a música do boss."""
        try:
            if hasattr(self.cutscene, 'parar_musica_definitivamente'):
                self.cutscene.parar_musica_definitivamente()
            else:
                pygame.mixer.music.stop()
            print("Música do boss parada!")
        except Exception as e:
            print(f"Erro ao parar música do boss: {e}")


class BossFightManager:
    """
    Gerenciador central para boss fights.
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

    def criar_boss_fight(self, tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador=None):
        """Cria e executa um boss fight do tipo especificado.

        Args:
            pos_jogador: Tupla (x, y) com a posição inicial do jogador. Se None, usa posição padrão.
        """
        if tipo_boss not in self.boss_types:
            print(f"Tipo de boss '{tipo_boss}' não encontrado!")
            return False

        boss_info = self.boss_types[tipo_boss]

        # Parar qualquer música anterior
        try:
            pygame.mixer.music.stop()
        except:
            pass

        # Criar e executar fase de boss
        fase_boss = FaseBoss(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, boss_info, pos_jogador)
        return fase_boss.executar()


# Função de conveniência para usar o sistema
def executar_boss_fight(tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador=None):
    """Função de conveniência para executar um boss fight.

    Args:
        pos_jogador: Tupla (x, y) com a posição inicial do jogador. Se None, usa posição padrão.
    """
    manager = BossFightManager()
    try:
        return manager.criar_boss_fight(tipo_boss, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador)
    except Exception as e:
        print(f"Erro no boss fight: {e}")
        # Garantir que música para mesmo em caso de erro
        try:
            pygame.mixer.music.stop()
        except:
            pass
        return False
