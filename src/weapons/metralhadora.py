#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar todas as funcionalidades relacionadas à metralhadora.
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

def carregar_upgrade_metralhadora():
    """
    Carrega o upgrade de metralhadora do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        # Verificar se o arquivo existe
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("metralhadora", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de metralhadora: {e}")
        return 0

def salvar_municao_metralhadora(quantidade):
    """
    Salva a quantidade atual de munição de metralhadora.

    Args:
        quantidade: Quantidade atual de munição
    """
    try:
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
        upgrades["metralhadora"] = max(0, quantidade)
        os.makedirs("data", exist_ok=True)
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar munição de metralhadora: {e}")

def atirar_metralhadora(jogador, tiros, pos_mouse, particulas=None, flashes=None):
    """
    Dispara um único tiro de metralhadora com alta cadência de tiro.
    
    Args:
        jogador: O objeto do jogador
        tiros: Lista onde adicionar o novo tiro
        pos_mouse: Tupla (x, y) com a posição do mouse
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
    """
    cooldown_metralhadora = 200
    
    # Verificar cooldown
    tempo_atual = pygame.time.get_ticks()
    if tempo_atual - jogador.tempo_ultimo_tiro < cooldown_metralhadora:
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
    
    # Adicionar ligeira imprecisão para simular recuo da metralhadora
    imprecisao = 0.08  # Pequena variação na direção
    dx += random.uniform(-imprecisao, imprecisao)
    dy += random.uniform(-imprecisao, imprecisao)
    
    # Normalizar novamente após adicionar imprecisão
    distancia_nova = math.sqrt(dx * dx + dy * dy)
    if distancia_nova > 0:
        dx /= distancia_nova
        dy /= distancia_nova
    
    # Som de tiro de metralhadora (mais seco e rápido)
    som_metralhadora = pygame.mixer.Sound(gerar_som_tiro())
    som_metralhadora.set_volume(0.15)  # Volume mais baixo devido à alta frequência
    pygame.mixer.Channel(3).play(som_metralhadora)  # Canal dedicado para metralhadora
    
    # Calcular a posição da ponta do cano para efeitos
    comprimento_arma = 40
    ponta_cano_x = centro_x + dx * comprimento_arma
    ponta_cano_y = centro_y + dy * comprimento_arma
    
    # Criar efeito de partículas mais intenso na ponta do cano
    if particulas is not None:
        # Cor vermelha/laranja para a metralhadora
        cor_metralhadora = (255, 150, 50)  # Laranja quente
        
        # Criar partículas de disparo (menos que a espingarda, mas mais frequentes)
        for _ in range(8):
            cor = cor_metralhadora
            
            # Posição com variação ao redor da ponta do cano
            vari_x = random.uniform(-3, 3)
            vari_y = random.uniform(-3, 3)
            pos_x = ponta_cano_x + vari_x
            pos_y = ponta_cano_y + vari_y
            
            # Criar partícula
            particula = Particula(pos_x, pos_y, cor)
            
            # Configurar propriedades para efeito rápido
            particula.velocidade_x = dx * random.uniform(3, 7) + random.uniform(-0.5, 0.5)
            particula.velocidade_y = dy * random.uniform(3, 7) + random.uniform(-0.5, 0.5)
            particula.vida = random.randint(3, 8)  # Vida muito curta
            particula.tamanho = random.uniform(1, 3)  # Partículas pequenas
            particula.gravidade = 0.02
            
            particulas.append(particula)
        
        # Adicionar partículas de casquinha sendo ejetada
        for _ in range(2):
            # Posição ligeiramente atrás da ponta do cano
            casquinha_x = centro_x + dx * (comprimento_arma * 0.7)
            casquinha_y = centro_y + dy * (comprimento_arma * 0.7)
            
            # Cor dourada para casquinhas
            cor_casquinha = (255, 215, 0)
            particula_casquinha = Particula(casquinha_x, casquinha_y, cor_casquinha)
            
            # Ejetar para o lado e para trás
            perp_x = -dy  # Vetor perpendicular
            perp_y = dx
            particula_casquinha.velocidade_x = (perp_x + dx * -0.3) * random.uniform(1, 3)
            particula_casquinha.velocidade_y = (perp_y + dy * -0.3) * random.uniform(1, 3)
            particula_casquinha.vida = random.randint(15, 30)
            particula_casquinha.tamanho = random.uniform(0.8, 1.5)
            particula_casquinha.gravidade = 0.1
            
            particulas.append(particula_casquinha)
    
    # Flash menor mas mais frequente
    if flashes is not None:
        flash = {
            'x': ponta_cano_x,
            'y': ponta_cano_y,
            'raio': 8,  # Menor que a espingarda
            'vida': 3,  # Muito rápido
            'cor': (255, 200, 100)  # Laranja claro
        }
        flashes.append(flash)
    
    # Criar tiro com velocidade ligeiramente maior (usar a cor do jogador)
    tiros.append(Tiro(centro_x, centro_y, dx, dy, jogador.cor, 15))  # Velocidade 12 (mais rápido que normal)
    
    # Reduzir contador de munição
    if hasattr(jogador, 'tiros_metralhadora'):
        jogador.tiros_metralhadora -= 1
        # Desativar metralhadora se acabaram os tiros
        if jogador.tiros_metralhadora <= 0:
            jogador.metralhadora_ativa = False

def desenhar_metralhadora(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha a metralhadora na posição do jogador, orientada para a direção do mouse.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
        pos_mouse: Posição do mouse para orientação
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
    
    # Comprimento da metralhadora
    comprimento_arma = 40
    
    # Simulação de recuo - a arma "treme" quando está ativa
    recuo_x = 0
    recuo_y = 0
    if hasattr(jogador, 'metralhadora_ativa') and jogador.metralhadora_ativa:
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
    
    # Cores da metralhadora
    cor_metal_escuro = (60, 60, 70)    # Metal escuro principal
    cor_metal_claro = (120, 120, 130)  # Metal claro para detalhes
    cor_cano = (40, 40, 45)            # Cano muito escuro
    cor_laranja = (255, 140, 0)        # Detalhes laranja
    cor_vermelho = (200, 50, 50)       # Detalhes vermelhos
    
    # DESENHO DA METRALHADORA
    
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
    
    # 7. Detalhes tátiles
    # Trilho superior
    trilho_inicio_x = corpo_x + dx * 5
    trilho_inicio_y = corpo_y + dy * 5
    trilho_fim_x = ponta_x - dx * 8
    trilho_fim_y = ponta_y - dy * 8
    pygame.draw.line(tela, cor_metal_claro,
                    (trilho_inicio_x + perp_x * 2, trilho_inicio_y + perp_y * 2),
                    (trilho_fim_x + perp_x * 2, trilho_fim_y + perp_y * 2), 2)
    
    # 8. Indicador de munição
    if hasattr(jogador, 'tiros_metralhadora') and jogador.tiros_metralhadora > 0:
        # Barras indicativas de munição
        for i in range(min(5, jogador.tiros_metralhadora // 20)):  # Cada barra = 20 tiros
            barra_x = carregador_x - 2 + i
            barra_y = carregador_y + 10 + i * 2
            pygame.draw.rect(tela, cor_laranja, (barra_x, barra_y, 1, 3))
    
    # 9. Efeito de aquecimento (quando ativa)
    if hasattr(jogador, 'metralhadora_ativa') and jogador.metralhadora_ativa:
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
    
    # 10. Mira laser (linha pontilhada)
    if hasattr(jogador, 'metralhadora_ativa') and jogador.metralhadora_ativa:
        # Linha laser vermelha pontilhada até o mouse
        passos = int(distancia // 10)
        for i in range(0, passos, 2):  # Pular de 2 em 2 para efeito pontilhado
            laser_x = ponta_x + dx * (i * 10)
            laser_y = ponta_y + dy * (i * 10)
            pygame.draw.circle(tela, cor_vermelho, (int(laser_x), int(laser_y)), 1)