#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cutscene do inimigo misterioso que aparece após a vitória do Boss Fusion.
Um inimigo preto se aproxima do jogador, fala e desaparece via teletransporte.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import Particula
from src.utils.visual import desenhar_texto, desenhar_estrelas
from src.utils.display_manager import present_frame


class InimigoMisterioso(Quadrado):
    """Classe para o inimigo misterioso preto."""

    def __init__(self, x, y):
        """Inicializa o inimigo misterioso."""
        # Cor preta profunda com aura vermelha
        cor_preta = (20, 20, 20)
        super().__init__(x, y, TAMANHO_QUADRADO * 1.2, cor_preta, 3)

        self.vidas = 999
        self.vidas_max = 999
        self.aura_intensidade = 0
        self.particulas_sombra = []

    def desenhar_com_aura(self, tela, tempo_atual):
        """Desenha o inimigo com uma aura sinistra."""
        # Aura vermelha pulsante
        pulso = math.sin(tempo_atual / 300) * 0.3 + 0.7
        cor_aura = (int(180 * pulso), 0, int(50 * pulso))

        # Desenhar múltiplas camadas de aura
        for i in range(5, 0, -1):
            alpha = int(50 * (6 - i) / 5 * pulso)
            raio = int(self.tamanho // 2 + i * 8)
            superficie_aura = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(superficie_aura, (*cor_aura, alpha), (raio, raio), raio)
            tela.blit(superficie_aura,
                     (self.x + self.tamanho // 2 - raio,
                      self.y + self.tamanho // 2 - raio))

        # Desenhar o quadrado principal
        self.desenhar(tela, tempo_atual)

        # Borda vermelha brilhante
        pygame.draw.rect(tela, (200, 0, 0), self.rect, 3)

        # Partículas de sombra
        if random.random() < 0.3:
            particula = Particula(
                self.x + random.randint(0, int(self.tamanho)),
                self.y + random.randint(0, int(self.tamanho)),
                (50, 0, 0)
            )
            particula.velocidade_x = random.uniform(-1, 1)
            particula.velocidade_y = random.uniform(-2, -0.5)
            particula.vida = random.randint(20, 40)
            particula.tamanho = random.uniform(2, 4)
            self.particulas_sombra.append(particula)

        # Atualizar e desenhar partículas
        for particula in self.particulas_sombra[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas_sombra.remove(particula)
            else:
                particula.desenhar(tela)


class MisteriosoCutscene:
    """
    Cutscene do inimigo misterioso após vencer o Boss Fusion.
    """

    def __init__(self, jogador_pos, jogador=None):
        """
        Inicializa a cutscene.

        Args:
            jogador_pos: Posição (x, y) do jogador
            jogador: Objeto do jogador (opcional)
        """
        self.estado = "fade_in"  # fade_in -> spawn -> aproximacao -> dialogo -> teletransporte -> espera -> final
        self.tempo_inicio = 0
        self.jogador_x, self.jogador_y = jogador_pos
        self.jogador = jogador

        # Criar inimigo misterioso longe à direita
        self.misterioso = InimigoMisterioso(LARGURA + 100, ALTURA_JOGO // 2)

        # Efeitos visuais
        self.particulas = []
        self.flashes = []
        self.intensidade_distorcao = 0
        self.alpha_fade = 255  # Fade in começa totalmente preto

        # Sistema de diálogo
        self.texto_dialogo = "Você não faz ideia de onde se meteu..."
        self.texto_visivel = ""
        self.indice_texto = 0
        self.tempo_ultima_letra = 0
        self.velocidade_texto = 50  # ms por letra

        # Configurações de timing
        self.duracao_fade_in = 1500  # 1.5 segundos de fade in
        self.duracao_total = 13000  # Total aumentado
        self.tempo_spawn = 1000
        self.tempo_aproximacao = 3000
        self.tempo_dialogo = 4000
        self.tempo_teletransporte = 2000  # Aumentado para 2 segundos
        self.tempo_espera = 1000  # 1 segundo de espera após teletransporte

        # Posição alvo (BEM PERTO do jogador - na frente dele)
        self.pos_alvo_x = self.jogador_x + 80  # Muito mais próximo
        self.pos_alvo_y = self.jogador_y

        # Efeito de teletransporte
        self.particulas_teleporte = []
        self.concluida = False

    def iniciar(self, tempo_atual):
        """Inicia a cutscene."""
        self.tempo_inicio = tempo_atual
        self.estado = "fade_in"
        print("👤 Cutscene do Misterioso iniciada!")

    def atualizar(self, tempo_atual):
        """
        Atualiza a cutscene.

        Returns:
            True se a cutscene terminou, False caso contrário
        """
        tempo_decorrido = tempo_atual - self.tempo_inicio

        # ESTADO: FADE IN (transição suave do preto)
        if self.estado == "fade_in":
            if tempo_decorrido < self.duracao_fade_in:
                # Fade in gradual
                progresso = tempo_decorrido / self.duracao_fade_in
                self.alpha_fade = int(255 * (1 - progresso))
            else:
                self.alpha_fade = 0
                self.estado = "spawn"
                print("👤 Fade in completo, spawn iniciado...")

        # ESTADO: SPAWN (aparecer com efeitos)
        elif self.estado == "spawn":
            tempo_spawn_decorrido = tempo_decorrido - self.duracao_fade_in
            if tempo_spawn_decorrido < self.tempo_spawn:
                # Efeito de materialização
                self.criar_particulas_spawn(tempo_atual)
                self.intensidade_distorcao = min(1.0, tempo_spawn_decorrido / self.tempo_spawn)
            else:
                self.estado = "aproximacao"
                print("👤 Misterioso se aproximando...")

        # ESTADO: APROXIMAÇÃO (mover em direção ao jogador)
        elif self.estado == "aproximacao":
            tempo_aprox = tempo_decorrido - self.duracao_fade_in - self.tempo_spawn
            if tempo_aprox < self.tempo_aproximacao:
                # Movimento suave (ease-out)
                progresso = tempo_aprox / self.tempo_aproximacao
                progresso_suave = 1 - (1 - progresso) ** 3  # Cubic ease-out

                # Interpolar posição
                pos_inicial_x = LARGURA + 100
                pos_inicial_y = ALTURA_JOGO // 2

                self.misterioso.x = pos_inicial_x + (self.pos_alvo_x - pos_inicial_x) * progresso_suave
                self.misterioso.y = pos_inicial_y + (self.pos_alvo_y - pos_inicial_y) * progresso_suave
                self.misterioso.rect.x = self.misterioso.x
                self.misterioso.rect.y = self.misterioso.y

                # Trilha de partículas
                if random.random() < 0.5:
                    self.criar_trilha_movimento()
            else:
                self.estado = "dialogo"
                self.tempo_inicio_dialogo = tempo_atual
                print("👤 Misterioso falando...")

        # ESTADO: DIÁLOGO (mostrar texto)
        elif self.estado == "dialogo":
            tempo_dialogo = tempo_atual - self.tempo_inicio_dialogo

            # Animação de texto (letra por letra)
            if tempo_atual - self.tempo_ultima_letra > self.velocidade_texto:
                if self.indice_texto < len(self.texto_dialogo):
                    self.texto_visivel += self.texto_dialogo[self.indice_texto]
                    self.indice_texto += 1
                    self.tempo_ultima_letra = tempo_atual

            if tempo_dialogo >= self.tempo_dialogo:
                self.estado = "teletransporte"
                self.tempo_inicio_teleporte = tempo_atual
                print("👤 Misterioso se teletransportando...")

        # ESTADO: TELETRANSPORTE (desaparecer)
        elif self.estado == "teletransporte":
            tempo_teleporte = tempo_atual - self.tempo_inicio_teleporte

            if tempo_teleporte < self.tempo_teletransporte:
                # Criar efeito de teletransporte
                self.criar_efeito_teletransporte(tempo_atual, tempo_teleporte)

                # Fade out do misterioso
                progresso = tempo_teleporte / self.tempo_teletransporte
                self.intensidade_distorcao = 1.0 - progresso
            else:
                self.estado = "espera"
                self.tempo_inicio_espera = tempo_atual
                print("👤 Aguardando partículas finalizarem...")

        # ESTADO: ESPERA (aguardar partículas desaparecerem)
        elif self.estado == "espera":
            tempo_espera = tempo_atual - self.tempo_inicio_espera

            if tempo_espera >= self.tempo_espera:
                self.estado = "final"
                self.concluida = True
                print("👤 Cutscene do Misterioso concluída!")
                return True

        # Atualizar partículas
        for particula in self.particulas[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas.remove(particula)

        return self.concluida

    def criar_particulas_spawn(self, tempo_atual):
        """Cria partículas de spawn/materialização."""
        for _ in range(5):
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(30, 80)
            x = self.misterioso.x + self.misterioso.tamanho // 2 + math.cos(angulo) * distancia
            y = self.misterioso.y + self.misterioso.tamanho // 2 + math.sin(angulo) * distancia

            particula = Particula(x, y, (100, 0, 0))
            particula.velocidade_x = -math.cos(angulo) * 2
            particula.velocidade_y = -math.sin(angulo) * 2
            particula.vida = random.randint(20, 40)
            particula.tamanho = random.uniform(3, 6)
            self.particulas.append(particula)

    def criar_trilha_movimento(self):
        """Cria trilha de partículas durante o movimento."""
        particula = Particula(
            self.misterioso.x + self.misterioso.tamanho // 2,
            self.misterioso.y + self.misterioso.tamanho // 2,
            (80, 0, 0)
        )
        particula.velocidade_x = random.uniform(-0.5, 0.5)
        particula.velocidade_y = random.uniform(-0.5, 0.5)
        particula.vida = random.randint(15, 30)
        particula.tamanho = random.uniform(2, 4)
        self.particulas.append(particula)

    def criar_efeito_teletransporte(self, tempo_atual, tempo_decorrido):
        """Cria efeito visual de teletransporte."""
        # Centro do inimigo
        centro_x = self.misterioso.x + self.misterioso.tamanho // 2
        centro_y = self.misterioso.y + self.misterioso.tamanho // 2

        # Muitas partículas convergindo para o centro (efeito de implosão)
        for _ in range(15):
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(20, 100)
            x = centro_x + math.cos(angulo) * distancia
            y = centro_y + math.sin(angulo) * distancia

            particula = Particula(x, y, (200, 0, 100))
            # Partículas vão em direção ao centro (implosão)
            particula.velocidade_x = -math.cos(angulo) * 5
            particula.velocidade_y = -math.sin(angulo) * 5
            particula.vida = random.randint(15, 25)
            particula.tamanho = random.uniform(4, 8)
            self.particulas.append(particula)

        # Partículas em espiral (efeito de portal)
        if random.random() < 0.7:
            for i in range(5):
                angulo = (tempo_decorrido / 100 + i * math.pi / 2.5) % (math.pi * 2)
                raio = 30 + (tempo_decorrido / self.tempo_teletransporte) * 20
                x = centro_x + math.cos(angulo) * raio
                y = centro_y + math.sin(angulo) * raio

                particula = Particula(x, y, (255, 50, 150))
                particula.velocidade_x = math.cos(angulo) * 2
                particula.velocidade_y = math.sin(angulo) * 2
                particula.vida = random.randint(8, 15)
                particula.tamanho = random.uniform(3, 6)
                self.particulas.append(particula)

    def desenhar(self, tela, tempo_atual):
        """Desenha a cutscene."""
        # Desenhar o jogador (sempre visível)
        if self.jogador is not None:
            # Salvar estados temporariamente
            invulneravel_original = self.jogador.invulneravel
            espingarda_ativa_original = getattr(self.jogador, 'espingarda_ativa', False)
            metralhadora_ativa_original = getattr(self.jogador, 'metralhadora_ativa', False)
            desert_eagle_ativa_original = getattr(self.jogador, 'desert_eagle_ativa', False)
            granada_selecionada_original = getattr(self.jogador, 'granada_selecionada', False)
            dimensional_hop_selecionado_original = getattr(self.jogador, 'dimensional_hop_selecionado', False)
            ampulheta_selecionada_original = getattr(self.jogador, 'ampulheta_selecionada', False)
            amuleto_ativo_original = getattr(self.jogador, 'amuleto_ativo', False)
            sabre_equipado_original = getattr(self.jogador, 'sabre_equipado', False)

            # Desativar invulnerabilidade e armas temporariamente
            self.jogador.invulneravel = False
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = False
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = False
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = False
            if hasattr(self.jogador, 'granada_selecionada'):
                self.jogador.granada_selecionada = False
            if hasattr(self.jogador, 'dimensional_hop_selecionado'):
                self.jogador.dimensional_hop_selecionado = False
            if hasattr(self.jogador, 'ampulheta_selecionada'):
                self.jogador.ampulheta_selecionada = False
            if hasattr(self.jogador, 'amuleto_ativo'):
                self.jogador.amuleto_ativo = False
            if hasattr(self.jogador, 'sabre_equipado'):
                self.jogador.sabre_equipado = False
            if hasattr(self.jogador, 'spas12_ativa'):
                self.jogador.spas12_ativa = False

            # Desenhar o jogador
            self.jogador.desenhar(tela, tempo_atual)

            # Restaurar estados
            self.jogador.invulneravel = invulneravel_original
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = espingarda_ativa_original
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = metralhadora_ativa_original
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = desert_eagle_ativa_original
            if hasattr(self.jogador, 'granada_selecionada'):
                self.jogador.granada_selecionada = granada_selecionada_original
            if hasattr(self.jogador, 'dimensional_hop_selecionado'):
                self.jogador.dimensional_hop_selecionado = dimensional_hop_selecionado_original
            if hasattr(self.jogador, 'ampulheta_selecionada'):
                self.jogador.ampulheta_selecionada = ampulheta_selecionada_original
            if hasattr(self.jogador, 'amuleto_ativo'):
                self.jogador.amuleto_ativo = amuleto_ativo_original
            if hasattr(self.jogador, 'sabre_equipado'):
                self.jogador.sabre_equipado = sabre_equipado_original
        else:
            # Fallback: desenhar um quadrado azul simples
            jogador_rect = pygame.Rect(self.jogador_x, self.jogador_y, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
            pygame.draw.rect(tela, AZUL, jogador_rect)
            pygame.draw.rect(tela, AZUL_ESCURO, jogador_rect, 3)

        # Desenhar o inimigo misterioso (se não estiver desaparecido)
        if self.estado not in ("espera", "final"):
            # Aplicar alpha baseado na distorção
            if self.intensidade_distorcao > 0:
                self.misterioso.desenhar_com_aura(tela, tempo_atual)

        # Desenhar partículas
        for particula in self.particulas:
            particula.desenhar(tela)

        # Efeito visual especial durante teletransporte
        if self.estado == "teletransporte":
            centro_x = self.misterioso.x + self.misterioso.tamanho // 2
            centro_y = self.misterioso.y + self.misterioso.tamanho // 2

            # Círculo pulsante no centro (portal)
            pulso = math.sin(tempo_atual / 100) * 0.3 + 0.7
            raio_portal = int(40 * (1 - self.intensidade_distorcao) * pulso)

            if raio_portal > 0:
                # Círculo externo
                pygame.draw.circle(tela, (200, 0, 100), (int(centro_x), int(centro_y)), raio_portal, 3)
                # Círculo médio
                pygame.draw.circle(tela, (255, 50, 150), (int(centro_x), int(centro_y)), raio_portal // 2, 2)
                # Centro brilhante
                superficie_brilho = pygame.Surface((raio_portal * 2, raio_portal * 2), pygame.SRCALPHA)
                alpha_brilho = int(150 * (1 - self.intensidade_distorcao))
                pygame.draw.circle(superficie_brilho, (255, 100, 200, alpha_brilho),
                                 (raio_portal, raio_portal), raio_portal // 3)
                tela.blit(superficie_brilho,
                         (int(centro_x) - raio_portal, int(centro_y) - raio_portal))

        # Desenhar diálogo
        if self.estado == "dialogo" and self.texto_visivel:
            # Fundo semi-transparente para o texto
            largura_caixa = 800
            altura_caixa = 100
            x_caixa = LARGURA // 2 - largura_caixa // 2
            y_caixa = ALTURA_JOGO - 150

            superficie_caixa = pygame.Surface((largura_caixa, altura_caixa), pygame.SRCALPHA)
            pygame.draw.rect(superficie_caixa, (20, 0, 0, 200), (0, 0, largura_caixa, altura_caixa))
            pygame.draw.rect(superficie_caixa, (150, 0, 0), (0, 0, largura_caixa, altura_caixa), 3)
            tela.blit(superficie_caixa, (x_caixa, y_caixa))

            # Nome do personagem
            desenhar_texto(tela, "???", 24, (200, 0, 0), x_caixa + 50, y_caixa + 25)

            # Texto do diálogo
            desenhar_texto(tela, self.texto_visivel, 28, BRANCO,
                          LARGURA // 2, y_caixa + altura_caixa // 2 + 10)

        # Efeito de distorção da tela durante teletransporte
        if self.estado == "teletransporte":
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)  # ALTURA completa incluindo HUD
            intensidade = int(100 * (1 - self.intensidade_distorcao))
            overlay.fill((100, 0, 0, intensidade))
            tela.blit(overlay, (0, 0))


        # Efeito de fade in (tela preta no início) - ALTURA completa incluindo HUD
        if self.alpha_fade > 0:
            fade_surface = pygame.Surface((LARGURA, ALTURA))  # ALTURA total, não ALTURA_JOGO
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.alpha_fade)
            tela.blit(fade_surface, (0, 0))


def executar_cutscene_misterioso(tela, relogio, gradiente_jogo, estrelas, jogador_pos, jogador=None):
    """
    Executa a cutscene do inimigo misterioso.

    Args:
        tela: Superfície de renderização
        relogio: Clock do pygame
        gradiente_jogo: Gradiente de fundo
        estrelas: Lista de estrelas de fundo
        jogador_pos: Posição (x, y) do jogador
        jogador: Objeto do jogador (opcional)

    Returns:
        True quando a cutscene termina
    """
    cutscene = MisteriosoCutscene(jogador_pos, jogador)
    cutscene.iniciar(pygame.time.get_ticks())

    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()

        # Processar eventos (permitir pular com ESC ou ENTER)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False


        # Atualizar cutscene
        if cutscene.atualizar(tempo_atual):
            rodando = False

        # Renderizar
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
        desenhar_estrelas(tela, estrelas)

        # Desenhar cutscene
        cutscene.desenhar(tela, tempo_atual)

        # Texto de instrução (pode pular)


        present_frame()
        relogio.tick(FPS)

    return True
