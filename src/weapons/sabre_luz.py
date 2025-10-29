#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
src/weapons/sabre_luz.py
Módulo para gerenciar todas as funcionalidades relacionadas ao sabre de luz.
Inclui ativação, deflexão de tiros, modo defesa e efeitos visuais.
"""

import pygame
import math
import random
import os
import json
from src.config import *
from src.utils.sound import gerar_som_tiro
from src.entities.particula import Particula

def carregar_upgrade_sabre():
    """
    Carrega o upgrade de sabre de luz do arquivo de upgrades.
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

def criar_som_sabre_ativacao():
    """Cria um som futurista para a ativação do sabre."""
    duracao = 0.8
    sample_rate = 22050
    frames = int(duracao * sample_rate)
    
    som_data = []
    for i in range(frames):
        t = i / sample_rate
        freq = 220 + (880 - 220) * (t / duracao)  # Frequência crescente
        
        amplitude = (
            0.4 * math.sin(2 * math.pi * freq * t) +
            0.2 * math.sin(2 * math.pi * freq * 1.5 * t)
        ) * (1 - math.exp(-t * 3))  # Fade in
        
        som_data.append(int(amplitude * 32767))
    
    som_bytes = bytearray()
    for sample in som_data:
        som_bytes.extend(sample.to_bytes(2, byteorder='little', signed=True))
    
    return pygame.mixer.Sound(bytes(som_bytes))

def criar_som_sabre_hum():
    """Cria um som contínuo do sabre ligado (REMOVIDO - sem som contínuo)."""
    # Som contínuo removido conforme solicitado
    return None

def arremessar_sabre(jogador, pos_mouse):
    """
    Arremessa o sabre de luz na direção do mouse como um boomerang.

    Args:
        jogador: Objeto do jogador
        pos_mouse: Posição do mouse para onde arremessar

    Returns:
        True se arremessou com sucesso, False caso contrário
    """
    if not hasattr(jogador, 'sabre_info'):
        return False

    sabre = jogador.sabre_info

    # Só pode arremessar se o sabre estiver ativo e não estiver já voando
    if not sabre['ativo'] or sabre.get('arremessado', False):
        return False

    # Calcular direção do arremesso
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    dx = pos_mouse[0] - centro_x
    dy = pos_mouse[1] - centro_y
    distancia = math.sqrt(dx**2 + dy**2)

    if distancia == 0:
        return False

    # Normalizar direção
    dx /= distancia
    dy /= distancia

    # Configurar estado de arremesso
    sabre['arremessado'] = True
    sabre['arremesso_pos_x'] = centro_x
    sabre['arremesso_pos_y'] = centro_y
    sabre['arremesso_vel_x'] = dx * 12  # Velocidade do arremesso (12 pixels/frame)
    sabre['arremesso_vel_y'] = dy * 12
    sabre['arremesso_rotacao'] = 0  # Ângulo de rotação inicial
    sabre['arremesso_retornando'] = False
    sabre['modo_defesa'] = False  # Desativar modo defesa durante arremesso

    return True

def forcar_retorno_sabre(jogador):
    """
    Força o retorno imediato do sabre arremessado para o jogador.

    Args:
        jogador: Objeto do jogador

    Returns:
        True se forçou o retorno, False se o sabre não estava arremessado
    """
    if not hasattr(jogador, 'sabre_info'):
        return False

    sabre = jogador.sabre_info

    if not sabre.get('arremessado', False):
        return False

    # Ativar modo de retorno imediato
    sabre['arremesso_retornando'] = True

    return True

def atualizar_sabre_arremessado(jogador, tempo_atual):
    """
    Atualiza a física do sabre arremessado (movimento e rotação).

    Args:
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms

    Returns:
        True se o sabre ainda está voando, False se retornou ao jogador
    """
    if not hasattr(jogador, 'sabre_info'):
        return False

    sabre = jogador.sabre_info

    if not sabre.get('arremessado', False):
        return False

    from src.config import LARGURA, ALTURA_JOGO

    # Atualizar rotação (gira rapidamente)
    sabre['arremesso_rotacao'] = (sabre['arremesso_rotacao'] + 25) % 360

    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2

    # Verificar se deve começar a retornar
    if not sabre['arremesso_retornando']:
        # Verificar colisão com bordas
        # IMPORTANTE: Só ativar retorno se o sabre já viajou uma distância mínima do jogador
        # Isso evita que o sabre retorne imediatamente quando o jogador está nas bordas
        distancia_do_jogador = math.sqrt((sabre['arremesso_pos_x'] - centro_x)**2 +
                                         (sabre['arremesso_pos_y'] - centro_y)**2)

        # Só verificar bordas se o sabre já viajou pelo menos 60 pixels
        if distancia_do_jogador > 60:
            if (sabre['arremesso_pos_x'] <= 20 or
                sabre['arremesso_pos_x'] >= LARGURA - 20 or
                sabre['arremesso_pos_y'] <= 20 or
                sabre['arremesso_pos_y'] >= ALTURA_JOGO - 20):
                sabre['arremesso_retornando'] = True

    # Atualizar posição
    if sabre['arremesso_retornando']:
        # Retornar ao jogador (movimento tipo boomerang)
        dx = centro_x - sabre['arremesso_pos_x']
        dy = centro_y - sabre['arremesso_pos_y']
        distancia = math.sqrt(dx**2 + dy**2)

        # Verificar se chegou de volta ao jogador
        if distancia < 30:
            sabre['arremessado'] = False
            sabre['arremesso_retornando'] = False
            return False

        # Normalizar e aplicar velocidade de retorno (mais rápido)
        dx /= distancia
        dy /= distancia
        sabre['arremesso_vel_x'] = dx * 15  # Retorno mais rápido
        sabre['arremesso_vel_y'] = dy * 15

    # Mover sabre
    sabre['arremesso_pos_x'] += sabre['arremesso_vel_x']
    sabre['arremesso_pos_y'] += sabre['arremesso_vel_y']

    return True

