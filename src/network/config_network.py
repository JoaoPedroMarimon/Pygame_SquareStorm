#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurações de rede para o multiplayer.
"""

# Configurações do servidor
DEFAULT_SERVER_PORT = 5555
DEFAULT_MAX_PLAYERS = 4

# Configurações de sincronização
TICK_RATE = 20  # Atualizações por segundo
SEND_RATE = 20  # Envios por segundo

# Timeouts
CONNECTION_TIMEOUT = 5.0  # Segundos
PING_INTERVAL = 1.0  # Intervalo entre pings (segundos)

# Interpolação
INTERPOLATION_SPEED = 0.3  # Velocidade de interpolação (0-1)

# Tamanhos de buffer
RECEIVE_BUFFER_SIZE = 4096
SEND_BUFFER_SIZE = 4096

# Reconexão
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY = 2.0  # Segundos entre tentativas
