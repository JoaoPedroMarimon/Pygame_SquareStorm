#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para inimigo que lança granadas.
O inimigo lança granadas em arco que explodem após um tempo.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.items.granada import Granada
from src.entities.particula import Particula
from src.utils.sound import gerar_som_tiro


class InimigoGranada(Quadrado):
    """
    Inimigo que lança granadas em direção ao jogador.
    As granadas explodem após um tempo causando dano em área.
    """

    def __init__(self, x, y):
        """Inicializa o inimigo granada."""
        # Cor marrom-militar para diferenciar
        cor_militar_granada = (101, 67, 33)  # Marrom terra
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.6  # Mais lento que outros

        super().__init__(x, y, TAMANHO_QUADRADO, cor_militar_granada, velocidade)

        # Atributos básicos
        self.vidas = 3
        self.vidas_max = 3

        # Sistema de granada
        self.cooldown_granada = 2500  # 2.5 segundos entre lançamentos
        self.tempo_ultimo_lancamento = 0

        # Flag para identificar tipo
        self.tipo_granada = True

        # Cooldown de movimento (para se manter parado às vezes)
        self.tempo_cooldown = 999999  # Não usa tiro normal

    def pode_lancar(self):
        """Verifica se o inimigo pode lançar uma granada."""
        tempo_atual = pygame.time.get_ticks()
        return tempo_atual - self.tempo_ultimo_lancamento >= self.cooldown_granada

    def lancar_granada(self, jogador, granadas_lista, particulas=None, flashes=None):
        """
        Lança uma granada em direção ao jogador.

        Args:
            jogador: Objeto do jogador (alvo)
            granadas_lista: Lista de granadas ativas
            particulas: Lista de partículas (opcional)
            flashes: Lista de flashes (opcional)
        """
        # Verificar se pode lançar
        if not self.pode_lancar():
            return

        tempo_atual = pygame.time.get_ticks()
        self.tempo_ultimo_lancamento = tempo_atual

        # Posição central do inimigo
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # Calcular direção para o jogador
        jogador_centro_x = jogador.x + jogador.tamanho // 2
        jogador_centro_y = jogador.y + jogador.tamanho // 2

        dx = jogador_centro_x - centro_x
        dy = jogador_centro_y - centro_y

        # Normalizar
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Som de lançamento de granada
        try:
            tamanho_amostra = 8000
            som_granada = pygame.mixer.Sound(bytes(bytearray(
                int(127 + 127 * (math.sin(i / 15) if i < 2000 else 0))
                for i in range(tamanho_amostra)
            )))
            som_granada.set_volume(0.15)
            pygame.mixer.Channel(5).play(som_granada)
        except:
            pass

        # Criar efeito de partículas de lançamento
        if particulas is not None:
            cor_lancamento = (150, 100, 50)

            for _ in range(8):
                vari_x = random.uniform(-3, 3)
                vari_y = random.uniform(-3, 3)
                pos_x = centro_x + vari_x
                pos_y = centro_y + vari_y

                particula = Particula(pos_x, pos_y, cor_lancamento)
                particula.velocidade_x = dx * random.uniform(1, 3) + random.uniform(-0.5, 0.5)
                particula.velocidade_y = dy * random.uniform(1, 3) + random.uniform(-0.5, 0.5)
                particula.vida = random.randint(8, 15)
                particula.tamanho = random.uniform(2, 4)
                particula.gravidade = 0.01

                particulas.append(particula)

        # Criar granada que pertence ao inimigo
        granada = Granada(centro_x, centro_y, dx, dy, pertence_inimigo=True)
        granadas_lista.append(granada)

    def desenhar_equipamento_granada(self, tela, tempo_atual, jogador):
        """
        Desenha o inimigo segurando uma granada na mão.

        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual para animações
            jogador: Objeto do jogador (para orientação)
        """
        # Calcular centro do inimigo
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # Calcular direção para o jogador
        jogador_centro_x = jogador.x + jogador.tamanho // 2
        jogador_centro_y = jogador.y + jogador.tamanho // 2

        dx = jogador_centro_x - centro_x
        dy = jogador_centro_y - centro_y

        # Normalizar
        distancia = math.sqrt(dx**2 + dy**2)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Verificar tempo desde último lançamento
        tempo_desde_lancamento = tempo_atual - self.tempo_ultimo_lancamento
        progresso = min(1.0, tempo_desde_lancamento / self.cooldown_granada)

        # Posição da mão (braço estendido)
        distancia_mao = 25
        mao_x = centro_x + dx * distancia_mao
        mao_y = centro_y + dy * distancia_mao

        # DESENHO DO BRAÇO
        cor_uniforme = (101, 67, 33)
        cor_pele = (180, 140, 100)

        # Braço (linha do corpo até a mão)
        pygame.draw.line(tela, cor_uniforme,
                        (centro_x, centro_y),
                        (mao_x - dx * 5, mao_y - dy * 5), 6)

        # Antebraço
        pygame.draw.line(tela, cor_pele,
                        (mao_x - dx * 5, mao_y - dy * 5),
                        (mao_x, mao_y), 5)

        # MÃO SEGURANDO GRANADA
        if progresso >= 1.0:
            # Mão/luva
            pygame.draw.circle(tela, (80, 60, 40), (int(mao_x), int(mao_y)), 5)

            # GRANADA na mão
            granada_x = mao_x + dx * 8
            granada_y = mao_y + dy * 8

            # Corpo da granada
            pygame.draw.circle(tela, (60, 120, 60), (int(granada_x), int(granada_y)), 7)
            pygame.draw.circle(tela, (40, 80, 40), (int(granada_x), int(granada_y)), 7, 1)

            # Detalhes da granada (linhas)
            pygame.draw.line(tela, (40, 80, 40),
                           (granada_x - 5, granada_y),
                           (granada_x + 5, granada_y), 2)
            pygame.draw.line(tela, (40, 80, 40),
                           (granada_x, granada_y - 5),
                           (granada_x, granada_y + 5), 2)

            # Topo da granada (bocal)
            bocal_y = granada_y - 7
            pygame.draw.rect(tela, (150, 150, 150),
                           (granada_x - 3, bocal_y - 4, 6, 4), 0, 2)

            # Pino da granada (anel amarelo)
            pino_x = granada_x + 6
            pino_y = granada_y - 6
            pygame.draw.circle(tela, (220, 220, 100), (int(pino_x), int(pino_y)), 4, 2)

            # Efeito de brilho/pulso quando pronta
            if (tempo_atual // 300) % 2 == 0:
                pygame.draw.circle(tela, (100, 255, 100, 128),
                                 (int(granada_x), int(granada_y)), 10, 2)
        else:
            # Mão fechada (sem granada - recarregando)
            pygame.draw.circle(tela, (80, 60, 40), (int(mao_x), int(mao_y)), 4)

            # Indicador visual de recarga (pequenas partículas)
            if int(tempo_atual / 100) % 2 == 0:
                for i in range(3):
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 3)
                    pygame.draw.circle(tela, (60, 255, 60),
                                     (int(mao_x + offset_x), int(mao_y + offset_y)), 1)

        # Linha de mira pontilhada ao jogador (quando pronta)
        if progresso >= 1.0:
            passos = int(distancia // 15)
            for i in range(0, passos, 3):
                laser_x = mao_x + dx * (i * 15)
                laser_y = mao_y + dy * (i * 15)
                pygame.draw.circle(tela, (255, 100, 0), (int(laser_x), int(laser_y)), 1)

    def desenhar(self, tela, tempo_atual):
        """Sobrescreve o método desenhar para incluir visual simplificado com cinto de granadas."""
        # Cores do granadeiro (tema marrom/terra)
        cor_uniforme_base = (101, 67, 33)           # Marrom terra
        cor_uniforme_sombra = (70, 45, 20)          # Sombra marrom escura
        cor_fivela_dourada = (200, 150, 50)         # Fivela dourada

        centro_x = self.x + self.tamanho // 2

        # ===== SOMBRA NO CHÃO =====
        shadow_surface = pygame.Surface((self.tamanho + 8, self.tamanho + 8))
        shadow_surface.set_alpha(80)
        shadow_surface.fill((0, 0, 0))
        tela.blit(shadow_surface, (self.x + 2, self.y + 2))

        # ===== CORPO DO SOLDADO (quadrado simples) =====
        corpo_rect = pygame.Rect(self.x, self.y, self.tamanho, self.tamanho)

        # Uniforme base
        pygame.draw.rect(tela, cor_uniforme_sombra, corpo_rect, 0, 5)
        pygame.draw.rect(tela, cor_uniforme_base,
                        (self.x + 2, self.y + 2, self.tamanho - 4, self.tamanho - 4), 0, 4)

        # ===== CINTO COM GRANADAS (na cintura) =====
        cinto_y = self.y + int(self.tamanho * 0.65)  # Um pouco abaixo do meio (65% da altura)

        # Linha do cinto
        pygame.draw.line(tela, cor_fivela_dourada,
                        (self.x + 3, cinto_y),
                        (self.x + self.tamanho - 3, cinto_y), 4)

        # Granadas penduradas no cinto (3 granadas mais visíveis)
        num_granadas = 3
        espacamento = self.tamanho // (num_granadas + 1)

        for i in range(num_granadas):
            granada_cinto_x = self.x + espacamento * (i + 1)
            granada_cinto_y = cinto_y + 6

            # Granada maior e mais visível
            pygame.draw.circle(tela, (60, 120, 60), (granada_cinto_x, granada_cinto_y), 5)
            pygame.draw.circle(tela, (40, 80, 40), (granada_cinto_x, granada_cinto_y), 5, 1)

            # Detalhes da granada
            pygame.draw.line(tela, (40, 80, 40),
                           (granada_cinto_x - 3, granada_cinto_y),
                           (granada_cinto_x + 3, granada_cinto_y), 1)

            # Topo da granada (bocal)
            pygame.draw.rect(tela, (150, 150, 150),
                           (granada_cinto_x - 2, granada_cinto_y - 6, 4, 3))

            # Pino amarelo
            pygame.draw.circle(tela, (220, 220, 100),
                             (granada_cinto_x + 4, granada_cinto_y - 5), 2, 1)

        # ===== INDICADOR DE COOLDOWN =====
        tempo_desde_lancamento = tempo_atual - self.tempo_ultimo_lancamento
        progresso = min(1.0, tempo_desde_lancamento / self.cooldown_granada)

        if progresso < 1.0:
            # Barra de cooldown embaixo do cinto
            barra_y = cinto_y + 18
            barra_largura = self.tamanho

            # Fundo da barra
            pygame.draw.rect(tela, (60, 60, 60), (self.x, barra_y, barra_largura, 4), 0, 2)
            # Progresso
            progresso_largura = int(barra_largura * progresso)
            pygame.draw.rect(tela, (60, 255, 60), (self.x, barra_y, progresso_largura, 4), 0, 2)

            # Texto "LOADING"
            from src.utils.visual import desenhar_texto
            desenhar_texto(tela, "LOADING", 10, (60, 255, 60), centro_x, barra_y + 10)
        else:
            # Indicador PRONTO
            led_x = self.x + self.tamanho - 5
            led_y = self.y + 5
            pygame.draw.circle(tela, (60, 255, 60), (led_x, led_y), 3)

        # ===== BARRA DE VIDA =====
        vida_largura = 50
        altura_barra = 6

        # Fundo escuro
        pygame.draw.rect(tela, (40, 40, 40),
                        (self.x, self.y - 15, vida_largura, altura_barra), 0, 2)

        # Vida atual
        vida_atual = int((self.vidas / self.vidas_max) * vida_largura)
        if vida_atual > 0:
            pygame.draw.rect(tela, self.cor,
                            (self.x, self.y - 15, vida_atual, altura_barra), 0, 2)
