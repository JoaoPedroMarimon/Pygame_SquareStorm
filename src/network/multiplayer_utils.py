#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilidades compartilhadas pelos minigames em modo multiplayer.

O problema central que estas funções resolvem:

Cada cliente montava a sua lista de jogadores começando pelo jogador LOCAL e
depois adicionando os remotos. Como o jogador local é diferente em cada máquina,
a lista ficava em ordens diferentes em cada cliente. Qualquer lógica que dependa
da ordem/índice (sorteio de times com seed, brackets, spawn points, turnos)
ficava dessincronizada — cada máquina achava que outro jogador estava em outro
time/turno/posição.

A solução é montar a lista de humanos em uma ordem DETERMINÍSTICA, igual em todos
os clientes: ordenada pelo player_id (que o servidor atribui e é o mesmo em toda
a rede). Assim, com o mesmo seed, todo cliente produz exatamente o mesmo sorteio.
"""

from typing import List, Optional, Tuple


def ordenar_humanos(cliente, nome_jogador: str) -> List[Tuple[Optional[int], str, bool]]:
    """
    Retorna a lista de jogadores humanos em ordem determinística (ordenada por
    player_id), idêntica em todos os clientes.

    Args:
        cliente: GameClient (ou None em single-player)
        nome_jogador: nome do jogador local

    Returns:
        Lista de tuplas (player_id, nome, is_local). Em single-player retorna
        apenas o jogador local com player_id 0.
    """
    if cliente is None:
        return [(0, nome_jogador, True)]

    local_id = cliente.local_player_id if cliente.local_player_id is not None else 0

    humanos: List[Tuple[Optional[int], str, bool]] = [(local_id, nome_jogador, True)]
    for pid, rp in cliente.get_remote_players().items():
        humanos.append((pid, rp.name, False))

    # Ordenar por player_id -> mesma ordem em todas as máquinas
    humanos.sort(key=lambda t: (t[0] is None, t[0] if t[0] is not None else 0))
    return humanos


def sou_host(cliente) -> bool:
    """
    Indica se ESTA máquina é a autoridade do jogo (o host).

    O host é quem abriu o servidor; como ele conecta primeiro, recebe o menor
    player_id da rede. Em single-player (cliente None) a própria máquina é a
    autoridade.

    No modelo host-autoritativo, só o host simula bots, dano, mortes e placar;
    os clientes apenas renderizam o estado recebido e enviam o próprio input.
    Isso evita que cada máquina simule de forma independente e divirja
    (bots fazendo coisas diferentes, jogador vivo numa tela e morto na outra).
    """
    if cliente is None:
        return True

    ids = [cliente.local_player_id]
    ids += list(cliente.get_remote_players().keys())
    ids = [i for i in ids if i is not None]
    if not ids:
        return True
    return cliente.local_player_id == min(ids)