def processar_deflexao_sabre_arremessado(jogador, tiros_inimigo, particulas=None, flashes=None):
    """
    Processa deflexão de tiros pelo sabre arremessado girando.
    Tiros que tocam o sabre arremessado são refletidos de volta aos inimigos.

    Args:
        jogador: Objeto do jogador
        tiros_inimigo: Lista de tiros inimigos
        particulas: Lista de partículas para efeitos
        flashes: Lista de flashes para efeitos

    Returns:
        Lista de tiros refletidos
    """
    tiros_refletidos = []

    if not hasattr(jogador, 'sabre_info'):
        return tiros_refletidos

    sabre = jogador.sabre_info

    if not sabre.get('arremessado', False):
        return tiros_refletidos

    raio_deflexao = 60  # Raio de deflexão do sabre girando (maior que o dano)

    for tiro in tiros_inimigo[:]:
        # Calcular distância do tiro ao sabre
        dx = tiro.x - sabre['arremesso_pos_x']
        dy = tiro.y - sabre['arremesso_pos_y']
        distancia = math.sqrt(dx**2 + dy**2)

        # Verificar se o tiro está próximo do sabre
        if distancia < raio_deflexao:
            # Refletir o tiro de volta
            # Inverter direção do tiro
            tiro.dx = -tiro.dx
            tiro.dy = -tiro.dy

            # Mudar cor para azul (tiro refletido)
            from src.config import AZUL
            tiro.cor = AZUL

            # Remover da lista de tiros inimigos e adicionar aos tiros do jogador
            tiros_inimigo.remove(tiro)
            tiros_refletidos.append(tiro)

            # Efeitos visuais de deflexão
            if particulas is not None:
                for _ in range(8):
                    particula_x = sabre['arremesso_pos_x'] + random.uniform(-10, 10)
                    particula_y = sabre['arremesso_pos_y'] + random.uniform(-10, 10)

                    particula = Particula(particula_x, particula_y, (150, 200, 255))
                    particula.velocidade_x = random.uniform(-3, 3)
                    particula.velocidade_y = random.uniform(-3, 3)
                    particula.vida = random.randint(5, 10)
                    particula.tamanho = random.uniform(1, 3)
                    particulas.append(particula)

            # Flash de deflexão
            if flashes is not None:
                flashes.append({
                    'x': sabre['arremesso_pos_x'],
                    'y': sabre['arremesso_pos_y'],
                    'raio': 20,
                    'vida': 8,
                    'cor': (100, 200, 255)
                })

            # Som de deflexão
            from src.utils.sound import gerar_som_tiro
            som_deflexao = gerar_som_tiro()
            som = pygame.mixer.Sound(som_deflexao)
            som.set_volume(0.12)
            pygame.mixer.Channel(7).play(som)

    return tiros_refletidos

