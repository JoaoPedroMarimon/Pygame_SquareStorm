#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servidor de jogo para multiplayer LAN.
Gerencia a lógica do jogo e sincroniza o estado entre os clientes.
"""

import socket
import threading
import time
import json
from typing import Dict, List, Optional, Tuple
from .network_protocol import NetworkProtocol, PacketType


class PlayerConnection:
    """Representa uma conexão de jogador."""

    def __init__(self, player_id: int, socket: socket.socket, address: tuple):
        self.player_id = player_id
        self.socket = socket
        self.address = address
        self.player_name = f"Player{player_id}"
        self.last_ping = time.time()
        self.latency = 0.0
        self.connected = True

        # Estado do jogador
        self.x = 0
        self.y = 0
        self.health = 5
        self.alive = True
        self.score = 0

        # Input do jogador
        self.keys = {}
        self.mouse_x = 0
        self.mouse_y = 0
        self.shooting = False


class GameServer:
    """
    Servidor do jogo que gerencia múltiplas conexões e sincroniza o estado.
    """

    def __init__(self, host: str = '0.0.0.0', port: int = 5555, max_players: int = 4):
        """
        Inicializa o servidor.

        Args:
            host: Endereço IP para bind (0.0.0.0 aceita todas as interfaces)
            port: Porta para escutar
            max_players: Número máximo de jogadores
        """
        self.host = host
        self.port = port
        self.max_players = max_players

        # Socket do servidor
        self.server_socket = None
        self.running = False

        # Conexões dos jogadores
        self.players: Dict[int, PlayerConnection] = {}
        self.next_player_id = 1
        self.players_lock = threading.Lock()

        # Estado do jogo
        self.game_state = {
            'phase': 1,
            'wave': 1,
            'enemies': [],
            'bullets': [],
            'items': []
        }
        self.game_state_lock = threading.Lock()

        # Threads
        self.accept_thread = None
        self.update_thread = None

        # Configurações de sincronização
        self.tick_rate = 20  # Atualizações por segundo
        self.tick_interval = 1.0 / self.tick_rate

    def start(self) -> bool:
        """
        Inicia o servidor.

        Returns:
            True se iniciado com sucesso
        """
        try:
            # Criar socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Fazer bind
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)

            self.running = True

            # Iniciar thread de aceitação de conexões
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.accept_thread.start()

            # Iniciar thread de atualização do jogo
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

            print(f"🌐 Servidor iniciado em {self.host}:{self.port}")
            print(f"📊 Aguardando até {self.max_players} jogadores...")

            return True

        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False

    def stop(self):
        """Para o servidor."""
        print("🛑 Parando servidor...")
        self.running = False

        # Desconectar todos os jogadores
        with self.players_lock:
            for player in list(self.players.values()):
                self._disconnect_player(player.player_id)

        # Fechar socket
        if self.server_socket:
            self.server_socket.close()

        print("✅ Servidor parado")

    def _accept_connections(self):
        """Thread que aceita novas conexões."""
        while self.running:
            try:
                # Aceitar conexão
                client_socket, address = self.server_socket.accept()

                # Verificar se há espaço para mais jogadores
                with self.players_lock:
                    if len(self.players) >= self.max_players:
                        print(f"⚠️ Conexão recusada de {address}: servidor cheio")
                        client_socket.close()
                        continue

                print(f"🔗 Nova conexão de {address}")

                # Iniciar thread para lidar com este cliente
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"❌ Erro ao aceitar conexão: {e}")

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """
        Thread que lida com um cliente específico.

        Args:
            client_socket: Socket do cliente
            address: Endereço do cliente
        """
        player_id = None

        try:
            # Receber pacote de conexão
            data = self._receive_packet(client_socket)
            if not data:
                client_socket.close()
                return

            packet_type, packet_data = NetworkProtocol.parse_packet(data)

            if packet_type != PacketType.CONNECT:
                print(f"⚠️ Primeiro pacote não é CONNECT de {address}")
                client_socket.close()
                return

            # Criar jogador
            with self.players_lock:
                player_id = self.next_player_id
                self.next_player_id += 1

                player = PlayerConnection(player_id, client_socket, address)
                player.player_name = packet_data.get('player_name', f'Player{player_id}')
                self.players[player_id] = player

            print(f"✅ Jogador {player.player_name} conectado (ID: {player_id})")

            # Enviar estado inicial
            self._send_full_sync(player_id)

            # Broadcast para outros jogadores
            self._broadcast_player_joined(player_id)

            # Loop de recepção de dados
            while self.running and player.connected:
                data = self._receive_packet(client_socket)
                if not data:
                    break

                self._process_packet(player_id, data)

        except Exception as e:
            print(f"❌ Erro ao lidar com cliente {address}: {e}")
        finally:
            if player_id is not None:
                self._disconnect_player(player_id)

    def _receive_packet(self, sock: socket.socket) -> Optional[bytes]:
        """
        Recebe um pacote completo do socket.

        Args:
            sock: Socket para receber dados

        Returns:
            Dados do pacote ou None se erro
        """
        try:
            # Receber header primeiro
            header_data = sock.recv(NetworkProtocol.HEADER_SIZE)
            if not header_data or len(header_data) < NetworkProtocol.HEADER_SIZE:
                return None

            # Extrair tamanho do payload
            import struct
            _, _, payload_length = struct.unpack(
                NetworkProtocol.HEADER_FORMAT,
                header_data
            )

            # Receber payload
            payload_data = b''
            while len(payload_data) < payload_length:
                chunk = sock.recv(payload_length - len(payload_data))
                if not chunk:
                    return None
                payload_data += chunk

            return header_data + payload_data

        except Exception as e:
            return None

    def _send_packet(self, player_id: int, packet: bytes):
        """
        Envia um pacote para um jogador.

        Args:
            player_id: ID do jogador
            packet: Pacote a enviar
        """
        with self.players_lock:
            player = self.players.get(player_id)
            if not player or not player.connected:
                return

            try:
                player.socket.sendall(packet)
            except Exception as e:
                print(f"❌ Erro ao enviar para jogador {player_id}: {e}")
                player.connected = False

    def _broadcast_packet(self, packet: bytes, exclude_player: Optional[int] = None):
        """
        Envia um pacote para todos os jogadores.

        Args:
            packet: Pacote a enviar
            exclude_player: ID do jogador a excluir (opcional)
        """
        with self.players_lock:
            for player_id, player in self.players.items():
                if player_id != exclude_player and player.connected:
                    try:
                        player.socket.sendall(packet)
                    except Exception as e:
                        print(f"❌ Erro ao broadcast para jogador {player_id}: {e}")
                        player.connected = False

    def _process_packet(self, player_id: int, packet_data: bytes):
        """
        Processa um pacote recebido.

        Args:
            player_id: ID do jogador que enviou
            packet_data: Dados do pacote
        """
        parsed = NetworkProtocol.parse_packet(packet_data)
        if not parsed:
            return

        packet_type, data = parsed

        # Processar diferentes tipos de pacotes
        if packet_type == PacketType.PING:
            # Responder com PONG
            pong = NetworkProtocol.create_pong_packet(data.get('timestamp', 0))
            self._send_packet(player_id, pong)

        elif packet_type == PacketType.PLAYER_INPUT:
            # Atualizar input do jogador
            self._update_player_input(player_id, data)

        elif packet_type == PacketType.DISCONNECT:
            # Jogador se desconectou
            self._disconnect_player(player_id)

    def _update_player_input(self, player_id: int, data: Dict):
        """
        Atualiza o input de um jogador.

        Args:
            player_id: ID do jogador
            data: Dados de input
        """
        with self.players_lock:
            player = self.players.get(player_id)
            if not player:
                return

            player.keys = data.get('keys', {})
            player.mouse_x = data.get('mouse_x', 0)
            player.mouse_y = data.get('mouse_y', 0)
            player.shooting = data.get('shooting', False)

    def _disconnect_player(self, player_id: int):
        """
        Desconecta um jogador.

        Args:
            player_id: ID do jogador
        """
        with self.players_lock:
            player = self.players.get(player_id)
            if not player:
                return

            player.connected = False

            try:
                player.socket.close()
            except:
                pass

            del self.players[player_id]

        print(f"👋 Jogador {player_id} desconectado")

        # Broadcast desconexão
        packet = NetworkProtocol.create_disconnect_packet(player_id)
        self._broadcast_packet(packet)

    def _send_full_sync(self, player_id: int):
        """
        Envia sincronização completa para um jogador.

        Args:
            player_id: ID do jogador
        """
        # Preparar dados de todos os jogadores
        players_data = []
        with self.players_lock:
            for pid, player in self.players.items():
                players_data.append({
                    'id': pid,
                    'name': player.player_name,
                    'x': player.x,
                    'y': player.y,
                    'health': player.health,
                    'alive': player.alive,
                    'score': player.score
                })

        # Preparar estado completo
        with self.game_state_lock:
            full_state = {
                'player_id': player_id,  # Informar qual é o ID deste jogador
                'players': players_data,
                'game_state': self.game_state.copy()
            }

        packet = NetworkProtocol.create_packet(PacketType.FULL_SYNC, full_state)
        self._send_packet(player_id, packet)

    def _broadcast_player_joined(self, player_id: int):
        """
        Notifica todos sobre um novo jogador.

        Args:
            player_id: ID do jogador que entrou
        """
        with self.players_lock:
            player = self.players.get(player_id)
            if not player:
                return

            player_data = {
                'id': player_id,
                'name': player.player_name,
                'x': player.x,
                'y': player.y,
                'health': player.health,
                'alive': player.alive
            }

        packet = NetworkProtocol.create_player_update_packet(player_data)
        self._broadcast_packet(packet, exclude_player=player_id)

    def _update_loop(self):
        """Loop principal de atualização do servidor."""
        last_update = time.time()

        while self.running:
            current_time = time.time()
            delta_time = current_time - last_update

            if delta_time >= self.tick_interval:
                # Atualizar lógica do jogo
                self._update_game_logic(delta_time)

                # Sincronizar estado com clientes
                self._sync_game_state()

                last_update = current_time
            else:
                # Dormir um pouco para não usar 100% da CPU
                time.sleep(0.001)

    def _update_game_logic(self, delta_time: float):
        """
        Atualiza a lógica do jogo no servidor.

        Args:
            delta_time: Tempo desde a última atualização
        """
        # TODO: Implementar lógica do jogo
        # - Mover jogadores baseado no input
        # - Atualizar inimigos
        # - Detectar colisões
        # - etc.
        pass

    def _sync_game_state(self):
        """Sincroniza o estado do jogo com todos os clientes."""
        # Preparar dados dos jogadores
        players_data = []
        with self.players_lock:
            for pid, player in self.players.items():
                players_data.append({
                    'id': pid,
                    'x': player.x,
                    'y': player.y,
                    'health': player.health,
                    'alive': player.alive
                })

        # Criar pacote de estado
        with self.game_state_lock:
            state_data = {
                'players': players_data,
                'enemies': self.game_state.get('enemies', []),
                'bullets': self.game_state.get('bullets', [])
            }

        packet = NetworkProtocol.create_game_state_packet(state_data)
        self._broadcast_packet(packet)

    def get_server_info(self) -> Dict:
        """
        Retorna informações sobre o servidor.

        Returns:
            Dicionário com informações do servidor
        """
        with self.players_lock:
            return {
                'host': self.host,
                'port': self.port,
                'running': self.running,
                'players_connected': len(self.players),
                'max_players': self.max_players,
                'player_names': [p.player_name for p in self.players.values()]
            }
