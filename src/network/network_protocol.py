#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Protocolo de rede para o multiplayer.
Define os tipos de pacotes e métodos de serialização/deserialização.
"""

import json
import struct
from enum import IntEnum
from typing import Dict, Any, Optional

class PacketType(IntEnum):
    """Tipos de pacotes de rede."""
    # Conexão
    CONNECT = 0
    DISCONNECT = 1
    PING = 2
    PONG = 3

    # Estado do jogo
    GAME_STATE = 10
    PLAYER_INPUT = 11
    PLAYER_UPDATE = 12

    # Entidades
    ENEMY_UPDATE = 20
    BULLET_FIRED = 21
    BULLET_HIT = 22

    # Eventos
    PLAYER_DIED = 30
    PLAYER_RESPAWN = 31
    WAVE_START = 32
    WAVE_END = 33
    PHASE_COMPLETE = 34
    GAME_START = 35  # Host inicia a partida

    # Sincronização
    FULL_SYNC = 40
    PARTIAL_SYNC = 41


class NetworkProtocol:
    """Gerencia a serialização e deserialização de pacotes de rede."""

    # Versão do protocolo (para compatibilidade futura)
    PROTOCOL_VERSION = 1

    # Tamanho máximo de um pacote (64KB)
    MAX_PACKET_SIZE = 65536

    # Header: [version:1byte][type:1byte][length:4bytes]
    HEADER_SIZE = 6
    HEADER_FORMAT = '!BBI'  # unsigned char, unsigned char, unsigned int

    @staticmethod
    def create_packet(packet_type: PacketType, data: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Cria um pacote de rede.

        Args:
            packet_type: Tipo do pacote
            data: Dados a serem enviados (serão serializados em JSON)

        Returns:
            Pacote serializado em bytes
        """
        # Serializar os dados para JSON
        if data is None:
            data = {}

        json_data = json.dumps(data, separators=(',', ':')).encode('utf-8')

        # Verificar tamanho
        if len(json_data) > NetworkProtocol.MAX_PACKET_SIZE - NetworkProtocol.HEADER_SIZE:
            raise ValueError(f"Pacote muito grande: {len(json_data)} bytes")

        # Criar header
        header = struct.pack(
            NetworkProtocol.HEADER_FORMAT,
            NetworkProtocol.PROTOCOL_VERSION,
            int(packet_type),
            len(json_data)
        )

        # Retornar header + dados
        return header + json_data

    @staticmethod
    def parse_packet(packet_data: bytes) -> Optional[tuple]:
        """
        Analisa um pacote de rede recebido.

        Args:
            packet_data: Dados do pacote em bytes

        Returns:
            Tupla (packet_type, data) ou None se inválido
        """
        # Verificar tamanho mínimo
        if len(packet_data) < NetworkProtocol.HEADER_SIZE:
            return None

        # Ler header
        try:
            version, packet_type, data_length = struct.unpack(
                NetworkProtocol.HEADER_FORMAT,
                packet_data[:NetworkProtocol.HEADER_SIZE]
            )
        except struct.error:
            return None

        # Verificar versão do protocolo
        if version != NetworkProtocol.PROTOCOL_VERSION:
            print(f"⚠️ Versão de protocolo incompatível: {version} != {NetworkProtocol.PROTOCOL_VERSION}")
            return None

        # Verificar tamanho dos dados
        if len(packet_data) < NetworkProtocol.HEADER_SIZE + data_length:
            return None

        # Extrair dados JSON
        json_data = packet_data[NetworkProtocol.HEADER_SIZE:NetworkProtocol.HEADER_SIZE + data_length]

        try:
            data = json.loads(json_data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

        return (PacketType(packet_type), data)

    @staticmethod
    def create_connect_packet(player_name: str) -> bytes:
        """Cria um pacote de conexão."""
        return NetworkProtocol.create_packet(PacketType.CONNECT, {
            'player_name': player_name
        })

    @staticmethod
    def create_disconnect_packet(player_id: int) -> bytes:
        """Cria um pacote de desconexão."""
        return NetworkProtocol.create_packet(PacketType.DISCONNECT, {
            'player_id': player_id
        })

    @staticmethod
    def create_ping_packet() -> bytes:
        """Cria um pacote de ping."""
        import time
        return NetworkProtocol.create_packet(PacketType.PING, {
            'timestamp': time.time()
        })

    @staticmethod
    def create_pong_packet(timestamp: float) -> bytes:
        """Cria um pacote de pong."""
        return NetworkProtocol.create_packet(PacketType.PONG, {
            'timestamp': timestamp
        })

    @staticmethod
    def create_player_input_packet(player_id: int, keys: Dict[str, bool],
                                   mouse_x: int, mouse_y: int,
                                   shooting: bool) -> bytes:
        """Cria um pacote de input do jogador."""
        return NetworkProtocol.create_packet(PacketType.PLAYER_INPUT, {
            'player_id': player_id,
            'keys': keys,
            'mouse_x': mouse_x,
            'mouse_y': mouse_y,
            'shooting': shooting
        })

    @staticmethod
    def create_game_state_packet(state: Dict[str, Any]) -> bytes:
        """Cria um pacote de estado completo do jogo."""
        return NetworkProtocol.create_packet(PacketType.GAME_STATE, state)

    @staticmethod
    def create_player_update_packet(player_data: Dict[str, Any]) -> bytes:
        """Cria um pacote de atualização de jogador."""
        return NetworkProtocol.create_packet(PacketType.PLAYER_UPDATE, player_data)

    @staticmethod
    def create_enemy_update_packet(enemies_data: list) -> bytes:
        """Cria um pacote de atualização de inimigos."""
        return NetworkProtocol.create_packet(PacketType.ENEMY_UPDATE, {
            'enemies': enemies_data
        })

    @staticmethod
    def create_bullet_fired_packet(bullet_data: Dict[str, Any]) -> bytes:
        """Cria um pacote de tiro disparado."""
        return NetworkProtocol.create_packet(PacketType.BULLET_FIRED, bullet_data)

    @staticmethod
    def create_bullet_hit_packet(bullet_id: int, target_id: int,
                                 target_type: str) -> bytes:
        """Cria um pacote de tiro acertado."""
        return NetworkProtocol.create_packet(PacketType.BULLET_HIT, {
            'bullet_id': bullet_id,
            'target_id': target_id,
            'target_type': target_type
        })
