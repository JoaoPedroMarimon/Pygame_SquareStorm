#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para representar a granada e suas funcionalidades.
"""

import pygame
import math
import random
from src.config import *
from src.entities.particula import criar_explosao

class Granada:
    """
    Classe para representar a granada que o jogador pode lançar.
    Cria uma explosão que causa dano aos inimigos próximos.
    """
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.raio = 10
        self.cor = (60, 120, 60)  # Verde militar
        self.cor_pino = (220, 220, 100)  # Amarelo para o pino
        
        # Normalizar a velocidade
        comprimento = math.sqrt(dx**2 + dy**2)
        velocidade_base = 10.0  # Aumentado de 6.0 para 10.0 para arremessar mais longe
        
        if comprimento > 0:
            self.dx = dx / comprimento * velocidade_base
            self.dy = dy / comprimento * velocidade_base
        else:
            self.dx = velocidade_base  # Padrão: lançar para a direita
            self.dy = 0
            
        # Adicionar um pouco de aleatoriedade à trajetória
        self.dx += random.uniform(-0.5, 0.5)
        self.dy += random.uniform(-0.5, 0.5)
        
        # Física da granada
        self.gravidade = 0.0  # Removendo a gravidade
        self.tempo_vida = 90  # Reduzido de 120 para 90 (1.5 segundos a 60 FPS)
        self.tempo_explosao = 0  # Será definido quando a granada parar
        self.explodiu = False
        self.raio_explosao = 150  # Raio da área de dano
        
        # Quicar a granada
        self.elasticidade = 0.9  # Aumentado de 0.6 para 0.9 para maior rebatimento
        self.fricao = 0.99  # Aumentado de 0.98 para 0.99 para menos desaceleração
        
        # Parâmetros para animação de rotação
        self.angulo = 0
        self.velocidade_rotacao = random.uniform(3, 8)
        
        # Criar retângulo de colisão
        self.rect = pygame.Rect(x - self.raio, y - self.raio, self.raio * 2, self.raio * 2)
        
        # Partículas para efeito de rastro
        self.particulas_rastro = []
        self.ultimo_rastro = 0
    
    def atualizar(self, particulas=None, flashes=None, inimigos=None):
        """
        Atualiza o estado da granada (movimento, física, etc.)
        
        Args:
            particulas: Lista de partículas para efeito visual
            flashes: Lista de flashes para efeito visual
            inimigos: Lista de inimigos para verificar colisão
            
        Returns:
            True se a granada ainda está ativa, False se deve ser removida
        """
        # Se já explodiu, não atualizar mais
        if self.explodiu:
            return False
        
        # Não aplicamos mais gravidade aqui
        
        # Atualizar velocidade com fricção (leve)
        self.dx *= self.fricao
        self.dy *= self.fricao
        
        # Detectar se a velocidade é muito baixa (granada "parada")
        velocidade_total = math.sqrt(self.dx**2 + self.dy**2)
        if velocidade_total < 0.5 and self.tempo_explosao == 0:
            # Se a granada está quase parada, começar contagem para explosão
            self.tempo_explosao = 30  # Reduzido de 60 para 30 (0.5 segundo até explodir)
        
        
        # Mover granada
        self.x += self.dx
        self.y += self.dy
        
        # Verificar colisão com as bordas da tela com rebatimento melhorado
        if self.x - self.raio < 0:
            self.x = self.raio
            self.dx = abs(self.dx) * self.elasticidade  # Garantir que rebata para a direita
        elif self.x + self.raio > LARGURA:
            self.x = LARGURA - self.raio
            self.dx = -abs(self.dx) * self.elasticidade  # Garantir que rebata para a esquerda
            
        if self.y - self.raio < 0:
            self.y = self.raio
            self.dy = abs(self.dy) * self.elasticidade  # Garantir que rebata para baixo
        elif self.y + self.raio > ALTURA_JOGO:  # Considerar apenas a área de jogo
            self.y = ALTURA_JOGO - self.raio
            self.dy = -abs(self.dy) * self.elasticidade  # Garantir que rebata para cima
        
        # Atualizar retângulo de colisão
        self.rect.x = self.x - self.raio
        self.rect.y = self.y - self.raio
        
        # Atualizar ângulo para rotação visual
        self.angulo = (self.angulo + self.velocidade_rotacao) % 360
        
        # Criar rastro da granada
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.ultimo_rastro > 50 and (abs(self.dx) > 0.5 or abs(self.dy) > 0.5):
            self.ultimo_rastro = tempo_atual
            
            if particulas is not None:
                # Criar partícula de rastro
                from src.entities.particula import Particula
                cor_rastro = (100, 160, 100)  # Verde claro para o rastro
                p = Particula(self.x, self.y, cor_rastro)
                p.tamanho = random.uniform(2, 4)
                p.vida = random.randint(10, 20)
                particulas.append(p)
        
        # Decrementar tempo para explosão se definido
        if self.tempo_explosao > 0:
            self.tempo_explosao -= 1
            
            # Piscar a granada quando estiver perto de explodir
            if self.tempo_explosao < 15 and self.tempo_explosao % 3 < 2:  # Piscar mais rápido
                self.cor = (200, 60, 60)  # Vermelho para indicar que vai explodir
            else:
                self.cor = (60, 120, 60)  # Voltar ao verde normal
                
            # Explodir quando o tempo acabar
            if self.tempo_explosao <= 0:
                self.explodir(particulas, flashes)
        
        # Decrementar tempo de vida geral
        self.tempo_vida -= 1
        
        # Se o tempo de vida acabou, explodir
        if self.tempo_vida <= 0:
            self.explodir(particulas, flashes)
            
        return not self.explodiu
    
    def explodir(self, particulas=None, flashes=None):
        """
        Faz a granada explodir, criando efeitos visuais e a lógica de dano.
        
        Args:
            particulas: Lista de partículas para efeito visual
            flashes: Lista de flashes para efeito visual
        """
        self.explodiu = True
        
        # Criar explosão visual se as listas foram fornecidas
        if particulas is not None and flashes is not None:
            # Cores da explosão (tons de vermelho, laranja e amarelo)
            cores = [(255, 100, 0), (255, 200, 0), (255, 50, 0)]
            
            # Criar várias explosões em sucessão para efeito mais dramático
            for i in range(3):
                offset_x = random.uniform(-10, 10)
                offset_y = random.uniform(-10, 10)
                flash = criar_explosao(self.x + offset_x, self.y + offset_y, 
                                     random.choice(cores), particulas, 40)
                flashes.append(flash)
            
            # Explosão central maior
            flash_principal = {
                'x': self.x,
                'y': self.y,
                'raio': 60,  # Muito maior
                'vida': 20,  # Dura mais tempo
                'cor': (255, 255, 200)  # Branco amarelado
            }
            flashes.append(flash_principal)
            
            # Criar onda de choque (círculo expandindo)
            for i in range(1, 5):
                delay = i * 3
                flash_onda = {
                    'x': self.x,
                    'y': self.y,
                    'raio': 20 + i * 15,  # Tamanho aumentando
                    'vida': 10 - i,        # Vida diminuindo
                    'cor': (255, 255, 255, 128)  # Branco semi-transparente
                }
                flashes.append(flash_onda)
    
    def desenhar(self, tela):
        """
        Desenha a granada na tela.
        
        Args:
            tela: Superfície onde desenhar
        """
        if self.explodiu:
            return
            
        # Criar uma superfície temporária para fazer a rotação
        superficie = pygame.Surface((self.raio * 3, self.raio * 3), pygame.SRCALPHA)
        centro = (self.raio * 1.5, self.raio * 1.5)
        
        # Desenhar corpo da granada
        pygame.draw.circle(superficie, self.cor, centro, self.raio)
        
        # Desenhar detalhes
        linha_superior = (centro[0], centro[1] - self.raio * 0.6)
        linha_inferior = (centro[0], centro[1] + self.raio * 0.6)
        linha_esquerda = (centro[0] - self.raio * 0.6, centro[1])
        linha_direita = (centro[0] + self.raio * 0.6, centro[1])
        
        cor_detalhe = (40, 80, 40)  # Verde mais escuro
        pygame.draw.line(superficie, cor_detalhe, linha_esquerda, linha_direita, 2)
        pygame.draw.line(superficie, cor_detalhe, linha_superior, linha_inferior, 2)
        
        # Desenhar bocal e pino
        bocal_rect = pygame.Rect(centro[0] - 5, centro[1] - self.raio - 7, 10, 7)
        pygame.draw.rect(superficie, (150, 150, 150), bocal_rect, 0, 2)
        
        # Anel do pino
        pino_pos = (centro[0] + 8, centro[1] - self.raio - 3)
        pygame.draw.circle(superficie, self.cor_pino, pino_pos, 6, 2)
        
        # Rotacionar a superfície
        superficie_rotada = pygame.transform.rotate(superficie, self.angulo)
        
        # Calcular nova posição após rotação
        rect_rotado = superficie_rotada.get_rect(center=(self.x, self.y))
        
        # Desenhar na tela
        tela.blit(superficie_rotada, rect_rotado)
        
    def causa_dano(self, inimigo):
        """
        Verifica se a explosão da granada causa dano a um inimigo.
        
        Args:
            inimigo: Objeto Quadrado (inimigo) para verificar dano
            
        Returns:
            True se o inimigo foi atingido, False caso contrário
        """
        if not self.explodiu:
            return False
            
        # Calcular distância entre o centro da explosão e o inimigo
        dx = self.x - (inimigo.x + inimigo.tamanho // 2)
        dy = self.y - (inimigo.y + inimigo.tamanho // 2)
        distancia = math.sqrt(dx**2 + dy**2)
        
        # Verificar se o inimigo está dentro do raio da explosão
        return distancia <= self.raio_explosao