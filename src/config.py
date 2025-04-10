#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arquivo de configurações do jogo.
Contém constantes, cores e outras configurações.
"""

# Configurações da janela
LARGURA, ALTURA = 800, 600
TITULO = "QUADRADO VERSUS QUADRADO"
FPS = 60
MAX_FASES = 10  # Número máximo de fases

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 50, 50)
VERMELHO_ESCURO = (180, 30, 30)
AZUL = (50, 100, 255)
AZUL_ESCURO = (30, 60, 180)
AMARELO = (255, 255, 0)
VERDE = (50, 255, 50)
ROXO = (180, 50, 230)
CIANO = (0, 255, 255)
LARANJA = (255, 165, 0)

# Configurações de jogabilidade
VELOCIDADE_JOGADOR = 5.5
VELOCIDADE_INIMIGO_BASE = 4.5
TAMANHO_QUADRADO = 40
DURACAO_INVULNERAVEL = 1000  # Tempo de invulnerabilidade após receber dano (ms)
COOLDOWN_TIRO_JOGADOR = 500  # Tempo entre tiros do jogador (ms)
COOLDOWN_TIRO_INIMIGO = 400  # Tempo base entre tiros do inimigo (ms)

# Configurações de efeitos visuais
NUM_ESTRELAS_MENU = 150
NUM_ESTRELAS_JOGO = 80
DURACAO_TRANSICAO_FASE = 180  # Frames para a transição entre fases