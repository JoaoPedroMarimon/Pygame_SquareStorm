#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para a seção de armas da loja do jogo.
Com sistema de preços dinâmicos integrado e scroll funcional.
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import desenhar_texto
import json
import os

# Importar o sistema de pricing
from src.game.pricing_system import PricingManager, aplicar_pricing_sistema

def salvar_upgrades(upgrades):
    """
    Salva os upgrades no arquivo.
    """
    try:
        # Criar o diretório de dados se não existir
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Salvar os upgrades no arquivo
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f)
    except Exception as e:
        print(f"Erro ao salvar upgrades: {e}")

def desenhar_icone_espingarda(tela, x, y, tempo_atual):
    """
    Desenha um ícone de espingarda de CANO DUPLO com efeitos visuais.
    """
    # Cores da espingarda (cano duplo)
    cor_metal = (60, 60, 70)
    cor_metal_claro = (120, 120, 130)
    cor_cano = (40, 40, 45)
    cor_madeira = (101, 67, 33)

    # Comprimento da arma
    comprimento_arma = 30
    ponta_x = x + comprimento_arma

    # === CORONHA (parte traseira) ===
    coronha_x = x - 10
    pygame.draw.polygon(tela, cor_madeira, [
        (coronha_x, y - 4),
        (coronha_x, y + 4),
        (x, y + 3),
        (x, y - 3)
    ])
    pygame.draw.polygon(tela, (139, 90, 43), [
        (coronha_x, y - 4),
        (coronha_x, y + 4),
        (x, y + 3),
        (x, y - 3)
    ], 1)

    # === CORPO/MECANISMO ===
    corpo_x = x + 5
    pygame.draw.rect(tela, cor_metal, (x, y - 4, 10, 8))
    pygame.draw.rect(tela, cor_metal_claro, (x, y - 4, 10, 8), 1)

    # === CANO DUPLO (característica principal) ===
    separacao = 2.5  # Distância entre os dois canos

    # CANO SUPERIOR
    pygame.draw.line(tela, cor_cano,
                    (corpo_x, y - separacao),
                    (ponta_x, y - separacao), 4)
    pygame.draw.line(tela, cor_metal_claro,
                    (corpo_x, y - separacao - 1.5),
                    (ponta_x, y - separacao - 1.5), 1)

    # CANO INFERIOR
    pygame.draw.line(tela, cor_cano,
                    (corpo_x, y + separacao),
                    (ponta_x, y + separacao), 4)
    pygame.draw.line(tela, cor_metal_claro,
                    (corpo_x, y + separacao + 1.5),
                    (ponta_x, y + separacao + 1.5), 1)

    # === BOCAS DOS CANOS ===
    # Boca superior
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(y - separacao)), 3)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(y - separacao)), 1)

    # Boca inferior
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(y + separacao)), 3)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(y + separacao)), 1)

    # === BANDA QUE UNE OS CANOS ===
    meio_x = x + comprimento_arma * 0.6
    pygame.draw.line(tela, cor_metal_claro,
                    (meio_x, y - separacao - 2),
                    (meio_x, y + separacao + 2), 2)

    # === EFEITO DE ENERGIA LARANJA ===
    pulso = (math.sin(tempo_atual / 150) + 1) / 2
    cor_energia = (255, int(100 + pulso * 155), 0)
    energia_width = 1 + int(pulso)

    # Energia no cano superior
    pygame.draw.line(tela, cor_energia,
                    (corpo_x + 2, y - separacao),
                    (ponta_x, y - separacao), energia_width)

    # Energia no cano inferior
    pygame.draw.line(tela, cor_energia,
                    (corpo_x + 2, y + separacao),
                    (ponta_x, y + separacao), energia_width)