def processar_dano_sabre_arremessado(jogador, inimigos, particulas=None, flashes=None):
    """
    Processa dano causado pelo sabre arremessado girando.

    Args:
        jogador: Objeto do jogador
        inimigos: Lista de inimigos
        particulas: Lista de partículas para efeitos
        flashes: Lista de flashes para efeitos

    Returns:
        Lista de inimigos atingidos
    """
    inimigos_atingidos = []

    if not hasattr(jogador, 'sabre_info'):
        return inimigos_atingidos

    sabre = jogador.sabre_info

    if not sabre.get('arremessado', False):
        return inimigos_atingidos

    raio_dano = 50  # Raio de dano do sabre girando
    tempo_atual = pygame.time.get_ticks()

    for inimigo in inimigos:
        # Verificar se inimigo está vivo
        if inimigo.vidas <= 0:
            continue

        # Calcular distância até o inimigo
        centro_inimigo_x = inimigo.x + inimigo.tamanho // 2
        centro_inimigo_y = inimigo.y + inimigo.tamanho // 2

        dx = centro_inimigo_x - sabre['arremesso_pos_x']
        dy = centro_inimigo_y - sabre['arremesso_pos_y']
        distancia = math.sqrt(dx**2 + dy**2)

        # Verificar colisão
        if distancia < raio_dano:
            # Verificar cooldown (para não dar dano múltiplas vezes muito rápido)
            if not hasattr(inimigo, 'ultimo_dano_sabre_arremessado'):
                inimigo.ultimo_dano_sabre_arremessado = 0

            # Cooldown de 200ms entre danos do sabre arremessado (mais rápido que o normal)
            if tempo_atual - inimigo.ultimo_dano_sabre_arremessado >= 200:
                inimigo.ultimo_dano_sabre_arremessado = tempo_atual

                # Aplicar dano usando o método do inimigo (3 de dano)
                if inimigo.tomar_dano(dano=3):
                    inimigos_atingidos.append(inimigo)

                    # Criar partículas de corte
                    if particulas is not None:
                        for _ in range(12):
                            particula_x = centro_inimigo_x + random.uniform(-15, 15)
                            particula_y = centro_inimigo_y + random.uniform(-15, 15)

                            particula = Particula(particula_x, particula_y, (150, 200, 255))
                            particula.velocidade_x = random.uniform(-4, 4)
                            particula.velocidade_y = random.uniform(-4, 4)
                            particula.vida = random.randint(8, 15)
                            particula.tamanho = random.uniform(2, 4)
                            particulas.append(particula)

                    # Criar flash no ponto de impacto
                    if flashes is not None:
                        flashes.append({
                            'x': centro_inimigo_x,
                            'y': centro_inimigo_y,
                            'raio': 25,
                            'vida': 10,
                            'cor': (150, 200, 255)
                        })

    return inimigos_atingidos

def verificar_colisao_sabre_tiro(sabre_info, tiro):
    """
    Verifica se um tiro colidiu com a lâmina do sabre.
    
    Args:
        sabre_info: Dicionário com informações do sabre
        tiro: Objeto do tiro
        
    Returns:
        True se houve colisão, False caso contrário
    """
    if not sabre_info['ativo']:
        return False
    
    # Obter linha da lâmina
    linha_inicio = sabre_info['pos_cabo']
    linha_fim = sabre_info['pos_ponta']
    
    # Posição do tiro
    tiro_pos = (tiro.x, tiro.y)
    
    # Calcular distância do ponto à linha
    distancia = distancia_ponto_linha(tiro_pos, linha_inicio, linha_fim)
    
    # Considerar colisão se estiver próximo o suficiente
    return distancia <= 8  # Raio de detecção

def distancia_ponto_linha(ponto, linha_inicio, linha_fim):
    """
    Calcula a distância mínima entre um ponto e uma linha.
    """
    x0, y0 = ponto
    x1, y1 = linha_inicio
    x2, y2 = linha_fim
    
    # Vetor da linha
    dx = x2 - x1
    dy = y2 - y1
    
    # Se a linha tem comprimento zero
    if dx == 0 and dy == 0:
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # Parâmetro t para projeção do ponto na linha
    t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)))
    
    # Ponto mais próximo na linha
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    
    # Distância
    return math.sqrt((x0 - proj_x)**2 + (y0 - proj_y)**2)

def calcular_angulo_reflexao(tiro, sabre_info):
    """
    Calcula o ângulo de reflexão do tiro no sabre.
    
    Args:
        tiro: Objeto do tiro
        sabre_info: Informações do sabre
        
    Returns:
        Tupla (dx, dy) com a nova direção do tiro
    """
    # Vetor da lâmina do sabre
    cabo_x, cabo_y = sabre_info['pos_cabo']
    ponta_x, ponta_y = sabre_info['pos_ponta']
    
    # Vetor normal à lâmina (perpendicular)
    lamina_dx = ponta_x - cabo_x
    lamina_dy = ponta_y - cabo_y
    
    # Normalizar
    lamina_len = math.sqrt(lamina_dx**2 + lamina_dy**2)
    if lamina_len > 0:
        lamina_dx /= lamina_len
        lamina_dy /= lamina_len
    
    # Vetor normal (perpendicular à lâmina)
    normal_x = -lamina_dy
    normal_y = lamina_dx
    
    # Vetor incidente do tiro
    inc_x = tiro.dx
    inc_y = tiro.dy
    
    # Reflexão: R = I - 2(I·N)N
    dot_product = inc_x * normal_x + inc_y * normal_y
    ref_x = inc_x - 2 * dot_product * normal_x
    ref_y = inc_y - 2 * dot_product * normal_y
    
    return ref_x, ref_y

