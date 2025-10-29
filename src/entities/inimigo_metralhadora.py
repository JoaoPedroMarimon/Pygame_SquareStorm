#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para inimigo que usa metralhadora.
O inimigo atira com cadência rápida por 5 segundos, depois recarrega por 3 segundos.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.entities.particula import Particula
from src.utils.sound import gerar_som_tiro


class InimigoMetralhadora(Quadrado):
    """
    Inimigo que usa metralhadora com sistema de recarga.
    Atira por 5 segundos, recarrega por 3 segundos.
    """

    def __init__(self, x, y):
        """Inicializa o inimigo metralhadora."""
        # Cor verde-oliva militar para diferenciar
        cor_militar = (107, 142, 35)  # Olive Drab
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.8  # Um pouco mais lento

        super().__init__(x, y, TAMANHO_QUADRADO, cor_militar, velocidade)

        # Atributos básicos
        self.vidas = 3
        self.vidas_max = 3

        # Sistema de metralhadora
        self.cooldown_metralhadora = 35  # 35ms entre tiros (~28 tiros/segundo) - cadência maior
        self.tempo_ultimo_tiro_metralhadora = 0

        # Sistema de recarga
        self.tempo_atirando = 5000  # 5 segundos atirando
        self.tempo_recarga = 3000   # 3 segundos recarregando
        self.iniciou_atirando = None  # Será definido no primeiro tiro
        self.esta_recarregando = False  # Começa ATIRANDO (não recarregando)
        self.tempo_inicio_recarga = 0
        self.primeira_vez = True  # Flag para inicializar no primeiro tiro

        # Flag para identificar tipo
        self.tipo_metralhadora = True

        # Cooldown de movimento (para se manter parado às vezes)
        self.tempo_cooldown = 999999  # Não usa tiro normal

    def pode_atirar(self):
        """Verifica se o inimigo pode atirar (não está recarregando)."""
        tempo_atual = pygame.time.get_ticks()

        # Inicializar timer na primeira vez que é chamado
        if self.primeira_vez:
            self.primeira_vez = False
            self.iniciou_atirando = tempo_atual
            return True

        # Verificar se está recarregando
        if self.esta_recarregando:
            tempo_decorrido_recarga = tempo_atual - self.tempo_inicio_recarga
            if tempo_decorrido_recarga >= self.tempo_recarga:
                # Terminou de recarregar
                self.esta_recarregando = False
                self.iniciou_atirando = tempo_atual
                return True
            else:
                # Ainda está recarregando
                return False
        else:
            # Verificar se precisa recarregar
            tempo_decorrido_atirando = tempo_atual - self.iniciou_atirando
            if tempo_decorrido_atirando >= self.tempo_atirando:
                # Precisa recarregar
                self.esta_recarregando = True
                self.tempo_inicio_recarga = tempo_atual
                return False
            else:
                # Pode continuar atirando
                return True

    def atirar_metralhadora(self, jogador, tiros_inimigo, particulas=None, flashes=None):
        """
        Atira com a metralhadora na direção do jogador.

        Args:
            jogador: Objeto do jogador (alvo)
            tiros_inimigo: Lista de tiros inimigos
            particulas: Lista de partículas (opcional)
            flashes: Lista de flashes (opcional)
        """
        # Verificar se pode atirar
        if not self.pode_atirar():
            return

        # Verificar cooldown entre tiros
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro_metralhadora < self.cooldown_metralhadora:
            return

        self.tempo_ultimo_tiro_metralhadora = tempo_atual

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

        # Adicionar imprecisão (metralhadora não é perfeitamente precisa)
        imprecisao = 0.1
        dx += random.uniform(-imprecisao, imprecisao)
        dy += random.uniform(-imprecisao, imprecisao)

        # Normalizar novamente
        distancia_nova = math.sqrt(dx * dx + dy * dy)
        if distancia_nova > 0:
            dx /= distancia_nova
            dy /= distancia_nova

        # Som de tiro (volume baixo)
        try:
            som_metralhadora = pygame.mixer.Sound(gerar_som_tiro())
            som_metralhadora.set_volume(0.1)
            pygame.mixer.Channel(4).play(som_metralhadora)
        except:
            pass

        # Calcular posição da ponta do cano
        comprimento_arma = 30
        ponta_cano_x = centro_x + dx * comprimento_arma
        ponta_cano_y = centro_y + dy * comprimento_arma

        # Criar efeito de partículas
        if particulas is not None:
            cor_metralhadora = (255, 150, 50)

            for _ in range(5):
                vari_x = random.uniform(-2, 2)
                vari_y = random.uniform(-2, 2)
                pos_x = ponta_cano_x + vari_x
                pos_y = ponta_cano_y + vari_y

                particula = Particula(pos_x, pos_y, cor_metralhadora)
                particula.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-0.3, 0.3)
                particula.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-0.3, 0.3)
                particula.vida = random.randint(3, 6)
                particula.tamanho = random.uniform(1, 2)
                particula.gravidade = 0.02

                particulas.append(particula)

        # Flash de tiro
        if flashes is not None:
            flash = {
                'x': ponta_cano_x,
                'y': ponta_cano_y,
                'raio': 6,
                'vida': 2,
                'cor': (255, 200, 100)
            }
            flashes.append(flash)

        # Criar tiro
        tiros_inimigo.append(Tiro(ponta_cano_x, ponta_cano_y, dx, dy, self.cor, 8))

    def desenhar_metralhadora_inimigo(self, tela, tempo_atual, jogador):
        """
        Desenha a metralhadora do inimigo orientada para o jogador.
        Visual idêntico à metralhadora do jogador.

        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual para animações
            jogador: Objeto do jogador (para orientação)
        """
        # Calcular centro do inimigo
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # Calcular direção para o jogador (ao invés do mouse)
        jogador_centro_x = jogador.x + jogador.tamanho // 2
        jogador_centro_y = jogador.y + jogador.tamanho // 2

        dx = jogador_centro_x - centro_x
        dy = jogador_centro_y - centro_y

        # Normalizar
        distancia = math.sqrt(dx**2 + dy**2)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Comprimento da metralhadora (mesmo do jogador)
        comprimento_arma = 40

        # Simulação de recuo - a arma "treme" quando está ativa
        recuo_x = 0
        recuo_y = 0
        if not self.esta_recarregando:
            # Criar efeito de tremor
            intensidade_recuo = 2
            recuo_x = random.uniform(-intensidade_recuo, intensidade_recuo)
            recuo_y = random.uniform(-intensidade_recuo, intensidade_recuo)

        # Posição da ponta da arma (com recuo)
        ponta_x = centro_x + dx * comprimento_arma + recuo_x
        ponta_y = centro_y + dy * comprimento_arma + recuo_y

        # Vetor perpendicular para elementos laterais
        perp_x = -dy
        perp_y = dx

        # Cores da metralhadora (IDÊNTICAS ao jogador)
        cor_metal_escuro = (60, 60, 70)    # Metal escuro principal
        cor_metal_claro = (120, 120, 130)  # Metal claro para detalhes
        cor_cano = (40, 40, 45)            # Cano muito escuro
        cor_laranja = (255, 140, 0)        # Detalhes laranja
        cor_vermelho = (200, 50, 50)       # Detalhes vermelhos

        # DESENHO DA METRALHADORA (CÓDIGO IDÊNTICO AO DO JOGADOR)

        # 1. Cano principal (mais grosso, múltiplas linhas)
        for i in range(6):
            offset = (i - 2.5) * 0.8
            espessura = 4 if abs(i - 2.5) < 1 else 2
            cor_linha = cor_cano if abs(i - 2.5) < 1 else cor_metal_escuro
            pygame.draw.line(tela, cor_linha,
                        (centro_x + perp_x * offset + recuo_x, centro_y + perp_y * offset + recuo_y),
                        (ponta_x + perp_x * offset, ponta_y + perp_y * offset), espessura)

        # 2. Boca do cano com supressor
        pygame.draw.circle(tela, cor_metal_escuro, (int(ponta_x), int(ponta_y)), 7)
        pygame.draw.circle(tela, cor_cano, (int(ponta_x), int(ponta_y)), 4)
        pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(ponta_y)), 2)

        # 3. Corpo principal (mais robusto)
        corpo_x = centro_x + dx * 12 + recuo_x
        corpo_y = centro_y + dy * 12 + recuo_y

        # Base do corpo (retangular para metralhadora)
        corpo_rect = pygame.Rect(corpo_x - 8, corpo_y - 6, 16, 12)
        pygame.draw.rect(tela, cor_metal_escuro, corpo_rect)
        pygame.draw.rect(tela, cor_metal_claro, corpo_rect, 2)

        # 4. Carregador
        carregador_x = corpo_x - dx * 2
        carregador_y = corpo_y - dy * 2
        carregador_rect = pygame.Rect(carregador_x - 4, carregador_y + 8, 8, 15)
        pygame.draw.rect(tela, cor_metal_escuro, carregador_rect)
        pygame.draw.rect(tela, cor_laranja, carregador_rect, 1)

        # 5. Punho e coronha compacta
        punho_x = centro_x - dx * 8 + recuo_x
        punho_y = centro_y - dy * 8 + recuo_y

        # Punho
        pygame.draw.line(tela, cor_metal_escuro,
                        (corpo_x, corpo_y),
                        (punho_x, punho_y + 10), 6)

        # Coronha retrátil
        pygame.draw.line(tela, cor_metal_claro,
                        (punho_x, punho_y),
                        (punho_x - dx * 12, punho_y - dy * 12), 4)

        # 6. Gatilho e proteção
        gatilho_x = corpo_x - dx * 3 - perp_x * 3
        gatilho_y = corpo_y - dy * 3 - perp_y * 3
        pygame.draw.circle(tela, cor_metal_claro, (int(gatilho_x), int(gatilho_y)), 3)
        pygame.draw.circle(tela, cor_vermelho, (int(gatilho_x), int(gatilho_y)), 1)

        # 7. Detalhes táticos
        # Trilho superior
        trilho_inicio_x = corpo_x + dx * 5
        trilho_inicio_y = corpo_y + dy * 5
        trilho_fim_x = ponta_x - dx * 8
        trilho_fim_y = ponta_y - dy * 8
        pygame.draw.line(tela, cor_metal_claro,
                        (trilho_inicio_x + perp_x * 2, trilho_inicio_y + perp_y * 2),
                        (trilho_fim_x + perp_x * 2, trilho_fim_y + perp_y * 2), 2)

        # 8. Indicador de recarga (em vez de munição)
        if self.esta_recarregando:
            # Mostrar barra de recarga
            tempo_decorrido = pygame.time.get_ticks() - self.tempo_inicio_recarga
            progresso = min(1.0, tempo_decorrido / self.tempo_recarga)

            # Desenhar barra de progresso no carregador
            for i in range(5):
                if i < int(progresso * 5):
                    barra_x = carregador_x - 2 + i
                    barra_y = carregador_y + 10 + i * 2
                    pygame.draw.rect(tela, cor_vermelho, (barra_x, barra_y, 1, 3))

        # 9. Efeito de aquecimento (quando ativa/atirando)
        if not self.esta_recarregando:
            # Criar efeito de calor no cano
            calor_intensidade = (tempo_atual % 1000) / 1000.0
            cor_calor = (255, int(100 + calor_intensidade * 155), 0)

            # Linhas de calor saindo do cano
            for i in range(3):
                heat_x = ponta_x - dx * (5 + i * 3) + random.uniform(-1, 1)
                heat_y = ponta_y - dy * (5 + i * 3) + random.uniform(-1, 1)
                pygame.draw.circle(tela, cor_calor, (int(heat_x), int(heat_y)), 1)

            # Brilho no cano
            pygame.draw.line(tela, cor_laranja,
                            (centro_x + recuo_x, centro_y + recuo_y),
                            (ponta_x, ponta_y), 1)

        # 10. Mira laser (linha pontilhada) - apontando para o jogador
        if not self.esta_recarregando:
            # Linha laser vermelha pontilhada até o jogador
            passos = int(distancia // 10)
            for i in range(0, passos, 2):  # Pular de 2 em 2 para efeito pontilhado
                laser_x = ponta_x + dx * (i * 10)
                laser_y = ponta_y + dy * (i * 10)
                pygame.draw.circle(tela, cor_vermelho, (int(laser_x), int(laser_y)), 1)

    def desenhar(self, tela, tempo_atual):
        """Sobrescreve o método desenhar para incluir a metralhadora."""
        # Desenhar o quadrado base
        super().desenhar(tela, tempo_atual)

        # A metralhadora será desenhada separadamente com a referência ao jogador
        # (feito na IA do inimigo)

    def obter_tempo_restante_estado(self):
        """
        Retorna o tempo restante no estado atual (atirando ou recarregando).
        Útil para UI ou debugging.
        """
        tempo_atual = pygame.time.get_ticks()

        if self.esta_recarregando:
            tempo_decorrido = tempo_atual - self.tempo_inicio_recarga
            return max(0, self.tempo_recarga - tempo_decorrido)
        else:
            tempo_decorrido = tempo_atual - self.iniciou_atirando
            return max(0, self.tempo_atirando - tempo_decorrido)
