#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de moedas para o jogo.
"""

import random
import json
import os
import pygame
import math
from src.config import LARGURA, ALTURA
from src.entities.moeda import Moeda


class MoedaManager:
    """
    Classe para gerenciar a geração, coleta e persistência de moedas.
    """
    def __init__(self):
        self.moedas_na_tela = []
        self.quantidade_moedas = self.carregar_moedas()  # Alterado para método sem underline
        self.ultimo_spawn = pygame.time.get_ticks()
        self.intervalo_spawn = random.randint(3000, 8000)  # Entre 3 e 8 segundos
        self.som_coleta = self.criar_som_coleta()  # Alterado para método sem underline
    
    def criar_som_coleta(self):  # Alterado para método sem underline
        """Cria um som para a coleta de moedas."""
        tamanho_amostra = 8000
        # Criar som de "ping" para coleta de moeda
        som = pygame.mixer.Sound(bytes(bytearray(
            int(127 + 127 * (math.sin(i / 20) if i < 1000 else 0)) 
            for i in range(tamanho_amostra)
        )))
        som.set_volume(0.2)
        return som
    
    def carregar_moedas(self):  # Alterado para método sem underline
        """
        Carrega a quantidade de moedas salva no arquivo.
        Se o arquivo não existir, inicia com 0 moedas.
        """
        try:
            # Criar o diretório de dados se não existir
            if not os.path.exists("data"):
                os.makedirs("data")
            
            # Tentar carregar o arquivo de moedas
            if os.path.exists("data/moedas.json"):
                with open("data/moedas.json", "r") as f:
                    data = json.load(f)
                    return data.get("moedas", 0)
            return 0
        except Exception as e:
            print(f"Erro ao carregar moedas: {e}")
            return 0
    
    def salvar_moedas(self):  # Alterado para método sem underline
        """Salva a quantidade atual de moedas no arquivo."""
        try:
            # Criar o diretório de dados se não existir
            if not os.path.exists("data"):
                os.makedirs("data")
            
            # Salvar as moedas no arquivo
            with open("data/moedas.json", "w") as f:
                json.dump({"moedas": self.quantidade_moedas}, f)
        except Exception as e:
            print(f"Erro ao salvar moedas: {e}")
    
    def atualizar(self, jogador):
        """
        Atualiza o estado das moedas, gera novas e verifica colisões.
        
        Args:
            jogador: O objeto do jogador para verificar colisões
            
        Returns:
            bool: True se uma moeda foi coletada neste frame
        """
        moeda_coletada = False
        tempo_atual = pygame.time.get_ticks()
        
        # Verificar se é hora de gerar uma nova moeda
        if tempo_atual - self.ultimo_spawn > self.intervalo_spawn:
            self.gerar_moeda()  # Alterado para método sem underline
            self.ultimo_spawn = tempo_atual
            self.intervalo_spawn = random.randint(2000, 3000)  # Novo intervalo aleatório
        
        # Atualizar moedas existentes
        for moeda in self.moedas_na_tela[:]:
            # Verificar colisão com o jogador
            if moeda.colidiu(jogador.rect):
                self.quantidade_moedas += 1
                self.moedas_na_tela.remove(moeda)
                pygame.mixer.Channel(3).play(self.som_coleta)
                self.salvar_moedas()  # Alterado para método sem underline
                moeda_coletada = True
                continue
            
            # Atualizar estado da moeda
            if not moeda.atualizar():
                # A moeda expirou
                self.moedas_na_tela.remove(moeda)
            else:
                # Atualizar o retângulo de colisão
                moeda.atualizar_rect()
        
        return moeda_coletada
    
    def gerar_moeda(self):  # Alterado para método sem underline
        """Gera uma nova moeda em uma posição aleatória na tela."""
        # Definir uma margem para não gerar moedas muito próximas às bordas
        margem = 50
        
        # Gerar posição aleatória
        x = random.randint(margem, LARGURA - margem)
        y = random.randint(margem, ALTURA - margem)
        
        # Criar a moeda
        moeda = Moeda(x, y)
        self.moedas_na_tela.append(moeda)
    
    def desenhar(self, tela):
        """Desenha todas as moedas na tela."""
        for moeda in self.moedas_na_tela:
            moeda.desenhar(tela)
    
    def obter_quantidade(self):
        """Retorna a quantidade atual de moedas."""
        return self.quantidade_moedas