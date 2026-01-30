#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar todas as funcionalidades relacionadas à Sniper.
Sniper - Rifle de ferrolho de alta precisão.
Características:
- Dano: 5 (muito alto)
- Velocidade do tiro: 25 (muito rápido)
- Cooldown: Alto (1500ms)
- Visual: Rifle de ferrolho típico com scope
- Mecânica especial:
  - Tiro normal (sem mirar): vai em direção aleatória
  - Com botão direito pressionado: ativa mira laser e tiro vai preciso
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


def carregar_upgrade_sniper():
    """
    Carrega o upgrade de Sniper do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("sniper", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de Sniper: {e}")
        return 0


def salvar_municao_sniper(quantidade):
    """
    Salva a quantidade atual de munição de sniper.

    Args:
        quantidade: Quantidade atual de munição
    """
    try:
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
        upgrades["sniper"] = max(0, quantidade)
        os.makedirs("data", exist_ok=True)
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar munição de sniper: {e}")


def atirar_sniper(jogador, tiros, pos_mouse, particulas=None, flashes=None, mirando=False):
    """
    Dispara um tiro da Sniper.
    Se mirando=True, tiro vai preciso na direção do mouse.
    Se mirando=False, tiro vai em direção aleatória.

    Args:
        jogador: O objeto do jogador
        tiros: Lista onde adicionar o novo tiro
        pos_mouse: Tupla (x, y) com a posição do mouse
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
        mirando: Se True, o jogador está segurando botão direito (mira ativa)
    """
    cooldown_sniper = 1500  # Cooldown alto para rifle de ferrolho

    # Verificar cooldown
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - jogador.tempo_ultimo_tiro < cooldown_sniper:
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

    # Se NÃO está mirando, adicionar grande imprecisão (tiro aleatório)
    if not mirando:
        # Imprecisão grande - tiro vai em direção completamente aleatória
        angulo_aleatorio = random.uniform(-math.pi / 2, math.pi / 2)  # -90 a +90 graus
        cos_a = math.cos(angulo_aleatorio)
        sin_a = math.sin(angulo_aleatorio)
        novo_dx = dx * cos_a - dy * sin_a
        novo_dy = dx * sin_a + dy * cos_a
        dx, dy = novo_dx, novo_dy

    # Som de tiro da Sniper (mais grave e impactante)
    som_sniper = pygame.mixer.Sound(gerar_som_tiro())
    som_sniper.set_volume(0.4)  # Volume alto para impacto
    pygame.mixer.Channel(5).play(som_sniper)  # Canal dedicado para sniper

    # Calcular posição da ponta do cano
    comprimento_arma = 55  # Sniper é mais longa
    ponta_cano_x = centro_x + dx * comprimento_arma
    ponta_cano_y = centro_y + dy * comprimento_arma

    # Criar tiro poderoso da Sniper
    # Velocidade: 25 (muito rápido)
    # Dano: 10 (extremamente alto)
    tiro = Tiro(ponta_cano_x, ponta_cano_y, dx, dy, jogador.cor, velocidade=40)
    tiro.dano = 6  # Dano extremo!
    tiro.raio = 3  # Projétil fino mas visível
    tiros.append(tiro)

    # Efeitos visuais no cano
    if particulas is not None:
        criar_efeito_disparo_sniper(ponta_cano_x, ponta_cano_y, dx, dy, particulas)

    # Flash de luz no disparo
    if flashes is not None:
        flash = {
            'x': ponta_cano_x,
            'y': ponta_cano_y,
            'raio': 15,
            'vida': 6,
            'cor': (255, 255, 200)  # Flash branco-amarelado
        }
        flashes.append(flash)

    # Efeito de recuo
    if hasattr(jogador, 'recuo_sniper'):
        jogador.recuo_sniper = 15
        jogador.tempo_recuo_sniper = tempo_atual

    # Reduzir munição
    if hasattr(jogador, 'tiros_sniper'):
        jogador.tiros_sniper -= 1


def criar_efeito_disparo_sniper(x, y, dx, dy, particulas):
    """
    Cria efeitos de partículas para o disparo da Sniper.

    Args:
        x, y: Posição do disparo
        dx, dy: Direção do disparo (normalizada)
        particulas: Lista onde adicionar as partículas
    """
    # Chama do disparo (mais intensa e direcionada)
    cores_chama = [
        (255, 255, 200),  # Branco amarelado
        (255, 220, 150),  # Amarelo claro
        (255, 180, 100),  # Laranja claro
    ]

    # Criar partículas da chama (menos partículas mas mais intensas)
    num_particulas = random.randint(8, 12)
    for _ in range(num_particulas):
        # Ângulo base do disparo
        angulo_base = math.atan2(dy, dx)

        # Dispersão menor para efeito mais focado
        dispersao = random.uniform(-0.3, 0.3)
        angulo_particula = angulo_base + dispersao

        # Velocidade da partícula
        velocidade = random.uniform(5, 10)
        vel_x = math.cos(angulo_particula) * velocidade
        vel_y = math.sin(angulo_particula) * velocidade

        # Cor aleatória da chama
        cor = random.choice(cores_chama)

        # Criar partícula
        particula = Particula(x, y, cor)
        particula.velocidade_x = vel_x
        particula.velocidade_y = vel_y
        particula.vida = random.randint(5, 10)
        particula.tamanho = random.randint(2, 4)
        particulas.append(particula)

    # Fumaça do disparo (mais visível)
    cores_fumaca = [
        (180, 180, 180),
        (150, 150, 150),
        (120, 120, 120),
    ]

    num_fumaca = random.randint(4, 7)
    for _ in range(num_fumaca):
        angulo_base = math.atan2(dy, dx)
        dispersao = random.uniform(-0.4, 0.4)
        angulo_fumaca = angulo_base + dispersao

        velocidade = random.uniform(1, 4)
        vel_x = math.cos(angulo_fumaca) * velocidade
        vel_y = math.sin(angulo_fumaca) * velocidade

        cor = random.choice(cores_fumaca)

        particula = Particula(
            x + random.randint(-5, 5),
            y + random.randint(-5, 5),
            cor
        )
        particula.velocidade_x = vel_x
        particula.velocidade_y = vel_y
        particula.vida = random.randint(20, 35)
        particula.tamanho = random.randint(2, 4)
        particulas.append(particula)

    # Casca de bala ejetada
    if random.random() < 0.9:  # 90% de chance
        # Perpendicular à direção do tiro (para o lado)
        perp_x = -dy
        perp_y = dx

        # Casca ejetada para o lado
        vel_casca_x = perp_x * random.uniform(3, 5) + dx * random.uniform(-1, 1)
        vel_casca_y = perp_y * random.uniform(3, 5) + dy * random.uniform(-1, 1) - 2

        particula_casca = Particula(
            x - dx * 10, y - dy * 10,  # Atrás do cano (câmara de ferrolho)
            (200, 180, 100)  # Cor de latão
        )
        particula_casca.velocidade_x = vel_casca_x
        particula_casca.velocidade_y = vel_casca_y
        particula_casca.vida = random.randint(25, 40)
        particula_casca.tamanho = 3
        particulas.append(particula_casca)


def desenhar_barra_cooldown_sniper(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha uma barra vertical mostrando o progresso do cooldown da sniper.
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

    # Calcular tempo de cooldown (mesmo valor usado em atirar_sniper)
    cooldown_sniper = 1000
    tempo_desde_ultimo_tiro = tempo_atual - jogador.tempo_ultimo_tiro

    # Se ainda está em cooldown, desenhar a barra
    if tempo_desde_ultimo_tiro < cooldown_sniper:
        # Calcular progresso (0 a 1)
        progresso = tempo_desde_ultimo_tiro / cooldown_sniper

        # Posição da barra no lado oposto (direção inversa)
        distancia_barra = 30  # Distância do centro do jogador
        pos_barra_x = centro_x - dx * distancia_barra
        pos_barra_y = centro_y - dy * distancia_barra

        # Dimensões da barra
        largura_barra = 6
        altura_barra_total = 30
        altura_preenchida = altura_barra_total * progresso

        # Desenhar fundo da barra (vazio)
        pygame.draw.rect(tela, (50, 50, 50),
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y - altura_barra_total // 2,
                         largura_barra,
                         altura_barra_total))

        # Desenhar barra de progresso (de baixo para cima)
        # Cor gradiente baseada no progresso (azul -> ciano para sniper)
        if progresso < 0.5:
            verde = min(255, max(0, int(progresso * 300)))
            cor_barra = (0, verde, 255)  # Azul -> Ciano
        else:
            azul = min(255, max(0, int(255 - (progresso - 0.5) * 200)))
            cor_barra = (0, 255, azul)  # Ciano -> Verde-água

        # Garantir altura mínima para evitar erros
        if altura_preenchida < 1:
            altura_preenchida = 1

        pygame.draw.rect(tela, cor_barra,
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y + altura_barra_total // 2 - altura_preenchida,
                         largura_barra,
                         altura_preenchida))

        # Contorno da barra
        pygame.draw.rect(tela, (200, 200, 200),
                        (pos_barra_x - largura_barra // 2,
                         pos_barra_y - altura_barra_total // 2,
                         largura_barra,
                         altura_barra_total), 1)


def desenhar_sniper(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha a Sniper seguindo a posição do mouse.
    Visual idêntico ao ícone da loja.
    O scope sempre fica na parte de cima, nunca inverte.
    Inclui mira laser quando o jogador está segurando botão direito.

    Args:
        tela: Superfície do Pygame onde desenhar
        jogador: Objeto do jogador
        pos_mouse: Tupla (x, y) com a posição do mouse
    """
    # Desenhar barra de cooldown primeiro (fica atrás da sniper)
    desenhar_barra_cooldown_sniper(tela, jogador, tempo_atual, pos_mouse)

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

    # Simulação de recuo
    recuo = 0
    if hasattr(jogador, 'recuo_sniper') and jogador.recuo_sniper > 0:
        recuo = jogador.recuo_sniper
        jogador.recuo_sniper -= 1

    # Cores da Sniper (idênticas ao ícone)
    cor_metal_escuro = (50, 55, 60)
    cor_metal_medio = (80, 85, 90)
    cor_metal_claro = (110, 115, 120)
    cor_coronha = (60, 45, 35)
    cor_scope = (30, 30, 35)
    cor_lente = (100, 150, 200)

    # Comprimento da arma
    comprimento = 56

    # Vetor perpendicular (sempre apontando para "cima" na tela)
    # Quando olhando para a esquerda (dx < 0), perp aponta para cima
    # Quando olhando para a direita (dx > 0), invertemos para manter scope em cima
    perp_x = dy
    perp_y = -dx

    # Se olhando para a esquerda, inverter o perpendicular para scope ficar em cima
    if dx < 0:
        perp_x = -dy
        perp_y = dx

    # Posição base (centro do jogador com recuo aplicado)
    base_x = centro_x - dx * recuo
    base_y = centro_y - dy * recuo

    # === CORONHA (parte traseira) ===
    coronha_tras_x = base_x - dx * 28
    coronha_tras_y = base_y - dy * 28
    coronha_frente_x = base_x - dx * 7
    coronha_frente_y = base_y - dy * 7

    pygame.draw.polygon(tela, cor_coronha, [
        (coronha_tras_x + perp_x * 6, coronha_tras_y + perp_y * 6),
        (coronha_tras_x - perp_x * 6, coronha_tras_y - perp_y * 6),
        (coronha_frente_x - perp_x * 4, coronha_frente_y - perp_y * 4),
        (coronha_frente_x + perp_x * 4, coronha_frente_y + perp_y * 4)
    ])

    # === CORPO/RECEPTOR ===
    corpo_x = base_x - dx * 7
    corpo_y = base_y - dy * 7
    corpo_largura = 21

    # Desenhar corpo como polígono
    corpo_p1 = (corpo_x + perp_x * 5, corpo_y + perp_y * 5)
    corpo_p2 = (corpo_x - perp_x * 6, corpo_y - perp_y * 6)
    corpo_p3 = (corpo_x + dx * corpo_largura - perp_x * 6, corpo_y + dy * corpo_largura - perp_y * 6)
    corpo_p4 = (corpo_x + dx * corpo_largura + perp_x * 5, corpo_y + dy * corpo_largura + perp_y * 5)
    pygame.draw.polygon(tela, cor_metal_medio, [corpo_p1, corpo_p2, corpo_p3, corpo_p4])
    pygame.draw.polygon(tela, cor_metal_claro, [corpo_p1, corpo_p2, corpo_p3, corpo_p4], 1)

    # === FERROLHO (sempre em cima) ===
    ferrolho_x = base_x + dx * 7
    ferrolho_y = base_y + dy * 7
    ferrolho_cima_x = ferrolho_x + perp_x * 7
    ferrolho_cima_y = ferrolho_y + perp_y * 7
    pygame.draw.circle(tela, cor_metal_claro, (int(ferrolho_cima_x), int(ferrolho_cima_y)), 4)
    pygame.draw.line(tela, cor_metal_claro,
                    (int(ferrolho_cima_x), int(ferrolho_cima_y)),
                    (int(ferrolho_cima_x + perp_x * 7), int(ferrolho_cima_y + perp_y * 7)), 2)

    # === CANO ===
    cano_inicio_x = base_x + dx * 14
    cano_inicio_y = base_y + dy * 14
    cano_fim_x = base_x + dx * comprimento
    cano_fim_y = base_y + dy * comprimento
    pygame.draw.line(tela, cor_metal_escuro, (int(cano_inicio_x), int(cano_inicio_y)), (int(cano_fim_x), int(cano_fim_y)), 5)
    # Brilho no cano
    pygame.draw.line(tela, cor_metal_claro,
                    (int(cano_inicio_x + perp_x * 2), int(cano_inicio_y + perp_y * 2)),
                    (int(cano_fim_x + perp_x * 2), int(cano_fim_y + perp_y * 2)), 1)

    # === BOCA DO CANO ===
    pygame.draw.circle(tela, cor_metal_medio, (int(cano_fim_x), int(cano_fim_y)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(cano_fim_x), int(cano_fim_y)), 2)

    # === SCOPE (sempre em cima - usa perp que já está ajustado) ===
    scope_offset = 8  # Distância do scope acima do cano
    scope_inicio_x = base_x + dx * 7 + perp_x * scope_offset
    scope_inicio_y = base_y + dy * 7 + perp_y * scope_offset
    scope_fim_x = base_x + dx * 28 + perp_x * scope_offset
    scope_fim_y = base_y + dy * 28 + perp_y * scope_offset

    # Corpo do scope
    pygame.draw.line(tela, cor_scope, (int(scope_inicio_x), int(scope_inicio_y)), (int(scope_fim_x), int(scope_fim_y)), 6)

    # Lentes do scope
    pygame.draw.circle(tela, cor_metal_medio, (int(scope_inicio_x), int(scope_inicio_y)), 5)
    pygame.draw.circle(tela, cor_lente, (int(scope_inicio_x), int(scope_inicio_y)), 3)
    pygame.draw.circle(tela, cor_metal_medio, (int(scope_fim_x), int(scope_fim_y)), 5)
    pygame.draw.circle(tela, cor_lente, (int(scope_fim_x), int(scope_fim_y)), 3)

    # === EFEITO DE ENERGIA ===
    pulso = (math.sin(tempo_atual / 250) + 1) / 2
    if pulso > 0.6:
        cor_energia = (255, int(200 + pulso * 55), int(150 + pulso * 105))
        energia_inicio_x = base_x + dx * 17
        energia_inicio_y = base_y + dy * 17
        energia_fim_x = base_x + dx * (comprimento - 3)
        energia_fim_y = base_y + dy * (comprimento - 3)
        pygame.draw.line(tela, cor_energia, (int(energia_inicio_x), int(energia_inicio_y)), (int(energia_fim_x), int(energia_fim_y)), 1)

        # Brilho na lente
        cor_brilho = (100 + int(pulso * 100), 150 + int(pulso * 50), 200 + int(pulso * 55))
        pygame.draw.circle(tela, cor_brilho, (int(scope_inicio_x), int(scope_inicio_y)), 4)

    # === MIRA LASER (quando segurando botão direito) ===
    if hasattr(jogador, 'sniper_mirando') and jogador.sniper_mirando:
        # Cor do laser (vermelho)
        cor_laser = (255, 50, 50)

        # Posição da ponta do cano
        ponta_x = cano_fim_x
        ponta_y = cano_fim_y

        # Linha laser pontilhada até o mouse
        passos = int(distancia // 12)
        for i in range(0, passos, 2):  # Pular de 2 em 2 para efeito pontilhado
            laser_x = ponta_x + dx * (i * 12)
            laser_y = ponta_y + dy * (i * 12)
            pygame.draw.circle(tela, cor_laser, (int(laser_x), int(laser_y)), 2)

        # Ponto final mais brilhante
        pygame.draw.circle(tela, (255, 100, 100), (int(pos_mouse[0]), int(pos_mouse[1])), 5)
        pygame.draw.circle(tela, cor_laser, (int(pos_mouse[0]), int(pos_mouse[1])), 3)

        # Efeito de brilho na lente do scope quando mirando
        pygame.draw.circle(tela, (150, 200, 255), (int(scope_inicio_x), int(scope_inicio_y)), 4)


def desenhar_icone_sniper(tela, x, y, tempo_atual):
    """
    Desenha o ícone da Sniper para a loja e inventário.
    """
    # Cores da Sniper
    cor_metal_escuro = (50, 55, 60)
    cor_metal_medio = (80, 85, 90)
    cor_metal_claro = (110, 115, 120)
    cor_coronha = (60, 45, 35)
    cor_scope = (30, 30, 35)
    cor_lente = (100, 150, 200)

    # Comprimento total do ícone
    comprimento = 40

    # === CORONHA ===
    pygame.draw.polygon(tela, cor_coronha, [
        (x - 20, y - 4),
        (x - 20, y + 4),
        (x - 5, y + 3),
        (x - 5, y - 3)
    ])

    # === CORPO ===
    pygame.draw.rect(tela, cor_metal_medio, (x - 5, y - 4, 15, 8))
    pygame.draw.rect(tela, cor_metal_claro, (x - 5, y - 4, 15, 8), 1)

    # === FERROLHO ===
    pygame.draw.circle(tela, cor_metal_claro, (x + 5, y - 5), 3)
    pygame.draw.line(tela, cor_metal_claro, (x + 5, y - 5), (x + 5, y - 10), 2)

    # === CANO ===
    pygame.draw.line(tela, cor_metal_escuro, (x + 10, y), (x + comprimento, y), 4)
    pygame.draw.line(tela, cor_metal_claro, (x + 10, y - 2), (x + comprimento, y - 2), 1)

    # === BOCA DO CANO ===
    pygame.draw.circle(tela, cor_metal_medio, (x + comprimento, y), 3)
    pygame.draw.circle(tela, (20, 20, 20), (x + comprimento, y), 1)

    # === SCOPE ===
    pygame.draw.line(tela, cor_scope, (x + 5, y - 6), (x + 20, y - 6), 5)
    pygame.draw.circle(tela, cor_metal_medio, (x + 5, y - 6), 4)
    pygame.draw.circle(tela, cor_lente, (x + 5, y - 6), 2)
    pygame.draw.circle(tela, cor_metal_medio, (x + 20, y - 6), 4)
    pygame.draw.circle(tela, cor_lente, (x + 20, y - 6), 2)

    # === EFEITO DE ENERGIA ===
    pulso = (math.sin(tempo_atual / 250) + 1) / 2
    if pulso > 0.6:
        cor_energia = (255, int(200 + pulso * 55), int(150 + pulso * 105))
        pygame.draw.line(tela, cor_energia, (x + 12, y), (x + comprimento - 2, y), 1)

        # Brilho na lente
        cor_brilho = (100 + int(pulso * 100), 150 + int(pulso * 50), 200 + int(pulso * 55))
        pygame.draw.circle(tela, cor_brilho, (x + 5, y - 6), 3)
