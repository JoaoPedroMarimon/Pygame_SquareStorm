#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal do jogo SquareStorm.
Versão atualizada com suporte a tela cheia e escalonamento.
Modificado para continuar da última fase alcançada.
CORRIGIDO: Import da função correta de fase.
"""

import pygame
import sys
from src.config import *
from src.utils.visual import criar_gradiente, criar_estrelas
from src.ui.menu import tela_inicio, tela_game_over, tela_vitoria_fase
from src.ui.loja import tela_loja
from src.game.fase import jogar_fase  # CORRIGIDO: Usar o nome correto da função
from src.ui.selecao_fase import tela_selecao_fase
from src.utils.progress import ProgressManager
from src.game.inventario import tela_inventario

# NOVO: Importações para multiplayer
from src.network import GameServer, GameClient
from src.ui.menu import (
    tela_criar_servidor_simples,
    tela_conectar_servidor_simples
)
from src.game.fase_multiplayer import jogar_fase_multiplayer_simples

# NOVO: Importações para o sistema de tela cheia
from src.utils.display_manager import (
    present_frame,
    toggle_fullscreen,
    convert_mouse_position,
    get_display_manager
)

def main_game(game_surface=None):
    """
    Função principal do jogo com suporte a tela cheia.
    Modificada para suportar continuar da última fase alcançada.
    
    Args:
        game_surface: Superfície onde desenhar o jogo (fornecida pelo display manager)
    """
    print("🎮 Iniciando main_game...")
    
    # Se não foi fornecida uma superfície, criar uma padrão (compatibilidade)
    if game_surface is None:
        print("⚠️ Usando modo compatibilidade - criando superfície padrão")
        tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption(TITULO)
    else:
        print("✅ Usando superfície do display manager")
        tela = game_surface
    
    # Inicializar o relógio
    relogio = pygame.time.Clock()
    
    # Criar gradientes para diferentes telas
    print("🎨 Criando gradientes...")
    gradiente_menu = criar_gradiente((20, 0, 40), (0, 20, 60))
    gradiente_jogo = criar_gradiente((10, 0, 30), (0, 10, 40))
    gradiente_jogo_toxico = criar_gradiente((0, 30, 10), (10, 60, 20))  # Gradiente tóxico para fases 11+
    gradiente_loja = criar_gradiente((30, 10, 0), (60, 30, 0))
    gradiente_vitoria = criar_gradiente((0, 30, 0), (0, 60, 20))
    gradiente_derrota = criar_gradiente((30, 0, 0), (60, 20, 0))
    gradiente_selecao = criar_gradiente((15, 0, 25), (30, 10, 50))
    
    # Criar fontes
    print("📝 Criando fontes...")
    try:
        fonte_titulo = pygame.font.SysFont("Arial", 72, True)
        fonte_normal = pygame.font.SysFont("Arial", 24)
    except Exception as e:
        print(f"⚠️ Erro ao criar fontes: {e}")
        fonte_titulo = pygame.font.Font(None, 72)
        fonte_normal = pygame.font.Font(None, 24)
    
    # Inicializar gerenciador de progresso
    progress_manager = ProgressManager()
    
    # Variáveis de estado do jogo
    estado_atual = "menu"  # menu, jogar, loja, inventario, selecao_fase, game_over
    fase_atual = 1
    
    print("🚀 Entrando no loop principal...")
    
    # Loop principal do jogo
    while True:
        try:
            if estado_atual == "menu":
                print("📋 Exibindo menu principal...")
                resultado = tela_inicio(tela, relogio, gradiente_menu, fonte_titulo)
                
                # MODIFICADO: Tratar o novo formato de retorno
                if isinstance(resultado, tuple) and resultado[0] == "jogar":
                    estado_atual = "jogar"
                    fase_atual = resultado[1]  # Usar a fase retornada pelo menu
                    print(f"🎯 Iniciando na fase {fase_atual}...")
                elif resultado == "jogar":
                    # Compatibilidade com retorno antigo (caso não seja tupla)
                    estado_atual = "jogar"
                    fase_atual = 1
                elif resultado == "loja":
                    estado_atual = "loja"
                elif resultado == "inventario":
                    estado_atual = "inventario"
                elif resultado == "selecao_fase":
                    estado_atual = "selecao_fase"
                elif resultado == "multiplayer":
                    estado_atual = "multiplayer"
                elif resultado == False:
                    print("👋 Saindo do jogo...")
                    break
                
            elif estado_atual == "jogar":
                print(f"🎯 Iniciando fase {fase_atual}...")
                # Selecionar gradiente baseado na fase (fases 11+ usam tema tóxico)
                gradiente_fase = gradiente_jogo_toxico if fase_atual >= 11 else gradiente_jogo
                # CORRIGIDO: Usar a função correta jogar_fase
                resultado = jogar_fase(tela, relogio, fase_atual, gradiente_fase, fonte_titulo, fonte_normal)
                
                if resultado == True:
                    # Fase completada com sucesso
                    print(f"✅ Fase {fase_atual} completada!")
                    
                    # Atualizar progresso
                    progress_manager.atualizar_progresso(fase_atual + 1)
                    
                    # Verificar se chegou ao final do jogo
                    if fase_atual >= MAX_FASES:
                        print("🎉 Jogo completado!")
                        resultado_vitoria = tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual)
                        if resultado_vitoria == "menu":
                            estado_atual = "menu"
                        else:
                            estado_atual = "menu"  # Voltar ao menu de qualquer forma
                    else:
                        # Mostrar tela de vitória da fase
                        resultado_vitoria = tela_vitoria_fase(tela, relogio, gradiente_vitoria, fase_atual)
                        
                        if resultado_vitoria == "proximo":
                            fase_atual += 1  # Avançar para a próxima fase
                            # Continuar no estado "jogar"
                        elif resultado_vitoria == "menu":
                            estado_atual = "menu"
                        else:
                            break  # Sair do jogo
                
                elif resultado == False:
                    # Jogador perdeu
                    print(f"💀 Jogador derrotado na fase {fase_atual}")
                    resultado_derrota = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, False, fase_atual)
                    
                    if resultado_derrota:
                        estado_atual = "menu"
                    else:
                        break  # Sair do jogo
                
                elif resultado == "menu":
                    # Voltar ao menu (pausado)
                    estado_atual = "menu"
                
            elif estado_atual == "loja":
                print("🏪 Exibindo loja...")
                resultado = tela_loja(tela, relogio, gradiente_loja)
                
                if resultado == "menu":
                    estado_atual = "menu"
                
            elif estado_atual == "inventario":
                print("🎒 Exibindo inventário...")
                resultado = tela_inventario(tela, relogio, gradiente_loja, fonte_titulo, fonte_normal)
                    
                if resultado == "menu":
                    estado_atual = "menu"
                
            elif estado_atual == "selecao_fase":
                print("🎯 Exibindo seleção de fase...")
                fase_selecionada = tela_selecao_fase(tela, relogio, gradiente_selecao, fonte_titulo, fonte_normal)
                
                if fase_selecionada is not None:
                    # Verificar se a fase está desbloqueada
                    if progress_manager.pode_jogar_fase(fase_selecionada):
                        fase_atual = fase_selecionada
                        estado_atual = "jogar"
                        print(f"🎯 Fase {fase_selecionada} selecionada pelo jogador...")
                    else:
                        print(f"🔒 Fase {fase_selecionada} ainda não foi desbloqueada!")
                        estado_atual = "menu"  # Voltar ao menu
                else:
                    estado_atual = "menu"  # Cancelou a seleção
                
            elif estado_atual == 'multiplayer_host':
                print("🎮 Criando servidor...")
                config = tela_criar_servidor_simples(tela, relogio, gradiente_menu)

                if config:
                    # Criar servidor
                    servidor = GameServer(port=config['port'], max_players=config['max_players'])
                    if servidor.start():
                        print(f"✅ Servidor criado na porta {config['port']}")

                        # Host também é cliente
                        cliente = GameClient()
                        if cliente.connect('127.0.0.1', config['port'], config['player_name']):
                            print("✅ Host conectado como cliente")
                            # Ir para o jogo multiplayer
                            resultado = jogar_fase_multiplayer_simples(tela, relogio, cliente, config['player_name'])

                            # Limpar
                            cliente.disconnect()
                            servidor.stop()
                            estado_atual = "menu"
                        else:
                            print("❌ Host falhou ao conectar como cliente")
                            servidor.stop()
                            estado_atual = "multiplayer"
                    else:
                        print("❌ Falha ao criar servidor")
                        estado_atual = "menu"
                else:
                    estado_atual = "menu"

            elif estado_atual == 'multiplayer_join':
                print("🔌 Conectando a servidor...")
                config = tela_conectar_servidor_simples(tela, relogio, gradiente_menu)

                if config:
                    cliente = GameClient()
                    if cliente.connect(config['host'], config['port'], config['player_name']):
                        print(f"✅ Conectado a {config['host']}:{config['port']}")
                        # Ir para o jogo multiplayer
                        resultado = jogar_fase_multiplayer_simples(tela, relogio, cliente, config['player_name'])

                        # Limpar
                        cliente.disconnect()
                        estado_atual = "menu"
                    else:
                        print("❌ Falha ao conectar")
                        estado_atual = "menu"
                else:
                    estado_atual = "menu"

            elif estado_atual == "game_over":
                print("💀 Exibindo tela de game over...")
                resultado = tela_game_over(tela, relogio, gradiente_vitoria, gradiente_derrota, False, fase_atual)

                if resultado:
                    estado_atual = "menu"
                else:
                    break  # Sair do jogo

            else:
                print(f"⚠️ Estado desconhecido: {estado_atual}")
                estado_atual = "menu"  # Voltar ao menu por segurança
                
        except KeyboardInterrupt:
            print("\n👋 Interrompido pelo usuário...")
            break
        except Exception as e:
            print(f"❌ Erro no loop principal: {e}")
            import traceback
            traceback.print_exc()
            # Tentar continuar voltando ao menu
            estado_atual = "menu"
    
    print("🔚 main_game finalizado")


# Função auxiliar para debugging
def debug_display_info():
    """Exibe informações sobre o display atual."""
    manager = get_display_manager()
    print(f"🖥️ Informações do Display:")
    print(f"   Modo: {'Tela Cheia' if manager.is_fullscreen() else 'Janela'}")
    print(f"   Resolução da tela: {manager.screen_width}x{manager.screen_height}")
    print(f"   Resolução do jogo: {manager.BASE_WIDTH}x{manager.BASE_HEIGHT}")
    print(f"   Escala: {manager.scale_x:.2f}x{manager.scale_y:.2f}")
    print(f"   Offset: {manager.offset_x}, {manager.offset_y}")


# Função para tratar eventos globais de tela cheia
def handle_fullscreen_events(evento):
    """
    Trata eventos relacionados à tela cheia.
    Deve ser chamada em todos os loops de eventos.
    
    Args:
        evento: Evento do pygame
        
    Returns:
        True se o evento foi tratado, False caso contrário
    """
    if evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_F11:
            toggle_fullscreen()
            debug_display_info()  # Mostrar info após alternar
            return True
        elif evento.key == pygame.K_ESCAPE and get_display_manager().is_fullscreen():
            toggle_fullscreen()
            debug_display_info()  # Mostrar info após alternar
            return True
    
    return False


# Função para obter posição do mouse de forma segura
def get_game_mouse_pos():
    """
    Obtém a posição do mouse convertida para coordenadas do jogo.
    
    Returns:
        Tupla (x, y) com coordenadas do mouse no espaço do jogo
    """
    return convert_mouse_position(pygame.mouse.get_pos())


# Função para verificar se um ponto está dentro da área do jogo
def is_point_in_game_area(x, y):
    """
    Verifica se um ponto está dentro da área jogável.
    
    Args:
        x, y: Coordenadas a verificar
        
    Returns:
        True se o ponto está na área do jogo
    """
    return 0 <= x <= LARGURA and 0 <= y <= ALTURA


# Função para debug de mouse
def debug_mouse_position():
    """Exibe informações sobre a posição do mouse (para debug)."""
    raw_pos = pygame.mouse.get_pos()
    game_pos = get_game_mouse_pos()
    print(f"🖱️ Mouse - Tela: {raw_pos}, Jogo: {game_pos}")


if __name__ == "__main__":
    # Se executar diretamente este arquivo (para testes)
    print("⚠️ Executando jogo.py diretamente - use main.py para execução normal")
    
    # Inicializar pygame básico
    pygame.init()
    pygame.display.set_caption("SquareStorm - Modo Debug")
    
    # Criar superfície básica
    tela_debug = pygame.display.set_mode((LARGURA, ALTURA))
    
    # Executar jogo em modo debug
    main_game(tela_debug)