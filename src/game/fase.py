#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a lógica das fases do jogo.
"""

import pygame
import random
import math
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.visual import criar_estrelas, desenhar_texto
from src.utils.sound import gerar_som_explosao, gerar_som_dano
from src.game.nivel_factory import NivelFactory
from src.game.moeda_manager import MoedaManager
from src.config import ALTURA_JOGO
from src.utils.visual import desenhar_mira, criar_mira
from src.utils.visual import desenhar_texto, criar_texto_flutuante, criar_botao
from src.utils.visual import desenhar_estrelas, criar_estrelas
from src.ui import desenhar_hud
from src.entities.granada import Granada


def criar_inimigos(numero_fase):
    """
    Cria uma lista de inimigos para a fase especificada.
    
    Args:
        numero_fase: Número da fase atual (1, 2 ou 3)
        
    Returns:
        Lista de objetos Quadrado (inimigos)
    """
    inimigos = []
    
    return inimigos


def atualizar_IA_inimigo(inimigo, idx, jogador, tiros_jogador, inimigos, tempo_atual, tempo_movimento_inimigos, 
                        intervalo_movimento, numero_fase, tiros_inimigo, movimento_x, movimento_y, 
                        particulas=None, flashes=None):
    """
    Atualiza a IA de um inimigo específico com comportamento mais individualizado.
    
    Args:
        inimigo: O inimigo a ser atualizado
        idx: Índice do inimigo na lista
        jogador: Objeto do jogador
        tiros_jogador: Lista de tiros do jogador
        inimigos: Lista de todos os inimigos
        tempo_atual: Tempo atual em ms
        tempo_movimento_inimigos: Lista de timestamps do último movimento de cada inimigo
        intervalo_movimento: Intervalo entre decisões de movimento
        numero_fase: Número da fase atual
        tiros_inimigo: Lista onde adicionar novos tiros
        movimento_x, movimento_y: Direção de movimento do jogador
        particulas: Lista de partículas para efeitos visuais (opcional)
        flashes: Lista de flashes para efeitos visuais (opcional)

    Returns:
        A timestamp atualizada do último movimento para este inimigo
    """
    # Se o inimigo foi derrotado, pular
    if inimigo.vidas <= 0:
        return tempo_movimento_inimigos[idx]
    
    # Verificar se é um inimigo perseguidor
    if hasattr(inimigo, 'perseguidor') and inimigo.perseguidor:
        # Calcular vetor direto para o jogador
        dir_x = jogador.x - inimigo.x
        dir_y = jogador.y - inimigo.y
        dist = math.sqrt(dir_x**2 + dir_y**2)
        
        # Normalizar
        if dist > 0:
            dir_x /= dist
            dir_y /= dist
        
        # Verificar colisão com o jogador
        if inimigo.rect.colliderect(jogador.rect):
            # Verificar cooldown de colisão
            if tempo_atual - inimigo.tempo_ultima_colisao > inimigo.cooldown_colisao:
                # Causar dano ao jogador
                if jogador.tomar_dano():
                    # Atualizar tempo da última colisão
                    inimigo.tempo_ultima_colisao = tempo_atual
                    
                    # DIREÇÃO CORRIGIDA: Calcular vetor diretamente do inimigo para o jogador
                    dir_empurrar_x = jogador.x - inimigo.x
                    dir_empurrar_y = jogador.y - inimigo.y
                    
                    # Normalizar o vetor
                    dist_empurrar = math.sqrt(dir_empurrar_x**2 + dir_empurrar_y**2)
                    if dist_empurrar > 0:
                        dir_empurrar_x /= dist_empurrar
                        dir_empurrar_y /= dist_empurrar
                    
                    # Força do arremesso (quanto maior, mais longe o jogador vai)
                    forca_arremesso = 160
                    
                    # Calcular o deslocamento
                    recuo_x = dir_empurrar_x * forca_arremesso
                    recuo_y = dir_empurrar_y * forca_arremesso
                    
                    # Garantir que o recuo não empurre o jogador para fora da tela
                    nova_x = max(0, min(jogador.x + recuo_x, LARGURA - jogador.tamanho))
                    nova_y = max(0, min(jogador.y + recuo_y, ALTURA - jogador.tamanho))
                    
                    # Aplicar o recuo ao jogador
                    jogador.x = nova_x
                    jogador.y = nova_y
                    jogador.rect.x = jogador.x
                    jogador.rect.y = jogador.y
                    
                    # Tocar som de dano
                    pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                    
                    # Criar efeito visual apenas se as listas de partículas e flashes foram fornecidas
                    if particulas is not None and flashes is not None:
                        flash = criar_explosao(jogador.x + jogador.tamanho//2, 
                                            jogador.y + jogador.tamanho//2, 
                                            LARANJA, particulas, 25)
                        flashes.append(flash)
            
            # Recuar o inimigo um pouco após a colisão (para não ficar preso no jogador)
            inimigo.x -= dir_x * 15
            inimigo.y -= dir_y * 15
            inimigo.rect.x = inimigo.x
            inimigo.rect.y = inimigo.y
            
            # Sair da função, já que o inimigo colidiu e não precisa de movimento adicional
            return tempo_movimento_inimigos[idx]
        
        # Movimento constante em direção ao jogador
        mover_x = dir_x
        mover_y = dir_y
        
        # Verificar limites da tela
        if inimigo.x < 10 or inimigo.x > LARGURA - inimigo.tamanho - 10:
            mover_x = 0  # Evitar que fique preso nas bordas laterais
        if inimigo.y < 10 or inimigo.y > ALTURA - inimigo.tamanho - 10:
            mover_y = 0  # Evitar que fique preso nas bordas superior/inferior
        
        # Adicionar pequena variação para evitar movimento em linha reta perfeita
        mover_x += random.uniform(-0.1, 0.1)
        mover_y += random.uniform(-0.1, 0.1)
        
        # Normalizar o vetor de movimento
        magnitude = math.sqrt(mover_x**2 + mover_y**2)
        if magnitude > 0:
            mover_x /= magnitude
            mover_y /= magnitude
        
        # Executar o movimento
        inimigo.mover(mover_x, mover_y)
        inimigo.atualizar()
        
        # Retornar timestamp de movimento
        return tempo_movimento_inimigos[idx]
    
    # Adicionar variação com base no ID único do inimigo
    # Isso garantirá que mesmo inimigos do mesmo tipo tenham comportamentos diferentes
    inimigo_id = inimigo.id
    
    # Calcular um valor de offset para este inimigo específico
    offset_fator = (inimigo_id % 10) / 10.0  # Valor entre 0.0 e 0.9 com base no ID
    random_seed = (inimigo_id * tempo_atual) % 10000  # Semente única para este inimigo neste momento
    
    # Calcular vetor direção para o jogador
    dir_x = jogador.x - inimigo.x
    dir_y = jogador.y - inimigo.y
    dist = math.sqrt(dir_x**2 + dir_y**2)
    
    # Normalizar a direção se a distância não for zero
    if dist > 0:
        dir_x /= dist
        dir_y /= dist
    
    # Modificar o intervalo de movimento de cada inimigo com base em seu ID
    # Isso faz com que inimigos iguais atualizem seu movimento em momentos diferentes
    intervalo_ajustado = intervalo_movimento * (0.8 + offset_fator * 0.4)  # 80%-120% do valor original
    
    # Atualizar comportamento a cada intervalo ajustado
    if tempo_atual - tempo_movimento_inimigos[idx] > intervalo_ajustado + (idx * 100):
        tempo_movimento_inimigos[idx] = tempo_atual
        
        # Usar uma semente baseada no ID do inimigo para seu comportamento aleatório
        # Inicializar o gerador de números aleatórios com uma semente baseada no ID
        random_state = random.getstate()  # Salvar estado atual
        random.seed(random_seed)
        
        # Escolher comportamento baseado na situação e fase
        comportamentos = ["perseguir", "flanquear", "recuar", "evasivo"]
        pesos = [0.4, 0.3, 0.15, 0.15]
        
        # Modificar a preferência de comportamento baseado no ID do inimigo
        # Isso faz com que diferentes inimigos prefiram diferentes táticas
        if offset_fator < 0.3:  # 30% dos inimigos preferem perseguir
            pesos[0] += 0.2
            pesos[1] -= 0.1
            pesos[2] -= 0.1
        elif offset_fator < 0.6:  # 30% preferem flanquear
            pesos[0] -= 0.1
            pesos[1] += 0.2  
            pesos[3] -= 0.1
        else:  # 40% preferem comportamento evasivo ou recuar
            pesos[0] -= 0.2
            pesos[2] += 0.1
            pesos[3] += 0.1
            
        # Aumentar agressividade com o nível da fase
        pesos[0] += min(0.3, numero_fase * 0.03)  # Mais perseguição nas fases avançadas
        
        # Normalizar pesos
        soma = sum(pesos)
        pesos = [p/soma for p in pesos]
        
        # Chance de atirar baseada na distância e fase
        chance_tiro = min(0.9, 0.4 + (800 - dist) / 1000 + (numero_fase * 0.05))
        
        # Adicionar variação na decisão de tiro baseada no ID do inimigo
        chance_tiro = chance_tiro * (0.8 + offset_fator * 0.4)  # 80%-120% da chance original
        
        if random.random() < chance_tiro:
            # Calcular direção para o jogador com previsão de movimento
            dir_tiro_x = dir_x
            dir_tiro_y = dir_y
            
            # Adicionar previsão simples (mirar um pouco à frente)
            # Inimigos diferentes terão níveis diferentes de previsão
            fator_previsao = 0.3 * (1.0 + offset_fator)  # 0.3 a 0.57
            if abs(movimento_x) > 0 or abs(movimento_y) > 0:
                dir_tiro_x += movimento_x * fator_previsao
                dir_tiro_y += movimento_y * fator_previsao
            
            # Normalizar novamente
            norm = math.sqrt(dir_tiro_x**2 + dir_tiro_y**2)
            if norm > 0:
                dir_tiro_x /= norm
                dir_tiro_y /= norm
            
            # Reduzir imprecisão em fases avançadas
            # Inimigos diferentes terão níveis diferentes de precisão
            fator_precisao = 1.0 - offset_fator * 0.5  # 0.5-1.0
            imprecisao = max(0.05, min(0.4, (dist / 1000 - (numero_fase * 0.02)) * fator_precisao))
            dir_tiro_x += random.uniform(-imprecisao, imprecisao)
            dir_tiro_y += random.uniform(-imprecisao, imprecisao)
            
            inimigo.atirar(tiros_inimigo, (dir_tiro_x, dir_tiro_y))
        
        # Restaurar o estado original do gerador de números aleatórios
        random.setstate(random_state)
    
    # Definir zona de segurança das bordas (mais ampla que antes)
    margem_borda = 100
    
    # Definir zona crítica das bordas (muito perto da borda)
    zona_critica = 40
    
    # Verificar se o inimigo está na zona de segurança das bordas
    perto_da_borda = (inimigo.x < margem_borda or 
                      inimigo.x > LARGURA - inimigo.tamanho - margem_borda or
                      inimigo.y < margem_borda or 
                      inimigo.y > ALTURA - inimigo.tamanho - margem_borda)
    
    # Verificar se o inimigo está na zona crítica das bordas
    muito_perto_da_borda = (inimigo.x < zona_critica or 
                           inimigo.x > LARGURA - inimigo.tamanho - zona_critica or
                           inimigo.y < zona_critica or 
                           inimigo.y > ALTURA - inimigo.tamanho - zona_critica)
    
    # Verificar se o jogador está perigosamente perto da borda
    jogador_perto_borda = (jogador.x < margem_borda or 
                          jogador.x > LARGURA - jogador.tamanho - margem_borda or
                          jogador.y < margem_borda or 
                          jogador.y > ALTURA - jogador.tamanho - margem_borda)
    
    # Inicializar o gerador de números aleatórios com uma semente baseada no ID
    random_state = random.getstate()  # Salvar estado atual
    random.seed(random_seed + tempo_atual // 1000)  # Mudar a cada segundo
    
    # Verificar proximidade com outros inimigos (evitar empilhamento)
    evitar_x, evitar_y = 0, 0
    for outro_idx, outro in enumerate(inimigos):
        if idx != outro_idx and outro.vidas > 0:
            dx = inimigo.x - outro.x
            dy = inimigo.y - outro.y
            dist_outro = math.sqrt(dx**2 + dy**2)
            
            if dist_outro < 80:  # Distância mínima entre inimigos
                forca = 1.0 - (dist_outro / 80)
                if dist_outro > 0:
                    evitar_x += dx / dist_outro * forca
                    evitar_y += dy / dist_outro * forca
    
    # Normalizar vetor de evasão
    mag_evitar = math.sqrt(evitar_x**2 + evitar_y**2)
    if mag_evitar > 0:
        evitar_x /= mag_evitar
        evitar_y /= mag_evitar
    
    # Detectar tiros próximos e tentar desviar
    tiro_mais_proximo = None
    dist_min = float('inf')
    
    for tiro in tiros_jogador:
        dx = tiro.x - inimigo.x
        dy = tiro.y - inimigo.y
        
        # Se o tiro está se aproximando
        if (tiro.dx > 0 and dx > 0) or (tiro.dx < 0 and dx < 0) or \
           (tiro.dy > 0 and dy > 0) or (tiro.dy < 0 and dy < 0):
            
            dist_tiro = math.sqrt(dx**2 + dy**2)
            
            if dist_tiro < dist_min and dist_tiro < 200:
                dist_min = dist_tiro
                tiro_mais_proximo = tiro
    
    # Determinar movimento principal
    mover_x, mover_y = 0, 0
    
    # PRIORIDADE 1: Zona Crítica - Se muito perto da borda, movimento forte em direção ao centro
    if muito_perto_da_borda:
        centro_x, centro_y = LARGURA / 2, ALTURA / 2
        
        # Calcular vetor para o centro
        para_centro_x = centro_x - inimigo.x
        para_centro_y = centro_y - inimigo.y
        
        # Normalizar
        dist_centro = math.sqrt(para_centro_x**2 + para_centro_y**2)
        if dist_centro > 0:
            mover_x = para_centro_x / dist_centro * 1.5  # Força forte para o centro
            mover_y = para_centro_y / dist_centro * 1.5
            
            # Adicionar variação para que inimigos do mesmo tipo não se movam identicamente
            mover_x += random.uniform(-0.2, 0.2) * offset_fator
            mover_y += random.uniform(-0.2, 0.2) * offset_fator
    
    # PRIORIDADE 2: Evite tiros próximos
    elif tiro_mais_proximo is not None:
        # Movimento evasivo - perpendicular à direção do tiro
        vetor_perp_x = -tiro_mais_proximo.dy
        vetor_perp_y = tiro_mais_proximo.dx
        
        # Garantir que estamos indo para longe do tiro
        dot_product = vetor_perp_x * (tiro_mais_proximo.x - inimigo.x) + \
                      vetor_perp_y * (tiro_mais_proximo.y - inimigo.y)
        
        if dot_product > 0:
            vetor_perp_x = -vetor_perp_x
            vetor_perp_y = -vetor_perp_y
        
        # Se estiver perto da borda, considere isso ao desviar
        if perto_da_borda and not muito_perto_da_borda:
            # Aplicar um viés para o centro
            centro_x, centro_y = LARGURA / 2, ALTURA / 2
            para_centro_x = centro_x - inimigo.x
            para_centro_y = centro_y - inimigo.y
            
            # Normalizar
            dist_centro = math.sqrt(para_centro_x**2 + para_centro_y**2)
            if dist_centro > 0:
                para_centro_x /= dist_centro
                para_centro_y /= dist_centro
            
            # Combinar os vetores (% baseado no ID do inimigo)
            fator_evasao = 0.7 - offset_fator * 0.2  # 0.5-0.7
            mover_x = vetor_perp_x * fator_evasao + para_centro_x * (1 - fator_evasao)
            mover_y = vetor_perp_y * fator_evasao + para_centro_y * (1 - fator_evasao)
        else:
            mover_x = vetor_perp_x
            mover_y = vetor_perp_y
            
        # Adicionar variação para que inimigos não se movam de forma idêntica
        mover_x += random.uniform(-0.2, 0.2) * offset_fator
        mover_y += random.uniform(-0.2, 0.2) * offset_fator
    
    # PRIORIDADE 3: Comportamento normal baseado na situação
    elif not perto_da_borda or (jogador_perto_borda and inimigo.x > margem_borda and 
                               inimigo.x < LARGURA - inimigo.tamanho - margem_borda and
                               inimigo.y > margem_borda and 
                               inimigo.y < ALTURA - inimigo.tamanho - margem_borda):
        # Comportamento tático adaptado à distância do jogador
        if dist < 300:  # Muito perto
            # Modificar a chance com base no ID do inimigo
            recuar_chance = 0.7 + (offset_fator - 0.5) * 0.4  # 0.5-0.9 dependendo do ID
            if random.random() < recuar_chance:  # Às vezes recuar
                mover_x = -dir_x * (0.8 + offset_fator * 0.4)  # Velocidade de recuo variável
                mover_y = -dir_y * (0.8 + offset_fator * 0.4)
            else:  # Movimento lateral para flanquear
                # Cada inimigo prefere um lado diferente para flanquear
                if offset_fator > 0.5:
                    mover_x = dir_y
                    mover_y = -dir_x
                else:
                    mover_x = -dir_y
                    mover_y = dir_x
        elif dist > 500:  # Muito longe
            # Aproximar do jogador com velocidade variável
            fator_aprox = 1.0 + (offset_fator - 0.5) * 0.6  # 0.7-1.3
            mover_x = dir_x * fator_aprox
            mover_y = dir_y * fator_aprox
        else:  # Distância média
            # Movimento estratégico: circular ao redor do jogador
            # Direção de circular variável com o ID
            if offset_fator > 0.5:
                mover_x = dir_y * 0.8
                mover_y = -dir_x * 0.8
            else:
                mover_x = -dir_y * 0.8
                mover_y = dir_x * 0.8
            
            # Com chance de se aproximar ou afastar
            aprox_chance = 0.3 + (offset_fator - 0.5) * 0.2  # 0.2-0.4
            if random.random() < aprox_chance:
                mover_x += dir_x * (0.3 + offset_fator * 0.1)  # 0.3-0.4
                mover_y += dir_y * (0.3 + offset_fator * 0.1)
    
    # PRIORIDADE 4: Perto da borda mas não na zona crítica
    else:
        # Calcular vetor para o centro da tela
        centro_x, centro_y = LARGURA / 2, ALTURA / 2
        
        # Se o jogador está longe da borda, podemos ter como alvo o jogador ao invés do centro
        if not jogador_perto_borda:
            centro_x = jogador.x
            centro_y = jogador.y
            
        para_centro_x = centro_x - inimigo.x
        para_centro_y = centro_y - inimigo.y
        
        # Normalizar
        dist_centro = math.sqrt(para_centro_x**2 + para_centro_y**2)
        if dist_centro > 0:
            para_centro_x /= dist_centro
            para_centro_y /= dist_centro
            
        # Aplicar um fator multiplicador baseado na proximidade da borda
        # Variável com base no ID do inimigo
        fator_borda = 0.6 + (offset_fator - 0.5) * 0.2  # 0.5-0.7
        mover_x = para_centro_x * fator_borda
        mover_y = para_centro_y * fator_borda
    
    # Adicionar componente para evitar outros inimigos
    mover_x += evitar_x * (0.5 + offset_fator * 0.2)  # 0.5-0.7
    mover_y += evitar_y * (0.5 + offset_fator * 0.2)
    
    # Adicionar um pouco de aleatoriedade ao movimento (menos quando perto da borda)
    aleatoriedade_base = 0.05 if muito_perto_da_borda else (0.1 if perto_da_borda else 0.2)
    # Variável com base no ID do inimigo
    aleatoriedade = aleatoriedade_base * (1.0 + offset_fator * 0.5)  # 50% mais ou menos aleatório
    mover_x += random.uniform(-aleatoriedade, aleatoriedade)
    mover_y += random.uniform(-aleatoriedade, aleatoriedade)
    
    # Verificar se o movimento nos levaria para dentro da borda
    nova_x = inimigo.x + mover_x * inimigo.velocidade
    nova_y = inimigo.y + mover_y * inimigo.velocidade
    
    # Se o movimento nos levaria para fora, inverta a direção
    if nova_x < zona_critica or nova_x > LARGURA - inimigo.tamanho - zona_critica:
        mover_x = -mover_x
    
    if nova_y < zona_critica or nova_y > ALTURA - inimigo.tamanho - zona_critica:
        mover_y = -mover_y
    
    # Normalizar o vetor de movimento
    magnitude = math.sqrt(mover_x**2 + mover_y**2)
    if magnitude > 0:
        mover_x /= magnitude
        mover_y /= magnitude
    
    # IMPORTANTE: movimento suavizado - isso evita tremores bruscos
    # Não alterar a velocidade quando estiver na zona crítica para permitir escape rápido
    velocidade_atual = inimigo.velocidade if muito_perto_da_borda else inimigo.velocidade * (0.8 + offset_fator * 0.1)
    
    # Restaurar o estado original do gerador de números aleatórios
    random.setstate(random_state)
    
    # Executar o movimento
    inimigo.mover(mover_x, mover_y)
    inimigo.atualizar()
    
    return tempo_movimento_inimigos[idx]


def jogar_fase(tela, relogio, numero_fase, gradiente_jogo, fonte_titulo, fonte_normal):
    """
    Executa uma fase específica do jogo.
    
    Args:
        tela: Superfície principal do jogo
        relogio: Objeto Clock para controle de FPS
        numero_fase: Número da fase a jogar
        gradiente_jogo: Superfície com o gradiente de fundo do jogo
        fonte_titulo: Fonte para títulos
        fonte_normal: Fonte para textos normais
        
    Returns:
        Tupla (resultado, pontuacao):
            - resultado: True se a fase foi completada, False se o jogador perdeu
            - pontuacao: Pontuação obtida nessa fase
    """
    # Criar jogador
    jogador = Quadrado(100, ALTURA_JOGO // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)
    
    # Criar fontes
    fonte_pequena = pygame.font.SysFont("Arial", 18)  # Fonte pequena para o HUD
    
    # Criar inimigos
    inimigos = NivelFactory.criar_fase(numero_fase)    
    moeda_manager = MoedaManager()

    # Listas para tiros, granadas e partículas
    tiros_jogador = []
    tiros_inimigo = []
    particulas = []     
    flashes = []
    granadas = []  # Nova lista para as granadas
    
    # Flag para pausa
    pausado = False
    
    # Flag para controle de morte
    jogador_morto = False
    
    # Controles de movimento
    movimento_x = 0
    movimento_y = 0
    
    # Tempos para a IA dos inimigos
    tempo_movimento_inimigos = [0] * len(inimigos)
    intervalo_movimento = max(300, 600 - numero_fase * 30)  # Reduz com a fase
    
    # Criar estrelas para o fundo
    estrelas = criar_estrelas(NUM_ESTRELAS_JOGO)
    
    # Efeito de início de fase
    fade_in = 255
    
    # Mostrar texto de início de fase
    mostrando_inicio = True
    contador_inicio = 120  # 2 segundos a 60 FPS
    
    # Atraso para tela de vitória
    tempo_transicao_vitoria = None  # Será definido quando o último inimigo for derrotado
    duracao_transicao_vitoria = 180  # 3 segundos a 60 FPS
    
    # Atraso para tela de derrota
    tempo_transicao_derrota = None  # Será definido quando o jogador perder
    duracao_transicao_derrota = 120  # 2 segundos a 60 FPS
    
    # Tempo de congelamento no início da fase (IMPORTANTE: Definir isso ANTES de usar)
    tempo_congelamento = 240  # 4 segundos a 60 FPS
    em_congelamento = False  # Será ativado após a introdução
    
    # Cursor do mouse visível durante o jogo
    pygame.mouse.set_visible(False)  # Esconder o cursor padrão do sistema

    # Criar mira personalizada
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)
    intervalo_minimo_clique = 100  # milissegundos

    # Rectangle for pause menu button
    rect_menu_pausado = None
    ultimo_clique_mouse = 0
    
    # Contador para evitar múltiplos lançamentos de granada
    tempo_ultimo_lancamento_granada = 0
    intervalo_lancamento_granada = 500  # Milissegundos entre lançamentos

# Loop principal da fase
    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()
        
        # Mostrar/ocultar cursor dependendo do estado
        if not mostrando_inicio and not pausado:
            pygame.mouse.set_visible(False)  # Ocultar apenas durante o jogo ativo
        else:
            pygame.mouse.set_visible(True)   # Mostrar nos menus/pausa/início
        
        # Obter a posição atual do mouse para o sistema de mira
        pos_mouse = pygame.mouse.get_pos()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            
            # Controles do teclado para o jogador (quando não estiver na introdução, pausado, morto ou congelado)
            if not mostrando_inicio and not pausado and not jogador_morto and not em_congelamento:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_w:
                        movimento_y = -1
                    if evento.key == pygame.K_s:
                        movimento_y = 1
                    if evento.key == pygame.K_a:
                        movimento_x = -1
                    if evento.key == pygame.K_d:
                        movimento_x = 1

                    if evento.key == pygame.K_ESCAPE:
                        pausado = True
                        pygame.mixer.pause()
                        pygame.mouse.set_visible(True)
               


                # Parar o movimento quando soltar as teclas
                if evento.type == pygame.KEYUP:
                    if evento.key == pygame.K_w and movimento_y < 0:
                        movimento_y = 0
                    if evento.key == pygame.K_s and movimento_y > 0:
                        movimento_y = 0
                    if evento.key == pygame.K_a and movimento_x < 0:
                        movimento_x = 0
                    if evento.key == pygame.K_d and movimento_x > 0:
                        movimento_x = 0
                    
                    
                    # Tecla para ativar/desativar espingarda (E)
                    if evento.key == pygame.K_e:
                        # Verificar se o jogador já comprou o upgrade da espingarda
                        if hasattr(jogador, 'tiros_espingarda'):
                            if jogador.tiros_espingarda > 0:
                                jogador.espingarda_ativa = not jogador.espingarda_ativa
                                jogador.granada_selecionada = False  # Desativar granada ao selecionar espingarda
                                # Mostrar mensagem de ativação/desativação


                            elif jogador._carregar_upgrade_espingarda() > 0:
                                # Jogador comprou o upgrade, mas já usou todos os tiros desta partida
                                criar_texto_flutuante("SEM TIROS DE ESPINGARDA RESTANTES!", 
                                                    LARGURA // 2, ALTURA // 4, 
                                                    VERMELHO, particulas, 120, 32)
                                # Se nunca comprou a espingarda, não mostra mensagem alguma
                    
                    # Tecla para ativar/desativar granada (Q)
                    if evento.key == pygame.K_q:
                        # Alternar modo de granada
                        if hasattr(jogador, 'granadas'):
                            if jogador.granadas > 0:
                                jogador.granada_selecionada = not jogador.granada_selecionada
                                jogador.espingarda_ativa = False  # Desativar espingarda ao selecionar granada
                                
                                # Mostrar mensagem de ativação/desativação

                            elif jogador._carregar_upgrade_granada() > 0:
                                # Jogador comprou o upgrade, mas já usou todas as granadas desta partida
                                criar_texto_flutuante("SEM GRANADAS RESTANTES!", 
                                                    LARGURA // 2, ALTURA // 4, 
                                                    VERMELHO, particulas, 120, 32)
                

                
                # Tiro com o botão esquerdo do mouse (apenas se não estiver morto ou congelado)
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Verificar se passou tempo suficiente desde o último clique
                    if tempo_atual - ultimo_clique_mouse >= intervalo_minimo_clique:
                        ultimo_clique_mouse = tempo_atual
                        
                        if jogador.granada_selecionada and jogador.granadas > 0:
                            # Verificar intervalo entre lançamentos de granadas
                            if tempo_atual - tempo_ultimo_lancamento_granada >= intervalo_lancamento_granada:
                                tempo_ultimo_lancamento_granada = tempo_atual
                                jogador.lancar_granada(granadas, pos_mouse, particulas, flashes)
                        elif jogador.espingarda_ativa and jogador.tiros_espingarda > 0:
                            # Verificar cooldown do jogador
                            if tempo_atual - jogador.tempo_ultimo_tiro >= jogador.tempo_cooldown:
                                jogador.atirar_espingarda(tiros_jogador, pos_mouse, particulas, flashes)
                                jogador.tiros_espingarda -= 1
                                # Desativar espingarda se acabaram os tiros
                                if jogador.tiros_espingarda <= 0:
                                    jogador.espingarda_ativa = False
                                    criar_texto_flutuante("SEM TIROS DE ESPINGARDA!", 
                                                        LARGURA // 2, ALTURA // 4, 
                                                        VERMELHO, particulas, 120, 32)
                        else:
                            # Atirar normal (já tem verificação de cooldown na função)
                            jogador.atirar_com_mouse(tiros_jogador, pos_mouse)
            
            # Handle pause menu controls
            elif pausado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        pausado = False
                        pygame.mixer.unpause()
                        pygame.mouse.set_visible(False)

                
                # Handle mouse clicks while paused
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if rect_menu_pausado and rect_menu_pausado.collidepoint(mouse_pos):
                        return "menu"
            

        
        # Atualizar contador de introdução
        if mostrando_inicio:
            contador_inicio -= 1
            if contador_inicio <= 0:
                mostrando_inicio = False
                em_congelamento = True  # Inicia o congelamento após a introdução
            
            # Preencher toda a tela com preto antes de desenhar qualquer coisa
            tela.fill((0, 0, 0))
            
            # Desenhar tela de introdução
            tela.blit(gradiente_jogo, (0, 0))
            
            # Desenhar estrelas
            for estrela in estrelas:
                x, y, tamanho, brilho, _ = estrela
                pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
            
            # Texto de introdução com efeito
            tamanho = 70 + int(math.sin(tempo_atual / 200) * 5)
            desenhar_texto(tela, f"FASE {numero_fase}", tamanho, BRANCO, LARGURA // 2, ALTURA_JOGO // 3)
            desenhar_texto(tela, f"{len(inimigos)} inimigo{'s' if len(inimigos) > 1 else ''} para derrotar", 36, 
                        AMARELO, LARGURA // 2, ALTURA_JOGO // 2)
            desenhar_texto(tela, "Preparado?", 30, BRANCO, LARGURA // 2, ALTURA_JOGO * 2 // 3)            
            pygame.display.flip()
            relogio.tick(FPS)
            continue

# Lógica de congelamento
        if em_congelamento:
            tempo_congelamento -= 1
            
            # Durante o congelamento, apenas desenha sem atualizar
            tela.fill((0, 0, 0))
            tela.blit(gradiente_jogo, (0, 0))
            
            # Desenhar estrelas (paradas)
            desenhar_estrelas(tela, estrelas)
            
            # Desenhar grid de fundo
            for i in range(0, LARGURA, 50):
                pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA_JOGO), 1)
            for i in range(0, ALTURA_JOGO, 50):
                pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
            
            # Desenhar jogador e inimigos (sem movimento)
            if jogador.vidas > 0:
                jogador.desenhar(tela)
            for inimigo in inimigos:
                if inimigo.vidas > 0:
                    inimigo.desenhar(tela)
            
            # Desenhar timer de congelamento
            segundos_restantes = max(0, tempo_congelamento // FPS)
            cor_timer = AMARELO if segundos_restantes > 0 else VERDE
            desenhar_texto(tela, f"PREPARAR: {segundos_restantes}", 50, cor_timer, 
                          LARGURA // 2, ALTURA_JOGO // 2)
            
            # Desenhar HUD
            desenhar_hud(tela, numero_fase, inimigos, tempo_atual, moeda_manager)
            
            # Quando o congelamento terminar
            if tempo_congelamento <= 0:
                em_congelamento = False
            
            pygame.display.flip()
            relogio.tick(FPS)
            continue
            
        # Efeito de fade in no início da fase
        if fade_in > 0:
            fade_in = max(0, fade_in - 10)
        
        # Se o jogo estiver pausado, pular a atualização
        if pausado:
            # Preencher toda a tela com preto antes de desenhar qualquer coisa
            tela.fill((0, 0, 0))
            
            # Desenhar mensagem de pausa com efeito transparente
            overlay = pygame.Surface((LARGURA, ALTURA))
            overlay.fill((0, 0, 20))
            overlay.set_alpha(180)
            tela.blit(overlay, (0, 0))
            
            # Desenhar PAUSADO
            desenhar_texto(tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 - 50)
            desenhar_texto(tela, "Pressione ESC para continuar", 30, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 20)
            
            # Create Menu button
            largura_menu = 250
            altura_menu = 50
            x_menu = LARGURA // 2
            y_menu = ALTURA_JOGO // 2 + 100
            
            # Scale adjustments
            escala_y = ALTURA / 848
            largura_ajustada_menu = int(largura_menu * escala_y)
            altura_ajustada_menu = int(altura_menu * escala_y)
            rect_menu_pausado = pygame.Rect(x_menu - largura_ajustada_menu // 2, 
                                           y_menu - altura_ajustada_menu // 2, 
                                           largura_ajustada_menu, 
                                           altura_ajustada_menu)
            
            # Draw the menu button
            hover_menu = criar_botao(tela, "VOLTAR AO MENU", x_menu, y_menu, 
                                    largura_menu, altura_menu, 
                                    (120, 60, 60), (180, 80, 80), BRANCO)
            
            pygame.display.flip()
            relogio.tick(FPS)
            continue

# Só atualiza se não estiver congelado
        if not em_congelamento:
            # Atualizar posição do jogador apenas se não estiver morto
            if not jogador_morto:
                jogador.mover(movimento_x, movimento_y)
                jogador.atualizar()
                
                # Garantir que o jogador não ultrapasse a área de jogo
                if jogador.y + jogador.tamanho > ALTURA_JOGO:
                    jogador.y = ALTURA_JOGO - jogador.tamanho
                    jogador.rect.y = jogador.y
            
            # Atualizar moedas e verificar colisões
            moeda_coletada = moeda_manager.atualizar(jogador)

                
            # Atualizar IA para cada inimigo
            for idx, inimigo in enumerate(inimigos):
                tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                    inimigo, idx, jogador, tiros_jogador, inimigos, tempo_atual, 
                    tempo_movimento_inimigos, intervalo_movimento, numero_fase, 
                    tiros_inimigo, movimento_x, movimento_y,
                    particulas, flashes  # Passando as listas como parâmetros
                )
                
                # Garantir que os inimigos não ultrapassem a área de jogo
                if inimigo.y + inimigo.tamanho > ALTURA_JOGO:
                    inimigo.y = ALTURA_JOGO - inimigo.tamanho
                    inimigo.rect.y = inimigo.y

# Atualizar tiros do jogador
            for tiro in tiros_jogador[:]:
                tiro.atualizar()
                
                # Verificar colisão com os inimigos
                for inimigo in inimigos:
                    if inimigo.vidas <= 0:
                        continue  # Ignorar inimigos derrotados
                    
                    if tiro.rect.colliderect(inimigo.rect):
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
                                    moedas_bonus = 5
                                elif inimigo.cor == CIANO:  # Inimigo ciano
                                    moedas_bonus = 8
                                elif inimigo.vidas_max > 1:  # Inimigos com múltiplas vidas
                                    moedas_bonus = 2
                                
                                # Adicionar moedas ao contador
                                moeda_manager.quantidade_moedas += moedas_bonus
                                moeda_manager.salvar_moedas()  # Salvar as moedas no arquivo
                                
                                # Criar animação de pontuação no local da morte
                                criar_texto_flutuante(f"+{moedas_bonus}", inimigo.x + inimigo.tamanho//5, 
                                                    inimigo.y, AMARELO, particulas)
                            
                            # Efeitos visuais de explosão
                            flash = criar_explosao(tiro.x, tiro.y, VERMELHO, particulas, 25)
                            flashes.append(flash)
                            pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
                        
                        tiros_jogador.remove(tiro)
                        break  # Sair do loop de inimigos após uma colisão
                
                # Se o tiro ainda existe, verificar se saiu da tela
                if tiro in tiros_jogador and tiro.fora_da_tela():
                    tiros_jogador.remove(tiro)
            
            # Atualizar tiros do inimigo
            for tiro in tiros_inimigo[:]:
                tiro.atualizar()
                
                # Verificar colisão com o jogador apenas se ele não estiver morto
                if not jogador_morto and tiro.rect.colliderect(jogador.rect):
                    if jogador.tomar_dano():
                        flash = criar_explosao(tiro.x, tiro.y, AZUL, particulas, 25)
                        flashes.append(flash)
                        pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                    tiros_inimigo.remove(tiro)
                    continue
                
                # Remover tiros que saíram da tela
                if tiro.fora_da_tela():
                    tiros_inimigo.remove(tiro)
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
            
            # Atualizar partículas
            for particula in particulas[:]:
                particula.atualizar()
                if particula.acabou():
                    particulas.remove(particula)

# Atualizar flashes
            for flash in flashes[:]:
                flash['vida'] -= 1
                flash['raio'] += 2
                if flash['vida'] <= 0:
                    flashes.remove(flash)
            
            # Atualizar estrelas
            for estrela in estrelas:
                estrela[0] -= estrela[4]  # Mover com base na velocidade
                if estrela[0] < 0:
                    estrela[0] = LARGURA
                    estrela[1] = random.randint(0, ALTURA_JOGO)  # Ajustado para usar ALTURA_JOGO
        
        # Verificar se todos os inimigos foram derrotados e tratar transição de vitória
        todos_derrotados = all(inimigo.vidas <= 0 for inimigo in inimigos)
        
        # Se todos os inimigos foram derrotados, tornar o jogador invulnerável
        if todos_derrotados:
            # Tornar o jogador invulnerável permanentemente
            jogador.invulneravel = True
            jogador.duracao_invulneravel = float('inf')  # Invulnerabilidade infinita
            
            # Iniciar contagem para transição se ainda não iniciou
            if tempo_transicao_vitoria is None:
                tempo_transicao_vitoria = duracao_transicao_vitoria
        
        # Se a contagem regressiva de vitória está ativa, decrementá-la
        if tempo_transicao_vitoria is not None:
            tempo_transicao_vitoria -= 1
            
            # Quando a contagem chegar a zero, concluir a fase
            if tempo_transicao_vitoria <= 0:
                return True  # Fase concluída com sucesso
        
        # Verificar condições de fim de fase
        if jogador.vidas <= 0:
            # Marcar o jogador como morto
            jogador_morto = True
            for inimigo in inimigos:
                inimigo.invulneravel = True
                inimigo.duracao_invulneravel = float('inf')
            # Iniciar contagem para transição de derrota se ainda não iniciou
            if tempo_transicao_derrota is None:
                tempo_transicao_derrota = duracao_transicao_derrota
                
                # Parar movimento do jogador
                movimento_x = 0
                movimento_y = 0
                
                # Criar explosões quando o jogador morrer
                for _ in range(5):
                    x = jogador.x + random.randint(-30, 30)
                    y = jogador.y + random.randint(-30, 30)
                    flash = criar_explosao(x, y, VERMELHO, particulas, 35)
                    flashes.append(flash)
                
                # Som de derrota
                pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_explosao()))
        
        # Se a contagem regressiva de derrota está ativa, decrementá-la
        if tempo_transicao_derrota is not None:
            tempo_transicao_derrota -= 1
            
            # Quando a contagem chegar a zero, ir para a tela de game over
            if tempo_transicao_derrota <= 0:
                return False # Jogador perdeu
# Desenhar fundo
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
        
        # Desenhar névoa colorida ondulante

            
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Desenhar grid de fundo
        for i in range(0, LARGURA, 50):
            pygame.draw.line(tela, (30, 30, 60), (i, 0), (i, ALTURA_JOGO), 1)
        for i in range(0, ALTURA_JOGO, 50):
            pygame.draw.line(tela, (30, 30, 60), (0, i), (LARGURA, i), 1)
        
        # Desenhar flashes
        for flash in flashes:
            if flash['y'] < ALTURA_JOGO:  # Só desenhar flashes na área de jogo
                pygame.draw.circle(tela, flash['cor'], (int(flash['x']), int(flash['y'])), int(flash['raio']))
        
        # Desenhar objetos do jogo
        if jogador.vidas > 0:
            jogador.desenhar(tela)
        
        # Desenhar inimigos ativos
        for inimigo in inimigos:
            if inimigo.vidas > 0:
                inimigo.desenhar(tela)
        
        for tiro in tiros_jogador:
            tiro.desenhar(tela)
        
        for tiro in tiros_inimigo:
            tiro.desenhar(tela)
        
        # Desenhar granadas
        for granada in granadas:
            granada.desenhar(tela)
        
        for particula in particulas:
            particula.desenhar(tela)
        
        # Desenhar moedas
        moeda_manager.desenhar(tela)
        
        # Desenhar HUD (pontuação, vidas e fase) na área dedicada
        desenhar_hud(tela, numero_fase, inimigos, tempo_atual, moeda_manager)
        
        # Aplicar efeito de fade-in (em toda a tela)
        if fade_in > 0:
            fade = pygame.Surface((LARGURA, ALTURA))
            fade.fill((0, 0, 0))
            fade.set_alpha(fade_in)
            tela.blit(fade, (0, 0))
# Desenhar mensagem de vitória durante a transição
        if tempo_transicao_vitoria is not None:
            # Criar um efeito de fade ou texto pulsante
            alpha = int(255 * (duracao_transicao_vitoria - tempo_transicao_vitoria) / duracao_transicao_vitoria)
            texto_surf = fonte_titulo.render("FASE CONCLUÍDA!", True, VERDE)
            texto_surf.set_alpha(alpha)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
            tela.blit(texto_surf, texto_rect)
            
            # Adicionar partículas de celebração aleatórias
            if random.random() < 0.2:  # 20% de chance por frame
                x = random.randint(0, LARGURA)
                y = random.randint(0, ALTURA_JOGO)
                cor = random.choice([VERDE, AMARELO, AZUL])
                flash = criar_explosao(x, y, cor, particulas, 15)
                flashes.append(flash)
        
        # Desenhar mensagem de derrota durante a transição
        if tempo_transicao_derrota is not None:
            # Criar um efeito de fade ou texto pulsante
            alpha = int(255 * (duracao_transicao_derrota - tempo_transicao_derrota) / duracao_transicao_derrota)
            texto_surf = fonte_titulo.render("DERROTADO!", True, VERMELHO)
            texto_surf.set_alpha(alpha)
            texto_rect = texto_surf.get_rect(center=(LARGURA // 2, ALTURA_JOGO // 2))
            tela.blit(texto_surf, texto_rect)
            
            # Adicionar efeito de tela vermelha
            overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
            overlay.fill(VERMELHO)
            overlay.set_alpha(int(50 * (duracao_transicao_derrota - tempo_transicao_derrota) / duracao_transicao_derrota))
            tela.blit(overlay, (0, 0))
            
            # Adicionar mais partículas de derrota
            if random.random() < 0.3:  # 30% de chance por frame
                x = jogador.x + random.randint(-50, 50)
                y = jogador.y + random.randint(-50, 50)
                criar_explosao(x, y, VERMELHO, particulas, 20)
        
# Desenhar mira personalizada do mouse apenas se não estiver congelado
        if not em_congelamento:
            desenhar_mira(tela, pos_mouse, (mira_surface, mira_rect))
        
        pygame.display.flip()
        relogio.tick(FPS)
    
    return False # Padrão: jogador saiu do jogo