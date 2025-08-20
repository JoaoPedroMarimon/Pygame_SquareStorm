#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para o sistema do amuleto da Combat Knife.
O amuleto é ativado quando o jogador pressiona Q com a Combat Knife equipada.
Agora inclui sistema de invocação do Chucky através de clique do mouse.
"""

import pygame
import math
import os
import json
from src.config import *
from src.items.chucky_invocation import criar_invocacao_chucky

def desenhar_amuleto_segurado(tela, jogador, tempo_atual):
    """
    Desenha o jogador segurando um amuleto místico quando a Combat Knife está equipada.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual para animações
    """
    # Posição do amuleto relativa ao jogador (na frente dele)
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2
    
    # Posição do amuleto (ligeiramente à frente do jogador)
    amuleto_x = centro_x + 25
    amuleto_y = centro_y - 5
    
    # Animação de flutuação suave
    flutuacao = math.sin(tempo_atual / 300) * 3
    amuleto_y += flutuacao
    
    # Cores do amuleto
    cor_base = (100, 50, 150)  # Roxo escuro
    cor_brilho = (200, 150, 255)  # Roxo brilhante
    cor_centro = (255, 200, 100)  # Dourado
    
    # Intensidade do brilho baseada no tempo
    intensidade_brilho = (math.sin(tempo_atual / 200) + 1) / 2
    
    # Desenhar aura do amuleto
    raio_aura = 12 + int(intensidade_brilho * 6)
    
    # Criar superfície para a aura com transparência
    aura_surface = pygame.Surface((raio_aura * 2, raio_aura * 2), pygame.SRCALPHA)
    pygame.draw.circle(aura_surface, (*cor_brilho, int(40 * intensidade_brilho)), 
                      (raio_aura, raio_aura), raio_aura)
    tela.blit(aura_surface, (amuleto_x - raio_aura, amuleto_y - raio_aura))
    
    # Corpo principal do amuleto (formato hexágono)
    pontos_hex = []
    raio_hex = 10
    for i in range(6):
        angulo = i * math.pi / 3 + tempo_atual / 1000  # Rotação lenta
        x = amuleto_x + math.cos(angulo) * raio_hex
        y = amuleto_y + math.sin(angulo) * raio_hex
        pontos_hex.append((x, y))
    
    # Desenhar hexágono principal
    pygame.draw.polygon(tela, cor_base, pontos_hex)
    pygame.draw.polygon(tela, cor_brilho, pontos_hex, 2)
    
    # Hexágono interno menor
    pontos_hex_interno = []
    raio_interno = 6
    for i in range(6):
        angulo = i * math.pi / 3 - tempo_atual / 800  # Rotação oposta
        x = amuleto_x + math.cos(angulo) * raio_interno
        y = amuleto_y + math.sin(angulo) * raio_interno
        pontos_hex_interno.append((x, y))
    
    pygame.draw.polygon(tela, (cor_base[0] + 30, cor_base[1] + 20, cor_base[2] + 50), pontos_hex_interno)
    
    # Centro do amuleto (círculo dourado pulsante)
    raio_centro = 4 + int(intensidade_brilho * 2)
    pygame.draw.circle(tela, cor_centro, (int(amuleto_x), int(amuleto_y)), raio_centro)
    pygame.draw.circle(tela, (255, 255, 200), (int(amuleto_x), int(amuleto_y)), raio_centro - 1)
    
    # Partículas místicas orbitando ao redor
    for i in range(4):
        particula_angulo = tempo_atual / 400 + i * (math.pi / 2)
        particula_raio = 18 + math.sin(tempo_atual / 300 + i) * 3
        particula_x = amuleto_x + math.cos(particula_angulo) * particula_raio
        particula_y = amuleto_y + math.sin(particula_angulo) * particula_raio
        
        tamanho_particula = 2 + int(math.sin(tempo_atual / 150 + i) * 1)
        cor_particula = (
            cor_brilho[0] + int(math.sin(tempo_atual / 100 + i) * 30),
            cor_brilho[1] + int(math.cos(tempo_atual / 120 + i) * 30),
            255
        )
        
        pygame.draw.circle(tela, cor_particula, (int(particula_x), int(particula_y)), tamanho_particula)
    
    # Cordão conectando o jogador ao amuleto
    pygame.draw.line(tela, (80, 60, 40), (centro_x + 8, centro_y - 5), (int(amuleto_x - 5), int(amuleto_y)), 3)
    pygame.draw.line(tela, (120, 90, 60), (centro_x + 8, centro_y - 5), (int(amuleto_x - 5), int(amuleto_y)), 1)
    
    # Efeito de energia saindo do amuleto (raios sutis)
    if intensidade_brilho > 0.8:
        for i in range(3):
            raio_angulo = tempo_atual / 200 + i * (2 * math.pi / 3)
            raio_x = amuleto_x + math.cos(raio_angulo) * 20
            raio_y = amuleto_y + math.sin(raio_angulo) * 20
            pygame.draw.line(tela, (cor_brilho[0], cor_brilho[1], cor_brilho[2], 100), 
                           (int(amuleto_x), int(amuleto_y)), (int(raio_x), int(raio_y)), 1)

def usar_amuleto_para_invocacao(pos_mouse, jogador):
    """
    Usa o amuleto para invocar o Chucky na posição do mouse.
    
    Args:
        pos_mouse: Posição do mouse onde invocar
        jogador: Objeto do jogador
        
    Returns:
        bool: True se a invocação foi bem-sucedida, False caso contrário
    """
    # Verificar se o jogador tem o amuleto ativo e facas disponíveis
    if (hasattr(jogador, 'amuleto_ativo') and jogador.amuleto_ativo and 
        hasattr(jogador, 'facas') and jogador.facas > 0):
        
        # Tentar criar invocação
        if criar_invocacao_chucky(pos_mouse):
            # Consumir uma faca/uso do amuleto
            jogador.facas -= 1
            
            # Se não há mais facas, desativar o amuleto
            if jogador.facas <= 0:
                jogador.amuleto_ativo = False
            
            return True
    
    return False


def carregar_upgrade_faca():
    """
    Carrega a quantidade de facas/amuletos do arquivo de upgrades.
    
    Returns:
        int: Quantidade de Combat Knives/amuletos disponíveis
    """
    try:
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("faca", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de faca: {e}")
        return 0

def desenhar_icone_amuleto_hud(tela, x, y, tempo_atual):
    """
    Desenha um ícone simplificado do amuleto para o HUD.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
    """
    # Cores místicas
    cor_base = (100, 50, 150)
    cor_brilho = (200, 150, 255)
    cor_centro = (255, 200, 100)
    
    # Animação de brilho
    intensidade = (math.sin(tempo_atual / 200) + 1) / 2
    
    # Desenhar hexágono pequeno
    pontos_hex = []
    raio = 8
    for i in range(6):
        angulo = i * math.pi / 3 + tempo_atual / 1000
        px = x + math.cos(angulo) * raio
        py = y + math.sin(angulo) * raio
        pontos_hex.append((px, py))
    
    pygame.draw.polygon(tela, cor_base, pontos_hex)
    pygame.draw.polygon(tela, cor_brilho, pontos_hex, 1)
    
    # Centro dourado
    pygame.draw.circle(tela, cor_centro, (int(x), int(y)), 4)
    pygame.draw.circle(tela, (255, 255, 200), (int(x), int(y)), 2)
    
    # Brilho pulsante
    if intensidade > 0.7:
        pygame.draw.circle(tela, cor_brilho, (int(x), int(y)), int(raio + 3), 1)
        
    # Partículas pequenas
    for i in range(2):
        part_angle = tempo_atual / 300 + i * math.pi
        part_x = x + math.cos(part_angle) * 12
        part_y = y + math.sin(part_angle) * 12
        pygame.draw.circle(tela, cor_brilho, (int(part_x), int(part_y)), 1)