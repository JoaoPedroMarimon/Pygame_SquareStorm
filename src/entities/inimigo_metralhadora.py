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
        """Sobrescreve o método desenhar para incluir visual militar completo."""
        # Não desenhar o quadrado base padrão - vamos fazer um visual totalmente customizado

        # Cores militares modernas
        cor_uniforme_base = (60, 70, 50)          # Verde-oliva escuro
        cor_uniforme_sombra = (40, 50, 30)        # Sombra do uniforme
        cor_colete = (30, 35, 25)                 # Colete balístico preto-esverdeado
        cor_capacete = (45, 55, 40)               # Capacete tático
        cor_metal = (100, 100, 110)               # Metal dos equipamentos
        cor_camuflagem_1 = (70, 80, 55)           # Tom claro camuflagem
        cor_camuflagem_2 = (50, 60, 40)           # Tom escuro camuflagem
        cor_patch = (180, 0, 0)                   # Patch vermelho
        cor_visor = (20, 20, 40)                  # Visor escuro
        cor_led_verde = (0, 255, 100)             # LED verde NVG

        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # ===== SOMBRA NO CHÃO =====
        shadow_surface = pygame.Surface((self.tamanho + 8, self.tamanho + 8))
        shadow_surface.set_alpha(80)
        shadow_surface.fill((0, 0, 0))
        tela.blit(shadow_surface, (self.x + 2, self.y + 2))

        # ===== CORPO DO SOLDADO (retângulo como base) =====
        corpo_rect = pygame.Rect(self.x, self.y, self.tamanho, self.tamanho)

        # Uniforme base com gradiente
        pygame.draw.rect(tela, cor_uniforme_sombra, corpo_rect, 0, 5)
        pygame.draw.rect(tela, cor_uniforme_base,
                        (self.x + 2, self.y + 2, self.tamanho - 4, self.tamanho - 4), 0, 4)

        # ===== PADRÃO DE CAMUFLAGEM (manchas) =====
        for _ in range(6):
            mancha_x = self.x + random.randint(3, self.tamanho - 3)
            mancha_y = self.y + random.randint(3, self.tamanho - 3)
            mancha_tamanho = random.randint(3, 6)
            cor_mancha = random.choice([cor_camuflagem_1, cor_camuflagem_2])
            pygame.draw.circle(tela, cor_mancha, (mancha_x, mancha_y), mancha_tamanho)

        # ===== COLETE BALÍSTICO (no centro do corpo) =====
        colete_largura = int(self.tamanho * 0.7)
        colete_altura = int(self.tamanho * 0.8)
        colete_x = centro_x - colete_largura // 2
        colete_y = centro_y - colete_altura // 2

        # Colete principal
        colete_rect = pygame.Rect(colete_x, colete_y, colete_largura, colete_altura)
        pygame.draw.rect(tela, cor_colete, colete_rect, 0, 3)
        pygame.draw.rect(tela, cor_metal, colete_rect, 1)

        # Placas balísticas (linhas horizontais)
        for i in range(3):
            placa_y = colete_y + 5 + i * 8
            pygame.draw.line(tela, cor_metal,
                           (colete_x + 3, placa_y),
                           (colete_x + colete_largura - 3, placa_y), 1)

        # Fivelas MOLLE (pequenos quadrados nas laterais)
        for i in range(4):
            fivela_y = colete_y + 5 + i * 7
            pygame.draw.rect(tela, cor_metal, (colete_x + 2, fivela_y, 2, 3))
            pygame.draw.rect(tela, cor_metal, (colete_x + colete_largura - 4, fivela_y, 2, 3))

        # ===== PATCH/INSÍGNIA (no colete) =====
        patch_size = 6
        patch_x = centro_x - patch_size // 2
        patch_y = colete_y + 5
        pygame.draw.rect(tela, cor_patch, (patch_x, patch_y, patch_size, patch_size))
        pygame.draw.rect(tela, (255, 200, 0), (patch_x, patch_y, patch_size, patch_size), 1)
        # Estrela no patch
        pygame.draw.line(tela, (255, 200, 0), (patch_x + 3, patch_y + 1), (patch_x + 3, patch_y + 5), 1)
        pygame.draw.line(tela, (255, 200, 0), (patch_x + 1, patch_y + 3), (patch_x + 5, patch_y + 3), 1)

        # ===== CAPACETE TÁTICO (parte superior) =====
        capacete_y = self.y + 3
        capacete_altura = int(self.tamanho * 0.35)

        # Capacete principal (formato arredondado)
        capacete_rect = pygame.Rect(self.x + 5, capacete_y, self.tamanho - 10, capacete_altura)
        pygame.draw.rect(tela, cor_capacete, capacete_rect, 0, 8)
        pygame.draw.rect(tela, cor_metal, capacete_rect, 1)

        # Faixa tática no capacete
        pygame.draw.line(tela, cor_metal,
                        (self.x + 8, capacete_y + capacete_altura // 2),
                        (self.x + self.tamanho - 8, capacete_y + capacete_altura // 2), 2)

        # ===== ÓCULOS DE VISÃO NOTURNA (NVG) =====
        nvg_y = capacete_y + capacete_altura - 5
        nvg_esquerda_x = centro_x - 8
        nvg_direita_x = centro_x + 3

        # Suporte dos NVG (barra horizontal)
        pygame.draw.line(tela, cor_metal,
                        (centro_x - 10, nvg_y - 2),
                        (centro_x + 10, nvg_y - 2), 2)

        # Lentes dos NVG (dois círculos)
        pygame.draw.circle(tela, (30, 30, 30), (nvg_esquerda_x, nvg_y), 5)
        pygame.draw.circle(tela, cor_visor, (nvg_esquerda_x, nvg_y), 4)
        pygame.draw.circle(tela, cor_led_verde, (nvg_esquerda_x, nvg_y), 2)

        pygame.draw.circle(tela, (30, 30, 30), (nvg_direita_x, nvg_y), 5)
        pygame.draw.circle(tela, cor_visor, (nvg_direita_x, nvg_y), 4)
        pygame.draw.circle(tela, cor_led_verde, (nvg_direita_x, nvg_y), 2)

        # Bateria dos NVG (atrás do capacete)
        bateria_x = centro_x - 3
        bateria_y = capacete_y + 2
        pygame.draw.rect(tela, cor_metal, (bateria_x, bateria_y, 6, 8))
        # LED de status piscando
        if tempo_atual % 1000 < 500:
            pygame.draw.circle(tela, (0, 255, 0), (bateria_x + 3, bateria_y + 2), 1)

        # ===== RÁDIO TÁTICO (ombro esquerdo) =====
        radio_x = self.x + 3
        radio_y = centro_y - 8
        pygame.draw.rect(tela, (20, 20, 20), (radio_x, radio_y, 5, 10))
        pygame.draw.rect(tela, cor_metal, (radio_x, radio_y, 5, 10), 1)
        # Antena
        pygame.draw.line(tela, cor_metal, (radio_x + 2, radio_y), (radio_x + 2, radio_y - 8), 1)

        # ===== POUCHES/BOLSOS (lateral do colete) =====
        pouch_x = self.x + self.tamanho - 8
        for i in range(2):
            pouch_y = centro_y - 5 + i * 10
            pygame.draw.rect(tela, cor_colete, (pouch_x, pouch_y, 5, 8))
            pygame.draw.rect(tela, cor_metal, (pouch_x, pouch_y, 5, 8), 1)
            # Fechos
            pygame.draw.line(tela, (200, 150, 50), (pouch_x + 1, pouch_y + 1), (pouch_x + 4, pouch_y + 1), 1)

        # ===== RANK/PATENTE (ombro direito) =====
        rank_x = self.x + self.tamanho - 10
        rank_y = self.y + 10
        # Três listras de sargento
        for i in range(3):
            pygame.draw.line(tela, (200, 150, 50),
                           (rank_x, rank_y + i * 2),
                           (rank_x + 6, rank_y + i * 2), 1)

        # ===== INDICADOR DE RECARGA/STATUS =====
        if self.esta_recarregando:
            # Barra de recarga embaixo do soldado
            barra_y = self.y + self.tamanho + 8
            barra_largura = self.tamanho
            tempo_decorrido = tempo_atual - self.tempo_inicio_recarga
            progresso = min(1.0, tempo_decorrido / self.tempo_recarga)

            # Fundo da barra
            pygame.draw.rect(tela, (60, 60, 60), (self.x, barra_y, barra_largura, 4), 0, 2)
            # Progresso
            progresso_largura = int(barra_largura * progresso)
            pygame.draw.rect(tela, (255, 140, 0), (self.x, barra_y, progresso_largura, 4), 0, 2)

            # Texto "RELOADING" embaixo
            from src.utils.visual import desenhar_texto
            desenhar_texto(tela, "RELOADING", 10, (255, 140, 0), centro_x, barra_y + 10)
        else:
            # LED verde quando está atirando
            led_x = self.x + self.tamanho - 5
            led_y = self.y + 5
            pygame.draw.circle(tela, (0, 255, 100), (led_x, led_y), 2)

        # ===== BARRA DE VIDA (estilo padrão) =====
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
