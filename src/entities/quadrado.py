#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo da classe Quadrado, que representa tanto o jogador quanto os inimigos.
"""

import pygame
import math
import random
from src.config import *
from src.entities.tiro import Tiro
from src.utils.sound import gerar_som_tiro
import os
import json
from src.items.granada import carregar_upgrade_granada,desenhar_granada_selecionada
from src.weapons.espingarda import carregar_upgrade_espingarda,desenhar_espingarda
from src.weapons.metralhadora import carregar_upgrade_metralhadora, desenhar_metralhadora
from src.utils.display_manager import convert_mouse_position
from src.weapons.sabre_luz import carregar_upgrade_sabre, desenhar_sabre

class Quadrado:
    """
    Classe para os quadrados (jogador e inimigo).
    Contém toda a lógica de movimento, tiros e colisões.
    """
    def __init__(self, x, y, tamanho, cor, velocidade):
        self.x = x
        self.y = y
        self.tamanho = tamanho
        self.cor = cor
        self.cor_escura = self._gerar_cor_escura(cor)
        self.cor_brilhante = self._gerar_cor_brilhante(cor)
        self.velocidade = velocidade
        
        # Verificar se é o jogador e inicializar sistemas
        if cor == AZUL:  # Se for o jogador
            vidas_upgrade = self._carregar_upgrade_vida()
            self.vidas = vidas_upgrade
            self.vidas_max = vidas_upgrade
            self.facas = self._carregar_upgrade_faca()
            self.amuleto_ativo = False  # Estado do amuleto (inativo por padrão)
            
            # SISTEMA DA AMPULHETA - ATUALIZADO
            self.ampulheta_uses = self._carregar_upgrade_ampulheta()
            self.ampulheta_selecionada = False  # Toggle visual (segurar na mão)
            self.tempo_desacelerado = False
            self.duracao_desaceleracao = 0
            self.fator_desaceleracao = 0.2  # 20% da velocidade normal
            self.duracao_ampulheta = 300  # 5 segundos a 60 FPS
            
            # SISTEMA DE ITENS (sempre inativos no início)
            self.granadas = carregar_upgrade_granada()
            self.granada_selecionada = False  # Jogador usa Q para ativar
            
            # SISTEMA DE ARMAS (sempre inativas no início)
            self.espingarda_ativa = False
            self.metralhadora_ativa = False
            self.desert_eagle_ativa = False
            self.tiros_espingarda = carregar_upgrade_espingarda()
            self.tiros_metralhadora = carregar_upgrade_metralhadora()
            from src.weapons.desert_eagle import carregar_upgrade_desert_eagle
            self.tiros_desert_eagle = carregar_upgrade_desert_eagle()
            
        else:  # Se for inimigo
            self.vidas = 1  # Padrão: 1 vida para inimigos normais
            self.vidas_max = 1
            
            # Inimigos não têm armas especiais nem ampulheta
            self.granada_selecionada = False
            self.espingarda_ativa = False
            self.metralhadora_ativa = False
            self.desert_eagle_ativa = False
            self.granadas = 0
            self.tiros_espingarda = 0
            self.tiros_metralhadora = 0
            self.tiros_desert_eagle = 0
            self.ampulheta_uses = 0
            self.ampulheta_selecionada = False
            self.tempo_desacelerado = False
            self.duracao_desaceleracao = 0
            self.fator_desaceleracao = 1.0
            self.facas = 0
            self.amuleto_ativo = False
            
        self.sabre_equipado = False
        self.sabre_uses = self._carregar_upgrade_sabre()
        self.sabre_info = {
            'ativo': False,
            'animacao_ativacao': 0,
            'modo_defesa': False,
            'pos_cabo': (0, 0),
            'pos_ponta': (0, 0),
            'angulo': 0,
            'comprimento_atual': 0,
            'tempo_ultimo_hum': 0
        }
        
        self.rect = pygame.Rect(x, y, tamanho, tamanho)
        self.tempo_ultimo_tiro = 0
        
        # Cooldown variável para inimigos
        if cor == AZUL:  # Azul = jogador
            self.tempo_cooldown = COOLDOWN_TIRO_JOGADOR
        else:
            # Para inimigos, o cooldown é baseado no quão "vermelho" é o inimigo
            vermelhidao = cor[0] / 255.0
            self.tempo_cooldown = COOLDOWN_TIRO_INIMIGO + int(vermelhidao * 200)  # 400-600ms
        
        self.invulneravel = False
        self.tempo_invulneravel = 0
        self.duracao_invulneravel = DURACAO_INVULNERAVEL
        
        # Trilha de movimento
        self.posicoes_anteriores = []
        self.max_posicoes = 15
        
        # Estética adicional
        self.angulo = 0
        self.pulsando = 0
        self.tempo_pulsacao = 0
        
        # Efeito de dano
        self.efeito_dano = 0
        
        # Identificador (útil para fases)
        self.id = id(self)
        
        # OPCIONAL: Log de debug (remover em produção)
        if cor == AZUL:
            print(f"🎮 Jogador iniciado - Granada: {self.granadas}, Ampulheta: {self.ampulheta_uses}, Espingarda: {self.tiros_espingarda}, Metralhadora: {self.tiros_metralhadora}")
            print("💡 Use Q para alternar itens, E para alternar armas")
                
    def _carregar_upgrade_vida(self):
        """
        Carrega o upgrade de vida do arquivo de upgrades.
        Retorna 1 se não houver upgrade.
        """
        try:
            # Verificar se o arquivo existe
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("vida", 1)
            return 1
        except Exception as e:
            print(f"Erro ao carregar upgrade de vida: {e}")
            return 1
        
    def _carregar_upgrade_faca(self):
        """
        Carrega o upgrade da faca do arquivo de upgrades.
        Retorna 0 se não houver upgrade.
        """
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("faca", 0)
            return 0
        except Exception as e:
            print(f"Erro ao carregar upgrade de faca: {e}")
            return 0

    def _carregar_upgrade_ampulheta(self):
        """
        Carrega o upgrade da ampulheta do arquivo de upgrades.
        Retorna 0 se não houver upgrade.
        """
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("ampulheta", 0)
            return 0
        except Exception as e:
            print(f"Erro ao carregar upgrade de ampulheta: {e}")
            return 0

    def usar_ampulheta(self):
        """
        Ativa a desaceleração do tempo se possível.
        Retorna True se foi ativada com sucesso, False caso contrário.
        """
        if self.ampulheta_uses > 0 and not self.tempo_desacelerado:
            self.ampulheta_uses -= 1
            self.tempo_desacelerado = True
            self.duracao_desaceleracao = self.duracao_ampulheta
            
            # Desativar modo visual após usar
            if self.ampulheta_uses <= 0:
                self.ampulheta_selecionada = False
            
            return True
        return False

    def atualizar_ampulheta(self):
        """
        Atualiza o estado da ampulheta.
        Deve ser chamado a cada frame.
        """
        if self.tempo_desacelerado:
            self.duracao_desaceleracao -= 1
            if self.duracao_desaceleracao <= 0:
                self.tempo_desacelerado = False
                self.duracao_desaceleracao = 0

    def obter_fator_tempo(self):
        """
        Retorna o fator de tempo atual.
        1.0 = tempo normal, 0.2 = tempo desacelerado
        """
        return self.fator_desaceleracao if self.tempo_desacelerado else 1.0

    def tem_ampulheta_ativa(self):
        """
        Retorna True se a ampulheta está atualmente ativa (desacelerando o tempo).
        """
        return self.tempo_desacelerado

    def verificar_auto_equipar_itens(self):
        """
        Verifica e auto-equipa o item selecionado no inventário.
        """
        from src.game.inventario import InventarioManager
        
        inventario_manager = InventarioManager()
        item_selecionado = inventario_manager.obter_item_selecionado()
        
        # Auto-equipar granada se selecionada e disponível
        if item_selecionado == "granada" and self.granadas > 0:
            self.granada_selecionada = True  # Auto-ativa a granada
            return f"Granada equipada! ({self.granadas} disponíveis) - Pressione Q para usar"
        
        # Ampulheta não precisa de auto-equip, mas informar que está disponível
        elif item_selecionado == "ampulheta" and hasattr(self, 'ampulheta_uses') and self.ampulheta_uses > 0:
            return f"Ampulheta disponível! ({self.ampulheta_uses} usos) - Pressione Q para segurar + clique para ativar"
        
        return None
        
    
    def _gerar_cor_escura(self, cor):
        """Gera uma versão mais escura da cor."""
        return tuple(max(0, c - 50) for c in cor)
    
    def _gerar_cor_brilhante(self, cor):
        """Gera uma versão mais brilhante da cor."""
        return tuple(min(255, c + 70) for c in cor)

    def desenhar(self, tela, tempo_atual=None):
        """
        Desenha o quadrado na tela com seus efeitos visuais.
        
        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual em ms para efeitos de animação (opcional)
        """
        # Se tempo_atual não foi fornecido, obtenha-o
        if tempo_atual is None:
            tempo_atual = pygame.time.get_ticks()
            
        # Desenhar trilha de movimento para o inimigo (qualquer coisa diferente de AZUL)
        if self.cor != AZUL:
            for i, (pos_x, pos_y) in enumerate(self.posicoes_anteriores):
                alpha = int(255 * (1 - i / len(self.posicoes_anteriores)))
                # Garantir que os valores RGB estejam no intervalo válido (0-255)
                cor_trilha = (max(0, min(255, self.cor[0] - 100)), 
                            max(0, min(255, self.cor[1] - 100)), 
                            max(0, min(255, self.cor[2] - 100)))
                tamanho = int(self.tamanho * (1 - i / len(self.posicoes_anteriores) * 0.7))
                pygame.draw.rect(tela, cor_trilha, 
                                (pos_x + (self.tamanho - tamanho) // 2, 
                                pos_y + (self.tamanho - tamanho) // 2, 
                                tamanho, tamanho))
        
        # Se estiver invulnerável, pisca o quadrado
        if self.invulneravel and tempo_atual % 200 < 100:
            return
        
        # Efeito de pulsação
        if tempo_atual - self.tempo_pulsacao > 100:
            self.tempo_pulsacao = tempo_atual
            self.pulsando = (self.pulsando + 1) % 12
            
        mod_tamanho = 0
        if self.pulsando < 6:
            mod_tamanho = self.pulsando
        else:
            mod_tamanho = 12 - self.pulsando
            
        if hasattr(self, 'perseguidor') and self.perseguidor:
            # Desenhar um efeito de "chamas" perseguindo
            # Desenhar efeito de rastro de "fogo"
            for i in range(8):
                # Variação no tamanho e posição
                offset_x = random.uniform(-self.tamanho / 3, self.tamanho / 3)
                offset_y = random.uniform(-self.tamanho / 3, self.tamanho / 3)
                
                # Cores variando de laranja a amarelo
                cor_r = min(255, self.cor[0] + random.randint(-40, 40))
                cor_g = min(255, self.cor[1] + random.randint(-40, 20))
                cor_b = 0  # Sem componente azul para manter o visual de fogo
                
                tamanho_particula = random.randint(3, 8)
                
                # Desenhar partícula de fogo
                pygame.draw.circle(tela, (cor_r, cor_g, cor_b), 
                                (int(self.x - offset_x + random.uniform(0, self.tamanho)), 
                                int(self.y - offset_y + random.uniform(0, self.tamanho))), 
                                tamanho_particula)

        # Desenhar sombra
        pygame.draw.rect(tela, (20, 20, 20), 
                        (self.x + 4, self.y + 4, 
                        self.tamanho, self.tamanho), 0, 3)
        
        # Desenhar o quadrado com bordas arredondadas
        cor_uso = self.cor
        if self.efeito_dano > 0:
            cor_uso = BRANCO
            self.efeito_dano -= 1
        
        # Quadrado interior
        pygame.draw.rect(tela, self.cor_escura, 
                        (self.x, self.y, 
                        self.tamanho + mod_tamanho, self.tamanho + mod_tamanho), 0, 5)
        
        # Quadrado exterior (menor)
        pygame.draw.rect(tela, cor_uso, 
                        (self.x + 3, self.y + 3, 
                        self.tamanho + mod_tamanho - 6, self.tamanho + mod_tamanho - 6), 0, 3)
        
        # Brilho no canto superior esquerdo
        pygame.draw.rect(tela, self.cor_brilhante, 
                        (self.x + 5, self.y + 5, 
                        8, 8), 0, 2)
        
        # Desenhar indicador de vidas (barra de vida)
        vida_largura = 50
        altura_barra = 6
        
        # Fundo escuro
        pygame.draw.rect(tela, (40, 40, 40), 
                        (self.x, self.y - 15, vida_largura, altura_barra), 0, 2)
        
        # Vida atual
        vida_atual = int((self.vidas / self.vidas_max) * vida_largura)
        if vida_atual > 0:
            pygame.draw.rect(tela, self.cor, 
                            (self.x, self.y - 15, vida_atual, altura_barra), 0, 2)
        
        # DELEGAÇÃO: Desenhar item/arma atualmente ativa
        if self.cor == AZUL:  # Se for o jogador
            pos_mouse = convert_mouse_position(pygame.mouse.get_pos())
            
            # Desenhar apenas a arma/item atualmente ativo
            if hasattr(self, 'espingarda_ativa') and self.espingarda_ativa and self.tiros_espingarda > 0:
                desenhar_espingarda(tela, self, tempo_atual, pos_mouse)
            elif hasattr(self, 'metralhadora_ativa') and self.metralhadora_ativa and self.tiros_metralhadora > 0:
                desenhar_metralhadora(tela, self, tempo_atual, pos_mouse)
            elif hasattr(self, 'desert_eagle_ativa') and self.desert_eagle_ativa and self.tiros_desert_eagle > 0:
                from src.weapons.desert_eagle import desenhar_desert_eagle
                desenhar_desert_eagle(tela, self, pos_mouse)
            elif hasattr(self, 'granada_selecionada') and self.granada_selecionada and self.granadas > 0:
                desenhar_granada_selecionada(tela, self, tempo_atual)
            elif hasattr(self, 'ampulheta_selecionada') and self.ampulheta_selecionada and self.ampulheta_uses > 0:
                from src.items.ampulheta import desenhar_ampulheta_selecionada
                desenhar_ampulheta_selecionada(tela, self, tempo_atual)
            elif hasattr(self, 'amuleto_ativo') and self.amuleto_ativo and hasattr(self, 'facas') and self.facas > 0:
                from src.items.amuleto import desenhar_amuleto_segurado
                desenhar_amuleto_segurado(tela, self, tempo_atual)
            elif hasattr(self, 'sabre_equipado') and self.sabre_equipado and self.sabre_uses > 0:
                from src.weapons.sabre_luz import desenhar_sabre
                desenhar_sabre(tela, self, tempo_atual, pos_mouse)


    def mover(self, dx, dy):
        """Move o quadrado na direção especificada, com lógica melhorada para evitar tremores."""
        # Salvar posição atual para a trilha (apenas inimigos)
        if self.cor != AZUL:
            self.posicoes_anteriores.insert(0, (self.x, self.y))
            if len(self.posicoes_anteriores) > self.max_posicoes:
                self.posicoes_anteriores.pop()
        
        # Calcular nova posição
        novo_x = self.x + dx * self.velocidade
        novo_y = self.y + dy * self.velocidade
        
        # Flag para indicar comportamento de fuga da borda
        em_fuga_da_borda = False
        
        # Verificar comportamento de inimigos perto das bordas
        if self.cor != AZUL:  # Somente para inimigos
            # Margens para detecção de proximidade com bordas
            margem_seguranca = 50
            margem_critica = 20
            
            # Verificar se está em zona crítica (muito perto da borda)
            em_zona_critica = (novo_x < margem_critica or 
                            novo_x > LARGURA - self.tamanho - margem_critica or
                            novo_y < margem_critica or 
                            novo_y > ALTURA - self.tamanho - margem_critica)
            
            # Verificar se está em zona de segurança (perto da borda, mas não crítico)
            em_zona_seguranca = (novo_x < margem_seguranca or 
                            novo_x > LARGURA - self.tamanho - margem_seguranca or
                            novo_y < margem_seguranca or 
                            novo_y > ALTURA - self.tamanho - margem_seguranca)
            
            if em_zona_critica:
                # Se está muito perto da borda, aplicar um impulso forte para o centro
                em_fuga_da_borda = True
                
                # Determinar direção para o centro
                centro_x = LARGURA / 2
                centro_y = ALTURA / 2
                
                # Calcular vetor para o centro
                vetor_x = centro_x - self.x
                vetor_y = centro_y - self.y
                
                # Normalizar vetor
                distancia = math.sqrt(vetor_x**2 + vetor_y**2)
                if distancia > 0:
                    vetor_x /= distancia
                    vetor_y /= distancia
                
                # Aplicar movimento em direção ao centro com impulso forte
                impulso = 1.5  # Mais forte para escapar rapidamente
                novo_x = self.x + vetor_x * self.velocidade * impulso
                novo_y = self.y + vetor_y * self.velocidade * impulso
                
            elif em_zona_seguranca:
                # Se está na zona de segurança mas não crítica, suavizar movimento
                # Combinamos o movimento original com um vetor para o centro
                centro_x = LARGURA / 2
                centro_y = ALTURA / 2
                
                # Calcular vetor para o centro
                vetor_x = centro_x - self.x
                vetor_y = centro_y - self.y
                
                # Normalizar vetor
                distancia = math.sqrt(vetor_x**2 + vetor_y**2)
                if distancia > 0:
                    vetor_x /= distancia
                    vetor_y /= distancia
                
                # Misturar o movimento original com movimento para o centro
                fator_mistura = 0.6  # 60% direção centro, 40% movimento original
                novo_x = self.x + ((vetor_x * fator_mistura) + (dx * (1 - fator_mistura))) * self.velocidade
                novo_y = self.y + ((vetor_y * fator_mistura) + (dy * (1 - fator_mistura))) * self.velocidade
        
        # Verificar limites da tela e ajustar posição
        if 0 <= novo_x <= LARGURA - self.tamanho:
            self.x = novo_x
        else:
            # Se for inimigo em fuga da borda, aplicar um impulso forte para dentro
            if self.cor != AZUL:
                if novo_x < 0:
                    self.x = 10  # Impulso forte para dentro
                else:
                    self.x = LARGURA - self.tamanho - 10
            else:
                # O jogador simplesmente fica na borda
                self.x = max(0, min(novo_x, LARGURA - self.tamanho))
        
        if 0 <= novo_y <= ALTURA - self.tamanho:
            self.y = novo_y
        else:
            # Se for inimigo em fuga da borda, aplicar um impulso forte para dentro
            if self.cor != AZUL:
                if novo_y < 0:
                    self.y = 10
                else:
                    self.y = ALTURA - self.tamanho - 10
            else:
                # O jogador simplesmente fica na borda
                self.y = max(0, min(novo_y, ALTURA - self.tamanho))
        
        # Atualizar o retângulo de colisão
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Atualizar ângulo para efeito visual
        if dx != 0 or dy != 0:
            self.angulo = (self.angulo + 5) % 360

    def atirar(self, tiros, direcao=None):
        """Faz o quadrado atirar na direção especificada."""
        # Verificar cooldown
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro < self.tempo_cooldown:
            return
        
        self.tempo_ultimo_tiro = tempo_atual
        
        # Posição central do quadrado
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2
        
        # Som de tiro
        pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))
        
        # Se não foi especificada uma direção, atira em linha reta
        if direcao is None:
            # Jogador atira para a direita
            if self.cor == AZUL:
                tiros.append(Tiro(centro_x, centro_y, 1, 0, AMARELO, 8))
            # Inimigo atira para a esquerda
            else:
                # Cor do tiro varia com a cor do inimigo
                cor_tiro = VERDE
                # Misturar um pouco da cor do inimigo no tiro
                if self.cor != VERMELHO:
                    verde_base = VERDE[1]
                    r = min(255, self.cor[0] // 3)  # Um pouco da componente vermelha
                    g = verde_base  # Manter o verde forte
                    b = min(255, self.cor[2] // 2)  # Um pouco da componente azul
                    cor_tiro = (r, g, b)
                    
                tiros.append(Tiro(centro_x, centro_y, -1, 0, self.cor, 7))
        else:
            # Cor do tiro baseada no tipo de quadrado
            cor_tiro = AMARELO if self.cor == AZUL else VERDE
            if self.cor != AZUL and self.cor != VERMELHO:
                # Misturar cores para inimigos especiais
                verde_base = VERDE[1]
                r = min(255, self.cor[0] // 3)
                g = verde_base
                b = min(255, self.cor[2] // 2)
                cor_tiro = (r, g, b)
                
            tiros.append(Tiro(centro_x, centro_y, direcao[0], direcao[1], self.cor, 7))


        
    def _inicializar_armas_por_inventario(self):
        """Inicializa as armas e itens baseado na seleção do inventário."""
        # Importação tardia para evitar circular import
        from src.game.inventario import InventarioManager
        
        # Sempre inicializar granada (sistema separado - ativada com Q)
        self.granadas = carregar_upgrade_granada()
        self.granada_selecionada = False
        
        # Sempre permitir tiro normal (não vai no inventário)
        # Tiro normal é sempre disponível
        
        # Inicializar armas do inventário como inativas
        self.espingarda_ativa = False
        self.metralhadora_ativa = False
        self.tiros_espingarda = 0
        self.tiros_metralhadora = 0
        
        # Carregar munição das armas compradas (mas não ativar ainda)
        # A ativação será feita com a tecla E no jogo
        self.tiros_espingarda = carregar_upgrade_espingarda()
        self.tiros_metralhadora = carregar_upgrade_metralhadora()
        
        # NOVO: Carregar item selecionado no inventário
        inventario_manager = InventarioManager()
        item_selecionado = inventario_manager.obter_item_selecionado()
        
        # Auto-equipar item selecionado se disponível

            
    def tomar_dano(self, dano=1):
        """
        Faz o quadrado tomar dano.

        Args:
            dano: Quantidade de dano a receber (padrão: 1)

        Retorna True se o dano foi aplicado, False se estava invulnerável.
        """
        if not self.invulneravel:
            self.vidas -= dano
            # Apenas o jogador fica invulnerável após tomar dano
            if self.cor == AZUL:
                self.invulneravel = True
                self.tempo_invulneravel = pygame.time.get_ticks()
            self.efeito_dano = 10  # Frames de efeito visual
            return True
        return False

    def atualizar(self):
        """Atualiza o estado do quadrado."""
        # Verificar se o tempo de invulnerabilidade acabou (apenas para o jogador)
        if self.invulneravel and self.duracao_invulneravel != float('inf') and pygame.time.get_ticks() - self.tempo_invulneravel > self.duracao_invulneravel:
            self.invulneravel = False
        
        # NOVO: Atualizar sistema de ampulheta (apenas para o jogador)
        if self.cor == AZUL:
            self.atualizar_ampulheta()


    def atirar_com_mouse(self, tiros, pos_mouse):
        """
        Faz o quadrado atirar na direção do cursor do mouse.
        
        Args:
            tiros: Lista onde adicionar o novo tiro
            pos_mouse: Tupla (x, y) com a posição do mouse na tela
        """
        # Verificar cooldown
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro < self.tempo_cooldown:
            return
        
        self.tempo_ultimo_tiro = tempo_atual
        
        # Posição central do quadrado
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2
        
        # Calcular vetor direção para o mouse
        dx = pos_mouse[0] - centro_x
        dy = pos_mouse[1] - centro_y
        
        # Normalizar o vetor direção
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:  # Evitar divisão por zero
            dx /= distancia
            dy /= distancia
        
        # Som de tiro
        pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))
        
        # Criar tiro com a direção calcul
# Criar tiro com a direção calculada
        if self.cor == AZUL:  # Se for o jogador
            tiros.append(Tiro(centro_x, centro_y, dx, dy, AZUL, 8))
        else:
            # Cor do tiro varia com a cor do inimigo (manter lógica original)
            cor_tiro = VERDE
            if self.cor != VERMELHO:
                verde_base = VERDE[1]
                r = min(255, self.cor[0] // 3)  # Um pouco da componente vermelha
                g = verde_base  # Manter o verde forte
                b = min(255, self.cor[2] // 2)  # Um pouco da componente azul
                cor_tiro = (r, g, b)
                
            tiros.append(Tiro(centro_x, centro_y, dx, dy, cor_tiro, 7))

    def ativar_arma_inventario(self):
        """
        Toggle da arma selecionada no inventário (chamado ao pressionar E).
        Agora inclui suporte ao sabre de luz.
        """
        from src.game.inventario import InventarioManager
        
        inventario = InventarioManager()
        arma_selecionada = inventario.obter_arma_selecionada()
        
        # Verificar se granada está selecionada
        if self.granada_selecionada:
            self.granada_selecionada = False
            return "granada_guardada"
        
        # Verificar se ampulheta está selecionada
        if hasattr(self, 'ampulheta_selecionada') and self.ampulheta_selecionada:
            self.ampulheta_selecionada = False
            return "ampulheta_guardada"
        
        # Verificar se já tem alguma arma equipada
        arma_ja_equipada = (self.espingarda_ativa or
                        self.metralhadora_ativa or
                        self.desert_eagle_ativa or
                        self.sabre_equipado)

        # Se já tem arma equipada, guardar todas
        if arma_ja_equipada:
            self.espingarda_ativa = False
            self.metralhadora_ativa = False
            self.desert_eagle_ativa = False
            self.sabre_equipado = False
            # Desativar sabre se estiver ativo
            if hasattr(self, 'sabre_info') and self.sabre_info['ativo']:
                self.sabre_info['ativo'] = False
                self.sabre_info['modo_defesa'] = False
            return "guardada"

        # Se não tem arma equipada, tentar equipar a selecionada
        if arma_selecionada == "espingarda" and self.tiros_espingarda > 0:
            self.espingarda_ativa = True
            self.metralhadora_ativa = False
            self.desert_eagle_ativa = False
            self.sabre_equipado = False
            return "espingarda"
        elif arma_selecionada == "metralhadora" and self.tiros_metralhadora > 0:
            self.metralhadora_ativa = True
            self.espingarda_ativa = False
            self.desert_eagle_ativa = False
            self.sabre_equipado = False
            return "metralhadora"
        elif arma_selecionada == "desert_eagle" and self.tiros_desert_eagle > 0:
            self.desert_eagle_ativa = True
            self.espingarda_ativa = False
            self.metralhadora_ativa = False
            self.sabre_equipado = False
            return "desert_eagle"
        elif arma_selecionada == "sabre_luz" and self.sabre_uses > 0:
            self.sabre_equipado = True
            self.espingarda_ativa = False
            self.metralhadora_ativa = False
            self.desert_eagle_ativa = False
            return "sabre_luz"
        elif arma_selecionada == "nenhuma":
            return "nenhuma_selecionada"
        else:
            return "sem_municao"

    def ativar_items_inventario(self):
        """
        Ativa o item selecionado no inventário (chamado ao pressionar Q).
        - Granada selecionada no inventário → Q toggle granada
        - Ampulheta selecionada no inventário → Q toggle ampulheta (segurar na mão)
        - Combat Knife selecionada no inventário → Q ativa amuleto
        - Nenhum selecionado → Q não faz nada
        """
        from src.game.inventario import InventarioManager
        
        inventario = InventarioManager()
        item_selecionado = inventario.obter_item_selecionado()
        
        # Guardar armas se estiverem ativas
        if self.espingarda_ativa:
            self.espingarda_ativa = False
        if self.metralhadora_ativa:
            self.metralhadora_ativa = False
        if self.sabre_equipado:
            self.sabre_equipado = False
            if hasattr(self, 'sabre_info') and self.sabre_info['ativo']:
                self.sabre_info['ativo'] = False
                self.sabre_info['modo_defesa'] = False
        
        # GRANADA: Se selecionada no inventário, Q faz toggle
        if item_selecionado == "granada":
            if self.granadas > 0:
                self.granada_selecionada = not self.granada_selecionada
                # Desativar ampulheta se granada for ativada
                if self.granada_selecionada and hasattr(self, 'ampulheta_selecionada'):
                    self.ampulheta_selecionada = False
                return "granada_toggle" if self.granada_selecionada else "granada_guardada"
            else:
                return "sem_granadas"
        
        # AMPULHETA: Se selecionada no inventário, Q toggle visual (segurar na mão)
        elif item_selecionado == "ampulheta":
            if hasattr(self, 'ampulheta_uses') and self.ampulheta_uses > 0:
                # Verificar se já está ativa (tempo desacelerado)
                if self.tempo_desacelerado:
                    return "ampulheta_ja_ativa"
                
                # Toggle do modo visual (segurar na mão)
                self.ampulheta_selecionada = not self.ampulheta_selecionada
                # Desativar granada se ampulheta for ativada
                if self.ampulheta_selecionada:
                    self.granada_selecionada = False
                return "ampulheta_toggle" if self.ampulheta_selecionada else "ampulheta_guardada"
            else:
                return "sem_ampulhetas"
        
        # COMBAT KNIFE: Se selecionada no inventário, Q ativa amuleto
        elif item_selecionado == "faca":
            if hasattr(self, 'facas') and self.facas > 0:
                # Toggle do amuleto
                if not hasattr(self, 'amuleto_ativo'):
                    self.amuleto_ativo = False
                
                self.amuleto_ativo = not self.amuleto_ativo
                # Desativar granada e ampulheta se amuleto for ativado
                if self.amuleto_ativo:
                    self.granada_selecionada = False
                    if hasattr(self, 'ampulheta_selecionada'):
                        self.ampulheta_selecionada = False
                return "amuleto_toggle" if self.amuleto_ativo else "amuleto_guardado"
            else:
                return "sem_facas"
        
        # NENHUM: Se nenhum item selecionado no inventário
        else:
            return "nenhum_item_selecionado"

    def usar_ampulheta_com_q(self):
        """Usa a ampulheta quando chamada pela tecla Q."""
        if self.usar_ampulheta():
            return "ampulheta_ativada"
        else:
            if self.tempo_desacelerado:
                return "ampulheta_ja_ativa"
            else:
                return "sem_ampulhetas"

    def obter_item_ativo(self):
        """
        Retorna qual item está atualmente ativo.
        """
        from src.game.inventario import InventarioManager
        
        if self.granada_selecionada and self.granadas > 0:
            return "granada"
        
        if hasattr(self, 'ampulheta_selecionada') and self.ampulheta_selecionada and self.ampulheta_uses > 0:
            return "ampulheta"
        
        inventario = InventarioManager()
        item_selecionado = inventario.obter_item_selecionado()
        if item_selecionado == "ampulheta" and hasattr(self, 'ampulheta_uses') and self.ampulheta_uses > 0:
            return "ampulheta"
        
        return "nenhum"

    def obter_status_itens(self):
        """
        Retorna um dicionário com o status dos itens.
        """
        from src.game.inventario import InventarioManager
        
        inventario = InventarioManager()
        item_selecionado = inventario.obter_item_selecionado()
        
        return {
            "granada": {
                "disponivel": self.granadas > 0,
                "quantidade": self.granadas,
                "ativo": self.granada_selecionada,
                "tecla": "Q"
            },
            "ampulheta": {
                "disponivel": hasattr(self, 'ampulheta_uses') and self.ampulheta_uses > 0,
                "quantidade": getattr(self, 'ampulheta_uses', 0),
                "ativo": hasattr(self, 'ampulheta_selecionada') and self.ampulheta_selecionada,
                "selecionado_inventario": item_selecionado == "ampulheta",
                "tecla": "Q (segurar) + Clique (ativar)"
            }
        }
        
    def _carregar_upgrade_sabre(self):
        """
        Carrega o upgrade do sabre de luz do arquivo de upgrades.
        Retorna 0 se não houver upgrade.
        """
        try:
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("sabre_luz", 0)
            return 0
        except Exception as e:
            print(f"Erro ao carregar upgrade de sabre de luz: {e}")
            return 0

    def ativar_sabre_luz(self):
        """
        Ativa ou desativa o sabre de luz (chamado pelo clique esquerdo quando equipado).
        """
        if not self.sabre_equipado or self.sabre_uses <= 0:
            return "sabre_nao_equipado"
        
        from src.weapons.sabre_luz import ativar_sabre
        return ativar_sabre(self)
    
    def alternar_modo_defesa_sabre(self):
        """
        Alterna o modo de defesa do sabre (chamado pelo clique direito).
        """
        if not self.sabre_equipado or self.sabre_uses <= 0:
            return "sabre_nao_equipado"
        
        from src.weapons.sabre_luz import alternar_modo_defesa
        return alternar_modo_defesa(self)
    
    def obter_info_sabre(self):
        """
        Retorna informações sobre o estado atual do sabre.
        """
        if not hasattr(self, 'sabre_info'):
            return None
        
        return {
            'equipado': self.sabre_equipado,
            'ativo': self.sabre_info.get('ativo', False),
            'modo_defesa': self.sabre_info.get('modo_defesa', False),
            'uses': self.sabre_uses
        }