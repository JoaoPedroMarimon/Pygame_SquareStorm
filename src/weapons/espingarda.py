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
        
        # Criar tiro com a direção calculada
        tiros.append(Tiro(centro_x, centro_y, tiro_dx, tiro_dy, AZUL, 8))
    
    # Reduzir contador de tiros apenas se jogador for passado como parâmetro
    if hasattr(jogador, 'tiros_espingarda'):
        jogador.tiros_espingarda -= 1
        # Desativar espingarda se acabaram os tiros
        if jogador.tiros_espingarda <= 0:
            jogador.espingarda_ativa = False
            # Efeito visual será mostrado no arquivo fase.py

def desenhar_espingarda(tela, jogador, tempo_atual):
    """
    Desenha a espingarda na posição do jogador, orientada para a direção do mouse.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
    """
    # Obter a posição do mouse para orientar a espingarda
    pos_mouse = pygame.mouse.get_pos()
    
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
    
    # Comprimento da espingarda
    comprimento_arma = 35  # Ligeiramente mais longo
    
    # Posição da ponta da arma
    ponta_x = centro_x + dx * comprimento_arma
    ponta_y = centro_y + dy * comprimento_arma
    
    # Vetor perpendicular para elementos laterais
    perp_x = -dy
    perp_y = dx
    
    # Cores da espingarda
    cor_metal = (180, 180, 190)  # Metal prateado
    cor_cano = (100, 100, 110)   # Cano escuro
    cor_madeira = (120, 80, 40)  # Madeira escura
    cor_madeira_clara = (150, 100, 50)  # Madeira clara
    
    # DESENHO COMPLETO DA ESPINGARDA
    
    # 1. Cano principal (mais grosso e com gradiente)
    for i in range(4):
        offset = i - 1.5
        pygame.draw.line(tela, cor_cano, 
                    (centro_x + perp_x * offset, centro_y + perp_y * offset), 
                    (ponta_x + perp_x * offset, ponta_y + perp_y * offset), 3)
    
    # 2. Boca do cano com destaque
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 5)
    pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 3)
    
    # 3. Suporte sob o cano
    meio_cano_x = centro_x + dx * (comprimento_arma * 0.6)
    meio_cano_y = centro_y + dy * (comprimento_arma * 0.6)
    pygame.draw.line(tela, cor_metal, 
                    (meio_cano_x + perp_x * 3, meio_cano_y + perp_y * 3), 
                    (meio_cano_x - perp_x * 3, meio_cano_y - perp_y * 3), 3)
    
    # 4. Corpo central / Mecanismo (mais detalhado)
    corpo_x = centro_x + dx * 8
    corpo_y = centro_y + dy * 8
    # Base do corpo
    pygame.draw.circle(tela, cor_metal, (int(corpo_x), int(corpo_y)), 7)
    # Detalhes do mecanismo
    pygame.draw.circle(tela, (50, 50, 55), (int(corpo_x), int(corpo_y)), 4)
    # Reflete mecanismo (brilho)
    brilho_x = corpo_x - dx + perp_x
    brilho_y = corpo_y - dy + perp_y
    pygame.draw.circle(tela, (220, 220, 230), (int(brilho_x), int(brilho_y)), 2)
    
    # 5. Coronha mais elegante (formato mais curvado)
    # Pontos para a coronha em formato mais curvo
    # Base conectando ao corpo
    coronha_base_x = corpo_x - dx * 2
    coronha_base_y = corpo_y - dy * 2
    
    # Pontos superiores e inferiores no início da coronha
    sup_inicio_x = coronha_base_x + perp_x * 6
    sup_inicio_y = coronha_base_y + perp_y * 6
    inf_inicio_x = coronha_base_x - perp_x * 6
    inf_inicio_y = coronha_base_y - perp_y * 6
    
    # Pontos do final da coronha (mais estreitos)
    sup_fim_x = coronha_base_x - dx * 15 + perp_x * 4
    sup_fim_y = coronha_base_y - dy * 15 + perp_y * 4
    inf_fim_x = coronha_base_x - dx * 15 - perp_x * 4
    inf_fim_y = coronha_base_y - dy * 15 - perp_y * 4
    
    # Desenhar coronha principal
    pygame.draw.polygon(tela, cor_madeira, [
        (sup_inicio_x, sup_inicio_y),
        (inf_inicio_x, inf_inicio_y),
        (inf_fim_x, inf_fim_y),
        (sup_fim_x, sup_fim_y)
    ])
    
    # 6. Detalhes da coronha (linhas de madeira)
    for i in range(1, 4):
        linha_x1 = sup_inicio_x - dx * (i * 3) + perp_x * (6 - i * 0.5)
        linha_y1 = sup_inicio_y - dy * (i * 3) + perp_y * (6 - i * 0.5)
        linha_x2 = inf_inicio_x - dx * (i * 3) - perp_x * (6 - i * 0.5)
        linha_y2 = inf_inicio_y - dy * (i * 3) - perp_y * (6 - i * 0.5)
        pygame.draw.line(tela, cor_madeira_clara, 
                        (linha_x1, linha_y1), 
                        (linha_x2, linha_y2), 1)
    
    # 7. Gatilho e proteção (mais detalhados)
    # Base do gatilho
    gatilho_base_x = corpo_x - dx * 3
    gatilho_base_y = corpo_y - dy * 3
    
    # Proteção do gatilho (arco)
    pygame.draw.arc(tela, cor_metal, 
                [gatilho_base_x - 5, gatilho_base_y - 5, 10, 10],
                math.pi/2, math.pi * 1.5, 2)
    
    # Gatilho (linha curva)
    gatilho_x = gatilho_base_x - perp_x * 2
    gatilho_y = gatilho_base_y - perp_y * 2
    pygame.draw.line(tela, (40, 40, 40), 
                    (gatilho_base_x, gatilho_base_y), 
                    (gatilho_x, gatilho_y), 2)
    
    # 8. Efeito de brilho no metal
    pygame.draw.line(tela, (220, 220, 230), 
                    (centro_x + perp_x * 2, centro_y + perp_y * 2), 
                    (corpo_x + perp_x * 2, corpo_y + perp_y * 2), 1)
    
    # 9. Efeito de energia/carregamento (quando estiver ativa)
    # Pulsar baseado no tempo atual
    pulso = (math.sin(tempo_atual / 150) + 1) / 2  # Valor entre 0 e 1
    cor_energia = (50 + int(pulso * 200), 50 + int(pulso * 150), 255)
    
    # Linha de energia ao longo do cano
    energia_width = 2 + int(pulso * 2)
    meio_cano2_x = centro_x + dx * (comprimento_arma * 0.3)
    meio_cano2_y = centro_y + dy * (comprimento_arma * 0.3)
    pygame.draw.line(tela, cor_energia, 
                    (meio_cano2_x, meio_cano2_y), 
                    (ponta_x, ponta_y), energia_width)