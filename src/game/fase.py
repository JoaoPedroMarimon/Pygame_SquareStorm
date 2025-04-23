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
from src.config import LARGURA_JOGO, ALTURA_JOGO
from src.utils.visual import desenhar_mira, criar_mira
from src.utils.visual import desenhar_texto, criar_texto_flutuante

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
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão atualizada da função para remover o comportamento de tremor dos inimigos.
Essa função deve substituir a função correspondente no arquivo src/game/fase.py
"""

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
            
            # Combinar os vetores (70% evasão, 30% para o centro)
            mover_x = vetor_perp_x * 0.7 + para_centro_x * 0.3
            mover_y = vetor_perp_y * 0.7 + para_centro_y * 0.3
        else:
            mover_x = vetor_perp_x
            mover_y = vetor_perp_y
    
    # PRIORIDADE 3: Comportamento normal baseado na situação
    elif not perto_da_borda or (jogador_perto_borda and inimigo.x > margem_borda and 
                               inimigo.x < LARGURA - inimigo.tamanho - margem_borda and
                               inimigo.y > margem_borda and 
                               inimigo.y < ALTURA - inimigo.tamanho - margem_borda):
        # Comportamento tático adaptado à distância do jogador
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
        fator_borda = 0.6
        mover_x = para_centro_x * fator_borda
        mover_y = para_centro_y * fator_borda
    
    # Adicionar componente para evitar outros inimigos
    mover_x += evitar_x * 0.5
    mover_y += evitar_y * 0.5
    
    # Adicionar um pouco de aleatoriedade ao movimento (menos quando perto da borda)
    aleatoriedade = 0.05 if muito_perto_da_borda else (0.1 if perto_da_borda else 0.2)
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
    velocidade_atual = inimigo.velocidade if muito_perto_da_borda else inimigo.velocidade * 0.8
    
    # Executar o movimento
    inimigo.mover(mover_x, mover_y)
    inimigo.atualizar()
    
    return tempo_movimento_inimigos[idx]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atualização da lógica de controle no arquivo src/game/fase.py
para implementar o sistema de mira com o mouse.
"""

# Modificação da função jogar_fase no arquivo src/game/fase.py

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
    duracao_transicao_vitoria = 180  # 3 segundos a 60 FPS (ajuste conforme necessário)
    
    # Cursor do mouse visível durante o jogo
    pygame.mouse.set_visible(False)  # Esconder o cursor padrão do sistema

    # Criar mira personalizada
    mira_surface, mira_rect = criar_mira(12, BRANCO, AMARELO)
    
    # Loop principal da fase
    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()
        
        # Obter a posição atual do mouse para o sistema de mira
        pos_mouse = pygame.mouse.get_pos()
        
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
                
                # Tiro com o botão esquerdo do mouse
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:  # Botão esquerdo
                    # Atirar na direção do mouse
                    jogador.atirar_com_mouse(tiros_jogador, pos_mouse)
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
            desenhar_texto(tela, "Pressione qualquer tecla para começar", 24, BRANCO, LARGURA // 2, ALTURA_JOGO * 3 // 4)
            
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
            
            # Desenhar mensagem de pausa
            tela.fill((0, 0, 20))
            desenhar_texto(tela, "PAUSADO", 60, BRANCO, LARGURA // 2, ALTURA_JOGO // 2)
            desenhar_texto(tela, "Pressione P para continuar", 30, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 80)
            pygame.display.flip()
            relogio.tick(FPS)
            continue
        
        # Atualizar posição do jogador
        jogador.mover(movimento_x, movimento_y)
        jogador.atualizar()
        
        # Garantir que o jogador não ultrapasse a área de jogo
        if jogador.y + jogador.tamanho > ALTURA_JOGO:
            jogador.y = ALTURA_JOGO - jogador.tamanho
            jogador.rect.y = jogador.y
        
        # Atualizar moedas e verificar colisões
        moeda_coletada = moeda_manager.atualizar(jogador)
        if moeda_coletada:
            # Adicionar pontos bônus ao coletar moedas
            pontuacao += 5
            
        # Atualizar IA para cada inimigo
        for idx, inimigo in enumerate(inimigos):
            tempo_movimento_inimigos[idx] = atualizar_IA_inimigo(
                inimigo, idx, jogador, tiros_jogador, inimigos, tempo_atual, 
                tempo_movimento_inimigos, intervalo_movimento, numero_fase, 
                tiros_inimigo, movimento_x, movimento_y
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
                        # Adicionar pontos bônus ao acertar o inimigo
                        pontuacao += 10 * numero_fase  # Pontuação aumenta com a fase
                        
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
                estrela[1] = random.randint(0, ALTURA_JOGO)  # Ajustado para usar ALTURA_JOGO
        
        # Verificar condições de fim de fase
        if jogador.vidas <= 0:
            return False, pontuacao  # Jogador perdeu
        
        # Verificar se todos os inimigos foram derrotados e tratar transição de vitória
        todos_derrotados = all(inimigo.vidas <= 0 for inimigo in inimigos)
        
        # Se todos os inimigos foram derrotados, iniciar contagem para transição
        if todos_derrotados and tempo_transicao_vitoria is None:
            tempo_transicao_vitoria = duracao_transicao_vitoria  # Iniciar contagem regressiva
            # Pode adicionar um efeito sonoro ou visual aqui para indicar a vitória iminente
        
        # Se a contagem regressiva de vitória está ativa, decrementá-la
        if tempo_transicao_vitoria is not None:
            tempo_transicao_vitoria -= 1
            
            # Quando a contagem chegar a zero, concluir a fase
            if tempo_transicao_vitoria <= 0:
                return True, pontuacao  # Fase concluída com sucesso
        
        # Preencher toda a tela com preto antes de desenhar qualquer elemento do jogo
        tela.fill((0, 0, 0))
        
        # Desenhar tela do jogo
        desenhar_tela_jogo(tela, jogador, inimigos, tiros_jogador, tiros_inimigo, 
                        particulas, flashes, estrelas, gradiente_jogo, pontuacao, numero_fase, fade_in, tempo_atual, moeda_manager)
        
        # Desenhar moedas
        moeda_manager.desenhar(tela)
        
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
        
        # Desenhar mira personalizada do mouse
        desenhar_mira(tela, pos_mouse, (mira_surface, mira_rect))
        
        pygame.display.flip()
        relogio.tick(FPS)
    
    return False, pontuacao  # Padrão: jogador saiu do jogo