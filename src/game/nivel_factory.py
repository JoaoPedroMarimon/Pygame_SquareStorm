#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criar inimigos e configurar fases.
Factory pattern para facilitar a criação de diferentes níveis/fases.
"""

import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.inimigo_factory import InimigoFactory

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
        
        inimigo = InimigoFactory.criar_inimigo_basico(pos_x, pos_y)
        inimigos.append(inimigo)
        
        return inimigos
    
    def criar_fase_2():
        """
        Fase 2: Dois inimigos, um superior e um inferior.
        """
        inimigos = []
        
        # Inimigo 1 - Superior (básico)
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA // 3
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        # Inimigo 2 - Inferior (rápido)
        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA // 3
        inimigos.append(InimigoFactory.criar_inimigo_rapido(pos_x2, pos_y2))
        
        return inimigos
    
    @staticmethod
    def criar_fase_3():
        """
        Fase 3: Um inimigo especial roxo com 2 vidas.
        """
        inimigos = []
        
        pos_x = LARGURA - 150
        pos_y = ALTURA // 2
        
        inimigo_especial = InimigoFactory.criar_inimigo_especial(pos_x, pos_y)
        inimigos.append(inimigo_especial)
        
        return inimigos
    
    @staticmethod
    def criar_fase_4():
        """
        Fase 4: Dois inimigos básicos e um inimigo especial.
        """
        inimigos = []
        
        # Dois inimigos básicos
        pos_x1 = LARGURA - 200
        pos_y1 = ALTURA // 4
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 200
        pos_y2 = 3 * ALTURA // 4
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x2, pos_y2))
        
        # Um inimigo especial roxo no meio
        pos_x3 = LARGURA - 100
        pos_y3 = ALTURA // 2
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        return inimigos
    
    @staticmethod
    def criar_fase_5():
        """
        Fase 5: Um inimigo elite ciano.
        """
        inimigos = []
        
        pos_x = LARGURA - 150
        pos_y = ALTURA // 2
        
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x, pos_y))
        
        return inimigos


    @staticmethod
    def criar_fase_6():
        """
        Fase 6: Um mix de todos os tipos de inimigos.
        """
        inimigos = []
        
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA // 3
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        

        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 =   ALTURA // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA // 5
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        return inimigos

    @staticmethod
    def criar_fase_7():
        """
        Fase 7: dois cianos e um especial.
        """
        inimigos = []
        
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x1, pos_y1))
        

        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 =   ALTURA // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA // 5
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        return inimigos
    
    @staticmethod
    def criar_fase_8():
        """
        Fase de exemplo com inimigos perseguidores.
        """
        inimigos = []
        
        # Adicionar 3 perseguidores em posições diferentes
        pos_x1 = LARGURA - 100
        pos_y1 = ALTURA // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 200
        pos_y2 = ALTURA // 2
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))
        
        pos_x3 = LARGURA - 100
        pos_y3 = 3 * ALTURA // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x3, pos_y3))
        
        
        return inimigos