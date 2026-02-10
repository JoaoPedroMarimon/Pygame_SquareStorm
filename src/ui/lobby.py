#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lobby Interativo SquareStorm - Sala jogável para o modo multiplayer.
Arena temática com efeitos de tempestade. Jogadores andam livremente
e selecionam modos de jogo pisando em portais.
"""

import pygame
import math
import random
from src.config import *
from src.utils.display_manager import present_frame


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


# --- Constantes ---
TAM_PLAYER = 30
VEL_LOBBY = 4.0
TEMPO_ZONA = 5000  # 5s em ms

# Cores da arena
COR_CHAO_BASE = (18, 16, 28)
COR_CHAO_TILE1 = (22, 20, 34)
COR_CHAO_TILE2 = (18, 16, 28)
COR_PAREDE = (45, 40, 65)
COR_PAREDE_TOPO = (60, 55, 85)

# Paleta de cores dos jogadores (cada player recebe uma cor diferente automaticamente)
PALETA_JOGADORES = [
    AZUL,              # Jogador 1
    VERMELHO,          # Jogador 2
    VERDE,             # Jogador 3
    AMARELO,           # Jogador 4
    CIANO,             # Jogador 5
    ROXO,              # Jogador 6
    LARANJA,           # Jogador 7
    (255, 105, 180),   # Jogador 8 - Rosa
]

# Definição dos portais de modo de jogo
PORTAIS = [
    {
        'nome': 'Bomb',
        'cor_base': (30, 160, 60),
        'cor_glow': (80, 255, 120),
        'disponivel': True,
        'desc': 'Team vs Team',
    },
    {
        'nome': '',
        'cor_base': (40, 80, 180),
        'cor_glow': (100, 150, 255),
        'disponivel': False,
        'desc': 'Em breve',
    },
    {
        'nome': '',
        'cor_base': (160, 40, 40),
        'cor_glow': (255, 100, 100),
        'disponivel': False,
        'desc': 'Em breve',
    },
]


# ============================================================
#  FUNÇÕES DE DESENHO
# ============================================================

def _gerar_cor_derivadas(cor):
    """Gera cores escura e brilhante a partir de uma cor base."""
    escura = tuple(max(0, c - 60) for c in cor)
    brilhante = tuple(min(255, c + 80) for c in cor)
    return escura, brilhante


def _desenhar_player(tela, x, y, cor, nome, fonte, is_host=False, pulsacao=0):
    """
    Desenha um jogador identico ao estilo de fase_base.py / Quadrado.desenhar().
    Shadow -> inner (cor_escura) -> outer (cor) -> highlight.
    """
    tam = TAM_PLAYER
    ix, iy = int(x), int(y)
    cor_escura, cor_brilhante = _gerar_cor_derivadas(cor)

    # Pulsação (ciclo 0-11, expande até 6, volta)
    mod = 0
    if pulsacao < 6:
        mod = int(pulsacao * 0.5)
    else:
        mod = int((12 - pulsacao) * 0.5)

    # 1) Sombra
    pygame.draw.rect(tela, (15, 12, 20),
                     (ix + 3, iy + 3, tam, tam), 0, 3)

    # 2) Quadrado interior (cor escura) - camada de fundo
    pygame.draw.rect(tela, cor_escura,
                     (ix, iy, tam + mod, tam + mod), 0, 5)

    # 3) Quadrado exterior (cor principal) - um pouco menor
    pygame.draw.rect(tela, cor,
                     (ix + 2, iy + 2, tam + mod - 4, tam + mod - 4), 0, 3)

    # 4) Highlight no canto superior esquerdo
    pygame.draw.rect(tela, cor_brilhante,
                     (ix + 4, iy + 4, 7, 7), 0, 2)

    # 5) Olhos
    olho_y = iy + tam // 3
    pygame.draw.rect(tela, BRANCO, (ix + tam // 4, olho_y, 4, 4))
    pygame.draw.rect(tela, BRANCO, (ix + 3 * tam // 4 - 3, olho_y, 4, 4))

    # 6) Nome acima
    if is_host:
        label = f"{nome} [HOST]"
        cor_nome = (100, 255, 100)
    else:
        label = nome
        cor_nome = BRANCO

    nome_surf = fonte.render(label, True, cor_nome)
    nx = ix + tam // 2 - nome_surf.get_width() // 2
    ny = iy - 18

    # Fundo semi-transparente do nome
    bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 150))
    tela.blit(bg, (nx - 3, ny - 1))
    tela.blit(nome_surf, (nx, ny))


def _calcular_portais(sala):
    """Retorna lista de Rects para os portais, centralizados horizontalmente."""
    rects = []
    portal_w = 140
    portal_h = 100
    n = len(PORTAIS)
    espaco = (sala.width - portal_w * n) // (n + 1)
    py = sala.y + sala.height // 3 - portal_h // 2  # Um terço da sala

    for i in range(n):
        px = sala.x + espaco + i * (portal_w + espaco)
        rects.append(pygame.Rect(px, py, portal_w, portal_h))
    return rects


def _desenhar_arena(tela, sala, tempo):
    """Desenha a arena temática SquareStorm."""
    # --- Chão com tiles alternados ---
    tile = 32
    for ty in range(sala.y, sala.bottom, tile):
        for tx in range(sala.x, sala.right, tile):
            idx = ((tx - sala.x) // tile + (ty - sala.y) // tile) % 2
            cor = COR_CHAO_TILE1 if idx == 0 else COR_CHAO_TILE2
            pygame.draw.rect(tela, cor, (tx, ty, tile, tile))

    # --- Linhas de energia no chão (pulsam) ---
    alpha_linha = int(15 + math.sin(tempo / 600) * 8)
    cor_linha = (40 + alpha_linha, 30 + alpha_linha, 70 + alpha_linha)
    # Horizontais
    for ly in range(sala.y + tile * 2, sala.bottom, tile * 4):
        pygame.draw.line(tela, cor_linha, (sala.x, ly), (sala.right, ly), 1)
    # Verticais
    for lx in range(sala.x + tile * 2, sala.right, tile * 4):
        pygame.draw.line(tela, cor_linha, (lx, sala.y), (lx, sala.bottom), 1)

    # --- Paredes ---
    espessura = 6
    # Parede inferior (mais escura, sombra)
    pygame.draw.rect(tela, (25, 22, 38),
                     (sala.x, sala.bottom - espessura, sala.width, espessura))
    # Parede direita
    pygame.draw.rect(tela, (30, 26, 45),
                     (sala.right - espessura, sala.y, espessura, sala.height))
    # Parede superior (mais clara, luz de cima)
    pygame.draw.rect(tela, COR_PAREDE_TOPO,
                     (sala.x, sala.y, sala.width, espessura))
    # Parede esquerda
    pygame.draw.rect(tela, COR_PAREDE,
                     (sala.x, sala.y, espessura, sala.height))
    # Borda fina brilhante
    pygame.draw.rect(tela, (70, 60, 100), sala, 2)

    # --- Logo "SquareStorm" sutil no chão ---
    fonte_logo = pygame.font.SysFont("Arial", 60, True)
    logo_surf = fonte_logo.render("SquareStorm", True, (30, 27, 45))
    logo_x = sala.centerx - logo_surf.get_width() // 2
    logo_y = sala.bottom - 100
    tela.blit(logo_surf, (logo_x, logo_y))


def _desenhar_particulas_tempestade(tela, particulas, sala, tempo):
    """Atualiza e desenha partículas temáticas de tempestade."""
    for p in particulas:
        p['x'] += p['vx']
        p['y'] += p['vy']

        # Reciclar partícula se saiu da sala
        if p['x'] < sala.x or p['x'] > sala.right or p['y'] > sala.bottom:
            p['x'] = random.randint(sala.x, sala.right)
            p['y'] = sala.y
            p['vy'] = random.uniform(0.5, 2.0)

        brilho = int(60 + math.sin(tempo / 300 + p['x'] * 0.01) * 30)
        cor = (brilho, brilho, brilho + 30)
        pygame.draw.circle(tela, cor, (int(p['x']), int(p['y'])), p['tam'])


def _desenhar_relampago(tela, sala, tempo, relampago_state):
    """Desenha um flash de relâmpago ocasional."""
    # Decidir se dispara um relâmpago
    if relampago_state['proximo'] <= tempo:
        relampago_state['ativo'] = True
        relampago_state['inicio'] = tempo
        relampago_state['proximo'] = tempo + random.randint(4000, 10000)
        # Gerar pontos do raio
        x_start = random.randint(sala.x + 50, sala.right - 50)
        pontos = [(x_start, sala.y)]
        y_cur = sala.y
        while y_cur < sala.y + sala.height // 3:
            y_cur += random.randint(8, 20)
            x_off = pontos[-1][0] + random.randint(-15, 15)
            pontos.append((x_off, y_cur))
        relampago_state['pontos'] = pontos

    if relampago_state['ativo']:
        duracao = tempo - relampago_state['inicio']
        if duracao < 150:
            # Flash branco no fundo
            if duracao < 60:
                flash = pygame.Surface((sala.width, sala.height), pygame.SRCALPHA)
                alpha = int(40 * (1 - duracao / 60))
                flash.fill((200, 200, 255, alpha))
                tela.blit(flash, sala.topleft)

            # Desenhar raio
            alpha_raio = max(0, 255 - int(duracao * 2.5))
            pontos = relampago_state['pontos']
            if len(pontos) > 1:
                # Glow
                for i in range(len(pontos) - 1):
                    pygame.draw.line(tela, (100, 100, 200), pontos[i], pontos[i + 1], 5)
                # Core
                for i in range(len(pontos) - 1):
                    pygame.draw.line(tela, (220, 220, 255), pontos[i], pontos[i + 1], 2)
        else:
            relampago_state['ativo'] = False


def _desenhar_portal(tela, rect, portal, tempo, idx, fonte_titulo, fonte_peq, jogador_dentro=False):
    """Desenha um portal de modo de jogo."""
    cor_base = portal['cor_base']
    cor_glow = portal['cor_glow']
    cx, cy = rect.centerx, rect.centery

    # --- Glow externo ---
    glow_size = rect.width + 16
    glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
    pulso = math.sin(tempo / 500 + idx * 2) * 0.3 + 0.7
    alpha_glow = int(35 * pulso)
    if jogador_dentro:
        alpha_glow = int(60 * pulso)
    pygame.draw.ellipse(glow_surf, (*cor_glow, alpha_glow),
                        (0, 0, glow_size, glow_size))
    tela.blit(glow_surf, (cx - glow_size // 2, cy - glow_size // 2))

    # --- Plataforma circular ---
    # Sombra
    pygame.draw.ellipse(tela, (10, 8, 18),
                        (rect.x + 4, rect.y + 4, rect.width, rect.height))
    # Base
    cor_plat = tuple(max(0, min(255, int(c * pulso))) for c in cor_base)
    pygame.draw.ellipse(tela, cor_plat, rect)

    # Anéis concêntricos
    for i in range(3):
        raio = min(rect.width, rect.height) // 2 - 8 - i * 12
        if raio > 5:
            alpha_anel = int(80 + 40 * math.sin(tempo / 400 + i * 1.5))
            cor_anel = tuple(min(255, c + 30) for c in cor_base)
            pygame.draw.ellipse(tela, cor_anel,
                                (cx - raio, cy - raio, raio * 2, raio * 2), 1)

    # Borda
    cor_borda = cor_glow if jogador_dentro else tuple(min(255, c + 40) for c in cor_base)
    largura_borda = 3 if jogador_dentro else 2
    pygame.draw.ellipse(tela, cor_borda, rect, largura_borda)

    # Partículas orbitando (se disponível)
    if portal['disponivel']:
        for i in range(4):
            ang = (tempo / 800 + i * math.pi / 2 + idx)
            r = min(rect.width, rect.height) // 2 - 5
            px = cx + int(math.cos(ang) * r)
            py = cy + int(math.sin(ang) * r * 0.5)  # Elíptico
            pygame.draw.circle(tela, cor_glow, (px, py), 3)

    # --- Texto ---
    linhas = portal['nome'].split('\n')
    y_text = cy - 16 if len(linhas) == 1 else cy - 22
    for linha in linhas:
        s = fonte_titulo.render(linha, True, BRANCO)
        tela.blit(s, (cx - s.get_width() // 2, y_text))
        y_text += s.get_height() + 2

    # Descrição
    if portal['disponivel']:
        desc_cor = (180, 255, 180)
    else:
        desc_cor = (255, 200, 100)
    desc_s = fonte_peq.render(portal['desc'], True, desc_cor)
    tela.blit(desc_s, (cx - desc_s.get_width() // 2, rect.bottom - 22))


def _desenhar_barra_timer(tela, jx, jy, progresso, fonte):
    """Barra de progresso circular estilizada sobre o jogador."""
    barra_w = 60
    barra_h = 8
    bx = int(jx) + TAM_PLAYER // 2 - barra_w // 2
    by = int(jy) - 35

    # Fundo
    pygame.draw.rect(tela, (20, 18, 30), (bx - 1, by - 1, barra_w + 2, barra_h + 2), 0, 5)

    # Preenchimento
    fill = int(barra_w * progresso)
    if fill > 0:
        g = int(120 + 135 * progresso)
        pygame.draw.rect(tela, (30, min(255, g), 50), (bx, by, fill, barra_h), 0, 5)

    # Borda
    pygame.draw.rect(tela, (150, 150, 150), (bx, by, barra_w, barra_h), 1, 5)

    # Tempo
    restante = max(0, (1 - progresso) * 5)
    ts = fonte.render(f"{restante:.1f}s", True, BRANCO)
    tela.blit(ts, (bx + barra_w + 5, by - 1))


# ============================================================
#  LOOP PRINCIPAL DO LOBBY
# ============================================================

def _lobby_loop(tela, relogio, gradiente, cliente, config, is_host, servidor=None):
    """Loop do lobby interativo. Compartilhado entre host e cliente."""
    print(f"[LOBBY] Sala SquareStorm aberta ({'HOST' if is_host else 'CLIENTE'})")

    # Fontes
    fonte_grande = pygame.font.SysFont("Arial", 34, True)
    fonte_titulo = pygame.font.SysFont("Arial", 16, True)
    fonte_peq = pygame.font.SysFont("Arial", 13)
    fonte_nomes = pygame.font.SysFont("Arial", 12)
    fonte_msg = pygame.font.SysFont("Arial", 20, True)
    fonte_ip = pygame.font.SysFont("Arial", 14)

    # Área da sala
    margem = 25
    topo = 65
    base = 40
    sala = pygame.Rect(margem, topo, LARGURA - margem * 2, ALTURA_JOGO - topo - base)

    # Portais
    portais_rects = _calcular_portais(sala)

    # Jogador local - posição
    jx = float(sala.centerx - TAM_PLAYER // 2)
    jy = float(sala.bottom - 90)

    # Cor do jogador local (index 0 = host, clientes recebem pelo player_id)
    player_id_local = cliente.local_player_id or 1
    cor_index_local = (player_id_local - 1) % len(PALETA_JOGADORES)

    # Pulsação
    pulsacao = 0
    ultimo_pulso = 0

    # Timer de zona
    zona_atual = -1
    zona_timer_start = 0

    # Mensagem temporária
    msg = ""
    msg_fim = 0

    # Bots (host)
    bot_cores = [VERMELHO, VERDE, ROXO, LARANJA, CIANO, (255, 105, 180), AMARELO, (100, 200, 255)]
    bots = []
    if is_host:
        for i in range(8):
            bots.append({'nome': f"Bot {i + 1}", 'cor': bot_cores[i % len(bot_cores)]})

    # Game start callback
    game_started = [False]

    def on_game_start(data):
        game_started[0] = True

    cliente.set_callback('on_game_start', on_game_start)

    # Partículas de tempestade (caem do topo)
    particulas = []
    for _ in range(25):
        particulas.append({
            'x': float(random.randint(sala.x, sala.right)),
            'y': float(random.randint(sala.y, sala.bottom)),
            'vx': random.uniform(-0.3, 0.3),
            'vy': random.uniform(0.4, 1.5),
            'tam': random.randint(1, 2),
        })

    # Estado do relâmpago
    relampago = {
        'ativo': False,
        'inicio': 0,
        'proximo': pygame.time.get_ticks() + random.randint(2000, 5000),
        'pontos': [],
    }

    while True:
        tempo = pygame.time.get_ticks()
        dt = 1.0 / 60.0

        # ========== EVENTOS ==========
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return ("cancel", None)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return ("cancel", None)

        # ========== GAME START ==========
        if game_started[0]:
            cor_local = PALETA_JOGADORES[cor_index_local]
            return ("start", {
                'cor': cor_local,
                'cor_nome': str(cor_index_local),
                'bots': bots,
            })

        # ========== MOVIMENTO ==========
        teclas = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= VEL_LOBBY
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += VEL_LOBBY
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= VEL_LOBBY
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += VEL_LOBBY

        if dx != 0 and dy != 0:
            f = VEL_LOBBY / math.sqrt(dx * dx + dy * dy)
            dx *= f
            dy *= f

        jx += dx
        jy += dy
        jx = max(float(sala.x + 8), min(float(sala.right - TAM_PLAYER - 8), jx))
        jy = max(float(sala.y + 8), min(float(sala.bottom - TAM_PLAYER - 8), jy))

        # Enviar input
        keys_net = {
            'w': bool(teclas[pygame.K_w] or teclas[pygame.K_UP]),
            's': bool(teclas[pygame.K_s] or teclas[pygame.K_DOWN]),
            'a': bool(teclas[pygame.K_a] or teclas[pygame.K_LEFT]),
            'd': bool(teclas[pygame.K_d] or teclas[pygame.K_RIGHT]),
        }
        cliente.send_player_input(keys_net, 0, 0, False)
        cliente.update_interpolation(dt)

        # Pulsação (ciclo 0-11)
        if tempo - ultimo_pulso > 100:
            ultimo_pulso = tempo
            pulsacao = (pulsacao + 1) % 12

        # ========== DETECÇÃO DE PORTAL ==========
        jrect = pygame.Rect(int(jx), int(jy), TAM_PLAYER, TAM_PLAYER)
        pisando = -1
        for i, pr in enumerate(portais_rects):
            # Usar colisão por centro do jogador dentro da elipse
            centro_jx = jx + TAM_PLAYER // 2
            centro_jy = jy + TAM_PLAYER // 2
            # Checar se centro está dentro do retângulo do portal
            if pr.collidepoint(centro_jx, centro_jy):
                pisando = i
                break

        if pisando != zona_atual:
            zona_atual = pisando
            zona_timer_start = tempo if pisando >= 0 else 0

        progresso = 0.0
        if zona_atual >= 0 and zona_timer_start > 0:
            t_zona = tempo - zona_timer_start
            progresso = min(1.0, t_zona / TEMPO_ZONA)

            if t_zona >= TEMPO_ZONA:
                portal = PORTAIS[zona_atual]
                if portal['disponivel']:
                    if is_host:
                        cor_local = PALETA_JOGADORES[cor_index_local]
                        cust = {
                            'cor': cor_local,
                            'cor_nome': str(cor_index_local),
                            'bots': bots,
                        }
                        print(f"[LOBBY] Host iniciou VERSUS!")
                        servidor.broadcast_game_start()
                        return ("start", cust)
                    else:
                        msg = "Somente o HOST pode iniciar!"
                        msg_fim = tempo + 2000
                        zona_timer_start = tempo
                else:
                    msg = f"{portal['nome'].replace(chr(10), ' ')}: EM DESENVOLVIMENTO!"
                    msg_fim = tempo + 2000
                    zona_timer_start = tempo

        # ========== DESENHAR ==========

        # Fundo gradiente
        tela.blit(gradiente, (0, 0))

        # Arena
        _desenhar_arena(tela, sala, tempo)

        # Partículas de tempestade
        _desenhar_particulas_tempestade(tela, particulas, sala, tempo)

        # Relâmpago
        _desenhar_relampago(tela, sala, tempo, relampago)

        # Portais
        for i, pr in enumerate(portais_rects):
            dentro = (i == zona_atual)
            _desenhar_portal(tela, pr, PORTAIS[i], tempo, i, fonte_titulo, fonte_peq, dentro)

        # Jogadores remotos
        remotos = cliente.get_remote_players()
        for idx, (pid, rp) in enumerate(remotos.items()):
            # Cada jogador remoto recebe cor baseada no seu player_id
            ci = (pid - 1) % len(PALETA_JOGADORES)
            cor_r = PALETA_JOGADORES[ci]
            _desenhar_player(tela, rp.x, rp.y, cor_r, rp.name, fonte_nomes,
                             is_host=False, pulsacao=pulsacao)

        # Jogador local (por cima)
        cor_local = PALETA_JOGADORES[cor_index_local]
        _desenhar_player(tela, jx, jy, cor_local,
                         config.get('player_name', 'Jogador'), fonte_nomes,
                         is_host=is_host, pulsacao=pulsacao)

        # Barra de timer
        if zona_atual >= 0 and progresso > 0:
            _desenhar_barra_timer(tela, jx, jy, progresso, fonte_peq)

        # ========== UI OVERLAY ==========

        # Título estilizado
        titulo = fonte_grande.render("SQUARESTORM", True, (200, 200, 255))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 10))

        # Subtítulo
        sub = fonte_ip.render("LOBBY", True, (120, 120, 160))
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 44))

        # IP
        if is_host:
            ip = obter_ip_local_simples()
            ip_txt = f"IP: {ip}:{config['port']}"
        else:
            ip_txt = f"Servidor: {config.get('host', '?')}:{config['port']}"
        ip_s = fonte_ip.render(ip_txt, True, AMARELO)
        tela.blit(ip_s, (LARGURA // 2 - ip_s.get_width() // 2, 56))

        # Jogadores conectados
        n_total = 1 + len(remotos)
        cnt = fonte_ip.render(f"Jogadores: {n_total}", True, VERDE)
        tela.blit(cnt, (LARGURA - cnt.get_width() - 15, 12))

        # Preview da cor do jogador
        pygame.draw.rect(tela, cor_local, (12, 12, 16, 16), 0, 3)
        cor_escura, _ = _gerar_cor_derivadas(cor_local)
        pygame.draw.rect(tela, cor_escura, (12, 12, 16, 16), 2, 3)
        nome_cor_s = fonte_ip.render(config.get('player_name', ''), True, cor_local)
        tela.blit(nome_cor_s, (32, 13))

        # Mensagem temporária
        if msg and tempo < msg_fim:
            ms = fonte_msg.render(msg, True, AMARELO)
            mw = ms.get_width() + 30
            mh = 40
            mr = pygame.Rect(LARGURA // 2 - mw // 2, sala.centery + 50, mw, mh)
            bg = pygame.Surface((mr.width, mr.height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 200))
            tela.blit(bg, mr.topleft)
            pygame.draw.rect(tela, (255, 200, 50), mr, 2, 8)
            tela.blit(ms, (mr.centerx - ms.get_width() // 2, mr.centery - ms.get_height() // 2))

        # Aguardando jogadores
        if is_host and len(remotos) == 0:
            p_a = int(100 + math.sin(tempo / 500) * 80)
            ag = fonte_ip.render("Aguardando jogadores se conectarem...", True, (p_a, p_a, 255))
            tela.blit(ag, (LARGURA // 2 - ag.get_width() // 2, sala.bottom + 4))

        # Instruções
        inst = "WASD: Mover  |  ESC: Sair  |  Fique no portal por 5s para iniciar"
        is_s = fonte_peq.render(inst, True, (100, 100, 120))
        tela.blit(is_s, (LARGURA // 2 - is_s.get_width() // 2, ALTURA_JOGO - 18))

        present_frame()
        relogio.tick(60)


# ============================================================
#  FUNÇÕES PÚBLICAS (mesma assinatura de antes)
# ============================================================

def tela_lobby_servidor(tela, relogio, gradiente, servidor, cliente, config):
    """Lobby interativo para o HOST."""
    return _lobby_loop(tela, relogio, gradiente, cliente, config, is_host=True, servidor=servidor)


def tela_lobby_cliente(tela, relogio, gradiente, cliente, config):
    """Lobby interativo para CLIENTES."""
    return _lobby_loop(tela, relogio, gradiente, cliente, config, is_host=False)
