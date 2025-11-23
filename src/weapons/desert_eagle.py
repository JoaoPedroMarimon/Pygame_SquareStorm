#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar todas as funcionalidades relacionadas à Desert Eagle.
Desert Eagle - Pistola de alto calibre com tiros poderosos e rápidos.
Características:
- Dano: 3 (triplo do tiro normal)
- Velocidade do tiro: 15 (bem mais rápido que o normal de 10)
- Cooldown: Normal (mesmo do tiro básico)
- Visual: Ícone da Desert Eagle da loja
"""

import pygame
import math
import random
import os
import json
from src.config import *
from src.entities.tiro import Tiro
from src.utils.sound import gerar_som_tiro
from src.entities.particula import Particula


def carregar_upgrade_desert_eagle():
    """
    Carrega o upgrade de Desert Eagle do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("desert_eagle", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de Desert Eagle: {e}")
        return 0


def atirar_desert_eagle(jogador, tiros, pos_mouse, particulas=None, flashes=None):
    """
    Dispara um tiro poderoso da Desert Eagle com maior velocidade e dano.

    Args:
        jogador: O objeto do jogador
        tiros: Lista onde adicionar o novo tiro
        pos_mouse: Tupla (x, y) com a posição do mouse
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
    """
    # Verificar cooldown (mesmo do tiro normal)
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - jogador.tempo_ultimo_tiro < jogador.tempo_cooldown:
        return

    jogador.tempo_ultimo_tiro = tempo_atual

    # Posição central do quadrado
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Calcular vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y

    # Normalizar o vetor direção
    distancia = math.sqrt(dx * dx + dy * dy)
    if distancia > 0:
        dx /= distancia
        dy /= distancia

    # Som de tiro da Desert Eagle (mais impactante)
    som_deagle = pygame.mixer.Sound(gerar_som_tiro())
    som_deagle.set_volume(0.35)  # Volume um pouco mais alto
    pygame.mixer.Channel(1).play(som_deagle)

    # Calcular posição da ponta do cano
    comprimento_arma = 38  # Desert Eagle é mais longa
    ponta_cano_x = centro_x + dx * comprimento_arma
    ponta_cano_y = centro_y + dy * comprimento_arma

    # Criar tiro poderoso da Desert Eagle
    # Velocidade: 15 (50% mais rápido que o normal de 10)
    # Dano: 3 (definido no atributo do tiro)
    # Usar a cor do jogador
    tiro = Tiro(ponta_cano_x, ponta_cano_y, dx, dy, jogador.cor, velocidade=15)
    tiro.dano = 3  # Dano triplo!
    tiro.raio = 4  # Projétil um pouco maior para destacar
    tiros.append(tiro)

    # Efeitos visuais no cano (chama de disparo)
    if particulas is not None:
        criar_efeito_disparo_desert_eagle(ponta_cano_x, ponta_cano_y, dx, dy, particulas)

    # Flash de luz no disparo
    if flashes is not None:
        flash = {
            'x': ponta_cano_x,
            'y': ponta_cano_y,
            'raio': 20,
            'vida': 8,
            'cor': (255, 200, 0)  # Flash dourado
        }
        flashes.append(flash)

    # Reduzir munição
    if hasattr(jogador, 'tiros_desert_eagle'):
        jogador.tiros_desert_eagle -= 1


def criar_efeito_disparo_desert_eagle(x, y, dx, dy, particulas):
    """
    Cria efeitos de partículas para o disparo da Desert Eagle.

    Args:
        x, y: Posição do disparo
        dx, dy: Direção do disparo (normalizada)
        particulas: Lista onde adicionar as partículas
    """
    # Chama do disparo (mais intensa que tiro normal)
    cores_chama = [
        (255, 220, 0),   # Amarelo ouro
        (255, 180, 0),   # Laranja dourado
        (255, 150, 50),  # Laranja
        (255, 100, 0),   # Laranja escuro
    ]

    # Criar partículas da chama (10-15 partículas)
    num_particulas = random.randint(10, 15)
    for _ in range(num_particulas):
        # Ângulo base do disparo
        angulo_base = math.atan2(dy, dx)

        # Dispersão da chama (cone de 45 graus)
        dispersao = random.uniform(-0.4, 0.4)
        angulo_particula = angulo_base + dispersao

        # Velocidade da partícula
        velocidade = random.uniform(3, 8)
        vel_x = math.cos(angulo_particula) * velocidade
        vel_y = math.sin(angulo_particula) * velocidade

        # Cor aleatória da chama
        cor = random.choice(cores_chama)

        # Criar partícula
        particula = Particula(x, y, cor)
        particula.velocidade_x = vel_x
        particula.velocidade_y = vel_y
        particula.vida = random.randint(8, 15)
        particula.tamanho = random.randint(2, 4)
        particulas.append(particula)

    # Fumaça do disparo (mais sutil)
    cores_fumaca = [
        (150, 150, 150),
        (120, 120, 120),
        (100, 100, 100),
    ]

    num_fumaca = random.randint(3, 5)
    for _ in range(num_fumaca):
        angulo_base = math.atan2(dy, dx)
        dispersao = random.uniform(-0.2, 0.2)
        angulo_fumaca = angulo_base + dispersao

        velocidade = random.uniform(1, 3)
        vel_x = math.cos(angulo_fumaca) * velocidade
        vel_y = math.sin(angulo_fumaca) * velocidade

        cor = random.choice(cores_fumaca)

        particula = Particula(
            x + random.randint(-3, 3),
            y + random.randint(-3, 3),
            cor
        )
        particula.velocidade_x = vel_x
        particula.velocidade_y = vel_y
        particula.vida = random.randint(15, 25)
        particula.tamanho = random.randint(1, 3)
        particulas.append(particula)

    # Casca de bala ejetada (efeito visual extra)
    if random.random() < 0.8:  # 80% de chance
        # Perpendicular à direção do tiro (para o lado)
        perp_x = -dy
        perp_y = dx

        # Casca ejetada para o lado
        vel_casca_x = perp_x * random.uniform(2, 4) + dx * random.uniform(-1, 1)
        vel_casca_y = perp_y * random.uniform(2, 4) + dy * random.uniform(-1, 1) - 2  # Gravidade

        particula_casca = Particula(
            x - dx * 5, y - dy * 5,  # Ligeiramente atrás do cano
            (200, 180, 100)  # Cor de latão
        )
        particula_casca.velocidade_x = vel_casca_x
        particula_casca.velocidade_y = vel_casca_y
        particula_casca.vida = random.randint(20, 30)
        particula_casca.tamanho = 2
        particulas.append(particula_casca)


def desenhar_desert_eagle(tela, jogador, pos_mouse):
    """
    Desenha a Desert Eagle seguindo a posição do mouse.
    Usa o mesmo visual detalhado do ícone original.

    Args:
        tela: Superfície do Pygame onde desenhar
        jogador: Objeto do jogador
        pos_mouse: Tupla (x, y) com a posição do mouse
    """
    # Posição central do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Calcular direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y

    # Normalizar direção
    distancia = math.sqrt(dx * dx + dy * dy)
    if distancia > 0:
        dx /= distancia
        dy /= distancia

    # Calcular ângulo de rotação
    angulo = math.atan2(dy, dx)

    # Simulação de recuo quando atira
    recuo = 0
    tempo_atual = pygame.time.get_ticks()
    if hasattr(jogador, 'desert_eagle_ativa') and jogador.desert_eagle_ativa:
        if tempo_atual - jogador.tempo_ultimo_tiro < 100:  # Recuo nos primeiros 100ms
            recuo = 3

    # Cores realistas da Desert Eagle (aço inoxidável/cromado)
    cor_metal_claro = (180, 180, 190)
    cor_metal_medio = (120, 120, 130)
    cor_metal_escuro = (60, 60, 70)
    cor_punho_preto = (30, 30, 35)
    cor_detalhes_punho = (50, 50, 55)
    cor_cano_interno = (20, 20, 25)

    # Criar superfície temporária para desenhar a arma
    tamanho_surf = 100
    surf = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)

    # Offset para centralizar na superfície
    offset_x = 50
    offset_y = 50

    # === SLIDE (parte superior massiva da Desert Eagle) ===
    slide_x = offset_x - 18 - recuo
    slide_y = offset_y - 5
    slide_largura = 38
    slide_altura = 8

    # Slide principal
    slide_rect = pygame.Rect(slide_x, slide_y, slide_largura, slide_altura)
    pygame.draw.rect(surf, cor_metal_medio, slide_rect, 0, 2)

    # Brilho superior do slide
    pygame.draw.line(surf, cor_metal_claro,
                    (slide_x + 2, slide_y + 1),
                    (slide_x + slide_largura - 4, slide_y + 1), 2)

    # Sombra inferior do slide
    pygame.draw.line(surf, cor_metal_escuro,
                    (slide_x + 2, slide_y + slide_altura - 2),
                    (slide_x + slide_largura - 4, slide_y + slide_altura - 2), 1)

    # Ranhuras de ventilação
    for i in range(5):
        ranhura_x = slide_x + 20 + i * 3
        pygame.draw.line(surf, cor_metal_escuro,
                        (ranhura_x, slide_y + 2),
                        (ranhura_x, slide_y + slide_altura - 2), 2)
        pygame.draw.line(surf, cor_metal_claro,
                        (ranhura_x + 1, slide_y + 2),
                        (ranhura_x + 1, slide_y + slide_altura - 2), 1)

    # === CANO MASSIVO ===
    cano_x = slide_x + slide_largura
    cano_y = offset_y
    cano_raio = 4

    pygame.draw.circle(surf, cor_metal_medio, (cano_x, cano_y), cano_raio)
    pygame.draw.circle(surf, cor_metal_claro, (cano_x, cano_y - 1), cano_raio - 1)
    pygame.draw.circle(surf, cor_cano_interno, (cano_x, cano_y), cano_raio - 2)
    pygame.draw.circle(surf, (10, 10, 15), (cano_x, cano_y), cano_raio - 3)
    pygame.draw.circle(surf, cor_metal_escuro, (cano_x, cano_y), cano_raio, 1)

    # === FRAME ===
    frame_x = slide_x + 3
    frame_y = offset_y
    frame_largura = 26
    frame_altura = 12

    frame_rect = pygame.Rect(frame_x, frame_y - frame_altura//2, frame_largura, frame_altura)
    pygame.draw.rect(surf, cor_metal_escuro, frame_rect, 0, 2)
    pygame.draw.rect(surf, cor_metal_medio,
                    (frame_x + 1, frame_y - frame_altura//2 + 1, frame_largura - 2, 2), 0, 1)

    # === TRILHO PICATINNY ===
    trilho_y = slide_y - 2
    for i in range(3):
        trilho_x = slide_x + 15 + i * 4
        pygame.draw.rect(surf, cor_metal_escuro, (trilho_x, trilho_y, 2, 2))

    # === GUARDA-MATO ===
    guarda_centro_x = frame_x + 10
    guarda_centro_y = offset_y + 6

    pygame.draw.ellipse(surf, cor_metal_medio,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 2)
    pygame.draw.ellipse(surf, cor_metal_claro,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 1)

    # === GATILHO ===
    gatilho_x = guarda_centro_x
    gatilho_y = guarda_centro_y
    pygame.draw.rect(surf, cor_metal_claro, (gatilho_x - 2, gatilho_y - 1, 4, 3), 0, 1)
    pygame.draw.line(surf, cor_metal_escuro, (gatilho_x - 1, gatilho_y + 1), (gatilho_x + 1, gatilho_y + 1), 1)

    # === PUNHO ERGONÔMICO ===
    punho_x = frame_x - 1
    punho_y = offset_y + 3

    punho_pontos = [
        (punho_x, punho_y - 4),
        (punho_x + 12, punho_y - 3),
        (punho_x + 10, punho_y + 12),
        (punho_x - 4, punho_y + 10)
    ]

    pygame.draw.polygon(surf, cor_punho_preto, punho_pontos)
    pygame.draw.polygon(surf, cor_metal_escuro, punho_pontos, 1)

    # Textura do punho
    for i in range(6):
        textura_y = punho_y + i * 2
        pygame.draw.line(surf, cor_detalhes_punho,
                        (punho_x + 2, textura_y),
                        (punho_x + 8, textura_y), 1)

    # === MARTELO ===
    martelo_x = frame_x + 5
    martelo_y = offset_y - 8
    pygame.draw.circle(surf, cor_metal_medio, (martelo_x, martelo_y), 3)
    pygame.draw.rect(surf, cor_metal_escuro, (martelo_x - 1, martelo_y - 5, 2, 5))

    # === MIRA FRONTAL ===
    mira_x = cano_x - 5
    mira_y = offset_y - 6
    pygame.draw.rect(surf, (255, 215, 0), (mira_x - 1, mira_y, 2, 4))

    # === MIRA TRASEIRA ===
    mira_tras_x = frame_x + 20
    mira_tras_y = offset_y - 7
    pygame.draw.rect(surf, cor_metal_escuro, (mira_tras_x - 3, mira_tras_y, 6, 4))
    pygame.draw.rect(surf, (100, 255, 100), (mira_tras_x - 1, mira_tras_y + 1, 2, 2))

    # Rotacionar a superfície
    angulo_graus = math.degrees(angulo)
    surf_rotacionada = pygame.transform.rotate(surf, -angulo_graus)

    # Obter o retângulo e posicionar no centro do jogador
    rect = surf_rotacionada.get_rect()
    rect.center = (centro_x, centro_y)

    # Desenhar na tela
    tela.blit(surf_rotacionada, rect)


def desenhar_icone_desert_eagle(tela, x, y, tempo_atual):
    """
    Desenha o ícone da Desert Eagle (mesmo visual da loja).
    Usado para desenhar a arma quando equipada.
    """
    # Cores realistas da Desert Eagle (aço inoxidável/cromado)
    cor_metal_claro = (180, 180, 190)
    cor_metal_medio = (120, 120, 130)
    cor_metal_escuro = (60, 60, 70)
    cor_punho_preto = (30, 30, 35)
    cor_detalhes_punho = (50, 50, 55)
    cor_cano_interno = (20, 20, 25)

    # Animação sutil de brilho metálico
    pulso = (math.sin(tempo_atual / 400) + 1) / 2

    # === SLIDE (parte superior massiva da Desert Eagle) ===
    slide_x = x - 18
    slide_y = y - 5
    slide_largura = 38
    slide_altura = 8

    # Slide principal
    slide_rect = pygame.Rect(slide_x, slide_y, slide_largura, slide_altura)
    pygame.draw.rect(tela, cor_metal_medio, slide_rect, 0, 2)

    # Brilho superior do slide
    pygame.draw.line(tela, cor_metal_claro,
                    (slide_x + 2, slide_y + 1),
                    (slide_x + slide_largura - 4, slide_y + 1), 2)

    # Sombra inferior do slide
    pygame.draw.line(tela, cor_metal_escuro,
                    (slide_x + 2, slide_y + slide_altura - 2),
                    (slide_x + slide_largura - 4, slide_y + slide_altura - 2), 1)

    # Ranhuras de ventilação
    for i in range(5):
        ranhura_x = slide_x + 20 + i * 3
        pygame.draw.line(tela, cor_metal_escuro,
                        (ranhura_x, slide_y + 2),
                        (ranhura_x, slide_y + slide_altura - 2), 2)
        pygame.draw.line(tela, cor_metal_claro,
                        (ranhura_x + 1, slide_y + 2),
                        (ranhura_x + 1, slide_y + slide_altura - 2), 1)

    # === CANO MASSIVO ===
    cano_x = slide_x + slide_largura
    cano_y = y
    cano_raio = 4

    pygame.draw.circle(tela, cor_metal_medio, (cano_x, cano_y), cano_raio)
    pygame.draw.circle(tela, cor_metal_claro, (cano_x, cano_y - 1), cano_raio - 1)
    pygame.draw.circle(tela, cor_cano_interno, (cano_x, cano_y), cano_raio - 2)
    pygame.draw.circle(tela, (10, 10, 15), (cano_x, cano_y), cano_raio - 3)
    pygame.draw.circle(tela, cor_metal_escuro, (cano_x, cano_y), cano_raio, 1)

    # === FRAME ===
    frame_x = slide_x + 3
    frame_y = y
    frame_largura = 26
    frame_altura = 12

    frame_rect = pygame.Rect(frame_x, frame_y - frame_altura//2, frame_largura, frame_altura)
    pygame.draw.rect(tela, cor_metal_escuro, frame_rect, 0, 2)
    pygame.draw.rect(tela, cor_metal_medio,
                    (frame_x + 1, frame_y - frame_altura//2 + 1, frame_largura - 2, 2), 0, 1)

    # === TRILHO PICATINNY ===
    trilho_y = slide_y - 2
    for i in range(3):
        trilho_x = slide_x + 15 + i * 4
        pygame.draw.rect(tela, cor_metal_escuro, (trilho_x, trilho_y, 2, 2))

    # === GUARDA-MATO ===
    guarda_centro_x = frame_x + 10
    guarda_centro_y = y + 6

    pygame.draw.ellipse(tela, cor_metal_medio,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 2)
    pygame.draw.ellipse(tela, cor_metal_claro,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 1)

    # === GATILHO ===
    gatilho_x = guarda_centro_x
    gatilho_y = guarda_centro_y
    pygame.draw.rect(tela, cor_metal_claro, (gatilho_x - 2, gatilho_y - 1, 4, 3), 0, 1)
    pygame.draw.line(tela, cor_metal_escuro, (gatilho_x - 1, gatilho_y + 1), (gatilho_x + 1, gatilho_y + 1), 1)

    # === PUNHO ERGONÔMICO ===
    punho_x = frame_x - 1
    punho_y = y + 3

    punho_pontos = [
        (punho_x, punho_y - 4),
        (punho_x + 12, punho_y - 3),
        (punho_x + 10, punho_y + 12),
        (punho_x - 4, punho_y + 10)
    ]

    pygame.draw.polygon(tela, cor_punho_preto, punho_pontos)
    pygame.draw.polygon(tela, cor_detalhes_punho, punho_pontos, 1)

    # Textura antiderrapante
    for i in range(4):
        for j in range(2):
            tex_x = punho_x + 2 + j * 3
            tex_y = punho_y + 1 + i * 3
            pygame.draw.rect(tela, cor_detalhes_punho, (tex_x, tex_y, 2, 2))

    # === CARREGADOR ===
    mag_x = punho_x + 3
    mag_y = punho_y + 12
    pygame.draw.rect(tela, cor_metal_escuro, (mag_x, mag_y, 5, 3))
    pygame.draw.line(tela, cor_metal_claro, (mag_x, mag_y), (mag_x + 5, mag_y), 1)

    # === MIRAS ===
    # Mira frontal
    mira_frontal_x = cano_x - 4
    mira_frontal_y = slide_y - 2
    pygame.draw.rect(tela, cor_metal_claro, (mira_frontal_x, mira_frontal_y, 2, 4))
    pygame.draw.circle(tela, (100, 255, 100), (mira_frontal_x + 1, mira_frontal_y + 1), 1)

    # Mira traseira
    mira_traseira_x = slide_x + 8
    mira_traseira_y = slide_y - 2
    pygame.draw.rect(tela, cor_metal_escuro, (mira_traseira_x, mira_traseira_y, 5, 3))
    pygame.draw.line(tela, cor_cano_interno, (mira_traseira_x + 2, mira_traseira_y),
                    (mira_traseira_x + 2, mira_traseira_y + 2), 2)

    # === EFEITO DE BRILHO ===
    if pulso > 0.7:
        brilho_surf = pygame.Surface((50, 25), pygame.SRCALPHA)
        alpha = int(40 * pulso)
        cor_glow = (200, 200, 210, alpha)

        pygame.draw.line(brilho_surf, cor_glow,
                        (10, 8),
                        (40, 8), 3)

        tela.blit(brilho_surf, (slide_x - 5, slide_y - 5))
