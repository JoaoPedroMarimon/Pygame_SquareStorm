#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de invocação do Chucky através do amuleto místico.
Cria animação de pentagrama e aparição do Chucky no centro da arena.
ADICIONADO: Portal simples que cobre o Chucky durante a transição.
"""

import pygame
import math
import random
from src.config import *

class ChuckyInvocation:
    """Classe para gerenciar a invocação do Chucky."""
    
    def __init__(self):
        # SEMPRE no centro da arena
        self.centro_x = LARGURA // 2
        self.centro_y = ALTURA_JOGO // 2
        self.x = LARGURA // 2.1
        self.y = ALTURA_JOGO // 2.2
        
        self.tempo_vida = 0
        self.max_tempo_vida = 900  # 10 segundos a 60 FPS
        
        # Estados da animação
        self.fase_pentagrama = True  # Primeira fase: desenhar pentagrama
        self.fase_chucky = False     # Segunda fase: aparecer Chucky
        self.tempo_pentagrama = 180  # 3 segundos para o pentagrama
        
        # Propriedades do pentagrama
        self.raio_pentagrama = 0
        self.raio_max_pentagrama = 80
        self.alpha_pentagrama = 0
        
        # Propriedades do Chucky
        self.escala_chucky = 0.0
        self.alpha_chucky = 0
        self.rotacao_chucky = 0
        self.flutuacao_chucky = 0
        self.portal_ativo = False
        self.portal_alpha = 0
        self.portal_raio = 0
        self.portal_rotacao = 0
        self.chucky_ativo = False  # Se o Chucky pode se mover e causar dano
        self.velocidade_x = 0
        self.velocidade_y = 0
        self.velocidade_max = 80  # Velocidade máxima do movimento
        self.mudanca_direcao_timer = 0
        self.intervalo_mudanca_direcao = 30  # Muda direção a cada 0.5 segundos

        # Hitbox do Chucky para colisões
        self.chucky_rect = pygame.Rect(self.x, self.y, 60, 80)
        
        # Efeitos visuais
        self.particulas_misticas = []
        self.chamas_infernais = []
        self.relampagos = []
        
        # Sons (placeholders)
        self.som_invocacao_tocado = False
        self.som_aparicao_tocado = False
    
    def atualizar(self):
        """Atualiza a animação de invocação."""
        self.tempo_vida += 1
        
        if self.tempo_vida <= self.tempo_pentagrama:
            # Primeira fase: só pentagrama
            self.fase_pentagrama = True
            self.fase_chucky = False
            self._atualizar_fase_pentagrama()
        else:
            # Segunda fase: só Chucky
            if not self.fase_chucky:
                # Primeira transição para Chucky
                self.fase_pentagrama = False
                self.fase_chucky = True
                # Inicializar valores do Chucky
                self.escala_chucky = 0.0
                self.alpha_chucky = 0
                self.rotacao_chucky = 360
            self._atualizar_fase_chucky()
            # NOVO: Atualizar portal
        
        # NOVO: Atualizar portal
        self._atualizar_portal()
        self._atualizar_movimento_chucky()

        # Atualizar efeitos
        self._atualizar_particulas()

        
        return self.tempo_vida < self.max_tempo_vida
    
    def _atualizar_portal(self):
        """Atualiza o portal que cobre o Chucky."""
        tempo_chucky = self.tempo_vida - self.tempo_pentagrama
        
        # Portal aparece 30 frames antes do Chucky (0.5 segundos)
        # e desaparece 60 frames depois do Chucky aparecer (1 segundo)
        if tempo_chucky >= -30 and tempo_chucky <= 120:
            self.portal_ativo = True
            
            if tempo_chucky < 0:
                # Portal crescendo antes do Chucky
                progresso = (30 + tempo_chucky) / 30  # 0 a 1
                self.portal_alpha = int(255 * progresso)
                self.portal_raio = int(150 * progresso)
            elif tempo_chucky <= 60:
                # Portal no máximo durante aparição do Chucky
                self.portal_alpha = 255
                self.portal_raio = 150
            else:
                # Portal diminuindo após Chucky aparecer
                progresso = 1 - ((tempo_chucky - 60) / 60)  # 1 a 0
                self.portal_alpha = int(255 * progresso)
                self.portal_raio = int(150 * progresso)
            
            # Rotação constante do portal
            self.portal_rotacao += 5
        else:
            self.portal_ativo = False
            
            # NOVO: Ativar o Chucky quando o portal se fechar
            if tempo_chucky > 120 and not self.chucky_ativo:
                self.chucky_ativo = True
                self._iniciar_movimento_chucky()

    def _desenhar_portal(self, tela):
        """Desenha um portal mágico mais bonito cobrindo o Chucky."""
        if not self.portal_ativo or self.portal_raio <= 0:
            return
        
        # Criar superfície para o portal
        portal_surface = pygame.Surface((self.portal_raio * 3, self.portal_raio * 3), pygame.SRCALPHA)
        centro_surface = self.portal_raio * 1.5
        
        # Efeito de brilho externo (halo)
        for i in range(3):
            raio_halo = self.portal_raio + 15 + i * 8
            alpha_halo = 30 - i * 10
            cor_halo = (200, 50, 50, alpha_halo)  # Vermelho brilhante
            
            # Círculo de brilho com transparência
            halo_surface = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo_surface, cor_halo, (raio_halo, raio_halo), raio_halo)
            halo_rect = halo_surface.get_rect(center=(centro_surface, centro_surface))
            portal_surface.blit(halo_surface, halo_rect, special_flags=pygame.BLEND_ADD)
        
        # Círculos concêntricos do portal (efeito de túnel melhorado)
        for i in range(6):
            raio_circulo = self.portal_raio - i * 8
            if raio_circulo > 0:
                # Cores do portal com gradiente mais suave
                intensidade = 1 - (i / 6)
                
                # Cores alternadas para criar profundidade
                if i % 2 == 0:
                    cor_portal = (
                        int(255 * intensidade),  # Vermelho vibrante
                        int(50 * intensidade),   
                        int(50 * intensidade)
                    )
                else:
                    cor_portal = (
                        int(200 * intensidade),  # Vermelho mais escuro
                        int(20 * intensidade),   
                        int(20 * intensidade)
                    )
                
                # Círculo pulsante com movimento mais suave
                pulso = math.sin((self.portal_rotacao + i * 45) * 0.08) * 4
                raio_pulsante = raio_circulo + pulso
                
                # Desenhar círculo principal
                pygame.draw.circle(portal_surface, cor_portal, 
                                (int(centro_surface), int(centro_surface)), 
                                int(raio_pulsante), 2)
                
                # Adicionar brilho interno aos círculos
                if i < 4:  # Só nos círculos externos
                    cor_brilho = tuple(min(255, c + 50) for c in cor_portal)
                    pygame.draw.circle(portal_surface, cor_brilho, 
                                    (int(centro_surface), int(centro_surface)), 
                                    int(raio_pulsante), 1)
        
        # Adicionar partículas flutuantes ao redor do portal
        num_particulas = 8
        for i in range(num_particulas):
            angulo = (self.portal_rotacao * 2 + i * 45) % 360
            distancia = self.portal_raio * 0.8 + math.sin((self.portal_rotacao + i * 30) * 0.05) * 10
            
            x = centro_surface + math.cos(math.radians(angulo)) * distancia
            y = centro_surface + math.sin(math.radians(angulo)) * distancia
            
            # Cor da partícula baseada na posição
            cor_particula = (
                200 + int(math.sin(angulo * 0.1) * 55),
                50,
                50
            )
            
            # Tamanho da partícula varia
            tamanho = 2 + int(math.sin((self.portal_rotacao + i * 20) * 0.1))
            pygame.draw.circle(portal_surface, cor_particula, (int(x), int(y)), tamanho)
        
        # Centro escuro do portal com efeito de vórtice
        centro_raio = self.portal_raio // 3
        
        # Múltiplos círculos para criar profundidade no centro
        for i in range(4):
            raio_centro = centro_raio - i * 3
            if raio_centro > 0:
                intensidade_escura = 0.3 + i * 0.15
                cor_centro = (
                    int(80 * intensidade_escura),
                    int(20 * intensidade_escura),
                    int(20 * intensidade_escura)
                )
                pygame.draw.circle(portal_surface, cor_centro, 
                                (int(centro_surface), int(centro_surface)), 
                                raio_centro)
        
        # Raios de energia saindo do centro
        num_raios = 6
        for i in range(num_raios):
            angulo = (self.portal_rotacao * 3 + i * 60) % 360
            
            # Pontos do raio
            x1 = centro_surface + math.cos(math.radians(angulo)) * (centro_raio + 5)
            y1 = centro_surface + math.sin(math.radians(angulo)) * (centro_raio + 5)
            x2 = centro_surface + math.cos(math.radians(angulo)) * (self.portal_raio * 0.6)
            y2 = centro_surface + math.sin(math.radians(angulo)) * (self.portal_raio * 0.6)
            
            # Cor do raio com transparência
            alpha_raio = 100 + int(math.sin((self.portal_rotacao + i * 30) * 0.1) * 50)
            cor_raio = (255, 100, 100, min(255, alpha_raio))
            
            # Desenhar linha com espessura variável
            espessura = 1 + int(math.sin((self.portal_rotacao + i * 45) * 0.1))
            pygame.draw.line(portal_surface, cor_raio[:3], (x1, y1), (x2, y2), espessura)
        
        # Aplicar transparência geral
        portal_surface.set_alpha(self.portal_alpha)
        
        # Desenhar na tela
        rect = portal_surface.get_rect(center=(self.centro_x, self.centro_y))
        tela.blit(portal_surface, rect)
    
    def _atualizar_fase_pentagrama(self):
        """Atualiza a fase de aparição do pentagrama."""
        progresso = self.tempo_vida / self.tempo_pentagrama
        
        # Pentagrama cresce gradualmente
        self.raio_pentagrama = int(self.raio_max_pentagrama * min(1.0, progresso * 1.5))
        self.alpha_pentagrama = min(255, int(255 * progresso * 2))
        
        # Criar partículas místicas
        if random.random() < 0.3:
            self._criar_particula_mistica()
        
        # Som de invocação (uma vez)
        if not self.som_invocacao_tocado and progresso > 0.1:
            self.som_invocacao_tocado = True
            # pygame.mixer.Channel(3).play(som_invocacao)
    
    def _atualizar_fase_chucky(self):
        """Atualiza a fase de aparição do Chucky."""
        tempo_chucky = self.tempo_vida - self.tempo_pentagrama
        
        if tempo_chucky <= 60:  # Primeiros 1 segundo: Chucky aparece
            aparicao_prog = tempo_chucky / 60
            self.escala_chucky = aparicao_prog * 1.2  # Cresce um pouco além do normal
            self.alpha_chucky = min(255, int(255 * aparicao_prog))
            self.rotacao_chucky = (1 - aparicao_prog) * 360  # Gira enquanto aparece
            
            # Som de aparição (uma vez)
            if not self.som_aparicao_tocado and aparicao_prog > 0.5:
                self.som_aparicao_tocado = True
                # pygame.mixer.Channel(4).play(som_aparicao_chucky)
                
        elif tempo_chucky <= 120:  # Próximo 1 segundo: estabiliza
            self.escala_chucky = max(1.0, 1.2 - (tempo_chucky - 60) / 60 * 0.2)
            self.alpha_chucky = 255
            self.rotacao_chucky = 0
            
        else:  # Resto do tempo: flutua menacingly
            self.escala_chucky = 1.0
            self.alpha_chucky = 255
        
        # Criar chamas infernais

    
    def _criar_particula_mistica(self):
        """Cria uma partícula mística ao redor do pentagrama."""
        angulo = random.uniform(0, 2 * math.pi)
        distancia = random.uniform(60, 120)
        x = self.centro_x + math.cos(angulo) * distancia
        y = self.centro_y + math.sin(angulo) * distancia
        
        particula = {
            'x': x,
            'y': y,
            'vel_x': math.cos(angulo + math.pi) * random.uniform(0.5, 2),
            'vel_y': math.sin(angulo + math.pi) * random.uniform(0.5, 2),
            'vida': random.randint(30, 80),
            'cor': random.choice([(200, 150, 255), (150, 100, 200), (255, 100, 150)]),
            'tamanho': random.randint(2, 5)
        }
        self.particulas_misticas.append(particula)
    

    

    
    def _atualizar_particulas(self):
        """Atualiza as partículas místicas."""
        for particula in self.particulas_misticas[:]:
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 1
            
            if particula['vida'] <= 0:
                self.particulas_misticas.remove(particula)
    
    

    
    def desenhar(self, tela):
        """Desenha toda a invocação na tela."""
        # MODIFICADO: Pentagrama fica visível durante toda a invocação
        if self.tempo_vida <= self.max_tempo_vida:
            self._desenhar_pentagrama(tela)
        
        if self.fase_chucky:
            self._desenhar_chucky(tela)
            self._desenhar_portal(tela)
        
        # NOVO: Desenhar portal por último (sobrepõe tudo)
        self._desenhar_portal(tela)
    
    def _desenhar_pentagrama(self, tela):
        """Desenha o pentagrama satânico com animação assustadora."""
        if self.raio_pentagrama <= 0:
            return
        
        # MODIFICADO: Raio ainda maior para pentagrama mais imponente
        raio_final = self.raio_pentagrama * 2.2  # 120% maior
        
        # Controle de crescimento inicial
        tempo = pygame.time.get_ticks()
        
        # Se não temos tempo de início, definir agora
        if not hasattr(self, 'tempo_inicio_pentagrama'):
            self.tempo_inicio_pentagrama = tempo
        
        tempo_crescimento = tempo - self.tempo_inicio_pentagrama
        duracao_crescimento = 3000  # 3 segundos para crescer (mais tempo para efeitos)
        
        if tempo_crescimento < duracao_crescimento:
            # Fase de crescimento: animação suave de 0 até tamanho final
            progresso = tempo_crescimento / duracao_crescimento
            # Easing out para crescimento mais dramático no final
            progresso = 1 - (1 - progresso) ** 3
            raio_atual = int(raio_final * progresso)
            crescendo = True
        else:
            # Fase de tremor: tamanho fixo com apenas tremor sutil
            raio_atual = int(raio_final)
            crescendo = False
        
        # NOVO: Efeitos especiais durante o crescimento
        if crescendo:
            # Círculos de energia expandindo
            for i in range(5):
                raio_onda = (progresso * 200 + i * 30) % 250
                if raio_onda > 0:
                    alpha_onda = int(100 * (1 - raio_onda / 250))
                    if alpha_onda > 0:
                        onda_surface = pygame.Surface((raio_onda * 2 + 50, raio_onda * 2 + 50), pygame.SRCALPHA)
                        pygame.draw.circle(onda_surface, (150, 0, 0), 
                                        (raio_onda + 25, raio_onda + 25), int(raio_onda), 3)
                        onda_surface.set_alpha(alpha_onda)
                        rect_onda = onda_surface.get_rect(center=(self.centro_x, self.centro_y))
                        tela.blit(onda_surface, rect_onda)
            
            # Raios de energia emergindo do centro
            
            # Partículas de fogo dançando ao redor
            
            # Texto místico aparecendo gradualmente
            if progresso > 0.3:
                simbolos = ["☠", "⚡", "🔥", "👁", "💀", "⭐"]
                alpha_texto = int((progresso - 0.3) * 255 / 0.7)
                
                for i, simbolo in enumerate(simbolos):
                    angulo_simbolo = i * 60 + (tempo * 0.02)
                    simbolo_x = self.centro_x + (raio_atual + 40) * math.cos(math.radians(angulo_simbolo))
                    simbolo_y = self.centro_y + (raio_atual + 40) * math.sin(math.radians(angulo_simbolo))
                    
                    # Criar superfície para o símbolo
                    try:
                        fonte_simbolo = pygame.font.Font(None, 30)
                        texto_surface = fonte_simbolo.render(simbolo, True, (255, 200, 0))
                        texto_surface.set_alpha(alpha_texto)
                        
                        rect_simbolo = texto_surface.get_rect(center=(int(simbolo_x), int(simbolo_y)))
                        tela.blit(texto_surface, rect_simbolo)
                    except:
                        # Fallback para círculos se símbolos não funcionarem
                        pygame.draw.circle(tela, (255, 200, 0), (int(simbolo_x), int(simbolo_y)), 5)
            
            # Distorção do espaço ao redor (efeito visual)
            if progresso > 0.5:
                for anel in range(3):
                    raio_distorcao = raio_atual + 30 + anel * 15
                    pontos_distorcao = []
                    
                    for angulo in range(0, 360, 20):
                        rad = math.radians(angulo)
                        # Distorção ondulatória
                        distorcao = math.sin(tempo * 0.01 + angulo * 0.1 + anel) * 8
                        
                        x = self.centro_x + (raio_distorcao + distorcao) * math.cos(rad)
                        y = self.centro_y + (raio_distorcao + distorcao) * math.sin(rad)
                        pontos_distorcao.append((x, y))
                    
                    if len(pontos_distorcao) >= 3:
                        cor_distorcao = (80 - anel * 20, 0, 0)
                        alpha_distorcao = int((progresso - 0.5) * 80 / 0.5)
                        
                        distorcao_surface = pygame.Surface((raio_distorcao * 2 + 100, raio_distorcao * 2 + 100), pygame.SRCALPHA)
                        
                        try:
                            pygame.draw.polygon(distorcao_surface, cor_distorcao, 
                                            [(p[0] - self.centro_x + raio_distorcao + 50, 
                                                p[1] - self.centro_y + raio_distorcao + 50) for p in pontos_distorcao], 2)
                            distorcao_surface.set_alpha(alpha_distorcao)
                            
                            rect_dist = distorcao_surface.get_rect(center=(self.centro_x, self.centro_y))
                            tela.blit(distorcao_surface, rect_dist)
                        except:
                            pass  # Ignorar se houver erro na distorção
        
        # MODIFICADO: Alpha com tremulação, mas sem pulsação excessiva
        alpha_base = self.alpha_pentagrama
        
        if crescendo:
            # Durante crescimento: Alpha mais intenso e dramático
            alpha_pentagrama = min(255, alpha_base + progresso * 100)
            # Pulsos rápidos durante crescimento
            pulso_crescimento = abs(math.sin(tempo * 0.05)) * 50
            alpha_pentagrama = min(255, alpha_pentagrama + pulso_crescimento)
        else:
            # Tremulação sutil no alpha para efeito assombrado
            tremulacao = abs(math.sin(tempo * 0.02)) * 25 + 10
            alpha_pentagrama = min(255, alpha_base + tremulacao)
        
        # Durante a fase do Chucky, criar efeito sinistro mais sutil
        
        # Criar superfície maior para comportar o pentagrama aumentado
        tamanho_surface = raio_atual * 2 + 200  # Maior para comportar efeitos
        pentagrama_surface = pygame.Surface((tamanho_surface, tamanho_surface), pygame.SRCALPHA)
        
        # NOVO: Efeito de aura sombria ao redor do pentagrama
        centro_surface = tamanho_surface // 2
        
        # Aura mais intensa durante crescimento
 
        
        desenhar_pentagrama(pentagrama_surface, 
                        centro_surface, 
                        centro_surface,
                        raio_atual, 
                        (255, 0, 0), 
                        5, # Espessura maior para mais impacto
                        crescendo,
                        progresso if crescendo else 1.0)
        
        # NOVO: Efeito de chamas espectrais nas bordas (mais intenso durante crescimento)
        
        # Aplicar transparência com efeito pulsante
        pentagrama_surface.set_alpha(int(alpha_pentagrama))
        
        # Desenhar na tela com tremor mais controlado
        if not crescendo:
            # Tremor apenas após o crescimento completo
            intensidade_tremor = 1 if alpha_pentagrama > 150 else 0.5
            tremor_x = random.randint(-2, 2) * intensidade_tremor
            tremor_y = random.randint(-2, 2) * intensidade_tremor
        else:
            # Durante crescimento: tremor mais intenso no final
            if progresso > 0.7:
                tremor_crescimento = (progresso - 0.7) / 0.3  # 0 a 1 nos últimos 30%
                tremor_x = random.randint(-4, 4) * tremor_crescimento
                tremor_y = random.randint(-4, 4) * tremor_crescimento
            else:
                tremor_x = 0
                tremor_y = 0
        
        rect = pentagrama_surface.get_rect(center=(self.centro_x + tremor_x, self.centro_y + tremor_y))
        tela.blit(pentagrama_surface, rect)


    
    def _desenhar_chucky(self, tela):            
        # Ajustar posição com flutuação
        if self.chucky_ativo:
            # Durante movimento: usar posição atual
            chucky_x = self.x
            chucky_y = self.y + self.flutuacao_chucky
        else:
            # Durante aparição: usar coordenadas centralizadas
            chucky_x = self.centro_x - 30  # Ajustar para centralizar o sprite do Chucky
            chucky_y = self.centro_y - 40 + self.flutuacao_chucky  # Centralizar verticalmente + flutuação        
        
        # Pernas (calça jeans azul)
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 20, chucky_y + 55, 8, 20))
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 32, chucky_y + 55, 8, 20))
        
        # Tênis vermelhos (característicos do Chucky)
        pygame.draw.ellipse(tela, (220, 20, 60), (chucky_x + 18, chucky_y + 72, 12, 8))
        pygame.draw.ellipse(tela, (220, 20, 60), (chucky_x + 30, chucky_y + 72, 12, 8))
        
        # Sola dos tênis (branca)
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 18, chucky_y + 76, 12, 4))
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 30, chucky_y + 76, 12, 4))
        
        # Detalhes dos tênis (cadarços/linhas)
        pygame.draw.line(tela, BRANCO, (chucky_x + 20, chucky_y + 74), (chucky_x + 28, chucky_y + 74), 1)
        pygame.draw.line(tela, BRANCO, (chucky_x + 32, chucky_y + 74), (chucky_x + 40, chucky_y + 74), 1)
        
        # Camisa listrada por baixo (mangas completas cobrindo todo o braço)
        # Mangas listradas coloridas - cores do Chucky
        cores_listras = [(220, 20, 60), (34, 139, 34), (30, 144, 255), (255, 140, 0), (148, 0, 211)]
        
        # Manga esquerda completa (cobrindo todo o braço)
        for i in range(10):  # mais listras para cobrir todo o braço
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 8, chucky_y + 30 + i*3, 14, 2))
        
        # Manga direita completa (cobrindo todo o braço)
        for i in range(10):  # mais listras para cobrir todo o braço
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 38, chucky_y + 30 + i*3, 14, 2))
            
        # Parte do peito da camisa listrada (visível)
        for i in range(3):
            cor = cores_listras[i % len(cores_listras)]
            pygame.draw.rect(tela, cor, (chucky_x + 22, chucky_y + 26 + i*2, 16, 1))
        
        # Macacão jeans azul (corpo principal) - por cima da camisa
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 18, chucky_y + 32, 24, 28))
        
        # Alças do macacão
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 22, chucky_y + 24, 4, 12))
        pygame.draw.rect(tela, (70, 130, 180), (chucky_x + 34, chucky_y + 24, 4, 12))
        
        # Botões das alças (detalhados)
        pygame.draw.circle(tela, (139, 69, 19), (chucky_x + 24, chucky_y + 28), 2)  # botão marrom
        pygame.draw.circle(tela, PRETO, (chucky_x + 24, chucky_y + 28), 1)  # centro do botão
        pygame.draw.circle(tela, (139, 69, 19), (chucky_x + 36, chucky_y + 28), 2)
        pygame.draw.circle(tela, PRETO, (chucky_x + 36, chucky_y + 28), 1)
        
        # BOLSO NO PEITO DO MACACÃO (característico do Chucky)
        pygame.draw.rect(tela, (60, 110, 160), (chucky_x + 24, chucky_y + 36, 12, 8))  # bolso um pouco mais escuro
        # Costura do bolso
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 36), (chucky_x + 36, chucky_y + 36), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 36), (chucky_x + 24, chucky_y + 44), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 36, chucky_y + 36), (chucky_x + 36, chucky_y + 44), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 24, chucky_y + 44), (chucky_x + 36, chucky_y + 44), 1)
        
        # Costuras do macacão
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 18, chucky_y + 45), (chucky_x + 42, chucky_y + 45), 1)
        pygame.draw.line(tela, (50, 100, 150), (chucky_x + 30, chucky_y + 32), (chucky_x + 30, chucky_y + 60), 1)
        
        # Mãos (sem braços visíveis - só as mãos saindo das mangas)
        pygame.draw.circle(tela, (255, 220, 177), (chucky_x + 13, chucky_y + 60), 3)
        pygame.draw.circle(tela, (255, 220, 177), (chucky_x + 47, chucky_y + 60), 3)
        
        # Cabeça (formato mais oval como o Chucky real)
        pygame.draw.ellipse(tela, (255, 220, 177), (chucky_x + 14, chucky_y + 8, 32, 28))
        
        # Cabelo ruivo detalhado (estilo característico do Chucky)
        # Base do cabelo - formato mais volumoso e bagunçado
        cabelo_cor_base = (180, 50, 50)
        cabelo_cor_clara = (220, 80, 60)
        cabelo_cor_escura = (150, 30, 30)
        
        # Volume principal do cabelo (formato irregular)
        pygame.draw.ellipse(tela, cabelo_cor_base, (chucky_x + 10, chucky_y + 1, 40, 22))
        
        # Cabelo na parte de trás (volume extra)
        pygame.draw.ellipse(tela, cabelo_cor_escura, (chucky_x + 8, chucky_y + 3, 44, 18))
        
        # Mechas superiores bagunçadas (em pé)
        mechas_topo = [
            (chucky_x + 15, chucky_y - 2, chucky_x + 13, chucky_y + 8),
            (chucky_x + 20, chucky_y - 1, chucky_x + 19, chucky_y + 6),
            (chucky_x + 25, chucky_y - 3, chucky_x + 24, chucky_y + 7),
            (chucky_x + 30, chucky_y - 2, chucky_x + 29, chucky_y + 6),
            (chucky_x + 35, chucky_y - 1, chucky_x + 34, chucky_y + 7),
            (chucky_x + 40, chucky_y - 2, chucky_x + 39, chucky_y + 8),
            (chucky_x + 45, chucky_y - 1, chucky_x + 44, chucky_y + 6)
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(mechas_topo):
            cor = cabelo_cor_clara if i % 2 == 0 else cabelo_cor_base
            pygame.draw.line(tela, cor, (x1, y1), (x2, y2), 4)
            # Mechas menores para textura
            pygame.draw.line(tela, cabelo_cor_escura, (x1 + 1, y1 + 1), (x2 - 1, y2 - 1), 2)
        
        # Franja bagunçada característica (caindo na testa)
        franja_mechas = [
            (chucky_x + 12, chucky_y + 8, chucky_x + 16, chucky_y + 18),
            (chucky_x + 16, chucky_y + 6, chucky_x + 18, chucky_y + 16),
            (chucky_x + 20, chucky_y + 7, chucky_x + 21, chucky_y + 17),
            (chucky_x + 24, chucky_y + 5, chucky_x + 25, chucky_y + 15),
            (chucky_x + 28, chucky_y + 6, chucky_x + 29, chucky_y + 16),
            (chucky_x + 32, chucky_y + 7, chucky_x + 33, chucky_y + 17),
            (chucky_x + 36, chucky_y + 5, chucky_x + 37, chucky_y + 15),
            (chucky_x + 40, chucky_y + 6, chucky_x + 42, chucky_y + 16),
            (chucky_x + 44, chucky_y + 8, chucky_x + 48, chucky_y + 18)
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(franja_mechas):
            cor = [cabelo_cor_clara, cabelo_cor_base, cabelo_cor_escura][i % 3]
            pygame.draw.line(tela, cor, (x1, y1), (x2 + random.randint(-2, 2), y2), 3)
        
        # Mechas laterais longas (características do Chucky)
        # Lado esquerdo
        laterais_esq = [
            (chucky_x + 8, chucky_y + 10, chucky_x + 6, chucky_y + 22),
            (chucky_x + 10, chucky_y + 12, chucky_x + 4, chucky_y + 25),
            (chucky_x + 12, chucky_y + 14, chucky_x + 8, chucky_y + 28),
            (chucky_x + 14, chucky_y + 16, chucky_x + 10, chucky_y + 30)
        ]
        
        for x1, y1, x2, y2 in laterais_esq:
            pygame.draw.line(tela, cabelo_cor_base, (x1, y1), (x2, y2), 4)
            pygame.draw.line(tela, cabelo_cor_escura, (x1 + 1, y1), (x2 + 1, y2), 2)
        
        # Lado direito
        laterais_dir = [
            (chucky_x + 52, chucky_y + 10, chucky_x + 54, chucky_y + 22),
            (chucky_x + 50, chucky_y + 12, chucky_x + 56, chucky_y + 25),
            (chucky_x + 48, chucky_y + 14, chucky_x + 52, chucky_y + 28),
            (chucky_x + 46, chucky_y + 16, chucky_x + 50, chucky_y + 30)
        ]
        
        for x1, y1, x2, y2 in laterais_dir:
            pygame.draw.line(tela, cabelo_cor_base, (x1, y1), (x2, y2), 4)
            pygame.draw.line(tela, cabelo_cor_escura, (x1 - 1, y1), (x2 - 1, y2), 2)
        
        # Mechas traseiras (atrás das orelhas)
        pygame.draw.arc(tela, cabelo_cor_escura, (chucky_x + 6, chucky_y + 8, 16, 20), 1.5, 3.0, 6)
        pygame.draw.arc(tela, cabelo_cor_escura, (chucky_x + 38, chucky_y + 8, 16, 20), 0, 1.5, 6)
        
        # Textura adicional no cabelo (mechas finas)
        for i in range(15):
            x_tex = chucky_x + 12 + i * 2.5
            y_start = chucky_y + 4 + random.randint(-2, 2)
            y_end = chucky_y + 12 + random.randint(-3, 3)
            cor_tex = [cabelo_cor_clara, cabelo_cor_base, cabelo_cor_escura][i % 3]
            pygame.draw.line(tela, cor_tex, (x_tex, y_start), (x_tex + random.randint(-1, 1), y_end), 1)
        
        # Testa mais proeminente
        pygame.draw.ellipse(tela, (245, 210, 167), (chucky_x + 18, chucky_y + 12, 24, 8))
        
        # Olhos azuis mais expressivos e malignos
        # Formato amendoado dos olhos
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 20, chucky_y + 18, 8, 6))
        pygame.draw.ellipse(tela, BRANCO, (chucky_x + 32, chucky_y + 18, 8, 6))
        
        # Íris azul intensa
        pygame.draw.circle(tela, (0, 100, 200), (chucky_x + 24, chucky_y + 21), 3)
        pygame.draw.circle(tela, (0, 100, 200), (chucky_x + 36, chucky_y + 21), 3)
        
        # Pupilas dilatadas (efeito sinistro)
        pygame.draw.circle(tela, PRETO, (chucky_x + 24, chucky_y + 21), 2)
        pygame.draw.circle(tela, PRETO, (chucky_x + 36, chucky_y + 21), 2)
        
        # Reflexos nos olhos
        pygame.draw.circle(tela, BRANCO, (chucky_x + 25, chucky_y + 20), 1)
        pygame.draw.circle(tela, BRANCO, (chucky_x + 37, chucky_y + 20), 1)
        
        # Sobrancelhas grossas e franzidas (expressão raivosa)
        pygame.draw.arc(tela, (139, 69, 19), (chucky_x + 18, chucky_y + 15, 12, 8), 0.2, 2.8, 3)
        pygame.draw.arc(tela, (139, 69, 19), (chucky_x + 30, chucky_y + 15, 12, 8), 0.3, 2.9, 3)
        
        # Rugas de expressão na testa
        pygame.draw.line(tela, (220, 190, 150), (chucky_x + 22, chucky_y + 14), (chucky_x + 26, chucky_y + 13), 1)
        pygame.draw.line(tela, (220, 190, 150), (chucky_x + 34, chucky_y + 13), (chucky_x + 38, chucky_y + 14), 1)
        
        # Nariz mais definido e pontudo
        pygame.draw.polygon(tela, (240, 200, 160), [(chucky_x + 30, chucky_y + 22), 
                                                (chucky_x + 28, chucky_y + 26), 
                                                (chucky_x + 32, chucky_y + 26)])
        # Narinas
        pygame.draw.circle(tela, (200, 170, 130), (chucky_x + 29, chucky_y + 25), 1)
        pygame.draw.circle(tela, (200, 170, 130), (chucky_x + 31, chucky_y + 25), 1)
        
        # Boca característica - sorriso sinistro largo
        pygame.draw.arc(tela, (120, 0, 0), (chucky_x + 22, chucky_y + 27, 16, 8), 0, math.pi, 3)
        
        # Dentes mais detalhados
        for i in range(6):
            pygame.draw.rect(tela, (245, 245, 220), (chucky_x + 24 + i*2, chucky_y + 29, 1, 3))
        
        # Lábios
        pygame.draw.arc(tela, (200, 120, 120), (chucky_x + 22, chucky_y + 27, 16, 6), 0, math.pi, 1)
        
        # Sardas características do Chucky (padrão fixo)
        sardas_pos = [
            (chucky_x + 19, chucky_y + 20), (chucky_x + 17, chucky_y + 23), (chucky_x + 21, chucky_y + 25),
            (chucky_x + 39, chucky_y + 19), (chucky_x + 41, chucky_y + 22), (chucky_x + 37, chucky_y + 24),
            (chucky_x + 26, chucky_y + 19), (chucky_x + 34, chucky_y + 20), (chucky_x + 30, chucky_y + 24)
        ]
        
        for x_sarda, y_sarda in sardas_pos:
            pygame.draw.circle(tela, (200, 150, 100), (x_sarda, y_sarda), 1)
        
        # Cicatrizes icônicas do Chucky
        # Cicatriz na bochecha esquerda
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 18, chucky_y + 22), (chucky_x + 16, chucky_y + 26), 2)
        pygame.draw.line(tela, (180, 100, 100), (chucky_x + 17, chucky_y + 23), (chucky_x + 15, chucky_y + 25), 1)
        
        # Cicatriz na bochecha direita
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 42, chucky_y + 24), (chucky_x + 44, chucky_y + 28), 2)
        pygame.draw.line(tela, (180, 100, 100), (chucky_x + 43, chucky_y + 25), (chucky_x + 45, chucky_y + 27), 1)
        
        # Cicatriz pequena na testa
        pygame.draw.line(tela, (160, 80, 80), (chucky_x + 28, chucky_y + 16), (chucky_x + 26, chucky_y + 18), 1)
        
        # Sombras para dar profundidade ao rosto
        pygame.draw.arc(tela, (230, 190, 150), (chucky_x + 16, chucky_y + 20, 8, 10), 1.5, 3.0, 2)
        pygame.draw.arc(tela, (230, 190, 150), (chucky_x + 36, chucky_y + 20, 8, 10), 0, 1.5, 2)
        
        # ===== FACA MELHORADA E MAIS BONITA =====
        
        # Base da mão direita
        mao_x = chucky_x + 47
        mao_y = chucky_y + 60

        # Parâmetros de inclinação e tamanho da faca
        angle = math.radians(-35)  # ângulo da faca
        handle_len = 15
        blade_len = 35
        
        # Vetores de direção
        dx_h = math.cos(angle) * handle_len
        dy_h = math.sin(angle) * handle_len
        dx_b = math.cos(angle) * blade_len
        dy_b = math.sin(angle) * blade_len
        
        # Vetor perpendicular para espessura
        perp_angle = angle + math.pi/2
        
        # ===== CABO DETALHADO =====
        
        # Base do cabo (madeira escura)
        cabo_points = []
        cabo_width = 4
        for i in range(4):
            factor = i / 3.0
            px = mao_x + dx_h * factor
            py = mao_y + dy_h * factor
            width = cabo_width - i * 0.5  # afunila levemente
            
            perp_dx = math.cos(perp_angle) * width / 2
            perp_dy = math.sin(perp_angle) * width / 2
            
            if i == 0:
                cabo_points.extend([(px + perp_dx, py + perp_dy), (px - perp_dx, py - perp_dy)])
            elif i == 3:
                cabo_points.extend([(px - perp_dx, py - perp_dy), (px + perp_dx, py + perp_dy)])
        
        # Desenhar cabo (madeira)
        pygame.draw.polygon(tela, (101, 67, 33), cabo_points)
        
        # Detalhes do cabo (textura de madeira)
        for i in range(3):
            start_x = mao_x + dx_h * (i / 3.0) * 0.8
            start_y = mao_y + dy_h * (i / 3.0) * 0.8
            end_x = mao_x + dx_h * ((i + 1) / 3.0) * 0.8
            end_y = mao_y + dy_h * ((i + 1) / 3.0) * 0.8
            pygame.draw.line(tela, (80, 50, 25), (start_x, start_y), (end_x, end_y), 1)
        
        # Pommel (extremidade do cabo)
        pommel_x = mao_x - dx_h * 0.1
        pommel_y = mao_y - dy_h * 0.1
        pygame.draw.circle(tela, (70, 45, 20), (int(pommel_x), int(pommel_y)), 3)
        pygame.draw.circle(tela, (50, 30, 15), (int(pommel_x), int(pommel_y)), 2)
        
        # ===== GUARDA (CROSSGUARD) =====
        
        guard_start_x = mao_x + dx_h
        guard_start_y = mao_y + dy_h
        guard_length = 8
        guard_thickness = 2
        
        # Pontos da guarda
        guard_perp_dx = math.cos(perp_angle) * guard_length / 2
        guard_perp_dy = math.sin(perp_angle) * guard_length / 2
        
        guard_points = [
            (guard_start_x + guard_perp_dx, guard_start_y + guard_perp_dy),
            (guard_start_x - guard_perp_dx, guard_start_y - guard_perp_dy),
            (guard_start_x - guard_perp_dx + dx_b * 0.05, guard_start_y - guard_perp_dy + dy_b * 0.05),
            (guard_start_x + guard_perp_dx + dx_b * 0.05, guard_start_y + guard_perp_dy + dy_b * 0.05)
        ]
        
        # Desenhar guarda (metal escuro)
        pygame.draw.polygon(tela, (60, 60, 60), guard_points)
        
        # Brilho na guarda
        pygame.draw.line(tela, (120, 120, 120), 
                        (guard_start_x + guard_perp_dx * 0.7, guard_start_y + guard_perp_dy * 0.7),
                        (guard_start_x - guard_perp_dx * 0.7, guard_start_y - guard_perp_dy * 0.7), 2)
        
        # ===== LÂMINA DETALHADA =====
        
        blade_start_x = guard_start_x
        blade_start_y = guard_start_y
        blade_end_x = blade_start_x + dx_b
        blade_end_y = blade_start_y + dy_b
        
        # Largura da lâmina (afunila até a ponta)
        blade_base_width = 6
        blade_tip_width = 1
        
        # Pontos da lâmina
        blade_points = []
        
        # Base da lâmina (larga)
        base_perp_dx = math.cos(perp_angle) * blade_base_width / 2
        base_perp_dy = math.sin(perp_angle) * blade_base_width / 2
        
        # Meio da lâmina
        mid_x = blade_start_x + dx_b * 0.7
        mid_y = blade_start_y + dy_b * 0.7
        mid_perp_dx = math.cos(perp_angle) * blade_tip_width / 2
        mid_perp_dy = math.sin(perp_angle) * blade_tip_width / 2
        
        # Construir polígono da lâmina
        blade_points = [
            (blade_start_x + base_perp_dx, blade_start_y + base_perp_dy),  # base direita
            (mid_x + mid_perp_dx, mid_y + mid_perp_dy),                   # meio direita
            (blade_end_x, blade_end_y),                                   # ponta
            (mid_x - mid_perp_dx, mid_y - mid_perp_dy),                   # meio esquerda
            (blade_start_x - base_perp_dx, blade_start_y - base_perp_dy)  # base esquerda
        ]
        
        # Desenhar lâmina principal (aço brilhante)
        pygame.draw.polygon(tela, (200, 200, 210), blade_points)
        
        # Sombra na lâmina (lado inferior)
        shadow_points = [
            (blade_start_x - base_perp_dx, blade_start_y - base_perp_dy),
            (mid_x - mid_perp_dx, mid_y - mid_perp_dy),
            (blade_end_x, blade_end_y),
            (blade_start_x, blade_start_y)
        ]
        pygame.draw.polygon(tela, (160, 160, 170), shadow_points)
        
        # Fio da lâmina (linha mais escura)
        pygame.draw.line(tela, (140, 140, 150), 
                        (mid_x + mid_perp_dx, mid_y + mid_perp_dy),
                        (blade_end_x, blade_end_y), 2)
        pygame.draw.line(tela, (140, 140, 150), 
                        (mid_x - mid_perp_dx, mid_y - mid_perp_dy),
                        (blade_end_x, blade_end_y), 2)
        
        # Sulco central (fuller)
        fuller_start_x = blade_start_x + dx_b * 0.1
        fuller_start_y = blade_start_y + dy_b * 0.1
        fuller_end_x = blade_start_x + dx_b * 0.8
        fuller_end_y = blade_start_y + dy_b * 0.8
        pygame.draw.line(tela, (180, 180, 190), 
                        (fuller_start_x, fuller_start_y),
                        (fuller_end_x, fuller_end_y), 2)

    def _iniciar_movimento_chucky(self):
        """Inicia o movimento aleatório do Chucky."""
        # Definir velocidade inicial aleatória
        self.velocidade_x = random.uniform(-self.velocidade_max, self.velocidade_max)
        self.velocidade_y = random.uniform(-self.velocidade_max, self.velocidade_max)
        self.mudanca_direcao_timer = self.intervalo_mudanca_direcao

    def _atualizar_movimento_chucky(self):
        """Atualiza o movimento louco do Chucky."""
        if not self.chucky_ativo:
            return
        
        # Mudar direção periodicamente
        self.mudanca_direcao_timer -= 1
        if self.mudanca_direcao_timer <= 0:
            # Nova direção aleatória
            self.velocidade_x = random.uniform(-self.velocidade_max, self.velocidade_max)
            self.velocidade_y = random.uniform(-self.velocidade_max, self.velocidade_max)
            self.mudanca_direcao_timer = random.randint(8, 25)  # Entre 0.25 e 0.75 segundos
        
        # Mover o Chucky
        self.x += self.velocidade_x
        self.y += self.velocidade_y
        
        # Manter dentro dos limites da arena com bounce
        if self.x <= 0 or self.x >= LARGURA - 60:
            self.velocidade_x = -self.velocidade_x
            self.x = max(0, min(LARGURA - 60, self.x))
        
        if self.y <= 0 or self.y >= ALTURA_JOGO - 80:
            self.velocidade_y = -self.velocidade_y
            self.y = max(0, min(ALTURA_JOGO - 80, self.y))
        
        # Atualizar hitbox
        self.chucky_rect.x = self.x
        self.chucky_rect.y = self.y

    def verificar_colisao_inimigos(self, inimigos):
        """
        Verifica colisão com inimigos e causa dano.
        
        Args:
            inimigos: Lista de inimigos para verificar colisão
            
        Returns:
            bool: True se houve colisão e dano, False caso contrário
        """
        if not self.chucky_ativo:
            return False
        
        for inimigo in inimigos:
            if inimigo.vidas > 0 and self.chucky_rect.colliderect(inimigo.rect):
                # Causar dano ao inimigo
                if inimigo.tomar_dano():
                    # Empurrar o Chucky para longe do inimigo (efeito de ricochete)
                    direcao_x = self.x - inimigo.x
                    direcao_y = self.y - inimigo.y
                    magnitude = math.sqrt(direcao_x**2 + direcao_y**2)
                    
                    if magnitude > 0:
                        self.velocidade_x = (direcao_x / magnitude) * self.velocidade_max * 1.5
                        self.velocidade_y = (direcao_y / magnitude) * self.velocidade_max * 1.5
                    
                    return True
        
        return False


def desenhar_pentagrama(tela, centro_x, centro_y, raio, cor, espessura, crescendo=False, progresso=1.0):
    """Desenha uma estrela satânica (pentagrama invertido) com efeitos sangrentos aprimorados"""
    
    # Cores sanguinolentas mais intensas
    if cor == (255, 0, 0) or cor[0] > cor[1] and cor[0] > cor[2]:
        vermelho_escuro = (100, 0, 0)     # Dark red mais profundo
        vermelho_sangue = (255, 10, 10)   # Blood red mais intenso  
        vermelho_claro = (255, 80, 20)    # Red orange mais vibrante
        vermelho_brilhante = (255, 40, 40) # Novo: vermelho brilhante
    else:
        vermelho_escuro = (max(0, cor[0] - 120), max(0, cor[1] - 60), max(0, cor[2] - 60))
        vermelho_sangue = cor
        vermelho_claro = (min(255, cor[0] + 60), min(255, cor[1] + 40), min(255, cor[2] + 40))
        vermelho_brilhante = (min(255, cor[0] + 40), min(255, cor[1] + 20), min(255, cor[2] + 20))
    
    preto = (0, 0, 0)
    preto_profundo = (20, 0, 0)
    
    # MELHORADO: Círculos com efeito de sangue escorrendo mais dramático
    for offset in range(12, 0, -1):  # Mais camadas para efeito mais rico
        intensidade = 1.0 - (offset / 12.0)
        cor_atual = (
            int(vermelho_escuro[0] * intensidade + 30),
            int(vermelho_escuro[1] * intensidade),
            int(vermelho_escuro[2] * intensidade)
        )
        
        # Efeito de gotejamento assimétrico
        offset_y = offset if offset % 2 == 0 else offset // 2
        pygame.draw.circle(tela, cor_atual, (centro_x, centro_y + offset_y), 
                         raio + offset * 2, espessura + offset)
    
    # NOVO: Círculo de energia sombria
    pygame.draw.circle(tela, preto_profundo, (centro_x, centro_y), raio + 8, espessura * 3)
    
    # Círculos principais mais imponentes
    pygame.draw.circle(tela, vermelho_sangue, (centro_x, centro_y), raio, espessura * 3)
    pygame.draw.circle(tela, vermelho_brilhante, (centro_x, centro_y), raio - 3, espessura * 2)
    pygame.draw.circle(tela, vermelho_escuro, (centro_x, centro_y), raio - 8, espessura)
    
    # Calcular pontos da estrela com rotação diagonal aprimorada
    pontos = []
    rotacao_diagonal = math.pi / 5
    
    for i in range(5):
        angulo = (i * 2 * math.pi / 5) - math.pi/2 + rotacao_diagonal
        x = centro_x + raio * 0.85 * math.cos(angulo)  # Levemente maior
        y = centro_y + raio * 0.85 * math.sin(angulo)
        pontos.append((x, y))
    
    # MELHORADO: Linhas da estrela com efeito mais terrorífico
    for i in range(5):
        inicio = pontos[i]
        fim = pontos[(i + 2) % 5]
        
        # Múltiplas sombras para profundidade
        for sombra in range(3, 0, -1):
            pygame.draw.line(tela, (sombra * 10, 0, 0), 
                           (inicio[0] + sombra, inicio[1] + sombra), 
                           (fim[0] + sombra, fim[1] + sombra), 
                           espessura * 4)
        
        # Linha base escura mais grossa
        pygame.draw.line(tela, preto, inicio, fim, espessura * 5)
        
        # Linha intermediária 
        pygame.draw.line(tela, vermelho_escuro, inicio, fim, espessura * 3)
        
        # Linha principal brilhante
        pygame.draw.line(tela, vermelho_sangue, inicio, fim, espessura * 2)
        
        # NOVO: Linha de energia no centro
        pygame.draw.line(tela, vermelho_brilhante, inicio, fim, espessura)
    
    # MELHORADO: Mais gotas de sangue com efeitos aprimorados
    tempo = pygame.time.get_ticks()
    raio_int = int(raio)  # Garantir que raio seja inteiro para random.randint
    
    # Mais gotas durante crescimento
    num_gotas = int(30 * progresso) if crescendo else 20
    for i in range(num_gotas):
        # Posição com movimento sutil
        if crescendo:
            # Durante crescimento: gotas aparecem gradualmente do centro
            distancia_gota = random.randint(0, int(raio_int * progresso + 40))
            angulo_gota = random.uniform(0, 2 * math.pi)
            base_x = centro_x + distancia_gota * math.cos(angulo_gota)
            base_y = centro_y + distancia_gota * math.sin(angulo_gota)
        else:
            base_x = centro_x + random.randint(-raio_int - 40, raio_int + 40)
            base_y = centro_y + random.randint(-raio_int - 40, raio_int + 40)
        
        movimento_x = math.sin(tempo * 0.005 + i) * 3
        movimento_y = math.cos(tempo * 0.003 + i) * 2
        
        gota_x = base_x + movimento_x
        gota_y = base_y + movimento_y
        
        tamanho_gota = random.randint(3, 9)
        
        # Gota com múltiplas camadas
        pygame.draw.circle(tela, vermelho_escuro, (int(gota_x), int(gota_y)), tamanho_gota + 1)
        pygame.draw.circle(tela, vermelho_sangue, (int(gota_x), int(gota_y)), tamanho_gota)
        pygame.draw.circle(tela, vermelho_brilhante, (int(gota_x), int(gota_y)), tamanho_gota // 2)
        
        # Rastro da gota mais longo
        for j in range(3):
            rastro_y = gota_y + tamanho_gota + j * 3
            rastro_size = max(1, tamanho_gota - j * 2)
            pygame.draw.circle(tela, vermelho_escuro, (int(gota_x), int(rastro_y)), rastro_size)
    
    # MELHORADO: Respingos nas pontas mais dramáticos
    for ponto in pontos:
        for _ in range(4):  # Mais respingos por ponta
            distancia = random.randint(5, 25)
            angulo = random.uniform(0, 2 * math.pi)
            
            respingo_x = int(ponto[0]) + distancia * math.cos(angulo)
            respingo_y = int(ponto[1]) + distancia * math.sin(angulo)
            tamanho = random.randint(2, 6)
            
            # Respingo com brilho
            pygame.draw.circle(tela, vermelho_escuro, (respingo_x + 1, respingo_y + 1), tamanho + 1)
            pygame.draw.circle(tela, vermelho_claro, (respingo_x, respingo_y), tamanho)
            pygame.draw.circle(tela, vermelho_brilhante, (respingo_x, respingo_y), tamanho // 2)
    
    # NOVO: Símbolos místicos nos vértices internos
    for i, ponto in enumerate(pontos):
        simbolo_x = int(centro_x + (ponto[0] - centro_x) * 0.3)
        simbolo_y = int(centro_y + (ponto[1] - centro_y) * 0.3)
        
        # Pequenos círculos místicos
        pygame.draw.circle(tela, vermelho_brilhante, (simbolo_x, simbolo_y), 4)
        pygame.draw.circle(tela, preto, (simbolo_x, simbolo_y), 2)
    
    # NOVO: Centro do pentagrama com símbolo especial
    centro_raio = 12
    pygame.draw.circle(tela, preto, (centro_x, centro_y), centro_raio + 2)
    pygame.draw.circle(tela, vermelho_sangue, (centro_x, centro_y), centro_raio)
    pygame.draw.circle(tela, vermelho_brilhante, (centro_x, centro_y), centro_raio - 4)
    pygame.draw.circle(tela, preto, (centro_x, centro_y), 3)


# Lista global para gerenciar invocações ativas
invocacoes_ativas = []

def criar_invocacao_chucky(pos_mouse=None):
    """
    Cria uma nova invocação do Chucky sempre no centro da arena.
    O parâmetro pos_mouse é ignorado - sempre aparece no centro.
    """
    # Limitar a uma invocação por vez
    if len(invocacoes_ativas) == 0:
        invocacao = ChuckyInvocation()  # Sem parâmetros - sempre no centro
        invocacoes_ativas.append(invocacao)
        return True
    return False
def atualizar_invocacoes():
    """Atualiza todas as invocações ativas."""
    for invocacao in invocacoes_ativas[:]:
        if not invocacao.atualizar():
            invocacoes_ativas.remove(invocacao)

def atualizar_invocacoes_com_inimigos(inimigos, particulas, flashes):
    """
    Atualiza todas as invocações ativas e verifica colisões com inimigos.
    
    Args:
        inimigos: Lista de inimigos
        particulas: Lista de partículas para efeitos visuais
        flashes: Lista de flashes para efeitos visuais
    """
    for invocacao in invocacoes_ativas[:]:
        if not invocacao.atualizar():
            invocacoes_ativas.remove(invocacao)
        else:
            # Verificar colisões com inimigos
            if invocacao.verificar_colisao_inimigos(inimigos):
                # Adicionar efeito de explosão nas partículas
                from src.entities.particula import criar_explosao
                explosao = criar_explosao(
                    invocacao.x + 30,  # Centro do Chucky
                    invocacao.y + 40,
                    (255, 50, 50),  # Vermelho sangue
                    particulas,
                    30
                )
                flashes.append(explosao)

def desenhar_invocacoes(tela):
    """Desenha todas as invocações ativas."""
    for invocacao in invocacoes_ativas:
        invocacao.desenhar(tela)

def tem_invocacao_ativa():
    """Verifica se há alguma invocação ativa."""
    return len(invocacoes_ativas) > 0

def limpar_invocacoes():
    """Limpa todas as invocações ativas (usar ao trocar de fase)."""
    global invocacoes_ativas
    invocacoes_ativas.clear()