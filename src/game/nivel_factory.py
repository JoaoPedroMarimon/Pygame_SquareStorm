#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criar inimigos e configurar fases.
Factory pattern para facilitar a criação de diferentes níveis/fases.
ATUALIZADO: Incluindo a Fase 10 - Boss Fight com Boss Fusion.
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
            Lista de inimigos para a fase, ou objeto especial para boss fight
        """
        # Se existir um método específico para a fase, use-o
        # Caso contrário, crie uma fase genérica baseada no número
        metodo_fase = getattr(NivelFactory, f"criar_fase_{numero_fase}", None)
        
        if metodo_fase:
            return metodo_fase()
        else:
            # Fase genérica para números altos
            return NivelFactory.criar_fase_generica(numero_fase)

    @staticmethod
    def criar_fase_generica(numero_fase):
        """
        Cria uma fase genérica baseada no número da fase.
        Usada para fases que não têm método específico.
        """
        inimigos = []
        
        # Dificuldade baseada no número da fase
        num_inimigos = min(3 + numero_fase // 2, 8)  # Máximo 8 inimigos
        
        for i in range(num_inimigos):
            # Posição aleatória na metade direita da tela
            pos_x = random.randint(LARGURA // 2, LARGURA - 100)
            pos_y = random.randint(50, ALTURA_JOGO - 50)
            
            # Tipo de inimigo baseado na fase
            if numero_fase < 5:
                inimigo = random.choice([
                    InimigoFactory.criar_inimigo_basico(pos_x, pos_y),
                    InimigoFactory.criar_inimigo_rapido(pos_x, pos_y)
                ])
            elif numero_fase < 10:
                inimigo = random.choice([
                    InimigoFactory.criar_inimigo_rapido(pos_x, pos_y),
                    InimigoFactory.criar_inimigo_especial(pos_x, pos_y),
                    InimigoFactory.criar_inimigo_elite(pos_x, pos_y)
                ])
            else:
                # Fases muito avançadas: mix de todos
                inimigo = random.choice([
                    InimigoFactory.criar_inimigo_especial(pos_x, pos_y),
                    InimigoFactory.criar_inimigo_elite(pos_x, pos_y),
                    InimigoFactory.criar_inimigo_perseguidor(pos_x, pos_y)
                ])
            
            inimigos.append(inimigo)
        
        return inimigos
    
    @staticmethod
    def criar_fase_1():
        """
        Fase 1: Um único inimigo vermelho simples.
        """
        inimigos = []
        
        # Inimigo centralizado
        pos_x = LARGURA - 150
        pos_y = ALTURA_JOGO // 2
        
        inimigo = InimigoFactory.criar_inimigo_basico(pos_x, pos_y)
        inimigos.append(inimigo)
        
        return inimigos
    
    @staticmethod
    @staticmethod
    def criar_fase_2():
        """
        Fase 2: Dois inimigos, um superior e um inferior.
        """
        inimigos = []
        
        # Inimigo 1 - Superior (básico)
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 = ALTURA_JOGO // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA_JOGO // 5
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        return inimigos

    @staticmethod
    def criar_fase_7():
        """
        Fase 7: dois cianos e um especial.
        """
        inimigos = []
        
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x1, pos_y1))
        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 = ALTURA_JOGO // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA_JOGO // 5
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
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 200
        pos_y2 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))
        
        pos_x3 = LARGURA - 100
        pos_y3 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x3, pos_y3))
        
        return inimigos
    
    @staticmethod
    def criar_fase_9():
        """
        Fase 9: Preparação para o boss - mix intenso de inimigos.
        """
        inimigos = []
        
        # 2 perseguidores
        pos_x1 = LARGURA - 100
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 100
        pos_y2 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))
        
        # 2 elites
        pos_x3 = LARGURA - 200
        pos_y3 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x3, pos_y3))
        
        pos_x4 = LARGURA - 200
        pos_y4 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        # 1 especial no centro
        pos_x5 = LARGURA - 150
        pos_y5 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x5, pos_y5))
        
        return inimigos
    
    @staticmethod
    def criar_fase_10():
        """
        Fase 10: BOSS FIGHT - Boss Fusion.
        Retorna informações sobre o boss fight.
        """
        print("🔥 Criando Boss Fight - Fase 10")
        return {
            'tipo': 'boss_fight',
            'boss': 'fusion',
            'cutscene': True,
            'mensagem': 'BOSS FIGHT - BOSS FUSION DESPERTA!'
        }
    
    @staticmethod
    def e_boss_fight(resultado_fase):
        """
        Verifica se o resultado da criação de fase é uma boss fight.
        
        Args:
            resultado_fase: Resultado retornado por criar_fase()
            
        Returns:
            True se for boss fight, False caso contrário
        """
        return (isinstance(resultado_fase, dict) and 
                resultado_fase.get('tipo') == 'boss_fight')
    
    @staticmethod
    def obter_info_boss(resultado_fase):
        """
        Obtém informações sobre o boss fight.
        
        Args:
            resultado_fase: Resultado retornado por criar_fase()
            
        Returns:
            Dicionário com informações do boss ou None
        """
        if NivelFactory.e_boss_fight(resultado_fase):
            return resultado_fase
        return None
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        # Inimigo 2 - Inferior (rápido)
        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_rapido(pos_x2, pos_y2))
        
        return inimigos
    
    @staticmethod
    def criar_fase_3():
        """
        Fase 3: Um inimigo especial roxo com 2 vidas.
        """
        inimigos = []
        
        pos_x = LARGURA - 150
        pos_y = ALTURA_JOGO // 2
        
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
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 200
        pos_y2 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x2, pos_y2))
        
        # Um inimigo especial roxo no meio
        pos_x3 = LARGURA - 100
        pos_y3 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        return inimigos
    
    @staticmethod
    def criar_fase_5():
        """
        Fase 5: Um inimigo elite ciano.
        """
        inimigos = []
        
        pos_x = LARGURA - 150
        pos_y = ALTURA_JOGO // 2
        
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x, pos_y))
        
        return inimigos

    @staticmethod
    def criar_fase_6():
        """
        Fase 6: Um mix de todos os tipos de inimigos.
        """
        inimigos = []
        
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))
        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 = ALTURA_JOGO // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA_JOGO // 5
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        return inimigos

    @staticmethod
    def criar_fase_7():
        """
        Fase 7: dois cianos e um especial.
        """
        inimigos = []
        
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x1, pos_y1))
        
        # Inimigo especial
        pos_x3 = LARGURA - 150
        pos_y3 = ALTURA_JOGO // 1.7
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))
        
        # Inimigo elite
        pos_x4 = LARGURA - 100
        pos_y4 = 4 * ALTURA_JOGO // 5
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
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 200
        pos_y2 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))
        
        pos_x3 = LARGURA - 100
        pos_y3 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x3, pos_y3))
        
        return inimigos
    
    @staticmethod
    def criar_fase_9():
        """
        Fase 9: Preparação para o boss - mix intenso de inimigos.
        """
        inimigos = []
        
        # 2 perseguidores
        pos_x1 = LARGURA - 100
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x1, pos_y1))
        
        pos_x2 = LARGURA - 100
        pos_y2 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))
        
        # 2 elites
        pos_x3 = LARGURA - 200
        pos_y3 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x3, pos_y3))
        
        pos_x4 = LARGURA - 200
        pos_y4 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x4, pos_y4))
        
        # 1 especial no centro
        pos_x5 = LARGURA - 150
        pos_y5 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x5, pos_y5))
        
        return inimigos
    
    @staticmethod
    def criar_fase_10():
        """
        Fase 10: BOSS FIGHT - Boss Fusion.
        Retorna uma flag especial indicando que é uma boss fight.
        """
        # Retornar um dicionário especial para indicar boss fight
        return {
            'tipo': 'boss_fight',
            'boss': 'fusion',
            'cutscene': True,
            'mensagem': 'BOSS FIGHT - PREPARE-SE!'
        }
    
    @staticmethod
    def e_boss_fight(resultado_fase):
        """
        Verifica se o resultado da criação de fase é uma boss fight.
        
        Args:
            resultado_fase: Resultado retornado por criar_fase()
            
        Returns:
            True se for boss fight, False caso contrário
        """
        return (isinstance(resultado_fase, dict) and 
                resultado_fase.get('tipo') == 'boss_fight')
    
    @staticmethod
    def obter_info_boss(resultado_fase):
        """
        Obtém informações sobre o boss fight.
        
        Args:
            resultado_fase: Resultado retornado por criar_fase()
            
        Returns:
            Dicionário com informações do boss ou None
        """
        if NivelFactory.e_boss_fight(resultado_fase):
            return resultado_fase
        return None