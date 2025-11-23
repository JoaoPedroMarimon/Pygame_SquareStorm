#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase multiplayer simples para testes.
Loop de jogo adaptado para modo multiplayer LAN.
"""

import pygame
import math
from src.config import *
from src.entities.quadrado import Quadrado
from src.network import GameClient
from src.utils.display_manager import present_frame, convert_mouse_position

def jogar_fase_multiplayer_simples(tela, relogio, cliente, nome_jogador):
    """
    Loop de jogo simplificado para modo multiplayer.

    Args:
        tela: Superfície do Pygame
        relogio: Relógio do Pygame
        cliente: Instância do GameClient
        nome_jogador: Nome do jogador local

    Returns:
        "menu" para voltar ao menu
    """
    print(f"[MULTIPLAYER] Iniciando fase multiplayer como {nome_jogador}")

    # Criar jogador local (apenas visual inicial)
    jogador_x = LARGURA // 2
    jogador_y = ALTURA_JOGO // 2
    jogador_cor = VERDE

    # Fonte para texto
    fonte = pygame.font.SysFont("Arial", 20)
    fonte_grande = pygame.font.SysFont("Arial", 36, True)

    # Estado do jogo
    rodando = True
    paused = False

    # Cores para jogadores remotos
    cores_remotos = [AZUL, CIANO, ROXO, LARANJA]

    print(f"[MULTIPLAYER] Fase multiplayer iniciada. ID local: {cliente.local_player_id}")

    while rodando:
        delta_time = relogio.tick(60) / 1000.0

        # 1. PROCESSAR EVENTOS
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "menu"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return "menu"
                if evento.key == pygame.K_p:
                    paused = not paused

        if paused:
            # Mostrar tela de pausa
            tela.fill(PRETO)
            texto = fonte_grande.render("PAUSADO - P para continuar", True, BRANCO)
            rect = texto.get_rect(center=(LARGURA // 2, ALTURA // 2))
            tela.blit(texto, rect)
            present_frame()
            continue

        # 2. CAPTURAR INPUT LOCAL
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = convert_mouse_position(pygame.mouse.get_pos())
        shooting = pygame.mouse.get_pressed()[0]

        # Movimento local (predição do cliente)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            jogador_y -= VELOCIDADE_JOGADOR
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            jogador_y += VELOCIDADE_JOGADOR
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            jogador_x -= VELOCIDADE_JOGADOR
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            jogador_x += VELOCIDADE_JOGADOR

        # Limitar bounds
        jogador_x = max(TAMANHO_QUADRADO // 2, min(LARGURA - TAMANHO_QUADRADO // 2, jogador_x))
        jogador_y = max(TAMANHO_QUADRADO // 2, min(ALTURA_JOGO - TAMANHO_QUADRADO // 2, jogador_y))

        # 3. ENVIAR INPUT PARA SERVIDOR
        if cliente.is_connected():
            keys_dict = {
                'w': keys[pygame.K_w] or keys[pygame.K_UP],
                'a': keys[pygame.K_a] or keys[pygame.K_LEFT],
                's': keys[pygame.K_s] or keys[pygame.K_DOWN],
                'd': keys[pygame.K_d] or keys[pygame.K_RIGHT]
            }
            try:
                cliente.send_player_input(keys_dict, mouse_x, mouse_y, shooting)
            except Exception as e:
                print(f" Erro ao enviar input: {e}")
                return "menu"
        else:
            # Perdeu conexão
            print(" Conexão perdida com o servidor")
            return "menu"

        # 4. ATUALIZAR INTERPOLAÇÃO DOS REMOTOS
        cliente.update_interpolation(delta_time)

        # 5. OBTER JOGADORES REMOTOS
        jogadores_remotos = cliente.get_remote_players()

        # 6. DESENHAR TUDO
        # Fundo
        tela.fill((10, 0, 30))

        # Grid de fundo
        for i in range(0, LARGURA, 40):
            pygame.draw.line(tela, (20, 0, 40), (i, 0), (i, ALTURA_JOGO), 1)
        for i in range(0, ALTURA_JOGO, 40):
            pygame.draw.line(tela, (20, 0, 40), (0, i), (LARGURA, i), 1)

        # Desenhar jogador local
        pygame.draw.rect(tela, jogador_cor,
                        (jogador_x - TAMANHO_QUADRADO // 2,
                         jogador_y - TAMANHO_QUADRADO // 2,
                         TAMANHO_QUADRADO,
                         TAMANHO_QUADRADO))

        # Nome acima do jogador local
        nome_surface = fonte.render(f"{nome_jogador} (Você)", True, AMARELO)
        nome_rect = nome_surface.get_rect(center=(jogador_x, jogador_y - 30))
        tela.blit(nome_surface, nome_rect)

        # Desenhar jogadores remotos
        cor_index = 0
        for player_id, player in jogadores_remotos.items():
            cor_remoto = cores_remotos[cor_index % len(cores_remotos)]
            cor_index += 1

            # Quadrado do jogador remoto
            pygame.draw.rect(tela, cor_remoto,
                           (player.x - TAMANHO_QUADRADO // 2,
                            player.y - TAMANHO_QUADRADO // 2,
                            TAMANHO_QUADRADO,
                            TAMANHO_QUADRADO))

            # Contorno
            pygame.draw.rect(tela, BRANCO,
                           (player.x - TAMANHO_QUADRADO // 2,
                            player.y - TAMANHO_QUADRADO // 2,
                            TAMANHO_QUADRADO,
                            TAMANHO_QUADRADO), 2)

            # Nome acima
            nome_surface = fonte.render(player.name, True, cor_remoto)
            nome_rect = nome_surface.get_rect(center=(player.x, player.y - 30))
            tela.blit(nome_surface, nome_rect)

        # HUD
        hud_y = ALTURA_JOGO
        pygame.draw.rect(tela, CINZA_ESCURO, (0, hud_y, LARGURA, ALTURA_HUD))

        # Informações do multiplayer
        info_x = 20
        info_y = hud_y + 10

        # Latência
        latencia = cliente.get_latency()
        cor_latencia = VERDE if latencia < 50 else (AMARELO if latencia < 100 else VERMELHO)
        texto_latencia = fonte.render(f"Latência: {latencia:.0f}ms", True, cor_latencia)
        tela.blit(texto_latencia, (info_x, info_y))

        # Jogadores conectados
        num_jogadores = len(jogadores_remotos) + 1  # +1 para o jogador local
        texto_jogadores = fonte.render(f"Jogadores: {num_jogadores}", True, BRANCO)
        tela.blit(texto_jogadores, (info_x + 200, info_y))

        # ID do jogador
        texto_id = fonte.render(f"Sua ID: {cliente.local_player_id}", True, CIANO)
        tela.blit(texto_id, (info_x + 400, info_y))

        # Instruções
        instrucoes_y = info_y + 30
        texto_instrucoes = fonte.render("ESC: Menu | P: Pausar | WASD: Mover", True, (150, 150, 150))
        tela.blit(texto_instrucoes, (info_x, instrucoes_y))

        # 7. ATUALIZAR DISPLAY
        present_frame()

    return "menu"
