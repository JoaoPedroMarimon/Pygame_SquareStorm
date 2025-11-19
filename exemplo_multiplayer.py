#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemplo de como usar o sistema de multiplayer no SquareStorm.
Este arquivo demonstra como integrar o servidor e cliente ao jogo existente.
"""

import sys
import socket

# Importar apenas o necessário do sistema de rede
from src.network import GameServer, GameClient


def obter_ip_local():
    """Obtém o IP local da máquina."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def exemplo_servidor():
    """
    Exemplo de como criar e iniciar um servidor.
    """
    print("=== EXEMPLO: CRIANDO SERVIDOR ===\n")

    # Criar servidor
    servidor = GameServer(
        host='0.0.0.0',  # Aceita conexões de qualquer IP
        port=5555,       # Porta padrão
        max_players=4    # Máximo de 4 jogadores
    )

    # Iniciar servidor
    if servidor.start():
        print("✅ Servidor iniciado com sucesso!")
        print(f"📍 IP Local: {obter_ip_local()}")
        print(f"🔌 Porta: 5555")
        print("\nAguardando jogadores...\n")

        try:
            # Manter servidor rodando
            import time
            while True:
                info = servidor.get_server_info()
                print(f"📊 Jogadores conectados: {info['players_connected']}/{info['max_players']}")
                print(f"   Jogadores: {info['player_names']}")
                time.sleep(5)

        except KeyboardInterrupt:
            print("\n🛑 Parando servidor...")
            servidor.stop()
    else:
        print("❌ Falha ao iniciar servidor")


def exemplo_cliente():
    """
    Exemplo de como criar e conectar um cliente.
    """
    print("=== EXEMPLO: CONECTANDO COMO CLIENTE ===\n")

    # Criar cliente
    cliente = GameClient()

    # Definir callbacks para eventos
    def on_connected():
        print("✅ Conectado ao servidor!")

    def on_disconnected():
        print("👋 Desconectado do servidor")

    def on_player_joined(player):
        print(f"👤 {player.name} entrou na partida")

    def on_player_left(player):
        print(f"👋 {player.name} saiu da partida")

    def on_game_state_update(state):
        # Processar atualização de estado
        pass

    # Registrar callbacks
    cliente.set_callback('on_connected', on_connected)
    cliente.set_callback('on_disconnected', on_disconnected)
    cliente.set_callback('on_player_joined', on_player_joined)
    cliente.set_callback('on_player_left', on_player_left)
    cliente.set_callback('on_game_state_update', on_game_state_update)

    # Conectar ao servidor
    host = input("Digite o IP do servidor (ou Enter para localhost): ").strip()
    if not host:
        host = '127.0.0.1'

    nome = input("Digite seu nome (ou Enter para 'Player'): ").strip()
    if not nome:
        nome = 'Player'

    if cliente.connect(host, 5555, nome):
        print(f"✅ Conectado como {nome}!")
        print(f"🆔 ID do jogador: {cliente.local_player_id}")

        try:
            # Simular envio de inputs
            import time
            while cliente.is_connected():
                # Enviar input de exemplo
                cliente.send_player_input(
                    keys={'w': False, 'a': False, 's': False, 'd': False},
                    mouse_x=400,
                    mouse_y=300,
                    shooting=False
                )

                # Enviar ping
                cliente.send_ping()

                # Mostrar latência
                print(f"🌐 Latência: {cliente.get_latency():.1f}ms")

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n👋 Desconectando...")
            cliente.disconnect()
    else:
        print("❌ Falha ao conectar")


def exemplo_menu_multiplayer():
    """
    Exemplo de como usar o menu de multiplayer.
    NOTA: Esta função requer que você integre o menu ao jogo principal.
    Por enquanto, use os exemplos 1, 2 ou 4 para testar o sistema.
    """
    print("=== EXEMPLO: MENU MULTIPLAYER ===\n")
    print("⚠️ Este exemplo requer integração completa com o jogo.")
    print("Para testar o sistema de rede, use:")
    print("  - Opção 1: Criar servidor")
    print("  - Opção 2: Conectar como cliente")
    print("  - Opção 4: Ver pseudocódigo de integração")
    print()
    print("Para usar os menus gráficos, você precisa:")
    print("  1. Integrar ao main.py do jogo")
    print("  2. Seguir o guia em INTEGRATION_TODO.md")
    print()


