#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Boss VelocityCyan - Boss rápido e ágil da Fase 20.
Focado em velocidade extrema, ataques rápidos e movimentação imprevisível.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.entities.particula import criar_explosao
from src.utils.sound import gerar_som_explosao, gerar_som_tiro, gerar_som_dano


class BossVelocityCyan:
    """
    Boss VelocityCyan - Boss extremamente rápido e ágil.
    """

    def __init__(self, x, y):
        # Propriedades básicas
        self.x = x
        self.y = y
        self.tamanho_base = TAMANHO_QUADRADO * 3
        self.tamanho = self.tamanho_base
        self.cor_principal = (50, 150, 200)  # Ciano escuro
        self.cor_secundaria = (0, 255, 255)  # Ciano brilhante
        self.cor_brilho = (150, 255, 255)

        # Sistema de vida com fases
        self.vidas_max = 40
        self.vidas = self.vidas_max
        self.fase_boss = 1

        # Boss não congela após morte do jogador
        self.congelado_por_morte_jogador = False

        # Posicionamento
        self.rect = pygame.Rect(x, y, self.tamanho, self.tamanho)
        self.velocidade_base = 4.5 * 5.0  # MESMA velocidade do inimigo ciano normal
        self.velocidade = self.velocidade_base

        # Sistema de movimentação independente (não persegue o jogador)
        # Boss se move em direções aleatórias com mudanças periódicas
        self.direcao_x = random.choice([-1, 1])
        self.direcao_y = random.choice([-1, 1])
        self.tempo_ultima_mudanca_direcao = 0
        self.intervalo_mudanca_direcao = random.randint(1000, 2500)  # Muda direção a cada 1-2.5s

        # Sistema de ataques - Focado em velocidade e quantidade
        self.tempo_ultimo_ataque = 0
        self.padroes_ataque = [
            "rajada_veloz", "chuva_rapida", "dash_ataque",
            "ondas_velocidade", "explosao_circular", "tiros_rastreadores"
        ]
        self.ataque_atual = None
        self.cooldown_ataque = 1200  # Ataca mais rápido que Boss Fusion

        # Sistema de invocação - DESATIVADO
        self.pode_invocar = False
        self.tempo_ultima_invocacao = 0
        self.cooldown_invocacao = 999999
        self.max_invocacoes = 0

        # Efeitos visuais
        self.pulsacao = 0
        self.tempo_pulsacao = 0
        self.particulas_aura = []
        self.energia_acumulada = 0
        self.rastro_movimento = []

        # Estados especiais
        self.invulneravel = False
        self.tempo_invulneravel = 0
        self.duracao_invulneravel = 0
        self.carregando_ataque = False
        self.tempo_carregamento = 0
        self.tempo_carregamento_necessario = 600  # Carrega MUITO rápido
        self.ataque_pronto_para_executar = False

        # ID único
        self.id = id(self)

        print(f"⚡ Boss VelocityCyan criado! Vida: {self.vidas}/{self.vidas_max}")

    def atualizar_fase(self):
        """Atualiza a fase do boss."""
        vida_porcentagem = self.vidas / self.vidas_max

        if vida_porcentagem > 0.66:
            nova_fase = 1
        elif vida_porcentagem > 0.33:
            nova_fase = 2
        else:
            nova_fase = 3

        if nova_fase != self.fase_boss:
            self.fase_boss = nova_fase
            self.aplicar_mudanca_fase()

    def aplicar_mudanca_fase(self):
        """Mudanças de fase - Velocidade MANTIDA (igual ao ciano), apenas ataques ficam mais rápidos."""
        print(f"⚡ VelocityCyan entrou na FASE {self.fase_boss}!")

        if self.fase_boss == 2:
            # Velocidade PERMANECE a mesma do inimigo ciano normal
            self.cooldown_ataque = 1000  # Ataca ainda mais rápido
            self.cor_principal = (30, 100, 180)
            self.tempo_carregamento_necessario = 500

        elif self.fase_boss == 3:
            # Velocidade PERMANECE a mesma do inimigo ciano normal
            self.cooldown_ataque = 800  # Ataca MUITO rápido
            self.cor_principal = (10, 50, 150)
            self.tamanho = int(self.tamanho_base * 1.15)
            self.rect.width = self.tamanho
            self.rect.height = self.tamanho
            self.tempo_carregamento_necessario = 400

    def atualizar(self, tempo_atual, jogador, inimigos):
        """Atualização principal."""
        self.atualizar_fase()

        # Sistema de movimentação simples (evitando o jogador)
        self.atualizar_movimento(jogador)

        # Manter dentro da tela
        self.x = max(0, min(self.x, LARGURA - self.tamanho))
        self.y = max(0, min(self.y, ALTURA_JOGO - self.tamanho))

        # Atualizar retângulo
        self.rect.x = self.x
        self.rect.y = self.y

        # Rastro de movimento
        self.atualizar_rastro()

        # Sistema de invulnerabilidade
        if self.invulneravel and tempo_atual - self.tempo_invulneravel > self.duracao_invulneravel:
            self.invulneravel = False

        # Efeitos visuais
        self.atualizar_efeitos_visuais(tempo_atual)

        # Sistema de ataques
        self.atualizar_sistema_ataques(tempo_atual, jogador, inimigos)

    def atualizar_movimento(self, jogador):
        """
        Sistema de movimentação independente que EVITA o jogador.
        Boss se move em direções aleatórias, mas desvia quando está próximo do jogador.
        Velocidade idêntica ao inimigo ciano normal.
        """
        tempo_atual = pygame.time.get_ticks()

        # Calcular distância até o jogador
        dx_jogador = jogador.x - self.x
        dy_jogador = jogador.y - self.y
        distancia_jogador = math.sqrt(dx_jogador**2 + dy_jogador**2)

        # Zona de evasão - se jogador está muito perto, boss tenta se afastar
        zona_evasao = 200  # pixels

        if distancia_jogador < zona_evasao and distancia_jogador > 0:
            # Calcular direção OPOSTA ao jogador (fugir)
            direcao_fuga_x = -dx_jogador / distancia_jogador
            direcao_fuga_y = -dy_jogador / distancia_jogador

            # Intensidade da fuga baseada na proximidade (quanto mais perto, mais forte)
            intensidade_fuga = 1.0 - (distancia_jogador / zona_evasao)

            # Misturar direção atual com direção de fuga
            self.direcao_x = self.direcao_x * (1 - intensidade_fuga) + direcao_fuga_x * intensidade_fuga
            self.direcao_y = self.direcao_y * (1 - intensidade_fuga) + direcao_fuga_y * intensidade_fuga

            # Normalizar para manter velocidade consistente
            magnitude = math.sqrt(self.direcao_x**2 + self.direcao_y**2)
            if magnitude > 0:
                self.direcao_x /= magnitude
                self.direcao_y /= magnitude

            # Resetar timer de mudança de direção quando está evitando
            self.tempo_ultima_mudanca_direcao = tempo_atual
        else:
            # Mudar direção periodicamente quando longe do jogador
            if tempo_atual - self.tempo_ultima_mudanca_direcao > self.intervalo_mudanca_direcao:
                self.direcao_x = random.choice([-1, -0.7, 0.7, 1])
                self.direcao_y = random.choice([-1, -0.7, 0.7, 1])
                self.tempo_ultima_mudanca_direcao = tempo_atual
                self.intervalo_mudanca_direcao = random.randint(1000, 2500)

        # Mover na direção atual
        self.x += self.direcao_x * self.velocidade
        self.y += self.direcao_y * self.velocidade

        # Rebater nas bordas (inverte direção ao colidir com paredes)
        if self.x <= 0 or self.x >= LARGURA - self.tamanho:
            self.direcao_x *= -1
            self.x = max(0, min(self.x, LARGURA - self.tamanho))

        if self.y <= 0 or self.y >= ALTURA_JOGO - self.tamanho:
            self.direcao_y *= -1
            self.y = max(0, min(self.y, ALTURA_JOGO - self.tamanho))

        # Atualizar retângulo de colisão
        self.rect.x = self.x
        self.rect.y = self.y

    def atualizar_rastro(self):
        """Atualiza rastro de movimento (maior e mais detalhado)."""
        self.rastro_movimento.append({
            'x': self.x + self.tamanho // 2,
            'y': self.y + self.tamanho // 2,
            'vida': 20  # Aumentado para durar mais
        })

        for rastro in self.rastro_movimento[:]:
            rastro['vida'] -= 1
            if rastro['vida'] <= 0:
                self.rastro_movimento.remove(rastro)

        # Aumentado para ter mais pontos
        if len(self.rastro_movimento) > 40:
            self.rastro_movimento.pop(0)

    def criar_particula_dash(self):
        """Cria partícula de efeito dash."""
        particula = {
            'x': self.x + self.tamanho // 2,
            'y': self.y + self.tamanho // 2,
            'dx': random.uniform(-4, 4),
            'dy': random.uniform(-4, 4),
            'vida': 30,
            'cor': self.cor_secundaria,
            'tamanho': random.uniform(4, 8)
        }
        self.particulas_aura.append(particula)

    def atualizar_sistema_ataques(self, tempo_atual, jogador, inimigos):
        """Sistema de ataques rápidos."""
        if self.congelado_por_morte_jogador:
            return

        if self.carregando_ataque:
            tempo_carregando = tempo_atual - self.tempo_carregamento
            if tempo_carregando >= self.tempo_carregamento_necessario:
                self.ataque_pronto_para_executar = True
        else:
            tempo_desde_ultimo = tempo_atual - self.tempo_ultimo_ataque
            if tempo_desde_ultimo > self.cooldown_ataque:
                self.iniciar_ataque(tempo_atual)

    def iniciar_ataque(self, tempo_atual):
        """Inicia ataque rápido."""
        if self.carregando_ataque:
            return

        padroes_disponiveis = self.padroes_ataque.copy()

        # Fase 3 tem ataques mais intensos
        if self.fase_boss == 3:
            ataques_avancados = ["dash_ataque", "tiros_rastreadores"]
            padroes_disponiveis.extend(ataques_avancados)

        self.ataque_atual = random.choice(padroes_disponiveis)

        self.carregando_ataque = True
        self.tempo_carregamento = tempo_atual
        self.energia_acumulada = 0

        print(f"⚡ VelocityCyan carregando: {self.ataque_atual}")

    def executar_ataque(self, tiros_inimigo, jogador, particulas, flashes):
        """Executa ataques velozes."""
        if not self.ataque_pronto_para_executar or not self.ataque_atual:
            return

        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        print(f"⚡ VelocityCyan executando ataque: {self.ataque_atual}")

        if self.ataque_atual == "rajada_veloz":
            self.ataque_rajada_veloz(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "chuva_rapida":
            self.ataque_chuva_rapida(tiros_inimigo, particulas, flashes)
        elif self.ataque_atual == "dash_ataque":
            self.ataque_dash_ataque(centro_x, centro_y, tiros_inimigo, jogador)
        elif self.ataque_atual == "ondas_velocidade":
            self.ataque_ondas_velocidade(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "explosao_circular":
            self.ataque_explosao_circular(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "tiros_rastreadores":
            self.ataque_tiros_rastreadores(centro_x, centro_y, tiros_inimigo, jogador)

        self.carregando_ataque = False
        self.ataque_pronto_para_executar = False
        self.ataque_atual = None

        pygame.mixer.Channel(3).play(pygame.mixer.Sound(gerar_som_explosao()))

        tempo_atual = pygame.time.get_ticks()
        self.tempo_ultimo_ataque = tempo_atual
        print(f"✅ Ataque concluído! Aguardando {self.cooldown_ataque}ms")

    # ATAQUES VELOZES

    def ataque_rajada_veloz(self, centro_x, centro_y, tiros_inimigo):
        """Rajada circular muito rápida."""
        num_tiros = 8 if self.fase_boss < 3 else 12

        for i in range(num_tiros):
            angulo = (2 * math.pi * i) / num_tiros

            dx = math.cos(angulo)
            dy = math.sin(angulo)

            velocidade = random.randint(6, 9)  # Tiros rápidos

            tiro = Tiro(centro_x, centro_y, dx, dy, self.cor_secundaria, velocidade)
            tiros_inimigo.append(tiro)

    def ataque_chuva_rapida(self, tiros_inimigo, particulas, flashes):
        """Chuva de tiros rápidos."""
        for _ in range(20):
            x = random.randint(0, LARGURA)
            y = -50

            dx = random.uniform(-0.3, 0.3)
            dy = random.uniform(4, 7)  # Muito rápido

            tiro = Tiro(x, y, dx, dy, self.cor_secundaria, random.randint(5, 8))
            tiro.raio = random.randint(5, 10)
            tiros_inimigo.append(tiro)

    def ataque_dash_ataque(self, centro_x, centro_y, tiros_inimigo, jogador):
        """Dash em direção ao jogador disparando tiros."""
        dx = jogador.x - centro_x
        dy = jogador.y - centro_y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > 0:
            dx /= dist
            dy /= dist

        # Tiros ao longo do dash
        for i in range(8):
            offset_x = dx * i * 30
            offset_y = dy * i * 30

            tiro = Tiro(centro_x + offset_x, centro_y + offset_y, dx, dy,
                       self.cor_secundaria, 8)
            tiros_inimigo.append(tiro)

    def ataque_ondas_velocidade(self, centro_x, centro_y, tiros_inimigo):
        """Ondas de tiros velozes."""
        num_ondas = 3 if self.fase_boss < 3 else 4

        for onda in range(num_ondas):
            tiros_por_onda = 10

            for i in range(tiros_por_onda):
                angulo = (2 * math.pi * i) / tiros_por_onda
                dx = math.cos(angulo)
                dy = math.sin(angulo)

                velocidade = 4.0 + onda * 1.5
                cor_onda = (int(self.cor_secundaria[0] * (1 - onda * 0.15)),
                          int(self.cor_secundaria[1] * (1 - onda * 0.15)),
                          int(self.cor_secundaria[2]))

                start_x = centro_x + dx * (onda + 1) * 40
                start_y = centro_y + dy * (onda + 1) * 40

                tiro = Tiro(start_x, start_y, dx, dy, cor_onda, velocidade)
                tiros_inimigo.append(tiro)

    def ataque_explosao_circular(self, centro_x, centro_y, tiros_inimigo):
        """Explosão circular de tiros."""
        num_tiros = 16 if self.fase_boss < 3 else 24

        for i in range(num_tiros):
            angulo = (2 * math.pi * i) / num_tiros
            dx = math.cos(angulo)
            dy = math.sin(angulo)

            velocidade = random.randint(4, 7)

            tiro = Tiro(centro_x, centro_y, dx, dy, self.cor_brilho, velocidade)
            tiros_inimigo.append(tiro)

    def ataque_tiros_rastreadores(self, centro_x, centro_y, tiros_inimigo, jogador):
        """Tiros que seguem o jogador."""
        num_tiros = 5 if self.fase_boss < 3 else 8

        for i in range(num_tiros):
            # Predição da posição do jogador
            predicao_x = jogador.x + random.randint(-80, 80)
            predicao_y = jogador.y + random.randint(-80, 80)

            dx = predicao_x - centro_x
            dy = predicao_y - centro_y
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 0:
                dx /= dist
                dy /= dist

            tiro = Tiro(centro_x, centro_y, dx, dy, (255, 255, 100), 6)
            tiro.rastreador = True  # Flag para indicar que é rastreador
            tiros_inimigo.append(tiro)

    def atualizar_efeitos_visuais(self, tempo_atual):
        """Efeitos visuais velozes."""
        if tempo_atual - self.tempo_pulsacao > 50:  # Pulsa mais rápido
            self.tempo_pulsacao = tempo_atual
            self.pulsacao = (self.pulsacao + 1) % 30

        # Reduzido de 0.6 para 0.15 e de 4 partículas para 1
        if random.random() < 0.15:
            particula = {
                'x': self.x + random.randint(0, self.tamanho),
                'y': self.y + random.randint(0, self.tamanho),
                'dx': random.uniform(-2, 2),
                'dy': random.uniform(-2, 2),
                'vida': random.randint(15, 30),  # Vida reduzida
                'cor': random.choice([self.cor_principal, self.cor_secundaria, self.cor_brilho]),
                'tamanho': random.uniform(2, 5)  # Tamanho reduzido
            }
            self.particulas_aura.append(particula)

        for particula in self.particulas_aura[:]:
            particula['x'] += particula['dx']
            particula['y'] += particula['dy']
            particula['vida'] -= 1
            particula['tamanho'] -= 0.1

            if particula['vida'] <= 0 or particula['tamanho'] <= 0:
                self.particulas_aura.remove(particula)

    def tomar_dano(self, dano=1):
        """Sistema de dano."""
        if self.congelado_por_morte_jogador:
            return False

        if not self.invulneravel:
            self.vidas -= dano

            duracao_base = 80
            if self.fase_boss == 2:
                duracao_base = 60
            elif self.fase_boss == 3:
                duracao_base = 40

            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks()
            self.duracao_invulneravel = duracao_base

            # Reduzido de 8 para 3 partículas
            for _ in range(3):
                particula = {
                    'x': self.x + self.tamanho // 2,
                    'y': self.y + self.tamanho // 2,
                    'dx': random.uniform(-3, 3),
                    'dy': random.uniform(-3, 3),
                    'vida': 12,  # Vida reduzida
                    'cor': (255, 255, 255),
                    'tamanho': 5  # Tamanho reduzido
                }
                self.particulas_aura.append(particula)

            print(f"⚡ VelocityCyan tomou dano! Vida: {self.vidas}/{self.vidas_max}")
            return True
        return False

    def desenhar(self, tela, tempo_atual):
        """Sistema de desenho com tema de velocidade."""
        # Desenhar rastro (maior e mais detalhado)
        for i, rastro in enumerate(self.rastro_movimento):
            if rastro['vida'] > 0:
                alpha = int(255 * (rastro['vida'] / 20))  # Ajustado para vida máxima de 20
                tamanho_rastro = max(2, int(self.tamanho * (rastro['vida'] / 20) * 0.7))  # Maior e mais visível

                rastro_surface = pygame.Surface((tamanho_rastro * 2, tamanho_rastro * 2), pygame.SRCALPHA)

                # Gradiente no rastro para dar mais profundidade
                for j in range(3):
                    alpha_layer = alpha // (j + 1)
                    rastro_surface.set_alpha(alpha_layer)
                    cor_rastro = self.cor_secundaria if i % 2 == 0 else self.cor_brilho
                    pygame.draw.rect(rastro_surface, cor_rastro,
                                   (j, j, tamanho_rastro * 2 - j * 2, tamanho_rastro * 2 - j * 2), 0, 5)

                tela.blit(rastro_surface, (rastro['x'] - tamanho_rastro, rastro['y'] - tamanho_rastro))

        # Desenhar partículas
        for particula in self.particulas_aura:
            if particula['tamanho'] > 0:
                pygame.draw.circle(tela, particula['cor'],
                                 (int(particula['x']), int(particula['y'])),
                                 max(1, int(particula['tamanho'])))

        # Pulsação
        pulso = int(self.pulsacao / 2)
        tamanho_atual = self.tamanho + pulso

        # Sombra
        shadow_surface = pygame.Surface((tamanho_atual + 8, tamanho_atual + 8))
        shadow_surface.set_alpha(120)
        shadow_surface.fill((0, 0, 0))
        tela.blit(shadow_surface, (self.x + 4, self.y + 4))

        # Cor baseada no estado
        cor_uso = self.cor_principal
        if self.invulneravel and tempo_atual % 100 < 50:
            cor_uso = (255, 255, 255)

        # Borda externa
        pygame.draw.rect(tela, (20, 40, 60),
                        (self.x - 3, self.y - 3, tamanho_atual + 6, tamanho_atual + 6), 0, 10)

        # Corpo principal com gradiente (sem núcleo central)
        for i in range(5):
            cor_gradiente = tuple(max(0, min(255, c + i * 10)) for c in cor_uso)
            pygame.draw.rect(tela, cor_gradiente,
                            (self.x + i, self.y + i,
                             tamanho_atual - i * 2, tamanho_atual - i * 2), 0, 8)

        # Detalhes de velocidade (linhas de movimento)
        if self.fase_boss >= 2:
            for i in range(3):
                linha_x = self.x - 10 - i * 8
                linha_y = self.y + tamanho_atual // 2
                pygame.draw.line(tela, self.cor_secundaria,
                               (linha_x, linha_y - 5), (linha_x + 15, linha_y), 2)
                pygame.draw.line(tela, self.cor_secundaria,
                               (linha_x, linha_y + 5), (linha_x + 15, linha_y), 2)

        if self.fase_boss == 3:
            # Aura de velocidade
            for i in range(4):
                raio_aura = tamanho_atual // 2 + 15 + i * 10
                alpha = 60 - i * 12
                if alpha > 0:
                    aura_surface = pygame.Surface((raio_aura * 2, raio_aura * 2))
                    aura_surface.set_alpha(alpha)
                    pygame.draw.circle(aura_surface, self.cor_secundaria,
                                     (raio_aura, raio_aura), raio_aura, 2)
                    tela.blit(aura_surface, (self.x + tamanho_atual // 2 - raio_aura,
                                           self.y + tamanho_atual // 2 - raio_aura))

        # Barra de vida
        self.desenhar_barra_vida(tela)

        # Indicador de carregamento
        if self.carregando_ataque:
            self.desenhar_carregamento_ataque(tela, tempo_atual)

    def desenhar_barra_vida(self, tela):
        """Barra de vida do VelocityCyan."""
        barra_largura = LARGURA - 100
        barra_altura = 25
        barra_x = 50
        barra_y = 25

        # Fundo
        pygame.draw.rect(tela, (10, 20, 30),
                        (barra_x - 3, barra_y - 3, barra_largura + 6, barra_altura + 6), 0, 8)
        pygame.draw.rect(tela, (50, 80, 100),
                        (barra_x, barra_y, barra_largura, barra_altura), 0, 5)

        # Vida restante
        vida_porcentagem = self.vidas / self.vidas_max
        vida_largura = int(barra_largura * vida_porcentagem)

        if vida_porcentagem > 0.66:
            cor_vida = (100, 200, 255)
        elif vida_porcentagem > 0.33:
            cor_vida = (50, 150, 255)
        else:
            cor_vida = (0, 100, 255)

        if vida_largura > 0:
            for i in range(vida_largura):
                alpha = 1.0 - (i / vida_largura) * 0.3
                cor_gradiente = tuple(int(c * alpha) for c in cor_vida)
                pygame.draw.line(tela, cor_gradiente,
                               (barra_x + i, barra_y),
                               (barra_x + i, barra_y + barra_altura))

        # Texto
        from src.utils.visual import desenhar_texto

        nome_texto = f"VELOCITY CYAN - FASE {self.fase_boss}"

        # Sombra
        desenhar_texto(tela, nome_texto, 26, (30, 30, 30), LARGURA // 2 + 2, barra_y - 17)
        # Texto principal
        cor_texto = (150, 255, 255) if self.fase_boss < 3 else (100, 255, 255)
        desenhar_texto(tela, nome_texto, 26, cor_texto, LARGURA // 2, barra_y - 15)

        # Vida numérica
        vida_texto = f"{self.vidas}/{self.vidas_max}"
        desenhar_texto(tela, vida_texto, 20, (255, 255, 255), LARGURA // 2, barra_y + 40)

        # Indicador de velocidade (ao invés de padrão de movimento)
        velocidade_texto = f"Velocidade: {self.velocidade:.1f}"
        desenhar_texto(tela, velocidade_texto, 16, (150, 200, 255), LARGURA // 2, barra_y + 60)

    def desenhar_carregamento_ataque(self, tela, tempo_atual):
        """Indicador de carregamento rápido."""
        tempo_carregando = tempo_atual - self.tempo_carregamento
        progresso = min(1.0, tempo_carregando / self.tempo_carregamento_necessario)

        if tela is not None:
            centro_x = self.x + self.tamanho // 2
            centro_y = self.y + self.tamanho // 2
            raio = self.tamanho // 2 + 25

            # Círculo de fundo
            pygame.draw.circle(tela, (30, 50, 70), (centro_x, centro_y), raio + 3, 3)

            # Arco de progresso
            if progresso > 0:
                num_pontos = int(64 * progresso)
                for i in range(num_pontos):
                    angulo = (2 * math.pi * i) / 64
                    x = centro_x + raio * math.cos(angulo - math.pi/2)
                    y = centro_y + raio * math.sin(angulo - math.pi/2)

                    cor = self.cor_secundaria

                    pygame.draw.circle(tela, cor, (int(x), int(y)), 4)

            # Texto do ataque
            if self.ataque_atual:
                from src.utils.visual import desenhar_texto
                nome_ataque = self.ataque_atual.replace("_", " ").title()
                desenhar_texto(tela, nome_ataque, 18, (150, 255, 255), centro_x, centro_y - 10)

                # Barra de progresso
                barra_w = 80
                barra_h = 6
                barra_x = centro_x - barra_w // 2
                barra_y = centro_y + 15

                pygame.draw.rect(tela, (30, 50, 70), (barra_x, barra_y, barra_w, barra_h), 0, 3)
                prog_w = int(barra_w * progresso)
                if prog_w > 0:
                    pygame.draw.rect(tela, self.cor_secundaria, (barra_x, barra_y, prog_w, barra_h), 0, 3)

        return progresso >= 1.0
