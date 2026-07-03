#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cliente de jogo para multiplayer LAN.
Conecta ao servidor e sincroniza o estado do jogo.
"""

import socket
import threading
import time
from typing import Dict, Optional, Callable, Any
from .network_protocol import NetworkProtocol, PacketType


class RemotePlayer:
    """Representa um jogador remoto."""

    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name

        # Posição atual
        self.x = 0
        self.y = 0

        # Estado
        self.health = 5
        self.alive = True
        self.score = 0

        # Interpolação
        self.target_x = 0
        self.target_y = 0
        self.interpolation_speed = 0.3


class GameClient:
    """
    Cliente do jogo que conecta ao servidor.
    """

    def __init__(self):
        """Inicializa o cliente."""
        # Socket
        self.socket = None
        self.connected = False

        # Informações do servidor
        self.server_host = None
        self.server_port = None

        # ID do jogador local
        self.local_player_id = None
        self.local_player_name = "Player"
        self.local_player_pos = None  # (x, y) posição inicial recebida do servidor

        # Jogadores remotos
        self.remote_players: Dict[int, RemotePlayer] = {}
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

        # Thread de recepção
        self.receive_thread = None

        # Callbacks para eventos
        self.callbacks = {
            'on_connected': None,
            'on_disconnected': None,
            'on_player_joined': None,
            'on_player_left': None,
            'on_game_state_update': None,
            'on_game_start': None,  # Callback quando o host inicia a partida
            'on_team_status': None,  # Callback quando recebe status de times
            'on_all_ready': None,  # Callback quando todos escolheram time
            'on_minigame_action': None,  # Callback para ações de minigame
        }

        # Fila thread-safe de ações de minigame recebidas
        self.minigame_actions = []
        self.minigame_actions_lock = threading.Lock()

        # Status de seleção de times
        self.team_status = {}  # {player_id: {'team': 'T'/'Q', 'name': 'nome'}}

        # Medição de latência
        self.latency = 0.0
        self.last_ping_time = 0.0

    def connect(self, host: str, port: int, player_name: str) -> bool:
        """
        Conecta ao servidor.

        Args:
            host: Endereço do servidor
            port: Porta do servidor
            player_name: Nome do jogador

        Returns:
            True se conectado com sucesso
        """
        try:
            print(f"🔗 Conectando ao servidor {host}:{port}...")

            # Criar socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # Timeout de 10 segundos para conexão

            # Conectar
            self.socket.connect((host, port))

            self.server_host = host
            self.server_port = port
            self.local_player_name = player_name
            self.connected = True

            print(f"✅ Conectado ao servidor!")

            # Remover timeout após conexão
            self.socket.settimeout(None)

            # Enviar pacote de conexão
            connect_packet = NetworkProtocol.create_connect_packet(player_name)
            self.socket.sendall(connect_packet)

            # Iniciar thread de recepção
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            # Chamar callback
            if self.callbacks['on_connected']:
                self.callbacks['on_connected']()

            return True

        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            if "timed out" in str(e):
                print("⚠️ FIREWALL: Verifique se a porta está liberada no firewall do host!")
                print("   Windows: Painel de Controle > Sistema e Segurança > Firewall do Windows")
                print(f"   Libere a porta {port} TCP para entrada")
            self.connected = False
            return False

    def disconnect(self):
        """Desconecta do servidor."""
        if not self.connected:
            return

        print("👋 Desconectando do servidor...")

        try:
            # Enviar pacote de desconexão
            if self.local_player_id:
                disconnect_packet = NetworkProtocol.create_disconnect_packet(self.local_player_id)
                self.socket.sendall(disconnect_packet)
        except:
            pass

        self.connected = False

        # Fechar socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        # Chamar callback
        if self.callbacks['on_disconnected']:
            self.callbacks['on_disconnected']()

        print("✅ Desconectado")

    def _receive_loop(self):
        """Loop de recepção de pacotes."""
        while self.connected:
            try:
                # Receber pacote
                packet_data = self._receive_packet()
                if not packet_data:
                    print("⚠️ Conexão perdida com o servidor")
                    break

                # Processar pacote
                self._process_packet(packet_data)

            except Exception as e:
                if self.connected:
                    print(f"❌ Erro na recepção: {e}")
                break

        # Desconectar se ainda estiver conectado
        if self.connected:
            self.connected = False
            if self.callbacks['on_disconnected']:
                self.callbacks['on_disconnected']()

    def _receive_packet(self) -> Optional[bytes]:
        """
        Recebe um pacote completo do socket.

        Returns:
            Dados do pacote ou None se erro
        """
        try:
            # Receber header
            header_data = self.socket.recv(NetworkProtocol.HEADER_SIZE)
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
                chunk = self.socket.recv(payload_length - len(payload_data))
                if not chunk:
                    return None
                payload_data += chunk

            return header_data + payload_data

        except Exception as e:
            return None

    def _process_packet(self, packet_data: bytes):
        """
        Processa um pacote recebido.

        Args:
            packet_data: Dados do pacote
        """
        parsed = NetworkProtocol.parse_packet(packet_data)
        if not parsed:
            return

        packet_type, data = parsed

        # Processar diferentes tipos de pacotes
        if packet_type == PacketType.FULL_SYNC:
            # Sincronização completa
            self._handle_full_sync(data)

        elif packet_type == PacketType.GAME_STATE:
            # Atualização de estado
            self._handle_game_state_update(data)

        elif packet_type == PacketType.PLAYER_UPDATE:
            # Atualização de jogador
            self._handle_player_update(data)

        elif packet_type == PacketType.DISCONNECT:
            # Jogador desconectou
            self._handle_player_disconnect(data)

        elif packet_type == PacketType.PONG:
            # Resposta de ping
            self._handle_pong(data)

        elif packet_type == PacketType.GAME_START:
            # Host iniciou a partida
            self._handle_game_start(data)

        elif packet_type == PacketType.TEAM_STATUS:
            # Status de seleção de times
            self._handle_team_status(data)

        elif packet_type == PacketType.ALL_READY:
            # Todos escolheram time
            self._handle_all_ready(data)

        elif packet_type == PacketType.MINIGAME_ACTION:
            # Ação de minigame recebida de outro jogador
            self._handle_minigame_action(data)

    def _handle_full_sync(self, data: Dict):
        """
        Processa sincronização completa.

        Args:
            data: Dados da sincronização
        """
        # Armazenar ID do jogador local
        self.local_player_id = data.get('player_id')
        print(f"🎮 ID do jogador local: {self.local_player_id}")

        # Processar jogadores
        with self.players_lock:
            self.remote_players.clear()

            for player_data in data.get('players', []):
                player_id = player_data['id']

                # Armazenar posição do jogador local
                if player_id == self.local_player_id:
                    self.local_player_pos = (player_data['x'], player_data['y'])
                    continue

                player = RemotePlayer(player_id, player_data['name'])
                player.x = player_data['x']
                player.y = player_data['y']
                player.target_x = player.x
                player.target_y = player.y
                player.health = player_data['health']
                player.alive = player_data['alive']
                player.score = player_data.get('score', 0)

                self.remote_players[player_id] = player

        # Processar estado do jogo
        with self.game_state_lock:
            self.game_state = data.get('game_state', {})

        print(f"✅ Sincronização completa recebida ({len(self.remote_players)} jogadores remotos)")

    def _handle_game_state_update(self, data: Dict):
        """
        Processa atualização de estado do jogo.

        Args:
            data: Dados do estado
        """
        # Atualizar jogadores
        with self.players_lock:
            for player_data in data.get('players', []):
                player_id = player_data['id']

                # Ignorar jogador local (cliente-autoritativo: nós já sabemos nossa posição)
                if player_id == self.local_player_id:
                    continue

                player = self.remote_players.get(player_id)
                if player:
                    # Atualizar posição alvo (para interpolação)
                    player.target_x = player_data['x']
                    player.target_y = player_data['y']
                    player.health = player_data['health']
                    player.alive = player_data['alive']

        # Atualizar estado do jogo
        with self.game_state_lock:
            if 'enemies' in data:
                self.game_state['enemies'] = data['enemies']
            if 'bullets' in data:
                self.game_state['bullets'] = data['bullets']

        # Chamar callback
        if self.callbacks['on_game_state_update']:
            self.callbacks['on_game_state_update'](data)

    def _handle_player_update(self, data: Dict):
        """
        Processa atualização de um jogador.

        Args:
            data: Dados do jogador
        """
        player_id = data.get('id')
        if player_id == self.local_player_id:
            return

        with self.players_lock:
            if player_id not in self.remote_players:
                # Novo jogador
                player = RemotePlayer(player_id, data.get('name', f'Player{player_id}'))
                player.x = data.get('x', 0)
                player.y = data.get('y', 0)
                player.target_x = player.x
                player.target_y = player.y
                player.health = data.get('health', 5)
                player.alive = data.get('alive', True)

                self.remote_players[player_id] = player

                print(f"👤 Jogador {player.name} entrou na partida")

                # Chamar callback
                if self.callbacks['on_player_joined']:
                    self.callbacks['on_player_joined'](player)
            else:
                # Atualizar jogador existente
                player = self.remote_players[player_id]
                player.target_x = data.get('x', player.x)
                player.target_y = data.get('y', player.y)
                player.health = data.get('health', player.health)
                player.alive = data.get('alive', player.alive)

    def _handle_player_disconnect(self, data: Dict):
        """
        Processa desconexão de um jogador.

        Args:
            data: Dados da desconexão
        """
        player_id = data.get('player_id')

        with self.players_lock:
            if player_id in self.remote_players:
                player = self.remote_players[player_id]
                del self.remote_players[player_id]

                print(f"👋 Jogador {player.name} saiu da partida")

                # Chamar callback
                if self.callbacks['on_player_left']:
                    self.callbacks['on_player_left'](player)

    def _handle_pong(self, data: Dict):
        """
        Processa resposta de ping.

        Args:
            data: Dados do pong
        """
        timestamp = data.get('timestamp', 0)
        if timestamp > 0:
            self.latency = (time.time() - timestamp) * 1000  # Em milissegundos

    def _handle_game_start(self, data: Dict):
        """
        Processa sinal de início de partida enviado pelo host.

        Args:
            data: Dados do início
        """
        print(f"[CLIENT] 🎮 Host iniciou a partida! {data.get('message', '')}")

        # Chamar callback
        if self.callbacks['on_game_start']:
            self.callbacks['on_game_start'](data)

    def _handle_team_status(self, data: Dict):
        """
        Processa status de seleção de times.

        Args:
            data: Dados com 'players' contendo as seleções
        """
        self.team_status = data.get('players', {})
        print(f"[CLIENT] Status de times atualizado: {len(self.team_status)} jogadores escolheram")

        # Chamar callback
        if self.callbacks['on_team_status']:
            self.callbacks['on_team_status'](self.team_status)

    def _handle_all_ready(self, data: Dict):
        """
        Processa sinal de que todos os jogadores escolheram time.

        Args:
            data: Dados do evento
        """
        print("[CLIENT] ✅ Todos os jogadores escolheram time! Iniciando...")

        # Chamar callback
        if self.callbacks['on_all_ready']:
            self.callbacks['on_all_ready'](data)

    def _handle_minigame_action(self, data: Dict):
        """
        Processa ação de minigame recebida de outro jogador.

        Args:
            data: Dados da ação
        """
        with self.minigame_actions_lock:
            self.minigame_actions.append(data)

        if self.callbacks.get('on_minigame_action'):
            self.callbacks['on_minigame_action'](data)

    def send_minigame_action(self, action_data: dict):
        """
        Envia uma ação de minigame para o servidor (que faz relay para os outros).

        Args:
            action_data: Dados da ação (ex: {'action': 'aim_shot', 'mx': 100, 'my': 200})
        """
        if not self.connected or not self.local_player_id:
            return

        try:
            packet = NetworkProtocol.create_minigame_action_packet(
                self.local_player_id, action_data
            )
            self.socket.sendall(packet)
        except Exception as e:
            print(f"Erro ao enviar minigame action: {e}")
            self.connected = False

    def get_minigame_actions(self):
        """Retorna e limpa a fila de ações de minigame recebidas."""
        with self.minigame_actions_lock:
            actions = list(self.minigame_actions)
            self.minigame_actions.clear()
            return actions

    def send_team_selection(self, team: str, player_name: str, classe=None):
        """
        Envia a seleção de time (e classe) para o servidor.

        Args:
            team: Time escolhido ('T' ou 'Q')
            player_name: Nome do jogador
            classe: Classe escolhida (para os bots não repetirem)
        """
        if not self.connected or not self.local_player_id:
            return

        try:
            packet = NetworkProtocol.create_team_select_packet(
                self.local_player_id,
                team,
                player_name,
                classe
            )
            self.socket.sendall(packet)
            print(f"[CLIENT] Enviado seleção de time: {team}")
        except Exception as e:
            print(f"❌ Erro ao enviar seleção de time: {e}")
            self.connected = False

    def get_team_status(self) -> Dict:
        """Retorna o status atual de seleção de times."""
        return self.team_status

    def send_player_input(self, keys: Dict[str, bool], mouse_x: int, mouse_y: int, shooting: bool,
                          x: Optional[float] = None, y: Optional[float] = None):
        """
        Envia input do jogador para o servidor.

        Modelo cliente-autoritativo: além das teclas, enviamos a posição real
        (x, y) calculada localmente. O servidor apenas repassa essa posição aos
        outros jogadores, sem re-simular o movimento. Assim a posição que cada
        jogador vê de si mesmo é exatamente a que os outros recebem.

        Args:
            keys: Estado das teclas
            mouse_x: Posição X do mouse
            mouse_y: Posição Y do mouse
            shooting: Se está atirando
            x: Posição X autoritativa do jogador (opcional)
            y: Posição Y autoritativa do jogador (opcional)
        """
        if not self.connected or not self.local_player_id:
            return

        try:
            packet = NetworkProtocol.create_player_input_packet(
                self.local_player_id,
                keys,
                mouse_x,
                mouse_y,
                shooting,
                x,
                y
            )
            self.socket.sendall(packet)
        except Exception as e:
            print(f"❌ Erro ao enviar input: {e}")
            self.connected = False

    def send_ping(self):
        """Envia um ping para medir latência."""
        if not self.connected:
            return

        try:
            self.last_ping_time = time.time()
            packet = NetworkProtocol.create_ping_packet()
            self.socket.sendall(packet)
        except Exception as e:
            print(f"❌ Erro ao enviar ping: {e}")

    def update_interpolation(self, delta_time: float):
        """
        Atualiza interpolação dos jogadores remotos.

        Args:
            delta_time: Tempo desde a última atualização (em segundos)
        """
        with self.players_lock:
            for player in self.remote_players.values():
                # Interpolar posição
                dx = player.target_x - player.x
                dy = player.target_y - player.y

                # Mover em direção ao alvo
                player.x += dx * player.interpolation_speed
                player.y += dy * player.interpolation_speed

    def set_callback(self, event: str, callback: Callable):
        """
        Define um callback para um evento.

        Args:
            event: Nome do evento
            callback: Função a ser chamada
        """
        if event in self.callbacks:
            self.callbacks[event] = callback

    def get_remote_players(self) -> Dict[int, RemotePlayer]:
        """
        Retorna os jogadores remotos.

        Returns:
            Dicionário de jogadores remotos
        """
        with self.players_lock:
            return self.remote_players.copy()

    def get_game_state(self) -> Dict:
        """
        Retorna o estado do jogo.

        Returns:
            Dicionário com o estado do jogo
        """
        with self.game_state_lock:
            return self.game_state.copy()

    def is_connected(self) -> bool:
        """
        Verifica se está conectado.

        Returns:
            True se conectado
        """
        return self.connected

    def get_latency(self) -> float:
        """
        Retorna a latência atual.

        Returns:
            Latência em milissegundos
        """
        return self.latency