def exemplo_integracao_completa():
    """
    Exemplo de integração completa no loop do jogo.
    """
    print("=== EXEMPLO: INTEGRAÇÃO COMPLETA ===\n")

    # Pseudocódigo de como integrar no loop principal do jogo

    """
    # No início do jogo (após o menu)
    if modo == "multiplayer_host":
        servidor = GameServer(...)
        servidor.start()
        cliente = GameClient()  # Host também é cliente
        cliente.connect('127.0.0.1', porta, nome)

    elif modo == "multiplayer_join":
        cliente = GameClient()
        cliente.connect(ip_servidor, porta, nome)

    # No loop principal do jogo
    while jogando:
        # 1. Processar eventos
        for evento in pygame.event.get():
            # ... processar eventos ...

        # 2. Capturar input do jogador
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        shooting = pygame.mouse.get_pressed()[0]

        # 3. Enviar input para o servidor
        if cliente and cliente.is_connected():
            input_dict = {
                'w': keys[pygame.K_w],
                'a': keys[pygame.K_a],
                's': keys[pygame.K_s],
                'd': keys[pygame.K_d]
            }
            cliente.send_player_input(input_dict, mouse_x, mouse_y, shooting)

        # 4. Atualizar interpolação dos jogadores remotos
        if cliente:
            cliente.update_interpolation(delta_time)

        # 5. Obter jogadores remotos e desenhar
        if cliente:
            jogadores_remotos = cliente.get_remote_players()
            for player_id, player in jogadores_remotos.items():
                # Desenhar jogador remoto
                pygame.draw.rect(tela, AZUL, (player.x, player.y, 40, 40))
                # Desenhar nome
                texto = fonte.render(player.name, True, BRANCO)
                tela.blit(texto, (player.x, player.y - 20))

        # 6. Desenhar seu próprio jogador (posição local)
        pygame.draw.rect(tela, VERDE, (jogador_x, jogador_y, 40, 40))

        # 7. Desenhar inimigos e bullets do estado do servidor
        if cliente:
            estado_jogo = cliente.get_game_state()

            # Desenhar inimigos
            for inimigo in estado_jogo.get('enemies', []):
                pygame.draw.rect(tela, VERMELHO,
                               (inimigo['x'], inimigo['y'], 40, 40))

            # Desenhar tiros
            for tiro in estado_jogo.get('bullets', []):
                pygame.draw.circle(tela, AMARELO,
                                 (int(tiro['x']), int(tiro['y'])), 5)

        # 8. Atualizar tela
        pygame.display.flip()
        clock.tick(60)  # Cliente roda a 60 FPS

        # 9. Enviar ping periodicamente (a cada 1 segundo)
        if cliente and time.time() - ultimo_ping > 1.0:
            cliente.send_ping()
            ultimo_ping = time.time()

    # Ao sair do jogo
    if cliente:
        cliente.disconnect()
    if servidor:
        servidor.stop()
    """

    print("Este é um pseudocódigo de como integrar.")
    print("Veja os arquivos em src/network/ para a implementação real.")


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLOS DE USO DO SISTEMA MULTIPLAYER")
    print("=" * 60)
    print()
    print("Escolha um exemplo:")
    print("1. Criar servidor")
    print("2. Conectar como cliente")
    print("3. Menu multiplayer (visual)")
    print("4. Ver pseudocódigo de integração")
    print("0. Sair")
    print()

    escolha = input("Digite o número: ").strip()

    if escolha == "1":
        exemplo_servidor()
    elif escolha == "2":
        exemplo_cliente()
    elif escolha == "3":
        exemplo_menu_multiplayer()
    elif escolha == "4":
        exemplo_integracao_completa()
    else:
        print("👋 Até logo!")
