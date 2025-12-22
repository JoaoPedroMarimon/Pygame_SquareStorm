#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar upgrades do jogador.
Contém funções para carregar, salvar e gerenciar os upgrades.
"""

import os
import json
from src.config import *

# Lista de upgrades disponíveis com seus preços e descrições
UPGRADES_DISPONIVEIS = {
    "vida": {
        "nome": "Vida Extra",
        "descricao": "Aumenta seu máximo de vida em +1",
        "preco_base": 50,        # Preço inicial
        "incremento_preco": 50,  # Quanto aumenta por nível
        "max_nivel": 5,          # Nível máximo
        "efeito_por_nivel": 1    # Quantas vidas são adicionadas por nível
    },
    "espingarda": {
        "nome": "Espingarda",
        "descricao": "Arma poderosa que dispara múltiplos projéteis em cone",
        "preco_base": 80,
        "incremento_preco": 40,
        "max_nivel": 10,
        "efeito_por_nivel": 3    # Quantos tiros são adicionados por nível
    },
    "granada": {
        "nome": "Granada",
        "descricao": "Explosivo que causa dano em área",
        "preco_base": 60,
        "incremento_preco": 30,
        "max_nivel": 10,
        "efeito_por_nivel": 2    # Quantas granadas são adicionadas por nível
    },
    "dash": {
        "nome": "Dash",
        "descricao": "Dá um dash rápido para frente ao pressionar ESPAÇO",
        "preco_base": 70,
        "incremento_preco": 35,
        "max_nivel": 10,
        "efeito_por_nivel": 1    # Quantos dashes são adicionados por nível
    }
}

def carregar_todos_upgrades():
    """
    Carrega todos os upgrades disponíveis do arquivo.
    
    Returns:
        dict: Dicionário com todos os upgrades e seus valores
    """
    try:
        # Verificar se o arquivo existe
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                return json.load(f)
        
        # Se não existir, retorna valores padrão
        return {
            "vida": 1,       # Upgrade de vida (padrão: 1)
            "espingarda": 0, # Upgrade de espingarda (padrão: 0 tiros)
            "granada": 0,    # Upgrade de granada (padrão: 0 granadas)
            "dash": 0        # Upgrade de dash (padrão: 0 dashes)
        }
    except Exception as e:
        print(f"Erro ao carregar upgrades: {e}")
        return {
            "vida": 1,
            "espingarda": 0,
            "granada": 0,
            "dash": 0
        }

def salvar_upgrades(upgrades):
    """
    Salva os upgrades no arquivo.
    
    Args:
        upgrades: Dicionário com os upgrades a serem salvos
    """
    try:
        # Criar o diretório de dados se não existir
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Salvar os upgrades no arquivo
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f)
    except Exception as e:
        print(f"Erro ao salvar upgrades: {e}")

def calcular_preco_upgrade(tipo_upgrade, nivel_atual):
    """
    Calcula o preço de um upgrade com base no nível atual.
    
    Args:
        tipo_upgrade: Tipo de upgrade ("vida", "espingarda" ou "granada")
        nivel_atual: Nível atual do upgrade
        
    Returns:
        int: Preço do próximo nível do upgrade
    """
    if tipo_upgrade not in UPGRADES_DISPONIVEIS:
        return 9999  # Valor alto para upgrades desconhecidos
    
    info = UPGRADES_DISPONIVEIS[tipo_upgrade]
    return info["preco_base"] + (nivel_atual * info["incremento_preco"])

def comprar_upgrade(tipo_upgrade, quantidade=1):
    """
    Compra um upgrade e atualiza o arquivo.
    
    Args:
        tipo_upgrade: Tipo de upgrade a ser comprado ("vida", "espingarda" ou "granada")
        quantidade: Quantidade a ser adicionada
        
    Returns:
        tuple: (sucesso, custo, msg)
            - sucesso: True se a compra foi bem-sucedida, False caso contrário
            - custo: Custo em moedas da compra (0 se falhou)
            - msg: Mensagem explicando o resultado
    """
    try:
        # Verificar se o tipo de upgrade existe
        if tipo_upgrade not in UPGRADES_DISPONIVEIS:
            return False, 0, f"Upgrade '{tipo_upgrade}' não existe"
        
        # Carregar upgrades e moedas
        upgrades = carregar_todos_upgrades()
        nivel_atual = upgrades.get(tipo_upgrade, 0)
        
        # Verificar se já atingiu o nível máximo
        info = UPGRADES_DISPONIVEIS[tipo_upgrade]
        if nivel_atual >= info["max_nivel"]:
            return False, 0, f"Já atingiu o nível máximo de {info['nome']}"
        
        # Calcular o custo
        custo = calcular_preco_upgrade(tipo_upgrade, nivel_atual)
        
        # Verificar se o jogador tem moedas suficientes
        moedas = carregar_moedas()
        if moedas < custo:
            return False, custo, f"Moedas insuficientes. Necessário: {custo}, Disponível: {moedas}"
        
        # Atualizar o upgrade
        novo_valor = nivel_atual + quantidade
        upgrades[tipo_upgrade] = novo_valor
            
        # Descontar as moedas
        salvar_moedas(moedas - custo)
        
        # Salvar os upgrades
        salvar_upgrades(upgrades)
        
        # Calcular o efeito real (ex: +3 tiros, +1 vida)
        efeito_real = quantidade * info["efeito_por_nivel"]
        
        return True, custo, f"{info['nome']} adquirido! +{efeito_real} {tipo_upgrade}"
    except Exception as e:
        print(f"Erro ao comprar upgrade: {e}")
        return False, 0, f"Erro ao comprar upgrade: {e}"

def carregar_moedas():
    """
    Carrega a quantidade de moedas do arquivo.
    
    Returns:
        int: Quantidade de moedas
    """
    try:
        if os.path.exists("data/moedas.json"):
            with open("data/moedas.json", "r") as f:
                data = json.load(f)
                return data.get("moedas", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar moedas: {e}")
        return 0

def salvar_moedas(quantidade):
    """
    Salva a quantidade de moedas no arquivo.
    
    Args:
        quantidade: Quantidade de moedas a ser salva
    """
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
        
        with open("data/moedas.json", "w") as f:
            json.dump({"moedas": quantidade}, f)
    except Exception as e:
        print(f"Erro ao salvar moedas: {e}")

def obter_info_upgrade(tipo_upgrade):
    """
    Obtém informações sobre um upgrade específico.
    
    Args:
        tipo_upgrade: Tipo de upgrade ("vida", "espingarda" ou "granada")
        
    Returns:
        dict: Informações sobre o upgrade ou None se não existir
    """
    return UPGRADES_DISPONIVEIS.get(tipo_upgrade)

def obter_nivel_atual(tipo_upgrade):
    """
    Obtém o nível atual de um upgrade específico.
    
    Args:
        tipo_upgrade: Tipo de upgrade ("vida", "espingarda" ou "granada")
        
    Returns:
        int: Nível atual do upgrade
    """
    upgrades = carregar_todos_upgrades()
    return upgrades.get(tipo_upgrade, 0)