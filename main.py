#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQUARE VERSUS SQUARE
Um jogo de batalha entre formas geométricas com sistema de fases.
VERSÃO ATUALIZADA com suporte a tela cheia e escalonamento.
"""

import pygame
import sys
print("Pygame importado")

from src.config import TITULO
print("Config importado")

# NOVO: Importar o sistema de display
from src.utils.display_manager import (
    initialize_game_display, 
    present_frame, 
    toggle_fullscreen,
    convert_mouse_position,
    get_display_manager
)

try:
    from src.game.jogo import main_game
    print("main_game importado")
except Exception as e:
    print(f"ERRO ao importar main_game: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def main():
    """Função principal do programa com suporte a tela cheia."""
    print("Iniciando pygame...")
    
    # Inicializar o Pygame
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    print("Pygame inicializado")
    
    # Configurar canais para mixagem de áudio
    pygame.mixer.set_num_channels(8)
    print("Canais de audio configurados")
    
    # NOVO: Inicializar sistema de display
    # Pode começar em tela cheia ou janela
    start_fullscreen = True  # Mude para True se quiser começar em tela cheia
    game_surface = initialize_game_display(fullscreen=start_fullscreen)
    print(f"[OK] Display inicializado ({'Tela Cheia' if start_fullscreen else 'Janela'})")
    
    try:
        print("Chamando main_game()...")
        # Iniciar o jogo principal passando a superfície correta
        main_game(game_surface)
    except Exception as e:
        print(f"ERRO em main_game(): {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Encerrando pygame...")
        # Encerrar o Pygame ao sair
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Iniciando SquareStorm...")
    print("Dicas:")
    print("   - Pressione F11 para alternar tela cheia")
    print("   - Pressione ESC para sair da tela cheia")
    main()