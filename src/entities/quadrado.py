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
        self.tiros_espingarda = self._carregar_upgrade_espingarda()
        self.espingarda_ativa = False
        
        # Verificar se é o jogador e carregar upgrade de vida
        if cor == AZUL:  # Se for o jogador
            vidas_upgrade = self._carregar_upgrade_vida()
            self.vidas = vidas_upgrade
            self.vidas_max = vidas_upgrade
        else:  # Se for inimigo
            self.vidas = 1  # Padrão: 1 vida para inimigos normais
            self.vidas_max = 1
        
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
        
    
    def _gerar_cor_escura(self, cor):
        """Gera uma versão mais escura da cor."""
        return tuple(max(0, c - 50) for c in cor)
    
    def _gerar_cor_brilhante(self, cor):
        """Gera uma versão mais brilhante da cor."""
        return tuple(min(255, c + 70) for c in cor)

    def desenhar(self, tela):
        """Desenha o quadrado na tela com seus efeitos visuais."""
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
        if self.invulneravel and pygame.time.get_ticks() % 200 < 100:
            return
        
        # Efeito de pulsação
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_pulsacao > 100:
            self.tempo_pulsacao = tempo_atual
            self.pulsando = (self.pulsando + 1) % 12
            
        mod_tamanho = 0
        if self.pulsando < 6:
            mod_tamanho = self.pulsando
        else:
            mod_tamanho = 12 - self.pulsando
            
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
        
        # Desenhar espingarda se for o jogador (cor AZUL) e tiver a espingarda ativa
        if self.cor == AZUL and hasattr(self, 'espingarda_ativa') and self.espingarda_ativa:
            # Obter a posição do mouse para orientar a espingarda
            pos_mouse = pygame.mouse.get_pos()
            
            # Calcular o centro do jogador
            centro_x = self.x + self.tamanho // 2
            centro_y = self.y + self.tamanho // 2
            
            # Calcular o vetor direção para o mouse
            dx = pos_mouse[0] - centro_x
            dy = pos_mouse[1] - centro_y
            
            # Normalizar o vetor direção
            distancia = math.sqrt(dx**2 + dy**2)
            if distancia > 0:
                dx /= distancia
                dy /= distancia
            
            # Comprimento da espingarda
            comprimento_arma = 35  # Ligeiramente mais longo
            
            # Posição da ponta da arma
            ponta_x = centro_x + dx * comprimento_arma
            ponta_y = centro_y + dy * comprimento_arma
            
            # Vetor perpendicular para elementos laterais
            perp_x = -dy
            perp_y = dx
            
            # Cores da espingarda
            cor_metal = (180, 180, 190)  # Metal prateado
            cor_cano = (100, 100, 110)   # Cano escuro
            cor_madeira = (120, 80, 40)  # Madeira escura
            cor_madeira_clara = (150, 100, 50)  # Madeira clara
            
            # DESENHO COMPLETO DA ESPINGARDA
            
            # 1. Cano principal (mais grosso e com gradiente)
            for i in range(4):
                offset = i - 1.5
                pygame.draw.line(tela, cor_cano, 
                            (centro_x + perp_x * offset, centro_y + perp_y * offset), 
                            (ponta_x + perp_x * offset, ponta_y + perp_y * offset), 3)
            
            # 2. Boca do cano com destaque
            pygame.draw.circle(tela, cor_metal, (int(ponta_x), int(ponta_y)), 5)
            pygame.draw.circle(tela, (40, 40, 40), (int(ponta_x), int(ponta_y)), 3)
            
            # 3. Suporte sob o cano
            meio_cano_x = centro_x + dx * (comprimento_arma * 0.6)
            meio_cano_y = centro_y + dy * (comprimento_arma * 0.6)
            pygame.draw.line(tela, cor_metal, 
                            (meio_cano_x + perp_x * 3, meio_cano_y + perp_y * 3), 
                            (meio_cano_x - perp_x * 3, meio_cano_y - perp_y * 3), 3)
            
            # 4. Corpo central / Mecanismo (mais detalhado)
            corpo_x = centro_x + dx * 8
            corpo_y = centro_y + dy * 8
            # Base do corpo
            pygame.draw.circle(tela, cor_metal, (int(corpo_x), int(corpo_y)), 7)
            # Detalhes do mecanismo
            pygame.draw.circle(tela, (50, 50, 55), (int(corpo_x), int(corpo_y)), 4)
            # Reflete mecanismo (brilho)
            brilho_x = corpo_x - dx + perp_x
            brilho_y = corpo_y - dy + perp_y
            pygame.draw.circle(tela, (220, 220, 230), (int(brilho_x), int(brilho_y)), 2)
            
            # 5. Coronha mais elegante (formato mais curvado)
            # Pontos para a coronha em formato mais curvo
            # Base conectando ao corpo
            coronha_base_x = corpo_x - dx * 2
            coronha_base_y = corpo_y - dy * 2
            
            # Pontos superiores e inferiores no início da coronha
            sup_inicio_x = coronha_base_x + perp_x * 6
            sup_inicio_y = coronha_base_y + perp_y * 6
            inf_inicio_x = coronha_base_x - perp_x * 6
            inf_inicio_y = coronha_base_y - perp_y * 6
            
            # Pontos do final da coronha (mais estreitos)
            sup_fim_x = coronha_base_x - dx * 15 + perp_x * 4
            sup_fim_y = coronha_base_y - dy * 15 + perp_y * 4
            inf_fim_x = coronha_base_x - dx * 15 - perp_x * 4
            inf_fim_y = coronha_base_y - dy * 15 - perp_y * 4
            
            # Desenhar coronha principal
            pygame.draw.polygon(tela, cor_madeira, [
                (sup_inicio_x, sup_inicio_y),
                (inf_inicio_x, inf_inicio_y),
                (inf_fim_x, inf_fim_y),
                (sup_fim_x, sup_fim_y)
            ])
            
            # 6. Detalhes da coronha (linhas de madeira)
            for i in range(1, 4):
                linha_x1 = sup_inicio_x - dx * (i * 3) + perp_x * (6 - i * 0.5)
                linha_y1 = sup_inicio_y - dy * (i * 3) + perp_y * (6 - i * 0.5)
                linha_x2 = inf_inicio_x - dx * (i * 3) - perp_x * (6 - i * 0.5)
                linha_y2 = inf_inicio_y - dy * (i * 3) - perp_y * (6 - i * 0.5)
                pygame.draw.line(tela, cor_madeira_clara, 
                                (linha_x1, linha_y1), 
                                (linha_x2, linha_y2), 1)
            
            # 7. Gatilho e proteção (mais detalhados)
            # Base do gatilho
            gatilho_base_x = corpo_x - dx * 3
            gatilho_base_y = corpo_y - dy * 3
            
            # Proteção do gatilho (arco)
            pygame.draw.arc(tela, cor_metal, 
                        [gatilho_base_x - 5, gatilho_base_y - 5, 10, 10],
                        math.pi/2, math.pi * 1.5, 2)
            
            # Gatilho (linha curva)
            gatilho_x = gatilho_base_x - perp_x * 2
            gatilho_y = gatilho_base_y - perp_y * 2
            pygame.draw.line(tela, (40, 40, 40), 
                            (gatilho_base_x, gatilho_base_y), 
                            (gatilho_x, gatilho_y), 2)
            
            # 8. Efeito de brilho no metal
            pygame.draw.line(tela, (220, 220, 230), 
                            (centro_x + perp_x * 2, centro_y + perp_y * 2), 
                            (corpo_x + perp_x * 2, corpo_y + perp_y * 2), 1)
            
            # 9. Efeito de energia/carregamento (quando estiver ativa)
            # Pulsar baseado no tempo atual
            pulso = (math.sin(tempo_atual / 150) + 1) / 2  # Valor entre 0 e 1
            cor_energia = (50 + int(pulso * 200), 50 + int(pulso * 150), 255)
            
            # Linha de energia ao longo do cano
            energia_width = 2 + int(pulso * 2)
            meio_cano2_x = centro_x + dx * (comprimento_arma * 0.3)
            meio_cano2_y = centro_y + dy * (comprimento_arma * 0.3)
            pygame.draw.line(tela, cor_energia, 
                            (meio_cano2_x, meio_cano2_y), 
                            (ponta_x, ponta_y), energia_width)


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

    def _carregar_upgrade_espingarda(self):
        """
        Carrega o upgrade de espingarda do arquivo de upgrades.
        Retorna 0 se não houver upgrade.
        """
        try:
            # Verificar se o arquivo existe
            if os.path.exists("data/upgrades.json"):
                with open("data/upgrades.json", "r") as f:
                    upgrades = json.load(f)
                    return upgrades.get("espingarda", 0)
            return 0
        except Exception as e:
            print(f"Erro ao carregar upgrade de espingarda: {e}")
            return 0