def desenhar_icone_metralhadora(tela, x, y, tempo_atual):
    """
    Desenha um ícone de metralhadora com efeitos visuais.
    """
    # Cores da metralhadora
    cor_metal_escuro = (60, 60, 70)
    cor_metal_claro = (120, 120, 130)
    cor_cano_metra = (40, 40, 45)
    cor_laranja = (255, 140, 0)

    # Desenhar metralhadora
    comprimento_metra = 35
    
    # Cano principal (mais grosso, múltiplas linhas)
    for i in range(6):
        offset = (i - 2.5) * 0.6
        espessura = 3 if abs(i - 2.5) < 1 else 2
        cor_linha = cor_cano_metra if abs(i - 2.5) < 1 else cor_metal_escuro
        pygame.draw.line(tela, cor_linha,
                    (x, y + offset),
                    (x + comprimento_metra, y + offset), espessura)

    # Boca do cano com supressor
    ponta_metra_x = x + comprimento_metra
    ponta_metra_y = y
    pygame.draw.circle(tela, cor_metal_escuro, (int(ponta_metra_x), int(ponta_metra_y)), 6)
    pygame.draw.circle(tela, cor_cano_metra, (int(ponta_metra_x), int(ponta_metra_y)), 3)

    # Corpo principal
    corpo_metra_x = x + 10
    corpo_metra_y = y
    corpo_rect = pygame.Rect(corpo_metra_x - 6, corpo_metra_y - 4, 12, 8)
    pygame.draw.rect(tela, cor_metal_escuro, corpo_rect)
    pygame.draw.rect(tela, cor_metal_claro, corpo_rect, 1)

    # Carregador
    carregador_x = corpo_metra_x - 2
    carregador_y = corpo_metra_y + 6
    carregador_rect = pygame.Rect(carregador_x - 3, carregador_y, 6, 12)
    pygame.draw.rect(tela, cor_metal_escuro, carregador_rect)
    pygame.draw.rect(tela, cor_laranja, carregador_rect, 1)

    # Coronha retrátil
    punho_x = x - 6
    punho_y = y
    pygame.draw.line(tela, cor_metal_claro, (corpo_metra_x, corpo_metra_y), (punho_x, punho_y + 8), 4)
    pygame.draw.line(tela, cor_metal_claro, (punho_x, punho_y), (punho_x - 10, punho_y), 3)

    # Efeito de aquecimento/energia
    calor_intensidade = (tempo_atual % 1000) / 1000.0
    cor_calor = (255, int(100 + calor_intensidade * 155), 0)
    
    # Linhas de calor saindo do cano
    for i in range(3):
        heat_x = ponta_metra_x - (5 + i * 3) + random.uniform(-1, 1)
        heat_y = ponta_metra_y + random.uniform(-1, 1)
        pygame.draw.circle(tela, cor_calor, (int(heat_x), int(heat_y)), 1)

    # Brilho no cano
    pygame.draw.line(tela, cor_laranja, (x, y), (ponta_metra_x, ponta_metra_y), 1)
    
    
def desenhar_icone_spas12(tela, x, y, tempo_atual):
    """
    Desenha um ícone de SPAS-12 - shotgun tática semi-automática italiana.
    Versão compacta para a loja com detalhes visuais modernos.
    """
    # Cores da SPAS-12 (design tático moderno)
    cor_metal_escuro = (45, 45, 50)      # Metal tático preto
    cor_metal_medio = (80, 80, 90)       # Metal médio
    cor_metal_claro = (120, 120, 130)    # Metal detalhes
    cor_cano = (35, 35, 40)              # Cano preto fosco
    cor_polimero = (60, 60, 65)          # Polímero preto
    cor_laranja_tatico = (255, 140, 0)   # Laranja tático

    # Comprimento da arma
    comprimento_arma = 32
    ponta_x = x + comprimento_arma

    # === CORONHA ===
    coronha_x = x - 12
    pygame.draw.polygon(tela, cor_polimero, [
        (coronha_x, y - 5),
        (coronha_x, y + 5),
        (x, y + 4),
        (x, y - 4)
    ])
    pygame.draw.polygon(tela, cor_metal_claro, [
        (coronha_x, y - 5),
        (coronha_x, y + 5),
        (x, y + 4),
        (x, y - 4)
    ], 1)

    # Detalhes da coronha
    pygame.draw.line(tela, cor_metal_claro, (coronha_x + 3, y - 4), (coronha_x + 3, y + 4), 1)

    # === CORPO/RECEIVER ===
    corpo_x = x + 6
    pygame.draw.rect(tela, cor_metal_escuro, (x, y - 5, 12, 10))
    pygame.draw.rect(tela, cor_metal_claro, (x, y - 5, 12, 10), 1)

    # Trilho Picatinny superior
    pygame.draw.line(tela, cor_metal_medio, (x + 2, y - 6), (corpo_x + 12, y - 6), 2)
    # Slots do trilho
    for i in range(3):
        slot_x = x + 4 + i * 4
        pygame.draw.circle(tela, cor_metal_escuro, (slot_x, y - 6), 1)

    # === GATILHO ===
    gatilho_x = x + 4
    gatilho_y = y + 6
    # Guarda-mato
    pygame.draw.ellipse(tela, cor_metal_medio, (gatilho_x - 3, gatilho_y - 3, 8, 6), 2)
    # Gatilho laranja
    pygame.draw.rect(tela, cor_laranja_tatico, (gatilho_x, gatilho_y - 1, 3, 3), 0, 1)

    # === CANO ÚNICO ===
    pygame.draw.line(tela, cor_cano, (corpo_x, y), (ponta_x, y), 6)
    # Contornos para profundidade
    pygame.draw.line(tela, cor_metal_claro, (corpo_x, y - 3), (ponta_x, y - 3), 1)
    pygame.draw.line(tela, cor_metal_escuro, (corpo_x, y + 3), (ponta_x, y + 3), 1)

    # === TUBO DE MAGAZINE EMBAIXO ===
    pygame.draw.line(tela, cor_metal_medio, (corpo_x - 2, y + 4), (ponta_x - 3, y + 4), 3)

    # === HANDGUARD (proteção de mão) ===
    handguard_inicio = corpo_x + 2
    handguard_fim = ponta_x - 8
    # Superior
    pygame.draw.line(tela, cor_polimero, (handguard_inicio, y - 4), (handguard_fim, y - 4), 2)
    # Inferior
    pygame.draw.line(tela, cor_polimero, (handguard_inicio, y + 4), (handguard_fim, y + 4), 2)

    # === BOCA DO CANO ===
    pygame.draw.circle(tela, cor_metal_medio, (int(ponta_x), int(y)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(y)), 2)
    # Ponta laranja de segurança
    pygame.draw.circle(tela, cor_laranja_tatico, (int(ponta_x), int(y)), 1)

    # === MIRA FRONTAL ===
    mira_x = ponta_x - 6
    pygame.draw.line(tela, cor_metal_claro, (mira_x, y - 5), (mira_x, y - 3), 2)
    # Ponto verde na mira
    pygame.draw.circle(tela, (100, 255, 100), (int(mira_x), int(y - 4)), 1)

    # === EFEITO DE ENERGIA ===
    pulso = (math.sin(tempo_atual / 130) + 1) / 2
    cor_energia = (255, int(140 + pulso * 115), 0)  # Laranja pulsante
    energia_width = 1 + int(pulso)

    # Energia no cano
    pygame.draw.line(tela, cor_energia, (corpo_x + 2, y), (ponta_x, y), energia_width)
    # Energia no tubo
    pygame.draw.line(tela, cor_energia, (corpo_x, y + 4), (ponta_x - 3, y + 4), max(1, energia_width - 1))

