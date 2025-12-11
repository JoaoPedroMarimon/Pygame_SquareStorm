#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criação padronizada de inimigos com diferentes características.
Este arquivo facilita a criação de diversos tipos de inimigos para as fases.
"""

from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.inimigo_metralhadora import InimigoMetralhadora
from src.entities.inimigo_mago import InimigoMago

class InimigoFactory:
    """
    Factory para criação de diferentes tipos de inimigos.
    Padroniza as cores, vida, velocidade e comportamentos específicos.
    """
    
    @staticmethod
    def criar_inimigo_basico(x, y):
        """
        Cria um inimigo básico vermelho com uma vida.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como inimigo básico
        """
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, VERMELHO, VELOCIDADE_INIMIGO_BASE)
        inimigo.vidas = 1
        inimigo.vidas_max = 1
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO
        return inimigo
    
    @staticmethod
    def criar_inimigo_rapido(x, y):
        """
        Cria um inimigo vermelho mais claro e mais rápido que o básico.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como inimigo rápido
        """
        cor_vermelho_claro = (255, 80, 80)  # Vermelho mais claro
        velocidade = VELOCIDADE_INIMIGO_BASE * 1.2  # 20% mais rápido
        
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, cor_vermelho_claro, velocidade)
        inimigo.vidas = 1
        inimigo.vidas_max = 1
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO - 50  # Atira um pouco mais rápido
        return inimigo
    
    
    @staticmethod
    def criar_inimigo_especial(x, y):
        """
        Cria um inimigo especial roxo com duas vidas.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como inimigo especial
        """
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, ROXO, VELOCIDADE_INIMIGO_ESPECIAL)
        inimigo.vidas = 2
        inimigo.vidas_max = 2
        inimigo.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL
        return inimigo
    
    @staticmethod
    def criar_inimigo_elite(x, y):
        """
        Cria um inimigo elite ciano, muito rápido.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como inimigo elite
        """
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, CIANO, VELOCIDADE_INIMIGO_CIANO)
        inimigo.vidas = 1
        inimigo.vidas_max = 1
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO - 100  # Atira muito mais rápido
        return inimigo
    
 

    @staticmethod
    def criar_inimigo_perseguidor(x, y):
        """
        Cria um inimigo perseguidor que corre atrás do jogador e causa dano por colisão.

        Args:
            x, y: Posição inicial do inimigo

        Returns:
            Objeto Quadrado configurado como inimigo perseguidor
        """
        # Cor laranja vibrante para o perseguidor
        cor_perseguidor = (255, 140, 0)  # Laranja
        # Velocidade maior que a média, para poder alcançar o jogador
        velocidade = VELOCIDADE_INIMIGO_BASE * 1.3

        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, cor_perseguidor, velocidade)
        inimigo.vidas = 2
        inimigo.vidas_max = 2
        # Definir um cooldown para o dano por colisão (evitar dano contínuo)
        inimigo.cooldown_colisao = 1000  # 1 segundo entre danos
        inimigo.tempo_ultima_colisao = 0
        # Flag para identificar este tipo especial de inimigo
        inimigo.perseguidor = True
        # Não vai atirar, então pode ter um cooldown muito alto
        inimigo.tempo_cooldown = 99999999
        return inimigo

    @staticmethod
    def criar_inimigo_metralhadora(x, y):
        """
        Cria um inimigo com metralhadora.
        Atira rapidamente por 5 segundos, depois recarrega por 3 segundos.

        Args:
            x, y: Posição inicial do inimigo

        Returns:
            Objeto InimigoMetralhadora configurado
        """
        return InimigoMetralhadora(x, y)

    @staticmethod
    def criar_inimigo_mago(x, y):
        """
        Cria um inimigo mago branco.
        Possui escudo protetor cíclico (4s ativo, 4s inativo),
        atira bolas de fogo e invoca 3 inimigos básicos após 4-15 tiros.

        Args:
            x, y: Posição inicial do inimigo

        Returns:
            Objeto InimigoMago configurado
        """
        return InimigoMago(x, y)