# Add to src/entities/quadrado.py in Quadrado class
# Modifique a função atirar_espingarda no arquivo src/entities/quadrado.py
# Modificação do método atirar_espingarda no arquivo src/entities/quadrado.py
    def atirar_espingarda(self, tiros, pos_mouse, particulas=None, flashes=None, num_tiros=5):
        """
        Dispara múltiplos tiros em um padrão de espingarda e cria uma animação de partículas no cano.
        
        Args:
            tiros: Lista onde adicionar os novos tiros
            pos_mouse: Tupla (x, y) com a posição do mouse
            particulas: Lista de partículas para efeitos visuais (opcional)
            flashes: Lista de flashes para efeitos visuais (opcional)
            num_tiros: Número de tiros a disparar
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
        
        # Som de tiro de espingarda (mais forte)
        som_espingarda = pygame.mixer.Sound(gerar_som_tiro())
        som_espingarda.set_volume(0.3)  # Volume mais alto para a espingarda
        pygame.mixer.Channel(1).play(som_espingarda)
        
        # Ângulo de dispersão para cada tiro
        angulo_base = math.atan2(dy, dx)
        dispersao = 0.3  # Aumentar a dispersão de 0.2 para 0.3 para ter um leque maior
        
        # Calcular a posição da ponta do cano para o efeito de partículas
        comprimento_arma = 35
        ponta_cano_x = centro_x + dx * comprimento_arma
        ponta_cano_y = centro_y + dy * comprimento_arma
        
        # Criar efeito de partículas na ponta do cano
        if particulas is not None:
            from src.entities.particula import Particula
            import random
            
            # Definir cor amarela para todas as partículas
            cor_amarela = (255, 255, 0)  # Amarelo puro
            
            # Criar várias partículas para um efeito de explosão no cano
            for _ in range(15):
                # Todas as partículas serão amarelas
                cor = cor_amarela
                
                # Posição com pequena variação aleatória ao redor da ponta do cano
                vari_x = random.uniform(-5, 5)
                vari_y = random.uniform(-5, 5)
                pos_x = ponta_cano_x + vari_x
                pos_y = ponta_cano_y + vari_y
                
                # Criar partícula
                particula = Particula(pos_x, pos_y, cor)
                
                # Configurar propriedades da partícula para simular o disparo
                particula.velocidade_x = dx * random.uniform(2, 5) + random.uniform(-1, 1)
                particula.velocidade_y = dy * random.uniform(2, 5) + random.uniform(-1, 1)
                particula.vida = random.randint(5, 15)  # Vida curta para um efeito rápido
                particula.tamanho = random.uniform(1.5, 4)  # Partículas menores
                particula.gravidade = 0.03  # Gravidade reduzida
                
                # Adicionar à lista de partículas
                particulas.append(particula)
        
        # Adicionar um flash luminoso na ponta do cano
        if flashes is not None:
            flash = {
                'x': ponta_cano_x,
                'y': ponta_cano_y,
                'raio': 15,
                'vida': 5,
                'cor': (255, 255, 0)  # Amarelo puro, mesma cor das partículas
            }
            flashes.append(flash)
        
        # Criar tiros com ângulos ligeiramente diferentes
        for i in range(num_tiros):
            # Calcular ângulo para este tiro
            angulo_variacao = dispersao * (i / (num_tiros - 1) - 0.5) * 2
            angulo_atual = angulo_base + angulo_variacao
            
            # Calcular direção com o novo ângulo
            tiro_dx = math.cos(angulo_atual)
            tiro_dy = math.sin(angulo_atual)
            
            # Criar tiro com a direção calculada
            tiros.append(Tiro(centro_x, centro_y, tiro_dx, tiro_dy, AZUL, 8))


    def tomar_dano(self):
        """
        Faz o quadrado tomar dano.
        Retorna True se o dano foi aplicado, False se estava invulnerável.
        """
        if not self.invulneravel:
            self.vidas -= 1
            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks()
            self.efeito_dano = 10  # Frames de efeito visual
            return True
        return False

    def atualizar(self):
        """Atualiza o estado do quadrado."""
        # Verificar se o tempo de invulnerabilidade acabou
        if self.invulneravel and pygame.time.get_ticks() - self.tempo_invulneravel > self.duracao_invulneravel:
            self.invulneravel = False

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