def desenhar_icone_desert_eagle(tela, x, y, tempo_atual):
    """
    Desenha um ícone de Desert Eagle realista com acabamento em aço inoxidável.
    Um verdadeiro canhão de mão - pistola poderosa de alto calibre.
    """
    # Cores realistas da Desert Eagle (aço inoxidável/cromado)
    cor_metal_claro = (180, 180, 190)      # Aço brilhante
    cor_metal_medio = (120, 120, 130)      # Aço médio
    cor_metal_escuro = (60, 60, 70)        # Aço escuro/sombra
    cor_punho_preto = (30, 30, 35)         # Punho de borracha preta
    cor_detalhes_punho = (50, 50, 55)      # Detalhes do grip
    cor_brilho_metal = (220, 220, 230)     # Reflexo do metal
    cor_cano_interno = (20, 20, 25)        # Interior do cano
    
    # Animação sutil de brilho metálico
    pulso = (math.sin(tempo_atual / 400) + 1) / 2
    
    # === SLIDE (parte superior massiva da Desert Eagle) ===
    slide_x = x - 18
    slide_y = y - 5
    slide_largura = 38
    slide_altura = 8
    
    # Slide principal com efeito de metal em camadas
    slide_rect = pygame.Rect(slide_x, slide_y, slide_largura, slide_altura)
    pygame.draw.rect(tela, cor_metal_medio, slide_rect, 0, 2)
    
    # Brilho superior do slide (simula reflexo de luz)
    pygame.draw.line(tela, cor_metal_claro, 
                    (slide_x + 2, slide_y + 1), 
                    (slide_x + slide_largura - 4, slide_y + 1), 2)
    
    # Sombra inferior do slide
    pygame.draw.line(tela, cor_metal_escuro, 
                    (slide_x + 2, slide_y + slide_altura - 2), 
                    (slide_x + slide_largura - 4, slide_y + slide_altura - 2), 1)
    
    # Ranhuras de ventilação no slide (característica marcante)
    for i in range(5):
        ranhura_x = slide_x + 20 + i * 3
        pygame.draw.line(tela, cor_metal_escuro,
                        (ranhura_x, slide_y + 2),
                        (ranhura_x, slide_y + slide_altura - 2), 2)
        # Reflexo nas ranhuras
        pygame.draw.line(tela, cor_metal_claro,
                        (ranhura_x + 1, slide_y + 2),
                        (ranhura_x + 1, slide_y + slide_altura - 2), 1)
    
    # === CANO MASSIVO (característica principal da Desert Eagle) ===
    cano_x = slide_x + slide_largura
    cano_y = y
    cano_raio = 4  # Cano grosso
    
    # Cano externo com sombreamento
    pygame.draw.circle(tela, cor_metal_medio, (cano_x, cano_y), cano_raio)
    pygame.draw.circle(tela, cor_metal_claro, (cano_x, cano_y - 1), cano_raio - 1)
    
    # Boca do cano (buraco interno)
    pygame.draw.circle(tela, cor_cano_interno, (cano_x, cano_y), cano_raio - 2)
    pygame.draw.circle(tela, (10, 10, 15), (cano_x, cano_y), cano_raio - 3)
    
    # Anel de precisão na boca do cano
    pygame.draw.circle(tela, cor_metal_escuro, (cano_x, cano_y), cano_raio, 1)
    
    # === FRAME (corpo/chassi da arma) ===
    frame_x = slide_x + 3
    frame_y = y
    frame_largura = 26
    frame_altura = 12
    
    frame_rect = pygame.Rect(frame_x, frame_y - frame_altura//2, frame_largura, frame_altura)
    pygame.draw.rect(tela, cor_metal_escuro, frame_rect, 0, 2)
    
    # Detalhes de sombreamento no frame
    pygame.draw.rect(tela, cor_metal_medio, 
                    (frame_x + 1, frame_y - frame_altura//2 + 1, frame_largura - 2, 2), 0, 1)
    
    # === TRILHO PICATINNY (em cima do slide) ===
    trilho_y = slide_y - 2
    for i in range(3):
        trilho_x = slide_x + 15 + i * 4
        pygame.draw.rect(tela, cor_metal_escuro, (trilho_x, trilho_y, 2, 2))
    
    # === GUARDA-MATO (trigger guard) ===
    guarda_centro_x = frame_x + 10
    guarda_centro_y = y + 6
    
    # Guarda-mato robusto
    pygame.draw.ellipse(tela, cor_metal_medio,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 2)
    pygame.draw.ellipse(tela, cor_metal_claro,
                       (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 1)
    
    # === GATILHO ===
    gatilho_x = guarda_centro_x
    gatilho_y = guarda_centro_y
    pygame.draw.rect(tela, cor_metal_claro, (gatilho_x - 2, gatilho_y - 1, 4, 3), 0, 1)
    pygame.draw.line(tela, cor_metal_escuro, (gatilho_x - 1, gatilho_y + 1), (gatilho_x + 1, gatilho_y + 1), 1)
    
    # === PUNHO ERGONÔMICO (grip) ===
    punho_x = frame_x - 1
    punho_y = y + 3
    
    # Formato anatômico do punho
    punho_pontos = [
        (punho_x, punho_y - 4),
        (punho_x + 12, punho_y - 3),
        (punho_x + 10, punho_y + 12),
        (punho_x - 4, punho_y + 10)
    ]
    
    # Punho principal (preto fosco)
    pygame.draw.polygon(tela, cor_punho_preto, punho_pontos)
    pygame.draw.polygon(tela, cor_detalhes_punho, punho_pontos, 1)
    
    # Textura antiderrapante do punho (checkering)
    for i in range(4):
        for j in range(2):
            tex_x = punho_x + 2 + j * 3
            tex_y = punho_y + 1 + i * 3
            pygame.draw.rect(tela, cor_detalhes_punho, (tex_x, tex_y, 2, 2))
    
    # === CARREGADOR (magazine) ===
    mag_x = punho_x + 3
    mag_y = punho_y + 12
    pygame.draw.rect(tela, cor_metal_escuro, (mag_x, mag_y, 5, 3))
    pygame.draw.line(tela, cor_metal_claro, (mag_x, mag_y), (mag_x + 5, mag_y), 1)
    
    # === MIRAS (sights) ===
    # Mira frontal
    mira_frontal_x = cano_x - 4
    mira_frontal_y = slide_y - 2
    pygame.draw.rect(tela, cor_metal_claro, (mira_frontal_x, mira_frontal_y, 2, 4))
    pygame.draw.circle(tela, (100, 255, 100), (mira_frontal_x + 1, mira_frontal_y + 1), 1)  # Ponto luminoso
    
    # Mira traseira
    mira_traseira_x = slide_x + 8
    mira_traseira_y = slide_y - 2
    pygame.draw.rect(tela, cor_metal_escuro, (mira_traseira_x, mira_traseira_y, 5, 3))
    # Entalhe da mira traseira
    pygame.draw.line(tela, cor_cano_interno, (mira_traseira_x + 2, mira_traseira_y), 
                    (mira_traseira_x + 2, mira_traseira_y + 2), 2)
    
    # === EFEITO DE BRILHO METÁLICO SUTIL ===
    if pulso > 0.7:
        brilho_surf = pygame.Surface((50, 25), pygame.SRCALPHA)
        alpha = int(40 * pulso)
        cor_glow = (200, 200, 210, alpha)
        
        # Brilho suave no slide
        pygame.draw.line(brilho_surf, cor_glow,
                        (10, 8),
                        (45, 8), 3)
        
        tela.blit(brilho_surf, (slide_x - 5, slide_y - 3))
    
    # === LOGO/MARCA "DESERT EAGLE" ===
    logo_x = frame_x + 14
    logo_y = frame_y - 2
    # Desenhar "DE" estilizado
    pygame.draw.line(tela, cor_metal_claro, (logo_x, logo_y), (logo_x + 3, logo_y), 1)
    pygame.draw.line(tela, cor_metal_claro, (logo_x + 4, logo_y), (logo_x + 6, logo_y), 1)

def desenhar_icone_sabre_luz(tela, x, y, tempo_atual):
    """
    Desenha um ícone de sabre de luz com efeitos visuais épicos.
    """
    # Cores do sabre de luz
    cor_cabo_metal = (150, 150, 160)
    cor_cabo_detalhes = (100, 100, 110)
    cor_ativador = (200, 50, 50)
    
    # Cores da lâmina (azul brilhante estilo Jedi)
    cor_lamina_core = (200, 230, 255)  # Centro da lâmina
    cor_lamina_edge = (50, 150, 255)   # Borda da lâmina
    cor_lamina_glow = (100, 200, 255)  # Brilho externo
    
    # Animação de pulsação
    pulso = (math.sin(tempo_atual / 200) + 1) / 2
    vibração = math.sin(tempo_atual / 50) * 0.5
    
    # Cabo do sabre
    cabo_comprimento = 25
    cabo_largura = 6
    cabo_x = x - cabo_comprimento // 2
    cabo_y = y
    
    # Desenhar cabo principal
    cabo_rect = pygame.Rect(cabo_x, cabo_y - cabo_largura//2, cabo_comprimento, cabo_largura)
    pygame.draw.rect(tela, cor_cabo_metal, cabo_rect, 0, 3)
    pygame.draw.rect(tela, cor_cabo_detalhes, cabo_rect, 1, 3)
    
    # Detalhes do cabo
    for i in range(3):
        detalhe_x = cabo_x + 5 + i * 5
        pygame.draw.line(tela, cor_cabo_detalhes, 
                        (detalhe_x, cabo_y - 2), 
                        (detalhe_x, cabo_y + 2), 1)
    
    # Botão ativador
    ativador_x = cabo_x + cabo_comprimento // 2
    ativador_y = cabo_y + 4
    pygame.draw.circle(tela, cor_ativador, (ativador_x, ativador_y), 3)
    pygame.draw.circle(tela, (255, 100, 100), (ativador_x, ativador_y), 2)
    
    # Emissor da lâmina
    emissor_x = cabo_x + cabo_comprimento
    emissor_y = cabo_y
    pygame.draw.circle(tela, (200, 200, 220), (emissor_x, emissor_y), 4)
    pygame.draw.circle(tela, (100, 100, 120), (emissor_x, emissor_y), 2)
    
    # Lâmina de energia
    lamina_comprimento = 35
    lamina_end_x = emissor_x + lamina_comprimento
    lamina_end_y = emissor_y + vibração
    
    # Brilho externo da lâmina (múltiplas camadas para efeito de glow)
    for i in range(5, 0, -1):
        alpha = int(50 * (1 - i/5) * (0.5 + pulso * 0.5))
        glow_surf = pygame.Surface((lamina_comprimento + 20, 20), pygame.SRCALPHA)
        glow_color = tuple(list(cor_lamina_glow) + [alpha])
        
        # Desenhar linha de brilho
        start_pos = (10, 10)
        end_pos = (lamina_comprimento + 10, 10 + vibração)
        
        for j in range(i):
            pygame.draw.line(glow_surf, glow_color, start_pos, end_pos, i * 2)
        
        tela.blit(glow_surf, (emissor_x - 10, emissor_y - 10))
    
    # Núcleo da lâmina
    pygame.draw.line(tela, cor_lamina_edge, 
                    (emissor_x, emissor_y), 
                    (lamina_end_x, lamina_end_y), 4)
    
    pygame.draw.line(tela, cor_lamina_core, 
                    (emissor_x, emissor_y), 
                    (lamina_end_x, lamina_end_y), 2)
    
    # Efeito de faíscas na ponta
    if pulso > 0.7:
        for i in range(3):
            spark_x = lamina_end_x + random.uniform(-2, 2)
            spark_y = lamina_end_y + random.uniform(-2, 2)
            pygame.draw.circle(tela, cor_lamina_core, (int(spark_x), int(spark_y)), 1)
    
    # Partículas de energia ao longo da lâmina
    for i in range(3):
        particle_progress = (i + 1) / 4
        particle_x = emissor_x + int(lamina_comprimento * particle_progress)
        particle_y = emissor_y + vibração * particle_progress
        particle_alpha = int(150 * pulso)
        
        if particle_alpha > 50:
            pygame.draw.circle(tela, cor_lamina_glow, 
                             (int(particle_x), int(particle_y)), 2)

def desenhar_weapons_shop(tela, area_conteudo, moeda_manager, upgrades, mouse_pos, clique_ocorreu, som_compra, som_erro, scroll_y=0):
    """
    Desenha a seção de armas da loja com sistema de preços dinâmicos e scroll.
    
    Args:
        tela: Superfície principal do jogo
        area_conteudo: Retângulo definindo a área de conteúdo
        moeda_manager: Gerenciador de moedas
        upgrades: Dicionário com os upgrades do jogador
        mouse_pos: Posição atual do mouse
        clique_ocorreu: Se houve clique neste frame
        som_compra: Som para compra bem-sucedida
        som_erro: Som para erro na compra
        scroll_y: Posição atual do scroll (padrão: 0)
        
    Returns:
        Tupla (mensagem, cor, max_scroll) ou (None, None, max_scroll)
    """
    # Inicializar sistema de pricing
    pricing_manager = PricingManager()
    
    # Título da seção
    desenhar_texto(tela, "WEAPONS", 36, (255, 120, 120), LARGURA // 2, area_conteudo.y + 30)
    
    # Obter o tempo atual para animações
    tempo_atual = pygame.time.get_ticks()
    
    resultado = None
    
    # Configurações dos itens
    altura_item = 120
    espaco_entre_itens = 30
    margem_superior = 70
    margem_lateral = 35
    margem_clipping = 15
    
    # Lista de armas para facilitar a adição de novas armas
    armas_loja = [
        {
            "key": "espingarda",
            "nome": "SHOTGUN",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Four shots at once!",
            "cor_fundo": (50, 30, 30),
            "cor_borda": (150, 70, 70),
            "cor_botao": (180, 100, 50),
            "cor_hover": (220, 140, 60),
            "cor_texto": (255, 150, 150),
            "cor_resultado": VERDE,
            "icone_func": "espingarda",
            "dano": 1
        },
        {
            "key": "metralhadora",
            "nome": "MACHINE GUN",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Rapid fire with high capacity",
            "cor_fundo": (60, 35, 20),
            "cor_borda": (255, 140, 70),
            "cor_botao": (180, 120, 30),
            "cor_hover": (220, 150, 50),
            "cor_texto": (255, 180, 70),
            "cor_resultado": VERDE,
            "icone_func": "metralhadora",
            "dano": 1
        },
        {
            "key": "spas12",
            "nome": "SPAS-12",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Tactical semi-auto shotgun - faster fire rate!",
            "cor_fundo": (35, 35, 40),
            "cor_borda": (255, 140, 0),
            "cor_botao": (200, 120, 30),
            "cor_hover": (255, 160, 50),
            "cor_texto": (255, 180, 80),
            "cor_resultado": LARANJA if 'LARANJA' in dir() else (255, 165, 0),
            "icone_func": "spas12",
            "dano": 2
        },
        {
            "key": "desert_eagle",
            "nome": "DESERT EAGLE",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Powerful hand cannon with high damage & accuracy",
            "cor_fundo": (60, 50, 30),
            "cor_borda": (220, 180, 80),
            "cor_botao": (180, 140, 60),
            "cor_hover": (220, 180, 80),
            "cor_texto": (255, 220, 120),
            "cor_resultado": AMARELO,
            "icone_func": "desert_eagle",
            "custo": 100,
            "dano": 3
        },
        {
            "key": "sniper",
            "nome": "SCOUT",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Hold right-click to aim precisely, otherwise shots go random!",
            "cor_fundo": (40, 45, 50),
            "cor_borda": (120, 140, 160),
            "cor_botao": (80, 100, 120),
            "cor_hover": (120, 140, 160),
            "cor_texto": (180, 200, 220),
            "cor_resultado": BRANCO,
            "icone_func": "sniper",
            "dano": 6
        },
        {
            "key": "sabre_luz",
            "nome": "LIGHTSABER",
            "descricao": "",
            "instrucoes": "Press R to switch weapon type",
            "info_extra": "Only for those who know what they're doing.",
            "cor_fundo": (30, 30, 60),
            "cor_borda": (100, 150, 255),
            "cor_botao": (50, 100, 200),
            "cor_hover": (80, 150, 255),
            "cor_texto": (150, 200, 255),
            "cor_resultado": CIANO,
            "icone_func": "sabre_luz",
            "dano": 10
        }
    ]
    
    # Aplicar sistema de pricing às armas
    armas_loja = aplicar_pricing_sistema(armas_loja, pricing_manager)
    
    # Calcular altura total necessária para todos os itens
    altura_total_conteudo = len(armas_loja) * (altura_item + espaco_entre_itens) + espaco_entre_itens + (margem_clipping * 2)
    area_scroll_altura = area_conteudo.height - margem_superior
    max_scroll = max(0, altura_total_conteudo - area_scroll_altura)
    
    # Criar uma superfície para o conteúdo dos itens com clipping
    area_scroll_y = area_conteudo.y + margem_superior
    conteudo_surf = pygame.Surface((area_conteudo.width, area_scroll_altura), pygame.SRCALPHA)
    conteudo_surf.fill((0, 0, 0, 0))  # Transparente
    
    # Desenhar fundo da área de scroll
    pygame.draw.rect(conteudo_surf, (20, 20, 50, 150), (0, 0, area_conteudo.width, area_scroll_altura), 0, 10)
    pygame.draw.rect(conteudo_surf, (70, 70, 130), (0, 0, area_conteudo.width, area_scroll_altura), 2, 10)
    
    # Definir área de clipping para os itens
    cliprect = pygame.Rect(margem_clipping, margem_clipping, 
                          area_conteudo.width - (margem_clipping * 2), 
                          area_scroll_altura - (margem_clipping * 2))
    conteudo_surf.set_clip(cliprect)
    
    # Desenhar cada arma na superfície de conteúdo
    for i, arma in enumerate(armas_loja):
        # Calcular posição Y do item considerando o scroll e margem de clipping
        y_item_relativo = i * (altura_item + espaco_entre_itens) + espaco_entre_itens + margem_clipping - scroll_y
        
        # Se o item está fora da área visível, não desenhar
        if (y_item_relativo + altura_item < margem_clipping or 
            y_item_relativo > area_scroll_altura - margem_clipping):
            continue
        
        # Retângulo do item na superfície de conteúdo
        item_rect = pygame.Rect(margem_lateral, y_item_relativo, 
                               area_conteudo.width - (margem_lateral * 2), altura_item)
        
        # Cor baseada na disponibilidade
        if not arma.get("pode_comprar", True):
            # Arma esgotada
            cor_fundo = (arma["cor_fundo"][0]//3, arma["cor_fundo"][1]//3, arma["cor_fundo"][2]//3)
            cor_borda = (100, 50, 50)  # Vermelho escuro para esgotado
        else:
            cor_fundo = arma["cor_fundo"]
            cor_borda = arma["cor_borda"]
        
        # Desenhar fundo do item
        pygame.draw.rect(conteudo_surf, cor_fundo, item_rect, 0, 8)
        pygame.draw.rect(conteudo_surf, cor_borda, item_rect, 2, 8)
        
        # Se esgotado, adicionar overlay
        if not arma.get("pode_comprar", True):
            overlay_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            overlay_surf.fill((0, 0, 0, 120))
            conteudo_surf.blit(overlay_surf, (item_rect.x, item_rect.y))
        
        # Desenhar ícone da arma
        icone_x = item_rect.x + 60
        icone_y = y_item_relativo + altura_item // 2
        
        if arma["icone_func"] == "desert_eagle":
            desenhar_icone_desert_eagle(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "espingarda":
            desenhar_icone_espingarda(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "spas12":
            desenhar_icone_spas12(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "metralhadora":
            desenhar_icone_metralhadora(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "sniper":
            from src.weapons.sniper import desenhar_icone_sniper
            desenhar_icone_sniper(conteudo_surf, icone_x, icone_y, tempo_atual)
        elif arma["icone_func"] == "sabre_luz":
            desenhar_icone_sabre_luz(conteudo_surf, icone_x, icone_y, tempo_atual)
        
        # Nome da arma
        cor_texto = arma["cor_texto"] if arma.get("pode_comprar", True) else (100, 100, 100)
        desenhar_texto(conteudo_surf, arma["nome"], 24, cor_texto, 
                      item_rect.x + 170, y_item_relativo + 20)
        
        # Descrição e status da arma
        if arma["key"] not in upgrades or upgrades[arma["key"]] == 0:
            if arma["key"] == "sabre_luz":
                status = f"{arma['descricao']} (Not owned)"
            else:
                status = f"{arma['descricao']} (No ammo)"
        else:
            if arma["key"] == "sabre_luz":
                status = f"Energy cells"
            else:
                status = f"Ammunition: {upgrades[arma['key']]}"
        
        desenhar_texto(conteudo_surf, status, 15, BRANCO if arma.get("pode_comprar", True) else (120, 120, 120), 
                      item_rect.x + 170, y_item_relativo + 40)
        
        # Informações de limite e próximo preço
        info_limite = arma.get("info_limite", "")
        desenhar_texto(conteudo_surf, info_limite, 12, (180, 180, 180),
                      item_rect.x + 170, y_item_relativo + 58)

        # Mostrar dano da arma
        if arma.get("pode_comprar", True):
            desenhar_texto(conteudo_surf, f"Damage: {arma.get('dano', 1)}", 16, (255, 200, 100),
                          item_rect.x + 170, y_item_relativo + 75)
        else:
            desenhar_texto(conteudo_surf, "SOLD OUT", 14, VERMELHO,
                          item_rect.x + 170, y_item_relativo + 75)
        
        # Informações adicionais da arma
        desenhar_texto(conteudo_surf, arma["info_extra"], 10, (150, 150, 150), 
                      item_rect.x + 170, y_item_relativo + 92)
        
        # Botão de compra
        botao_largura = 120
        botao_altura = 35
        botao_x_relativo = item_rect.x + item_rect.width - 70
        botao_y_relativo = y_item_relativo + altura_item // 2
        
        rect_compra_relativo = pygame.Rect(botao_x_relativo - botao_largura//2, 
                                         botao_y_relativo - botao_altura//2,
                                         botao_largura, botao_altura)
        
        # Verificar se o jogador tem moedas suficientes e se pode comprar
        pode_comprar = (moeda_manager.obter_quantidade() >= arma["custo"] and 
                       arma.get("pode_comprar", True))
        
        # Calcular posição real do botão na tela para verificar hover e clique
        botao_x_real = area_conteudo.x + botao_x_relativo
        botao_y_real = area_scroll_y + botao_y_relativo
        rect_compra_real = pygame.Rect(botao_x_real - botao_largura//2, 
                                      botao_y_real - botao_altura//2,
                                      botao_largura, botao_altura)
        
        # Verificar hover
        hover_compra = (rect_compra_real.collidepoint(mouse_pos) and 
                       area_scroll_y <= botao_y_real <= area_scroll_y + area_scroll_altura and
                       pode_comprar)
        
        # Cores do botão baseadas na capacidade de compra
        if not arma.get("pode_comprar", True):
            # Esgotado
            cor_botao = (80, 40, 40)
            cor_hover = (80, 40, 40)
        elif pode_comprar:
            # Pode comprar
            cor_botao = arma["cor_botao"]
            cor_hover = arma["cor_hover"]
        else:
            # Sem moedas suficientes
            cor_botao = (arma["cor_botao"][0]//3, arma["cor_botao"][1]//3, arma["cor_botao"][2]//3)
            cor_hover = cor_botao
        
        # Desenhar botão de compra na superfície de conteúdo
        pygame.draw.rect(conteudo_surf, cor_hover if hover_compra else cor_botao, 
                        rect_compra_relativo, 0, 6)
        pygame.draw.rect(conteudo_surf, arma["cor_borda"], rect_compra_relativo, 2, 6)
        
        # Ícone de moeda e custo
        moeda_mini_x = botao_x_relativo - 25
        moeda_mini_y = botao_y_relativo
        pygame.draw.circle(conteudo_surf, AMARELO, (moeda_mini_x, moeda_mini_y), 6)
        
        # Texto de custo
        desenhar_texto(conteudo_surf, f"{arma['custo']}", 16, BRANCO, 
                      botao_x_relativo + 8, botao_y_relativo)
        
        # Verificar clique no botão de compra
        if clique_ocorreu and hover_compra and arma.get("pode_comprar", True):
            if pode_comprar:
                # Compra bem-sucedida
                moeda_manager.quantidade_moedas -= arma["custo"]
                moeda_manager.salvar_moedas()
                
                # Registrar compra no sistema de pricing
                pricing_manager.realizar_compra(arma["key"])
                
                # Atualizar quantidade da arma
                quantidade_compra = pricing_manager.dados_pricing[arma["key"]]["quantidade_por_compra"]
                if arma["key"] in upgrades:
                    upgrades[arma["key"]] += quantidade_compra
                else:
                    upgrades[arma["key"]] = quantidade_compra
                
                salvar_upgrades(upgrades)
                pygame.mixer.Channel(4).play(som_compra)
                
                if arma["key"] == "sabre_luz":
                    nome_resultado = f"{arma['nome']} +{quantidade_compra} energy cells purchased!"
                else:
                    nome_resultado = f"{arma['nome']} +{quantidade_compra} ammo purchased!"
                resultado = (nome_resultado, arma["cor_resultado"])
            else:
                # Não tem moedas suficientes
                pygame.mixer.Channel(4).play(som_erro)
                resultado = ("Not enough coins!", VERMELHO)
    
    # Resetar clipping
    conteudo_surf.set_clip(None)
    
    # Aplicar a superfície de conteúdo à tela
    tela.blit(conteudo_surf, (area_conteudo.x, area_scroll_y))
    
    # Desenhar barra de scroll se necessário
    if max_scroll > 0:
        barra_largura = 12
        barra_x = area_conteudo.x + area_conteudo.width - barra_largura - 8
        barra_y = area_scroll_y
        barra_altura = area_scroll_altura
        
        # Fundo da barra de scroll
        pygame.draw.rect(tela, (50, 50, 50), (barra_x, barra_y, barra_largura, barra_altura), 0, 6)
        
        # Calcular posição e tamanho do indicador
        handle_ratio = min(1.0, area_scroll_altura / altura_total_conteudo)
        indicador_altura = max(30, int(barra_altura * handle_ratio))
        scroll_ratio = scroll_y / max_scroll if max_scroll > 0 else 0
        indicador_y = barra_y + int((barra_altura - indicador_altura) * scroll_ratio)
        
        pygame.draw.rect(tela, (180, 180, 180), (barra_x, indicador_y, barra_largura, indicador_altura), 0, 6)
    
    # Adicionar instruções na parte inferior
    instrucoes_y = area_conteudo.y + area_conteudo.height - 30
    desenhar_texto(tela, "Use mouse wheel to scroll • Click buttons to buy ammunition", 16, (180, 180, 180), 
                  area_conteudo.x + area_conteudo.width//2, instrucoes_y)
    
    return (resultado[0] if resultado else None, 
            resultado[1] if resultado else None, 
            max_scroll)