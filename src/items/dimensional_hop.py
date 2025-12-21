#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para o item Dimensional Hop - teletransporte instantâneo.
"""

import pygame
import math
import random
import os
import json
from src.config import *
from src.entities.particula import Particula
from src.utils.display_manager import convert_mouse_position


class DimensionalHop:
    """
    Item de teletransporte que permite ao jogador se teletransportar
    para a posição do cursor.
    """

    def __init__(self):
        """Inicializa o Dimensional Hop."""
        self.ativo = False  # Se está sendo segurado
        self.pode_usar = True  # Cooldown
        self.cooldown_tempo = 500  # 0.5 segundo de cooldown
        self.ultimo_uso = 0

        # Cores retrofuturísticas
        self.cor_portal = (200, 50, 255)  # Magenta
        self.cor_particula = (255, 150, 255)  # Rosa neon
        self.cor_grid = (150, 80, 200)  # Roxo

    def ativar(self):
        """Ativa o item (jogador segurando)."""
        self.ativo = True

    def desativar(self):
        """Desativa o item."""
        self.ativo = False

    def usar(self, jogador, pos_destino, particulas=None, flashes=None):
        """
        Teletransporta o jogador para a posição de destino.

        Args:
            jogador: Objeto do jogador
            pos_destino: Tupla (x, y) da posição de destino
            particulas: Lista de partículas para efeitos visuais
            flashes: Lista de flashes para efeitos visuais

        Returns:
            True se o teletransporte foi bem-sucedido, False caso contrário
        """
        tempo_atual = pygame.time.get_ticks()

        # Verificar cooldown
        if tempo_atual - self.ultimo_uso < self.cooldown_tempo:
            return False

        # Posição de origem
        origem_x = jogador.x + jogador.tamanho // 2
        origem_y = jogador.y + jogador.tamanho // 2

        # Garantir que o destino está dentro da tela
        destino_x = max(jogador.tamanho, min(pos_destino[0], LARGURA - jogador.tamanho))
        destino_y = max(jogador.tamanho, min(pos_destino[1], ALTURA_JOGO - jogador.tamanho))

        # Efeitos visuais na origem
        if particulas is not None:
            self._criar_efeito_portal(origem_x, origem_y, particulas, True)

        if flashes is not None:
            # Flash de saída
            flash_saida = {
                'x': origem_x,
                'y': origem_y,
                'raio': 40,
                'vida': 15,
                'cor': self.cor_portal
            }
            flashes.append(flash_saida)

        # Teletransportar jogador
        jogador.x = destino_x - jogador.tamanho // 2
        jogador.y = destino_y - jogador.tamanho // 2
        jogador.rect.x = jogador.x
        jogador.rect.y = jogador.y

        # Ativar invulnerabilidade por 1.5 segundos
        jogador.invulneravel = True
        jogador.tempo_invulneravel = tempo_atual
        # Salvar duração original e aplicar nova duração temporária
        jogador.duracao_invulneravel_original = getattr(jogador, 'duracao_invulneravel', DURACAO_INVULNERAVEL)
        jogador.duracao_invulneravel = 1500  # 1.5 segundos

        # Efeitos visuais no destino
        if particulas is not None:
            self._criar_efeito_portal(destino_x, destino_y, particulas, False)

        if flashes is not None:
            # Flash de chegada
            flash_chegada = {
                'x': destino_x,
                'y': destino_y,
                'raio': 50,
                'vida': 20,
                'cor': (100, 200, 255)  # Ciano
            }
            flashes.append(flash_chegada)

        # Som de teletransporte
        try:
            som_teleporte = pygame.mixer.Sound(bytes(bytearray(
                int(127 + 127 * math.sin(i / (20 - i/400)) * (1.0 - i/8000))
                for i in range(8000)
            )))
            som_teleporte.set_volume(0.3)
            pygame.mixer.Channel(6).play(som_teleporte)
        except:
            pass

        # Atualizar cooldown
        self.ultimo_uso = tempo_atual

        return True

    def _criar_efeito_portal(self, x, y, particulas, is_saida):
        """
        Cria efeito de partículas do portal.

        Args:
            x, y: Posição do portal
            particulas: Lista de partículas
            is_saida: True se é portal de saída, False se é de chegada
        """
        num_particulas = 30

        for _ in range(num_particulas):
            # Ângulo aleatório
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(2, 6)

            # Direção baseada se é saída ou chegada
            if is_saida:
                # Partículas se afastando (implosão)
                vx = -math.cos(angulo) * velocidade
                vy = -math.sin(angulo) * velocidade
            else:
                # Partículas se aproximando (explosão)
                vx = math.cos(angulo) * velocidade
                vy = math.sin(angulo) * velocidade

            # Criar partícula
            cor = random.choice([self.cor_portal, self.cor_particula, (100, 200, 255)])
            particula = Particula(x, y, cor)
            particula.velocidade_x = vx
            particula.velocidade_y = vy
            particula.vida = random.randint(15, 30)
            particula.tamanho = random.uniform(2, 5)
            particula.gravidade = 0  # Sem gravidade

            particulas.append(particula)

    def desenhar_segurado(self, tela, jogador, pos_mouse, tempo_atual):
        """
        Desenha o item quando está sendo segurado pelo jogador.

        Args:
            tela: Superfície onde desenhar
            jogador: Objeto do jogador
            pos_mouse: Posição do mouse
            tempo_atual: Tempo atual para animações
        """
        if not self.ativo:
            return

        centro_jogador_x = jogador.x + jogador.tamanho // 2
        centro_jogador_y = jogador.y + jogador.tamanho // 2

        # Calcular direção para o mouse
        dx = pos_mouse[0] - centro_jogador_x
        dy = pos_mouse[1] - centro_jogador_y
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Posição do portal segurado (perto do jogador)
        distancia_portal = 30
        portal_x = centro_jogador_x + dx * distancia_portal
        portal_y = centro_jogador_y + dy * distancia_portal

        # Desenhar portal segurado (menor que o normal)
        pulso = (math.sin(tempo_atual / 100) + 1) / 2
        raio_portal = 12

        # Anéis do portal
        for i in range(3):
            raio_anel = raio_portal - i * 3
            # Calcular cor com valores seguros (0-255)
            r = max(0, min(255, int(self.cor_portal[0] * (1 - i/3) + 100)))
            g = max(0, min(255, int(self.cor_portal[1] * (1 - i/3) + 200)))
            b = max(0, min(255, int(self.cor_portal[2])))
            cor_anel = (r, g, b)
            pygame.draw.circle(tela, cor_anel, (int(portal_x), int(portal_y)), int(raio_anel + pulso * 2), 2)

        # Núcleo
        pygame.draw.circle(tela, (255, 255, 255), (int(portal_x), int(portal_y)), int(4 + pulso * 2))

        # Partículas orbitando
        for i in range(6):
            angulo = (2 * math.pi * i / 6) + (tempo_atual / 150)
            raio_orbita = 16

            part_x = portal_x + math.cos(angulo) * raio_orbita
            part_y = portal_y + math.sin(angulo) * raio_orbita

            pygame.draw.rect(tela, self.cor_particula,
                           (int(part_x - 2), int(part_y - 2), 4, 4))

        # Desenhar preview do destino (indicador onde vai aparecer)
        self._desenhar_preview_destino(tela, pos_mouse, tempo_atual)

        # Linha conectando portal ao destino
        pygame.draw.line(tela, (150, 80, 200, 100),
                        (int(portal_x), int(portal_y)),
                        (int(pos_mouse[0]), int(pos_mouse[1])), 2)

    def _desenhar_preview_destino(self, tela, pos_destino, tempo_atual):
        """
        Desenha um preview no local onde o jogador vai aparecer.

        Args:
            tela: Superfície onde desenhar
            pos_destino: Posição de destino
            tempo_atual: Tempo atual
        """
        pulso = (math.sin(tempo_atual / 150) + 1) / 2

        # Círculo pulsante no destino
        raio_destino = int(20 + pulso * 8)
        cor_destino = (100, 200, 255)  # Ciano

        pygame.draw.circle(tela, cor_destino, (int(pos_destino[0]), int(pos_destino[1])), raio_destino, 3)
        pygame.draw.circle(tela, cor_destino, (int(pos_destino[0]), int(pos_destino[1])), raio_destino - 8, 2)

        # X marcando o ponto
        tamanho_x = 10
        pygame.draw.line(tela, (255, 255, 255),
                        (pos_destino[0] - tamanho_x, pos_destino[1] - tamanho_x),
                        (pos_destino[0] + tamanho_x, pos_destino[1] + tamanho_x), 3)
        pygame.draw.line(tela, (255, 255, 255),
                        (pos_destino[0] + tamanho_x, pos_destino[1] - tamanho_x),
                        (pos_destino[0] - tamanho_x, pos_destino[1] + tamanho_x), 3)

        # Grid retrofuturístico ao redor
        for i in range(4):
            angulo = (2 * math.pi * i / 4) + (tempo_atual / 200)
            grid_raio = raio_destino + 10

            grid_x = pos_destino[0] + math.cos(angulo) * grid_raio
            grid_y = pos_destino[1] + math.sin(angulo) * grid_raio

            pygame.draw.rect(tela, self.cor_grid,
                           (int(grid_x - 3), int(grid_y - 3), 6, 6))


# Funções auxiliares para integração com o sistema do jogo

def carregar_upgrade_dimensional_hop():
    """
    Carrega o upgrade de dimensional hop do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("dimensional_hop", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de dimensional hop: {e}")
        return 0


def desenhar_dimensional_hop_selecionado(tela, jogador, tempo_atual):
    """
    Desenha o dimensional hop quando selecionado pelo jogador.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
    """
    # Obter posição do mouse
    pos_mouse = convert_mouse_position(pygame.mouse.get_pos())

    # Desenhar usando o método da classe
    if hasattr(jogador, 'dimensional_hop_obj') and jogador.dimensional_hop_obj:
        jogador.dimensional_hop_obj.desenhar_segurado(tela, jogador, pos_mouse, tempo_atual)

    # Desenhar contador de usos perto do jogador
    if hasattr(jogador, 'dimensional_hop_uses'):
        fonte = pygame.font.SysFont("Arial", 20, True)
        texto_hop = fonte.render(f"{jogador.dimensional_hop_uses}", True, (200, 150, 255))
        texto_rect = texto_hop.get_rect(center=(jogador.x + jogador.tamanho + 15, jogador.y - 10))
        tela.blit(texto_hop, texto_rect)
