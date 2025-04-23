#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para efeitos visuais como gradientes, estrelas e renderização de texto.
"""

import pygame
import random
from src.config import LARGURA, ALTURA, BRANCO, AMARELO, VERMELHO
from src.config import LARGURA_JOGO, ALTURA_JOGO

def criar_gradiente(cor1, cor2, largura=None, altura=None):
    """
    Cria uma superfície com um gradiente vertical.
    
    Args:
        cor1: Cor RGB do topo
        cor2: Cor RGB da base
        largura: Largura personalizada (opcional)
        altura: Altura personalizada (opcional)
        
    Returns:
        Superfície com gradiente
    """
    # Usar dimensões fornecidas ou padrão da configuração
    if largura is None:
        largura = LARGURA
    if altura is None:
        altura = ALTURA
        
    gradiente = pygame.Surface((largura, altura))
    for y in range(altura):
        r = cor1[0] + (cor2[0] - cor1[0]) * y / altura
        g = cor1[1] + (cor2[1] - cor1[1]) * y / altura
        b = cor1[2] + (cor2[2] - cor1[2]) * y / altura
        pygame.draw.line(gradiente, (r, g, b), (0, y), (largura, y))
    return gradiente

def criar_estrelas(quantidade):
    """
    Cria uma lista de estrelas para o fundo.
    
    Args:
        quantidade: Número de estrelas a criar
        
    Returns:
        Lista de estrelas (cada uma é uma lista [x, y, tamanho, brilho, velocidade])
    """
    estrelas = []
    for _ in range(quantidade):
        x = random.randint(0, LARGURA)
        y = random.randint(0, ALTURA_JOGO)  # Limitar à área de jogo
        tamanho = random.uniform(0.5, 2.5)
        brilho = random.randint(100, 255)
        vel = random.uniform(0.1, 0.5)
        estrelas.append([x, y, tamanho, brilho, vel])
    return estrelas

def desenhar_estrelas(tela, estrelas):
    """
    Desenha e atualiza as estrelas na tela.
    
    Args:
        tela: Superfície onde desenhar
        estrelas: Lista de estrelas
    """
    for estrela in estrelas:
        x, y, tamanho, brilho, vel = estrela
        # Desenhar a estrela apenas se estiver na área de jogo
        if y < ALTURA_JOGO:
            pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
        
        # Mover a estrela (paralaxe)
        estrela[0] -= vel
        
        # Se a estrela sair da tela, reposicioná-la
        if estrela[0] < 0:
            estrela[0] = LARGURA
            estrela[1] = random.randint(0, ALTURA_JOGO)
def desenhar_texto(tela, texto, tamanho, cor, x, y, fonte=None, sombra=True):
    """
    Desenha texto na tela, opcionalmente com uma sombra.
    
    Args:
        tela: Superfície onde desenhar
        texto: String a ser renderizada
        tamanho: Tamanho da fonte
        cor: Cor RGB do texto
        x, y: Coordenadas do centro do texto
        fonte: Objeto de fonte (opcional)
        sombra: Se True, adiciona sombra ao texto
        
    Returns:
        Rect do texto desenhado
    """
    # Ajustar tamanho da fonte para a resolução atual
    tamanho_ajustado = int(tamanho * (ALTURA / 848))
    
    if fonte is None:
        fonte = pygame.font.SysFont("Arial", tamanho_ajustado, True)
    
    if sombra:
        # Desenhar sombra do texto
        superficie_sombra = fonte.render(texto, True, (30, 30, 30))
        rect_sombra = superficie_sombra.get_rect()
        rect_sombra.center = (x + 2, y + 2)
        tela.blit(superficie_sombra, rect_sombra)
    
    # Desenhar texto principal
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    rect.center = (x, y)
    tela.blit(superficie, rect)
    
    return rect

def criar_botao(tela, texto, x, y, largura, altura, cor_normal, cor_hover, cor_texto):
    """
    Cria um botão interativo na tela.
    
    Args:
        tela: Superfície onde desenhar
        texto: Texto do botão
        x, y: Coordenadas do centro do botão
        largura, altura: Dimensões do botão
        cor_normal: Cor RGB quando não hover
        cor_hover: Cor RGB quando hover
        cor_texto: Cor RGB do texto
        
    Returns:
        True se o mouse estiver sobre o botão, False caso contrário
    """
    # Ajustar dimensões para a resolução atual
    escala_y = ALTURA / 848
    largura_ajustada = int(largura * escala_y)
    altura_ajustada = int(altura * escala_y)
    
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(x - largura_ajustada // 2, y - altura_ajustada // 2, largura_ajustada, altura_ajustada)
    
    hover = rect.collidepoint(mouse_pos)
    
    # Desenhar o botão com efeito de hover
    if hover:
        pygame.draw.rect(tela, cor_hover, rect, 0, 10)
        pygame.draw.rect(tela, (255, 255, 255), rect, 2, 10)
    else:
        pygame.draw.rect(tela, cor_normal, rect, 0, 10)
        pygame.draw.rect(tela, (150, 150, 150), rect, 2, 10)
    
    # Renderizar o texto do botão
    tamanho_fonte = int(28 * escala_y)
    fonte = pygame.font.SysFont("Arial", tamanho_fonte, True)
    texto_surf = fonte.render(texto, True, cor_texto)
    texto_rect = texto_surf.get_rect(center=rect.center)
    tela.blit(texto_surf, texto_rect)
    
    return hover

def criar_mira(tamanho=12, cor=BRANCO, cor_interna=AMARELO):
    """
    Cria uma superfície com uma mira customizada.
    
    Args:
        tamanho: Tamanho da mira em pixels
        cor: Cor principal da mira
        cor_interna: Cor do círculo interno
        
    Returns:
        Tupla (surface, rect) contendo a mira
    """
    # Ajustar tamanho para a resolução atual
    escala = ALTURA / 848
    tamanho_ajustado = int(tamanho * escala)
    
    # Criar uma superfície transparente
    surface = pygame.Surface((tamanho_ajustado*2, tamanho_ajustado*2), pygame.SRCALPHA)
    centro = tamanho_ajustado, tamanho_ajustado
    
    # Desenhar círculo externo
    pygame.draw.circle(surface, cor, centro, tamanho_ajustado, max(1, int(escala)))
    
    # Desenhar cruz
    espessura_linha = max(1, int(escala))
    pygame.draw.line(surface, cor, 
                    (centro[0], centro[1]-tamanho_ajustado+2*escala), 
                    (centro[0], centro[1]+tamanho_ajustado-2*escala), 
                    espessura_linha)
    pygame.draw.line(surface, cor, 
                    (centro[0]-tamanho_ajustado+2*escala, centro[1]), 
                    (centro[0]+tamanho_ajustado-2*escala, centro[1]), 
                    espessura_linha)
    
    # Desenhar círculo interno
    pygame.draw.circle(surface, cor_interna, centro, max(1, tamanho_ajustado//4), 0)
    
    # Criar retângulo para posicionamento
    rect = surface.get_rect(center=centro)
    
    return surface, rect

def desenhar_mira(tela, pos_mouse, mira=None):
    """
    Desenha uma mira personalizada na posição do mouse.
    
    Args:
        tela: Superfície onde desenhar
        pos_mouse: Tupla (x, y) com a posição do mouse
        mira: Tupla (surface, rect) com a mira pré-criada (opcional)
    """
    escala = ALTURA / 848
    
    if mira is None:
        # Mira simples (círculo e cruz)
        raio = int(10 * escala)
        espessura = max(1, int(escala))
        tamanho_linha = int(8 * escala)
        raio_interno = max(1, int(3 * escala))
        
        pygame.draw.circle(tela, BRANCO, pos_mouse, raio, espessura)
        pygame.draw.line(tela, BRANCO, 
                        (pos_mouse[0]-tamanho_linha, pos_mouse[1]), 
                        (pos_mouse[0]+tamanho_linha, pos_mouse[1]), 
                        espessura)
        pygame.draw.line(tela, BRANCO, 
                        (pos_mouse[0], pos_mouse[1]-tamanho_linha), 
                        (pos_mouse[0], pos_mouse[1]+tamanho_linha), 
                        espessura)
        pygame.draw.circle(tela, AMARELO, pos_mouse, raio_interno)
    else:
        # Usar a mira personalizada
        surface, rect = mira
        rect.center = pos_mouse
        tela.blit(surface, rect)

def mira_estilos():
    """
    Retorna uma lista de diferentes estilos de mira para o jogador escolher.
    
    Returns:
        Lista de miras pré-criadas [(surface, rect), ...]
    """
    estilos = []
    
    # Estilo 1: Padrão (branco e amarelo)
    estilos.append(criar_mira(12, BRANCO, AMARELO))
    
    # Estilo 2: Vermelho e branco
    estilos.append(criar_mira(12, VERMELHO, BRANCO))
    
    # Estilo 3: Verde e amarelo
    estilos.append(criar_mira(12, (30, 200, 30), AMARELO))
    
    # Estilo 4: Mira circular
    escala = ALTURA / 848
    tamanho_mira = int(24 * escala)
    raio_externo = int(10 * escala)
    raio_medio = int(6 * escala)
    raio_interno = max(1, int(2 * escala))
    espessura = max(1, int(escala))
    
    mira4 = pygame.Surface((tamanho_mira, tamanho_mira), pygame.SRCALPHA)
    pygame.draw.circle(mira4, BRANCO, (tamanho_mira//2, tamanho_mira//2), raio_externo, espessura)
    pygame.draw.circle(mira4, BRANCO, (tamanho_mira//2, tamanho_mira//2), raio_medio, espessura)
    pygame.draw.circle(mira4, AMARELO, (tamanho_mira//2, tamanho_mira//2), raio_interno)
    rect4 = mira4.get_rect(center=(tamanho_mira//2, tamanho_mira//2))
    estilos.append((mira4, rect4))
    
    # Estilo 5: Mira Triangular
    mira5 = pygame.Surface((tamanho_mira, tamanho_mira), pygame.SRCALPHA)
    pygame.draw.polygon(mira5, BRANCO, [
        (tamanho_mira//2, int(2 * escala)), 
        (tamanho_mira - int(2 * escala), tamanho_mira - int(2 * escala)), 
        (int(2 * escala), tamanho_mira - int(2 * escala))
    ], espessura)
    pygame.draw.circle(mira5, AMARELO, (tamanho_mira//2, tamanho_mira//2), raio_interno)
    rect5 = mira5.get_rect(center=(tamanho_mira//2, tamanho_mira//2))
    estilos.append((mira5, rect5))
    
    return estilos

def criar_texto_flutuante(texto, x, y, cor, particulas, duracao=60, tamanho_fonte=20):
    """
    Cria um texto que flutua para cima e desaparece gradualmente.
    
    Args:
        texto: O texto a ser exibido
        x, y: Posição inicial
        cor: Cor do texto
        particulas: Lista onde adicionar o texto flutuante
        duracao: Duração em frames do texto
        tamanho_fonte: Tamanho da fonte do texto
    """
    # Criar uma classe anônima para o texto flutuante
    class TextoFlutuante:
        def __init__(self, texto, x, y, cor, duracao, tamanho_fonte):
            self.texto = texto
            self.x = x
            self.y = y
            self.cor = cor
            self.vida = duracao
            self.vida_maxima = duracao
            self.tamanho_fonte = tamanho_fonte
            self.velocidade_y = -0.7  # Velocidade para cima
            
        def atualizar(self):
            self.y += self.velocidade_y
            self.vida -= 1
            return self.vida > 0
            
        def desenhar(self, tela):
            # Calcular opacidade com base no tempo de vida restante
            alpha = int(255 * (self.vida / self.vida_maxima))
            
            # Criar fonte e renderizar texto
            fonte = pygame.font.SysFont("Arial", self.tamanho_fonte, True)
            texto_surf = fonte.render(self.texto, True, self.cor)
            texto_surf.set_alpha(alpha)
            
            # Posicionar texto centralizado
            texto_rect = texto_surf.get_rect(center=(int(self.x), int(self.y)))
            tela.blit(texto_surf, texto_rect)
            
        def acabou(self):
            return self.vida <= 0
            
    # Criar e adicionar o texto à lista de partículas
    texto_flutuante = TextoFlutuante(texto, x, y, cor, duracao, tamanho_fonte)
    particulas.append(texto_flutuante)