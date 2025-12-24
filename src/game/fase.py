#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a lógica das fases normais do jogo.
Sistema corrigido: E=equipar arma, Q=granada, mouse=tiro com prioridade.
REFATORADO: Agora herda de FaseBase para eliminar duplicação de código.
"""

import pygame
import random
import math
from src.config import *
from src.game.fase_base import FaseBase
from src.game.nivel_factory import NivelFactory
from src.utils.visual import desenhar_texto
from src.utils.display_manager import present_frame
from src.entities.inimigo_ia import atualizar_IA_inimigo
from src.items.chucky_invocation import atualizar_invocacoes_com_inimigos

# Importação do sistema modular de boss fights
from src.game.fase_boss import executar_boss_fight


class FaseNormal(FaseBase):
    """
    Classe para fases normais do jogo.
    Herda toda a lógica comum de FaseBase.
    """

    def __init__(self, tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, inimigos, pos_jogador=None):
        """Inicializa a fase normal com inimigos específicos.

        Args:
            pos_jogador: Tupla (x, y) com a posição inicial do jogador. Se None, usa posição padrão.
        """
        super().__init__(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, pos_jogador)
        self.inimigos = inimigos if inimigos else []

        # Tempos para a IA dos inimigos
        self.tempo_movimento_inimigos = [0] * len(self.inimigos)
        self.intervalo_movimento = max(300, 600 - numero_fase * 30)  # Reduz com a fase

    def executar(self):
        """
        Loop principal da fase normal.
        Retorna: True (vitória), False (derrota) ou "menu"
        """
        rodando = True

        while rodando:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse = self.obter_pos_mouse()

            # Mostrar/ocultar cursor dependendo do estado
            if not self.mostrando_inicio and not self.pausado:
                pygame.mouse.set_visible(False)
            else:
                pygame.mouse.set_visible(True)

            # Processar eventos
            resultado = self.processar_eventos()
            if resultado == "sair":
                self.limpar()
                return False
            elif resultado == "menu":
                self.limpar()
                return "menu"

            # Atualizar contador de introdução
            if self.mostrando_inicio:
                self._mostrar_introducao(tempo_atual)
                continue

            # Lógica de congelamento
            if self.em_congelamento:
                self._mostrar_congelamento(tempo_atual)
                continue

            # Efeito de fade in
            if self.fade_in > 0:
                self.fade_in = max(0, self.fade_in - 10)

            # Se pausado, mostrar menu de pausa
            if self.pausado:
                self.renderizar_menu_pausa()
                present_frame()
                self.relogio.tick(FPS)
                continue

            # Obter fator de tempo da ampulheta
            fator_tempo = self.jogador.obter_fator_tempo()

            # Atualizar jogador
            self.atualizar_jogador(pos_mouse, tempo_atual)
            atualizar_invocacoes_com_inimigos(self.inimigos, self.particulas, self.flashes)

            # Atualizar moedas
            self.atualizar_moedas()

            # Atualizar IA dos inimigos
            self._atualizar_inimigos(tempo_atual, fator_tempo)

            # Atualizar tiros
            self.atualizar_tiros_jogador(self.inimigos)
            self.atualizar_tiros_inimigo()

            # Processar sabre de luz
            self.processar_sabre_luz(self.inimigos)

            # Processar granadas
            self.processar_granadas(self.inimigos)

            # Atualizar efeitos visuais
            self.atualizar_efeitos_visuais()

            # Verificar condições de vitória/derrota
            resultado_condicao = self._verificar_condicoes_fim()
            if resultado_condicao == "vitoria":
                self.limpar()
                return True
            elif resultado_condicao == "derrota":
                self.limpar()
                return False

            # Processar transições
            resultado_transicao = self.processar_transicoes()
            if resultado_transicao == "vitoria":
                self.limpar()
                return True
            elif resultado_transicao == "derrota":
                self.limpar()
                return False

            # Renderização
            self._renderizar_fase(tempo_atual, pos_mouse)

            present_frame()
            self.relogio.tick(FPS)

        self.limpar()
        return False

    def _mostrar_introducao(self, tempo_atual):
        """Mostra a tela de introdução da fase."""
        self.contador_inicio -= 1
        if self.contador_inicio <= 0:
            self.mostrando_inicio = False
            self.em_congelamento = True

        self.tela.fill((0, 0, 0))
        self.tela.blit(self.gradiente_jogo, (0, 0))

        # Desenhar estrelas
        from src.utils.visual import desenhar_estrelas
        desenhar_estrelas(self.tela, self.estrelas)

        # Texto de introdução com efeito
        tamanho = 70 + int(math.sin(tempo_atual / 200) * 5)
        desenhar_texto(self.tela, f"FASE {self.numero_fase}", tamanho, BRANCO, LARGURA // 2, ALTURA_JOGO // 3)
        desenhar_texto(self.tela, f"{len(self.inimigos)} inimigo{'s' if len(self.inimigos) > 1 else ''} para derrotar",
                      36, AMARELO, LARGURA // 2, ALTURA_JOGO // 2)
        desenhar_texto(self.tela, "Preparado?", 30, BRANCO, LARGURA // 2, ALTURA_JOGO * 2 // 3)

        present_frame()
        self.relogio.tick(FPS)

    def _mostrar_congelamento(self, tempo_atual):
        """Mostra a tela de congelamento antes do início."""
        self.tempo_congelamento -= 1

        self.tela.fill((0, 0, 0))
        self.tela.blit(self.gradiente_jogo, (0, 0))

        from src.utils.visual import desenhar_estrelas
        desenhar_estrelas(self.tela, self.estrelas)

        # Desenhar espinhos com animação (fases 11+)
        if self.numero_fase >= 11:
            # Iniciar animação dos espinhos
            if not self.animacao_espinhos_iniciada:
                self.animacao_espinhos_iniciada = True
                self.tempo_inicio_animacao_espinhos = self.tempo_congelamento

                # Criar efeitos visuais dramáticos em todas as bordas
                from src.entities.particula import criar_explosao
                # Explosões nas bordas da tela (espaçadas)
                for i in range(10):
                    # Borda superior
                    criar_explosao(i * (LARGURA // 10), 0, (200, 50, 50), self.particulas, 50)
                    # Borda inferior
                    criar_explosao(i * (LARGURA // 10), ALTURA_JOGO, (200, 50, 50), self.particulas, 50)
                for i in range(8):
                    # Borda esquerda
                    criar_explosao(0, i * (ALTURA_JOGO // 8), (200, 50, 50), self.particulas, 50)
                    # Borda direita
                    criar_explosao(LARGURA, i * (ALTURA_JOGO // 8), (200, 50, 50), self.particulas, 50)

            # Calcular progresso da animação (0.0 a 1.0)
            frames_decorridos = self.tempo_inicio_animacao_espinhos - self.tempo_congelamento
            progresso = min(1.0, frames_decorridos / self.duracao_animacao_espinhos)

            # Efeito de borda vermelha pulsante durante toda a animação
            if progresso < 1.0:
                # Criar overlay nas bordas com intensidade baseada no progresso
                intensidade_base = int(80 * (1 - progresso))
                # Adicionar pulsação
                pulso = abs(math.sin(frames_decorridos / 15))
                intensidade = int(intensidade_base * (0.5 + 0.5 * pulso))

                # Bordas superior e inferior
                overlay_h = pygame.Surface((LARGURA, 40))
                overlay_h.fill((200, 0, 0))
                overlay_h.set_alpha(intensidade)
                self.tela.blit(overlay_h, (0, 0))  # Superior
                self.tela.blit(overlay_h, (0, ALTURA_JOGO - 40))  # Inferior

                # Bordas esquerda e direita
                overlay_v = pygame.Surface((40, ALTURA_JOGO))
                overlay_v.fill((200, 0, 0))
                overlay_v.set_alpha(intensidade)
                self.tela.blit(overlay_v, (0, 0))  # Esquerda
                self.tela.blit(overlay_v, (LARGURA - 40, 0))  # Direita

                # Efeito de tremor da tela nos primeiros frames
                if frames_decorridos < 20:
                    import random
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 3)
                    # Aplicar tremor movendo temporariamente o gradiente
                    temp_surf = pygame.Surface((LARGURA, ALTURA_JOGO))
                    temp_surf.blit(self.tela, (offset_x, offset_y))
                    self.tela.blit(temp_surf, (0, 0))

            # Desenhar espinhos com animação
            for espinho in self.espinhos:
                espinho.desenhar(self.tela, tempo_atual, progresso)

        # Desenhar jogador e inimigos (sem movimento)
        if self.jogador.vidas > 0:
            self.jogador.desenhar(self.tela, tempo_atual)
        for inimigo in self.inimigos:
            if inimigo.vidas > 0:
                inimigo.desenhar(self.tela, tempo_atual)
                # Desenhar cajado do mago (se for mago)
                if hasattr(inimigo, 'tipo_mago') and inimigo.tipo_mago:
                    inimigo.desenhar_cajado(self.tela, tempo_atual, self.jogador)

        # Desenhar timer de congelamento
        segundos_restantes = max(0, self.tempo_congelamento // FPS)
        cor_timer = AMARELO if segundos_restantes > 0 else VERDE
        desenhar_texto(self.tela, f"PREPARAR: {segundos_restantes}", 50, cor_timer,
                      LARGURA // 2, ALTURA_JOGO // 2)

        # Desenhar HUD
        self.renderizar_hud(tempo_atual, self.inimigos)

        if self.tempo_congelamento <= 0:
            self.em_congelamento = False

        present_frame()
        self.relogio.tick(FPS)

    def _atualizar_inimigos(self, tempo_atual, fator_tempo):
        """Atualiza IA de todos os inimigos."""
        for idx, inimigo in enumerate(self.inimigos):
            # BUGFIX: Sincronizar lista de tempo_movimento DENTRO do loop
            # (necessário quando inimigos são adicionados dinamicamente durante o loop, ex: invocações do mago)
            while len(self.tempo_movimento_inimigos) <= idx:
                self.tempo_movimento_inimigos.append(0)

            # Aplicar fator de tempo ao inimigo
            velocidade_original = inimigo.velocidade
            inimigo.velocidade *= fator_tempo

            self.tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                inimigo, idx, self.jogador, self.tiros_jogador, self.inimigos, tempo_atual,
                self.tempo_movimento_inimigos, self.intervalo_movimento, self.numero_fase,
                self.tiros_inimigo, self.movimento_x, self.movimento_y,
                self.particulas, self.flashes
            )

            # Se for inimigo granada, tentar lançar granada (apenas se estiver vivo)
            if hasattr(inimigo, 'tipo_granada') and inimigo.tipo_granada and inimigo.vidas > 0:
                inimigo.lancar_granada(self.jogador, self.granadas, self.particulas, self.flashes)

            # Restaurar velocidade original
            inimigo.velocidade = velocidade_original

            # Garantir que os inimigos não ultrapassem a área de jogo
            if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                inimigo.y = ALTURA_JOGO - inimigo.tamanho
                inimigo.rect.y = inimigo.y

    def _verificar_condicoes_fim(self):
        """Verifica condições de vitória ou derrota."""
        # Verificar se todos os inimigos foram derrotados
        todos_derrotados = all(inimigo.vidas <= 0 for inimigo in self.inimigos)

        if todos_derrotados:
            # Tornar jogador invulnerável
            self.jogador.invulneravel = True
            self.jogador.duracao_invulneravel = float('inf')

            # Iniciar transição de vitória
            if self.tempo_transicao_vitoria is None:
                self.tempo_transicao_vitoria = self.duracao_transicao_vitoria

        # Verificar se o jogador morreu
        if self.verificar_jogador_morto():
            # Tornar inimigos invulneráveis
            for inimigo in self.inimigos:
                inimigo.invulneravel = True
                inimigo.duracao_invulneravel = float('inf')

        return None

    def _renderizar_fase(self, tempo_atual, pos_mouse):
        """Renderiza toda a fase."""
        # Fundo
        self.renderizar_fundo()

        # Objetos do jogo
        self.renderizar_objetos_jogo(tempo_atual, self.inimigos)

        # HUD
        self.renderizar_hud(tempo_atual, self.inimigos)

        # Fade-in
        if self.fade_in > 0:
            fade = pygame.Surface((LARGURA, ALTURA))
            fade.fill((0, 0, 0))
            fade.set_alpha(self.fade_in)
            self.tela.blit(fade, (0, 0))

        # Mensagem de vitória durante transição
        if self.tempo_transicao_vitoria is not None:
            self._desenhar_mensagem_vitoria()

        # Mensagem de derrota durante transição
        if self.tempo_transicao_derrota is not None:
            self._desenhar_mensagem_derrota()

        # Mira do mouse
        self.renderizar_mira(pos_mouse)

    def _desenhar_mensagem_vitoria(self):
        """Desenha mensagem de vitória."""
        alpha = int(255 * (self.duracao_transicao_vitoria - self.tempo_transicao_vitoria) / self.duracao_transicao_vitoria)
        texto_surf = self.fonte_titulo.render("FASE CONCLUÍDA!", True, VERDE)
        texto_surf.set_alpha(alpha)
        texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
        self.tela.blit(texto_surf, texto_rect)

        # Partículas de celebração
        if random.random() < 0.2:
            from src.entities.particula import criar_explosao
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA_JOGO)
            cor = random.choice([VERDE, AMARELO, AZUL])
            flash = criar_explosao(x, y, cor, self.particulas, 15)
            self.flashes.append(flash)

    def _desenhar_mensagem_derrota(self):
        """Desenha mensagem de derrota."""
        alpha = int(255 * (self.duracao_transicao_derrota - self.tempo_transicao_derrota) / self.duracao_transicao_derrota)
        texto_surf = self.fonte_titulo.render("DERROTADO!", True, VERMELHO)
        texto_surf.set_alpha(alpha)
        texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
        self.tela.blit(texto_surf, texto_rect)

        # Efeito de tela vermelha
        overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
        overlay.fill(VERMELHO)
        overlay.set_alpha(int(50 * (self.duracao_transicao_derrota - self.tempo_transicao_derrota) / self.duracao_transicao_derrota))
        self.tela.blit(overlay, (0, 0))

        # Mais partículas de derrota
        if random.random() < 0.3:
            from src.entities.particula import criar_explosao
            x = self.jogador.x + random.randint(-50, 50)
            y = self.jogador.y + random.randint(-50, 50)
            criar_explosao(x, y, VERMELHO, self.particulas, 20)


def jogar_fase(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
    """
    Executa uma fase específica do jogo com sistema corrigido.
    REFATORADO: Usa sistema de classes para eliminar duplicação.

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
    print(f"🎯 Iniciando fase {numero_fase}...")

    # Criar a fase
    resultado_fase = NivelFactory.criar_fase(numero_fase)

    # Verificar se é boss fight
    if NivelFactory.e_boss_fight(resultado_fase):
        info_boss = NivelFactory.obter_info_boss(resultado_fase)
        print(f"🔥 DETECTADO: {info_boss['mensagem']}")

        # Executar boss fight usando sistema modular
        if info_boss['boss'] == 'fusion':
            # Boss fight pode ter posição customizada do jogador
            pos_jogador = info_boss.get('pos_jogador', None)
            return executar_boss_fight('fusion', tela, relogio, numero_fase,
                                      gradiente_jogo, fonte_titulo, fonte_normal,
                                      pos_jogador=pos_jogador)

        # Fallback para fase normal se boss não reconhecido
        print(f"⚠️ Tipo de boss '{info_boss['boss']}' não reconhecido, executando fase normal")
        inimigos = NivelFactory.criar_fase_generica(numero_fase)
        pos_jogador = None
    else:
        # Fase normal - extrair inimigos e posição do jogador
        if isinstance(resultado_fase, dict):
            inimigos = resultado_fase.get('inimigos', [])
            pos_jogador = resultado_fase.get('pos_jogador', None)
        else:
            # Fallback para compatibilidade com código antigo
            inimigos = resultado_fase
            pos_jogador = None

    # Validação dos inimigos
    if inimigos is None:
        print(f"[ERROR] NivelFactory.criar_fase({numero_fase}) retornou None. Abortando fase e voltando ao menu.")
        from src.items.chucky_invocation import limpar_invocacoes
        limpar_invocacoes()
        return "menu"

    # Converter para lista se necessário
    if not isinstance(inimigos, (list, tuple)):
        try:
            inimigos = list(inimigos)
        except Exception:
            print(f"[ERROR] NivelFactory.criar_fase({numero_fase}) retornou um tipo inválido: {type(inimigos)}. Voltando ao menu.")
            from src.items.chucky_invocation import limpar_invocacoes
            limpar_invocacoes()
            return "menu"

    # Criar e executar fase normal
    fase = FaseNormal(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal, inimigos, pos_jogador)
    return fase.executar()