def atualizar_sabre(jogador, pos_mouse, tempo_atual):
    """
    Atualiza o estado do sabre de luz do jogador.
    
    Args:
        jogador: Objeto do jogador
        pos_mouse: Posição do mouse
        tempo_atual: Tempo atual em ms
        
    Returns:
        Dicionário com informações do sabre
    """
    if not hasattr(jogador, 'sabre_info'):
        jogador.sabre_info = {
            'ativo': False,
            'animacao_ativacao': 0,
            'modo_defesa': False,
            'pos_cabo': (0, 0),
            'pos_ponta': (0, 0),
            'angulo': 0,
            'comprimento_atual': 0,
            'tempo_ultimo_hum': 0
        }
    
    sabre = jogador.sabre_info
    
    # Calcular posições
    centro_x = jogador.x + jogador.tamanho // 2
    centro_y = jogador.y + jogador.tamanho // 2
    
    # Calcular ângulo baseado no modo
    if sabre['modo_defesa']:
        # Modo defesa: sabre segue o mouse, mas fica perpendicular à direção
        dx = pos_mouse[0] - centro_x
        dy = pos_mouse[1] - centro_y
        angulo_mouse = math.atan2(dy, dx)
        
        # Sabre perpendicular à direção do mouse (- 90 graus para cabo embaixo)
        angulo = angulo_mouse - math.pi / 2
    else:
        # Modo normal: sabre segue o mouse
        dx = pos_mouse[0] - centro_x
        dy = pos_mouse[1] - centro_y
        angulo = math.atan2(dy, dx)
    
    sabre['angulo'] = angulo
    
    # Posição do cabo (próximo ao jogador)
    if sabre['modo_defesa']:
        # No modo defesa, o cabo fica mais distante para criar uma "parede" à frente
        distancia_cabo = 35
    else:
        # Modo normal
        distancia_cabo = 20
    
    cabo_x = centro_x + math.cos(angulo_mouse if sabre['modo_defesa'] else angulo) * distancia_cabo
    cabo_y = centro_y + math.sin(angulo_mouse if sabre['modo_defesa'] else angulo) * distancia_cabo
    sabre['pos_cabo'] = (cabo_x, cabo_y)
    
    # Atualizar animação de ativação
    if sabre['ativo'] and sabre['animacao_ativacao'] < 100:
        sabre['animacao_ativacao'] += 5  # Animação rápida
    elif not sabre['ativo'] and sabre['animacao_ativacao'] > 0:
        sabre['animacao_ativacao'] -= 8  # Desativação mais rápida
    
    # Comprimento da lâmina baseado na animação (AUMENTADO para ficar mais legal)
    comprimento_max = 90  # Aumentado de 60 para 90
    sabre['comprimento_atual'] = (sabre['animacao_ativacao'] / 100) * comprimento_max
    
    # Posição da ponta
    ponta_x = cabo_x + math.cos(angulo) * sabre['comprimento_atual']
    ponta_y = cabo_y + math.sin(angulo) * sabre['comprimento_atual']
    sabre['pos_ponta'] = (ponta_x, ponta_y)
    
    return sabre

def ativar_sabre(jogador):
    """
    Ativa ou desativa o sabre de luz.
    
    Args:
        jogador: Objeto do jogador
        
    Returns:
        String indicando o resultado da ação
    """
    if not hasattr(jogador, 'sabre_info'):
        jogador.sabre_info = {
            'ativo': False,
            'animacao_ativacao': 0,
            'modo_defesa': False,
            'pos_cabo': (0, 0),
            'pos_ponta': (0, 0),
            'angulo': 0,
            'comprimento_atual': 0,
            'tempo_ultimo_hum': 0
        }
    
    sabre = jogador.sabre_info
    
    if not sabre['ativo']:
        # Ativar sabre
        sabre['ativo'] = True
        sabre['modo_defesa'] = False
        
        # Som de ativação
        som_ativacao = criar_som_sabre_ativacao()
        som_ativacao.set_volume(0.3)
        pygame.mixer.Channel(5).play(som_ativacao)
        
        return "sabre_ativado"
    else:
        # Desativar sabre
        sabre['ativo'] = False
        sabre['modo_defesa'] = False
        return "sabre_desativado"

def alternar_modo_defesa(jogador):
    """
    Alterna o modo de defesa do sabre.
    
    Args:
        jogador: Objeto do jogador
        
    Returns:
        String indicando o novo estado
    """
    if hasattr(jogador, 'sabre_info') and jogador.sabre_info['ativo']:
        jogador.sabre_info['modo_defesa'] = not jogador.sabre_info['modo_defesa']
        
        if jogador.sabre_info['modo_defesa']:
            return "modo_defesa_ativado"
        else:
            return "modo_defesa_desativado"
    
    return "sabre_inativo"

