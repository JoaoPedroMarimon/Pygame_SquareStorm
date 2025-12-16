#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo completo do sistema de inventário do jogo com sistema de abas.
Interface visual moderna e rica em efeitos visuais.
"""

import pygame
import json
import os
import random
import math
from src.config import *
from src.utils.visual import criar_estrelas, desenhar_estrelas, desenhar_texto, criar_botao
from src.utils.display_manager import present_frame,convert_mouse_position

class InventarioManager:
    """Gerencia o inventário e a seleção de armas/itens do jogador."""
    
    def __init__(self):
        self.arma_selecionada = "nenhuma"
        self.item_selecionado = "nenhum"
        self.arquivo_inventario = "data/inventario.json"
        self.carregar_inventario()
    
    def carregar_inventario(self):
        """Carrega a configuração do inventário do arquivo."""
        try:
            if os.path.exists(self.arquivo_inventario):
                with open(self.arquivo_inventario, "r") as f:
                    data = json.load(f)
                    self.arma_selecionada = data.get("arma_selecionada", "nenhuma")
                    self.item_selecionado = data.get("item_selecionado", "nenhum")
            else:
                self.salvar_inventario()
        except Exception as e:
            print(f"Erro ao carregar inventário: {e}")
            self.arma_selecionada = "nenhuma"
            self.item_selecionado = "nenhum"
    
    def salvar_inventario(self):
        """Salva a configuração atual do inventário."""
        try:
            os.makedirs("data", exist_ok=True)
            data = {
                "arma_selecionada": self.arma_selecionada,
                "item_selecionado": self.item_selecionado
            }
            with open(self.arquivo_inventario, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar inventário: {e}")
    
    def selecionar_arma(self, arma):
        """Seleciona uma arma para usar na partida."""
        self.arma_selecionada = arma
        self.salvar_inventario()
    
    def selecionar_item(self, item):
        """Seleciona um item para usar na partida."""
        self.item_selecionado = item
        self.salvar_inventario()
    
    def obter_arma_selecionada(self):
        """Retorna a arma atualmente selecionada."""
        return self.arma_selecionada
    
    def obter_item_selecionado(self):
        """Retorna o item atualmente selecionado."""
        return self.item_selecionado
    
    def obter_armas_disponiveis(self):
        """Retorna dicionário com as armas disponíveis no inventário."""
        armas_info = {
            "espingarda": {
                "nome": "Shotgun",
                "quantidade": 0,
                "cor": (255, 150, 150),
                "descricao": "Multiple shot devastating damage",
                "tipo": "arma",
                "categoria": "arma",
                "key": "espingarda",
                "raridade": "Common",
                "dano": "★★★★☆",
                "alcance": "★★☆☆☆"
            },
            "metralhadora": {
                "nome": "Machine Gun",
                "quantidade": 0,
                "cor": (255, 180, 70),
                "descricao": "Extreme rate of fire",
                "tipo": "arma",
                "categoria": "arma",
                "key": "metralhadora",
                "raridade": "Rare",
                "dano": "★★★☆☆",
                "alcance": "★★★☆☆"
            },
            "sabre_luz": {
                "nome": "Lightsaber",
                "quantidade": 0,
                "cor": (150, 150, 255),
                "descricao": "Elegant weapon for a more civilized age",
                "tipo": "arma",
                "categoria": "arma",
                "key": "sabre_luz",
                "raridade": "Legendary",
                "dano": "★★★★★",
                "alcance": "★★★★☆"
            },
            "desert_eagle": {
                "nome": "Desert Eagle",
                "quantidade": 0,
                "cor": (200, 180, 100),
                "descricao": "Powerful hand cannon with high damage",
                "tipo": "arma",
                "categoria": "arma",
                "key": "desert_eagle",
                "raridade": "Rare",
                "dano": "★★★★☆",
                "alcance": "★★★★★"
            }
        }
        
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    for arma_key in armas_info:
                        armas_info[arma_key]["quantidade"] = upgrades.get(arma_key, 0)
        except Exception as e:
            print(f"Erro ao carregar upgrades para inventário: {e}")
        
        return armas_info
    
    def obter_itens_disponiveis(self):
        """Retorna dicionário com os itens disponíveis no inventário."""
        itens_info = {
            "granada": {
                "nome": "Grenade",
                "quantidade": 0,
                "cor": (150, 220, 150),
                "descricao": "Explosive area damage!",
                "tipo": "item",
                "categoria": "item",
                "tecla": "Q",
                "key": "granada",
                "raridade": "Uncommon",
                "efeito": "Area Damage",
                "duracao": "Instant"
            },
            "ampulheta": {
                "nome": "Hourglass of Balance",
                "quantidade": 0,
                "cor": (150, 150, 255),
                "descricao": "Slows down time for precision!",
                "tipo": "item",
                "categoria": "item",
                "tecla": "Q",
                "key": "ampulheta",
                "raridade": "Legendary",
                "efeito": "Time Slow",
                "duracao": "5 seconds"
            },
            "faca": {
                "nome": "Killer Doll",
                "quantidade": 0,
                "cor": (220, 150, 150),
                "descricao": "Summon a little friend to help you",
                "tipo": "item",
                "categoria": "item",
                "tecla": "Q",
                "key": "faca",
                "raridade": "Epic",
                "efeito": "Summon Ally",
                "duracao": "15 seconds"
            },
            "dimensional_hop": {
                "nome": "Dimensional Hop",
                "quantidade": 0,
                "cor": (200, 150, 255),
                "descricao": "Teleport instantly to cursor position",
                "tipo": "item",
                "categoria": "item",
                "tecla": "Q",
                "key": "dimensional_hop",
                "raridade": "Legendary",
                "efeito": "Teleportation",
                "duracao": "Instant"
            }
        }
        
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    for item_key in itens_info:
                        itens_info[item_key]["quantidade"] = upgrades.get(item_key, 0)
        except Exception as e:
            print(f"Erro ao carregar upgrades para inventário: {e}")
        
        return itens_info

def desenhar_fundo_futurista(tela, tempo_atual):
    """Desenha um fundo futurista com efeitos de particulas."""
    # Particulas de energia flutuantes
    for i in range(20):
        x = (tempo_atual / 10 + i * 73) % LARGURA
        y = 100 + 400 * math.sin((tempo_atual / 2000 + i) * 0.5)
        size = 2 + int(math.sin(tempo_atual / 300 + i) * 2)
        alpha = int(100 + 100 * math.sin(tempo_atual / 500 + i))
        cor = (0, 150, 255, alpha)
        pygame.draw.circle(tela, (0, 150, 255), (int(x), int(y)), size)

def desenhar_icone_ampulheta_moderno(tela, x, y, tempo_atual, tamanho=30):
    """Desenha ícone moderno da ampulheta com efeitos visuais avançados."""
    # Estrutura principal com gradiente
    cor_estrutura = (150, 120, 80)
    cor_brilho = (255, 215, 120)
    
    largura = tamanho
    altura = int(tamanho * 1.2)
    
    # Criar superfície com transparência para efeitos
    ampulheta_surf = pygame.Surface((largura + 20, altura + 20), pygame.SRCALPHA)
    
    # Corpo da ampulheta com gradiente simulado
    pontos_superior = [
        (10, 10),
        (largura + 10, 10),
        (largura//2 + 10, altura//2 + 10)
    ]
    pontos_inferior = [
        (largura//2 + 10, altura//2 + 10),
        (10, altura + 10),
        (largura + 10, altura + 10)
    ]
    
    pygame.draw.polygon(ampulheta_surf, cor_estrutura, pontos_superior)
    pygame.draw.polygon(ampulheta_surf, cor_estrutura, pontos_inferior)
    
    # Bordas brilhantes
    pygame.draw.polygon(ampulheta_surf, cor_brilho, pontos_superior, 3)
    pygame.draw.polygon(ampulheta_surf, cor_brilho, pontos_inferior, 3)
    
    # Animação da areia
    tempo_ciclo = (tempo_atual % 4000) / 4000.0
    
    # Areia superior
    if tempo_ciclo < 0.8:
        areia_altura = int((altura//2 - 8) * (1 - tempo_ciclo))
        if areia_altura > 0:
            for i in range(areia_altura):
                largura_linha = int((largura - 12) * (1 - i / areia_altura))
                y_areia = 15 + i
                x_centro = largura//2 + 10
                cor_areia = (255, 215 - i * 2, 50)
                pygame.draw.line(ampulheta_surf, cor_areia, 
                               (x_centro - largura_linha//2, y_areia), 
                               (x_centro + largura_linha//2, y_areia), 2)
    
    # Areia inferior
    areia_altura_inf = int((altura//2 - 8) * tempo_ciclo)
    if areia_altura_inf > 0:
        for i in range(areia_altura_inf):
            largura_linha = int((largura - 12) * (i / areia_altura_inf))
            y_areia = altura + 5 - i
            x_centro = largura//2 + 10
            cor_areia = (200, 165, 30)
            pygame.draw.line(ampulheta_surf, cor_areia, 
                           (x_centro - largura_linha//2, y_areia), 
                           (x_centro + largura_linha//2, y_areia), 2)
    
    # Partículas caindo
    if 0.1 < tempo_ciclo < 0.9:
        for i in range(3):
            part_y = altura//2 + 10 + (i - 1) * 4
            pygame.draw.circle(ampulheta_surf, (255, 215, 0), 
                             (largura//2 + 10, part_y), 2)
    
    # Efeito de brilho temporal
    pulso = (math.sin(tempo_atual / 300) + 1) / 2
    if pulso > 0.7:
        brilho_surf = pygame.Surface((largura + 40, altura + 40), pygame.SRCALPHA)
        alpha = int(150 * (pulso - 0.7) / 0.3)
        pygame.draw.polygon(brilho_surf, (100, 150, 255, alpha), 
                          [(p[0] + 10, p[1] + 10) for p in pontos_superior], 5)
        pygame.draw.polygon(brilho_surf, (100, 150, 255, alpha), 
                          [(p[0] + 10, p[1] + 10) for p in pontos_inferior], 5)
        tela.blit(brilho_surf, (x - largura//2 - 20, y - altura//2 - 20))
    
    tela.blit(ampulheta_surf, (x - largura//2 - 10, y - altura//2 - 10))


def desenhar_icone_sabre_moderno(tela, x, y, tempo_atual, tamanho=30):
    """Desenha ícone moderno do sabre de luz para o inventário."""
    cor_cabo = (120, 120, 130)
    cor_cabo_detalhes = (80, 80, 150)
    cor_lamina = (150, 150, 255)
    cor_brilho = (255, 255, 255)
    
    # Cabo principal (vertical)
    cabo_height = tamanho // 2
    cabo_width = 8
    cabo_rect = pygame.Rect(x - cabo_width//2, y, cabo_width, cabo_height)
    pygame.draw.rect(tela, cor_cabo, cabo_rect, 0, 3)
    pygame.draw.rect(tela, cor_cabo_detalhes, cabo_rect, 2, 3)
    
    # Detalhes do cabo
    for i in range(3):
        det_y = y + (i + 1) * (cabo_height // 4)
        pygame.draw.line(tela, cor_cabo_detalhes, 
                        (x - cabo_width//2 + 1, det_y), 
                        (x + cabo_width//2 - 1, det_y), 1)
    
    # Lâmina com efeito pulsante
    pulso = (math.sin(tempo_atual / 200) + 1) / 2
    lamina_length = int((tamanho * 1.2) + pulso * 5)
    
    # Brilho da lâmina (múltiplas linhas para efeito glow)
    for i in range(5, 0, -1):
        alpha = int(100 + (6-i) * 30)
        cor_atual = cor_lamina if i <= 2 else cor_brilho
        
        # Criar superfície temporária para alpha
        temp_surf = pygame.Surface((cabo_width + 6, lamina_length + 10), pygame.SRCALPHA)
        pygame.draw.line(temp_surf, (*cor_atual, alpha),
                        (3 + cabo_width//2, lamina_length + 5),
                        (3 + cabo_width//2, 5), i)
        
        tela.blit(temp_surf, (x - cabo_width//2 - 3, y - lamina_length - 5))
    
    # Núcleo brilhante
    pygame.draw.line(tela, cor_brilho, (x, y), (x, y - lamina_length), 1)
    
    # Emitter na base da lâmina
    pygame.draw.circle(tela, cor_brilho, (x, y), 3)
    pygame.draw.circle(tela, cor_lamina, (x, y), 2)


def desenhar_icone_granada_moderno(tela, x, y, tempo_atual, tamanho=25):
    """Desenha ícone moderno da granada com efeitos explosivos."""
    cor_granada = (60, 120, 60)
    cor_metal = (150, 150, 150)
    
    # Corpo principal com efeito metálico
    pygame.draw.circle(tela, cor_granada, (x, y), tamanho)
    pygame.draw.circle(tela, (80, 150, 80), (x, y), tamanho, 3)
    
    # Segmentos da granada
    for i in range(4):
        angulo = i * 90
        end_x = x + int((tamanho - 5) * math.cos(math.radians(angulo)))
        end_y = y + int((tamanho - 5) * math.sin(math.radians(angulo)))
        pygame.draw.line(tela, (40, 80, 40), (x, y), (end_x, end_y), 2)
    
    # Parte superior com detalhes
    top_rect = pygame.Rect(x - 8, y - tamanho - 12, 16, 12)
    pygame.draw.rect(tela, cor_metal, top_rect, 0, 3)
    pygame.draw.rect(tela, (200, 200, 200), top_rect, 2, 3)
    
    # Pino animado
    pin_x = x + 12
    pin_y = y - tamanho - 6
    pin_pulso = (math.sin(tempo_atual / 200) + 1) / 2
    pin_size = 7 + int(pin_pulso * 3)
    pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), pin_size, 3)
    
    # Efeito de energia explosiva
    if pin_pulso > 0.8:
        explosion_radius = int((pin_pulso - 0.8) * 50)
        explosion_alpha = int(100 * (1 - (pin_pulso - 0.8) * 5))
        explosion_surf = pygame.Surface((explosion_radius * 2, explosion_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(explosion_surf, (255, 100, 0, explosion_alpha), 
                         (explosion_radius, explosion_radius), explosion_radius)
        tela.blit(explosion_surf, (x - explosion_radius, y - explosion_radius))

def desenhar_icone_dimensional_hop_moderno(tela, x, y, tempo_atual, tamanho=25):
    """Desenha ícone moderno do Dimensional Hop com efeitos retrofuturísticos."""
    # Cores retrofuturísticas
    cor_portal_externo = (200, 50, 255)  # Magenta
    cor_portal_interno = (100, 200, 255)  # Ciano
    cor_particulas = (255, 150, 255)  # Rosa neon

    # Animação de pulsação
    pulso = (math.sin(tempo_atual / 150) + 1) / 2

    # Portal principal com anéis concêntricos
    raio_portal = tamanho
    for i in range(3):
        raio_anel = raio_portal - i * (tamanho // 4)
        cor_anel = (
            int(cor_portal_externo[0] * (1 - i/3) + cor_portal_interno[0] * (i/3)),
            int(cor_portal_externo[1] * (1 - i/3) + cor_portal_interno[1] * (i/3)),
            int(cor_portal_externo[2] * (1 - i/3) + cor_portal_interno[2] * (i/3))
        )
        pygame.draw.circle(tela, cor_anel, (int(x), int(y)), int(raio_anel + pulso * 3), 2)

    # Núcleo central brilhante
    raio_nucleo = int((tamanho // 3) + pulso * 3)
    pygame.draw.circle(tela, (255, 255, 255), (int(x), int(y)), raio_nucleo)
    pygame.draw.circle(tela, cor_portal_interno, (int(x), int(y)), raio_nucleo - 2)

    # Partículas orbitando
    num_particulas = 6
    for i in range(num_particulas):
        angulo = (2 * math.pi * i / num_particulas) + (tempo_atual / 200)
        raio_orbita = raio_portal + 5

        part_x = x + math.cos(angulo) * raio_orbita
        part_y = y + math.sin(angulo) * raio_orbita

        tamanho_part = 3 + int(pulso * 2)
        pygame.draw.rect(tela, cor_particulas,
                       (int(part_x - tamanho_part/2), int(part_y - tamanho_part/2),
                        tamanho_part, tamanho_part))

    # Raios de energia
    num_raios = 4
    for i in range(num_raios):
        angulo = (2 * math.pi * i / num_raios) + (tempo_atual / 300)
        comprimento_raio = 8 + pulso * 4

        raio_start_x = x + math.cos(angulo) * raio_portal
        raio_start_y = y + math.sin(angulo) * raio_portal
        raio_end_x = x + math.cos(angulo) * (raio_portal + comprimento_raio)
        raio_end_y = y + math.sin(angulo) * (raio_portal + comprimento_raio)

        pygame.draw.line(tela, cor_portal_externo,
                        (int(raio_start_x), int(raio_start_y)),
                        (int(raio_end_x), int(raio_end_y)), 2)

def desenhar_icone_faca_moderno(tela, x, y, tempo_atual, tamanho=25):
    """Desenha ícone moderno da faca com efeitos de brilho."""
    # Rotação sutil
    angulo = math.sin(tempo_atual / 1000) * 10
    
    # Cores melhoradas
    cor_lamina = (220, 220, 240)
    cor_cabo = (139, 69, 19)
    cor_brilho = (255, 255, 255)
    
    # Calcular pontos rotacionados
    def rotacionar(px, py, angulo_rot):
        rad = math.radians(angulo_rot)
        novo_x = px * math.cos(rad) - py * math.sin(rad)
        novo_y = px * math.sin(rad) + py * math.cos(rad)
        return x + novo_x, y + novo_y
    
    # Lâmina
    pontos_lamina = [
        rotacionar(-tamanho//2, -4, angulo),
        rotacionar(-tamanho//2, 4, angulo),
        rotacionar(tamanho//2, 0, angulo)
    ]
    pygame.draw.polygon(tela, cor_lamina, pontos_lamina)
    pygame.draw.polygon(tela, (180, 180, 200), pontos_lamina, 2)
    
    # Cabo
    cabo_pontos = [
        rotacionar(-tamanho//2 - 10, -3, angulo),
        rotacionar(-tamanho//2 - 10, 3, angulo),
        rotacionar(-tamanho//2, 3, angulo),
        rotacionar(-tamanho//2, -3, angulo)
    ]
    pygame.draw.polygon(tela, cor_cabo, cabo_pontos)
    pygame.draw.polygon(tela, (100, 50, 10), cabo_pontos, 1)
    
    # Brilho na lâmina
    brilho_intensidade = (math.sin(tempo_atual / 400) + 1) / 2
    if brilho_intensidade > 0.6:
        start_pos = rotacionar(-tamanho//2 + 5, 0, angulo)
        end_pos = rotacionar(tamanho//2 - 5, 0, angulo)
        pygame.draw.line(tela, cor_brilho, start_pos, end_pos, 2)

def desenhar_icone_espingarda_moderno(tela, x, y, tempo_atual, tamanho=30):
    """Desenha ícone moderno da espingarda de CANO DUPLO."""
    cor_metal = (60, 60, 70)
    cor_metal_claro = (120, 120, 130)
    cor_cano = (40, 40, 45)
    cor_madeira = (101, 67, 33)

    # Comprimento da arma
    ponta_x = x + tamanho//2

    # === CORONHA (parte traseira) ===
    coronha_x = x - tamanho//2 - 12
    pygame.draw.polygon(tela, cor_madeira, [
        (coronha_x, y - 5),
        (coronha_x, y + 5),
        (x - tamanho//2, y + 4),
        (x - tamanho//2, y - 4)
    ])
    pygame.draw.polygon(tela, (139, 90, 43), [
        (coronha_x, y - 5),
        (coronha_x, y + 5),
        (x - tamanho//2, y + 4),
        (x - tamanho//2, y - 4)
    ], 1)

    # === CORPO/MECANISMO ===
    corpo_x = x - tamanho//2 + 8
    pygame.draw.rect(tela, cor_metal, (x - tamanho//2, y - 5, 16, 10))
    pygame.draw.rect(tela, cor_metal_claro, (x - tamanho//2, y - 5, 16, 10), 1)

    # === CANO DUPLO (característica principal) ===
    separacao = 3  # Distância entre os dois canos

    # CANO SUPERIOR
    pygame.draw.line(tela, cor_cano,
                    (corpo_x, y - separacao),
                    (ponta_x, y - separacao), 5)
    pygame.draw.line(tela, cor_metal_claro,
                    (corpo_x, y - separacao - 2),
                    (ponta_x, y - separacao - 2), 1)

    # CANO INFERIOR
    pygame.draw.line(tela, cor_cano,
                    (corpo_x, y + separacao),
                    (ponta_x, y + separacao), 5)
    pygame.draw.line(tela, cor_metal_claro,
                    (corpo_x, y + separacao + 2),
                    (ponta_x, y + separacao + 2), 1)

    # === BOCAS DOS CANOS ===
    # Boca superior
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(y - separacao)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(y - separacao)), 2)

    # Boca inferior
    pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(y + separacao)), 4)
    pygame.draw.circle(tela, (20, 20, 20), (int(ponta_x), int(y + separacao)), 2)

    # === BANDA QUE UNE OS CANOS ===
    meio_x = x + tamanho * 0.15
    pygame.draw.line(tela, cor_metal_claro,
                    (meio_x, y - separacao - 2),
                    (meio_x, y + separacao + 2), 3)

    # === EFEITO DE ENERGIA LARANJA ===
    energia_pulso = (math.sin(tempo_atual / 150) + 1) / 2
    if energia_pulso > 0.5:
        cor_energia = (255, int(100 + energia_pulso * 155), 0)
        energia_width = 1 + int(energia_pulso * 2)

        # Energia no cano superior
        pygame.draw.line(tela, cor_energia,
                        (corpo_x + 3, y - separacao),
                        (ponta_x, y - separacao), energia_width)

        # Energia no cano inferior
        pygame.draw.line(tela, cor_energia,
                        (corpo_x + 3, y + separacao),
                        (ponta_x, y + separacao), energia_width)

def desenhar_icone_desert_eagle_moderno(tela, x, y, tempo_atual, tamanho=30):
    """Desenha ícone moderno da Desert Eagle para o inventário."""
    from src.weapons.desert_eagle import desenhar_icone_desert_eagle
    desenhar_icone_desert_eagle(tela, x, y, tempo_atual)

def desenhar_icone_metralhadora_moderno(tela, x, y, tempo_atual, tamanho=35):
    """
    Desenha um ícone de metralhadora com efeitos visuais.
    """
    # Cores da metralhadora
    cor_metal_escuro = (60, 60, 70)
    cor_metal_claro = (120, 120, 130)
    cor_cano_metra = (40, 40, 45)
    cor_laranja = (255, 140, 0)

    # Desenhar metralhadora
    comprimento_metra = 35
    
    # Cano principal (mais grosso, múltiplas linhas)
    for i in range(6):
        offset = (i - 2.5) * 0.6
        espessura = 3 if abs(i - 2.5) < 1 else 2
        cor_linha = cor_cano_metra if abs(i - 2.5) < 1 else cor_metal_escuro
        pygame.draw.line(tela, cor_linha,
                    (x, y + offset),
                    (x + comprimento_metra, y + offset), espessura)

    # Boca do cano com supressor
    ponta_metra_x = x + comprimento_metra
    ponta_metra_y = y
    pygame.draw.circle(tela, cor_metal_escuro, (int(ponta_metra_x), int(ponta_metra_y)), 6)
    pygame.draw.circle(tela, cor_cano_metra, (int(ponta_metra_x), int(ponta_metra_y)), 3)

    # Corpo principal
    corpo_metra_x = x + 10
    corpo_metra_y = y
    corpo_rect = pygame.Rect(corpo_metra_x - 6, corpo_metra_y - 4, 12, 8)
    pygame.draw.rect(tela, cor_metal_escuro, corpo_rect)
    pygame.draw.rect(tela, cor_metal_claro, corpo_rect, 1)

    # Carregador
    carregador_x = corpo_metra_x - 2
    carregador_y = corpo_metra_y + 6
    carregador_rect = pygame.Rect(carregador_x - 3, carregador_y, 6, 12)
    pygame.draw.rect(tela, cor_metal_escuro, carregador_rect)
    pygame.draw.rect(tela, cor_laranja, carregador_rect, 1)

    # Coronha retrátil
    punho_x = x - 6
    punho_y = y
    pygame.draw.line(tela, cor_metal_claro, (corpo_metra_x, corpo_metra_y), (punho_x, punho_y + 8), 4)
    pygame.draw.line(tela, cor_metal_claro, (punho_x, punho_y), (punho_x - 10, punho_y), 3)

    # Efeito de aquecimento/energia
    calor_intensidade = (tempo_atual % 1000) / 1000.0
    cor_calor = (255, int(100 + calor_intensidade * 155), 0)
    
    # Linhas de calor saindo do cano
    for i in range(3):
        heat_x = ponta_metra_x - (5 + i * 3) + random.uniform(-1, 1)
        heat_y = ponta_metra_y + random.uniform(-1, 1)
        pygame.draw.circle(tela, cor_calor, (int(heat_x), int(heat_y)), 1)

    # Brilho no cano
    pygame.draw.line(tela, cor_laranja, (x, y), (ponta_metra_x, ponta_metra_y), 1)


def desenhar_card_item_moderno(tela, item_data, item_key, x, y, largura, altura, selecionado, tempo_atual, hover=False):
    """Desenha um card moderno para um item do inventário."""
    # Verificar se tem estoque
    tem_estoque = item_data["quantidade"] > 0
    
    # Cores baseadas na raridade
    cores_raridade = {
        "Common": ((100, 100, 100), (150, 150, 150)),
        "Uncommon": ((50, 150, 50), (100, 200, 100)),
        "Rare": ((50, 100, 200), (100, 150, 255)),
        "Epic": ((150, 50, 200), (200, 100, 255)),
        "Legendary": ((255, 150, 0), (255, 200, 50))
    }
    
    raridade = item_data.get("raridade", "Common")
    cor_base, cor_brilho = cores_raridade.get(raridade, cores_raridade["Common"])
    
    # Converter para lista para poder modificar
    cor_base = list(cor_base)
    cor_brilho = list(cor_brilho)
    
    # Escurecer cores se não tem estoque
    if not tem_estoque:
        cor_base = [max(0, min(255, int(c // 3))) for c in cor_base]
        cor_brilho = [max(0, min(255, int(c // 2))) for c in cor_brilho]
    
    # Efeitos de hover e seleção (apenas se tem estoque)
    if tem_estoque and selecionado:
        cor_base = [max(0, min(255, int(c + 50))) for c in cor_base]
        cor_brilho = [255, 255, 255]
    elif tem_estoque and hover:
        cor_base = [max(0, min(255, int(c + 20))) for c in cor_base]
    
    # Converter de volta para tupla
    cor_base = tuple(cor_base)
    cor_brilho = tuple(cor_brilho)
    
    # Fundo do card com gradiente simulado
    card_rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, cor_base, card_rect, 0, 15)
    
    # Borda brilhante
    espessura_borda = 4 if (tem_estoque and selecionado) else 2
    pygame.draw.rect(tela, cor_brilho, card_rect, espessura_borda, 15)
    
    # Overlay para itens sem estoque
    if not tem_estoque:
        overlay_surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 120))
        tela.blit(overlay_surf, (x, y))
    
    # Efeito de brilho para itens lendários (apenas se tem estoque)
    if tem_estoque and raridade == "Legendary":
        brilho_pulso = (math.sin(tempo_atual / 300) + 1) / 2
        if brilho_pulso > 0.7:
            brilho_surf = pygame.Surface((largura + 20, altura + 20), pygame.SRCALPHA)
            alpha = max(0, min(255, int(100 * (brilho_pulso - 0.7) / 0.3)))
            brilho_color = tuple(list(cor_brilho) + [alpha])
            pygame.draw.rect(brilho_surf, brilho_color, (0, 0, largura + 20, altura + 20), 0, 20)
            tela.blit(brilho_surf, (x - 10, y - 10))
    
    # Ícone do item
    icone_x = x + 60
    icone_y = y + altura // 2
    
    if item_key == "ampulheta":
        desenhar_icone_ampulheta_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "granada":
        desenhar_icone_granada_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "faca":
        desenhar_icone_faca_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "dimensional_hop":
        desenhar_icone_dimensional_hop_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "espingarda":
        desenhar_icone_espingarda_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "metralhadora":
        desenhar_icone_metralhadora_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "sabre_luz":
        desenhar_icone_sabre_moderno(tela, icone_x, icone_y, tempo_atual)
    elif item_key == "desert_eagle":
        desenhar_icone_desert_eagle_moderno(tela, icone_x, icone_y, tempo_atual)

    # Nome do item
    cor_texto = BRANCO if tem_estoque else (100, 100, 100)
    desenhar_texto(tela, item_data["nome"], 24, cor_texto, x + 150, y + 25)
    
    # Quantidade/munição
    if item_data["tipo"] == "arma":
        if item_key == "sabre_luz":
            desenhar_texto(tela, f"Energy", 18, cor_texto, x + 150, y + 50)
        else:
            desenhar_texto(tela, f"Ammo: {item_data['quantidade']}", 18, cor_texto, x + 150, y + 50)
    else:
        desenhar_texto(tela, f"Uses: {item_data['quantidade']}", 18, cor_texto, x + 150, y + 50)
    
    # Descrição
    desenhar_texto(tela, item_data["descricao"], 14, cor_texto, x + 150, y + 75)
    
    # Estatísticas especiais
    cor_stats = (150, 150, 150) if tem_estoque else (80, 80, 80)
    if item_data["tipo"] == "arma":
        desenhar_texto(tela, f"Damage: {item_data.get('dano', 'N/A')}", 12, cor_stats, x + 150, y + 95)
        desenhar_texto(tela, f"Range: {item_data.get('alcance', 'N/A')}", 12, cor_stats, x + 350, y + 95)
    else:
        desenhar_texto(tela, f"Effect: {item_data.get('efeito', 'N/A')}", 12, cor_stats, x + 150, y + 95)
        desenhar_texto(tela, f"Duration: {item_data.get('duracao', 'N/A')}", 12, cor_stats, x + 300, y + 95)
    
    # Badge de raridade
    badge_x = x + largura - 80
    badge_y = y + 10
    badge_rect = pygame.Rect(badge_x, badge_y, 70, 20)
    badge_color = cor_brilho if tem_estoque else (100, 100, 100)
    pygame.draw.rect(tela, badge_color, badge_rect, 0, 10)
    desenhar_texto(tela, raridade.upper(), 10, (0, 0, 0), badge_x + 35, badge_y + 10)
    
    # Status de seleção
    if tem_estoque and selecionado:
        # Checkmark
        check_x = x + largura - 40
        check_y = y + altura - 40
        pygame.draw.circle(tela, VERDE, (check_x, check_y), 15)
        pygame.draw.polygon(tela, BRANCO, [
            (check_x - 8, check_y),
            (check_x - 3, check_y + 5),
            (check_x + 8, check_y - 5)
        ], 3)
        desenhar_texto(tela, "EQUIPPED", 12, VERDE, x + largura - 100, y + altura - 15)
    elif not tem_estoque:
        desenhar_texto(tela, "NOT PURCHASED", 12, VERMELHO, x + largura - 120, y + altura - 15)
    else:
        desenhar_texto(tela, "Click to equip", 12, CIANO, x + largura - 120, y + altura - 15)

def tela_inventario(tela, relogio, gradiente_inventario, fonte_titulo, fonte_normal):
    """
    Exibe a tela de inventário moderna com interface visual rica.
    """
    pygame.mouse.set_visible(True)
    
    from src.game.moeda_manager import MoedaManager
    
    inventario_manager = InventarioManager()
    moeda_manager = MoedaManager()
    
    estrelas = criar_estrelas(NUM_ESTRELAS_MENU)
    
    scroll_y = 0
    max_scroll = 0
    aba_ativa = 0
    
    while True:
        tempo_atual = pygame.time.get_ticks()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
                if evento.key == pygame.K_1:
                    aba_ativa = 0
                    scroll_y = 0
                if evento.key == pygame.K_2:
                    aba_ativa = 1
                    scroll_y = 0
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
                    
                    # Verificar abas
                    aba_largura = 250
                    aba_altura = 60
                    aba1_x = LARGURA // 2 - 130
                    aba2_x = LARGURA // 2 + 130
                    aba_y = 180
                    
                    rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
                    rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
                    
                    if rect_aba1.collidepoint(mouse_pos):
                        aba_ativa = 0
                        scroll_y = 0
                    elif rect_aba2.collidepoint(mouse_pos):
                        aba_ativa = 1
                        scroll_y = 0
                    
                    # Verificar cliques nos cards
                    y_inicial = 270 - scroll_y
                    card_altura = 130
                    espaco_cards = 20
                    
                    if aba_ativa == 0:  # Armas
                        armas = inventario_manager.obter_armas_disponiveis()
                        arma_atual = inventario_manager.obter_arma_selecionada()
                        
                        for i, (arma_key, arma_data) in enumerate(armas.items()):
                            # Sempre mostrar todos os itens, não filtrar por quantidade
                            y_card = y_inicial + i * (card_altura + espaco_cards)
                            card_rect = pygame.Rect(LARGURA // 2 - 350, y_card, 700, card_altura)
                            
                            # Apenas permitir clique se tem estoque e está visível
                            if (card_rect.collidepoint(mouse_pos) and 
                                y_card > 200 and y_card < ALTURA - 150 and
                                arma_data["quantidade"] > 0):
                                inventario_manager.selecionar_arma(
                                    arma_key if arma_key != arma_atual else "nenhuma"
                                )
                    
                    else:  # Itens
                        itens = inventario_manager.obter_itens_disponiveis()
                        item_atual = inventario_manager.obter_item_selecionado()
                        
                        for i, (item_key, item_data) in enumerate(itens.items()):
                            # Sempre mostrar todos os itens, não filtrar por quantidade
                            y_card = y_inicial + i * (card_altura + espaco_cards)
                            card_rect = pygame.Rect(LARGURA // 2 - 350, y_card, 700, card_altura)
                            
                            # Apenas permitir clique se tem estoque e está visível
                            if (card_rect.collidepoint(mouse_pos) and 
                                y_card > 200 and y_card < ALTURA - 150 and
                                item_data["quantidade"] > 0):
                                inventario_manager.selecionar_item(
                                    item_key if item_key != item_atual else "nenhum"
                                )
                    
                    # Botão voltar
                    if pygame.Rect(60, ALTURA - 80, 180, 50).collidepoint(mouse_pos):
                        return "menu"
                
                elif evento.button == 4:  # Scroll up
                    scroll_y = max(0, scroll_y - 40)
                elif evento.button == 5:  # Scroll down
                    scroll_y = min(max_scroll, scroll_y + 40)
        
        # Atualizar estrelas
        for estrela in estrelas:
            estrela[0] -= estrela[4] * 0.5
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        
        # Desenhar fundo
        tela.blit(gradiente_inventario, (0, 0))
        desenhar_estrelas(tela, estrelas)
        desenhar_fundo_futurista(tela, tempo_atual)
        
        # Overlay semi-transparente para profundidade
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 100))
        tela.blit(overlay, (0, 0))
        
        # Título principal com efeitos
        titulo_y = 80
        # Sombra do título
        desenhar_texto(tela, "TACTICAL INVENTORY", 60, (50, 50, 100), LARGURA // 2 + 3, titulo_y + 3, sombra=False)
        # Título principal
        desenhar_texto(tela, "TACTICAL INVENTORY", 60, (200, 220, 255), LARGURA // 2, titulo_y, sombra=False)
        
        # Subtítulo
        desenhar_texto(tela, "Configure your loadout for battle", 24, (150, 170, 200), LARGURA // 2, titulo_y + 40)
        
        # HUD - Moedas com design futurista
        moeda_x = LARGURA - 150
        moeda_y = 40
        
        # Fundo da moeda
        moeda_bg = pygame.Rect(moeda_x - 60, moeda_y - 20, 120, 40)
        pygame.draw.rect(tela, (20, 40, 80, 200), moeda_bg, 0, 20)
        pygame.draw.rect(tela, (100, 150, 255), moeda_bg, 2, 20)
        
        # Ícone da moeda animado
        moeda_pulso = (math.sin(tempo_atual / 300) + 1) / 2
        moeda_size = 12 + int(moeda_pulso * 3)
        pygame.draw.circle(tela, AMARELO, (moeda_x - 30, moeda_y), moeda_size)
        pygame.draw.circle(tela, (255, 215, 0), (moeda_x - 30, moeda_y), moeda_size - 2)
        
        # Quantidade de moedas
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 20, AMARELO, moeda_x + 10, moeda_y)
        
        # Sistema de abas futurista
        aba_largura = 250
        aba_altura = 60
        aba1_x = LARGURA // 2 - 130
        aba2_x = LARGURA // 2 + 130
        aba_y = 180
        
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        
        # Aba 1 (Armas)
        rect_aba1 = pygame.Rect(aba1_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
        hover_aba1 = rect_aba1.collidepoint(mouse_pos)
        
        cor_aba1_base = (100, 50, 50) if aba_ativa == 0 else (60, 30, 30)
        cor_aba1_hover = (150, 80, 80) if aba_ativa == 0 else (100, 50, 50)
        cor_aba1_borda = (255, 100, 100) if aba_ativa == 0 else (150, 70, 70)
        
        pygame.draw.rect(tela, cor_aba1_hover if hover_aba1 else cor_aba1_base, rect_aba1, 0, 15)
        pygame.draw.rect(tela, cor_aba1_borda, rect_aba1, 4 if aba_ativa == 0 else 2, 15)
        
        # Ícone de arma na aba
        desenhar_icone_espingarda_moderno(tela, aba1_x - 60, aba_y, tempo_atual, 20)
        desenhar_texto(tela, "WEAPONS", 22, BRANCO, aba1_x + 20, aba_y - 5)
        desenhar_texto(tela, "Press 1", 12, (180, 180, 180), aba1_x + 20, aba_y + 15)
        
        # Aba 2 (Itens)
        rect_aba2 = pygame.Rect(aba2_x - aba_largura//2, aba_y - aba_altura//2, aba_largura, aba_altura)
        hover_aba2 = rect_aba2.collidepoint(mouse_pos)
        
        cor_aba2_base = (50, 100, 50) if aba_ativa == 1 else (30, 60, 30)
        cor_aba2_hover = (80, 150, 80) if aba_ativa == 1 else (50, 100, 50)
        cor_aba2_borda = (100, 255, 100) if aba_ativa == 1 else (70, 150, 70)
        
        pygame.draw.rect(tela, cor_aba2_hover if hover_aba2 else cor_aba2_base, rect_aba2, 0, 15)
        pygame.draw.rect(tela, cor_aba2_borda, rect_aba2, 4 if aba_ativa == 1 else 2, 15)
        
        # Ícone de item na aba
        desenhar_icone_granada_moderno(tela, aba2_x - 60, aba_y, tempo_atual, 15)
        desenhar_texto(tela, "ITEMS", 22, BRANCO, aba2_x + 20, aba_y - 5)
        desenhar_texto(tela, "Press 2", 12, (180, 180, 180), aba2_x + 20, aba_y + 15)
        
        # Área de conteúdo com clipping
        conteudo_y = 270
        conteudo_altura = ALTURA - 350
        
        # Criar superfície para clipping
        conteudo_surf = pygame.Surface((LARGURA, conteudo_altura), pygame.SRCALPHA)
        
        # Desenhar cards na superfície de conteúdo
        y_inicial = -scroll_y
        card_altura = 130
        espaco_cards = 20
        
        if aba_ativa == 0:  # Armas
            armas = inventario_manager.obter_armas_disponiveis()
            arma_atual = inventario_manager.obter_arma_selecionada()
            
            for i, (arma_key, arma_data) in enumerate(armas.items()):
                y_card = y_inicial + i * (card_altura + espaco_cards)
                
                if y_card > -card_altura and y_card < conteudo_altura:
                    card_x = LARGURA // 2 - 350
                    card_rect = pygame.Rect(card_x, y_card, 700, card_altura)
                    # Apenas verificar hover se tem estoque
                    hover_card = (card_rect.move(0, conteudo_y).collidepoint(mouse_pos) and 
                                conteudo_y <= mouse_pos[1] <= conteudo_y + conteudo_altura and
                                arma_data["quantidade"] > 0)
                    
                    desenhar_card_item_moderno(
                        conteudo_surf, arma_data, arma_key, 
                        card_x, y_card, 700, card_altura,
                        arma_key == arma_atual, tempo_atual, hover_card
                    )
            
            max_scroll = max(0, len(armas) * (card_altura + espaco_cards) - conteudo_altura + 50)
            
        else:  # Itens
            itens = inventario_manager.obter_itens_disponiveis()
            item_atual = inventario_manager.obter_item_selecionado()
            
            for i, (item_key, item_data) in enumerate(itens.items()):
                y_card = y_inicial + i * (card_altura + espaco_cards)
                
                if y_card > -card_altura and y_card < conteudo_altura:
                    card_x = LARGURA // 2 - 350
                    card_rect = pygame.Rect(card_x, y_card, 700, card_altura)
                    # Apenas verificar hover se tem estoque
                    hover_card = (card_rect.move(0, conteudo_y).collidepoint(mouse_pos) and 
                                conteudo_y <= mouse_pos[1] <= conteudo_y + conteudo_altura and
                                item_data["quantidade"] > 0)
                    
                    desenhar_card_item_moderno(
                        conteudo_surf, item_data, item_key, 
                        card_x, y_card, 700, card_altura,
                        item_key == item_atual, tempo_atual, hover_card
                    )
            
            max_scroll = max(0, len(itens) * (card_altura + espaco_cards) - conteudo_altura + 50)
        
        # Aplicar clipping e desenhar conteúdo
        clip_rect = pygame.Rect(0, 0, LARGURA, conteudo_altura)
        conteudo_surf.set_clip(clip_rect)
        tela.blit(conteudo_surf, (0, conteudo_y))
        
        # Barra de scroll moderna
        if max_scroll > 0:
            barra_x = LARGURA - 15
            barra_y = conteudo_y
            barra_largura = 8
            barra_altura_total = conteudo_altura
            
            # Fundo da barra
            pygame.draw.rect(tela, (50, 50, 80, 150), 
                           (barra_x, barra_y, barra_largura, barra_altura_total), 0, 4)
            
            # Indicador
            indicador_altura = max(30, int(barra_altura_total * conteudo_altura / (conteudo_altura + max_scroll)))
            indicador_y = barra_y + int((scroll_y / max_scroll) * (barra_altura_total - indicador_altura))
            
            pygame.draw.rect(tela, (150, 200, 255), 
                           (barra_x, indicador_y, barra_largura, indicador_altura), 0, 4)
        
        # Instruções na parte inferior
        instrucoes_y = ALTURA - 120
        
        if aba_ativa == 0:
            desenhar_texto(tela, "Press E during gameplay to switch weapons", 18, (100, 200, 255), 
                          LARGURA // 2, instrucoes_y)
        else:
            desenhar_texto(tela, "Press Q during gameplay to use equipped item", 18, (100, 255, 100), 
                          LARGURA // 2, instrucoes_y)
        
        desenhar_texto(tela, "Use number keys 1-2 or click tabs to navigate • Mouse wheel to scroll", 14, 
                      (150, 150, 200), LARGURA // 2, instrucoes_y + 25)
        
        # Botão voltar futurista
        botao_rect = pygame.Rect(60, ALTURA - 80, 180, 50)
        hover_voltar = botao_rect.collidepoint(mouse_pos)
        
        cor_botao = (80, 50, 100) if hover_voltar else (60, 30, 80)
        pygame.draw.rect(tela, cor_botao, botao_rect, 0, 15)
        pygame.draw.rect(tela, (150, 100, 200), botao_rect, 3, 15)
        
        # Ícone de seta no botão
        seta_pontos = [
            (80, ALTURA - 55),
            (95, ALTURA - 65),
            (95, ALTURA - 45)
        ]
        pygame.draw.polygon(tela, BRANCO, seta_pontos)
        desenhar_texto(tela, "BACK TO MENU", 16, BRANCO, 150, ALTURA - 55)
        
        present_frame()
        relogio.tick(FPS)