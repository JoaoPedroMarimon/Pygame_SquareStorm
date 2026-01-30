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
        "vidas": 5,
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
        "descricao2": "Comeca com metralhadora",
        "cor": (107, 142, 35),  # Verde-oliva
        "cor_escura": (70, 95, 20),
        "vidas": 5,
        "velocidade_base": 1.0,  # Um pouco mais lento
        "arma_inicial": "metralhadora",
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
        "habilidade_cooldown": 8000,  # 8 segundos
        "tiros_explosao": 12,
    },
    "normal": {
        "nome": "Normal",
        "descricao": "Equilibrado",
        "descricao2": "ESPACO: Dash rapido",
        "cor": (100, 150, 255),  # Azul (Time Q padrão)
        "cor_escura": (60, 100, 180),
        "vidas": 5,
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

    def _calcular_posicoes_cards(self):
        """Calcula as posições dos cards de classe na tela."""
        self.cards = []
        card_largura = 150
        card_altura = 200
        espacamento = 30
        total_largura = len(self.ordem_classes) * card_largura + (len(self.ordem_classes) - 1) * espacamento
        inicio_x = (LARGURA - total_largura) // 2
        y = ALTURA // 2 - card_altura // 2

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
            # Processar eventos
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return None

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return None
                    # Atalhos numéricos
                    if evento.key == pygame.K_1:
                        return self.ordem_classes[0]
                    if evento.key == pygame.K_2:
                        return self.ordem_classes[1]
                    if evento.key == pygame.K_3:
                        return self.ordem_classes[2]
                    if evento.key == pygame.K_4:
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
                                return card["id"]

            # Desenhar
            self._desenhar()
            present_frame()
            self.relogio.tick(60)

        return None

    def _desenhar(self):
        """Desenha a tela de seleção de classes."""
        # Fundo gradiente
        for y in range(ALTURA):
            cor = (
                int(20 + y * 0.02),
                int(20 + y * 0.01),
                int(40 + y * 0.03)
            )
            pygame.draw.line(self.tela, cor, (0, y), (LARGURA, y))

        # Título
        desenhar_texto(self.tela, "SELECIONE SUA CLASSE", 36, (255, 255, 255), LARGURA // 2, 80)
        desenhar_texto(self.tela, self.titulo_time, 20, self.cor_time, LARGURA // 2, 120)

        # Desenhar cards
        for i, card in enumerate(self.cards):
            self._desenhar_card(card, i + 1)

        # Instruções
        desenhar_texto(self.tela, "Clique em uma classe ou pressione 1-4", 16, (150, 150, 150), LARGURA // 2, ALTURA - 60)
        desenhar_texto(self.tela, "ESC para voltar", 14, (100, 100, 100), LARGURA // 2, ALTURA - 35)

    def _desenhar_card(self, card, numero):
        """Desenha um card de classe."""
        dados = card["dados"]
        rect = card["rect"]
        is_hover = self.hover_classe == card["id"]

        # Cores
        cor_principal = dados["cor"]
        cor_escura = dados["cor_escura"]

        # Efeito hover
        if is_hover:
            rect_desenho = rect.inflate(10, 10)
            borda_cor = (255, 255, 255)
            borda_largura = 3
        else:
            rect_desenho = rect
            borda_cor = cor_escura
            borda_largura = 2

        # Fundo do card
        pygame.draw.rect(self.tela, (30, 30, 40), rect_desenho, 0, 10)
        pygame.draw.rect(self.tela, borda_cor, rect_desenho, borda_largura, 10)

        # Número da classe
        desenhar_texto(self.tela, f"[{numero}]", 14, (150, 150, 150),
                      rect_desenho.centerx, rect_desenho.top + 15)

        # Preview do visual (quadrado colorido)
        preview_size = 50
        preview_x = rect_desenho.centerx - preview_size // 2
        preview_y = rect_desenho.top + 35

        # Sombra
        pygame.draw.rect(self.tela, (20, 20, 20),
                        (preview_x + 3, preview_y + 3, preview_size, preview_size), 0, 5)
        # Quadrado principal
        pygame.draw.rect(self.tela, cor_escura,
                        (preview_x, preview_y, preview_size, preview_size), 0, 5)
        pygame.draw.rect(self.tela, cor_principal,
                        (preview_x + 2, preview_y + 2, preview_size - 4, preview_size - 4), 0, 4)
        # Brilho
        pygame.draw.rect(self.tela, tuple(min(255, c + 50) for c in cor_principal),
                        (preview_x + 4, preview_y + 4, 8, 8), 0, 2)

        # Desenhar chapéu de mago se for a classe mago
        if dados.get("tem_chapeu_mago", False):
            self._desenhar_chapeu_mago(preview_x + preview_size // 2, preview_y - 5)

        # Nome da classe
        desenhar_texto(self.tela, dados["nome"], 20, cor_principal,
                      rect_desenho.centerx, preview_y + preview_size + 20)

        # Descrição
        desenhar_texto(self.tela, dados["descricao"], 12, (200, 200, 200),
                      rect_desenho.centerx, preview_y + preview_size + 45)

        # Habilidade
        desenhar_texto(self.tela, dados["descricao2"], 10, (150, 200, 150),
                      rect_desenho.centerx, preview_y + preview_size + 65)

        # Vidas
        vidas = dados["vidas"]
        vidas_texto = f"Vidas: {vidas}"
        cor_vidas = (100, 255, 100) if vidas > 3 else ((255, 200, 100) if vidas == 3 else (255, 100, 100))
        desenhar_texto(self.tela, vidas_texto, 12, cor_vidas,
                      rect_desenho.centerx, rect_desenho.bottom - 25)

    def _desenhar_chapeu_mago(self, x, y):
        """Desenha um chapéu de mago em miniatura."""
        # Triângulo do chapéu
        pontos = [(x, y - 15), (x - 12, y + 5), (x + 12, y + 5)]
        pygame.draw.polygon(self.tela, (100, 50, 150), pontos)  # Roxo escuro
        pygame.draw.polygon(self.tela, (150, 100, 200), pontos, 2)  # Borda
        # Aba do chapéu
        pygame.draw.ellipse(self.tela, (100, 50, 150), (x - 15, y + 2, 30, 8))
        # Estrela
        pygame.draw.circle(self.tela, (255, 255, 100), (x, y - 5), 3)


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
