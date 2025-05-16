#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para lidar com todas as funcionalidades relacionadas a granadas.
Inclui a classe Granada e funções auxiliares para gerenciar granadas no jogo.
"""

import pygame
import math
import random
import os
import json
from src.config import *
from src.entities.particula import criar_explosao
from src.utils.visual import criar_texto_flutuante

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

# Funções adicionais relacionadas a granadas (extraídas de quadrado.py e fase.py)

def carregar_upgrade_granada():
    """
    Carrega o upgrade de granada do arquivo de upgrades.
    Retorna 0 se não houver upgrade.
    """
    try:
        # Verificar se o arquivo existe
        if os.path.exists("data/upgrades.json"):
            with open("data/upgrades.json", "r") as f:
                upgrades = json.load(f)
                return upgrades.get("granada", 0)
        return 0
    except Exception as e:
        print(f"Erro ao carregar upgrade de granada: {e}")
        return 0

def lancar_granada(jogador, granadas_lista, pos_mouse, particulas=None, flashes=None):
    """
    Lança uma granada na direção do cursor do mouse a partir do jogador.
    
    Args:
        jogador: O objeto do jogador
        granadas_lista: Lista onde adicionar a nova granada
        pos_mouse: Tupla (x, y) com a posição do mouse na tela
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)
    """
    # Verificar se o jogador tem granadas disponíveis
    if not hasattr(jogador, 'granadas') or jogador.granadas <= 0:
        return
    
    # Reduzir o contador de granadas
    jogador.granadas -= 1
    
    # Posição central do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2
    
    # Calcular vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y
    
    # Normalizar o vetor direção
    distancia = math.sqrt(dx * dx + dy * dy)
    if distancia > 0:  # Evitar divisão por zero
        dx /= distancia
        dy /= distancia
    
    # Criar som de lançamento de granada
    tamanho_amostra = 8000
    som_granada = pygame.mixer.Sound(bytes(bytearray(
        int(127 + 127 * (math.sin(i / 15) if i < 2000 else 0)) 
        for i in range(tamanho_amostra)
    )))
    som_granada.set_volume(0.2)
    pygame.mixer.Channel(3).play(som_granada)
    
    # Criar efeito visual de lançamento
    if particulas is not None and flashes is not None:
        from src.entities.particula import Particula
        
        # Posição inicial da granada (ligeiramente à frente do jogador)
        pos_x = centro_x + dx * jogador.tamanho
        pos_y = centro_y + dy * jogador.tamanho
        
        # Criar algumas partículas para o efeito de lançamento
        for _ in range(10):
            cor = (100, 200, 100)  # Verde claro
            particula = Particula(pos_x, pos_y, cor)
            particula.velocidade_x = dx * random.uniform(0.5, 2.0) + random.uniform(-1, 1)
            particula.velocidade_y = dy * random.uniform(0.5, 2.0) + random.uniform(-1, 1)
            particula.vida = random.randint(10, 20)
            particula.tamanho = random.uniform(2, 4)
            particulas.append(particula)
    
    # Posição inicial da granada (ligeiramente à frente do jogador)
    pos_x = centro_x + dx * jogador.tamanho
    pos_y = centro_y + dy * jogador.tamanho
    
    # Adicionar a granada à lista
    granada = Granada(pos_x, pos_y, dx, dy)
    granadas_lista.append(granada)
    
    # Desativar o modo de granada após lançar se não houver mais granadas
    if jogador.granadas <= 0:
        jogador.granada_selecionada = False

def processar_granadas(granadas, particulas, flashes, inimigos, moeda_manager):
    """
    Processa todas as granadas na lista, atualizando-as e verificando colisões.
    
    Args:
        granadas: Lista de granadas ativas
        particulas: Lista de partículas para efeitos visuais
        flashes: Lista de flashes para efeitos visuais
        inimigos: Lista de inimigos para verificar colisão
        moeda_manager: Gerenciador de moedas para adicionar moedas quando inimigos são derrotados
        
    Returns:
        None (modifica as listas diretamente)
    """
    # Atualizar granadas
    for granada in granadas[:]:
        # Atualizar a granada e verificar se ainda está ativa
        if not granada.atualizar(particulas, flashes):
            # Verificar dano a inimigos se a granada explodiu
            if granada.explodiu:
                for inimigo in inimigos:
                    if inimigo.vidas > 0 and granada.causa_dano(inimigo):
                        dano_causou_morte = False
                        
                        # Verificar se este dano vai matar o inimigo
                        if inimigo.vidas == 1:
                            dano_causou_morte = True
                        
                        # Aplicar o dano
                        if inimigo.tomar_dano():
                            # Se o inimigo morreu, adicionar moedas
                            if dano_causou_morte:
                                # Determinar quantidade de moedas com base no tipo de inimigo
                                moedas_bonus = 1  # Valor padrão para inimigos básicos
                                
                                # Inimigos com mais vida ou especiais dão mais moedas
                                if inimigo.cor == ROXO:  # Inimigo roxo (especial)
                                    moedas_bonus = 3
                                elif inimigo.cor == CIANO:  # Inimigo ciano
                                    moedas_bonus = 5
                                elif inimigo.vidas_max > 1:  # Inimigos com múltiplas vidas
                                    moedas_bonus = 2
                                
                                # Adicionar moedas ao contador
                                moeda_manager.quantidade_moedas += moedas_bonus
                                moeda_manager.salvar_moedas()  # Salvar as moedas no arquivo
                                
                                # Criar animação de pontuação no local da morte
                                criar_texto_flutuante(f"+{moedas_bonus}", inimigo.x + inimigo.tamanho//2, 
                                                   inimigo.y, AMARELO, particulas)
            
            # Remover a granada da lista
            granadas.remove(granada)

def inicializar_sistema_granadas():
    """
    Inicializa as variáveis necessárias para o sistema de granadas.
    
    Returns:
        Tupla (lista_granadas, timestamp_lancamento):
            - lista_granadas: Lista vazia para armazenar granadas ativas
            - timestamp_lancamento: Timestamp inicial do último lançamento
    """
    return [], pygame.time.get_ticks()

def obter_intervalo_lancamento():
    """
    Obtém o intervalo mínimo entre lançamentos de granadas.
    
    Returns:
        Intervalo em milissegundos
    """
    return 500 

def desenhar_granada_selecionada(tela, jogador, tempo_atual):
    """
    Desenha a granada selecionada pelo jogador.
    
    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos de animação
    """
    # Obter a posição do mouse para orientar a direção de lançamento
    pos_mouse = pygame.mouse.get_pos()
    
    # Calcular o centro do jogador
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2
    
    # Calcular o vetor direção para o mouse
    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y
    
    # Normalizar o vetor direção
    distancia = math.sqrt(dx**2 + dy**2)
    if distancia > 0:
        dx /= distancia
        dy /= distancia
    
    # Distância do jogador onde a granada será desenhada
    distancia_desenho = 25
    
    # Posição da granada
    granada_x = centro_x + dx * distancia_desenho
    granada_y = centro_y + dy * distancia_desenho
    
    # Tamanho e cores da granada
    tamanho_granada = 12
    cor_granada = (60, 120, 60)  # Verde militar
    cor_escura = (40, 80, 40)   # Verde mais escuro
    
    # Desenhar corpo da granada (círculo)
    pygame.draw.circle(tela, cor_granada, (int(granada_x), int(granada_y)), tamanho_granada)
    
    # Detalhes da granada (linhas cruzadas)
    pygame.draw.line(tela, cor_escura, 
                (granada_x - tamanho_granada * 0.6, granada_y), 
                (granada_x + tamanho_granada * 0.6, granada_y), 2)
    pygame.draw.line(tela, cor_escura, 
                (granada_x, granada_y - tamanho_granada * 0.6), 
                (granada_x, granada_y + tamanho_granada * 0.6), 2)
                
    # Parte superior (bocal)
    pygame.draw.rect(tela, (150, 150, 150), 
                (granada_x - 4, granada_y - tamanho_granada - 5, 8, 5), 0, 2)
    
    # Pino da granada
    pin_x = granada_x + 7
    pin_y = granada_y - tamanho_granada - 2
    
    # Anel do pino
    pygame.draw.circle(tela, (220, 220, 100), (pin_x, pin_y), 5, 2)
    
    # Efeito de pulso para indicar que está pronta para uso
    if (tempo_atual // 300) % 2 == 0:  # Piscar a cada 0.3 segundos
        # Brilho ao redor da granada
        pygame.draw.circle(tela, (100, 255, 100, 128), 
                        (int(granada_x), int(granada_y)), 
                        tamanho_granada + 5, 2)
    
    # Desenhar contador de granadas perto do jogador
    fonte = pygame.font.SysFont("Arial", 20, True)
    texto_granada = fonte.render(f"{jogador.granadas}", True, (60, 255, 60))
    texto_rect = texto_granada.get_rect(center=(jogador.x + jogador.tamanho + 15, jogador.y - 10))
    tela.blit(texto_granada, texto_rect)