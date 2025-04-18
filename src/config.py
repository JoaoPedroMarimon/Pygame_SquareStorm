#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arquivo de configurações do jogo.
Contém constantes, cores e outras configurações.
"""

# Configurações da janela
LARGURA, ALTURA = 1024, 768
TITULO = "QUADRADO VERSUS QUADRADO"
FPS = 60
MAX_FASES = 5  # Alterado de 2 para 3 - agora com fase especial

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 50, 50)
VERMELHO_ESCURO = (180, 30, 30)
AZUL = (50, 100, 255)
AZUL_ESCURO = (30, 60, 180)
AMARELO = (255, 255, 0)
VERDE = (50, 255, 50)
ROXO = (180, 50, 230)  # Cor do inimigo especial
CIANO = (0, 255, 255)
LARANJA = (255, 165, 0)

# Configurações de jogabilidade
VELOCIDADE_JOGADOR = 3.0
VELOCIDADE_INIMIGO_BASE = 4.5
VELOCIDADE_INIMIGO_ESPECIAL = 3.8  # Velocidade do inimigo roxo (um pouco mais lento)
TAMANHO_QUADRADO = 40
DURACAO_INVULNERAVEL = 1000  # Tempo de invulnerabilidade após receber dano (ms)
COOLDOWN_TIRO_JOGADOR = 500  # Tempo entre tiros do jogador (ms)
COOLDOWN_TIRO_INIMIGO = 400  # Tempo base entre tiros do inimigo (ms)
COOLDOWN_TIRO_ESPECIAL = 600  # Cooldown maior para o inimigo especial

# Configurações de efeitos visuais
NUM_ESTRELAS_MENU = 200
NUM_ESTRELAS_JOGO = 120
DURACAO_TRANSICAO_FASE = 180  # Frames para a transição entre fases

# Adicionar ao arquivo config.py:

# Constantes para moedas
MOEDA_TAMANHO = 15
MOEDA_COR = AMARELO  # Usar a cor AMARELO já definida
MOEDA_INTERVALO_MIN = 3000  # Tempo mínimo entre geração de moedas (ms)
MOEDA_INTERVALO_MAX = 8000  # Tempo máximo entre geração de moedas (ms)
MOEDA_DURACAO_MIN = 5000    # Tempo mínimo que uma moeda fica na tela (ms)
MOEDA_DURACAO_MAX = 10000   # Tempo máximo que uma moeda fica na tela (ms)

# Cores para a loja
ROXO_CLARO = (100, 50, 150)
ROXO_ESCURO = (40, 0, 80)