def processar_dano_sabre(jogador, inimigos, particulas=None, flashes=None):
    """
    Processa o dano do sabre de luz nos inimigos.
    APENAS A LÂMINA DE ENERGIA causa dano, não o cabo.
    
    Args:
        jogador: Objeto do jogador
        inimigos: Lista de inimigos
        particulas: Lista de partículas para efeitos
        flashes: Lista de flashes para efeitos
        
    Returns:
        Lista de inimigos que foram atingidos
    """
    inimigos_atingidos = []
    
    if not hasattr(jogador, 'sabre_info') or not jogador.sabre_info['ativo']:
        return inimigos_atingidos
    
    sabre = jogador.sabre_info
    
    # Verificar se a lâmina tem comprimento suficiente
    if sabre['comprimento_atual'] <= 10:  # Só causa dano se a lâmina estiver bem estendida
        return inimigos_atingidos
    
    # CORREÇÃO: Usar apenas a parte da LÂMINA, não incluir o cabo
    cabo_x, cabo_y = sabre['pos_cabo']
    ponta_x, ponta_y = sabre['pos_ponta']
    
    # Calcular o ponto onde a lâmina começa (emissor, não o cabo)
    angulo = sabre['angulo']
    tamanho_cabo = 15  # Tamanho aproximado do cabo
    
    # Início da lâmina (após o cabo/emissor)
    lamina_inicio_x = cabo_x + math.cos(angulo) * tamanho_cabo
    lamina_inicio_y = cabo_y + math.sin(angulo) * tamanho_cabo
    
    # A lâmina vai do emissor até a ponta
    linha_inicio = (lamina_inicio_x, lamina_inicio_y)
    linha_fim = (ponta_x, ponta_y)
    
    for inimigo in inimigos:
        if inimigo.vidas <= 0:
            continue
            
        # Verificar se o inimigo está próximo APENAS da lâmina de energia
        centro_inimigo = (
            inimigo.x + inimigo.tamanho // 2,
            inimigo.y + inimigo.tamanho // 2
        )
        
        # Calcular distância do centro do inimigo à linha da LÂMINA (não cabo)
        distancia = distancia_ponto_linha(centro_inimigo, linha_inicio, linha_fim)
        
        # Raio de hit mais restrito para apenas a lâmina
        raio_hit = 8 + inimigo.tamanho // 4  # Reduzido para ser mais preciso
        
        if distancia <= raio_hit:
            # Verificar se o dano pode ser aplicado (cooldown)
            tempo_atual = pygame.time.get_ticks()
            
            # Verificar se este inimigo já foi atingido recentemente
            if not hasattr(inimigo, 'ultimo_dano_sabre'):
                inimigo.ultimo_dano_sabre = 0
            
            # Cooldown de 500ms entre danos do sabre no mesmo inimigo
            if tempo_atual - inimigo.ultimo_dano_sabre >= 500:
                inimigo.ultimo_dano_sabre = tempo_atual

                # Aplicar dano (3 de dano)
                if inimigo.tomar_dano(dano=3):
                    inimigos_atingidos.append(inimigo)
                    
                    # Efeitos visuais do corte
                    if particulas is not None:
                        for _ in range(15):
                            particula_x = centro_inimigo[0] + random.uniform(-10, 10)
                            particula_y = centro_inimigo[1] + random.uniform(-10, 10)
                            
                            # Partículas de corte de energia
                            from src.entities.particula import Particula
                            particula = Particula(particula_x, particula_y, (200, 230, 255))
                            particula.velocidade_x = random.uniform(-5, 5)
                            particula.velocidade_y = random.uniform(-5, 5)
                            particula.vida = random.randint(10, 20)
                            particula.tamanho = random.uniform(2, 5)
                            particulas.append(particula)
                    
                    if flashes is not None:
                        # Flash de corte
                        flash = {
                            'x': centro_inimigo[0],
                            'y': centro_inimigo[1],
                            'raio': 20,
                            'vida': 12,
                            'cor': (150, 200, 255)
                        }
                        flashes.append(flash)
                    
                    # Som de corte do sabre
                    from src.utils.sound import gerar_som_explosao
                    som_corte = pygame.mixer.Sound(gerar_som_explosao())
                    som_corte.set_volume(0.2)
                    pygame.mixer.Channel(4).play(som_corte)
    
    return inimigos_atingidos
