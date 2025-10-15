#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a Ampulheta - Item que desacelera o tempo.
Sistema visual similar à granada: segura na mão e ativa com clique do mouse.
"""

import pygame
import math
import random
import os
import json
from src.config import *
from src.entities.particula import criar_explosao
from src.utils.visual import criar_texto_flutuante
from src.utils.display_manager import convert_mouse_position

def carregar_upgrade_ampulheta():
    """
    Carrega o upgrade da ampulheta do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("ampulheta", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de ampulheta: {e}")
        return 0

def criar_som_ampulheta():
    """Cria um som místico para a ativação da ampulheta."""
    duracao = 0.5
    sample_rate = 22050
    frames = int(duracao * sample_rate)
    
    som_data = []
    for i in range(frames):
        t = i / sample_rate
        freq_base = 523  # C5
        
        amplitude = (
            0.3 * math.sin(2 * math.pi * freq_base * t) +
            0.2 * math.sin(2 * math.pi * freq_base * 1.5 * t) +
            0.1 * math.sin(2 * math.pi * freq_base * 2 * t)
        ) * math.exp(-t * 2)
        
        som_data.append(int(amplitude * 32767))
    
    som_bytes = bytearray()
    for sample in som_data:
        som_bytes.extend(sample.to_bytes(2, byteorder='little', signed=True))
    
    return pygame.mixer.Sound(bytes(som_bytes))

def usar_ampulheta(jogador, particulas=None, flashes=None):
    """
    Ativa a ampulheta para desacelerar o tempo.
    
    Args:
        jogador: O objeto do jogador
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
    
    Returns:
        True se foi ativada com sucesso, False caso contrário
    """
    # Verificar se o jogador tem ampulhetas disponíveis
    if not hasattr(jogador, 'ampulheta_uses') or jogador.ampulheta_uses <= 0:
        return False
    
    # Verificar se já tem uma ampulheta ativa
    if hasattr(jogador, 'tempo_desacelerado') and jogador.tempo_desacelerado:
        return False
    
    # Reduzir o contador de ampulhetas
    jogador.ampulheta_uses -= 1
    
    # Ativar desaceleração do tempo
    jogador.tempo_desacelerado = True
    jogador.duracao_desaceleracao = jogador.duracao_ampulheta
    
    # Posição central do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2
    
    # Criar som de ativação
    som_ampulheta = criar_som_ampulheta()
    pygame.mixer.Channel(5).play(som_ampulheta)
    
    # Criar efeitos visuais de ativação
    if particulas is not None and flashes is not None:
        from src.entities.particula import Particula
        
        # Criar ondas de energia temporal
        for i in range(5):
            flash_onda = {
                'x': centro_x,
                'y': centro_y,
                'raio': 40 + i * 30,
                'vida': 20 - i * 2,
                'cor': (150, 200, 255)
            }
            flashes.append(flash_onda)
        
        # Criar partículas místicas azuladas
        for _ in range(30):
            cor = random.choice([(150, 200, 255), (100, 150, 255), (200, 220, 255)])
            particula = Particula(centro_x, centro_y, cor)
            
            # Direção aleatória
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(2, 6)
            
            particula.velocidade_x = math.cos(angulo) * velocidade
            particula.velocidade_y = math.sin(angulo) * velocidade
            particula.vida = random.randint(30, 60)
            particula.tamanho = random.uniform(3, 7)
            particula.gravidade = -0.05  # Partículas flutuam para cima
            
            particulas.append(particula)
        
        # Flash central brilhante
        flash_central = {
            'x': centro_x,
            'y': centro_y,
            'raio': 80,
            'vida': 15,
            'cor': (200, 230, 255)
        }
        flashes.append(flash_central)
    
    # Desativar modo de ampulheta selecionada após usar
    if jogador.ampulheta_uses <= 0:
        jogador.ampulheta_selecionada = False
    
    print(f"⏰ Ampulheta ativada! Usos restantes: {jogador.ampulheta_uses}")
    return True

def desenhar_ampulheta_selecionada(tela, jogador, tempo_atual):
    """
    Desenha a ampulheta na mão do jogador quando selecionada.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
    """
    # Obter a posição do mouse para orientar a direção
    pos_mouse = convert_mouse_position(pygame.mouse.get_pos())
    
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
    
    # Distância do jogador onde a ampulheta será desenhada
    distancia_desenho = 30
    
    # Posição da ampulheta
    amp_x = centro_x + dx * distancia_desenho
    amp_y = centro_y + dy * distancia_desenho
    
    # Cores da ampulheta
    cor_madeira = (139, 90, 43)
    cor_vidro = (200, 230, 255, 180)
    cor_areia = (255, 223, 186)
    
    # Tamanhos
    largura_total = 16
    altura_total = 24
    altura_topo = 6
    altura_meio = 12
    
    # Criar superfície para a ampulheta com alpha
    amp_surface = pygame.Surface((largura_total * 2, altura_total * 2), pygame.SRCALPHA)
    centro_surf = (largura_total, altura_total)
    
    # Desenhar moldura superior (madeira)
    pygame.draw.rect(amp_surface, cor_madeira, 
                     (centro_surf[0] - largura_total//2, centro_surf[1] - altura_total//2, 
                      largura_total, altura_topo), 0, 2)
    
    # Desenhar moldura inferior (madeira)
    pygame.draw.rect(amp_surface, cor_madeira, 
                     (centro_surf[0] - largura_total//2, 
                      centro_surf[1] + altura_total//2 - altura_topo, 
                      largura_total, altura_topo), 0, 2)
    
    # Desenhar vidro (parte superior - triângulo invertido)
    pontos_superior = [
        (centro_surf[0] - largura_total//2 + 2, centro_surf[1] - altura_total//2 + altura_topo),
        (centro_surf[0] + largura_total//2 - 2, centro_surf[1] - altura_total//2 + altura_topo),
        (centro_surf[0], centro_surf[1])
    ]
    pygame.draw.polygon(amp_surface, cor_vidro, pontos_superior)
    pygame.draw.polygon(amp_surface, (100, 150, 200), pontos_superior, 2)
    
    # Desenhar vidro (parte inferior - triângulo)
    pontos_inferior = [
        (centro_surf[0] - largura_total//2 + 2, 
         centro_surf[1] + altura_total//2 - altura_topo),
        (centro_surf[0] + largura_total//2 - 2, 
         centro_surf[1] + altura_total//2 - altura_topo),
        (centro_surf[0], centro_surf[1])
    ]
    pygame.draw.polygon(amp_surface, cor_vidro, pontos_inferior)
    pygame.draw.polygon(amp_surface, (100, 150, 200), pontos_inferior, 2)
    
    # Desenhar areia (animação de queda)
    # Areia superior (diminui com o tempo)
    tempo_ciclo = (tempo_atual % 2000) / 2000.0  # Ciclo de 2 segundos
    altura_areia_superior = int((1 - tempo_ciclo) * (altura_meio - 4))
    
    if altura_areia_superior > 0:
        # Areia na parte superior
        for y_offset in range(altura_areia_superior):
            largura_areia = int((largura_total - 4) * (1 - y_offset / altura_meio))
            if largura_areia > 2:
                pygame.draw.line(amp_surface, cor_areia,
                               (centro_surf[0] - largura_areia//2, 
                                centro_surf[1] - altura_meio//2 + y_offset),
                               (centro_surf[0] + largura_areia//2, 
                                centro_surf[1] - altura_meio//2 + y_offset), 1)
    
    # Areia inferior (aumenta com o tempo)
    altura_areia_inferior = int(tempo_ciclo * (altura_meio - 4))
    
    if altura_areia_inferior > 0:
        # Areia na parte inferior
        for y_offset in range(altura_areia_inferior):
            largura_areia = int((largura_total - 4) * (y_offset / altura_meio))
            if largura_areia > 2:
                pygame.draw.line(amp_surface, cor_areia,
                               (centro_surf[0] - largura_areia//2, 
                                centro_surf[1] + altura_meio//2 - y_offset),
                               (centro_surf[0] + largura_areia//2, 
                                centro_surf[1] + altura_meio//2 - y_offset), 1)
    
    # Desenhar ponto de passagem da areia (centro)
    pygame.draw.circle(amp_surface, cor_areia, centro_surf, 2)
    
    # Calcular posição final na tela
    rect = amp_surface.get_rect(center=(int(amp_x), int(amp_y)))
    
    # Desenhar na tela
    tela.blit(amp_surface, rect)
    
    # Efeito de pulso para indicar que está pronta para uso
    if (tempo_atual // 400) % 2 == 0:  # Piscar a cada 0.4 segundos
        # Brilho azulado ao redor da ampulheta
        pygame.draw.circle(tela, (150, 200, 255, 128), 
                          (int(amp_x), int(amp_y)), 
                          20, 2)
    
    # Desenhar contador de ampulhetas perto do jogador
    fonte = pygame.font.SysFont("Arial", 20, True)
    texto_amp = fonte.render(f"{jogador.ampulheta_uses}", True, (150, 200, 255))
    texto_rect = texto_amp.get_rect(center=(jogador.x + jogador.tamanho + 15, jogador.y - 10))
    tela.blit(texto_amp, texto_rect)

def desenhar_efeito_tempo_desacelerado(tela, ativo, tempo_atual):
    """
    Desenha efeitos visuais quando o tempo está desacelerado.
    
    Args:
        tela: Superfície onde desenhar
        ativo: Se o efeito deve ser desenhado
        tempo_atual: Tempo atual para animações
    """
    if ativo:
        # Criar overlay azulado sutil
        overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
        overlay.fill((100, 150, 255, 30))  # Azul transparente
        tela.blit(overlay, (0, 0))
        
        # Efeito de ondas temporais nas bordas
        for i in range(3):
            alpha = int(50 * math.sin(tempo_atual / 200 + i * 2))
            if alpha > 0:
                pygame.draw.rect(tela, (150, 200, 255, alpha), 
                               (0, i * 10, LARGURA, 3), 0)
                pygame.draw.rect(tela, (150, 200, 255, alpha), 
                               (0, ALTURA_JOGO - (i + 1) * 10, LARGURA, 3), 0)