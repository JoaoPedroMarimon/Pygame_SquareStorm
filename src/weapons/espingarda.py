#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar todas as funcionalidades relacionadas à espingarda.
Inclui funções para carregar upgrades, atirar e criar efeitos visuais.
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

def carregar_upgrade_espingarda():
    """
    Carrega o upgrade de espingarda do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        # Verificar se o arquivo existe
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("espingarda", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de espingarda: {e}")
        return 0

def salvar_municao_espingarda(quantidade):
    """
    Salva a quantidade atual de munição de espingarda.

    Args:
        quantidade: Quantidade atual de munição
    """
    try:
        # Carregar upgrades existentes
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)

        # Atualizar munição de espingarda
        upgrades["espingarda"] = max(0, quantidade)

        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)

        # Salvar
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar munição de espingarda: {e}")

def atirar_espingarda(jogador, tiros, pos_mouse, particulas=None, flashes=None, num_tiros=5):
    """
    Dispara múltiplos tiros em um padrão de espingarda e cria uma animação de partículas no cano.

    Args:
        jogador: O objeto do jogador
        tiros: Lista onde adicionar os novos tiros
        pos_mouse: Tupla (x, y) com a posição do mouse
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
        num_tiros: Número de tiros a disparar
    """
    # Verificar cooldown
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - jogador.tempo_ultimo_tiro < jogador.tempo_cooldown:
        return

    jogador.tempo_ultimo_tiro = tempo_atual

    # Adicionar efeito de recuo (tremida) ao atirar
    jogador.recuo_espingarda = 10  # Intensidade do recuo
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
    
    # Som de tiro de espingarda (mais forte)
    som_espingarda = pygame.mixer.Sound(gerar_som_tiro())
    som_espingarda.set_volume(0.3)  # Volume mais alto para a espingarda
    pygame.mixer.Channel(1).play(som_espingarda)
    
    # Ângulo de dispersão para cada tiro
    angulo_base = math.atan2(dy, dx)
    dispersao = 0.3  # Aumentar a dispersão de 0.2 para 0.3 para ter um leque maior
    
    # Calcular a posição da ponta do cano para o efeito de partículas
    comprimento_arma = 35
    ponta_cano_x = centro_x + dx * comprimento_arma
    ponta_cano_y = centro_y + dy * comprimento_arma
    
    # Criar efeito de partículas na ponta do cano
    if particulas is not None:
        # Definir cor amarela para todas as partículas
        cor_amarela = (255, 255, 0)  # Amarelo puro
        
        # Criar várias partículas para um efeito de explosão no cano
        for _ in range(15):
            # Todas as partículas serão amarelas
            cor = cor_amarela
            
            # Posição com pequena variação aleatória ao redor da ponta do cano
            vari_x = random.uniform(-5, 5)
            vari_y = random.uniform(-5, 5)
            pos_x = ponta_cano_x + vari_x
            pos_y = ponta_cano_y + vari_y
            
            # Criar partícula
            particula = Particula(pos_x, pos_y, cor)
            
            # Configurar propriedades da partícula para simular o disparo
            particula.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-1, 1)
            particula.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-1, 1)
            particula.vida = random.randint(5, 15)  # Vida curta para um efeito rápido
            particula.tamanho = random.uniform(1.5, 4)  # Partículas menores
            particula.gravidade = 0.03  # Gravidade reduzida
            
            # Adicionar à lista de partículas
            particulas.append(particula)
    
    # Adicionar um flash luminoso na ponta do cano
    if flashes is not None:
        flash = {
            'x': ponta_cano_x,
            'y': ponta_cano_y,
            'raio': 15,
            'vida': 5,
            'cor': (255, 255, 0)  # Amarelo puro, mesma cor das partículas
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
        tiros.append(Tiro(centro_x, centro_y, tiro_dx, tiro_dy, jogador.cor, 8))
    
    # Reduzir contador de tiros apenas se jogador for passado como parâmetro
    if hasattr(jogador, 'tiros_espingarda'):
        jogador.tiros_espingarda -= 1
        # Desativar espingarda se acabaram os tiros
        if jogador.tiros_espingarda <= 0:
            jogador.espingarda_ativa = False
            # Efeito visual será mostrado no arquivo fase.py

def desenhar_espingarda(tela, jogador, tempo_atual,pos_mouse):
    """
    Desenha a espingarda na posição do jogador, orientada para a direção do mouse.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
    """
    # Obter a posição do mouse para orientar a espingarda

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
    if hasattr(jogador, 'recuo_espingarda') and hasattr(jogador, 'tempo_recuo'):
        tempo_desde_tiro = tempo_atual - jogador.tempo_recuo
        if tempo_desde_tiro < 200:  # Duração do efeito de recuo em ms
            # Recuo diminui ao longo do tempo
            intensidade = jogador.recuo_espingarda * (1 - tempo_desde_tiro / 200)
            # Recuar na direção oposta ao tiro (para trás)
            offset_recuo_x = -dx * intensidade
            offset_recuo_y = -dy * intensidade
            # Adicionar pequena tremida aleatória
            offset_recuo_x += random.uniform(-2, 2) * (intensidade / 10)
            offset_recuo_y += random.uniform(-2, 2) * (intensidade / 10)

    # Aplicar offset de recuo ao centro
    centro_x += offset_recuo_x
    centro_y += offset_recuo_y

    # Comprimento da espingarda
    comprimento_arma = 40  # Espingarda mais longa

    # Posição da ponta da arma
    ponta_x = centro_x + dx * comprimento_arma
    ponta_y = centro_y + dy * comprimento_arma

    # Vetor perpendicular para elementos laterais
    perp_x = -dy
    perp_y = dx
    
    # Cores da espingarda
    cor_metal = (60, 60, 70)  # Metal escuro
    cor_metal_claro = (120, 120, 130)  # Metal mais claro para detalhes
    cor_cano = (40, 40, 45)   # Cano bem escuro
    cor_madeira = (101, 67, 33)  # Madeira marrom escura
    cor_madeira_clara = (139, 90, 43)  # Madeira com destaque

    # DESENHO COMPLETO DA ESPINGARDA DE CANO DUPLO

    # === CORONHA (parte traseira de madeira) ===
    coronha_inicio_x = centro_x - dx * 18
    coronha_inicio_y = centro_y - dy * 18

    # Polígono da coronha (formato mais largo atrás)
    coronha_pontos = [
        (coronha_inicio_x + perp_x * 7, coronha_inicio_y + perp_y * 7),
        (coronha_inicio_x - perp_x * 7, coronha_inicio_y - perp_y * 7),
        (centro_x - dx * 5 - perp_x * 5, centro_y - dy * 5 - perp_y * 5),
        (centro_x - dx * 5 + perp_x * 5, centro_y - dy * 5 + perp_y * 5)
    ]
    pygame.draw.polygon(tela, cor_madeira, coronha_pontos)
    pygame.draw.polygon(tela, cor_madeira_clara, coronha_pontos, 2)

    # Detalhes da madeira (linhas)
    for i in range(3):
        offset_dist = -18 + i * 5
        det_x1 = centro_x - dx * offset_dist + perp_x * 6
        det_y1 = centro_y - dy * offset_dist + perp_y * 6
        det_x2 = centro_x - dx * offset_dist - perp_x * 6
        det_y2 = centro_y - dy * offset_dist - perp_y * 6
        pygame.draw.line(tela, cor_madeira_clara, (det_x1, det_y1), (det_x2, det_y2), 1)

    # === CORPO/MECANISMO DA ESPINGARDA ===
    corpo_x = centro_x + dx * 5
    corpo_y = centro_y + dy * 5

    # Corpo principal (retangular)
    corpo_pontos = [
        (centro_x - dx * 5 + perp_x * 6, centro_y - dy * 5 + perp_y * 6),
        (centro_x - dx * 5 - perp_x * 6, centro_y - dy * 5 - perp_y * 6),
        (corpo_x - perp_x * 5, corpo_y - perp_y * 5),
        (corpo_x + perp_x * 5, corpo_y + perp_y * 5)
    ]
    pygame.draw.polygon(tela, cor_metal, corpo_pontos)
    pygame.draw.polygon(tela, cor_metal_claro, corpo_pontos, 1)

    # === GATILHO ===
    gatilho_base_x = centro_x - dx * 2
    gatilho_base_y = centro_y - dy * 2
    gatilho_ponta_x = gatilho_base_x - perp_x * 4
    gatilho_ponta_y = gatilho_base_y - perp_y * 4

    # Proteção do gatilho
    pygame.draw.line(tela, cor_metal_claro,
                    (gatilho_base_x - dx * 4, gatilho_base_y - dy * 4),
                    (gatilho_ponta_x - dx * 3, gatilho_ponta_y - dy * 3), 2)
    pygame.draw.line(tela, cor_metal_claro,
                    (gatilho_ponta_x - dx * 3, gatilho_ponta_y - dy * 3),
                    (gatilho_ponta_x, gatilho_ponta_y), 2)

    # Gatilho
    pygame.draw.line(tela, (200, 150, 0),
                    (gatilho_base_x, gatilho_base_y),
                    (gatilho_ponta_x - dx * 1, gatilho_ponta_y - dy * 1), 3)

    # === CANO DUPLO (característica principal da espingarda) ===
    separacao_canos = 3.5  # Distância entre os dois canos

    # Início dos canos (na parte do corpo)
    inicio_cano_x = corpo_x
    inicio_cano_y = corpo_y

    # CANO SUPERIOR
    inicio_sup_x = inicio_cano_x + perp_x * separacao_canos
    inicio_sup_y = inicio_cano_y + perp_y * separacao_canos
    ponta_sup_x = ponta_x + perp_x * separacao_canos
    ponta_sup_y = ponta_y + perp_y * separacao_canos

    # Desenhar cano superior (grosso)
    pygame.draw.line(tela, cor_cano,
                    (inicio_sup_x, inicio_sup_y),
                    (ponta_sup_x, ponta_sup_y), 5)
    # Contorno do cano superior
    pygame.draw.line(tela, cor_metal_claro,
                    (inicio_sup_x + perp_x * 2.5, inicio_sup_y + perp_y * 2.5),
                    (ponta_sup_x + perp_x * 2.5, ponta_sup_y + perp_y * 2.5), 1)
    pygame.draw.line(tela, cor_metal_claro,
                    (inicio_sup_x - perp_x * 2.5, inicio_sup_y - perp_y * 2.5),
                    (ponta_sup_x - perp_x * 2.5, ponta_sup_y - perp_y * 2.5), 1)

    # CANO INFERIOR
    inicio_inf_x = inicio_cano_x - perp_x * separacao_canos
    inicio_inf_y = inicio_cano_y - perp_y * separacao_canos
    ponta_inf_x = ponta_x - perp_x * separacao_canos
    ponta_inf_y = ponta_y - perp_y * separacao_canos

    # Desenhar cano inferior (grosso)
    pygame.draw.line(tela, cor_cano,
                    (inicio_inf_x, inicio_inf_y),
                    (ponta_inf_x, ponta_inf_y), 5)
    # Contorno do cano inferior
    pygame.draw.line(tela, cor_metal_claro,
                    (inicio_inf_x + perp_x * 2.5, inicio_inf_y + perp_y * 2.5),
                    (ponta_inf_x + perp_x * 2.5, ponta_inf_y + perp_y * 2.5), 1)
    pygame.draw.line(tela, cor_metal_claro,
                    (inicio_inf_x - perp_x * 2.5, inicio_inf_y - perp_y * 2.5),
                    (ponta_inf_x - perp_x * 2.5, ponta_inf_y - perp_y * 2.5), 1)

    # === BOCAS DOS CANOS ===
    # Boca do cano superior
    pygame.draw.circle(tela, cor_metal, (int(ponta_sup_x), int(ponta_sup_y)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_sup_x), int(ponta_sup_y)), 2)

    # Boca do cano inferior
    pygame.draw.circle(tela, cor_metal, (int(ponta_inf_x), int(ponta_inf_y)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_inf_x), int(ponta_inf_y)), 2)

    # === SUPORTE ENTRE OS CANOS (banda que une os dois canos) ===
    # Meio do cano
    meio_x = centro_x + dx * (comprimento_arma * 0.5)
    meio_y = centro_y + dy * (comprimento_arma * 0.5)
    pygame.draw.line(tela, cor_metal_claro,
                    (meio_x + perp_x * (separacao_canos + 2), meio_y + perp_y * (separacao_canos + 2)),
                    (meio_x - perp_x * (separacao_canos + 2), meio_y - perp_y * (separacao_canos + 2)), 3)

    # Perto da ponta
    frente_x = centro_x + dx * (comprimento_arma * 0.85)
    frente_y = centro_y + dy * (comprimento_arma * 0.85)
    pygame.draw.line(tela, cor_metal_claro,
                    (frente_x + perp_x * (separacao_canos + 2), frente_y + perp_y * (separacao_canos + 2)),
                    (frente_x - perp_x * (separacao_canos + 2), frente_y - perp_y * (separacao_canos + 2)), 2)

    # === EFEITO DE ENERGIA (quando ativa) ===
    pulso = (math.sin(tempo_atual / 150) + 1) / 2
    cor_energia = (255, int(100 + pulso * 155), 0)  # Laranja pulsante
    energia_width = 1 + int(pulso * 2)

    # Linha de energia no cano superior
    pygame.draw.line(tela, cor_energia,
                    (corpo_x + perp_x * separacao_canos, corpo_y + perp_y * separacao_canos),
                    (ponta_sup_x, ponta_sup_y), energia_width)

    # Linha de energia no cano inferior
    pygame.draw.line(tela, cor_energia,
                    (corpo_x - perp_x * separacao_canos, corpo_y - perp_y * separacao_canos),
                    (ponta_inf_x, ponta_inf_y), energia_width)