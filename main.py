# Adicione prints de debug no arquivo main.py para ver onde está travando:

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQUARE VERSUS SQUARE
Um jogo de batalha entre formas geométricas com sistema de fases.

Este é o arquivo principal que inicia o jogo.
"""

import pygame
import sys
print("✅ Pygame importado")

from src.config import TITULO
print("✅ Config importado")

try:
    from src.game.jogo import main_game
    print("✅ main_game importado")
except Exception as e:
    print(f"❌ ERRO ao importar main_game: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def main():
    """Função principal do programa."""
    print("🚀 Iniciando pygame...")
    
    # Inicializar o Pygame
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    print("✅ Pygame inicializado")
    
    # Configurar canais para mixagem de áudio
    pygame.mixer.set_num_channels(8)
    print("✅ Canais de áudio configurados")
    
    try:
        print("🎮 Chamando main_game()...")
        # Iniciar o jogo principal
        main_game()
    except Exception as e:
        print(f"❌ ERRO em main_game(): {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔚 Encerrando pygame...")
        # Encerrar o Pygame ao sair
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("🎯 Iniciando SquareStorm...")
    main()