def processar_deflexao_tiros(jogador, tiros_inimigo, particulas=None, flashes=None):
    """
    Processa a deflexão de tiros pelos sabre de luz.
    
    Args:
        jogador: Objeto do jogador
        tiros_inimigo: Lista de tiros dos inimigos
        particulas: Lista de partículas para efeitos
        flashes: Lista de flashes para efeitos
        
    Returns:
        Lista de tiros refletidos
    """
    tiros_refletidos = []
    
    if not hasattr(jogador, 'sabre_info') or not jogador.sabre_info['ativo']:
        return tiros_refletidos
    
    sabre = jogador.sabre_info
    
    for tiro in tiros_inimigo[:]:
        if verificar_colisao_sabre_tiro(sabre, tiro):
            # Calcular nova direção
            nova_dx, nova_dy = calcular_angulo_reflexao(tiro, sabre)
            
            # Criar tiro refletido
            from src.entities.tiro import Tiro
            tiro_refletido = Tiro(
                tiro.x, tiro.y, 
                nova_dx, nova_dy,
                AZUL,  # Cor azul para tiros refletidos
                tiro.velocidade + 2  # Ligeiramente mais rápido
            )
            tiros_refletidos.append(tiro_refletido)
            
            # Efeitos visuais da deflexão
            if particulas is not None:
                for _ in range(8):
                    from src.entities.particula import Particula
                    particula = Particula(tiro.x, tiro.y, (150, 200, 255))
                    particula.velocidade_x = random.uniform(-3, 3)
                    particula.velocidade_y = random.uniform(-3, 3)
                    particula.vida = random.randint(8, 15)
                    particula.tamanho = random.uniform(2, 4)
                    particulas.append(particula)
            
            if flashes is not None:
                flash = {
                    'x': tiro.x,
                    'y': tiro.y,
                    'raio': 12,
                    'vida': 8,
                    'cor': (200, 220, 255)
                }
                flashes.append(flash)
            
            # Remover tiro original
            tiros_inimigo.remove(tiro)
            
            # Som de deflexão
            from src.utils.sound import gerar_som_tiro
            som_deflexao = gerar_som_tiro()
            som = pygame.mixer.Sound(som_deflexao)
            som.set_volume(0.15)
            pygame.mixer.Channel(7).play(som)
    
    return tiros_refletidos


def desenhar_sabre_arremessado(tela, jogador, tempo_atual):
    """
    Desenha o sabre de luz arremessado girando no ar como um boomerang.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos
    """
    if not hasattr(jogador, 'sabre_info'):
        return

    sabre = jogador.sabre_info

    if not sabre.get('arremessado', False):
        return

    # Posição e rotação do sabre
    pos_x = sabre['arremesso_pos_x']
    pos_y = sabre['arremesso_pos_y']
    rotacao = math.radians(sabre['arremesso_rotacao'])

    # Cores da lâmina (azul brilhante)
    cor_lamina_core = (200, 230, 255)
    cor_lamina_edge = (50, 150, 255)
    cor_lamina_glow = (100, 200, 255)
    cor_cabo_metal = (150, 150, 160)

    # Dimensões
    comprimento_lamina = 90
    comprimento_cabo = 25
    largura_lamina = 6

    # Calcular posições rotacionadas
    cos_r = math.cos(rotacao)
    sin_r = math.sin(rotacao)

    # Calcular pontos da lâmina
    cabo_inicio_x = -comprimento_cabo
    lamina_fim_x = comprimento_lamina

    p1_x = pos_x + cabo_inicio_x * cos_r
    p1_y = pos_y + cabo_inicio_x * sin_r
    p2_x = pos_x + lamina_fim_x * cos_r
    p2_y = pos_y + lamina_fim_x * sin_r

    # Desenhar borda da lâmina (SEM brilho azul ao redor)
    pygame.draw.line(tela, cor_lamina_edge, (p1_x, p1_y), (p2_x, p2_y), largura_lamina + 2)

    # Desenhar núcleo da lâmina
    pygame.draw.line(tela, cor_lamina_core, (p1_x, p1_y), (p2_x, p2_y), largura_lamina - 2)

    # Desenhar linha brilhante no centro
    pygame.draw.line(tela, (255, 255, 255), (p1_x, p1_y), (p2_x, p2_y), 2)

    # Desenhar cabo metálico no centro
    cabo_points = []
    largura_cabo = 8
    half_cabo = largura_cabo // 2

    for offset in [-half_cabo, half_cabo]:
        perp_x = -sin_r * offset
        perp_y = cos_r * offset

        # Início do cabo
        cabo_points.append((
            pos_x - comprimento_cabo * cos_r + perp_x,
            pos_y - comprimento_cabo * sin_r + perp_y
        ))

    for offset in [half_cabo, -half_cabo]:
        perp_x = -sin_r * offset
        perp_y = cos_r * offset

        # Fim do cabo
        cabo_points.append((
            pos_x + perp_x,
            pos_y + perp_y
        ))

    pygame.draw.polygon(tela, cor_cabo_metal, cabo_points)
    pygame.draw.polygon(tela, (100, 100, 110), cabo_points, 2)

