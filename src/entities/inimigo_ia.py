#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gerenciar a Inteligência Artificial dos inimigos.
Contém funções para controlar o comportamento dos inimigos no jogo.
"""

import pygame
import math
import random
from src.config import *
from src.entities.particula import criar_explosao
from src.utils.sound import gerar_som_dano

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

    # Verificar se é inimigo mago e atualizar sistemas especiais
    if hasattr(inimigo, 'tipo_mago') and inimigo.tipo_mago:
        # Atualizar escudo cíclico
        inimigo.atualizar_escudo()

        # Atualizar invocação (se estiver invocando)
        if inimigo.esta_invocando:
            inimigo.atualizar_invocacao(inimigos)

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

    # BUGFIX: Verificar se idx está dentro dos limites (proteção contra invocações durante loop)
    if idx >= len(tempo_movimento_inimigos):
        return 0  # Retornar timestamp padrão para novos inimigos

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

            # Verificar se é inimigo metralhadora para usar método específico
            if hasattr(inimigo, 'tipo_metralhadora') and inimigo.tipo_metralhadora:
                inimigo.atirar_metralhadora(jogador, tiros_inimigo, particulas, flashes)
            # Verificar se é inimigo mago para usar método específico
            elif hasattr(inimigo, 'tipo_mago') and inimigo.tipo_mago:
                inimigo.atirar_bola_fogo(jogador, tiros_inimigo, particulas, flashes)
            # Verificar se é inimigo granada para usar método específico
            elif hasattr(inimigo, 'tipo_granada') and inimigo.tipo_granada:
                # Nota: granadas_lista deve ser passada pelo sistema de jogo
                # Por enquanto, vamos apenas marcar que ele quer atirar
                pass  # O lançamento será gerenciado no loop principal do jogo
            # Verificar se é inimigo fantasma para usar método específico
            elif hasattr(inimigo, 'tipo_fantasma') and inimigo.tipo_fantasma:
                inimigo.atirar(jogador, tiros_inimigo, particulas, flashes)
            else:
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