#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de preços dinâmicos para as lojas do jogo.
Cada item tem preço base, limite máximo de compras e multiplicador de preço.
"""

import json
import os
import math

class PricingManager:
    """Gerencia preços dinâmicos e limites de compra para todos os itens das lojas."""
    
    def __init__(self):
        self.arquivo_pricing = "data/pricing.json"
        self.dados_pricing = self.carregar_pricing()
    
    def carregar_pricing(self):
        """Carrega os dados de preços ou cria valores padrão."""
        dados_padrao = {
            # WEAPONS SHOP
            "espingarda": {
                "preco_base": 15,
                "compras_realizadas": 0,
                "limite_maximo": 10,  # Máximo 10 compras
                "multiplicador": 1.3,  # Preço aumenta 30% a cada compra
                "quantidade_por_compra": 10
            },
            "metralhadora": {
                "preco_base": 25,
                "compras_realizadas": 0,
                "limite_maximo": 8,   # Máximo 8 compras
                "multiplicador": 1.4, # Preço aumenta 40% a cada compra
                "quantidade_por_compra": 25
            },
            "sabre_luz": {
                "preco_base": 50,
                "compras_realizadas": 0,
                "limite_maximo": 1,   # Máximo 5 compras (arma épica)
                "multiplicador": 1.8, # Preço aumenta 80% a cada compra
                "quantidade_por_compra": 20
            },
            "desert_eagle": {
                "preco_base": 40,
                "compras_realizadas": 0,
                "limite_maximo": 8,   # Máximo 8 compras
                "multiplicador": 1.35, # Preço aumenta 35% a cada compra
                "quantidade_por_compra": 15
            },

            # UPGRADES SHOP
            "vida": {
                "preco_base": 20,
                "compras_realizadas": 0,
                "limite_maximo": 15,  # Máximo 15 compras de vida
                "multiplicador": 1.5, # Preço aumenta 50% a cada compra
                "quantidade_por_compra": 1
            },
            
            # ITEMS SHOP
            "granada": {
                "preco_base": 25,
                "compras_realizadas": 0,
                "limite_maximo": 12,  # Máximo 12 compras
                "multiplicador": 1.2, # Preço aumenta 20% a cada compra
                "quantidade_por_compra": 3
            },
            "ampulheta": {
                "preco_base": 40,
                "compras_realizadas": 0,
                "limite_maximo": 6,   # Máximo 6 compras (item raro)
                "multiplicador": 1.6, # Preço aumenta 60% a cada compra
                "quantidade_por_compra": 2
            },
            "faca": {
                "preco_base": 30,
                "compras_realizadas": 0,
                "limite_maximo": 8,   # Máximo 8 compras
                "multiplicador": 1.35, # Preço aumenta 35% a cada compra
                "quantidade_por_compra": 5
            }
        }
        
        try:
            if os.path.exists(self.arquivo_pricing):
                with open(self.arquivo_pricing, "r") as f:
                    dados_salvos = json.load(f)
                    # Verificar se todos os itens existem, adicionar os que faltam
                    for item_key, item_data in dados_padrao.items():
                        if item_key not in dados_salvos:
                            dados_salvos[item_key] = item_data
                    return dados_salvos
            else:
                self.salvar_pricing(dados_padrao)
                return dados_padrao
        except Exception as e:
            print(f"Erro ao carregar pricing: {e}")
            return dados_padrao
    
    def salvar_pricing(self, dados=None):
        """Salva os dados de pricing no arquivo."""
        try:
            os.makedirs("data", exist_ok=True)
            dados_para_salvar = dados if dados else self.dados_pricing
            with open(self.arquivo_pricing, "w") as f:
                json.dump(dados_para_salvar, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar pricing: {e}")
    
    def calcular_preco_atual(self, item_key):
        """Calcula o preço atual do item baseado nas compras realizadas."""
        if item_key not in self.dados_pricing:
            return 0
        
        item_data = self.dados_pricing[item_key]
        preco_base = item_data["preco_base"]
        compras = item_data["compras_realizadas"]
        multiplicador = item_data["multiplicador"]
        
        # Fórmula: preço_base * (multiplicador ^ compras_realizadas)
        preco_atual = int(preco_base * (multiplicador ** compras))
        return preco_atual
    
    def pode_comprar(self, item_key):
        """Verifica se o item ainda pode ser comprado (não atingiu o limite)."""
        if item_key not in self.dados_pricing:
            return False
        
        item_data = self.dados_pricing[item_key]
        return item_data["compras_realizadas"] < item_data["limite_maximo"]
    
    def realizar_compra(self, item_key):
        """Registra uma compra e atualiza os dados."""
        if not self.pode_comprar(item_key):
            return False
        
        self.dados_pricing[item_key]["compras_realizadas"] += 1
        self.salvar_pricing()
        return True
    
    def obter_info_item(self, item_key):
        """Retorna informações completas sobre um item."""
        if item_key not in self.dados_pricing:
            return None
        
        item_data = self.dados_pricing[item_key]
        return {
            "preco_atual": self.calcular_preco_atual(item_key),
            "compras_realizadas": item_data["compras_realizadas"],
            "limite_maximo": item_data["limite_maximo"],
            "pode_comprar": self.pode_comprar(item_key),
            "quantidade_por_compra": item_data["quantidade_por_compra"],
            "compras_restantes": item_data["limite_maximo"] - item_data["compras_realizadas"]
        }
    
    def obter_proximo_preco(self, item_key):
        """Retorna o preço da próxima compra (se houver)."""
        if not self.pode_comprar(item_key):
            return None
        
        # Simular uma compra para calcular o próximo preço
        item_data = self.dados_pricing[item_key]
        preco_base = item_data["preco_base"]
        proximas_compras = item_data["compras_realizadas"] + 1
        multiplicador = item_data["multiplicador"]
        
        if proximas_compras < item_data["limite_maximo"]:
            return int(preco_base * (multiplicador ** proximas_compras))
        return None
    
    def resetar_item(self, item_key):
        """Reseta as compras de um item específico (para debug/admin)."""
        if item_key in self.dados_pricing:
            self.dados_pricing[item_key]["compras_realizadas"] = 0
            self.salvar_pricing()
    
    def resetar_todos(self):
        """Reseta todas as compras (para debug/admin)."""
        for item_key in self.dados_pricing:
            self.dados_pricing[item_key]["compras_realizadas"] = 0
        self.salvar_pricing()
    
    def obter_estatisticas(self):
        """Retorna estatísticas gerais do sistema de pricing."""
        total_itens = len(self.dados_pricing)
        itens_esgotados = sum(1 for item in self.dados_pricing.values() 
                             if item["compras_realizadas"] >= item["limite_maximo"])
        
        total_compras = sum(item["compras_realizadas"] for item in self.dados_pricing.values())
        
        return {
            "total_itens": total_itens,
            "itens_esgotados": itens_esgotados,
            "itens_disponiveis": total_itens - itens_esgotados,
            "total_compras_realizadas": total_compras
        }


# Função auxiliar para integrar com as lojas existentes
def aplicar_pricing_sistema(lista_itens, pricing_manager):
    """
    Aplica o sistema de pricing a uma lista de itens de loja.
    
    Args:
        lista_itens: Lista de dicionários representando itens da loja
        pricing_manager: Instância do PricingManager
    
    Returns:
        Lista atualizada com preços dinâmicos e informações de limite
    """
    for item in lista_itens:
        item_key = item["key"]
        info_pricing = pricing_manager.obter_info_item(item_key)
        
        if info_pricing:
            # Atualizar preço atual
            item["custo"] = info_pricing["preco_atual"]
            
            # Adicionar informações de limite
            item["pode_comprar"] = info_pricing["pode_comprar"]
            item["compras_realizadas"] = info_pricing["compras_realizadas"]
            item["limite_maximo"] = info_pricing["limite_maximo"]
            item["compras_restantes"] = info_pricing["compras_restantes"]
            
            # Informações para exibição
            if info_pricing["compras_restantes"] > 0:
                proximo_preco = pricing_manager.obter_proximo_preco(item_key)
                if proximo_preco:
                    item["proximo_preco"] = proximo_preco
                else:
                    item["proximo_preco"] = None
            else:
                item["proximo_preco"] = None
                
            # Atualizar descrição para mostrar limite
            item["info_limite"] = f"Purchases: {info_pricing['compras_realizadas']}/{info_pricing['limite_maximo']}"
    
    return lista_itens


# Exemplo de uso:
if __name__ == "__main__":
    # Teste do sistema
    pricing = PricingManager()
    
    print("=== SISTEMA DE PREÇOS DINÂMICOS ===")
    print(f"Estatísticas: {pricing.obter_estatisticas()}")
    
    # Testar alguns itens
    for item in ["espingarda", "granada", "ampulheta", "sabre_luz"]:
        info = pricing.obter_info_item(item)
        print(f"\n{item.upper()}:")
        print(f"  Preço atual: {info['preco_atual']} moedas")
        print(f"  Compras: {info['compras_realizadas']}/{info['limite_maximo']}")
        print(f"  Pode comprar: {'Sim' if info['pode_comprar'] else 'NÃO (ESGOTADO)'}")
        
        proximo = pricing.obter_proximo_preco(item)
        if proximo:
            print(f"  Próximo preço: {proximo} moedas")