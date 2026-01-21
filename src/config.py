#!/usr/bin/env python3
# -*- coding: utf-8 -*-



# Configurações da janela
LARGURA, ALTURA = 1480, 820 # Aumentamos a altura em 80 pixels para a barra de HUD
LARGURA_JOGO, ALTURA_JOGO = 1480, 820-80  # Dimensões da área jogável
ALTURA_HUD = 80  # Altura da barra de HUD
TITULO = "SquareStorm"
FPS = 60
MAX_FASES = 25  # Atualizado para incluir a Fase 11 (Inimigos Metralhadora)

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
CINZA_ESCURO = (40, 40, 60)  # Cor para o fundo do HUD
# Configurações de jogabilidade
VELOCIDADE_INIMIGO_CIANO = 4.5 * 4.0
VELOCIDADE_JOGADOR = 4.5
VELOCIDADE_INIMIGO_BASE = 4.5
VELOCIDADE_INIMIGO_ESPECIAL = 3.8  # Velocidade do inimigo roxo (um pouco mais lento)
TAMANHO_QUADRADO = 40
TAMANHO_MULTIPLAYER = 12  # Tamanho menor para caber nos corredores do dungeon (tiles 16x16)
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
MOEDA_INTERVALO_MIN = 1000  # Tempo mínimo entre geração de moedas (ms)
MOEDA_INTERVALO_MAX = 3000  # Tempo máximo entre geração de moedas (ms)
MOEDA_DURACAO_MIN = 5000    # Tempo mínimo que uma moeda fica na tela (ms)
MOEDA_DURACAO_MAX = 30000   # Tempo máximo que uma moeda fica na tela (ms)


# Adicione estas linhas ao final do arquivo src/config.py

# Configurações do Sabre de Luz
SABRE_COMPRIMENTO_MAX = 60
SABRE_VELOCIDADE_ATIVACAO = 5
SABRE_COR_AZUL = (150, 150, 255)
SABRE_COR_VERDE = (100, 255, 100)  # Cor para modo defesa
SABRE_COR_CABO = (150, 150, 150)
SABRE_RAIO_DEFLEXAO = 8

# Cores para a loja
ROXO_CLARO = (100, 50, 150)
ROXO_ESCURO = (40, 0, 80)