def desenhar_sabre(tela, jogador, tempo_atual, pos_mouse):
    """
    Desenha o sabre de luz na posição do jogador com visual avançado estilo Star Wars.

    Args:
        tela: Superfície onde desenhar
        jogador: Objeto do jogador
        tempo_atual: Tempo atual em ms para efeitos
        pos_mouse: Posição do mouse para orientação
    """
    if not hasattr(jogador, 'sabre_info'):
        return

    sabre = jogador.sabre_info

    # Se estiver arremessado, desenhar versão girando
    if sabre.get('arremessado', False):
        desenhar_sabre_arremessado(tela, jogador, tempo_atual)
        return

    # Atualizar informações do sabre (modo normal)
    sabre_info = atualizar_sabre(jogador, pos_mouse, tempo_atual)
    
    cabo_x, cabo_y = sabre_info['pos_cabo']
    ponta_x, ponta_y = sabre_info['pos_ponta']
    angulo = sabre_info['angulo']
    
    # Cores do sabre de luz
    cor_cabo_metal = (150, 150, 160)
    cor_cabo_detalhes = (100, 100, 110)
    cor_ativador = (200, 50, 50)
    
    # Cores da lâmina (azul brilhante estilo Jedi) - sempre as mesmas
    cor_lamina_core = (200, 230, 255)  # Centro da lâmina
    cor_lamina_edge = (50, 150, 255)   # Borda da lâmina
    cor_lamina_glow = (100, 200, 255)  # Brilho externo
    
    # Animação de pulsação
    pulso = (math.sin(tempo_atual / 200) + 1) / 2
    vibracao = math.sin(tempo_atual / 50) * 0.5
    
    # Calcular vetores para orientação do cabo
    cos_a = math.cos(angulo)
    sin_a = math.sin(angulo)
    
    # Cabo do sabre
    cabo_comprimento = 25
    cabo_largura = 6
    
    # Calcular os 4 pontos do retângulo do cabo
    half_width = cabo_largura // 2
    half_length = cabo_comprimento // 2
    
    # Vetores perpendiculares para a largura
    perp_x = -sin_a * half_width
    perp_y = cos_a * half_width
    
    # Vetores paralelos para o comprimento
    para_x = cos_a * half_length
    para_y = sin_a * half_length
    
    # Calcular os 4 cantos do cabo
    cabo_points = [
        (cabo_x - para_x + perp_x, cabo_y - para_y + perp_y),  # canto 1
        (cabo_x + para_x + perp_x, cabo_y + para_y + perp_y),  # canto 2
        (cabo_x + para_x - perp_x, cabo_y + para_y - perp_y),  # canto 3
        (cabo_x - para_x - perp_x, cabo_y - para_y - perp_y)   # canto 4
    ]
    
    # Desenhar cabo principal
    pygame.draw.polygon(tela, cor_cabo_metal, cabo_points)
    pygame.draw.polygon(tela, cor_cabo_detalhes, cabo_points, 2)
    
    # Detalhes do cabo (anéis)
    for i in range(3):
        ring_pos = 0.2 + i * 0.3  # Posições ao longo do cabo
        ring_x = cabo_x + (ring_pos - 0.5) * cabo_comprimento * cos_a
        ring_y = cabo_y + (ring_pos - 0.5) * cabo_comprimento * sin_a
        
        # Desenhar anel como linha perpendicular
        ring_perp_x = -sin_a * (cabo_largura - 1)
        ring_perp_y = cos_a * (cabo_largura - 1)
        
        pygame.draw.line(tela, cor_cabo_detalhes,
                        (ring_x - ring_perp_x, ring_y - ring_perp_y),
                        (ring_x + ring_perp_x, ring_y + ring_perp_y), 2)
    
    # Botão ativador
    ativador_offset = cabo_comprimento * 0.3
    ativador_x = cabo_x + ativador_offset * cos_a + sin_a * 4
    ativador_y = cabo_y + ativador_offset * sin_a - cos_a * 4
    
    pygame.draw.circle(tela, cor_ativador, (int(ativador_x), int(ativador_y)), 3)
    pygame.draw.circle(tela, (255, 100, 100), (int(ativador_x), int(ativador_y)), 2)
    
    # Emissor da lâmina (na ponta do cabo)
    emissor_x = cabo_x + half_length * cos_a
    emissor_y = cabo_y + half_length * sin_a
    
    pygame.draw.circle(tela, (200, 200, 220), (int(emissor_x), int(emissor_y)), 4)
    pygame.draw.circle(tela, (100, 100, 120), (int(emissor_x), int(emissor_y)), 2)
    
    # Desenhar lâmina apenas se estiver ativa ou em animação
    if sabre_info['comprimento_atual'] > 0:
        # Calcular posição da ponta com vibração
        lamina_end_x = ponta_x + vibracao * sin_a
        lamina_end_y = ponta_y - vibracao * cos_a
        
        # Núcleo da lâmina (borda) - sempre o mesmo tamanho
        pygame.draw.line(tela, cor_lamina_edge, 
                        (emissor_x, emissor_y), 
                        (lamina_end_x, lamina_end_y), 6)
        
        # Núcleo da lâmina (centro brilhante)
        pygame.draw.line(tela, cor_lamina_core, 
                        (emissor_x, emissor_y), 
                        (lamina_end_x, lamina_end_y), 3)
        
        # Centro super brilhante
        pygame.draw.line(tela, (255, 255, 255), 
                        (emissor_x, emissor_y), 
                        (lamina_end_x, lamina_end_y), 1)
        
        # Efeito de faíscas na ponta
        if pulso > 0.7:
            for i in range(3):
                spark_x = lamina_end_x + random.uniform(-3, 3)
                spark_y = lamina_end_y + random.uniform(-3, 3)
                spark_size = random.randint(1, 2)
                pygame.draw.circle(tela, cor_lamina_core, (int(spark_x), int(spark_y)), spark_size)
        
        # Partículas de energia ao longo da lâmina
        for i in range(4):
            particle_progress = (i + 1) / 5
            particle_x = emissor_x + (lamina_end_x - emissor_x) * particle_progress
            particle_y = emissor_y + (lamina_end_y - emissor_y) * particle_progress
            particle_alpha = int(150 * pulso)
            
            if particle_alpha > 50:
                # Adicionar vibração às partículas
                particle_x += random.uniform(-1, 1)
                particle_y += random.uniform(-1, 1)
                pygame.draw.circle(tela, cor_lamina_glow, 
                                 (int(particle_x), int(particle_y)), 2)
        
        # Efeito de energia no emissor
        if random.random() < 0.3:  # 30% de chance por frame
            energy_size = random.randint(2, 4)
            energy_x = emissor_x + random.uniform(-2, 2)
            energy_y = emissor_y + random.uniform(-2, 2)
            pygame.draw.circle(tela, (150, 200, 255), (int(energy_x), int(energy_y)), energy_size)
            
