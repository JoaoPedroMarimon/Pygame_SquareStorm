#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de invocação do Chucky através do amuleto místico.
Cria animação de pentagrama e aparição do Chucky no centro da arena.
OTIMIZADO: Cache de superfícies e pré-computação de valores para melhor performance.
"""

import pygame
import math
import random
from src.config import *

class ChuckyInvocation:
    """Classe para gerenciar a invocação do Chucky."""

    def __init__(self):
        # SEMPRE no centro da arena
        self.centro_x = LARGURA // 2
        self.centro_y = ALTURA_JOGO // 2
        self.x = LARGURA // 2.1
        self.y = ALTURA_JOGO // 2.2

        self.tempo_vida = 0
        self.max_tempo_vida = 900  # 10 segundos a 60 FPS

        # Estados da animação
        self.fase_pentagrama = True  # Primeira fase: desenhar pentagrama
        self.fase_chucky = False     # Segunda fase: aparecer Chucky
        self.tempo_pentagrama = 90  # 1.5 segundos para o pentagrama (acelerado)

        # Propriedades do pentagrama
        self.raio_pentagrama = 0
        self.raio_max_pentagrama = 80
        self.alpha_pentagrama = 0

        # Propriedades do Chucky
        self.escala_chucky = 0.0
        self.alpha_chucky = 0
        self.rotacao_chucky = 0
        self.flutuacao_chucky = 0
        self.portal_ativo = False
        self.portal_alpha = 0
        self.portal_raio = 0
        self.portal_rotacao = 0
        self.chucky_ativo = False  # Se o Chucky pode se mover e causar dano
        self.velocidade_x = 0
        self.velocidade_y = 0
        self.velocidade_max = 80  # Velocidade máxima do movimento
        self.mudanca_direcao_timer = 0
        self.intervalo_mudanca_direcao = 30  # Muda direção a cada 0.5 segundos

        # Hitbox do Chucky para colisões
        self.chucky_rect = pygame.Rect(self.x, self.y, 60, 80)

        # Efeitos visuais
        self.particulas_misticas = []

        # Sons (placeholders)
        self.som_invocacao_tocado = False
        self.som_aparicao_tocado = False

        # OTIMIZAÇÃO: Cache de superfícies renderizadas
        self.chucky_surface = None
        self.chucky_surface_criada = False

        # OTIMIZAÇÃO: Pré-computar valores do portal
        self._precomputar_portal()

    def _precomputar_portal(self):
        """Pré-computa valores que não mudam no portal para economizar CPU."""
        # Pré-computar ângulos das partículas do portal
        self.portal_angulos_particulas = [(i * 45) for i in range(8)]

        # Pré-computar ângulos dos raios de energia
        self.portal_angulos_raios = [(i * 60) for i in range(6)]

    def atualizar(self):
        """Atualiza a animação de invocação."""
        self.tempo_vida += 1

        if self.tempo_vida <= self.tempo_pentagrama:
            # Primeira fase: só pentagrama
            self.fase_pentagrama = True
            self.fase_chucky = False
            self._atualizar_fase_pentagrama()
        else:
            # Segunda fase: só Chucky
            if not self.fase_chucky:
                # Primeira transição para Chucky
                self.fase_pentagrama = False
                self.fase_chucky = True
                # Inicializar valores do Chucky
                self.escala_chucky = 0.0
                self.alpha_chucky = 0
                self.rotacao_chucky = 360
            self._atualizar_fase_chucky()

        # Atualizar portal
        self._atualizar_portal()
        self._atualizar_movimento_chucky()

        # Atualizar efeitos
        self._atualizar_particulas()

        return self.tempo_vida < self.max_tempo_vida

    def _atualizar_portal(self):
        """Atualiza o portal que cobre o Chucky."""
        tempo_chucky = self.tempo_vida - self.tempo_pentagrama

        # Portal aparece 15 frames antes do Chucky (0.25 segundos) - ACELERADO
        # e desaparece 30 frames depois do Chucky aparecer (0.5 segundos) - ACELERADO
        if tempo_chucky >= -15 and tempo_chucky <= 60:
            self.portal_ativo = True

            if tempo_chucky < 0:
                # Portal crescendo antes do Chucky
                progresso = (15 + tempo_chucky) / 15  # 0 a 1
                self.portal_alpha = int(255 * progresso)
                self.portal_raio = int(150 * progresso)
            elif tempo_chucky <= 30:
                # Portal no máximo durante aparição do Chucky
                self.portal_alpha = 255
                self.portal_raio = 150
            else:
                # Portal diminuindo após Chucky aparecer
                progresso = 1 - ((tempo_chucky - 30) / 30)  # 1 a 0
                self.portal_alpha = int(255 * progresso)
                self.portal_raio = int(150 * progresso)

            # Rotação constante do portal
            self.portal_rotacao += 5
        else:
            self.portal_ativo = False

            # Ativar o Chucky quando o portal se fechar
            if tempo_chucky > 60 and not self.chucky_ativo:
                self.chucky_ativo = True
                self._iniciar_movimento_chucky()

    def _desenhar_portal(self, tela):
        """Desenha um portal mágico mais bonito cobrindo o Chucky."""
        if not self.portal_ativo or self.portal_raio <= 0:
            return

        # OTIMIZAÇÃO: Reduzir número de círculos e cálculos
        tamanho = self.portal_raio * 3
        portal_surface = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        centro_surface = self.portal_raio * 1.5

        # Efeito de brilho externo (reduzido de 3 para 2)
        for i in range(2):
            raio_halo = self.portal_raio + 15 + i * 8
            alpha_halo = 30 - i * 10
            cor_halo = (200, 50, 50, alpha_halo)

            halo_surface = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo_surface, cor_halo, (raio_halo, raio_halo), raio_halo)
            halo_rect = halo_surface.get_rect(center=(centro_surface, centro_surface))
            portal_surface.blit(halo_surface, halo_rect, special_flags=pygame.BLEND_ADD)

        # OTIMIZAÇÃO: Círculos concêntricos (reduzido de 6 para 4)
        for i in range(4):
            raio_circulo = self.portal_raio - i * 12
            if raio_circulo > 0:
                intensidade = 1 - (i / 4)

                if i % 2 == 0:
                    cor_portal = (
                        int(255 * intensidade),
                        int(50 * intensidade),
                        int(50 * intensidade)
                    )
                else:
                    cor_portal = (
                        int(200 * intensidade),
                        int(20 * intensidade),
                        int(20 * intensidade)
                    )

                # OTIMIZAÇÃO: Pulso pré-calculado com menos iterações
                pulso = math.sin((self.portal_rotacao + i * 45) * 0.08) * 4
                raio_pulsante = raio_circulo + pulso

                pygame.draw.circle(portal_surface, cor_portal,
                                (int(centro_surface), int(centro_surface)),
                                int(raio_pulsante), 2)

        # OTIMIZAÇÃO: Partículas flutuantes (reduzido de 8 para 6)
        for i in range(6):
            angulo = (self.portal_rotacao * 2 + self.portal_angulos_particulas[i]) % 360
            distancia = self.portal_raio * 0.8 + math.sin((self.portal_rotacao + i * 30) * 0.05) * 10

            x = centro_surface + math.cos(math.radians(angulo)) * distancia
            y = centro_surface + math.sin(math.radians(angulo)) * distancia

            cor_particula = (
                200 + int(math.sin(angulo * 0.1) * 55),
                50,
                50
            )

            tamanho = 2 + int(math.sin((self.portal_rotacao + i * 20) * 0.1))
            pygame.draw.circle(portal_surface, cor_particula, (int(x), int(y)), tamanho)

        # Centro escuro do portal (simplificado)
        centro_raio = self.portal_raio // 3
        pygame.draw.circle(portal_surface, (40, 10, 10),
                         (int(centro_surface), int(centro_surface)),
                         centro_raio)

        # OTIMIZAÇÃO: Raios de energia (mesmos 6, mas cálculo otimizado)
        for i in range(6):
            angulo = (self.portal_rotacao * 3 + self.portal_angulos_raios[i]) % 360
            rad = math.radians(angulo)

            x1 = centro_surface + math.cos(rad) * (centro_raio + 5)
            y1 = centro_surface + math.sin(rad) * (centro_raio + 5)
            x2 = centro_surface + math.cos(rad) * (self.portal_raio * 0.6)
            y2 = centro_surface + math.sin(rad) * (self.portal_raio * 0.6)

            cor_raio = (255, 100, 100)
            pygame.draw.line(portal_surface, cor_raio, (x1, y1), (x2, y2), 2)

        # Aplicar transparência geral
        portal_surface.set_alpha(self.portal_alpha)

        # Desenhar na tela
        rect = portal_surface.get_rect(center=(self.centro_x, self.centro_y))
        tela.blit(portal_surface, rect)

    def _atualizar_fase_pentagrama(self):
        """Atualiza a fase de aparição do pentagrama."""
        progresso = self.tempo_vida / self.tempo_pentagrama

        # Pentagrama cresce gradualmente
        self.raio_pentagrama = int(self.raio_max_pentagrama * min(1.0, progresso * 1.5))
        self.alpha_pentagrama = min(255, int(255 * progresso * 2))

        # OTIMIZAÇÃO: Reduzir criação de partículas (de 30% para 15%)
        if random.random() < 0.15:
            self._criar_particula_mistica()

        # Som de invocação (uma vez)
        if not self.som_invocacao_tocado and progresso > 0.1:
            self.som_invocacao_tocado = True

    def _atualizar_fase_chucky(self):
        """Atualiza a fase de aparição do Chucky."""
        tempo_chucky = self.tempo_vida - self.tempo_pentagrama

        if tempo_chucky <= 30:  # Primeiros 0.5 segundos: Chucky aparece - ACELERADO
            aparicao_prog = tempo_chucky / 30
            self.escala_chucky = aparicao_prog * 1.2  # Cresce um pouco além do normal
            self.alpha_chucky = min(255, int(255 * aparicao_prog))
            self.rotacao_chucky = (1 - aparicao_prog) * 360  # Gira enquanto aparece

            # Som de aparição (uma vez)
            if not self.som_aparicao_tocado and aparicao_prog > 0.5:
                self.som_aparicao_tocado = True

        elif tempo_chucky <= 60:  # Próximos 0.5 segundos: estabiliza - ACELERADO
            self.escala_chucky = max(1.0, 1.2 - (tempo_chucky - 30) / 30 * 0.2)
            self.alpha_chucky = 255
            self.rotacao_chucky = 0

        else:  # Resto do tempo: flutua menacingly
            self.escala_chucky = 1.0
            self.alpha_chucky = 255

    def _criar_particula_mistica(self):
        """Cria uma partícula mística ao redor do pentagrama."""
        angulo = random.uniform(0, 2 * math.pi)
        distancia = random.uniform(60, 120)
        x = self.centro_x + math.cos(angulo) * distancia
        y = self.centro_y + math.sin(angulo) * distancia

        particula = {
            'x': x,
            'y': y,
            'vel_x': math.cos(angulo + math.pi) * random.uniform(0.5, 2),
            'vel_y': math.sin(angulo + math.pi) * random.uniform(0.5, 2),
            'vida': random.randint(30, 80),
            'cor': random.choice([(200, 150, 255), (150, 100, 200), (255, 100, 150)]),
            'tamanho': random.randint(2, 5)
        }
        self.particulas_misticas.append(particula)

    def _atualizar_particulas(self):
        """Atualiza as partículas místicas."""
        for particula in self.particulas_misticas[:]:
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 1

            if particula['vida'] <= 0:
                self.particulas_misticas.remove(particula)

    def desenhar(self, tela):
        """Desenha toda a invocação na tela."""
        # Desenhar APENAS o Chucky (visível normalmente)
        if self.fase_chucky:
            self._desenhar_chucky(tela)

    def desenhar_background(self, tela):
        """Desenha os elementos de fundo (pentagrama e portal) que devem ficar atrás de tudo."""
        # Pentagrama fica visível durante toda a invocação (na camada de fundo)
        if self.tempo_vida <= self.max_tempo_vida:
            self._desenhar_pentagrama(tela)

        # Portal também fica na camada de fundo
        self._desenhar_portal(tela)

    def _desenhar_pentagrama(self, tela):
        """Desenha o pentagrama satânico com animação assustadora."""
        if self.raio_pentagrama <= 0:
            return

        raio_final = self.raio_pentagrama * 2.2

        # Controle de crescimento inicial
        tempo = pygame.time.get_ticks()

        if not hasattr(self, 'tempo_inicio_pentagrama'):
            self.tempo_inicio_pentagrama = tempo

        tempo_crescimento = tempo - self.tempo_inicio_pentagrama
        duracao_crescimento = 1500  # 1.5 segundos (acelerado)

        if tempo_crescimento < duracao_crescimento:
            progresso = tempo_crescimento / duracao_crescimento
            progresso = 1 - (1 - progresso) ** 3  # Easing
            raio_atual = int(raio_final * progresso)
            crescendo = True
        else:
            raio_atual = int(raio_final)
            crescendo = False

        # OTIMIZAÇÃO: Simplificar efeitos durante crescimento
        if crescendo:
            # Círculos de energia (reduzido de 5 para 3)
            for i in range(3):
                raio_onda = (progresso * 200 + i * 50) % 250
                if raio_onda > 0:
                    alpha_onda = int(100 * (1 - raio_onda / 250))
                    if alpha_onda > 10:  # Skip desenhar se alpha muito baixo
                        onda_surface = pygame.Surface((raio_onda * 2 + 50, raio_onda * 2 + 50), pygame.SRCALPHA)
                        pygame.draw.circle(onda_surface, (150, 0, 0),
                                        (raio_onda + 25, raio_onda + 25), int(raio_onda), 3)
                        onda_surface.set_alpha(alpha_onda)
                        rect_onda = onda_surface.get_rect(center=(self.centro_x, self.centro_y))
                        tela.blit(onda_surface, rect_onda)

        # Alpha com tremulação
        alpha_base = self.alpha_pentagrama

        if crescendo:
            alpha_pentagrama = min(255, alpha_base + progresso * 100)
            pulso_crescimento = abs(math.sin(tempo * 0.05)) * 50
            alpha_pentagrama = min(255, alpha_pentagrama + pulso_crescimento)
        else:
            tremulacao = abs(math.sin(tempo * 0.02)) * 25 + 10
            alpha_pentagrama = min(255, alpha_base + tremulacao)

        # Criar superfície para o pentagrama
        tamanho_surface = raio_atual * 2 + 200
        pentagrama_surface = pygame.Surface((tamanho_surface, tamanho_surface), pygame.SRCALPHA)
        centro_surface = tamanho_surface // 2

        desenhar_pentagrama_otimizado(pentagrama_surface,
                        centro_surface,
                        centro_surface,
                        raio_atual,
                        5,
                        crescendo,
                        progresso if crescendo else 1.0)

        # Aplicar transparência
        pentagrama_surface.set_alpha(int(alpha_pentagrama))

        # Desenhar com tremor
        if not crescendo:
            intensidade_tremor = 1 if alpha_pentagrama > 150 else 0.5
            tremor_x = random.randint(-2, 2) * intensidade_tremor
            tremor_y = random.randint(-2, 2) * intensidade_tremor
        else:
            if progresso > 0.7:
                tremor_crescimento = (progresso - 0.7) / 0.3
                tremor_x = random.randint(-4, 4) * tremor_crescimento
                tremor_y = random.randint(-4, 4) * tremor_crescimento
            else:
                tremor_x = 0
                tremor_y = 0

        rect = pentagrama_surface.get_rect(center=(self.centro_x + tremor_x, self.centro_y + tremor_y))
        tela.blit(pentagrama_surface, rect)

    def _desenhar_chucky(self, tela):
        # Ajustar posição com flutuação
        if self.chucky_ativo:
            chucky_x = self.x
            chucky_y = self.y + self.flutuacao_chucky
        else:
            # Durante aparição: usar coordenadas centralizadas
            chucky_x = self.centro_x - 30  # Ajustar para centralizar o sprite do Chucky
            chucky_y = self.centro_y - 40 + self.flutuacao_chucky  # Centralizar verticalmente + flutuação        
        
        # Pernas (calça jeans azul)
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 20, chucky_y + 55, 8, 20))
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 32, chucky_y + 55, 8, 20))
        
        # Tênis vermelhos (característicos do Chucky)
        pygame.draw.ellipse(tela, (220, 20, 60), (chucky_x + 18, chucky_y + 72, 12, 8))
        pygame.draw.ellipse(tela, (220, 20, 60), (chucky_x + 30, chucky_y + 72, 12, 8))
        
        # Sola dos tênis (branca)
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 18, chucky_y + 76, 12, 4))
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 30, chucky_y + 76, 12, 4))
        
        # Detalhes dos tênis (cadarços/linhas)
        pygame.draw.line(tela, BRANCO, (chucky_x + 20, chucky_y + 74), (chucky_x + 28, chucky_y + 74), 1)
        pygame.draw.line(tela, BRANCO, (chucky_x + 32, chucky_y + 74), (chucky_x + 40, chucky_y + 74), 1)
        
        # Camisa listrada por baixo (mangas completas cobrindo todo o braço)
        # Mangas listradas coloridas - cores do Chucky
        cores_listras = [(220, 20, 60), (34, 139, 34), (30, 144, 255), (255, 140, 0), (148, 0, 211)]
        
        # Manga esquerda completa (cobrindo todo o braço)
        for i in range(10):  # mais listras para cobrir todo o braço
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 8, chucky_y + 30 + i*3, 14, 2))
        
        # Manga direita completa (cobrindo todo o braço)
        for i in range(10):  # mais listras para cobrir todo o braço
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 38, chucky_y + 30 + i*3, 14, 2))
            
        # Parte do peito da camisa listrada (visível)
        for i in range(3):
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 22, chucky_y + 26 + i*2, 16, 1))
        
        # Macacão jeans azul (corpo principal) - por cima da camisa
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 18, chucky_y + 32, 24, 28))
        
        # Alças do macacão
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 22, chucky_y + 24, 4, 12))
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 34, chucky_y + 24, 4, 12))
        
        # Botões das alças (detalhados)
        pygame.draw.circle(tela, (139, 69, 19), (chucky_x + 24, chucky_y + 28), 2)  # botão marrom
        pygame.draw.circle(tela, PRETO, (chucky_x + 24, chucky_y + 28), 1)  # centro do botão
        pygame.draw.circle(tela, (139, 69, 19), (chucky_x + 36, chucky_y + 28), 2)
        pygame.draw.circle(tela, PRETO, (chucky_x + 36, chucky_y + 28), 1)
        
        # BOLSO NO PEITO DO MACACÃO (característico do Chucky)
        pygame.draw.rect(tela, (60, 110, 160), (chucky_x + 24, chucky_y + 36, 12, 8))  # bolso um pouco mais escuro
        # Costura do bolso
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 36), (chucky_x + 36, chucky_y + 36), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 36), (chucky_x + 24, chucky_y + 44), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 36, chucky_y + 36), (chucky_x + 36, chucky_y + 44), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 44), (chucky_x + 36, chucky_y + 44), 1)
        
        # Costuras do macacão
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 18, chucky_y + 45), (chucky_x + 42, chucky_y + 45), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 30, chucky_y + 32), (chucky_x + 30, chucky_y + 60), 1)
        
        # Mãos (sem braços visíveis - só as mãos saindo das mangas)
        pygame.draw.circle(tela, (255, 220, 177), (chucky_x + 13, chucky_y + 60), 3)
        pygame.draw.circle(tela, (255, 220, 177), (chucky_x + 47, chucky_y + 60), 3)
        
        # Cabeça (formato mais oval como o Chucky real)
        pygame.draw.ellipse(tela, (255, 220, 177), (chucky_x + 14, chucky_y + 8, 32, 28))
        
        # Cabelo ruivo detalhado (estilo característico do Chucky)
        # Base do cabelo - formato mais volumoso e bagunçado
        cabelo_cor_base = (180, 50, 50)
        cabelo_cor_clara = (220, 80, 60)
        cabelo_cor_escura = (150, 30, 30)
        
        # Volume principal do cabelo (formato irregular)
        pygame.draw.ellipse(tela, cabelo_cor_base, (chucky_x + 10, chucky_y + 1, 40, 22))
        
        # Cabelo na parte de trás (volume extra)
        pygame.draw.ellipse(tela, cabelo_cor_escura, (chucky_x + 8, chucky_y + 3, 44, 18))
        
        # Mechas superiores bagunçadas (em pé)
        mechas_topo = [
            (chucky_x + 15, chucky_y - 2, chucky_x + 13, chucky_y + 8),
            (chucky_x + 20, chucky_y - 1, chucky_x + 19, chucky_y + 6),
            (chucky_x + 25, chucky_y - 3, chucky_x + 24, chucky_y + 7),
            (chucky_x + 30, chucky_y - 2, chucky_x + 29, chucky_y + 6),
            (chucky_x + 35, chucky_y - 1, chucky_x + 34, chucky_y + 7),
            (chucky_x + 40, chucky_y - 2, chucky_x + 39, chucky_y + 8),
            (chucky_x + 45, chucky_y - 1, chucky_x + 44, chucky_y + 6)
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(mechas_topo):
            cor = cabelo_cor_clara if i % 2 == 0 else cabelo_cor_base
            pygame.draw.line(tela, cor, (x1, y1), (x2, y2), 4)
            # Mechas menores para textura
            pygame.draw.line(tela, cabelo_cor_escura, (x1 + 1, y1 + 1), (x2 - 1, y2 - 1), 2)
        
        # Franja bagunçada característica (caindo na testa)
        franja_mechas = [
            (chucky_x + 12, chucky_y + 8, chucky_x + 16, chucky_y + 18),
            (chucky_x + 16, chucky_y + 6, chucky_x + 18, chucky_y + 16),
            (chucky_x + 20, chucky_y + 7, chucky_x + 21, chucky_y + 17),
            (chucky_x + 24, chucky_y + 5, chucky_x + 25, chucky_y + 15),
            (chucky_x + 28, chucky_y + 6, chucky_x + 29, chucky_y + 16),
            (chucky_x + 32, chucky_y + 7, chucky_x + 33, chucky_y + 17),
            (chucky_x + 36, chucky_y + 5, chucky_x + 37, chucky_y + 15),
            (chucky_x + 40, chucky_y + 6, chucky_x + 42, chucky_y + 16),
            (chucky_x + 44, chucky_y + 8, chucky_x + 48, chucky_y + 18)
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(franja_mechas):
            cor = [cabelo_cor_clara, cabelo_cor_base, cabelo_cor_escura][i % 3]
            pygame.draw.line(tela, cor, (x1, y1), (x2 + random.randint(-2, 2), y2), 3)
        
        # Mechas laterais longas (características do Chucky)
        # Lado esquerdo
        laterais_esq = [
            (chucky_x + 8, chucky_y + 10, chucky_x + 6, chucky_y + 22),
            (chucky_x + 10, chucky_y + 12, chucky_x + 4, chucky_y + 25),
            (chucky_x + 12, chucky_y + 14, chucky_x + 8, chucky_y + 28),
            (chucky_x + 14, chucky_y + 16, chucky_x + 10, chucky_y + 30)
        ]
        
        for x1, y1, x2, y2 in laterais_esq:
            pygame.draw.line(tela, cabelo_cor_base, (x1, y1), (x2, y2), 4)
            pygame.draw.line(tela, cabelo_cor_escura, (x1 + 1, y1), (x2 + 1, y2), 2)
        
        # Lado direito
        laterais_dir = [
            (chucky_x + 52, chucky_y + 10, chucky_x + 54, chucky_y + 22),
            (chucky_x + 50, chucky_y + 12, chucky_x + 56, chucky_y + 25),
            (chucky_x + 48, chucky_y + 14, chucky_x + 52, chucky_y + 28),
            (chucky_x + 46, chucky_y + 16, chucky_x + 50, chucky_y + 30)
        ]
        
        for x1, y1, x2, y2 in laterais_dir:
            pygame.draw.line(tela, cabelo_cor_base, (x1, y1), (x2, y2), 4)
            pygame.draw.line(tela, cabelo_cor_escura, (x1 - 1, y1), (x2 - 1, y2), 2)
        
        # Mechas traseiras (atrás das orelhas)

        
        # Testa mais proeminente
        pygame.draw.ellipse(tela, (245, 210, 167), (chucky_x + 18, chucky_y + 12, 24, 8))
        
        # Olhos azuis mais expressivos e malignos
        # Formato amendoado dos olhos
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 20, chucky_y + 18, 8, 6))
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 32, chucky_y + 18, 8, 6))
        
        # Íris azul intensa
        pygame.draw.circle(tela, (0, 100, 200), (chucky_x + 24, chucky_y + 21), 3)
        pygame.draw.circle(tela, (0, 100, 200), (chucky_x + 36, chucky_y + 21), 3)
        
        # Pupilas dilatadas (efeito sinistro)
        pygame.draw.circle(tela, PRETO, (chucky_x + 24, chucky_y + 21), 2)
        pygame.draw.circle(tela, PRETO, (chucky_x + 36, chucky_y + 21), 2)
        
        # Reflexos nos olhos
        pygame.draw.circle(tela, BRANCO, (chucky_x + 25, chucky_y + 20), 1)
        pygame.draw.circle(tela, BRANCO, (chucky_x + 37, chucky_y + 20), 1)
        
        # Sobrancelhas grossas e franzidas (expressão raivosa)
        pygame.draw.arc(tela, (139, 69, 19), (chucky_x + 18, chucky_y + 15, 12, 8), 0.2, 2.8, 3)
        pygame.draw.arc(tela, (139, 69, 19), (chucky_x + 30, chucky_y + 15, 12, 8), 0.3, 2.9, 3)
        
        # Rugas de expressão na testa
        pygame.draw.line(tela, (220, 190, 150), (chucky_x + 22, chucky_y + 14), (chucky_x + 26, chucky_y + 13), 1)
        pygame.draw.line(tela, (220, 190, 150), (chucky_x + 34, chucky_y + 13), (chucky_x + 38, chucky_y + 14), 1)
        
        # Nariz mais definido e pontudo
        pygame.draw.polygon(tela, (240, 200, 160), [(chucky_x + 30, chucky_y + 22), 
                                                (chucky_x + 28, chucky_y + 26), 
                                                (chucky_x + 32, chucky_y + 26)])
        # Narinas
        pygame.draw.circle(tela, (200, 170, 130), (chucky_x + 29, chucky_y + 25), 1)
        pygame.draw.circle(tela, (200, 170, 130), (chucky_x + 31, chucky_y + 25), 1)
        
        # Boca característica - sorriso sinistro largo
        pygame.draw.arc(tela, (120, 0, 0), (chucky_x + 22, chucky_y + 27, 16, 8), 0, math.pi, 3)
        
        # Dentes mais detalhados
        for i in range(6):
            pygame.draw.rect(tela, (245, 245, 220), (chucky_x + 24 + i*2, chucky_y + 29, 1, 3))
        
        # Lábios
        pygame.draw.arc(tela, (200, 120, 120), (chucky_x + 22, chucky_y + 27, 16, 6), 0, math.pi, 1)
        
        # Sardas características do Chucky (padrão fixo)
        sardas_pos = [
            (chucky_x + 19, chucky_y + 20), (chucky_x + 17, chucky_y + 23), (chucky_x + 21, chucky_y + 25),
            (chucky_x + 39, chucky_y + 19), (chucky_x + 41, chucky_y + 22), (chucky_x + 37, chucky_y + 24),
            (chucky_x + 26, chucky_y + 19), (chucky_x + 34, chucky_y + 20), (chucky_x + 30, chucky_y + 24)
        ]
        
        for x_sarda, y_sarda in sardas_pos:
            pygame.draw.circle(tela, (200, 150, 100), (x_sarda, y_sarda), 1)
        
        # Cicatrizes icônicas do Chucky
        # Cicatriz na bochecha esquerda
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 18, chucky_y + 22), (chucky_x + 16, chucky_y + 26), 2)
        pygame.draw.line(tela, (180, 100, 100), (chucky_x + 17, chucky_y + 23), (chucky_x + 15, chucky_y + 25), 1)
        
        # Cicatriz na bochecha direita
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 42, chucky_y + 24), (chucky_x + 44, chucky_y + 28), 2)
        pygame.draw.line(tela, (180, 100, 100), (chucky_x + 43, chucky_y + 25), (chucky_x + 45, chucky_y + 27), 1)
        
        # Cicatriz pequena na testa
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 28, chucky_y + 16), (chucky_x + 26, chucky_y + 18), 1)
        
        # Sombras para dar profundidade ao rosto
        pygame.draw.arc(tela, (230, 190, 150), (chucky_x + 16, chucky_y + 20, 8, 10), 1.5, 3.0, 2)
        pygame.draw.arc(tela, (230, 190, 150), (chucky_x + 36, chucky_y + 20, 8, 10), 0, 1.5, 2)
        
        # ===== FACA MELHORADA E MAIS BONITA =====
        
        # Base da mão direita
        mao_x = chucky_x + 47
        mao_y = chucky_y + 60

        # Parâmetros de inclinação e tamanho da faca
        angle = math.radians(-35)  # ângulo da faca
        handle_len = 15
        blade_len = 35
        
        # Vetores de direção
        dx_h = math.cos(angle) * handle_len
        dy_h = math.sin(angle) * handle_len
        dx_b = math.cos(angle) * blade_len
        dy_b = math.sin(angle) * blade_len
        
        # Vetor perpendicular para espessura
        perp_angle = angle + math.pi/2
        
        # ===== CABO DETALHADO =====
        
        # Base do cabo (madeira escura)
        cabo_points = []
        cabo_width = 4
        for i in range(4):
            factor = i / 3.0
            px = mao_x + dx_h * factor
            py = mao_y + dy_h * factor
            width = cabo_width - i * 0.5  # afunila levemente
            
            perp_dx = math.cos(perp_angle) * width / 2
            perp_dy = math.sin(perp_angle) * width / 2
            
            if i == 0:
                cabo_points.extend([(px + perp_dx, py + perp_dy), (px - perp_dx, py - perp_dy)])
            elif i == 3:
                cabo_points.extend([(px - perp_dx, py - perp_dy), (px + perp_dx, py + perp_dy)])
        
        # Desenhar cabo (madeira)
        pygame.draw.polygon(tela, (101, 67, 33), cabo_points)
        
        # Detalhes do cabo (textura de madeira)
        for i in range(3):
            start_x = mao_x + dx_h * (i / 3.0) * 0.8
            start_y = mao_y + dy_h * (i / 3.0) * 0.8
            end_x = mao_x + dx_h * ((i + 1) / 3.0) * 0.8
            end_y = mao_y + dy_h * ((i + 1) / 3.0) * 0.8
            pygame.draw.line(tela, (80, 50, 25), (start_x, start_y), (end_x, end_y), 1)
        
        # Pommel (extremidade do cabo)
        pommel_x = mao_x - dx_h * 0.1
        pommel_y = mao_y - dy_h * 0.1
        pygame.draw.circle(tela, (70, 45, 20), (int(pommel_x), int(pommel_y)), 3)
        pygame.draw.circle(tela, (50, 30, 15), (int(pommel_x), int(pommel_y)), 2)
        
        # ===== GUARDA (CROSSGUARD) =====
        
        guard_start_x = mao_x + dx_h
        guard_start_y = mao_y + dy_h
        guard_length = 8
        guard_thickness = 2
        
        # Pontos da guarda
        guard_perp_dx = math.cos(perp_angle) * guard_length / 2
        guard_perp_dy = math.sin(perp_angle) * guard_length / 2
        
        guard_points = [
            (guard_start_x + guard_perp_dx, guard_start_y + guard_perp_dy),
            (guard_start_x - guard_perp_dx, guard_start_y - guard_perp_dy),
            (guard_start_x - guard_perp_dx + dx_b * 0.05, guard_start_y - guard_perp_dy + dy_b * 0.05),
            (guard_start_x + guard_perp_dx + dx_b * 0.05, guard_start_y + guard_perp_dy + dy_b * 0.05)
        ]
        
        # Desenhar guarda (metal escuro)
        pygame.draw.polygon(tela, (60, 60, 60), guard_points)
        
        # Brilho na guarda
        pygame.draw.line(tela, (120, 120, 120), 
                        (guard_start_x + guard_perp_dx * 0.7, guard_start_y + guard_perp_dy * 0.7),
                        (guard_start_x - guard_perp_dx * 0.7, guard_start_y - guard_perp_dy * 0.7), 2)
        
        # ===== LÂMINA DETALHADA =====
        
        blade_start_x = guard_start_x
        blade_start_y = guard_start_y
        blade_end_x = blade_start_x + dx_b
        blade_end_y = blade_start_y + dy_b
        
        # Largura da lâmina (afunila até a ponta)
        blade_base_width = 6
        blade_tip_width = 1
        
        # Pontos da lâmina
        blade_points = []
        
        # Base da lâmina (larga)
        base_perp_dx = math.cos(perp_angle) * blade_base_width / 2
        base_perp_dy = math.sin(perp_angle) * blade_base_width / 2
        
        # Meio da lâmina
        mid_x = blade_start_x + dx_b * 0.7
        mid_y = blade_start_y + dy_b * 0.7
        mid_perp_dx = math.cos(perp_angle) * blade_tip_width / 2
        mid_perp_dy = math.sin(perp_angle) * blade_tip_width / 2
        
        # Construir polígono da lâmina
        blade_points = [
            (blade_start_x + base_perp_dx, blade_start_y + base_perp_dy),  # base direita
            (mid_x + mid_perp_dx, mid_y + mid_perp_dy),                   # meio direita
            (blade_end_x, blade_end_y),                                   # ponta
            (mid_x - mid_perp_dx, mid_y - mid_perp_dy),                   # meio esquerda
            (blade_start_x - base_perp_dx, blade_start_y - base_perp_dy)  # base esquerda
        ]
        
        # Desenhar lâmina principal (aço brilhante)
        pygame.draw.polygon(tela, (200, 200, 210), blade_points)
        
        # Sombra na lâmina (lado inferior)
        shadow_points = [
            (blade_start_x - base_perp_dx, blade_start_y - base_perp_dy),
            (mid_x - mid_perp_dx, mid_y - mid_perp_dy),
            (blade_end_x, blade_end_y),
            (blade_start_x, blade_start_y)
        ]
        pygame.draw.polygon(tela, (160, 160, 170), shadow_points)
        
        # Fio da lâmina (linha mais escura)
        pygame.draw.line(tela, (140, 140, 150), 
                        (mid_x + mid_perp_dx, mid_y + mid_perp_dy),
                        (blade_end_x, blade_end_y), 2)
        pygame.draw.line(tela, (140, 140, 150), 
                        (mid_x - mid_perp_dx, mid_y - mid_perp_dy),
                        (blade_end_x, blade_end_y), 2)
        
        # Sulco central (fuller)
        fuller_start_x = blade_start_x + dx_b * 0.1
        fuller_start_y = blade_start_y + dy_b * 0.1
        fuller_end_x = blade_start_x + dx_b * 0.8
        fuller_end_y = blade_start_y + dy_b * 0.8
        pygame.draw.line(tela, (180, 180, 190), 
                        (fuller_start_x, fuller_start_y),
                        (fuller_end_x, fuller_end_y), 2)

    def _iniciar_movimento_chucky(self):
        """Inicia o movimento aleatório do Chucky."""
        self.velocidade_x = random.uniform(-self.velocidade_max, self.velocidade_max)
        self.velocidade_y = random.uniform(-self.velocidade_max, self.velocidade_max)
        self.mudanca_direcao_timer = self.intervalo_mudanca_direcao

    def _atualizar_movimento_chucky(self):
        """Atualiza o movimento louco do Chucky."""
        if not self.chucky_ativo:
            return

        # Mudar direção periodicamente
        self.mudanca_direcao_timer -= 1
        if self.mudanca_direcao_timer <= 0:
            self.velocidade_x = random.uniform(-self.velocidade_max, self.velocidade_max)
            self.velocidade_y = random.uniform(-self.velocidade_max, self.velocidade_max)
            self.mudanca_direcao_timer = random.randint(8, 25)

        # Mover o Chucky
        self.x += self.velocidade_x
        self.y += self.velocidade_y

        # Manter dentro dos limites
        if self.x <= 0 or self.x >= LARGURA - 60:
            self.velocidade_x = -self.velocidade_x
            self.x = max(0, min(LARGURA - 60, self.x))

        if self.y <= 0 or self.y >= ALTURA_JOGO - 80:
            self.velocidade_y = -self.velocidade_y
            self.y = max(0, min(ALTURA_JOGO - 80, self.y))

        # Atualizar hitbox
        self.chucky_rect.x = self.x
        self.chucky_rect.y = self.y

    def verificar_colisao_inimigos(self, inimigos):
        """Verifica colisão com inimigos e causa dano."""
        if not self.chucky_ativo:
            return False

        for inimigo in inimigos:
            if inimigo.vidas > 0 and self.chucky_rect.colliderect(inimigo.rect):
                if inimigo.tomar_dano():
                    direcao_x = self.x - inimigo.x
                    direcao_y = self.y - inimigo.y
                    magnitude = math.sqrt(direcao_x**2 + direcao_y**2)

                    if magnitude > 0:
                        self.velocidade_x = (direcao_x / magnitude) * self.velocidade_max * 1.5
                        self.velocidade_y = (direcao_y / magnitude) * self.velocidade_max * 1.5

                    return True

        return False


# OTIMIZAÇÃO: Pré-computar pontos do pentagrama
_pontos_pentagrama_cache = {}

def desenhar_pentagrama_otimizado(tela, centro_x, centro_y, raio, espessura, crescendo=False, progresso=1.0):
    """Desenha pentagrama com otimizações de performance."""

    # Cores (sempre vermelho para consistência visual)
    vermelho_escuro = (100, 0, 0)
    vermelho_sangue = (255, 10, 10)
    vermelho_brilhante = (255, 40, 40)
    preto_profundo = (20, 0, 0)

    # OTIMIZAÇÃO: Círculos simplificados (menos camadas)
    for offset in range(6, 0, -2):  # Pulando de 2 em 2 ao invés de 1 em 1
        intensidade = 1.0 - (offset / 6.0)
        cor_atual = (
            int(vermelho_escuro[0] * intensidade + 30),
            0,
            0
        )
        pygame.draw.circle(tela, cor_atual, (centro_x, centro_y + offset),
                         raio + offset * 2, espessura + offset)

    # Círculos principais
    pygame.draw.circle(tela, preto_profundo, (centro_x, centro_y), raio + 8, espessura * 3)
    pygame.draw.circle(tela, vermelho_sangue, (centro_x, centro_y), raio, espessura * 3)
    pygame.draw.circle(tela, vermelho_brilhante, (centro_x, centro_y), raio - 3, espessura * 2)

    # Calcular pontos da estrela (com cache)
    cache_key = raio
    if cache_key not in _pontos_pentagrama_cache:
        pontos = []
        rotacao_diagonal = math.pi / 5

        for i in range(5):
            angulo = (i * 2 * math.pi / 5) - math.pi/2 + rotacao_diagonal
            x = raio * 0.85 * math.cos(angulo)
            y = raio * 0.85 * math.sin(angulo)
            pontos.append((x, y))

        _pontos_pentagrama_cache[cache_key] = pontos

    pontos = _pontos_pentagrama_cache[cache_key]
    pontos_tela = [(centro_x + px, centro_y + py) for px, py in pontos]

    # Desenhar linhas da estrela
    for i in range(5):
        inicio = pontos_tela[i]
        fim = pontos_tela[(i + 2) % 5]

        pygame.draw.line(tela, (10, 0, 0), inicio, fim, espessura * 5)
        pygame.draw.line(tela, vermelho_escuro, inicio, fim, espessura * 3)
        pygame.draw.line(tela, vermelho_sangue, inicio, fim, espessura * 2)
        pygame.draw.line(tela, vermelho_brilhante, inicio, fim, espessura)

    # OTIMIZAÇÃO: Gotas de sangue reduzidas (de 30 para 12)
    tempo = pygame.time.get_ticks()
    num_gotas = 12

    for i in range(num_gotas):
        if crescendo:
            distancia_gota = random.randint(0, int(raio * progresso + 40))
            angulo_gota = random.uniform(0, 2 * math.pi)
            base_x = centro_x + distancia_gota * math.cos(angulo_gota)
            base_y = centro_y + distancia_gota * math.sin(angulo_gota)
        else:
            base_x = centro_x + random.randint(-raio - 40, raio + 40)
            base_y = centro_y + random.randint(-raio - 40, raio + 40)

        movimento_x = math.sin(tempo * 0.005 + i) * 3
        movimento_y = math.cos(tempo * 0.003 + i) * 2

        gota_x = base_x + movimento_x
        gota_y = base_y + movimento_y

        tamanho_gota = random.randint(3, 7)

        pygame.draw.circle(tela, vermelho_sangue, (int(gota_x), int(gota_y)), tamanho_gota)

    # Centro do pentagrama
    centro_raio = 12
    pygame.draw.circle(tela, (0, 0, 0), (centro_x, centro_y), centro_raio + 2)
    pygame.draw.circle(tela, vermelho_sangue, (centro_x, centro_y), centro_raio)
    pygame.draw.circle(tela, (0, 0, 0), (centro_x, centro_y), 3)


# Lista global para gerenciar invocações ativas
invocacoes_ativas = []

def criar_invocacao_chucky(pos_mouse=None):
    """Cria uma nova invocação do Chucky sempre no centro da arena."""
    if len(invocacoes_ativas) == 0:
        invocacao = ChuckyInvocation()
        invocacoes_ativas.append(invocacao)
        return True
    return False

def atualizar_invocacoes():
    """Atualiza todas as invocações ativas."""
    for invocacao in invocacoes_ativas[:]:
        if not invocacao.atualizar():
            invocacoes_ativas.remove(invocacao)

def atualizar_invocacoes_com_inimigos(inimigos, particulas, flashes):
    """Atualiza todas as invocações ativas e verifica colisões com inimigos."""
    for invocacao in invocacoes_ativas[:]:
        if not invocacao.atualizar():
            invocacoes_ativas.remove(invocacao)
        else:
            if invocacao.verificar_colisao_inimigos(inimigos):
                from src.entities.particula import criar_explosao
                explosao = criar_explosao(
                    invocacao.x + 30,
                    invocacao.y + 40,
                    (255, 50, 50),
                    particulas,
                    30
                )
                flashes.append(explosao)

def desenhar_invocacoes(tela):
    """Desenha todas as invocações ativas (apenas o Chucky)."""
    for invocacao in invocacoes_ativas:
        invocacao.desenhar(tela)

def desenhar_invocacoes_background(tela):
    """Desenha os elementos de fundo das invocações (pentagrama e portal)."""
    for invocacao in invocacoes_ativas:
        invocacao.desenhar_background(tela)

def tem_invocacao_ativa():
    """Verifica se há alguma invocação ativa."""
    return len(invocacoes_ativas) > 0

def limpar_invocacoes():
    """Limpa todas as invocações ativas (usar ao trocar de fase)."""
    global invocacoes_ativas
    invocacoes_ativas.clear()
