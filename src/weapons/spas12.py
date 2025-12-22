#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a SPAS-12 - uma shotgun tática semi-automática italiana.
A SPAS-12 é mais rápida que a espingarda comum, com detalhes visuais realistas.
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

def carregar_upgrade_spas12():
    """
    Carrega o upgrade de SPAS-12 do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        # Verificar se o arquivo existe
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("spas12", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de SPAS-12: {e}")
        return 0

def salvar_municao_spas12(quantidade):
    """
    Salva a quantidade atual de munição de SPAS-12.

    Args:
        quantidade: Quantidade atual de munição
    """
    try:
        # Carregar upgrades existentes
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)

        # Atualizar munição de SPAS-12
        upgrades["spas12"] = max(0, quantidade)

        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)

        # Salvar
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar munição de SPAS-12: {e}")

def atirar_spas12(jogador, tiros, pos_mouse, particulas=None, flashes=None, num_tiros=5):
    """
    Dispara múltiplos tiros em um padrão de espingarda e cria uma animação de partículas no cano.
    A SPAS-12 tem cooldown reduzido (mais rápida que a espingarda comum).

    Args:
        jogador: O objeto do jogador
        tiros: Lista onde adicionar os novos tiros
        pos_mouse: Tupla (x, y) com a posição do mouse
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
        num_tiros: Número de tiros a disparar
    """
    # Verificar cooldown (SPAS-12 é mais rápida - 1.8x ao invés de 3.2x)
    tempo_atual = pygame.time.get_ticks()
    cooldown_spas12 = jogador.tempo_cooldown * 1.8  # Mais rápida que a espingarda comum
    if tempo_atual - jogador.tempo_ultimo_tiro < cooldown_spas12:
        return

    jogador.tempo_ultimo_tiro = tempo_atual

    # Adicionar efeito de recuo (tremida) ao atirar - menor que a espingarda comum
    jogador.recuo_spas12 = 7  # Intensidade do recuo menor (espingarda comum é 10)
    jogador.tempo_recuo = tempo_atual

    # Posição central do quadrado
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Calcular vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y

    # Normalizar o vetor direção
    distancia = math.sqrt(dx * dx + dy * dy)
    if distancia > 0:  # Evitar divisão por zero
        dx /= distancia
        dy /= distancia

    # Som de tiro de SPAS-12 (mais seco e forte)
    som_spas = pygame.mixer.Sound(gerar_som_tiro())
    som_spas.set_volume(0.35)  # Volume ligeiramente mais alto
    pygame.mixer.Channel(1).play(som_spas)

    # Ângulo de dispersão para cada tiro (menor que espingarda comum)
    angulo_base = math.atan2(dy, dx)
    dispersao = 0.25  # Dispersão menor (espingarda comum é 0.3)

    # Calcular a posição da ponta do cano para o efeito de partículas
    comprimento_arma = 38
    ponta_cano_x = centro_x + dx * comprimento_arma
    ponta_cano_y = centro_y + dy * comprimento_arma

    # Criar efeito de partículas na ponta do cano
    if particulas is not None:
        # Cor laranja/amarela para SPAS-12
        cores_particulas = [
            (255, 255, 0),   # Amarelo
            (255, 200, 0),   # Amarelo-laranja
            (255, 150, 0)    # Laranja
        ]

        # Criar várias partículas para um efeito de explosão no cano
        for _ in range(18):  # Mais partículas que a espingarda comum
            # Alternar cores
            cor = random.choice(cores_particulas)

            # Posição com pequena variação aleatória ao redor da ponta do cano
            vari_x = random.uniform(-4, 4)
            vari_y = random.uniform(-4, 4)
            pos_x = ponta_cano_x + vari_x
            pos_y = ponta_cano_y + vari_y

            # Criar partícula
            particula = Particula(pos_x, pos_y, cor)

            # Configurar propriedades da partícula para simular o disparo
            particula.velocidade_x = dx * random.uniform(2, 6) + random.uniform(-1, 1)
            particula.velocidade_y = dy * random.uniform(2, 6) + random.uniform(-1, 1)
            particula.vida = random.randint(6, 18)  # Vida média
            particula.tamanho = random.uniform(1.8, 4.5)  # Partículas variadas
            particula.gravidade = 0.04  # Gravidade reduzida

            # Adicionar à lista de partículas
            particulas.append(particula)

    # Adicionar um flash luminoso na ponta do cano (maior que espingarda comum)
    if flashes is not None:
        flash = {
            'x': ponta_cano_x,
            'y': ponta_cano_y,
            'raio': 18,  # Flash maior
            'vida': 6,
            'cor': (255, 200, 0)  # Laranja-amarelo
        }
        flashes.append(flash)

    # Criar tiros com ângulos ligeiramente diferentes
    for i in range(num_tiros):
        # Calcular ângulo para este tiro
        angulo_variacao = dispersao * (i / (num_tiros - 1) - 0.5) * 2
        angulo_atual = angulo_base + angulo_variacao

        # Calcular direção com o novo ângulo
        tiro_dx = math.cos(angulo_atual)
        tiro_dy = math.sin(angulo_atual)

        # Criar tiro com a direção calculada (usar a cor do jogador)
        tiro = Tiro(centro_x, centro_y, tiro_dx, tiro_dy, jogador.cor, 8)
        tiro.dano = 2  # SPAS-12 causa 2 de dano!
        tiros.append(tiro)

    # Reduzir contador de tiros apenas se jogador for passado como parâmetro
    if hasattr(jogador, 'tiros_spas12'):
        jogador.tiros_spas12 -= 1
        # Desativar SPAS-12 se acabaram os tiros
        if jogador.tiros_spas12 <= 0:
            jogador.spas12_ativa = False

def desenhar_barra_cooldown_spas12(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha uma barra vertical mostrando o progresso do cooldown da SPAS-12.
    A barra aparece no lado oposto ao qual o jogador está apontando.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms
        pos_mouse: Posição do mouse para calcular direção
    """
    # Calcular o centro do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Calcular o vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y

    # Normalizar o vetor direção
    distancia = math.sqrt(dx**2 + dy**2)
    if distancia > 0:
        dx /= distancia
        dy /= distancia

    # Calcular tempo de cooldown
    cooldown_spas12 = jogador.tempo_cooldown
    tempo_desde_ultimo_tiro = tempo_atual - jogador.tempo_ultimo_tiro

    # Se ainda está em cooldown, desenhar a barra
    if tempo_desde_ultimo_tiro < cooldown_spas12:
        # Calcular progresso (0 a 1)
        progresso = tempo_desde_ultimo_tiro / cooldown_spas12

        # Posição da barra no lado oposto (direção inversa)
        distancia_barra = 32  # Distância do centro do jogador
        pos_barra_x = centro_x - dx * distancia_barra
        pos_barra_y = centro_y - dy * distancia_barra

        # Dimensões da barra
        largura_barra = 7
        altura_barra_total = 32
        altura_preenchida = altura_barra_total * progresso

        # Desenhar fundo da barra (vazio)
        pygame.draw.rect(tela, (60, 60, 60),
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y - altura_barra_total // 2,
                         largura_barra,
                         altura_barra_total))

        # Desenhar barra de progresso (de baixo para cima)
        # Cor gradiente laranja -> verde (diferente da espingarda)
        if progresso < 0.5:
            cor_barra = (255, int(140 + progresso * 230), 0)  # Laranja -> Amarelo
        else:
            cor_barra = (int(255 - (progresso - 0.5) * 430), 255, int((progresso - 0.5) * 100))  # Amarelo -> Verde-amarelado

        pygame.draw.rect(tela, cor_barra,
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y + altura_barra_total // 2 - altura_preenchida,
                         largura_barra,
                         altura_preenchida))

        # Contorno da barra
        pygame.draw.rect(tela, (220, 180, 100),
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y - altura_barra_total // 2,
                         largura_barra,
                         altura_barra_total), 1)

