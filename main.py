#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QUADRADO VERSUS QUADRADO
Um jogo de batalha entre formas geométricas com sistema de fases.

Este é o arquivo principal que inicia o jogo.
"""

import pygame
import sys
from src.config import TITULO
from src.game.jogo import main_game

def main():
    """Função principal do programa."""
    # Inicializar o Pygame
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    
    # Configurar canais para mixagem de áudio
    pygame.mixer.set_num_channels(8)
    
    try:
        # Iniciar o jogo principal
        main_game()
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        # Encerrar o Pygame ao sair
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()