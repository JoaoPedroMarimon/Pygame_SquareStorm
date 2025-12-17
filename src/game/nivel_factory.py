#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criar inimigos e configurar fases.
Factory pattern para facilitar a criação de diferentes níveis/fases.
CORRIGIDO: Incluindo a Fase 10 - Boss Fight com Boss Fusion.

NOVO: Agora suporta definição da posição inicial do jogador por fase.
Cada fase retorna um dicionário com 'inimigos' e 'pos_jogador'.

Exemplo de uso:
    resultado = NivelFactory.criar_fase(1)
    inimigos = resultado['inimigos']
    pos_jogador = resultado['pos_jogador']  # (x, y)

Posições customizadas podem ser usadas para:
    - Posicionar jogador no centro: (LARGURA // 2, ALTURA_JOGO // 2)
    - Posicionar na parte inferior: (100, ALTURA_JOGO - 100)
    - Posicionar na parte superior: (100, 100)
"""

import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.inimigo_factory import InimigoFactory
import math

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
            Dicionário com 'inimigos' e 'pos_jogador' (tuple x, y), ou objeto especial para boss fight
        """
        print(f"🎯 Criando fase {numero_fase}...")

        # Verificar se existe método específico para a fase
        metodo_fase = getattr(NivelFactory, f"criar_fase_{numero_fase}", None)

        if metodo_fase:
            print(f"✅ Método específico encontrado: criar_fase_{numero_fase}")
            return metodo_fase()
        else:
            print(f"⚠️ Método criar_fase_{numero_fase} não encontrado, criando fase genérica")

    
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

        # Posição inicial do jogador (esquerda, centralizado)
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_2():
        """
        Fase 2: Dois inimigos, um superior e um inferior.
        """
        inimigos = []

        # Inimigo 1 - Superior (básico)
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_basico(pos_x1, pos_y1))

        # Inimigo 2 - Inferior (rápido)
        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_rapido(pos_x2, pos_y2))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
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

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
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

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_5():
        """
        Fase 5: Um inimigo elite ciano.
        """
        inimigos = []

        pos_x = LARGURA - 150
        pos_y = ALTURA_JOGO // 2

        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x, pos_y))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }

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

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }

    @staticmethod
    def criar_fase_7():
        """
        Fase 7: Dois elites cianos e um especial.
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

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_8():
        """
        Fase 8: Inimigos perseguidores - introdução de nova mecânica.
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

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_9():
        """
        Fase 9: Mix de tipos - rápido, perseguidor e especial.
        """
        inimigos = []

        # Adicionar 3 inimigos em posições diferentes
        pos_x1 = LARGURA - 100
        pos_y1 = ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_rapido(pos_x1, pos_y1))

        pos_x2 = LARGURA - 200
        pos_y2 = ALTURA_JOGO // 2
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))

        pos_x3 = LARGURA - 100
        pos_y3 = 3 * ALTURA_JOGO // 4
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x3, pos_y3))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }


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
            'mensagem': 'BOSS FIGHT - BOSS FUSION DESPERTA!',
            'pos_jogador': (100, ALTURA_JOGO // 2)
        }

    @staticmethod
    def criar_fase_11():
        """
        Fase 11: Inimigos com metralhadora - nova mecânica de combate.
        2 inimigos que usam metralhadora com sistema de recarga.
        """
        inimigos = []

        # Inimigo metralhadora 1 - parte superior
        pos_x1 = 80
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x1, pos_y1))

        # Inimigo metralhadora 2 - parte inferior
        pos_x2 = LARGURA - 150
        pos_y2 = 1.5 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x2, pos_y2))

        # Posição inicial do jogador
        pos_jogador = (700, 1.2*ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    

    @staticmethod
    def criar_fase_12():

        inimigos = []

        # Inimigo metralhadora 1 - parte superior
        pos_x1 = LARGURA - 500
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x1, pos_y1))

        # Inimigo metralhadora 2 - parte inferior
        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_perseguidor(pos_x2, pos_y2))

        pos_x3 = LARGURA - 500
        pos_y3 = 2.5*ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x3, pos_y3))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_13():

        inimigos = []

        # Inimigo metralhadora 1 - parte superior
        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x1, pos_y1))


        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_14():

        inimigos = []

        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x1, pos_y1))

        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x2, pos_y2))

        pos_x3 = LARGURA - 150
        pos_y3 = 2.5*ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_elite(pos_x3, pos_y3))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    
    @staticmethod
    def criar_fase_15():

        inimigos = []

        pos_x1 = LARGURA - 150
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x1, pos_y1))

        pos_x2 = LARGURA - 150
        pos_y2 = 2 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x2, pos_y2))

        pos_x3 = LARGURA - 150
        pos_y3 = 2.5*ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x3, pos_y3))

        # Posição inicial do jogador
        pos_jogador = (100, ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    

    @staticmethod
    def criar_fase_16():

        inimigos = []

        pos_x1 = 80
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x1, pos_y1))

        # Inimigo metralhadora 2 - parte inferior
        pos_x2 = LARGURA - 150
        pos_y2 = 1.5 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_especial(pos_x2, pos_y2))

        pos_x3 = 700
        pos_y3 = 2.6*ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x3, pos_y3))

        pos_x4 = 700
        pos_y4 = 0.4*ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_metralhadora(pos_x4, pos_y4))

        # Posição inicial do jogador
        pos_jogador = (700, 1*ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
        }
    @staticmethod
    def criar_fase_17():
        """
        Fase 11: Inimigos com metralhadora - nova mecânica de combate.
        2 inimigos que usam metralhadora com sistema de recarga.
        """
        inimigos = []

        # Inimigo metralhadora 1 - parte superior
        pos_x1 = 80
        pos_y1 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x1, pos_y1))

        # Inimigo metralhadora 2 - parte inferior
        pos_x2 = 700
        pos_y2 = 0.6 * ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x2, pos_y2))

        pos_x3 = LARGURA - 150
        pos_y3 = ALTURA_JOGO // 3
        inimigos.append(InimigoFactory.criar_inimigo_mago(pos_x3, pos_y3))

        # Posição inicial do jogador
        pos_jogador = (700, 1.2*ALTURA_JOGO // 2)

        return {
            'inimigos': inimigos,
            'pos_jogador': pos_jogador
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