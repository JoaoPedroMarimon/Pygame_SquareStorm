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


# --- Constantes ---
TAM_PLAYER = 30
VEL_LOBBY = 10.0
TEMPO_ZONA = 2500  # tempo (ms) parado no portal para ativá-lo

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

# Portais do lobby. O primeiro (PLAY) abre a tela de seleção de minigames.
# Os demais ficam como "Em Breve" (a definir depois).
PORTAIS = [
    {
        'nome': 'PLAY',
        'cor_base': (30, 160, 60),
        'cor_glow': (80, 255, 120),
        'disponivel': True,
        'acao': 'play',               # abre a tela de seleção de minigame
        'desc': 'Escolher Minigame',
    },
    {
        'nome': 'COR',
        'cor_base': (150, 60, 190),
        'cor_glow': (210, 130, 255),
        'disponivel': True,
        'acao': 'cor',                # abre a tela de personalização de cor
        'desc': 'Personalizar',
    },
    {
        'nome': 'COSMETICOS',
        'cor_base': (40, 130, 160),
        'cor_glow': (110, 220, 255),
        'disponivel': True,
        'acao': 'cosmetico',          # abre a tela de cosméticos (chapéus)
        'desc': 'Chapeus',
    },
    {
        'nome': 'Em Breve',
        'cor_base': (60, 60, 75),
        'cor_glow': (130, 130, 160),
        'disponivel': False,
        'acao': 'em_breve',
        'desc': 'A definir',
    },
    {
        'nome': 'Em Breve',
        'cor_base': (60, 60, 75),
        'cor_glow': (130, 130, 160),
        'disponivel': False,
        'acao': 'em_breve',
        'desc': 'A definir',
    },
    {
        'nome': 'Em Breve',
        'cor_base': (60, 60, 75),
        'cor_glow': (130, 130, 160),
        'disponivel': False,
        'acao': 'em_breve',
        'desc': 'A definir',
    },
    {
        'nome': 'Em Breve',
        'cor_base': (60, 60, 75),
        'cor_glow': (130, 130, 160),
        'disponivel': False,
        'acao': 'em_breve',
        'desc': 'A definir',
    },
]

# Minigames disponíveis, exibidos na tela de seleção (portal PLAY).
# Para adicionar um novo minigame, basta acrescentar um dict aqui.
MINIGAMES = [
    {
        'nome': 'Bomb',
        'cor_base': (30, 160, 60),
        'cor_glow': (80, 255, 120),
        'disponivel': True,
        'desc': 'Team vs Team',
    },
    {
        'nome': 'Aim',
        'cor_base': (40, 80, 180),
        'cor_glow': (100, 150, 255),
        'disponivel': True,
        'desc': 'Tiro ao Alvo',
    },
    {
        'nome': 'Duel',
        'cor_base': (160, 40, 120),
        'cor_glow': (255, 100, 200),
        'disponivel': True,
        'desc': 'Duelo 1v1',
    },
    {
        'nome': 'Sabers',
        'cor_base': (40, 80, 180),
        'cor_glow': (100, 180, 255),
        'disponivel': True,
        'desc': 'Free-for-all Sabers',
    },
    {
        'nome': 'Deadeye',
        'cor_base': (180, 150, 30),
        'cor_glow': (255, 220, 100),
        'disponivel': True,
        'desc': '4v4 Desert Eagle',
    },
    {
        'nome': 'BoxFight',
        'cor_base': (180, 80, 20),
        'cor_glow': (255, 150, 60),
        'disponivel': True,
        'desc': 'Constroi & Atira',
    },
]

# Cosméticos divididos em duas categorias combináveis: CABEÇA e CORPO.
# O jogador equipa um de cada e os dois aparecem juntos.
# Para adicionar: acrescente um dict aqui e trate o 'tipo' na função de
# desenho correspondente (_desenhar_cabeca / _desenhar_corpo).
COSMETICOS_CABECA = [
    {'nome': 'Nenhum',   'tipo': None,       'desc': 'Sem cosmetico'},
    {'nome': 'Cartola',  'tipo': 'cartola',  'desc': 'Classica'},
    {'nome': 'Bone',     'tipo': 'bone',     'desc': 'Descolado'},
    {'nome': 'Coroa',    'tipo': 'coroa',    'desc': 'Realeza'},
    {'nome': 'Chifres',  'tipo': 'chifres',  'desc': 'Travesso'},
    {'nome': 'Aureola',  'tipo': 'aureola',  'desc': 'Angelical'},
    {'nome': 'Festa',    'tipo': 'festa',    'desc': 'Aniversario'},
    {'nome': 'Antenas',  'tipo': 'antena',   'desc': 'Alienigena'},
]

COSMETICOS_CORPO = [
    {'nome': 'Nenhum',       'tipo': None,             'desc': 'Sem cosmetico'},
    {'nome': 'Oculos',       'tipo': 'oculos',         'desc': 'Inteligente'},
    {'nome': 'Oculos Sol',   'tipo': 'oculos_escuros', 'desc': 'Descolado'},
    {'nome': 'Gravata',      'tipo': 'gravata',        'desc': 'Formal'},
    {'nome': 'Borboleta',    'tipo': 'borboleta',      'desc': 'Elegante'},
    {'nome': 'Cachecol',     'tipo': 'cachecol',       'desc': 'Aconchegante'},
    {'nome': 'Bigode',       'tipo': 'bigode',         'desc': 'Distinto'},
]


# ============================================================
#  FUNÇÕES DE DESENHO
# ============================================================

def _gerar_cor_derivadas(cor):
    """Gera cores escura e brilhante a partir de uma cor base."""
    escura = tuple(max(0, c - 60) for c in cor)
    brilhante = tuple(min(255, c + 80) for c in cor)
    return escura, brilhante