def desenhar_icone_sabre_hud(tela, x, y, tempo_atual, ativo=False):
    """
    Desenha um ícone simplificado do sabre para o HUD com novo visual.
    
    Args:
        tela: Superfície onde desenhar
        x, y: Posição central do ícone
        tempo_atual: Tempo atual para animações
        ativo: Se o sabre está ativo
    """
    # Cores do sabre
    cor_cabo = (150, 150, 160)
    cor_cabo_detalhes = (100, 100, 110)
    cor_ativador = (200, 50, 50)
    
    if ativo:
        cor_lamina_core = (200, 230, 255)
        cor_lamina_edge = (50, 150, 255)
        cor_brilho = (255, 255, 255)
    else:
        cor_lamina_core = (60, 60, 80)
        cor_lamina_edge = (40, 40, 60)
        cor_brilho = (100, 100, 120)
    
    # Cabo (horizontal no HUD)
    cabo_rect = pygame.Rect(x - 8, y + 3, 16, 4)
    pygame.draw.rect(tela, cor_cabo, cabo_rect, 0, 2)
    pygame.draw.rect(tela, cor_cabo_detalhes, cabo_rect, 1, 2)
    
    # Detalhes do cabo
    for i in range(2):
        det_x = x - 4 + i * 4
        pygame.draw.line(tela, cor_cabo_detalhes, (det_x, y + 2), (det_x, y + 6), 1)
    
    # Botão ativador
    pygame.draw.circle(tela, cor_ativador, (x, y + 8), 2)
    
    # Emissor
    pygame.draw.circle(tela, (200, 200, 220), (x + 8, y + 5), 2)
    
    # Lâmina
    if ativo:
        # Efeito pulsante quando ativo
        pulso = (math.sin(tempo_atual / 150) + 1) / 2
        comprimento = int(12 + pulso * 2)
        
        # Brilho
        pygame.draw.line(tela, cor_lamina_edge, (x + 8, y + 5), (x + 8, y - comprimento), 4)
        pygame.draw.line(tela, cor_lamina_core, (x + 8, y + 5), (x + 8, y - comprimento), 2)
        pygame.draw.line(tela, cor_brilho, (x + 8, y + 5), (x + 8, y - comprimento), 1)
    else:
        # Lâmina apagada
        pygame.draw.line(tela, cor_lamina_core, (x + 8, y + 5), (x + 8, y - 8), 2).circle(tela, cor_cabo_detalhes, (x + i, y + 8), 1)