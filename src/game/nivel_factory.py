#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criar inimigos e configurar fases.
Factory pattern para facilitar a criação de diferentes níveis/fases.
"""

import random
from src.config import *
from src.entities.quadrado import Quadrado
import math  # Adicionando a importação de math


class NivelFactory:
    """
    Classe factory para criar diferentes níveis/fases do jogo.
    Cada método cria os inimigos para uma fase específica.
    """
    
    @staticmethod
    def criar_fase(numero_fase):
        """
        Cria os inimigos para a fase especificada.
        
        Args:
            numero_fase: Número da fase a ser criada
            
        Returns:
            Lista de inimigos para a fase
        """
        # Se existir um método específico para a fase, use-o
        # Caso contrário, crie uma fase genérica baseada no número
        metodo_fase = getattr(NivelFactory, f"criar_fase_{numero_fase}", None)
        
        if metodo_fase:
            return metodo_fase()
        else:
            # Fase genérica: número da fase = número de inimigos
            return NivelFactory.criar_fase_generica(numero_fase)
    
    @staticmethod
    def criar_fase_1():
        """
        Fase 1: Um único inimigo vermelho simples.
        """
        inimigos = []
        
        # Inimigo centralizado
        pos_x = LARGURA - 150
        pos_y = ALTURA // 2
        cor_inimigo = VERMELHO
        velocidade = VELOCIDADE_INIMIGO_BASE
        
        inimigo = Quadrado(pos_x, pos_y, TAMANHO_QUADRADO, cor_inimigo, velocidade)
        inimigos.append(inimigo)
        
        return inimigos
    
    @staticmethod
    def criar_fase_2():
        """
        Fase 2: Dois inimigos vermelhos em posições diferentes.
        """
        inimigos = []
        
        # Inimigo 1 - Superior
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA // 3
        cor_inimigo1 = VERMELHO
        velocidade_inimigo1 = VELOCIDADE_INIMIGO_BASE
        inimigos.append(Quadrado(pos_x1, pos_y1, TAMANHO_QUADRADO, cor_inimigo1, velocidade_inimigo1))
        
        # Inimigo 2 - Inferior (com cor ligeiramente diferente)
        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA // 3
        cor_inimigo2 = (255, 80, 80)  # Vermelho um pouco diferente
        velocidade_inimigo2 = VELOCIDADE_INIMIGO_BASE * 1.1  # Um pouco mais rápido
        inimigos.append(Quadrado(pos_x2, pos_y2, TAMANHO_QUADRADO, cor_inimigo2, velocidade_inimigo2))
        
        return inimigos
    
    @staticmethod
    def criar_fase_3():
        """
        Fase 3: Um inimigo roxo especial com 2 vidas.
        """
        inimigos = []
        
        # Inimigo especial roxo
        pos_x = LARGURA - 150
        pos_y = ALTURA // 2
        
        # Criando o inimigo especial com características únicas
        inimigo_especial = Quadrado(pos_x, pos_y, TAMANHO_QUADRADO, ROXO, VELOCIDADE_INIMIGO_ESPECIAL)
        
        # Configurações especiais para o inimigo roxo
        inimigo_especial.vidas = 2
        inimigo_especial.vidas_max = 2
        inimigo_especial.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
        
        inimigos.append(inimigo_especial)
        
        return inimigos
    
    @staticmethod
    def criar_fase_4():
        """
        Fase 4: Dois inimigos normais e um inimigo roxo.
        """
        inimigos = []
        
        # Inimigo 1 - Superior
        pos_x1 = LARGURA - 200
        pos_y1 = ALTURA // 4
        inimigos.append(Quadrado(pos_x1, pos_y1, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        # Inimigo 2 - Inferior
        pos_x2 = LARGURA - 200
        pos_y2 = 3 * ALTURA // 4
        inimigos.append(Quadrado(pos_x2, pos_y2, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        # Inimigo Roxo - Central
        pos_x3 = LARGURA - 100
        pos_y3 = ALTURA // 2
        inimigo_roxo = Quadrado(pos_x3, pos_y3, TAMANHO_QUADRADO, ROXO, VELOCIDADE_INIMIGO_ESPECIAL)
        inimigo_roxo.vidas = 2
        inimigo_roxo.vidas_max = 2
        inimigo_roxo.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
        inimigos.append(inimigo_roxo)
        
        return inimigos
    
    @staticmethod
    def criar_fase_5():
        """
        Fase 5: Um inimigo ciano especial que se move mais rápido e três inimigos normais.
        """
        inimigos = []
        
        # Três inimigos normais em formação triangular
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA // 4
        inimigos.append(Quadrado(pos_x1, pos_y1, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        pos_x2 = LARGURA - 150
        pos_y2 = 3 * ALTURA // 4
        inimigos.append(Quadrado(pos_x2, pos_y2, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        pos_x3 = LARGURA - 250
        pos_y3 = ALTURA // 2
        inimigos.append(Quadrado(pos_x3, pos_y3, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        # Inimigo Ciano Especial - mais rápido
        pos_x4 = LARGURA - 50
        pos_y4 = ALTURA // 2
        inimigo_ciano = Quadrado(pos_x4, pos_y4, TAMANHO_QUADRADO, CIANO, VELOCIDADE_INIMIGO_BASE * 1.5)
        inimigos.append(inimigo_ciano)
        
        return inimigos
        
    @staticmethod
    def criar_fase_generica(numero_fase):
        """
        Cria uma fase genérica com base no número da fase.
        Útil para fases não implementadas especificamente.
        
        Args:
            numero_fase: Número da fase, determina a quantidade e dificuldade dos inimigos
            
        Returns:
            Lista de inimigos para a fase
        """
        inimigos = []
        
        # Número de inimigos base = número da fase
        num_inimigos = numero_fase
        
        # A cada 3 fases, adiciona um inimigo roxo (2 vidas)
        num_roxos = numero_fase // 3
        
        # Restante são inimigos normais
        num_normais = num_inimigos - num_roxos
        
        # Criar inimigos normais
        for i in range(num_normais):
            # Distribuir os inimigos em um semicírculo do lado direito da tela
            angulo = math.pi * (i / (num_normais - 1 if num_normais > 1 else 1) - 0.5)
            raio = 200
            
            pos_x = LARGURA - 100 - raio * math.cos(angulo)
            pos_y = ALTURA // 2 + raio * math.sin(angulo)
            
            # Variação na cor vermelha
            r = 255
            g = 50 + (i * 20) % 100
            b = 50 + (i * 15) % 100
            cor = (r, g, b)
            
            # Velocidade varia um pouco
            velocidade = VELOCIDADE_INIMIGO_BASE * (0.9 + random.random() * 0.4)
            
            inimigos.append(Quadrado(pos_x, pos_y, TAMANHO_QUADRADO, cor, velocidade))
        
        # Criar inimigos roxos (com 2 vidas)
        for i in range(num_roxos):
            # Posicionamento dos roxos mais ao centro
            angulo = math.pi * (i / (num_roxos - 1 if num_roxos > 1 else 1) - 0.5)
            raio = 120
            
            pos_x = LARGURA - 150 - raio * math.cos(angulo)
            pos_y = ALTURA // 2 + raio * math.sin(angulo)
            
            # Variação na cor roxa
            r = 180 + (i * 10) % 40
            g = 50 + (i * 5) % 30
            b = 230 - (i * 10) % 40
            cor = (r, g, b)
            
            inimigo_roxo = Quadrado(pos_x, pos_y, TAMANHO_QUADRADO, cor, VELOCIDADE_INIMIGO_ESPECIAL)
            inimigo_roxo.vidas = 2
            inimigo_roxo.vidas_max = 2
            inimigo_roxo.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
            
            inimigos.append(inimigo_roxo)
        
        return inimigos