def _desenhar_cabeca(tela, ix, iy, tam, tipo):
    """Desenha um cosmético de CABEÇA no topo do quadrado do jogador."""
    if not tipo:
        return
    cx = ix + tam // 2

    if tipo == 'cartola':
        pygame.draw.rect(tela, (20, 20, 25), (cx - 17, iy - 3, 34, 5), 0, 2)
        pygame.draw.rect(tela, (30, 30, 38), (cx - 11, iy - 17, 22, 15), 0, 3)
        pygame.draw.rect(tela, (200, 60, 70), (cx - 11, iy - 8, 22, 4))
        pygame.draw.rect(tela, (70, 70, 85), (cx - 8, iy - 15, 5, 9), 0, 2)

    elif tipo == 'bone':
        # Copa arredondada + aba para a direita
        pygame.draw.rect(tela, (210, 60, 60), (cx - 13, iy - 12, 26, 12), 0, 6)
        pygame.draw.rect(tela, (170, 40, 40), (cx - 2, iy - 2, 22, 5), 0, 3)  # aba
        pygame.draw.circle(tela, (255, 210, 90), (cx, iy - 12), 3)            # botão

    elif tipo == 'coroa':
        base_y = iy - 2
        pygame.draw.rect(tela, (255, 200, 40), (cx - 14, base_y - 4, 28, 6), 0, 2)
        # Pontas
        for px in (-14, -5, 4, 13):
            pygame.draw.polygon(tela, (255, 210, 60),
                                [(cx + px, base_y - 3), (cx + px + 4, base_y - 15),
                                 (cx + px + 8, base_y - 3)])
        # Gemas
        pygame.draw.circle(tela, (230, 60, 90), (cx, base_y - 1), 2)
        pygame.draw.circle(tela, (80, 130, 240), (cx - 9, base_y - 1), 2)
        pygame.draw.circle(tela, (80, 130, 240), (cx + 9, base_y - 1), 2)

    elif tipo == 'chifres':
        for s in (-1, 1):
            base_x = cx + s * 9
            pygame.draw.polygon(tela, (170, 30, 30),
                                [(base_x, iy + 1), (base_x + s * 3, iy - 14),
                                 (base_x + s * 8, iy + 1)])
            pygame.draw.polygon(tela, (220, 60, 60),
                                [(base_x + s * 2, iy), (base_x + s * 3, iy - 10),
                                 (base_x + s * 6, iy)])

    elif tipo == 'aureola':
        halo = pygame.Surface((36, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (255, 240, 120, 90), (0, 0, 36, 16))
        pygame.draw.ellipse(halo, (255, 235, 90), (0, 0, 36, 16), 3)
        tela.blit(halo, (cx - 18, iy - 16))

    elif tipo == 'festa':
        # Cone listrado + pompom
        pygame.draw.polygon(tela, (90, 200, 220), [(cx - 10, iy), (cx + 10, iy), (cx, iy - 20)])
        pygame.draw.polygon(tela, (255, 120, 180),
                            [(cx - 6, iy - 8), (cx - 3, iy - 8), (cx, iy - 20)])
        pygame.draw.circle(tela, (255, 230, 90), (cx, iy - 20), 3)

    elif tipo == 'antena':
        for s in (-1, 1):
            tip_x = cx + s * 8
            pygame.draw.line(tela, (120, 120, 130), (cx + s * 4, iy),
                             (tip_x, iy - 14), 2)
            pygame.draw.circle(tela, (120, 255, 160), (tip_x, iy - 15), 3)


def _desenhar_corpo(tela, ix, iy, tam, tipo):
    """Desenha um cosmético de CORPO (rosto/pescoço) sobre o quadrado do jogador."""
    if not tipo:
        return
    cx = ix + tam // 2

    if tipo == 'oculos':
        y = iy + 10
        pygame.draw.circle(tela, (240, 240, 255), (ix + 9, y), 5)
        pygame.draw.circle(tela, (240, 240, 255), (ix + tam - 9, y), 5)
        pygame.draw.circle(tela, (40, 40, 60), (ix + 9, y), 5, 2)
        pygame.draw.circle(tela, (40, 40, 60), (ix + tam - 9, y), 5, 2)
        pygame.draw.line(tela, (40, 40, 60), (ix + 13, y), (ix + tam - 13, y), 2)

    elif tipo == 'oculos_escuros':
        y = iy + 10
        pygame.draw.rect(tela, (15, 15, 20), (ix + 4, y - 4, 8, 8), 0, 2)
        pygame.draw.rect(tela, (15, 15, 20), (ix + tam - 12, y - 4, 8, 8), 0, 2)
        pygame.draw.line(tela, (15, 15, 20), (ix + 12, y - 2), (ix + tam - 12, y - 2), 2)
        pygame.draw.line(tela, (90, 160, 220), (ix + 6, y - 2), (ix + 9, y - 2), 1)

    elif tipo == 'gravata':
        # Nó + gravata pendurada
        pygame.draw.polygon(tela, (200, 40, 50),
                            [(cx - 3, iy + tam - 12), (cx + 3, iy + tam - 12),
                             (cx + 2, iy + tam - 8), (cx - 2, iy + tam - 8)])
        pygame.draw.polygon(tela, (220, 50, 60),
                            [(cx - 4, iy + tam - 8), (cx + 4, iy + tam - 8),
                             (cx, iy + tam + 3)])

    elif tipo == 'borboleta':
        y = iy + tam - 8
        pygame.draw.polygon(tela, (60, 90, 200),
                            [(cx - 9, y - 4), (cx - 9, y + 4), (cx - 1, y)])
        pygame.draw.polygon(tela, (60, 90, 200),
                            [(cx + 9, y - 4), (cx + 9, y + 4), (cx + 1, y)])
        pygame.draw.rect(tela, (40, 60, 150), (cx - 2, y - 3, 4, 6), 0, 1)

    elif tipo == 'cachecol':
        pygame.draw.rect(tela, (60, 160, 90), (ix + 2, iy + tam - 9, tam - 4, 6), 0, 2)
        pygame.draw.rect(tela, (50, 140, 80), (cx + 4, iy + tam - 6, 5, 11), 0, 2)  # ponta

    elif tipo == 'bigode':
        y = iy + 17
        pygame.draw.polygon(tela, (60, 40, 30),
                            [(cx, y), (cx - 10, y - 3), (cx - 6, y + 3)])
        pygame.draw.polygon(tela, (60, 40, 30),
                            [(cx, y), (cx + 10, y - 3), (cx + 6, y + 3)])


def _desenhar_player(tela, x, y, cor, nome, fonte, is_host=False, pulsacao=0,
                     cabeca_tipo=None, corpo_tipo=None):
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

    # 5) Cosméticos (corpo por baixo do nome, cabeça no topo)
    _desenhar_corpo(tela, ix, iy, tam, corpo_tipo)
    _desenhar_cabeca(tela, ix, iy, tam, cabeca_tipo)

    # 6) Nome acima
    if is_host:
        label = f"{nome} [HOST]"
        cor_nome = (100, 255, 100)
    else:
        label = nome
        cor_nome = BRANCO

    nome_surf = fonte.render(label, True, cor_nome)
    nx = ix + tam // 2 - nome_surf.get_width() // 2
    # Sobe o nome quando há cosmético de cabeça para não sobrepô-lo
    ny = iy - (34 if cabeca_tipo else 18)

    # Fundo semi-transparente do nome
    bg = pygame.Surface((nome_surf.get_width() + 6, nome_surf.get_height() + 2), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 150))
    tela.blit(bg, (nx - 3, ny - 1))
    tela.blit(nome_surf, (nx, ny))


