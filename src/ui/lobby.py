#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tela de Lobby MODERNA para aguardar jogadores no modo multiplayer.
Versão redesenhada com customização de personagem e interface bonita.
"""

import pygame
import math
import random
from src.config import *
from src.utils.display_manager import present_frame, convert_mouse_position


def obter_ip_local_simples():
    """Obtém o IP local de forma simples."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def desenhar_card(tela, rect, cor_fundo, cor_borda, titulo, fonte_titulo):
    """Desenha um card moderno com sombra e bordas arredondadas."""
    # Sombra
    sombra = pygame.Rect(rect.x + 5, rect.y + 5, rect.width, rect.height)
    pygame.draw.rect(tela, (10, 10, 20), sombra, 0, 15)

    # Card
    pygame.draw.rect(tela, cor_fundo, rect, 0, 15)
    pygame.draw.rect(tela, cor_borda, rect, 3, 15)

    # Título do card
    if titulo:
        texto_titulo = fonte_titulo.render(titulo, True, BRANCO)
        tela.blit(texto_titulo, (rect.x + 20, rect.y + 15))


def desenhar_avatar_jogador(tela, x, y, tamanho, cor_personagem, acessorio=None):
    """Desenha um avatar do jogador (quadrado estilizado)."""
    # Sombra
    pygame.draw.rect(tela, (0, 0, 0, 100), (x + 3, y + 3, tamanho, tamanho), 0, 5)

    # Corpo principal
    pygame.draw.rect(tela, cor_personagem, (x, y, tamanho, tamanho), 0, 5)

    # Borda com a mesma cor do personagem (mas mais clara)
    cor_borda = tuple(min(255, c + 80) for c in cor_personagem)
    pygame.draw.rect(tela, cor_borda, (x, y, tamanho, tamanho), 3, 5)

    # Acessórios
    if acessorio == "chapeu":
        # Chapéu
        pygame.draw.rect(tela, (50, 50, 50), (x - 5, y - 10, tamanho + 10, 8), 0, 2)
        pygame.draw.rect(tela, (80, 80, 80), (x + 5, y - 20, tamanho - 10, 12), 0, 2)
    elif acessorio == "oculos":
        # Óculos
        tamanho_lente = tamanho // 4
        pygame.draw.circle(tela, (50, 50, 50), (x + tamanho // 3, y + tamanho // 3), tamanho_lente, 2)
        pygame.draw.circle(tela, (50, 50, 50), (x + 2 * tamanho // 3, y + tamanho // 3), tamanho_lente, 2)
        pygame.draw.line(tela, (50, 50, 50), (x + tamanho // 3 + tamanho_lente, y + tamanho // 3),
                        (x + 2 * tamanho // 3 - tamanho_lente, y + tamanho // 3), 2)


def tela_lobby_servidor(tela, relogio, gradiente, servidor, cliente, config):
    """
    Tela de lobby MODERNA com customização de personagem.

    Args:
        tela: Superfície do jogo
        relogio: Relógio do pygame
        gradiente: Gradiente de fundo
        servidor: Instância do GameServer
        cliente: Instância do GameClient (host como cliente)
        config: Configuração do servidor (nome, porta, max_players)

    Returns:
        ("start", game_mode, customizacao) - Iniciar partida com modo e customização
        ("cancel", None, None) - Cancelar e voltar ao menu
    """
    print("[LOBBY] Tela de lobby moderna aberta")

    # Fontes
    fonte_titulo = pygame.font.SysFont("Arial", 28, True)
    fonte_normal = pygame.font.SysFont("Arial", 22)
    fonte_pequena = pygame.font.SysFont("Arial", 18)
    fonte_grande = pygame.font.SysFont("Arial", 42, True)

    # Estado da customização
    cores_disponiveis = [
        ("Azul", AZUL),
        ("Verde", VERDE),
        ("Vermelho", VERMELHO),
        ("Amarelo", AMARELO),
        ("Ciano", CIANO),
        ("Roxo", ROXO),
        ("Laranja", LARANJA),
        ("Rosa", (255, 105, 180))
    ]
    cor_selecionada_index = 0  # Começa com Azul

    # Layout moderno em 2 colunas
    margem = 60
    col_width = (LARGURA - 3 * margem) // 2

    # Cards das 2 colunas
    card_customizacao = pygame.Rect(margem, 120, col_width, 520)
    card_jogadores = pygame.Rect(margem * 2 + col_width, 120, col_width, 520)

    # Botões
    btn_iniciar = pygame.Rect(LARGURA // 2 - 150, ALTURA - 100, 300, 60)
    btn_cancelar = pygame.Rect(margem, ALTURA - 100, 150, 60)

    # Lista de bots - iniciar com 8 bots por padrão
    bot_cores = [VERMELHO, VERDE, ROXO, LARANJA, CIANO, (255, 105, 180), AMARELO, (100, 200, 255)]
    bots = []
    for i in range(8):
        bot = {
            'nome': f"Bot {i + 1}",
            'cor': bot_cores[i % len(bot_cores)]
        }
        bots.append(bot)

    # Partículas de fundo (animação)
    particulas = []
    for _ in range(30):
        particulas.append({
            'x': random.randint(0, LARGURA),
            'y': random.randint(0, ALTURA_JOGO),
            'velocidade': random.uniform(0.2, 0.8),
            'tamanho': random.randint(1, 3)
        })

    while True:
        tempo_atual = pygame.time.get_ticks()
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())

        # Eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return ("cancel", None)

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    print("[LOBBY] Cancelado")
                    return ("cancel", None)
                if evento.key == pygame.K_RETURN:
                    customizacao = {
                        'cor': cores_disponiveis[cor_selecionada_index][1],
                        'cor_nome': cores_disponiveis[cor_selecionada_index][0],
                        'bots': bots  # Passar lista de bots
                    }
                    print(f"[LOBBY] Iniciando - Modo: Versus, Cor: {customizacao['cor_nome']}, Bots: {len(bots)}")
                    # Enviar sinal para todos os clientes que a partida está iniciando
                    print("[LOBBY_HOST] Enviando GAME_START para todos os clientes...")
                    servidor.broadcast_game_start()
                    return ("start", customizacao)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_click_pos = convert_mouse_position(evento.pos)

                # Botão Iniciar
                if btn_iniciar.collidepoint(mouse_click_pos):
                    customizacao = {
                        'cor': cores_disponiveis[cor_selecionada_index][1],
                        'cor_nome': cores_disponiveis[cor_selecionada_index][0],
                        'bots': bots  # Passar lista de bots
                    }
                    # Enviar sinal para todos os clientes que a partida está iniciando
                    print("[LOBBY_HOST] Enviando GAME_START para todos os clientes...")
                    servidor.broadcast_game_start()
                    return ("start", customizacao)

                # Botão Cancelar
                if btn_cancelar.collidepoint(mouse_click_pos):
                    return ("cancel", None)

                # Seletor de cores (dentro do card de customização)
                y_cores = card_customizacao.y + 180
                for i, (nome_cor, cor) in enumerate(cores_disponiveis):
                    cor_rect = pygame.Rect(card_customizacao.x + 20, y_cores + i * 40, 30, 30)
                    if cor_rect.collidepoint(mouse_click_pos):
                        cor_selecionada_index = i
                        print(f"[LOBBY] Cor alterada para: {nome_cor}")

        # ========== DESENHAR ==========

        # Fundo com gradiente
        tela.blit(gradiente, (0, 0))

        # Partículas animadas
        for p in particulas:
            p['y'] += p['velocidade']
            if p['y'] > ALTURA_JOGO:
                p['y'] = 0
                p['x'] = random.randint(0, LARGURA)
            pygame.draw.circle(tela, (100, 100, 150, 80), (int(p['x']), int(p['y'])), p['tamanho'])

        # Título principal
        pulso = math.sin(tempo_atual / 500) * 5
        titulo_surf = fonte_grande.render("LOBBY MULTIPLAYER", True, BRANCO)
        tela.blit(titulo_surf, (LARGURA // 2 - titulo_surf.get_width() // 2, 40 + pulso))

        # IP para compartilhar
        ip = obter_ip_local_simples()
        ip_surf = fonte_pequena.render(f"IP: {ip}:{config['port']}", True, AMARELO)
        tela.blit(ip_surf, (LARGURA // 2 - ip_surf.get_width() // 2, 85))

        # ========== CARD 1: CUSTOMIZAÇÃO ==========
        desenhar_card(tela, card_customizacao, (30, 30, 50), (100, 100, 200), "PERSONAGEM", fonte_titulo)

        # Preview do personagem customizado (grande)
        preview_size = 120
        preview_x = card_customizacao.centerx - preview_size // 2
        preview_y = card_customizacao.y + 80
        desenhar_avatar_jogador(
            tela, preview_x, preview_y, preview_size,
            cores_disponiveis[cor_selecionada_index][1],
            None  # Sem acessórios
        )

        # Seletor de cores
        y_cores = card_customizacao.y + 180
        label_cor = fonte_normal.render("Cor:", True, BRANCO)
        tela.blit(label_cor, (card_customizacao.x + 20, y_cores - 30))

        for i, (nome_cor, cor) in enumerate(cores_disponiveis):
            cor_rect = pygame.Rect(card_customizacao.x + 20, y_cores + i * 40, 30, 30)

            # Desenhar quadrado da cor
            pygame.draw.rect(tela, cor, cor_rect, 0, 5)
            pygame.draw.rect(tela, BRANCO if i == cor_selecionada_index else (100, 100, 100), cor_rect, 3 if i == cor_selecionada_index else 1, 5)

            # Nome da cor
            texto_cor = fonte_pequena.render(nome_cor, True, BRANCO if i == cor_selecionada_index else (150, 150, 150))
            tela.blit(texto_cor, (card_customizacao.x + 60, y_cores + i * 40 + 5))

        # ========== CARD 2: JOGADORES ==========
        desenhar_card(tela, card_jogadores, (30, 50, 30), (100, 200, 100), "JOGADORES", fonte_titulo)

        # Obter jogadores conectados
        try:
            jogadores = servidor.get_connected_players() if hasattr(servidor, 'get_connected_players') else []
            num_jogadores = len(jogadores) if jogadores else 1
        except:
            jogadores = []
            num_jogadores = 1

        # Contador de jogadores (incluindo bots)
        total_jogadores = num_jogadores + len(bots)
        contador_surf = fonte_normal.render(f"{total_jogadores} / {config['max_players']}", True, AMARELO if total_jogadores < config['max_players'] else VERDE)
        tela.blit(contador_surf, (card_jogadores.x + 20, card_jogadores.y + 60))

        # Lista de jogadores
        y_jogador = card_jogadores.y + 110

        # Host (você)
        desenhar_avatar_jogador(tela, card_jogadores.x + 30, y_jogador, 40,
                               cores_disponiveis[cor_selecionada_index][1],
                               None)  # Sem acessórios
        texto_host = fonte_normal.render(f"{config['player_name']} (HOST)", True, VERDE)
        tela.blit(texto_host, (card_jogadores.x + 85, y_jogador + 8))
        y_jogador += 60

        # Outros jogadores
        if jogadores:
            for i, jogador in enumerate(jogadores):
                if jogador.get('name') != config['player_name']:
                    desenhar_avatar_jogador(tela, card_jogadores.x + 30, y_jogador, 40, AZUL, None)
                    texto_jog = fonte_normal.render(jogador.get('name', f'Jogador {i+1}'), True, BRANCO)
                    tela.blit(texto_jog, (card_jogadores.x + 85, y_jogador + 8))
                    y_jogador += 60

        # Bots
        for bot in bots:
            desenhar_avatar_jogador(tela, card_jogadores.x + 30, y_jogador, 40, bot['cor'], None)
            texto_bot = fonte_normal.render(f"{bot['nome']} (BOT)", True, (150, 150, 150))
            tela.blit(texto_bot, (card_jogadores.x + 85, y_jogador + 8))
            y_jogador += 60

        # Aviso se sozinho
        if num_jogadores == 1:
            pulso_alpha = int(100 + (math.sin(tempo_atual / 500) + 1) / 2 * 155)
            texto_aguardando = fonte_pequena.render("Aguardando conexoes...", True, (pulso_alpha, pulso_alpha, 255))
            tela.blit(texto_aguardando, (card_jogadores.x + 20, card_jogadores.y + card_jogadores.height - 40))

        # Modo de jogo fixo (mostrar badge)
        modo_badge = fonte_titulo.render("MODO: VERSUS", True, AMARELO)
        tela.blit(modo_badge, (LARGURA // 2 - modo_badge.get_width() // 2, card_jogadores.y + card_jogadores.height + 20))

        # ========== BOTÕES PRINCIPAIS ==========

        # Botão Iniciar
        hover_iniciar = btn_iniciar.collidepoint(mouse_pos)
        cor_iniciar = (60, 200, 60) if hover_iniciar else (40, 150, 40)

        # Efeito de pulso no botão
        if hover_iniciar:
            tamanho_extra = int(math.sin(tempo_atual / 200) * 3)
            btn_temp = pygame.Rect(btn_iniciar.x - tamanho_extra, btn_iniciar.y - tamanho_extra,
                                   btn_iniciar.width + tamanho_extra * 2, btn_iniciar.height + tamanho_extra * 2)
        else:
            btn_temp = btn_iniciar

        pygame.draw.rect(tela, cor_iniciar, btn_temp, 0, 15)
        pygame.draw.rect(tela, BRANCO, btn_temp, 4, 15)

        texto_iniciar = fonte_titulo.render("INICIAR PARTIDA", True, BRANCO)
        tela.blit(texto_iniciar, (btn_iniciar.centerx - texto_iniciar.get_width() // 2, btn_iniciar.centery - texto_iniciar.get_height() // 2))

        # Botão Cancelar
        hover_cancelar = btn_cancelar.collidepoint(mouse_pos)
        cor_cancelar = (200, 60, 60) if hover_cancelar else (150, 40, 40)
        pygame.draw.rect(tela, cor_cancelar, btn_cancelar, 0, 15)
        pygame.draw.rect(tela, BRANCO, btn_cancelar, 3, 15)

        texto_cancelar = fonte_normal.render("SAIR", True, BRANCO)
        tela.blit(texto_cancelar, (btn_cancelar.centerx - texto_cancelar.get_width() // 2, btn_cancelar.centery - texto_cancelar.get_height() // 2))

        # Instruções
        inst = fonte_pequena.render("ENTER para iniciar | ESC para sair", True, (150, 150, 150))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA - 30))

        present_frame()
        relogio.tick(60)


def tela_lobby_cliente(tela, relogio, gradiente, cliente, config):
    """
    Tela de lobby para CLIENTES (quem se conecta).
    Aguarda o host iniciar a partida.

    Returns:
        ("start", customizacao) se o host iniciar
        ("cancel", None) se cancelar
    """
    print("[LOBBY_CLIENT] Aguardando host iniciar...")

    fonte_grande = pygame.font.SysFont("Arial", 48, True)
    fonte_titulo = pygame.font.SysFont("Arial", 32, True)
    fonte_normal = pygame.font.SysFont("Arial", 24)
    fonte_pequena = pygame.font.SysFont("Arial", 18)

    # Partículas de fundo
    particulas = []
    for _ in range(50):
        particulas.append({
            'x': random.randint(0, LARGURA),
            'y': random.randint(0, ALTURA_JOGO),
            'velocidade': random.uniform(0.5, 2),
            'tamanho': random.randint(1, 3)
        })

    # Cores disponíveis
    cores_disponiveis = [
        ("Azul", AZUL),
        ("Vermelho", VERMELHO),
        ("Verde", VERDE),
        ("Roxo", ROXO),
        ("Laranja", LARANJA),
        ("Ciano", CIANO),
        ("Amarelo", AMARELO),
        ("Rosa", (255, 105, 180))
    ]
    cor_selecionada_index = 0

    # Botões
    btn_cancelar = pygame.Rect(LARGURA // 2 - 100, ALTURA - 100, 200, 50)

    # Cards
    card_info = pygame.Rect(LARGURA // 2 - 400, 150, 300, 450)
    card_customizacao = pygame.Rect(LARGURA // 2 + 100, 150, 300, 450)

    bots = []  # Lista de bots (se o host adicionar)

    # Flag para saber quando o host iniciou
    game_started = [False]  # Lista para poder modificar dentro do callback

    # Configurar callback para detectar início de partida
    def on_game_start(data):
        print("[LOBBY_CLIENT] Recebido sinal de início da partida!")
        game_started[0] = True

    cliente.set_callback('on_game_start', on_game_start)

    while True:
        tempo_atual = pygame.time.get_ticks()
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return ("cancel", None)

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    print("[LOBBY_CLIENT] Cancelado")
                    return ("cancel", None)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_click_pos = convert_mouse_position(evento.pos)

                # Botão Cancelar
                if btn_cancelar.collidepoint(mouse_click_pos):
                    return ("cancel", None)

                # Seletor de cores
                y_cores = card_customizacao.y + 180
                for i, (nome_cor, cor) in enumerate(cores_disponiveis):
                    cor_rect = pygame.Rect(card_customizacao.x + 20, y_cores + i * 40, 30, 30)
                    if cor_rect.collidepoint(mouse_click_pos):
                        cor_selecionada_index = i
                        print(f"[LOBBY_CLIENT] Cor alterada para: {nome_cor}")

        # ========== VERIFICAR SE O HOST INICIOU ==========
        if game_started[0]:
            print("[LOBBY_CLIENT] Host iniciou! Entrando na partida...")
            customizacao = {
                'cor': cores_disponiveis[cor_selecionada_index][1],
                'cor_nome': cores_disponiveis[cor_selecionada_index][0],
                'bots': []  # Clientes não têm bots
            }
            return ("start", customizacao)

        # ========== DESENHAR ==========

        # Fundo com gradiente
        tela.blit(gradiente, (0, 0))

        # Partículas animadas
        for p in particulas:
            p['y'] += p['velocidade']
            if p['y'] > ALTURA_JOGO:
                p['y'] = 0
                p['x'] = random.randint(0, LARGURA)
            pygame.draw.circle(tela, (100, 100, 150, 80), (int(p['x']), int(p['y'])), p['tamanho'])

        # Título principal
        pulso = math.sin(tempo_atual / 500) * 5
        titulo_surf = fonte_grande.render("AGUARDANDO HOST", True, BRANCO)
        tela.blit(titulo_surf, (LARGURA // 2 - titulo_surf.get_width() // 2, 40 + pulso))

        # ========== CARD 1: INFORMAÇÕES ==========
        desenhar_card(tela, card_info, (30, 30, 50), (100, 100, 200), "SERVIDOR", fonte_titulo)

        # IP do servidor
        try:
            server_info = f"{config['host']}:{config['port']}"
            ip_surf = fonte_normal.render(f"IP: {server_info}", True, AMARELO)
            tela.blit(ip_surf, (card_info.x + 20, card_info.y + 70))
        except:
            pass

        # Status de conexão
        status_surf = fonte_normal.render("Status: Conectado", True, VERDE)
        tela.blit(status_surf, (card_info.x + 20, card_info.y + 110))

        # Mensagem piscante
        pulso_alpha = int(100 + (math.sin(tempo_atual / 300) + 1) / 2 * 155)
        texto_aguardando = fonte_titulo.render("Aguardando...", True, (pulso_alpha, pulso_alpha, 255))
        tela.blit(texto_aguardando, (card_info.x + 20, card_info.y + 200))

        msg_surf = fonte_pequena.render("O host iniciará a partida", True, (150, 150, 150))
        tela.blit(msg_surf, (card_info.x + 20, card_info.y + 250))

        # ========== CARD 2: CUSTOMIZAÇÃO ==========
        desenhar_card(tela, card_customizacao, (30, 30, 50), (100, 100, 200), "PERSONAGEM", fonte_titulo)

        # Preview do personagem
        preview_size = 120
        preview_x = card_customizacao.centerx - preview_size // 2
        preview_y = card_customizacao.y + 80
        desenhar_avatar_jogador(
            tela, preview_x, preview_y, preview_size,
            cores_disponiveis[cor_selecionada_index][1],
            None
        )

        # Seletor de cores
        y_cores = card_customizacao.y + 180
        label_cor = fonte_normal.render("Sua Cor:", True, BRANCO)
        tela.blit(label_cor, (card_customizacao.x + 20, y_cores - 30))

        for i, (nome_cor, cor) in enumerate(cores_disponiveis):
            cor_rect = pygame.Rect(card_customizacao.x + 20, y_cores + i * 40, 30, 30)

            # Desenhar quadrado da cor
            pygame.draw.rect(tela, cor, cor_rect, 0, 5)
            pygame.draw.rect(tela, BRANCO if i == cor_selecionada_index else (100, 100, 100), cor_rect, 3 if i == cor_selecionada_index else 1, 5)

            # Nome da cor
            texto_cor = fonte_pequena.render(nome_cor, True, BRANCO if i == cor_selecionada_index else (150, 150, 150))
            tela.blit(texto_cor, (card_customizacao.x + 60, y_cores + i * 40 + 5))

        # ========== BOTÃO CANCELAR ==========
        hover_cancelar = btn_cancelar.collidepoint(mouse_pos)
        cor_cancelar = (200, 60, 60) if hover_cancelar else (150, 40, 40)
        pygame.draw.rect(tela, cor_cancelar, btn_cancelar, 0, 15)
        pygame.draw.rect(tela, BRANCO, btn_cancelar, 3, 15)

        texto_cancelar = fonte_normal.render("SAIR", True, BRANCO)
        tela.blit(texto_cancelar, (btn_cancelar.centerx - texto_cancelar.get_width() // 2, btn_cancelar.centery - texto_cancelar.get_height() // 2))

        # Instruções
        inst = fonte_pequena.render("ESC para sair", True, (150, 150, 150))
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA - 30))

        present_frame()
        relogio.tick(60)