def desenhar_spas12(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha a SPAS-12 na posição do jogador, orientada para a direção do mouse.
    SPAS-12 é uma shotgun tática italiana semi-automática com design moderno.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
        pos_mouse: Posição do mouse
    """
    # Desenhar barra de cooldown primeiro (fica atrás da arma)
    desenhar_barra_cooldown_spas12(tela, jogador, tempo_atual, pos_mouse)

    # Calcular o centro do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Calcular o vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y

    # Normalizar o vetor direção
    distancia = math.sqrt(dx**2 + dy**2)
    if distancia > 0:
        dx /= distancia
        dy /= distancia

    # Efeito de recuo (tremida) após atirar
    offset_recuo_x = 0
    offset_recuo_y = 0
    if hasattr(jogador, 'recuo_spas12') and hasattr(jogador, 'tempo_recuo'):
        tempo_desde_tiro = tempo_atual - jogador.tempo_recuo
        if tempo_desde_tiro < 180:  # Duração do efeito de recuo em ms (mais rápido)
            # Recuo diminui ao longo do tempo
            intensidade = jogador.recuo_spas12 * (1 - tempo_desde_tiro / 180)
            # Recuar na direção oposta ao tiro (para trás)
            offset_recuo_x = -dx * intensidade
            offset_recuo_y = -dy * intensidade
            # Adicionar pequena tremida aleatória
            offset_recuo_x += random.uniform(-1.5, 1.5) * (intensidade / 10)
            offset_recuo_y += random.uniform(-1.5, 1.5) * (intensidade / 10)

    # Aplicar offset de recuo ao centro
    centro_x += offset_recuo_x
    centro_y += offset_recuo_y

    # Comprimento da SPAS-12
    comprimento_arma = 45  # SPAS-12 é mais longa

    # Posição da ponta da arma
    ponta_x = centro_x + dx * comprimento_arma
    ponta_y = centro_y + dy * comprimento_arma

    # Vetor perpendicular para elementos laterais
    perp_x = -dy
    perp_y = dx

    # Cores da SPAS-12 (design tático moderno)
    cor_metal_escuro = (45, 45, 50)      # Metal tático preto
    cor_metal_medio = (80, 80, 90)       # Metal médio
    cor_metal_claro = (120, 120, 130)    # Metal detalhes
    cor_cano = (35, 35, 40)              # Cano preto fosco
    cor_polimero = (60, 60, 65)          # Polímero preto
    cor_laranja_tatico = (255, 140, 0)   # Laranja tático (ponta de segurança)

    # === CORONHA DOBRÁVEL (característica da SPAS-12) ===
    coronha_inicio_x = centro_x - dx * 20
    coronha_inicio_y = centro_y - dy * 20

    # Coronha tática de polímero/metal
    coronha_pontos = [
        (coronha_inicio_x + perp_x * 6, coronha_inicio_y + perp_y * 6),
        (coronha_inicio_x - perp_x * 6, coronha_inicio_y - perp_y * 6),
        (centro_x - dx * 6 - perp_x * 4, centro_y - dy * 6 - perp_y * 4),
        (centro_x - dx * 6 + perp_x * 4, centro_y - dy * 6 + perp_y * 4)
    ]
    pygame.draw.polygon(tela, cor_polimero, coronha_pontos)
    pygame.draw.polygon(tela, cor_metal_claro, coronha_pontos, 2)

    # Detalhes da coronha (linhas táticas)
    for i in range(2):
        offset_dist = -18 + i * 8
        det_x1 = centro_x - dx * offset_dist + perp_x * 5
        det_y1 = centro_y - dy * offset_dist + perp_y * 5
        det_x2 = centro_x - dx * offset_dist - perp_x * 5
        det_y2 = centro_y - dy * offset_dist - perp_y * 5
        pygame.draw.line(tela, cor_metal_claro, (det_x1, det_y1), (det_x2, det_y2), 2)

    # === CORPO/RECEIVER DA SPAS-12 ===
    corpo_x = centro_x + dx * 8
    corpo_y = centro_y + dy * 8

    # Corpo principal (mais robusto)
    corpo_pontos = [
        (centro_x - dx * 6 + perp_x * 7, centro_y - dy * 6 + perp_y * 7),
        (centro_x - dx * 6 - perp_x * 7, centro_y - dy * 6 - perp_y * 7),
        (corpo_x - perp_x * 6, corpo_y - perp_y * 6),
        (corpo_x + perp_x * 6, corpo_y + perp_y * 6)
    ]
    pygame.draw.polygon(tela, cor_metal_escuro, corpo_pontos)
    pygame.draw.polygon(tela, cor_metal_claro, corpo_pontos, 1)

    # Trilho superior Picatinny (característica moderna)
    trilho_x1 = centro_x - dx * 4
    trilho_y1 = centro_y - dy * 4
    trilho_x2 = corpo_x + dx * 8
    trilho_y2 = corpo_y + dy * 8
    pygame.draw.line(tela, cor_metal_medio,
                    (trilho_x1 + perp_x * 7, trilho_y1 + perp_y * 7),
                    (trilho_x2 + perp_x * 7, trilho_y2 + perp_y * 7), 3)

    # Detalhes do trilho (slots)
    for i in range(4):
        slot_x = trilho_x1 + dx * (i * 4) + perp_x * 7
        slot_y = trilho_y1 + dy * (i * 4) + perp_y * 7
        pygame.draw.circle(tela, cor_metal_escuro, (int(slot_x), int(slot_y)), 1)

    # === GATILHO E GUARDA-MATO ===
    gatilho_base_x = centro_x - dx * 1
    gatilho_base_y = centro_y - dy * 1
    gatilho_ponta_x = gatilho_base_x - perp_x * 5
    gatilho_ponta_y = gatilho_base_y - perp_y * 5

    # Guarda-mato robusto
    pygame.draw.line(tela, cor_metal_claro,
                    (gatilho_base_x - dx * 5, gatilho_base_y - dy * 5),
                    (gatilho_ponta_x - dx * 3, gatilho_ponta_y - dy * 3), 3)
    pygame.draw.line(tela, cor_metal_claro,
                    (gatilho_ponta_x - dx * 3, gatilho_ponta_y - dy * 3),
                    (gatilho_ponta_x, gatilho_ponta_y), 3)

    # Gatilho (laranja para segurança)
    pygame.draw.line(tela, cor_laranja_tatico,
                    (gatilho_base_x, gatilho_base_y),
                    (gatilho_ponta_x - dx * 1, gatilho_ponta_y - dy * 1), 3)

    # === CANO ÚNICO (SPAS-12 tem cano único, não duplo) ===
    inicio_cano_x = corpo_x
    inicio_cano_y = corpo_y

    # Cano principal grosso e robusto
    pygame.draw.line(tela, cor_cano,
                    (inicio_cano_x, inicio_cano_y),
                    (ponta_x, ponta_y), 7)

    # Contornos do cano para profundidade
    pygame.draw.line(tela, cor_metal_claro,
                    (inicio_cano_x + perp_x * 3.5, inicio_cano_y + perp_y * 3.5),
                    (ponta_x + perp_x * 3.5, ponta_y + perp_y * 3.5), 1)
    pygame.draw.line(tela, cor_metal_escuro,
                    (inicio_cano_x - perp_x * 3.5, inicio_cano_y - perp_y * 3.5),
                    (ponta_x - perp_x * 3.5, ponta_y - perp_y * 3.5), 1)

    # === TUBO DE MAGAZINE EMBAIXO (característica da SPAS-12) ===
    tubo_inicio_x = corpo_x - dx * 3
    tubo_inicio_y = corpo_y - dy * 3
    tubo_fim_x = ponta_x - dx * 5
    tubo_fim_y = ponta_y - dy * 5

    pygame.draw.line(tela, cor_metal_medio,
                    (tubo_inicio_x - perp_x * 5, tubo_inicio_y - perp_y * 5),
                    (tubo_fim_x - perp_x * 5, tubo_fim_y - perp_y * 5), 4)

    # === HANDGUARD (proteção de mão) ===
    handguard_x1 = corpo_x + dx * 2
    handguard_y1 = corpo_y + dy * 2
    handguard_x2 = ponta_x - dx * 10
    handguard_y2 = ponta_y - dy * 10

    # Proteção superior
    pygame.draw.line(tela, cor_polimero,
                    (handguard_x1 + perp_x * 5, handguard_y1 + perp_y * 5),
                    (handguard_x2 + perp_x * 5, handguard_y2 + perp_y * 5), 3)
    # Proteção inferior
    pygame.draw.line(tela, cor_polimero,
                    (handguard_x1 - perp_x * 5, handguard_y1 - perp_y * 5),
                    (handguard_x2 - perp_x * 5, handguard_y2 - perp_y * 5), 3)

    # === BOCA DO CANO ===
    pygame.draw.circle(tela, cor_metal_medio, (int(ponta_x), int(ponta_y)), 5)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(ponta_y)), 3)

    # Ponta laranja de segurança (característica de algumas SPAS-12)
    pygame.draw.circle(tela, cor_laranja_tatico, (int(ponta_x), int(ponta_y)), 2)

    # === SIGHT (mira frontal) ===
    mira_x = ponta_x - dx * 8
    mira_y = ponta_y - dy * 8
    pygame.draw.line(tela, cor_metal_claro,
                    (mira_x + perp_x * 8, mira_y + perp_y * 8),
                    (mira_x + perp_x * 8 - perp_x * 2, mira_y + perp_y * 8 - perp_y * 2), 3)
    # Ponto verde na mira
    pygame.draw.circle(tela, (100, 255, 100), (int(mira_x + perp_x * 7), int(mira_y + perp_y * 7)), 2)

    # === EFEITO DE ENERGIA (quando ativa) ===
    pulso = (math.sin(tempo_atual / 130) + 1) / 2
    cor_energia = (255, int(140 + pulso * 115), 0)  # Laranja pulsante
    energia_width = 1 + int(pulso * 2.5)

    # Linha de energia no cano
    pygame.draw.line(tela, cor_energia,
                    (corpo_x, corpo_y),
                    (ponta_x, ponta_y), energia_width)

    # Linha de energia no tubo de magazine
    pygame.draw.line(tela, cor_energia,
                    (tubo_inicio_x - perp_x * 5, tubo_inicio_y - perp_y * 5),
                    (tubo_fim_x - perp_x * 5, tubo_fim_y - perp_y * 5), max(1, energia_width - 1))