def _calcular_portais(sala):
    """Retorna lista de Rects para os portais em grid 3x2 (3 colunas, 2 linhas)."""
    rects = []
    portal_w = 95
    portal_h = 70
    colunas = 3
    linhas = 2
    espaco_x = (sala.width - portal_w * colunas) // (colunas + 1)
    espaco_y = 30
    # Centralizar verticalmente as 2 linhas
    altura_total = linhas * portal_h + (linhas - 1) * espaco_y
    y_inicio = sala.y + (sala.height - altura_total) // 2 - 20

    for linha in range(linhas):
        for col in range(colunas):
            px = sala.x + espaco_x + col * (portal_w + espaco_x)
            py = y_inicio + linha * (portal_h + espaco_y)
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
    disponivel = portal['disponivel']
    cx, cy = rect.centerx, rect.centery

    pulso = math.sin(tempo / 500 + idx * 2) * 0.3 + 0.7

    if disponivel:
        # --- Glow externo ---
        glow_size = rect.width + 16
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
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
    if disponivel:
        cor_plat = tuple(max(0, min(255, int(c * pulso))) for c in cor_base)
    else:
        cor_plat = (35, 32, 45)
    pygame.draw.ellipse(tela, cor_plat, rect)

    # Anéis concêntricos
    if disponivel:
        for i in range(3):
            raio = min(rect.width, rect.height) // 2 - 8 - i * 10
            if raio > 5:
                cor_anel = tuple(min(255, c + 30) for c in cor_base)
                pygame.draw.ellipse(tela, cor_anel,
                                    (cx - raio, cy - raio, raio * 2, raio * 2), 1)

    # Borda
    if disponivel:
        cor_borda = cor_glow if jogador_dentro else tuple(min(255, c + 40) for c in cor_base)
        largura_borda = 3 if jogador_dentro else 2
    else:
        cor_borda = (60, 55, 75)
        largura_borda = 1
    pygame.draw.ellipse(tela, cor_borda, rect, largura_borda)

    # Partículas orbitando (se disponível)
    if disponivel:
        for i in range(4):
            ang = (tempo / 800 + i * math.pi / 2 + idx)
            r = min(rect.width, rect.height) // 2 - 5
            px = cx + int(math.cos(ang) * r)
            py = cy + int(math.sin(ang) * r * 0.5)
            pygame.draw.circle(tela, cor_glow, (px, py), 3)

    # --- Texto ---
    if disponivel:
        nome_cor = BRANCO
    else:
        nome_cor = (100, 95, 120)
    s = fonte_titulo.render(portal['nome'], True, nome_cor)
    tela.blit(s, (cx - s.get_width() // 2, cy - 14))

    # Descrição
    if disponivel:
        desc_cor = (180, 255, 180)
    else:
        desc_cor = (120, 110, 80)
    desc_s = fonte_peq.render(portal['desc'], True, desc_cor)
    tela.blit(desc_s, (cx - desc_s.get_width() // 2, rect.bottom - 18))


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
    restante = max(0, (1 - progresso) * (TEMPO_ZONA / 1000))
    ts = fonte.render(f"{restante:.1f}s", True, BRANCO)
    tela.blit(ts, (bx + barra_w + 5, by - 1))


# ============================================================
#  TELA DE SELEÇÃO DE MINIGAME (overlay do portal PLAY)
# ============================================================

def _calcular_painel_selecao():
    """Retorna o Rect do painel central da tela de seleção."""
    pw, ph = 720, 470
    px = LARGURA // 2 - pw // 2
    py = ALTURA_JOGO // 2 - ph // 2
    return pygame.Rect(px, py, pw, ph)


def _calcular_cards_selecao(painel):
    """Retorna a lista de Rects dos cards de minigame dentro do painel (grid 3x2)."""
    cards = []
    card_w, card_h = 200, 150
    cols, rows = 3, 2
    gap_x = (painel.width - card_w * cols) // (cols + 1)
    gap_y = 28
    y0 = painel.y + 92
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(MINIGAMES):
                break
            x = painel.x + gap_x + c * (card_w + gap_x)
            y = y0 + r * (card_h + gap_y)
            cards.append(pygame.Rect(x, y, card_w, card_h))
    return cards


def _desenhar_selecao_minigames(tela, painel, cards, sel_idx, mouse_pos, tempo,
                                fonte_titulo, fonte_card, fonte_desc, fonte_dica):
    """Desenha a tela de seleção de minigame por cima do lobby."""
    # Escurecer o fundo
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    tela.blit(overlay, (0, 0))

    # Painel
    painel_surf = pygame.Surface((painel.width, painel.height), pygame.SRCALPHA)
    painel_surf.fill((20, 18, 32, 245))
    tela.blit(painel_surf, painel.topleft)
    pygame.draw.rect(tela, (90, 80, 140), painel, 3, 14)
    pygame.draw.rect(tela, (140, 130, 200), painel, 1, 14)

    # Título
    tit = fonte_titulo.render("ESCOLHA O MINIGAME", True, (200, 200, 255))
    tela.blit(tit, (painel.centerx - tit.get_width() // 2, painel.y + 28))

    # Cards
    for i, rect in enumerate(cards):
        mg = MINIGAMES[i]
        disponivel = mg['disponivel']
        hover = rect.collidepoint(mouse_pos)
        selecionado = (i == sel_idx)
        realce = selecionado or hover

        pulso = math.sin(tempo / 400 + i) * 0.15 + 0.85

        # Glow do card selecionado
        if realce and disponivel:
            glow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*mg['cor_glow'], 60),
                             (0, 0, rect.width + 20, rect.height + 20), 0, 16)
            tela.blit(glow, (rect.x - 10, rect.y - 10))

        # Fundo do card
        if disponivel:
            cor_fundo = tuple(max(0, min(255, int(c * (0.55 if not realce else pulso)))) for c in mg['cor_base'])
        else:
            cor_fundo = (40, 38, 52)
        pygame.draw.rect(tela, cor_fundo, rect, 0, 12)

        # Borda
        if disponivel:
            cor_borda = mg['cor_glow'] if realce else tuple(min(255, c + 40) for c in mg['cor_base'])
            larg = 3 if realce else 2
        else:
            cor_borda = (70, 65, 85)
            larg = 1
        pygame.draw.rect(tela, cor_borda, rect, larg, 12)

        # Ícone (quadrado temático)
        icon = pygame.Rect(0, 0, 44, 44)
        icon.center = (rect.centerx, rect.y + 52)
        cor_icon = mg['cor_glow'] if disponivel else (90, 85, 110)
        pygame.draw.rect(tela, tuple(max(0, c - 60) for c in cor_icon),
                         (icon.x + 3, icon.y + 3, icon.width, icon.height), 0, 6)
        pygame.draw.rect(tela, cor_icon, icon, 0, 6)
        pygame.draw.rect(tela, tuple(min(255, c + 60) for c in cor_icon),
                         (icon.x + 5, icon.y + 5, 10, 10), 0, 3)

        # Nome
        cor_nome = BRANCO if disponivel else (130, 125, 150)
        nome_s = fonte_card.render(mg['nome'], True, cor_nome)
        tela.blit(nome_s, (rect.centerx - nome_s.get_width() // 2, rect.y + 84))

        # Descrição
        cor_desc = (200, 220, 200) if disponivel else (110, 105, 130)
        desc_s = fonte_desc.render(mg['desc'], True, cor_desc)
        tela.blit(desc_s, (rect.centerx - desc_s.get_width() // 2, rect.y + 112))

    # Dica de rodapé
    dica = "Setas/Mouse: Escolher  |  ENTER ou Clique: Iniciar  |  ESC: Voltar"
    dica_s = fonte_dica.render(dica, True, (150, 150, 180))
    tela.blit(dica_s, (painel.centerx - dica_s.get_width() // 2, painel.bottom - 34))


# ============================================================
#  TELA DE PERSONALIZAÇÃO DE COR (overlay do portal COR)
# ============================================================

def _calcular_painel_cor():
    """Retorna o Rect do painel central da tela de personalização de cor."""
    pw, ph = 640, 400
    px = LARGURA // 2 - pw // 2
    py = ALTURA_JOGO // 2 - ph // 2
    return pygame.Rect(px, py, pw, ph)


def _calcular_swatches_cor(painel):
    """Retorna a lista de Rects das amostras de cor dentro do painel (grid 4x2)."""
    swatches = []
    size = 96
    cols, rows = 4, 2
    gap_x = (painel.width - size * cols) // (cols + 1)
    gap_y = 26
    y0 = painel.y + 96
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(PALETA_JOGADORES):
                break
            x = painel.x + gap_x + c * (size + gap_x)
            y = y0 + r * (size + gap_y)
            swatches.append(pygame.Rect(x, y, size, size))
    return swatches


def _desenhar_selecao_cor(tela, painel, swatches, cor_atual_idx, cores_em_uso,
                          mouse_pos, fonte_titulo, fonte_desc, fonte_dica):
    """Desenha a tela de personalização de cor por cima do lobby."""
    # Escurecer o fundo
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    tela.blit(overlay, (0, 0))

    # Painel
    painel_surf = pygame.Surface((painel.width, painel.height), pygame.SRCALPHA)
    painel_surf.fill((20, 18, 32, 245))
    tela.blit(painel_surf, painel.topleft)
    pygame.draw.rect(tela, (140, 90, 200), painel, 3, 14)
    pygame.draw.rect(tela, (200, 150, 240), painel, 1, 14)

    # Título
    tit = fonte_titulo.render("PERSONALIZAR COR", True, (230, 200, 255))
    tela.blit(tit, (painel.centerx - tit.get_width() // 2, painel.y + 30))

    # Amostras de cor
    for i, rect in enumerate(swatches):
        cor = PALETA_JOGADORES[i]
        selecionado = (i == cor_atual_idx)
        # Ocupada por OUTRO jogador (não pode escolher)
        ocupada = (i in cores_em_uso) and not selecionado
        hover = rect.collidepoint(mouse_pos)

        cor_escura, cor_brilhante = _gerar_cor_derivadas(cor)

        # Amostra
        if ocupada:
            cor_draw = tuple(c // 3 for c in cor)
        else:
            cor_draw = cor
        pygame.draw.rect(tela, cor_escura if not ocupada else (30, 28, 40),
                         (rect.x + 3, rect.y + 3, rect.width, rect.height), 0, 10)
        pygame.draw.rect(tela, cor_draw, rect, 0, 10)
        if not ocupada:
            pygame.draw.rect(tela, cor_brilhante, (rect.x + 8, rect.y + 8, 14, 14), 0, 4)

        # Borda / realce
        if selecionado:
            pygame.draw.rect(tela, BRANCO, rect.inflate(8, 8), 3, 12)
            # Marca de check
            cx, cy = rect.centerx, rect.centery
            pygame.draw.lines(tela, BRANCO, False,
                              [(cx - 14, cy), (cx - 4, cy + 12), (cx + 16, cy - 14)], 4)
        elif ocupada:
            # X indicando indisponível
            cx, cy = rect.centerx, rect.centery
            pygame.draw.line(tela, (200, 80, 80), (cx - 14, cy - 14), (cx + 14, cy + 14), 4)
            pygame.draw.line(tela, (200, 80, 80), (cx + 14, cy - 14), (cx - 14, cy + 14), 4)
        elif hover:
            pygame.draw.rect(tela, (230, 230, 255), rect, 3, 12)

    # Legenda "ocupada"
    leg = fonte_desc.render("X = cor ja usada por outro jogador", True, (180, 130, 130))
    tela.blit(leg, (painel.centerx - leg.get_width() // 2, painel.bottom - 58))

    # Dica de rodapé
    dica = "Setas/Mouse: Escolher  |  ENTER ou Clique: Aplicar  |  ESC: Voltar"
    dica_s = fonte_dica.render(dica, True, (180, 160, 200))
    tela.blit(dica_s, (painel.centerx - dica_s.get_width() // 2, painel.bottom - 32))


# ============================================================
#  TELA DE COSMÉTICOS (overlay do portal COSMETICOS)
# ============================================================

# Colunas da grade de cards de cosméticos
COSM_COLS = 4


def _calcular_painel_cosmetico():
    """Retorna o Rect do painel central da tela de cosméticos."""
    pw, ph = 760, 470
    px = LARGURA // 2 - pw // 2
    py = ALTURA_JOGO // 2 - ph // 2
    return pygame.Rect(px, py, pw, ph)


def _calcular_abas_cosmetico(painel):
    """Retorna os Rects das duas abas (cabeça, corpo)."""
    aba_w, aba_h = 160, 34
    gap = 16
    total = aba_w * 2 + gap
    x0 = painel.centerx - total // 2
    y = painel.y + 62
    aba_cabeca = pygame.Rect(x0, y, aba_w, aba_h)
    aba_corpo = pygame.Rect(x0 + aba_w + gap, y, aba_w, aba_h)
    return aba_cabeca, aba_corpo


def _calcular_cards_cosmetico(painel, n_itens):
    """Retorna os Rects dos cards (grade de COSM_COLS colunas) para n_itens itens."""
    cards = []
    card_w, card_h = 150, 150
    cols = COSM_COLS
    gap_x = (painel.width - card_w * cols) // (cols + 1)
    gap_y = 18
    y0 = painel.y + 116
    for i in range(n_itens):
        c = i % cols
        r = i // cols
        x = painel.x + gap_x + c * (card_w + gap_x)
        y = y0 + r * (card_h + gap_y)
        cards.append(pygame.Rect(x, y, card_w, card_h))
    return cards


def _preview_jogador_card(tela, rect, cor_preview, cabeca_tipo, corpo_tipo):
    """Desenha o mini-jogador (com combinação de cosméticos) dentro de um card."""
    tam = TAM_PLAYER
    px = rect.centerx - tam // 2
    py = rect.y + 58
    cor_escura, cor_brilhante = _gerar_cor_derivadas(cor_preview)
    pygame.draw.rect(tela, cor_escura, (px, py, tam, tam), 0, 5)
    pygame.draw.rect(tela, cor_preview, (px + 2, py + 2, tam - 4, tam - 4), 0, 3)
    pygame.draw.rect(tela, cor_brilhante, (px + 4, py + 4, 7, 7), 0, 2)
    _desenhar_corpo(tela, px, py, tam, corpo_tipo)
    _desenhar_cabeca(tela, px, py, tam, cabeca_tipo)


def _desenhar_selecao_cosmetico(tela, painel, aba, cards, sel_idx,
                                cor_preview, cabeca_tipo, corpo_tipo, mouse_pos,
                                fonte_titulo, fonte_card, fonte_dica):
    """
    Desenha a tela de cosméticos com abas (cabeça/corpo).
    aba: 'cabeca' ou 'corpo'. Os cards preview mostram a COMBINAÇÃO atual,
    trocando apenas o slot da aba ativa pelo item do card.
    """
    lista = COSMETICOS_CABECA if aba == 'cabeca' else COSMETICOS_CORPO

    # Escurecer o fundo
    overlay = pygame.Surface((LARGURA, ALTURA_JOGO), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    tela.blit(overlay, (0, 0))

    # Painel
    painel_surf = pygame.Surface((painel.width, painel.height), pygame.SRCALPHA)
    painel_surf.fill((20, 18, 32, 245))
    tela.blit(painel_surf, painel.topleft)
    pygame.draw.rect(tela, (60, 150, 180), painel, 3, 14)
    pygame.draw.rect(tela, (130, 210, 240), painel, 1, 14)

    # Título
    tit = fonte_titulo.render("COSMETICOS", True, (190, 235, 255))
    tela.blit(tit, (painel.centerx - tit.get_width() // 2, painel.y + 22))

    # Abas
    aba_cabeca, aba_corpo = _calcular_abas_cosmetico(painel)
    for nome_aba, r, ativa in (("CABECA", aba_cabeca, aba == 'cabeca'),
                               ("CORPO", aba_corpo, aba == 'corpo')):
        if ativa:
            pygame.draw.rect(tela, (60, 150, 180), r, 0, 8)
            pygame.draw.rect(tela, BRANCO, r, 2, 8)
            cor_txt = BRANCO
        else:
            pygame.draw.rect(tela, (34, 40, 52), r, 0, 8)
            pygame.draw.rect(tela, (80, 100, 120), r, 1, 8)
            cor_txt = (150, 170, 190)
        ts = fonte_card.render(nome_aba, True, cor_txt)
        tela.blit(ts, (r.centerx - ts.get_width() // 2, r.centery - ts.get_height() // 2))

    # Cards da aba ativa
    for i, rect in enumerate(cards):
        item = lista[i]
        selecionado = (i == sel_idx)
        hover = rect.collidepoint(mouse_pos)
        realce = selecionado or hover

        cor_fundo = (46, 60, 72) if realce else (34, 42, 52)
        pygame.draw.rect(tela, cor_fundo, rect, 0, 12)
        if selecionado:
            pygame.draw.rect(tela, BRANCO, rect, 3, 12)
        elif hover:
            pygame.draw.rect(tela, (150, 220, 255), rect, 2, 12)
        else:
            pygame.draw.rect(tela, (70, 90, 105), rect, 2, 12)

        # Preview combinando: aba ativa recebe este item, a outra mantém o atual
        if aba == 'cabeca':
            cab, corp = item['tipo'], corpo_tipo
        else:
            cab, corp = cabeca_tipo, item['tipo']
        _preview_jogador_card(tela, rect, cor_preview, cab, corp)

        # Nome + descrição
        nome_s = fonte_card.render(item['nome'], True, BRANCO if realce else (210, 220, 230))
        tela.blit(nome_s, (rect.centerx - nome_s.get_width() // 2, rect.bottom - 42))
        desc_s = fonte_dica.render(item['desc'], True, (160, 190, 205))
        tela.blit(desc_s, (rect.centerx - desc_s.get_width() // 2, rect.bottom - 22))

        # Check de equipado
        if selecionado:
            cx, cy = rect.right - 18, rect.y + 18
            pygame.draw.circle(tela, (60, 200, 90), (cx, cy), 10)
            pygame.draw.lines(tela, BRANCO, False,
                              [(cx - 4, cy), (cx - 1, cy + 4), (cx + 5, cy - 4)], 3)

    # Dica de rodapé
    dica = "TAB/Q/E: Trocar aba  |  Setas/Mouse: Escolher  |  ENTER/Clique: Equipar  |  ESC: Voltar"
    dica_s = fonte_dica.render(dica, True, (160, 200, 220))
    tela.blit(dica_s, (painel.centerx - dica_s.get_width() // 2, painel.bottom - 30))


# ============================================================
#  LOOP PRINCIPAL DO LOBBY
# ============================================================

def _lobby_loop(tela, relogio, gradiente, cliente, config, is_host, servidor=None):
    """Loop do lobby interativo. Compartilhado entre host e cliente."""
    print(f"[LOBBY] Sala SquareStorm aberta ({'HOST' if is_host else 'CLIENTE'})")

    # Fontes
    try:
        fonte_grande = pygame.font.Font(FONTE_PIXEL_PATH, 24)
        fonte_lobby_sub = pygame.font.Font(FONTE_PIXEL_PATH, 12)
    except:
        fonte_grande = pygame.font.SysFont("Arial", 34, True)
        fonte_lobby_sub = pygame.font.SysFont("Arial", 14)
    fonte_titulo = pygame.font.SysFont("Arial", 16, True)
    fonte_peq = pygame.font.SysFont("Arial", 13)
    fonte_nomes = pygame.font.SysFont("Arial", 12)
    fonte_msg = pygame.font.SysFont("Arial", 20, True)
    fonte_ip = pygame.font.SysFont("Arial", 14)
    # Fontes da tela de seleção de minigame
    fonte_sel_titulo = pygame.font.SysFont("Arial", 26, True)
    fonte_sel_card = pygame.font.SysFont("Arial", 18, True)
    fonte_sel_desc = pygame.font.SysFont("Arial", 13)
    fonte_sel_dica = pygame.font.SysFont("Arial", 13)

    # Área da sala
    margem = 25
    topo = 65
    base = 40
    sala = pygame.Rect(margem, topo, LARGURA - margem * 2, ALTURA_JOGO - topo - base)

    # Portais
    portais_rects = _calcular_portais(sala)

    # Jogador local - posição (usar posição do servidor se disponível)
    if cliente.local_player_pos:
        jx = float(cliente.local_player_pos[0])
        jy = float(cliente.local_player_pos[1])
    else:
        jx = float(sala.centerx - TAM_PLAYER // 2)
        jy = float(sala.bottom - 90)

    # Aparência do jogador local. IMPORTANTE: o id só é conhecido depois do
    # full_sync, que pode chegar DEPOIS do lobby abrir. Por isso o id é lido
    # dinamicamente (_meu_id) e a cor padrão é derivada dele; a cor/chapéu só
    # ficam "fixos" quando o jogador personaliza.
    cor_customizada = None   # índice escolhido no portal COR (None = padrão do id)
    cabeca_local = 0         # índice em COSMETICOS_CABECA
    corpo_local = 0          # índice em COSMETICOS_CORPO

    def _meu_id():
        return cliente.local_player_id or 1

    def _meu_cor_index():
        if cor_customizada is not None:
            return cor_customizada
        return (_meu_id() - 1) % len(PALETA_JOGADORES)

    # Aparência dos jogadores remotos, sincronizada via relay.
    cores_jogadores = {}     # {player_id: color_index}
    cabeca_jogadores = {}    # {player_id: head_index}
    corpo_jogadores = {}     # {player_id: body_index}
    pids_conhecidos = set()  # ids remotos já vistos (para reenviar aparência)

    def _cor_index_de(pid):
        """Índice de cor de um jogador remoto (escolhida ou padrão do id)."""
        return cores_jogadores.get(pid, (pid - 1) % len(PALETA_JOGADORES))

    def _cabeca_de(pid):
        """Índice de cosmético de cabeça de um jogador remoto (0 = nenhum)."""
        return cabeca_jogadores.get(pid, 0)

    def _corpo_de(pid):
        """Índice de cosmético de corpo de um jogador remoto (0 = nenhum)."""
        return corpo_jogadores.get(pid, 0)

    def _broadcast_meu_visual():
        """Envia cor + cosméticos do jogador local para todos (relay via servidor)."""
        cliente.send_minigame_action({
            'action': 'lobby_visual',
            'color_index': _meu_cor_index(),
            'head_index': cabeca_local,
            'body_index': corpo_local,
        })

    # Avisa a todos a nossa aparência ao entrar no lobby
    _broadcast_meu_visual()

    # Pulsação
    pulsacao = 0
    ultimo_pulso = 0

    # Timer de zona
    zona_atual = -1
    zona_timer_start = 0

    # Tela de seleção de minigame (aberta pelo portal PLAY)
    mostrando_selecao = False
    sel_idx = 0
    painel_sel = _calcular_painel_selecao()
    cards_sel = _calcular_cards_selecao(painel_sel)

    # Tela de personalização de cor (aberta pelo portal COR)
    mostrando_cor = False
    cor_sel_idx = _meu_cor_index()
    painel_cor = _calcular_painel_cor()
    swatches_cor = _calcular_swatches_cor(painel_cor)

    # Tela de cosméticos (aberta pelo portal COSMETICOS) - abas cabeça/corpo
    mostrando_cosmetico = False
    cosm_aba = 'cabeca'
    cosm_sel_idx = cabeca_local
    painel_cosm = _calcular_painel_cosmetico()
    aba_cabeca_rect, aba_corpo_rect = _calcular_abas_cosmetico(painel_cosm)
    cards_cabeca = _calcular_cards_cosmetico(painel_cosm, len(COSMETICOS_CABECA))
    cards_corpo = _calcular_cards_cosmetico(painel_cosm, len(COSMETICOS_CORPO))

    def _cards_cosm_ativos():
        return cards_cabeca if cosm_aba == 'cabeca' else cards_corpo

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
    game_start_data = [None]

    def on_game_start(data):
        game_start_data[0] = data

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

        # Converte a posição do mouse (janela real) para coordenadas do jogo,
        # senão o hover/clique fica desalinhado em tela cheia.
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())

        meu_id = _meu_id()

        def _iniciar_minigame(mg):
            """Monta os dados e dispara o início do minigame escolhido (host)."""
            idx = _meu_cor_index()
            cust = {
                'cor': PALETA_JOGADORES[idx],
                'cor_nome': str(idx),
                'cosmetico_cabeca': COSMETICOS_CABECA[cabeca_local]['tipo'],
                'cosmetico_corpo': COSMETICOS_CORPO[corpo_local]['tipo'],
                'bots': bots,
                'modo': mg['nome'],
                'seed': random.randint(0, 2**31),
            }
            print(f"[LOBBY] Host iniciou {mg['nome']}!")
            servidor.broadcast_game_start(modo=mg['nome'], seed=cust['seed'])
            return ("start", cust)

        # ========== SINCRONIZAÇÃO DE APARÊNCIA (cor + cosméticos) ==========
        # Aplica a aparência recebida dos outros jogadores (relay MINIGAME_ACTION)
        for acao in cliente.get_minigame_actions():
            if acao.get('action') == 'lobby_visual':
                pid = acao.get('player_id')
                if pid is None or pid == meu_id:
                    continue
                ci = acao.get('color_index')
                hi = acao.get('head_index')
                bi = acao.get('body_index')
                if ci is not None:
                    cores_jogadores[pid] = ci % len(PALETA_JOGADORES)
                if hi is not None:
                    cabeca_jogadores[pid] = hi % len(COSMETICOS_CABECA)
                if bi is not None:
                    corpo_jogadores[pid] = bi % len(COSMETICOS_CORPO)

        # Gossip: quando um novo jogador entra, reenviamos nossa aparência para ele
        pids_atuais = set(cliente.get_remote_players().keys())
        if pids_atuais - pids_conhecidos:
            _broadcast_meu_visual()
        for pid_saiu in pids_conhecidos - pids_atuais:
            cores_jogadores.pop(pid_saiu, None)
            cabeca_jogadores.pop(pid_saiu, None)
            corpo_jogadores.pop(pid_saiu, None)
        pids_conhecidos = pids_atuais

        # Cores atualmente usadas por OUTROS jogadores (bloqueadas no seletor)
        cores_em_uso = set(_cor_index_de(pid) for pid in pids_atuais)

        # ========== EVENTOS ==========
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return ("cancel", None)

            if mostrando_selecao:
                # --- Eventos da tela de seleção de minigame ---
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        mostrando_selecao = False
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        sel_idx = (sel_idx + 1) % len(cards_sel)
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        sel_idx = (sel_idx - 1) % len(cards_sel)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        sel_idx = (sel_idx + 3) % len(cards_sel)
                    elif ev.key in (pygame.K_UP, pygame.K_w):
                        sel_idx = (sel_idx - 3) % len(cards_sel)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if MINIGAMES[sel_idx]['disponivel']:
                            return _iniciar_minigame(MINIGAMES[sel_idx])
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    click_pos = convert_mouse_position(ev.pos)
                    for ci, crect in enumerate(cards_sel):
                        if crect.collidepoint(click_pos):
                            sel_idx = ci
                            if MINIGAMES[ci]['disponivel']:
                                return _iniciar_minigame(MINIGAMES[ci])
                            break
                continue

            if mostrando_cor:
                # --- Eventos da tela de personalização de cor ---
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        mostrando_cor = False
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        cor_sel_idx = (cor_sel_idx + 1) % len(swatches_cor)
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        cor_sel_idx = (cor_sel_idx - 1) % len(swatches_cor)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        cor_sel_idx = (cor_sel_idx + 4) % len(swatches_cor)
                    elif ev.key in (pygame.K_UP, pygame.K_w):
                        cor_sel_idx = (cor_sel_idx - 4) % len(swatches_cor)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if cor_sel_idx not in cores_em_uso:
                            cor_customizada = cor_sel_idx
                            _broadcast_meu_visual()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    click_pos = convert_mouse_position(ev.pos)
                    for ci, srect in enumerate(swatches_cor):
                        if srect.collidepoint(click_pos):
                            if ci not in cores_em_uso:
                                cor_sel_idx = ci
                                cor_customizada = ci
                                _broadcast_meu_visual()
                            break
                continue

            if mostrando_cosmetico:
                # --- Eventos da tela de cosméticos (abas cabeça/corpo) ---
                cards_ativos = _cards_cosm_ativos()
                n = len(cards_ativos)

                def _ir_para_aba(nova):
                    nonlocal cosm_aba, cosm_sel_idx
                    cosm_aba = nova
                    cosm_sel_idx = cabeca_local if nova == 'cabeca' else corpo_local

                def _aplicar_cosmetico(idx):
                    nonlocal cabeca_local, corpo_local
                    if cosm_aba == 'cabeca':
                        cabeca_local = idx
                    else:
                        corpo_local = idx
                    _broadcast_meu_visual()

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        mostrando_cosmetico = False
                    elif ev.key in (pygame.K_TAB, pygame.K_q, pygame.K_e):
                        _ir_para_aba('corpo' if cosm_aba == 'cabeca' else 'cabeca')
                    elif ev.key == pygame.K_RIGHT:
                        cosm_sel_idx = (cosm_sel_idx + 1) % n
                    elif ev.key == pygame.K_LEFT:
                        cosm_sel_idx = (cosm_sel_idx - 1) % n
                    elif ev.key == pygame.K_DOWN:
                        cosm_sel_idx = (cosm_sel_idx + COSM_COLS) % n
                    elif ev.key == pygame.K_UP:
                        cosm_sel_idx = (cosm_sel_idx - COSM_COLS) % n
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        _aplicar_cosmetico(cosm_sel_idx)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    click_pos = convert_mouse_position(ev.pos)
                    if aba_cabeca_rect.collidepoint(click_pos):
                        _ir_para_aba('cabeca')
                    elif aba_corpo_rect.collidepoint(click_pos):
                        _ir_para_aba('corpo')
                    else:
                        for ci, crect in enumerate(cards_ativos):
                            if crect.collidepoint(click_pos):
                                cosm_sel_idx = ci
                                _aplicar_cosmetico(ci)
                                break
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return ("cancel", None)

        # ========== GAME START ==========
        if game_start_data[0] is not None:
            idx = _meu_cor_index()
            gsd = game_start_data[0]
            return ("start", {
                'cor': PALETA_JOGADORES[idx],
                'cor_nome': str(idx),
                'cosmetico_cabeca': COSMETICOS_CABECA[cabeca_local]['tipo'],
                'cosmetico_corpo': COSMETICOS_CORPO[corpo_local]['tipo'],
                'bots': bots,
                'modo': gsd.get('modo', 'Bomb'),
                'seed': gsd.get('seed'),
            })

        # Enquanto qualquer tela (minigame, cor ou cosméticos) está aberta,
        # o jogador fica parado e não interage com os portais.
        overlay_aberto = mostrando_selecao or mostrando_cor or mostrando_cosmetico

        # ========== MOVIMENTO ==========
        teclas = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if not overlay_aberto:
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

        # Enviar input (parado quando alguma tela está aberta)
        if overlay_aberto:
            keys_net = {'w': False, 's': False, 'a': False, 'd': False}
        else:
            keys_net = {
                'w': bool(teclas[pygame.K_w] or teclas[pygame.K_UP]),
                's': bool(teclas[pygame.K_s] or teclas[pygame.K_DOWN]),
                'a': bool(teclas[pygame.K_a] or teclas[pygame.K_LEFT]),
                'd': bool(teclas[pygame.K_d] or teclas[pygame.K_RIGHT]),
            }
        # Cliente-autoritativo: enviamos a posição real (jx, jy) para o servidor
        # repassar aos outros. Assim todos veem o jogador na mesma posição.
        cliente.send_player_input(keys_net, 0, 0, False, float(jx), float(jy))
        cliente.update_interpolation(dt)

        # Pulsação (ciclo 0-11)
        if tempo - ultimo_pulso > 100:
            ultimo_pulso = tempo
            pulsacao = (pulsacao + 1) % 12

        # ========== DETECÇÃO DE PORTAL ==========
        progresso = 0.0
        if overlay_aberto:
            # Com alguma tela aberta, nenhum portal está sendo carregado.
            zona_atual = -1
            zona_timer_start = 0
        else:
            pisando = -1
            centro_jx = jx + TAM_PLAYER // 2
            centro_jy = jy + TAM_PLAYER // 2
            for i, pr in enumerate(portais_rects):
                # Checar se centro está dentro do retângulo do portal
                if pr.collidepoint(centro_jx, centro_jy):
                    pisando = i
                    break

            if pisando != zona_atual:
                zona_atual = pisando
                zona_timer_start = tempo if pisando >= 0 else 0

            if zona_atual >= 0 and zona_timer_start > 0:
                t_zona = tempo - zona_timer_start
                progresso = min(1.0, t_zona / TEMPO_ZONA)

                if t_zona >= TEMPO_ZONA:
                    portal = PORTAIS[zona_atual]
                    acao = portal.get('acao', 'em_breve')
                    if acao == 'play':
                        if is_host:
                            # Abre a tela de seleção de minigame (só o host)
                            mostrando_selecao = True
                            sel_idx = 0
                            zona_atual = -1
                            zona_timer_start = 0
                        else:
                            msg = "Somente o HOST pode iniciar!"
                            msg_fim = tempo + 2000
                            zona_timer_start = tempo
                    elif acao == 'cor':
                        # Abre a tela de personalização de cor (qualquer jogador)
                        mostrando_cor = True
                        cor_sel_idx = _meu_cor_index()
                        zona_atual = -1
                        zona_timer_start = 0
                    elif acao == 'cosmetico':
                        # Abre a tela de cosméticos (qualquer jogador)
                        mostrando_cosmetico = True
                        cosm_aba = 'cabeca'
                        cosm_sel_idx = cabeca_local
                        zona_atual = -1
                        zona_timer_start = 0
                    else:
                        msg = f"{portal['nome'].replace(chr(10), ' ')}: EM BREVE!"
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

        # Jogadores remotos (cor + cosméticos sincronizados, iguais para todos)
        remotos = cliente.get_remote_players()
        for idx, (pid, rp) in enumerate(remotos.items()):
            cor_r = PALETA_JOGADORES[_cor_index_de(pid)]
            cabeca_r = COSMETICOS_CABECA[_cabeca_de(pid)]['tipo']
            corpo_r = COSMETICOS_CORPO[_corpo_de(pid)]['tipo']
            _desenhar_player(tela, rp.x, rp.y, cor_r, rp.name, fonte_nomes,
                             is_host=False, pulsacao=pulsacao,
                             cabeca_tipo=cabeca_r, corpo_tipo=corpo_r)

        # Jogador local (por cima)
        cor_local = PALETA_JOGADORES[_meu_cor_index()]
        _desenhar_player(tela, jx, jy, cor_local,
                         config.get('player_name', 'Jogador'), fonte_nomes,
                         is_host=is_host, pulsacao=pulsacao,
                         cabeca_tipo=COSMETICOS_CABECA[cabeca_local]['tipo'],
                         corpo_tipo=COSMETICOS_CORPO[corpo_local]['tipo'])

        # Barra de timer
        if zona_atual >= 0 and progresso > 0:
            _desenhar_barra_timer(tela, jx, jy, progresso, fonte_peq)

        # ========== UI OVERLAY ==========

        # Título estilizado (pixel)
        titulo = fonte_grande.render("SQUARESTORM", True, (200, 200, 255))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 8))

        # Subtítulo (pixel)
        sub = fonte_lobby_sub.render("LOBBY", True, (120, 120, 160))
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 38))

        # IP
 

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
        inst = "WASD: Mover  |  ESC: Sair  |  PLAY: minigame  |  COR: cor  |  COSMETICOS: chapeu/oculos..."
        is_s = fonte_peq.render(inst, True, (100, 100, 120))
        tela.blit(is_s, (LARGURA // 2 - is_s.get_width() // 2, ALTURA_JOGO - 18))

        # ========== TELAS SOBREPOSTAS (por cima de tudo) ==========
        if mostrando_selecao:
            _desenhar_selecao_minigames(
                tela, painel_sel, cards_sel, sel_idx, mouse_pos, tempo,
                fonte_sel_titulo, fonte_sel_card, fonte_sel_desc, fonte_sel_dica)
        elif mostrando_cor:
            _desenhar_selecao_cor(
                tela, painel_cor, swatches_cor, cor_sel_idx, cores_em_uso,
                mouse_pos, fonte_sel_titulo, fonte_sel_desc, fonte_sel_dica)
        elif mostrando_cosmetico:
            _desenhar_selecao_cosmetico(
                tela, painel_cosm, cosm_aba, _cards_cosm_ativos(), cosm_sel_idx,
                PALETA_JOGADORES[_meu_cor_index()],
                COSMETICOS_CABECA[cabeca_local]['tipo'],
                COSMETICOS_CORPO[corpo_local]['tipo'], mouse_pos,
                fonte_sel_titulo, fonte_sel_card, fonte_sel_dica)

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
