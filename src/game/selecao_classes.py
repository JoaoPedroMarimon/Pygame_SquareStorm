#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de seleção de classes para os times no modo multiplayer.

Classes Time T (Terroristas):
1. Mago - Branco, escudo protetor por 4s (cooldown 10s)
2. Ghost - Cinza-azul, invisibilidade por 4s (cooldown 10s)
3. Granada - Marrom, começa com 3 granadas
4. Metralhadora - Verde-oliva, começa com metralhadora

Classes Time Q (Counter-Terrorists):
1. Cyan - Menos vida, velocidade turbo por 5s (cooldown 15s)
2. Explosive - Visual laranja, explosão de tiros em todas direções
3. Normal - Visual padrão, dash ao pressionar espaço
4. Purple - Mais vida, cor roxa
"""

import pygame
import math
import random
from src.config import *
from src.utils.visual import desenhar_texto


# Definição das classes do Time T
CLASSES_TIME_T = {
    "mago": {
        "nome": "Mago",
        "descricao": "Escudo protetor!",
        "descricao2": "ESPACO: Escudo por 4s",
        "cor": (255, 255, 255),  # Branco
        "cor_escura": (180, 180, 180),
        "vidas": 6,
        "velocidade_base": 1.0,
        "habilidade_duracao": 4000,  # 4 segundos
        "habilidade_cooldown": 10000,  # 10 segundos
        "tem_chapeu_mago": True,
    },
    "ghost": {
        "nome": "Ghost",
        "descricao": "Invisibilidade!",
        "descricao2": "ESPACO: Invisivel por 4s",
        "cor": (150, 150, 200),  # Cinza-azul
        "cor_escura": (100, 100, 150),
        "vidas": 5,
        "velocidade_base": 1.0,
        "habilidade_duracao": 4000,  # 4 segundos
        "habilidade_cooldown": 10000,  # 10 segundos
    },
    "granada": {
        "nome": "Granada",
        "descricao": "Especialista em granadas!",
        "descricao2": "ESPACO: Lanca granada",
        "cor": (101, 67, 33),  # Marrom terra
        "cor_escura": (70, 45, 20),
        "vidas": 5,
        "velocidade_base": 1.0,
        "habilidade_cooldown": 2000,  # 2 segundos
    },
    "metralhadora": {
        "nome": "Metralhadora",
        "descricao": "Fogo rapido!",
        "descricao2": "Metralhadora gratis + 2x dano",
        "cor": (107, 142, 35),  # Verde-oliva
        "cor_escura": (70, 95, 20),
        "vidas": 6,
        "velocidade_base": 1.0,
        "metralhadora_gratis": True,
        "metralhadora_dano_bonus": 2,  # Dano = 2 ao invés de 1
    },
}

# Definição das classes do Time Q
CLASSES_TIME_Q = {
    "cyan": {
        "nome": "Cyan",
        "descricao": "Velocidade extrema!",
        "descricao2": "ESPACO: Turbo por 5s",
        "cor": (0, 255, 255),  # CIANO
        "cor_escura": (0, 150, 150),
        "vidas": 4,  # Menos vida
        "velocidade_base": 1.0,
        "habilidade_duracao": 5000,  # 5 segundos
        "habilidade_cooldown": 15000,  # 15 segundos
    },
    "explosive": {
        "nome": "Explosive",
        "descricao": "Explosao de tiros!",
        "descricao2": "ESPACO: Tiros em todas direcoes",
        "cor": (255, 140, 0),  # Laranja (perseguidor)
        "cor_escura": (180, 100, 0),
        "vidas": 5,
        "velocidade_base": 1.0,
        "habilidade_cooldown": 3000,  # 8 segundos
        "tiros_explosao": 12,
    },
    "normal": {
        "nome": "Player",
        "descricao": "",
        "descricao2": "ESPACO: Dash rapido",
        "cor": (100, 150, 255),  # Azul (Time Q padrão)
        "cor_escura": (60, 100, 180),
        "vidas": 6,
        "velocidade_base": 1.0,
        "dash_velocidade": 25,
        "dash_duracao": 8,
        "habilidade_cooldown": 500,
    },
    "purple": {
        "nome": "Purple",
        "descricao": "Tanque resistente!",
        "descricao2": "Mais vida, sem habilidade",
        "cor": (180, 50, 230),  # ROXO
        "cor_escura": (120, 30, 160),
        "vidas": 11,
        "velocidade_base": 1.0,
    },
}


class SelecaoClasses:
    """Tela de seleção de classes para os times."""

    def __init__(self, tela, relogio, fonte_titulo, fonte_normal, time='Q'):
        self.tela = tela
        self.relogio = relogio
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.time = time
        self.classe_selecionada = None
        self.hover_classe = None

        # Tempo para animações
        self.tempo_inicio = pygame.time.get_ticks()

        # Selecionar classes baseado no time
        if time == 'T':
            self.classes_disponiveis = CLASSES_TIME_T
            self.ordem_classes = ["mago", "ghost", "granada", "metralhadora"]
            self.titulo_time = "Time T - Terroristas"
            self.cor_time = (255, 100, 100)
        else:
            self.classes_disponiveis = CLASSES_TIME_Q
            self.ordem_classes = ["cyan", "explosive", "normal", "purple"]
            self.titulo_time = "Time Q - Counter-Terrorists"
            self.cor_time = (100, 150, 255)

        # Posições dos cards
        self.cards = []
        self._calcular_posicoes_cards()

        # Quadrados animados do fundo
        self.quadrados_fundo = []
        self._inicializar_quadrados_fundo()

        # Partículas
        self.particulas = []

    def _inicializar_quadrados_fundo(self):
        """Inicializa os quadrados animados do fundo."""
        cores_classes = [dados["cor"] for dados in self.classes_disponiveis.values()]
        for _ in range(20):
            self.quadrados_fundo.append({
                'x': random.randint(0, LARGURA),
                'y': random.randint(0, ALTURA),
                'tamanho': random.randint(10, 30),
                'vel_x': random.uniform(-0.3, 0.3),
                'vel_y': random.uniform(-0.5, -0.1),
                'cor': random.choice(cores_classes),
                'alpha': random.randint(15, 40),
                'rotacao': random.uniform(0, 360),
                'vel_rot': random.uniform(-0.5, 0.5)
            })

    def _atualizar_quadrados_fundo(self):
        """Atualiza posição dos quadrados do fundo."""
        for q in self.quadrados_fundo:
            q['x'] += q['vel_x']
            q['y'] += q['vel_y']
            q['rotacao'] += q['vel_rot']

            # Wrap around
            if q['y'] < -50:
                q['y'] = ALTURA + 50
                q['x'] = random.randint(0, LARGURA)
            if q['x'] < -50:
                q['x'] = LARGURA + 50
            elif q['x'] > LARGURA + 50:
                q['x'] = -50

    def _criar_particula(self, x, y, cor):
        """Cria partículas ao selecionar uma classe."""
        for _ in range(15):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(2, 6)
            self.particulas.append({
                'x': x,
                'y': y,
                'vel_x': math.cos(angulo) * velocidade,
                'vel_y': math.sin(angulo) * velocidade,
                'vida': 40,
                'cor': cor,
                'tamanho': random.randint(3, 8)
            })

    def _atualizar_particulas(self):
        """Atualiza e remove partículas expiradas."""
        for p in self.particulas[:]:
            p['x'] += p['vel_x']
            p['y'] += p['vel_y']
            p['vel_y'] += 0.15
            p['vida'] -= 1
            p['tamanho'] = max(1, p['tamanho'] - 0.15)
            if p['vida'] <= 0:
                self.particulas.remove(p)

    def _calcular_posicoes_cards(self):
        """Calcula as posições dos cards de classe na tela."""
        self.cards = []
        card_largura = 170
        card_altura = 240
        espacamento = 35
        total_largura = len(self.ordem_classes) * card_largura + (len(self.ordem_classes) - 1) * espacamento
        inicio_x = (LARGURA - total_largura) // 2
        y = ALTURA // 2 - card_altura // 2 + 20

        for i, classe_id in enumerate(self.ordem_classes):
            x = inicio_x + i * (card_largura + espacamento)
            self.cards.append({
                "id": classe_id,
                "rect": pygame.Rect(x, y, card_largura, card_altura),
                "dados": self.classes_disponiveis[classe_id]
            })

    def executar(self):
        """
        Executa a tela de seleção de classes.

        Returns:
            str: ID da classe selecionada ou None se cancelou
        """
        from src.utils.display_manager import present_frame, convert_mouse_position

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
                    # Atalhos numéricos
                    if evento.key == pygame.K_1:
                        self._criar_particula(self.cards[0]["rect"].centerx,
                                            self.cards[0]["rect"].centery,
                                            self.cards[0]["dados"]["cor"])
                        return self.ordem_classes[0]
                    if evento.key == pygame.K_2:
                        self._criar_particula(self.cards[1]["rect"].centerx,
                                            self.cards[1]["rect"].centery,
                                            self.cards[1]["dados"]["cor"])
                        return self.ordem_classes[1]
                    if evento.key == pygame.K_3:
                        self._criar_particula(self.cards[2]["rect"].centerx,
                                            self.cards[2]["rect"].centery,
                                            self.cards[2]["dados"]["cor"])
                        return self.ordem_classes[2]
                    if evento.key == pygame.K_4:
                        self._criar_particula(self.cards[3]["rect"].centerx,
                                            self.cards[3]["rect"].centery,
                                            self.cards[3]["dados"]["cor"])
                        return self.ordem_classes[3]

                if evento.type == pygame.MOUSEMOTION:
                    mouse_pos = convert_mouse_position(evento.pos)
                    self.hover_classe = None
                    for card in self.cards:
                        if card["rect"].collidepoint(mouse_pos):
                            self.hover_classe = card["id"]
                            break

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  # Clique esquerdo
                        mouse_pos = convert_mouse_position(evento.pos)
                        for card in self.cards:
                            if card["rect"].collidepoint(mouse_pos):
                                self._criar_particula(card["rect"].centerx,
                                                    card["rect"].centery,
                                                    card["dados"]["cor"])
                                return card["id"]

            # Atualizar animações
            self._atualizar_quadrados_fundo()
            self._atualizar_particulas()

            # Desenhar
            self._desenhar(tempo_atual)
            present_frame()
            self.relogio.tick(60)

        return None

    def _desenhar(self, tempo_atual):
        """Desenha a tela de seleção de classes."""
        # Fundo gradiente animado
        self._desenhar_fundo(tempo_atual)

        # Quadrados animados do fundo
        self._desenhar_quadrados_fundo()

        # Linha decorativa do time
        self._desenhar_decoracao_time(tempo_atual)

        # Título
        self._desenhar_titulo(tempo_atual)

        # Desenhar cards
        for i, card in enumerate(self.cards):
            self._desenhar_card(card, i + 1, tempo_atual)

        # Partículas
        self._desenhar_particulas()

        # Instruções
        self._desenhar_instrucoes(tempo_atual)

    def _desenhar_fundo(self, tempo_atual):
        """Desenha o fundo gradiente animado."""
        for y in range(ALTURA):
            # Onda sutil no gradiente
            onda = math.sin((y + tempo_atual * 0.03) / 150) * 3
            cor = (
                int(max(0, min(255, 18 + y * 0.015 + onda))),
                int(max(0, min(255, 18 + y * 0.008))),
                int(max(0, min(255, 35 + y * 0.025)))
            )
            pygame.draw.line(self.tela, cor, (0, y), (LARGURA, y))

    def _desenhar_quadrados_fundo(self):
        """Desenha os quadrados animados do fundo."""
        for q in self.quadrados_fundo:
            surf = pygame.Surface((q['tamanho'], q['tamanho']), pygame.SRCALPHA)
            cor_alpha = (*q['cor'], q['alpha'])
            pygame.draw.rect(surf, cor_alpha, (0, 0, q['tamanho'], q['tamanho']), 0, 3)

            rotated = pygame.transform.rotate(surf, q['rotacao'])
            rect = rotated.get_rect(center=(int(q['x']), int(q['y'])))
            self.tela.blit(rotated, rect)

    def _desenhar_decoracao_time(self, tempo_atual):
        """Desenha decorações com a cor do time."""
        # Linhas laterais pulsantes
        pulso = math.sin(tempo_atual / 500) * 0.3 + 0.7
        cor_linha = tuple(int(c * pulso) for c in self.cor_time)

        # Linha superior
        pygame.draw.line(self.tela, cor_linha, (50, 140), (LARGURA - 50, 140), 2)

        # Detalhes nas pontas
        pygame.draw.circle(self.tela, self.cor_time, (50, 140), 5)
        pygame.draw.circle(self.tela, self.cor_time, (LARGURA - 50, 140), 5)

        # Linha inferior
        pygame.draw.line(self.tela, cor_linha, (100, ALTURA - 90), (LARGURA - 100, ALTURA - 90), 1)

    def _desenhar_titulo(self, tempo_atual):
        """Desenha o título com animações."""
        # Efeito de pulso
        pulso = math.sin(tempo_atual / 400) * 3
        escala = 1 + math.sin(tempo_atual / 600) * 0.015

        # Sombra do título
        desenhar_texto(self.tela, "SELECIONE SUA CLASSE", int(42 * escala),
                      (20, 20, 30), LARGURA // 2 + 3, 70 + pulso + 3)

        # Título principal
        desenhar_texto(self.tela, "SELECIONE SUA CLASSE", int(42 * escala),
                      BRANCO, LARGURA // 2, 70 + pulso)

        # Subtítulo do time com brilho
        brilho = int(180 + math.sin(tempo_atual / 300) * 75)
        cor_subtitulo = tuple(min(255, int(c * brilho / 180)) for c in self.cor_time)
        desenhar_texto(self.tela, self.titulo_time, 22, cor_subtitulo, LARGURA // 2, 115)

    def _desenhar_card(self, card, numero, tempo_atual):
        """Desenha um card de classe."""
        dados = card["dados"]
        rect = card["rect"]
        is_hover = self.hover_classe == card["id"]

        # Cores
        cor_principal = dados["cor"]
        cor_escura = dados["cor_escura"]

        # Animação de hover - card sobe levemente
        offset_y = 0
        if is_hover:
            offset_y = -8

        # Rect ajustado
        rect_desenho = pygame.Rect(rect.x, rect.y + offset_y, rect.width, rect.height)

        # Efeito glow no hover
        if is_hover:
            for i in range(4):
                glow_rect = rect_desenho.inflate(i * 6, i * 6)
                surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                alpha = 40 - i * 10
                pygame.draw.rect(surf, (*cor_principal, alpha),
                               (0, 0, glow_rect.width, glow_rect.height), 0, 15)
                self.tela.blit(surf, glow_rect)

        # Sombra do card
        sombra_offset = 8 if is_hover else 5
        pygame.draw.rect(self.tela, (10, 10, 15),
                        (rect_desenho.x + sombra_offset, rect_desenho.y + sombra_offset,
                         rect_desenho.width, rect_desenho.height), 0, 12)

        # Fundo do card com gradiente simulado
        pygame.draw.rect(self.tela, (25, 25, 35), rect_desenho, 0, 12)

        # Borda interna mais clara
        pygame.draw.rect(self.tela, (35, 35, 50),
                        (rect_desenho.x + 2, rect_desenho.y + 2,
                         rect_desenho.width - 4, rect_desenho.height - 4), 0, 11)

        # Fundo principal do card
        pygame.draw.rect(self.tela, (28, 28, 40),
                        (rect_desenho.x + 4, rect_desenho.y + 4,
                         rect_desenho.width - 8, rect_desenho.height - 8), 0, 10)

        # Borda externa
        borda_cor = cor_principal if is_hover else cor_escura
        borda_largura = 3 if is_hover else 2
        pygame.draw.rect(self.tela, borda_cor, rect_desenho, borda_largura, 12)

        # Número da classe com destaque
        num_y = rect_desenho.top + 18
        if is_hover:
            pygame.draw.circle(self.tela, (*cor_principal, 100), (rect_desenho.centerx, num_y), 14)
        desenhar_texto(self.tela, f"[{numero}]", 16, (180, 180, 180) if not is_hover else BRANCO,
                      rect_desenho.centerx, num_y)

        # Preview do visual (quadrado colorido) - MANTIDO ORIGINAL
        preview_size = 55
        preview_x = rect_desenho.centerx - preview_size // 2
        preview_y = rect_desenho.top + 45

        # Sombra do preview
        pygame.draw.rect(self.tela, (15, 15, 20),
                        (preview_x + 4, preview_y + 4, preview_size, preview_size), 0, 6)
        # Quadrado principal
        pygame.draw.rect(self.tela, cor_escura,
                        (preview_x, preview_y, preview_size, preview_size), 0, 6)
        pygame.draw.rect(self.tela, cor_principal,
                        (preview_x + 3, preview_y + 3, preview_size - 6, preview_size - 6), 0, 5)
        # Brilho
        pygame.draw.rect(self.tela, tuple(min(255, c + 50) for c in cor_principal),
                        (preview_x + 6, preview_y + 6, 10, 10), 0, 3)

        # Desenhar elementos visuais específicos de cada classe
        centro_preview_x = preview_x + preview_size // 2
        centro_preview_y = preview_y + preview_size // 2

        # Mago - Chapéu
        if dados.get("tem_chapeu_mago", False):
            self._desenhar_chapeu_mago(centro_preview_x, preview_y - 5)

        # Ghost - Rosto assustador
        if card["id"] == "ghost":
            self._desenhar_rosto_ghost(preview_x, preview_y, preview_size)

        # Granada - Cinto com granadas
        if card["id"] == "granada":
            self._desenhar_cinto_granadas(preview_x, preview_y, preview_size)

        # Metralhadora - NVG e visual tático
        if card["id"] == "metralhadora":
            self._desenhar_visual_metralhadora(preview_x, preview_y, preview_size)

        # Explosive - Efeito de chamas
        if card["id"] == "explosive":
            self._desenhar_chamas_explosive(preview_x, preview_y, preview_size)

        # Separador
        sep_y = preview_y + preview_size + 15
        pygame.draw.line(self.tela, (50, 50, 60),
                        (rect_desenho.x + 20, sep_y), (rect_desenho.right - 20, sep_y), 1)

        # Nome da classe
        nome_y = sep_y + 18
        desenhar_texto(self.tela, dados["nome"], 22, cor_principal if is_hover else tuple(min(255, c + 30) for c in cor_escura),
                      rect_desenho.centerx, nome_y)

        # Descrição
        desc_y = nome_y + 28
        desenhar_texto(self.tela, dados["descricao"], 13, (200, 200, 200),
                      rect_desenho.centerx, desc_y)

        # Habilidade
        hab_y = desc_y + 22
        desenhar_texto(self.tela, dados["descricao2"], 11, (130, 200, 130),
                      rect_desenho.centerx, hab_y)

        # Vidas com ícones
        vidas = dados["vidas"]
        vidas_y = rect_desenho.bottom - 30
        cor_vidas = (100, 255, 100) if vidas > 5 else ((255, 200, 100) if vidas >= 4 else (255, 100, 100))

        # Desenhar corações/vidas
        total_width = vidas * 12
        start_x = rect_desenho.centerx - total_width // 2
        for i in range(vidas):
            x = start_x + i * 12 + 6
            # Mini quadrado representando vida
            pygame.draw.rect(self.tela, cor_vidas, (x - 4, vidas_y - 4, 8, 8), 0, 2)

    def _desenhar_particulas(self):
        """Desenha as partículas."""
        for p in self.particulas:
            alpha = int((p['vida'] / 40) * 255)
            surf = pygame.Surface((int(p['tamanho'] * 2), int(p['tamanho'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['cor'], alpha),
                             (int(p['tamanho']), int(p['tamanho'])), int(p['tamanho']))
            self.tela.blit(surf, (int(p['x'] - p['tamanho']), int(p['y'] - p['tamanho'])))

    def _desenhar_instrucoes(self, tempo_atual):
        """Desenha as instruções na parte inferior."""
        # Animação sutil
        alpha = int(150 + math.sin(tempo_atual / 800) * 30)
        cor_inst = (alpha, alpha, alpha)

        desenhar_texto(self.tela, "Clique em uma classe ou pressione 1-4", 16, cor_inst,
                      LARGURA // 2, ALTURA - 55)
        desenhar_texto(self.tela, "ESC para voltar", 14, (100, 100, 100),
                      LARGURA // 2, ALTURA - 30)

    def _desenhar_chapeu_mago(self, x, y):
        """Desenha um chapéu de mago."""
        # Triângulo do chapéu (maior)
        pontos = [(x, y - 28), (x - 18, y + 8), (x + 18, y + 8)]
        pygame.draw.polygon(self.tela, (100, 50, 150), pontos)  # Roxo escuro
        pygame.draw.polygon(self.tela, (150, 100, 200), pontos, 2)  # Borda
        # Aba do chapéu (maior)
        pygame.draw.ellipse(self.tela, (100, 50, 150), (x - 22, y + 4, 44, 12))
        pygame.draw.ellipse(self.tela, (150, 100, 200), (x - 22, y + 4, 44, 12), 2)
        # Estrela (maior)
        pygame.draw.circle(self.tela, (255, 255, 100), (x, y - 10), 5)

    def _desenhar_rosto_ghost(self, x, y, tamanho):
        """Desenha o rosto assustador do ghost no preview."""
        # Aura fantasmagórica
        for i in range(2):
            pygame.draw.rect(self.tela, (180, 180, 220),
                           (x - i - 1, y - i - 1, tamanho + i * 2 + 2, tamanho + i * 2 + 2), 1, 5)

        # Olhos vermelhos
        olho_esq_x = x + tamanho // 3
        olho_dir_x = x + 2 * tamanho // 3
        olho_y = y + tamanho // 3

        # Brilho dos olhos
        pygame.draw.circle(self.tela, (255, 150, 150), (olho_esq_x, olho_y), 6)
        pygame.draw.circle(self.tela, (255, 150, 150), (olho_dir_x, olho_y), 6)

        # Olhos internos (vermelho)
        pygame.draw.circle(self.tela, (255, 30, 30), (olho_esq_x, olho_y), 4)
        pygame.draw.circle(self.tela, (255, 30, 30), (olho_dir_x, olho_y), 4)

        # Pupilas
        pygame.draw.circle(self.tela, (0, 0, 0), (olho_esq_x, olho_y), 2)
        pygame.draw.circle(self.tela, (0, 0, 0), (olho_dir_x, olho_y), 2)

        # Boca assustadora
        boca_x = x + tamanho // 2
        boca_y = y + 2 * tamanho // 3
        pygame.draw.ellipse(self.tela, (30, 0, 0), (boca_x - 8, boca_y, 16, 10))

        # Dentes
        for i in range(4):
            dente_x = boca_x - 6 + i * 4
            pygame.draw.rect(self.tela, (255, 255, 200), (dente_x, boca_y + 1, 2, 4))

    def _desenhar_cinto_granadas(self, x, y, tamanho):
        """Desenha o cinto com granadas no preview."""
        # Cinto dourado
        cinto_y = y + int(tamanho * 0.65)
        pygame.draw.line(self.tela, (200, 150, 50),
                       (x + 5, cinto_y), (x + tamanho - 5, cinto_y), 3)

        # 3 granadas no cinto
        espacamento = tamanho // 4
        for i in range(3):
            granada_x = x + espacamento * (i + 1)
            granada_y = cinto_y + 8

            # Corpo da granada
            pygame.draw.circle(self.tela, (60, 120, 60), (granada_x, granada_y), 5)
            pygame.draw.circle(self.tela, (40, 80, 40), (granada_x, granada_y), 5, 1)

            # Detalhe
            pygame.draw.line(self.tela, (40, 80, 40),
                           (granada_x - 3, granada_y), (granada_x + 3, granada_y), 1)

            # Bocal
            pygame.draw.rect(self.tela, (150, 150, 150),
                           (granada_x - 2, granada_y - 7, 4, 4))

            # Pino
            pygame.draw.circle(self.tela, (220, 220, 100), (granada_x + 4, granada_y - 6), 2, 1)

    def _desenhar_visual_metralhadora(self, x, y, tamanho):
        """Desenha o visual tático do metralhadora no preview."""
        centro_x = x + tamanho // 2

        # Padrão de camuflagem
        random.seed(42)
        for _ in range(6):
            mancha_x = x + random.randint(5, tamanho - 5)
            mancha_y = y + random.randint(5, tamanho - 5)
            cor_mancha = random.choice([(70, 80, 55), (50, 60, 40)])
            pygame.draw.circle(self.tela, cor_mancha, (mancha_x, mancha_y), 4)

        # Colete tático
        pygame.draw.rect(self.tela, (30, 35, 25),
                       (x + 5, y + 8, tamanho - 10, tamanho - 12), 2, 3)

        # Faixas MOLLE
        for i in range(3):
            faixa_y = y + 15 + i * 10
            pygame.draw.line(self.tela, (100, 100, 110),
                           (x + 8, faixa_y), (x + tamanho - 8, faixa_y), 1)

        # NVG (óculos de visão noturna)
        nvg_y = y - 3
        nvg_esq_x = centro_x - 8
        nvg_dir_x = centro_x + 8

        # Suporte
        pygame.draw.line(self.tela, (100, 100, 110),
                       (centro_x - 12, nvg_y), (centro_x + 12, nvg_y), 2)

        # Lentes NVG
        pygame.draw.circle(self.tela, (20, 20, 40), (nvg_esq_x, nvg_y + 4), 5)
        pygame.draw.circle(self.tela, (0, 255, 100), (nvg_esq_x, nvg_y + 4), 3)
        pygame.draw.circle(self.tela, (20, 20, 40), (nvg_dir_x, nvg_y + 4), 5)
        pygame.draw.circle(self.tela, (0, 255, 100), (nvg_dir_x, nvg_y + 4), 3)

    def _desenhar_chamas_explosive(self, x, y, tamanho):
        """Desenha o efeito de chamas ao redor do explosive no preview."""
        random.seed(42)  # Seed fixa para não piscar

        # Partículas de fogo ao redor do quadrado
        for i in range(8):
            # Variação no tamanho e posição
            offset_x = random.uniform(-tamanho / 3, tamanho / 3)
            offset_y = random.uniform(-tamanho / 3, tamanho / 3)

            # Cores variando de laranja a amarelo
            cor_r = min(255, 255 + random.randint(-40, 0))
            cor_g = min(255, 140 + random.randint(-40, 60))
            cor_b = 0  # Sem componente azul para manter o visual de fogo

            tamanho_particula = random.randint(3, 6)

            # Desenhar partícula de fogo
            particula_x = int(x - offset_x + random.uniform(0, tamanho))
            particula_y = int(y - offset_y + random.uniform(0, tamanho))
            pygame.draw.circle(self.tela, (cor_r, cor_g, cor_b),
                             (particula_x, particula_y), tamanho_particula)


def obter_dados_classe(classe_id, time='Q'):
    """
    Retorna os dados de uma classe pelo ID.

    Args:
        classe_id: ID da classe
        time: 'T' ou 'Q'

    Returns:
        dict: Dados da classe ou None se não existir
    """
    if time == 'T':
        return CLASSES_TIME_T.get(classe_id, None)
    else:
        return CLASSES_TIME_Q.get(classe_id, None)
