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

        inimigos = []
        
        pos_x = LARGURA - 150
        pos_y = ALTURA // 2
        
        inimigo_especial = Quadrado(pos_x, pos_y, TAMANHO_QUADRADO, ROXO, VELOCIDADE_INIMIGO_ESPECIAL)
        
        inimigo_especial.vidas = 2
        inimigo_especial.vidas_max = 2
        inimigo_especial.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
        
        inimigos.append(inimigo_especial)
        
        return inimigos
    
    @staticmethod
    def criar_fase_4():

        inimigos = []
        
        pos_x1 = LARGURA - 200
        pos_y1 = ALTURA // 4
        inimigos.append(Quadrado(pos_x1, pos_y1, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        pos_x2 = LARGURA - 200
        pos_y2 = 3 * ALTURA // 4
        inimigos.append(Quadrado(pos_x2, pos_y2, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
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

        inimigos = []
        
        pos_x4 = LARGURA - 50
        pos_y4 = ALTURA // 2
        inimigo_ciano = Quadrado(pos_x4, pos_y4, TAMANHO_QUADRADO, CIANO, VELOCIDADE_INIMIGO_CIANO)
        inimigos.append(inimigo_ciano)
        
        return inimigos


    @staticmethod
    def criar_fase_6():

        inimigos = []
        
        pos_x1 = LARGURA - 200
        pos_y1 = ALTURA // 4
        inimigos.append(Quadrado(pos_x1, pos_y1, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE))
        
        pos_x2 = LARGURA - 200
        pos_y2 = 3 * ALTURA // 4
        inimigo_roxo = Quadrado(pos_x2, pos_y2, TAMANHO_QUADRADO, ROXO, VELOCIDADE_INIMIGO_ESPECIAL)
        inimigo_roxo.vidas = 2
        inimigo_roxo.vidas_max = 2
        inimigo_roxo.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
        inimigos.append(inimigo_roxo)
        
        pos_x3 = LARGURA - 100
        pos_y3 = ALTURA // 2
        inimigo_ciano = Quadrado(pos_x3, pos_y3, TAMANHO_QUADRADO, CIANO, VELOCIDADE_INIMIGO_CIANO)
        inimigos.append(inimigo_ciano)
        
        return inimigos
