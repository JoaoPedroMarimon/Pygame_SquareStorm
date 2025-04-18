#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a lógica das fases do jogo.
"""

import pygame
import random
import math
import sys
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.visual import criar_estrelas, desenhar_texto
from src.utils.sound import gerar_som_explosao, gerar_som_dano
from src.ui.hud import desenhar_tela_jogo, desenhar_transicao_fase
from src.game.nivel_factory import NivelFactory
from src.game.moeda_manager import MoedaManager  # Importar o MoedaManager



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
                        intervalo_movimento, numero_fase, tiros_inimigo, movimento_x, movimento_y):
    """
    Atualiza a IA de um inimigo específico.
    
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

    Returns:
        A timestamp atualizada do último movimento para este inimigo
    """
    # Se o inimigo foi derrotado, pular
    if inimigo.vidas <= 0:
        return tempo_movimento_inimigos[idx]
        
    # Calcular vetor direção para o jogador
    dir_x = jogador.x - inimigo.x
    dir_y = jogador.y - inimigo.y
    dist = math.sqrt(dir_x**2 + dir_y**2)
    
    # Normalizar a direção se a distância não for zero
    if dist > 0:
        dir_x /= dist
        dir_y /= dist
    
    # Atualizar comportamento a cada intervalo
    if tempo_atual - tempo_movimento_inimigos[idx] > intervalo_movimento + (idx * 100):
        tempo_movimento_inimigos[idx] = tempo_atual
        
        # Escolher comportamento baseado na situação e fase
        comportamentos = ["perseguir", "flanquear", "recuar", "evasivo"]
        pesos = [0.4, 0.3, 0.15, 0.15]
        
        # Aumentar agressividade com o nível da fase
        pesos[0] += min(0.3, numero_fase * 0.03)  # Mais perseguição nas fases avançadas
        
        # Normalizar pesos
        soma = sum(pesos)
        pesos = [p/soma for p in pesos]
        
        comportamento = random.choices(comportamentos, weights=pesos)[0]
        
        # Chance de atirar baseada na distância e fase
        chance_tiro = min(0.9, 0.4 + (800 - dist) / 1000 + (numero_fase * 0.05))
        
        if random.random() < chance_tiro:
            # Calcular direção para o jogador com previsão de movimento
            dir_tiro_x = dir_x
            dir_tiro_y = dir_y
            
            # Adicionar previsão simples (mirar um pouco à frente)
            if abs(movimento_x) > 0 or abs(movimento_y) > 0:
                dir_tiro_x += movimento_x * 0.3
                dir_tiro_y += movimento_y * 0.3
            
            # Normalizar novamente
            norm = math.sqrt(dir_tiro_x**2 + dir_tiro_y**2)
            if norm > 0:
                dir_tiro_x /= norm
                dir_tiro_y /= norm
            
            # Reduzir imprecisão em fases avançadas
            imprecisao = max(0.05, min(0.4, dist / 1000 - (numero_fase * 0.02)))
            dir_tiro_x += random.uniform(-imprecisao, imprecisao)
            dir_tiro_y += random.uniform(-imprecisao, imprecisao)
            
            inimigo.atirar(tiros_inimigo, (dir_tiro_x, dir_tiro_y))
    
    # Verificar se o inimigo está perto das bordas
    margem_borda = 80
    perto_da_borda = (inimigo.x < margem_borda or 
                     inimigo.x > LARGURA - inimigo.tamanho - margem_borda or
                     inimigo.y < margem_borda or 
                     inimigo.y > ALTURA - inimigo.tamanho - margem_borda)
    
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
    
    # Lógica de movimento baseada no comportamento, tiros e bordas
    if perto_da_borda:
        # Movimento para o centro quando está perto da borda
        mover_x = (LARGURA / 2 - inimigo.x) / dist if dist > 0 else 0
        mover_y = (ALTURA / 2 - inimigo.y) / dist if dist > 0 else 0
        
        # Mais forte se estiver muito perto da borda
        if inimigo.x < 30 or inimigo.x > LARGURA - inimigo.tamanho - 30 or \
           inimigo.y < 30 or inimigo.y > ALTURA - inimigo.tamanho - 30:
            mover_x *= 2
            mover_y *= 2
    else:
        # Verificar se há tiros próximos e tentar desviar
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
        
        if tiro_mais_proximo is not None:
            # Movimento evasivo - perpendicular à direção do tiro
            vetor_perp_x = -tiro_mais_proximo.dy
            vetor_perp_y = tiro_mais_proximo.dx
            
            # Garantir que estamos indo para longe do tiro
            dot_product = vetor_perp_x * (tiro_mais_proximo.x - inimigo.x) + \
                          vetor_perp_y * (tiro_mais_proximo.y - inimigo.y)
            
            if dot_product > 0:
                vetor_perp_x = -vetor_perp_x
                vetor_perp_y = -vetor_perp_y
            
            # Adicionar componente para se afastar do tiro
            mover_x = vetor_perp_x
            mover_y = vetor_perp_y
        else:
            # Comportamento normal quando não há tiros para desviar
            if dist < 300:  # Muito perto
                if random.random() < 0.7:  # Às vezes recuar
                    mover_x = -dir_x * 0.8
                    mover_y = -dir_y * 0.8
                else:  # Movimento lateral para flanquear
                    mover_x = dir_y
                    mover_y = -dir_x
            elif dist > 500:  # Muito longe
                # Aproximar do jogador
                mover_x = dir_x
                mover_y = dir_y
            else:  # Distância média
                # Movimento estratégico: circular ao redor do jogador
                mover_x = dir_y * 0.8
                mover_y = -dir_x * 0.8
                
                # Com chance de se aproximar ou afastar
                if random.random() < 0.3:
                    mover_x += dir_x * 0.3
                    mover_y += dir_y * 0.3
    
    # Adicionar componente para evitar outros inimigos
    mover_x += evitar_x * 0.5
    mover_y += evitar_y * 0.5
    
    # Adicionar um pouco de aleatoriedade ao movimento
    mover_x += random.uniform(-0.2, 0.2)
    mover_y += random.uniform(-0.2, 0.2)
    
    # Normalizar o vetor de movimento
    magnitude = math.sqrt(mover_x**2 + mover_y**2)
    if magnitude > 0:
        mover_x /= magnitude
        mover_y /= magnitude
    
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
    jogador = Quadrado(100, ALTURA // 2, TAMANHO_QUADRADO, AZUL, VELOCIDADE_JOGADOR)
    
    # Criar inimigos (quantidade = número da fase)
    inimigos = NivelFactory.criar_fase(numero_fase)    
    moeda_manager = MoedaManager()

    # Listas para tiros e partículas
    tiros_jogador = []
    tiros_inimigo = []
    particulas = []     
    flashes = []
    
    # Pontuação
    pontuacao = 0
    
    # Flag para pausa
    pausado = False
    
    # Controles de movimento
    movimento_x = 0
    movimento_y = 0
    
    # Tempos para a IA dos inimigos
    tempo_movimento_inimigos = [0] * numero_fase
    intervalo_movimento = max(300, 600 - numero_fase * 30)  # Reduz com a fase
    
    # Criar estrelas para o fundo
    estrelas = criar_estrelas(NUM_ESTRELAS_JOGO)
    
    # Efeito de início de fase
    fade_in = 255
    
    # Mostrar texto de início de fase
    mostrando_inicio = True
    contador_inicio = 120  # 2 segundos a 60 FPS
    
    # Loop principal da fase
    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False, pontuacao
            
            # Controles do teclado para o jogador (quando não estiver na introdução)
            if not mostrando_inicio:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_w:
                        movimento_y = -1
                    if evento.key == pygame.K_s:
                        movimento_y = 1
                    if evento.key == pygame.K_a:
                        movimento_x = -1
                    if evento.key == pygame.K_d:
                        movimento_x = 1
                    
                    # Atirar com as setas (nas diagonais e direções cardeais)
                    if evento.key == pygame.K_UP:
                        jogador.atirar(tiros_jogador, (0, -1))
                    if evento.key == pygame.K_DOWN:
                        jogador.atirar(tiros_jogador, (0, 1))
                    if evento.key == pygame.K_LEFT:
                        jogador.atirar(tiros_jogador, (-1, 0))
                    if evento.key == pygame.K_RIGHT:
                        jogador.atirar(tiros_jogador, (1, 0))
                    
                    # Tecla P para pausar
                    if evento.key == pygame.K_p:
                        pausado = not pausado
                        if pausado:
                            pygame.mixer.pause()
                        else:
                            pygame.mixer.unpause()
                    
                    # Tecla ESC para sair
                    if evento.key == pygame.K_ESCAPE:
                        return False, pontuacao
                
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
            else:
                # Durante a introdução, apenas ESC funciona
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return False, pontuacao
                    # Qualquer tecla avança a introdução
                    contador_inicio = 0
        
        # Atualizar contador de introdução
        if mostrando_inicio:
            contador_inicio -= 1
            if contador_inicio <= 0:
                mostrando_inicio = False
            
            # Desenhar tela de introdução
            tela.blit(gradiente_jogo, (0, 0))
            
            # Desenhar estrelas
            for estrela in estrelas:
                x, y, tamanho, brilho, _ = estrela
                pygame.draw.circle(tela, (brilho, brilho, brilho), (int(x), int(y)), int(tamanho))
            
            # Texto de introdução com efeito
            tamanho = 70 + int(math.sin(tempo_atual / 200) * 5)
            desenhar_texto(tela, f"FASE {numero_fase}", tamanho, BRANCO, LARGURA // 2, ALTURA // 3)
            desenhar_texto(tela, f"{numero_fase} inimigo{'s' if numero_fase > 1 else ''} para derrotar", 36, 
                           AMARELO, LARGURA // 2, ALTURA // 2)
            desenhar_texto(tela, "Preparado?", 30, BRANCO, LARGURA // 2, ALTURA * 2 // 3)
            desenhar_texto(tela, "Pressione qualquer tecla para começar", 24, BRANCO, LARGURA // 2, ALTURA * 3 // 4)
            
            pygame.display.flip()
            relogio.tick(FPS)
            continue
            
        # Efeito de fade in no início da fase
        if fade_in > 0:
            fade_in = max(0, fade_in - 10)
        
        # Se o jogo estiver pausado, pular a atualização
        if pausado:
            # Desenhar mensagem de pausa
            tela.fill((0, 0, 20))
            desenhar_texto(tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA // 2)
            desenhar_texto(tela, "Pressione P para continuar", 30, BRANCO, LARGURA // 2, ALTURA // 2 + 80)
            pygame.display.flip()
            relogio.tick(FPS)
            continue
        
        # Atualizar posição do jogador
        jogador.mover(movimento_x, movimento_y)
        jogador.atualizar()
        jogador.mover(movimento_x, movimento_y)
        jogador.atualizar()
        
        # Atualizar moedas e verificar colisões
        moeda_coletada = moeda_manager.atualizar(jogador)
        if moeda_coletada:
            # Adicionar pontos bônus ao coletar moedas
            pontuacao += 5
        # Atualizar IA para cada inimigo
        for idx, inimigo in enumerate(inimigos):
            if inimigo.vidas <= 0:
                continue  # Pular inimigos derrotados
                
            # Calcular vetor direção para o jogador
            dir_x = jogador.x - inimigo.x
            dir_y = jogador.y - inimigo.y
            dist = math.sqrt(dir_x**2 + dir_y**2)
            
            # Normalizar a direção se a distância não for zero
            if dist > 0:
                dir_x /= dist
                dir_y /= dist
            
            # Atualizar comportamento a cada intervalo
            if tempo_atual - tempo_movimento_inimigos[idx] > intervalo_movimento + (idx * 100):
                tempo_movimento_inimigos[idx] = tempo_atual
                
                # Escolher comportamento baseado na situação e fase
                comportamentos = ["perseguir", "flanquear", "recuar", "evasivo"]
                pesos = [0.4, 0.3, 0.15, 0.15]
                
                # Aumentar agressividade com o nível da fase
                pesos[0] += min(0.3, numero_fase * 0.03)  # Mais perseguição nas fases avançadas
                
                # Normalizar pesos
                soma = sum(pesos)
                pesos = [p/soma for p in pesos]
                
                comportamento = random.choices(comportamentos, weights=pesos)[0]
                
                # Chance de atirar baseada na distância e fase
                chance_tiro = min(0.9, 0.4 + (800 - dist) / 1000 + (numero_fase * 0.05))
                
                if random.random() < chance_tiro:
                    # Calcular direção para o jogador com previsão de movimento
                    dir_tiro_x = dir_x
                    dir_tiro_y = dir_y
                    
                    # Adicionar previsão simples (mirar um pouco à frente)
                    if abs(movimento_x) > 0 or abs(movimento_y) > 0:
                        dir_tiro_x += movimento_x * 0.3
                        dir_tiro_y += movimento_y * 0.3
                    
                    # Normalizar novamente
                    norm = math.sqrt(dir_tiro_x**2 + dir_tiro_y**2)
                    if norm > 0:
                        dir_tiro_x /= norm
                        dir_tiro_y /= norm
                    
                    # Reduzir imprecisão em fases avançadas
                    imprecisao = max(0.05, min(0.4, dist / 1000 - (numero_fase * 0.02)))
                    dir_tiro_x += random.uniform(-imprecisao, imprecisao)
                    dir_tiro_y += random.uniform(-imprecisao, imprecisao)
                    
                    inimigo.atirar(tiros_inimigo, (dir_tiro_x, dir_tiro_y))
            
            # Verificar se o inimigo está perto das bordas
            margem_borda = 80
            perto_da_borda = (inimigo.x < margem_borda or 
                             inimigo.x > LARGURA - inimigo.tamanho - margem_borda or
                             inimigo.y < margem_borda or 
                             inimigo.y > ALTURA - inimigo.tamanho - margem_borda)
            
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
            
            # Lógica de movimento baseada no comportamento, tiros e bordas
            if perto_da_borda:
                # Movimento para o centro quando está perto da borda
                mover_x = (LARGURA / 2 - inimigo.x) / dist if dist > 0 else 0
                mover_y = (ALTURA / 2 - inimigo.y) / dist if dist > 0 else 0
                
                # Mais forte se estiver muito perto da borda
                if inimigo.x < 30 or inimigo.x > LARGURA - inimigo.tamanho - 30 or \
                   inimigo.y < 30 or inimigo.y > ALTURA - inimigo.tamanho - 30:
                    mover_x *= 2
                    mover_y *= 2
            else:
                # Verificar se há tiros próximos e tentar desviar
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
                
                if tiro_mais_proximo is not None:
                    # Movimento evasivo - perpendicular à direção do tiro
                    vetor_perp_x = -tiro_mais_proximo.dy
                    vetor_perp_y = tiro_mais_proximo.dx
                    
                    # Garantir que estamos indo para longe do tiro
                    dot_product = vetor_perp_x * (tiro_mais_proximo.x - inimigo.x) + \
                                  vetor_perp_y * (tiro_mais_proximo.y - inimigo.y)
                    
                    if dot_product > 0:
                        vetor_perp_x = -vetor_perp_x
                        vetor_perp_y = -vetor_perp_y
                    
                    # Adicionar componente para se afastar do tiro
                    mover_x = vetor_perp_x
                    mover_y = vetor_perp_y
                else:
                    # Comportamento normal quando não há tiros para desviar
                    if dist < 300:  # Muito perto
                        if random.random() < 0.7:  # Às vezes recuar
                            mover_x = -dir_x * 0.8
                            mover_y = -dir_y * 0.8
                        else:  # Movimento lateral para flanquear
                            mover_x = dir_y
                            mover_y = -dir_x
                    elif dist > 500:  # Muito longe
                        # Aproximar do jogador
                        mover_x = dir_x
                        mover_y = dir_y
                    else:  # Distância média
                        # Movimento estratégico: circular ao redor do jogador
                        mover_x = dir_y * 0.8
                        mover_y = -dir_x * 0.8
                        
                        # Com chance de se aproximar ou afastar
                        if random.random() < 0.3:
                            mover_x += dir_x * 0.3
                            mover_y += dir_y * 0.3
            
            # Adicionar componente para evitar outros inimigos
            mover_x += evitar_x * 0.5
            mover_y += evitar_y * 0.5
            
            # Adicionar um pouco de aleatoriedade ao movimento
            mover_x += random.uniform(-0.2, 0.2)
            mover_y += random.uniform(-0.2, 0.2)
            
            # Normalizar o vetor de movimento
            magnitude = math.sqrt(mover_x**2 + mover_y**2)
            if magnitude > 0:
                mover_x /= magnitude
                mover_y /= magnitude
            
            inimigo.mover(mover_x, mover_y)
            inimigo.atualizar()
        
        # Atualizar tiros do jogador
        for tiro in tiros_jogador[:]:
            tiro.atualizar()
            
            # Verificar colisão com os inimigos
            for inimigo in inimigos:
                if inimigo.vidas <= 0:
                    continue  # Ignorar inimigos derrotados
                
                if tiro.rect.colliderect(inimigo.rect):
                    if inimigo.tomar_dano():
                        pontuacao += 10 * numero_fase  # Pontuação aumenta com a fase
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
            
            # Verificar colisão com o jogador
            if tiro.rect.colliderect(jogador.rect):
                if jogador.tomar_dano():
                    flash = criar_explosao(tiro.x, tiro.y, AZUL, particulas, 25)
                    flashes.append(flash)
                    pygame.mixer.Channel(2).play(pygame.mixer.Sound(gerar_som_dano()))
                tiros_inimigo.remove(tiro)
                continue
            
            # Remover tiros que saíram da tela
            if tiro.fora_da_tela():
                tiros_inimigo.remove(tiro)
        
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
                estrela[1] = random.randint(0, ALTURA)
        
        # Verificar condições de fim de fase
        if jogador.vidas <= 0:
            return False, pontuacao  # Jogador perdeu
        
        # Verificar se todos os inimigos foram derrotados
        todos_derrotados = all(inimigo.vidas <= 0 for inimigo in inimigos)
        if todos_derrotados:
            return True, pontuacao  # Fase concluída com sucesso
        
        # Desenhar tela do jogo
        desenhar_tela_jogo(tela, jogador, inimigos, tiros_jogador, tiros_inimigo, 
                        particulas, flashes, estrelas, gradiente_jogo, pontuacao, numero_fase, fade_in, tempo_atual)
        

        moeda_manager.desenhar(tela)
        cor_moeda = AMARELO
        pygame.draw.circle(tela, cor_moeda, (30, 30), 10)  # Ícone de moeda
        desenhar_texto(tela, f"{moeda_manager.obter_quantidade()}", 20, cor_moeda, 60, 30)
        pygame.display.flip()
        relogio.tick(FPS)
    
    return False, pontuacao  # Padrão: jogador saiu do jogo