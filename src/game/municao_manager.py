#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador centralizado de munições do jogador.
Salva e carrega munições permanentes (não recarregam entre fases).
"""

import os
import json


def salvar_todas_municoes(jogador):
    """
    Salva todas as munições atuais do jogador no arquivo upgrades.json.

    Args:
        jogador: Objeto do jogador com as munições
    """
    try:
        # Carregar upgrades existentes
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)

        # Atualizar todas as munições com os valores atuais
        if hasattr(jogador, 'tiros_espingarda'):
            upgrades["espingarda"] = max(0, jogador.tiros_espingarda)

        if hasattr(jogador, 'tiros_metralhadora'):
            upgrades["metralhadora"] = max(0, jogador.tiros_metralhadora)

        if hasattr(jogador, 'tiros_desert_eagle'):
            upgrades["desert_eagle"] = max(0, jogador.tiros_desert_eagle)

        if hasattr(jogador, 'granadas'):
            upgrades["granada"] = max(0, jogador.granadas)

        if hasattr(jogador, 'sabre_uses'):
            upgrades["sabre_luz"] = max(0, jogador.sabre_uses)

        if hasattr(jogador, 'facas'):
            upgrades["faca"] = max(0, jogador.facas)

        if hasattr(jogador, 'ampulheta_uses'):
            upgrades["ampulheta"] = max(0, jogador.ampulheta_uses)

        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)

        # Salvar
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)

        print(f"✅ Munições salvas: Shotgun={upgrades.get('espingarda', 0)}, "
              f"MachineGun={upgrades.get('metralhadora', 0)}, "
              f"DesertEagle={upgrades.get('desert_eagle', 0)}, "
              f"Grenades={upgrades.get('granada', 0)}, "
              f"Chucky={upgrades.get('faca', 0)}")

    except Exception as e:
        print(f"❌ Erro ao salvar munições: {e}")


def salvar_municao_individual(tipo_municao, quantidade):
    """
    Salva a quantidade de um tipo específico de munição.

    Args:
        tipo_municao: String identificando o tipo (ex: "espingarda", "metralhadora")
        quantidade: Quantidade atual
    """
    try:
        upgrades = {}
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)

        upgrades[tipo_municao] = max(0, quantidade)

        os.makedirs("data", exist_ok=True)
        with open("data/upgrades.json", "w") as f:
            json.dump(upgrades, f, indent=4)

    except Exception as e:
        print(f"Erro ao salvar munição {tipo_municao}: {e}")
