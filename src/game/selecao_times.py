#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de seleção de times para o modo multiplayer.

Time T (Terroristas):
- Objetivo: Plantar a bomba no site
- Cor: Vermelho
- Classe especiais disponíveis

Time Q (Counter-Terrorists):
- Objetivo: Defender os sites / Defusar bomba
- Cor: Azul
- Classes especiais disponíveis
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import desenhar_texto


class SelecaoTimes:
    """Tela de seleção de times para o modo multiplayer."""

    # Cores dos times
    COR_TIME_T = (255, 100, 100)  # Vermelho claro
    COR_TIME_Q = (100, 150, 255)  # Azul claro

    def __init__(self, tela, relogio, fonte_titulo, fonte_normal, gradiente_jogo=None, cliente=None):
        """
        Inicializa a tela de seleção de times.

        Args:
            tela: Surface do pygame
            relogio: Clock do pygame
            fonte_titulo: Fonte para títulos
            fonte_normal: Fonte para texto normal
            gradiente_jogo: Gradiente de fundo (opcional)
            cliente: Cliente de rede para status de jogadores (opcional)
        """
        self.tela = tela
        self.relogio = relogio
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.gradiente_jogo = gradiente_jogo
        self.cliente = cliente

        self.time_selecionado = None
        self.hover_time = None

        # Animações
        self.tempo_inicio = pygame.time.get_ticks()
        self.particulas = []
        self.quadrados_fundo = []
        self._inicializar_quadrados_fundo()

        # Posições dos botões
        self.btn_time_t = pygame.Rect(LARGURA // 4 - 140, ALTURA // 2 - 100, 280, 200)
        self.btn_time_q = pygame.Rect(3 * LARGURA // 4 - 140, ALTURA // 2 - 100, 280, 200)
        self.btn_dev_mode = pygame.Rect(LARGURA // 2 - 90, ALTURA - 100, 180, 50)

    def _inicializar_quadrados_fundo(self):
        """Inicializa os quadrados animados do fundo."""
        for _ in range(25):
            self.quadrados_fundo.append({
                'x': random.randint(0, LARGURA),
                'y': random.randint(0, ALTURA),
                'tamanho': random.randint(15, 40),
                'vel_x': random.uniform(-0.5, 0.5),
                'vel_y': random.uniform(-0.3, 0.3),
                'cor': random.choice([self.COR_TIME_T, self.COR_TIME_Q]),
                'alpha': random.randint(20, 60),
                'rotacao': random.uniform(0, 360),
                'vel_rot': random.uniform(-1, 1)
            })

    def _atualizar_quadrados_fundo(self):
        """Atualiza posição dos quadrados do fundo."""
        for q in self.quadrados_fundo:
            q['x'] += q['vel_x']
            q['y'] += q['vel_y']
            q['rotacao'] += q['vel_rot']

            # Wrap around
            if q['x'] < -50:
                q['x'] = LARGURA + 50
            elif q['x'] > LARGURA + 50:
                q['x'] = -50
            if q['y'] < -50:
                q['y'] = ALTURA + 50
            elif q['y'] > ALTURA + 50:
                q['y'] = -50

    def _criar_particula_explosao(self, x, y, cor):
        """Cria partículas de explosão ao selecionar time."""
        for _ in range(20):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(3, 8)
            self.particulas.append({
                'x': x,
                'y': y,
                'vel_x': math.cos(angulo) * velocidade,
                'vel_y': math.sin(angulo) * velocidade,
                'vida': 60,
                'cor': cor,
                'tamanho': random.randint(4, 10)
            })

    def _atualizar_particulas(self):
        """Atualiza e remove partículas expiradas."""
        for p in self.particulas[:]:
            p['x'] += p['vel_x']
            p['y'] += p['vel_y']
            p['vel_y'] += 0.2  # Gravidade
            p['vida'] -= 1
            p['tamanho'] = max(1, p['tamanho'] - 0.1)
            if p['vida'] <= 0:
                self.particulas.remove(p)

    def executar(self):
        """
        Executa a tela de seleção de times.

        Returns:
            str: 'T', 'Q', 'dev', ou None se cancelou
        """
        from src.utils.display_manager import present_frame, convert_mouse_position

        pygame.mouse.set_visible(True)
        rodando = True

        while rodando:
            tempo_atual = pygame.time.get_ticks()

            # Processar eventos
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return None

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return None
                    if evento.key == pygame.K_t:
                        self._criar_particula_explosao(
                            self.btn_time_t.centerx, self.btn_time_t.centery, self.COR_TIME_T)
                        return 'T'
                    if evento.key == pygame.K_q:
                        self._criar_particula_explosao(
                            self.btn_time_q.centerx, self.btn_time_q.centery, self.COR_TIME_Q)
                        return 'Q'
                    if evento.key == pygame.K_d:
                        return 'dev'

                if evento.type == pygame.MOUSEMOTION:
                    mouse_pos = convert_mouse_position(evento.pos)
                    self.hover_time = None
                    if self.btn_time_t.collidepoint(mouse_pos):
                        self.hover_time = 'T'
                    elif self.btn_time_q.collidepoint(mouse_pos):
                        self.hover_time = 'Q'

                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    mouse_pos = convert_mouse_position(evento.pos)
                    if self.btn_time_t.collidepoint(mouse_pos):
                        self._criar_particula_explosao(
                            self.btn_time_t.centerx, self.btn_time_t.centery, self.COR_TIME_T)
                        return 'T'
                    if self.btn_time_q.collidepoint(mouse_pos):
                        self._criar_particula_explosao(
                            self.btn_time_q.centerx, self.btn_time_q.centery, self.COR_TIME_Q)
                        return 'Q'
                    if self.btn_dev_mode.collidepoint(mouse_pos):
                        return 'dev'

            # Atualizar animações
            self._atualizar_quadrados_fundo()
            self._atualizar_particulas()

            # Desenhar
            self._desenhar(tempo_atual)
            present_frame()
            self.relogio.tick(60)

        return None

    def _desenhar(self, tempo_atual):
        """Desenha a tela de seleção de times."""
        # Fundo gradiente escuro
        self._desenhar_fundo(tempo_atual)

        # Quadrados animados do fundo
        self._desenhar_quadrados_fundo()

        # Efeito de divisão no meio (vermelho vs azul)
        self._desenhar_divisao_times(tempo_atual)

        # Título principal
        self._desenhar_titulo(tempo_atual)

        # Botões dos times
        self._desenhar_botao_time_t(tempo_atual)
        self._desenhar_botao_time_q(tempo_atual)

        # VS no meio
        self._desenhar_vs(tempo_atual)

        # Status de jogadores (se tiver cliente)
        if self.cliente:
            self._desenhar_status_jogadores()

        # Botão DEV MODE
        self._desenhar_botao_dev(tempo_atual)

        # Partículas
        self._desenhar_particulas()

        # Instruções
        self._desenhar_instrucoes()

    def _desenhar_fundo(self, tempo_atual):
        """Desenha o fundo gradiente animado."""
        # Gradiente vertical com leve animação
        for y in range(ALTURA):
            # Onda sutil no gradiente
            onda = math.sin((y + tempo_atual * 0.05) / 100) * 5
            cor = (
                int(max(0, min(255, 15 + y * 0.01 + onda))),
                int(max(0, min(255, 15 + y * 0.005))),
                int(max(0, min(255, 25 + y * 0.02)))
            )
            pygame.draw.line(self.tela, cor, (0, y), (LARGURA, y))

    def _desenhar_quadrados_fundo(self):
        """Desenha os quadrados animados do fundo."""
        for q in self.quadrados_fundo:
            # Criar surface com alpha
            surf = pygame.Surface((q['tamanho'], q['tamanho']), pygame.SRCALPHA)
            cor_alpha = (*q['cor'], q['alpha'])
            pygame.draw.rect(surf, cor_alpha, (0, 0, q['tamanho'], q['tamanho']), 0, 3)

            # Rotacionar
            rotated = pygame.transform.rotate(surf, q['rotacao'])
            rect = rotated.get_rect(center=(int(q['x']), int(q['y'])))
            self.tela.blit(rotated, rect)

    def _desenhar_divisao_times(self, tempo_atual):
        """Desenha efeito de divisão vermelho/azul no fundo."""
        # Gradiente lateral sutil
        largura_fade = 150
        centro = LARGURA // 2

        # Lado vermelho (Time T)
        for x in range(centro - largura_fade, centro):
            alpha = int((1 - (centro - x) / largura_fade) * 30)
            surf = pygame.Surface((1, ALTURA), pygame.SRCALPHA)
            surf.fill((*self.COR_TIME_T, alpha))
            self.tela.blit(surf, (x, 0))

        # Lado azul (Time Q)
        for x in range(centro, centro + largura_fade):
            alpha = int((1 - (x - centro) / largura_fade) * 30)
            surf = pygame.Surface((1, ALTURA), pygame.SRCALPHA)
            surf.fill((*self.COR_TIME_Q, alpha))
            self.tela.blit(surf, (x, 0))

    def _desenhar_titulo(self, tempo_atual):
        """Desenha o título principal com animações."""
        # Efeito de pulso
        pulso = math.sin(tempo_atual / 400) * 4
        escala = 1 + math.sin(tempo_atual / 600) * 0.02

        # Sombra do título
        desenhar_texto(self.tela, "ESCOLHA SEU TIME", int(65 * escala),
                      (30, 30, 50), LARGURA // 2 + 3, ALTURA // 8 + pulso + 3)

        # Título principal
        desenhar_texto(self.tela, "ESCOLHA SEU TIME", int(65 * escala),
                      BRANCO, LARGURA // 2, ALTURA // 8 + pulso)

        # Subtítulo com brilho
        brilho = int(200 + math.sin(tempo_atual / 300) * 55)
        desenhar_texto(self.tela, "SQUARESTORM MULTIPLAYER", 24,
                      (brilho, brilho, 100), LARGURA // 2, ALTURA // 8 + 55)

    def _desenhar_botao_time_t(self, tempo_atual):
        """Desenha o botão do Time T com visual melhorado."""
        hover = self.hover_time == 'T'
        rect = self.btn_time_t

        # Efeito de hover - expandir
        if hover:
            rect = rect.inflate(15, 15)
            # Glow effect
            for i in range(3):
                glow_rect = rect.inflate(i * 8, i * 8)
                surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(surf, (*self.COR_TIME_T, 30 - i * 10),
                               (0, 0, glow_rect.width, glow_rect.height), 0, 25)
                self.tela.blit(surf, glow_rect)

        # Sombra
        pygame.draw.rect(self.tela, (40, 15, 15),
                        (rect.x + 6, rect.y + 6, rect.width, rect.height), 0, 20)

        # Fundo do botão
        cor_fundo = (80, 30, 30) if not hover else (100, 40, 40)
        pygame.draw.rect(self.tela, cor_fundo, rect, 0, 20)

        # Borda
        cor_borda = (255, 180, 180) if hover else self.COR_TIME_T
        pygame.draw.rect(self.tela, cor_borda, rect, 4, 20)

        # Quadrado representando o time
        self._desenhar_quadrado_preview(rect.centerx, rect.centery - 30,
                                        self.COR_TIME_T, tempo_atual, hover)

        # Nome do time
        cor_texto = BRANCO if hover else (230, 230, 230)
        desenhar_texto(self.tela, "TIME T", 45, cor_texto, rect.centerx, rect.centery + 35)
        desenhar_texto(self.tela, "(Terroristas)", 18, (200, 150, 150), rect.centerx, rect.centery + 65)

        # Objetivo
        desenhar_texto(self.tela, "Plante a bomba!", 14, (180, 120, 120), rect.centerx, rect.centery + 85)

        # Atalho
        desenhar_texto(self.tela, "[T]", 16, (150, 150, 150), rect.centerx, rect.bottom - 15)

    def _desenhar_botao_time_q(self, tempo_atual):
        """Desenha o botão do Time Q com visual melhorado."""
        hover = self.hover_time == 'Q'
        rect = self.btn_time_q

        # Efeito de hover - expandir
        if hover:
            rect = rect.inflate(15, 15)
            # Glow effect
            for i in range(3):
                glow_rect = rect.inflate(i * 8, i * 8)
                surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(surf, (*self.COR_TIME_Q, 30 - i * 10),
                               (0, 0, glow_rect.width, glow_rect.height), 0, 25)
                self.tela.blit(surf, glow_rect)

        # Sombra
        pygame.draw.rect(self.tela, (15, 20, 40),
                        (rect.x + 6, rect.y + 6, rect.width, rect.height), 0, 20)

        # Fundo do botão
        cor_fundo = (30, 40, 80) if not hover else (40, 50, 100)
        pygame.draw.rect(self.tela, cor_fundo, rect, 0, 20)

        # Borda
        cor_borda = (180, 200, 255) if hover else self.COR_TIME_Q
        pygame.draw.rect(self.tela, cor_borda, rect, 4, 20)

        # Quadrado representando o time
        self._desenhar_quadrado_preview(rect.centerx, rect.centery - 30,
                                        self.COR_TIME_Q, tempo_atual, hover)

        # Nome do time
        cor_texto = BRANCO if hover else (230, 230, 230)
        desenhar_texto(self.tela, "TIME Q", 45, cor_texto, rect.centerx, rect.centery + 35)
        desenhar_texto(self.tela, "(Counter-Terrorists)", 18, (150, 150, 200), rect.centerx, rect.centery + 65)

        # Objetivo
        desenhar_texto(self.tela, "Defenda o site!", 14, (120, 150, 200), rect.centerx, rect.centery + 85)

        # Atalho
        desenhar_texto(self.tela, "[Q]", 16, (150, 150, 150), rect.centerx, rect.bottom - 15)

    def _desenhar_quadrado_preview(self, x, y, cor, tempo_atual, hover):
        """Desenha um quadrado preview representando o jogador do time."""
        tamanho = 55 if hover else 50
        pulso = math.sin(tempo_atual / 200) * 3 if hover else 0

        # Sombra
        pygame.draw.rect(self.tela, (20, 20, 20),
                        (x - tamanho // 2 + 4, y - tamanho // 2 + 4, tamanho, tamanho), 0, 8)

        # Contorno escuro
        cor_escura = tuple(max(0, c - 80) for c in cor)
        pygame.draw.rect(self.tela, cor_escura,
                        (x - tamanho // 2, y - tamanho // 2 + pulso, tamanho, tamanho), 0, 8)

        # Quadrado principal
        pygame.draw.rect(self.tela, cor,
                        (x - tamanho // 2 + 3, y - tamanho // 2 + 3 + pulso, tamanho - 6, tamanho - 6), 0, 6)

        # Brilho
        cor_brilho = tuple(min(255, c + 60) for c in cor)
        pygame.draw.rect(self.tela, cor_brilho,
                        (x - tamanho // 2 + 6, y - tamanho // 2 + 6 + pulso, 12, 12), 0, 3)

    def _desenhar_vs(self, tempo_atual):
        """Desenha o VS no centro da tela."""
        # Efeito de pulso
        escala = 1 + math.sin(tempo_atual / 300) * 0.1
        tamanho = int(50 * escala)

        # Relâmpago/energia entre os times
        centro_y = ALTURA // 2
        for i in range(5):
            offset = math.sin(tempo_atual / 100 + i) * 10
            y = centro_y - 60 + i * 30
            cor_energia = (200 + int(math.sin(tempo_atual / 50 + i) * 55), 200, 255)
            pygame.draw.line(self.tela, cor_energia,
                           (LARGURA // 2 - 5 + offset, y),
                           (LARGURA // 2 + 5 - offset, y + 15), 2)

        # Círculo de fundo
        pygame.draw.circle(self.tela, (40, 40, 60), (LARGURA // 2, centro_y), 45)
        pygame.draw.circle(self.tela, (80, 80, 100), (LARGURA // 2, centro_y), 45, 3)

        # Texto VS
        desenhar_texto(self.tela, "VS", tamanho, (220, 220, 255), LARGURA // 2, centro_y)

    def _desenhar_status_jogadores(self):
        """Desenha o status dos jogadores conectados."""
        status = self.cliente.get_team_status() if hasattr(self.cliente, 'get_team_status') else {}

        if not status:
            return

        y_inicio = ALTURA - 170
        desenhar_texto(self.tela, "Jogadores Conectados:", 18, (150, 150, 150), LARGURA // 2, y_inicio - 25)

        y = y_inicio
        for pid, info in status.items():
            nome = info.get('name', f'Jogador {pid}')
            time = info.get('team', '?')
            cor = self.COR_TIME_T if time == 'T' else self.COR_TIME_Q

            # Mini quadrado do jogador
            pygame.draw.rect(self.tela, cor, (LARGURA // 2 - 100, y - 6, 12, 12), 0, 2)

            texto = f"{nome} - Time {time}"
            desenhar_texto(self.tela, texto, 16, cor, LARGURA // 2 + 20, y)
            y += 25

    def _desenhar_botao_dev(self, tempo_atual):
        """Desenha o botão do modo desenvolvedor."""
        from src.utils.display_manager import convert_mouse_position
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        hover = self.btn_dev_mode.collidepoint(mouse_pos)

        rect = self.btn_dev_mode

        # Cores
        cor_fundo = (40, 80, 40) if not hover else (50, 100, 50)
        cor_borda = (100, 200, 100) if hover else (70, 150, 70)

        # Sombra
        pygame.draw.rect(self.tela, (15, 30, 15),
                        (rect.x + 3, rect.y + 3, rect.width, rect.height), 0, 10)

        # Botão
        pygame.draw.rect(self.tela, cor_fundo, rect, 0, 10)
        pygame.draw.rect(self.tela, cor_borda, rect, 2, 10)

        # Texto
        desenhar_texto(self.tela, "DEV MODE", 20, BRANCO, rect.centerx, rect.centery - 5)
        desenhar_texto(self.tela, "[D]", 12, (150, 200, 150), rect.centerx, rect.centery + 15)

    def _desenhar_particulas(self):
        """Desenha as partículas de explosão."""
        for p in self.particulas:
            alpha = int((p['vida'] / 60) * 255)
            surf = pygame.Surface((int(p['tamanho'] * 2), int(p['tamanho'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['cor'], alpha),
                             (int(p['tamanho']), int(p['tamanho'])), int(p['tamanho']))
            self.tela.blit(surf, (int(p['x'] - p['tamanho']), int(p['y'] - p['tamanho'])))

    def _desenhar_instrucoes(self):
        """Desenha as instruções na parte inferior da tela."""
        desenhar_texto(self.tela, "ESC para voltar ao menu", 16, (100, 100, 100), LARGURA // 2, ALTURA - 30)


class TelaAguardandoJogadores:
    """Tela de espera enquanto aguarda outros jogadores escolherem time."""

    COR_TIME_T = (255, 100, 100)
    COR_TIME_Q = (100, 150, 255)

    def __init__(self, tela, relogio, fonte_titulo, fonte_normal, time_escolhido, cliente=None):
        """
        Inicializa a tela de aguardar jogadores.

        Args:
            tela: Surface do pygame
            relogio: Clock do pygame
            fonte_titulo: Fonte para títulos
            fonte_normal: Fonte para texto normal
            time_escolhido: 'T' ou 'Q'
            cliente: Cliente de rede
        """
        self.tela = tela
        self.relogio = relogio
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.time_escolhido = time_escolhido
        self.cliente = cliente

        self.tempo_inicio = pygame.time.get_ticks()
        self.quadrados_animados = []
        self._inicializar_quadrados()

    def _inicializar_quadrados(self):
        """Inicializa quadrados animados do fundo."""
        cor = self.COR_TIME_T if self.time_escolhido == 'T' else self.COR_TIME_Q
        for _ in range(15):
            self.quadrados_animados.append({
                'x': random.randint(0, LARGURA),
                'y': random.randint(0, ALTURA),
                'tamanho': random.randint(20, 50),
                'vel_y': random.uniform(-1, -0.3),
                'alpha': random.randint(30, 80),
                'cor': cor
            })

    def _atualizar_quadrados(self):
        """Atualiza posição dos quadrados."""
        for q in self.quadrados_animados:
            q['y'] += q['vel_y']
            if q['y'] < -50:
                q['y'] = ALTURA + 50
                q['x'] = random.randint(0, LARGURA)

    def executar(self):
        """
        Executa a tela de aguardar.

        Returns:
            bool: True se todos prontos, False se cancelou, None para continuar
        """
        from src.utils.display_manager import present_frame, convert_mouse_position

        tempo_atual = pygame.time.get_ticks()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return False

        self._atualizar_quadrados()
        self._desenhar(tempo_atual)
        present_frame()
        self.relogio.tick(60)

        return None

    def _desenhar(self, tempo_atual):
        """Desenha a tela de aguardar."""
        # Fundo
        for y in range(ALTURA):
            cor = (
                int(15 + y * 0.01),
                int(15 + y * 0.005),
                int(25 + y * 0.02)
            )
            pygame.draw.line(self.tela, cor, (0, y), (LARGURA, y))

        # Quadrados animados
        for q in self.quadrados_animados:
            surf = pygame.Surface((q['tamanho'], q['tamanho']), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*q['cor'], q['alpha']),
                           (0, 0, q['tamanho'], q['tamanho']), 0, 5)
            self.tela.blit(surf, (int(q['x']), int(q['y'])))

        # Título animado
        pulso = math.sin(tempo_atual / 300) * 5
        desenhar_texto(self.tela, "AGUARDANDO JOGADORES", 50, BRANCO,
                      LARGURA // 2, ALTURA // 4 + pulso)

        # Time escolhido
        cor_time = self.COR_TIME_T if self.time_escolhido == 'T' else self.COR_TIME_Q
        nome_time = "Terroristas" if self.time_escolhido == 'T' else "Counter-Terrorists"

        # Quadrado do jogador
        self._desenhar_quadrado_jogador(LARGURA // 2, ALTURA // 2 - 20, cor_time, tempo_atual)

        desenhar_texto(self.tela, f"Voce e do TIME {self.time_escolhido}", 30, cor_time,
                      LARGURA // 2, ALTURA // 2 + 60)
        desenhar_texto(self.tela, f"({nome_time})", 20, (180, 180, 180),
                      LARGURA // 2, ALTURA // 2 + 90)

        # Animação de carregamento
        dots = "." * (1 + (tempo_atual // 400) % 4)
        desenhar_texto(self.tela, f"Esperando outros jogadores{dots}", 22, AMARELO,
                      LARGURA // 2, ALTURA // 2 + 140)

        # Status dos jogadores
        if self.cliente:
            self._desenhar_status_jogadores()

        # Instrução
        desenhar_texto(self.tela, "ESC para cancelar", 16, (100, 100, 100),
                      LARGURA // 2, ALTURA - 40)

    def _desenhar_quadrado_jogador(self, x, y, cor, tempo_atual):
        """Desenha o quadrado do jogador com animação."""
        tamanho = 60
        pulso = math.sin(tempo_atual / 200) * 3

        # Sombra
        pygame.draw.rect(self.tela, (20, 20, 20),
                        (x - tamanho // 2 + 5, y - tamanho // 2 + 5, tamanho, tamanho), 0, 8)

        # Contorno
        cor_escura = tuple(max(0, c - 80) for c in cor)
        pygame.draw.rect(self.tela, cor_escura,
                        (x - tamanho // 2, y - tamanho // 2 + pulso, tamanho, tamanho), 0, 8)

        # Principal
        pygame.draw.rect(self.tela, cor,
                        (x - tamanho // 2 + 3, y - tamanho // 2 + 3 + pulso, tamanho - 6, tamanho - 6), 0, 6)

        # Brilho
        cor_brilho = tuple(min(255, c + 60) for c in cor)
        pygame.draw.rect(self.tela, cor_brilho,
                        (x - tamanho // 2 + 8, y - tamanho // 2 + 8 + pulso, 15, 15), 0, 4)

    def _desenhar_status_jogadores(self):
        """Desenha o status dos jogadores."""
        status = self.cliente.get_team_status() if hasattr(self.cliente, 'get_team_status') else {}

        if not status:
            return

        y_inicio = ALTURA - 150
        desenhar_texto(self.tela, "Jogadores:", 16, (150, 150, 150), LARGURA // 2, y_inicio - 20)

        y = y_inicio
        for pid, info in status.items():
            nome = info.get('name', f'Jogador {pid}')
            time = info.get('team', '?')
            cor = self.COR_TIME_T if time == 'T' else self.COR_TIME_Q

            pygame.draw.rect(self.tela, cor, (LARGURA // 2 - 80, y - 5, 10, 10), 0, 2)
            desenhar_texto(self.tela, f"{nome} - Time {time}", 14, cor, LARGURA // 2 + 20, y)
            y += 22
