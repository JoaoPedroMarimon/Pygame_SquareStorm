#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criação padronizada de inimigos com diferentes características.
Este arquivo facilita a criação de diversos tipos de inimigos para as fases.
"""

from src.config import *
from src.entities.quadrado import Quadrado

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
    def criar_inimigo_resistente(x, y):
        """
        Cria um inimigo vermelho mais escuro, mais lento e com mais vida.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como inimigo resistente
        """
        cor_vermelho_escuro = (180, 30, 30)  # Vermelho mais escuro
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.9  # 10% mais lento
        
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, cor_vermelho_escuro, velocidade)
        inimigo.vidas = 2
        inimigo.vidas_max = 2
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO + 50  # Atira um pouco mais devagar
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
    def criar_inimigo_boss(x, y):
        """
        Cria um chefe com três vidas e alta cadência de tiro.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como chefe
        """
        # Tamanho maior para o chefe
        tamanho = TAMANHO_QUADRADO * 1.5
        
        # Cor personalizada para o chefe
        cor_boss = (180, 0, 180)  # Roxo intenso
        
        # Velocidade reduzida
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.8
        
        # Criar o chefe com propriedades personalizadas
        boss = Quadrado(x, y, int(tamanho), cor_boss, velocidade)
        boss.vidas = 3
        boss.vidas_max = 3
        boss.tempo_cooldown = COOLDOWN_TIRO_ESPECIAL - 100  # Atira muito mais rápido
        return boss
    
    @staticmethod
    def criar_inimigo_bombardeiro(x, y):
        """
        Cria um inimigo laranja que é lento mas dispara tiros mais rápidos.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como bombardeiro
        """
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.7  # 30% mais lento
        
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, LARANJA, velocidade)
        inimigo.vidas = 1
        inimigo.vidas_max = 1
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO - 150  # Atira muito mais rápido
        return inimigo
    
    @staticmethod
    def criar_inimigo_sniper(x, y):
        """
        Cria um inimigo verde escuro que atira mais lentamente,
        mas é mais preciso.
        
        Args:
            x, y: Posição inicial do inimigo
            
        Returns:
            Objeto Quadrado configurado como sniper
        """
        cor_verde_escuro = (0, 100, 0)  # Verde escuro
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.9  # 10% mais lento
        
        inimigo = Quadrado(x, y, TAMANHO_QUADRADO, cor_verde_escuro, velocidade)
        inimigo.vidas = 1
        inimigo.vidas_max = 1
        inimigo.tempo_cooldown = COOLDOWN_TIRO_INIMIGO + 200  # Atira muito mais devagar
        # Para implementar a maior precisão, seria necessário modificar a lógica de IA
        return inimigo
    
    @staticmethod
    def criar_inimigo_aleatorio(x, y, dificuldade=1):
        """
        Cria um inimigo aleatório com base na dificuldade.
        
        Args:
            x, y: Posição inicial do inimigo
            dificuldade: Nível de dificuldade (1-5)
            
        Returns:
            Objeto Quadrado configurado aleatoriamente
        """
        import random
        
        # Quanto maior a dificuldade, mais chance de inimigos melhores
        if dificuldade == 1:
            tipos = ["basico", "rapido"]
            pesos = [0.7, 0.3]
        elif dificuldade == 2:
            tipos = ["basico", "rapido", "resistente"]
            pesos = [0.5, 0.3, 0.2]
        elif dificuldade == 3:
            tipos = ["basico", "rapido", "resistente", "bombardeiro"]
            pesos = [0.4, 0.3, 0.2, 0.1]
        elif dificuldade == 4:
            tipos = ["rapido", "resistente", "bombardeiro", "especial"]
            pesos = [0.3, 0.3, 0.2, 0.2]
        else:  # dificuldade 5 ou maior
            tipos = ["resistente", "bombardeiro", "especial", "elite"]
            pesos = [0.3, 0.3, 0.3, 0.1]
        
        # Escolher um tipo com base nos pesos
        tipo_escolhido = random.choices(tipos, weights=pesos, k=1)[0]
        
        # Criar o inimigo conforme o tipo escolhido
        if tipo_escolhido == "basico":
            return InimigoFactory.criar_inimigo_basico(x, y)
        elif tipo_escolhido == "rapido":
            return InimigoFactory.criar_inimigo_rapido(x, y)
        elif tipo_escolhido == "resistente":
            return InimigoFactory.criar_inimigo_resistente(x, y)
        elif tipo_escolhido == "bombardeiro":
            return InimigoFactory.criar_inimigo_bombardeiro(x, y)
        elif tipo_escolhido == "especial":
            return InimigoFactory.criar_inimigo_especial(x, y)
        elif tipo_escolhido == "elite":
            return InimigoFactory.criar_inimigo_elite(x, y)
        else:
            return InimigoFactory.criar_inimigo_basico(x, y)  # Fallback
        

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