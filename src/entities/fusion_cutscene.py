#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cutscene de fusão para a fase 10 - Boss Fight.
Animação épica de inimigos se fundindo para formar o boss final.
"""

import pygame
import math
import random
import os
from src.config import *
from src.entities.inimigo_factory import InimigoFactory
from src.entities.particula import criar_explosao
from src.utils.visual import desenhar_texto
from src.utils.sound import gerar_som_explosao
from src.utils.display_manager import present_frame

class FusionCutscene:
    """
    Gerencia a cutscene de fusão que acontece no início da fase 10.
    """

    def __init__(self, gradiente_jogo=None, estrelas=None, jogador=None):
        self.estado = "preparacao"  # preparacao -> convergencia -> fusao -> final
        self.tempo_inicio = 0
        self.inimigos_fusao = []
        self.particulas = []
        self.flashes = []
        self.energia_central = []
        self.intensidade_shake = 0
        self.som_fusao_tocando = False

        # Sistema de música
        self.musica_boss_iniciada = False
        self.musica_boss_path = "song_boss.mp3"  # Caminho para o arquivo de música

        # Configurações da animação
        self.duracao_total = 8000  # 8 segundos
        self.centro_fusao_x = LARGURA - 200
        self.centro_fusao_y = ALTURA_JOGO // 2

        # Efeitos visuais
        self.brilho_intensidade = 0
        self.ondas_energia = []
        self.texto_atual = ""
        self.mostrar_texto = False

        # Fundo da arena
        self.gradiente_jogo = gradiente_jogo
        self.estrelas = estrelas if estrelas is not None else []

        # Jogador
        self.jogador = jogador
    
    def carregar_musica_boss(self):
        """Carrega e inicializa a música do boss."""
        try:
            # Verificar se o arquivo existe
            if os.path.exists(self.musica_boss_path):
                pygame.mixer.music.load(self.musica_boss_path)
                print(f"🎵 Música do boss carregada: {self.musica_boss_path}")
                return True
            else:
                print(f"⚠️ Arquivo de música não encontrado: {self.musica_boss_path}")
                return False
        except pygame.error as e:
            print(f"❌ Erro ao carregar música do boss: {e}")
            return False
    
    def iniciar_musica_boss(self):
        """Inicia a reprodução da música do boss."""
        try:
            if self.carregar_musica_boss():
                # Parar qualquer música que esteja tocando
                pygame.mixer.music.stop()
                
                # Iniciar a música do boss do começo
                pygame.mixer.music.play(-1)  # -1 = loop infinito
                pygame.mixer.music.set_volume(0.7)  # Volume a 70%
                
                self.musica_boss_iniciada = True
                print("🎵 Música do boss iniciada!")
                return True
            return False
        except pygame.error as e:
            print(f"❌ Erro ao reproduzir música do boss: {e}")
            return False
    
    def parar_musica_boss(self):
        """Para a música do boss."""
        try:
            pygame.mixer.music.stop()
            self.musica_boss_iniciada = False
            print("🔇 Música do boss parada.")
        except pygame.error as e:
            print(f"❌ Erro ao parar música do boss: {e}")
    
    def iniciar(self, tempo_atual):
        """Inicia a cutscene de fusão."""
        self.tempo_inicio = tempo_atual
        self.estado = "preparacao"
        self.criar_inimigos_fusao()
        
        # INICIAR A MÚSICA DO BOSS
        self.iniciar_musica_boss()
        
        print("🎬 Iniciando cutscene de fusão melhorada...")
    
    def criar_inimigos_fusao(self):
        """Cria os inimigos que serão fundidos."""
        # Criar 8 inimigos vermelhos em círculo (todos da mesma cor)
        num_inimigos = 8
        raio_inicial = 300
        
        for i in range(num_inimigos):
            angulo = (2 * math.pi * i) / num_inimigos
            x = self.centro_fusao_x + raio_inicial * math.cos(angulo)
            y = self.centro_fusao_y + raio_inicial * math.sin(angulo)
            
            # Garantir que ficam na tela
            x = max(50, min(x, LARGURA - 50))
            y = max(50, min(y, ALTURA_JOGO - 50))
            
            # TODOS os inimigos são vermelhos básicos para a cutscene
            inimigo = InimigoFactory.criar_inimigo_basico(x, y)
            
            # GARANTIR que todos têm a cor VERMELHO do config
            inimigo.cor = VERMELHO
            inimigo.cor_escura = tuple(max(0, c - 50) for c in VERMELHO)
            inimigo.cor_brilhante = tuple(min(255, c + 70) for c in VERMELHO)
            
            # Propriedades especiais para a fusão
            inimigo.angulo_original = angulo
            inimigo.raio_atual = raio_inicial
            inimigo.velocidade_fusao = 0
            inimigo.brilho_fusao = 0
            inimigo.particulas_proprias = []
            
            self.inimigos_fusao.append(inimigo)
    
    def atualizar(self, tempo_atual, tela, relogio):
        """
        Atualiza e executa a cutscene com fundo preto.
        
        Returns:
            True se a cutscene terminou, False caso contrário
        """
        tempo_decorrido = tempo_atual - self.tempo_inicio
        progresso = min(1.0, tempo_decorrido / self.duracao_total)
        
        # Determinar estado atual baseado no progresso
        if progresso < 0.2:
            self.estado = "preparacao"
        elif progresso < 0.6:
            self.estado = "convergencia"
        elif progresso < 0.9:
            self.estado = "fusao"
        else:
            self.estado = "final"
        
        # Atualizar baseado no estado
        if self.estado == "preparacao":
            self.atualizar_preparacao(tempo_decorrido)
        elif self.estado == "convergencia":
            self.atualizar_convergencia(tempo_decorrido)
        elif self.estado == "fusao":
            self.atualizar_fusao(tempo_decorrido)
        elif self.estado == "final":
            self.atualizar_final(tempo_decorrido)
        
        # Atualizar efeitos visuais
        self.atualizar_efeitos(tempo_atual)
        
        # Desenhar a cutscene (com fundo preto)
        self.desenhar(tela, tempo_atual)
        
        # Apresentar frame
        present_frame()
        relogio.tick(FPS)
        
        # Verificar se terminou
        cutscene_terminou = progresso >= 1.0
        
        # Se a cutscene terminou, manter a música tocando para o boss fight
        if cutscene_terminou:
            print("🎬 Cutscene terminada - música continua para o boss fight")
        
        return cutscene_terminou
    
    def finalizar_cutscene(self):
        """Método chamado quando a cutscene termina - NÃO para a música."""
        # A música continua tocando para o boss fight
        print("🎵 Cutscene finalizada - música do boss continua...")
    
    def parar_musica_definitivamente(self):
        """Para a música definitivamente (quando sair do boss fight)."""
        self.parar_musica_boss()
        print("🔇 Música do boss parada definitivamente.")
    
    def atualizar_preparacao(self, tempo_decorrido):
        """Fase de preparação - inimigos se posicionam e começam a brilhar."""
        self.texto_atual = "Os inimigos sentem uma força estranha..."
        self.mostrar_texto = True
        
        # Inimigos começam a brilhar e vibrar
        for inimigo in self.inimigos_fusao:
            inimigo.brilho_fusao = min(255, tempo_decorrido / 10)
            
            # Pequena vibração
            inimigo.x += random.uniform(-2, 2)
            inimigo.y += random.uniform(-2, 2)
            inimigo.rect.x = inimigo.x
            inimigo.rect.y = inimigo.y
            
            # Criar partículas de energia
            if random.random() < 0.3:
                particula = {
                    'x': inimigo.x + inimigo.tamanho // 2,
                    'y': inimigo.y + inimigo.tamanho // 2,
                    'dx': random.uniform(-1, 1),
                    'dy': random.uniform(-1, 1),
                    'vida': 30,
                    'cor': (255, 255, 100),
                    'tamanho': 3
                }
                inimigo.particulas_proprias.append(particula)
    
    def atualizar_convergencia(self, tempo_decorrido):
        """Fase de convergência - inimigos se movem em direção ao centro."""
        self.texto_atual = "Uma energia poderosa os atrai..."
        
        # Calcular velocidade de convergência
        velocidade_base = 2.0
        aceleracao = (tempo_decorrido - 1600) / 1000  # Acelera após 1.6s
        
        for inimigo in self.inimigos_fusao:
            # Calcular direção para o centro
            dx = self.centro_fusao_x - (inimigo.x + inimigo.tamanho // 2)
            dy = self.centro_fusao_y - (inimigo.y + inimigo.tamanho // 2)
            distancia = math.sqrt(dx**2 + dy**2)
            
            if distancia > 5:
                # Normalizar e aplicar velocidade
                dx /= distancia
                dy /= distancia
                
                velocidade_atual = velocidade_base * (1 + aceleracao)
                inimigo.x += dx * velocidade_atual
                inimigo.y += dy * velocidade_atual
                inimigo.rect.x = inimigo.x
                inimigo.rect.y = inimigo.y
            
            # Intensificar brilho
            inimigo.brilho_fusao = min(255, 100 + tempo_decorrido / 5)
            
            # Mais partículas de energia
            if random.random() < 0.5:
                for _ in range(2):
                    particula = {
                        'x': inimigo.x + random.randint(0, inimigo.tamanho),
                        'y': inimigo.y + random.randint(0, inimigo.tamanho),
                        'dx': random.uniform(-3, 3),
                        'dy': random.uniform(-3, 3),
                        'vida': 40,
                        'cor': random.choice([(255, 200, 0), (255, 100, 255), (100, 255, 100)]),
                        'tamanho': 4
                    }
                    inimigo.particulas_proprias.append(particula)
        
        # Criar ondas de energia no centro
        if random.random() < 0.1:
            onda = {
                'x': self.centro_fusao_x,
                'y': self.centro_fusao_y,
                'raio': 0,
                'vida': 60,
                'cor': (200, 100, 255)
            }
            self.ondas_energia.append(onda)
    
    def atualizar_fusao(self, tempo_decorrido):
        """Fase de fusão - inimigos se fundem em uma explosão de energia."""
        self.texto_atual = "A FUSÃO COMEÇA!"
        
        # Tocar som de fusão
        if not self.som_fusao_tocando:
            pygame.mixer.Channel(4).play(pygame.mixer.Sound(gerar_som_explosao()))
            self.som_fusao_tocando = True
        
        # Intensificar shake da tela
        self.intensidade_shake = min(20, (tempo_decorrido - 4800) / 50)
        
        # Inimigos desaparecem gradualmente
        for inimigo in self.inimigos_fusao:
            inimigo.brilho_fusao = 255
            
            # Encolher inimigos
            if inimigo.tamanho > 5:
                inimigo.tamanho -= 1
                inimigo.rect.width = inimigo.tamanho
                inimigo.rect.height = inimigo.tamanho
            
            # Explosão de partículas
            if random.random() < 0.8:
                for _ in range(5):
                    particula = {
                        'x': inimigo.x + inimigo.tamanho // 2,
                        'y': inimigo.y + inimigo.tamanho // 2,
                        'dx': random.uniform(-8, 8),
                        'dy': random.uniform(-8, 8),
                        'vida': 50,
                        'cor': random.choice([(255, 0, 0), (255, 255, 0), (255, 0, 255)]),
                        'tamanho': random.randint(3, 8)
                    }
                    self.particulas.append(particula)
        
        # Intensificar brilho central
        self.brilho_intensidade = min(255, (tempo_decorrido - 4800) / 10)
        
        # Criar energia no centro
        for _ in range(10):
            energia = {
                'x': self.centro_fusao_x + random.uniform(-50, 50),
                'y': self.centro_fusao_y + random.uniform(-50, 50),
                'dx': random.uniform(-2, 2),
                'dy': random.uniform(-2, 2),
                'vida': 30,
                'cor': (255, 255, 255),
                'tamanho': random.randint(5, 15)
            }
            self.energia_central.append(energia)
    
    def atualizar_final(self, tempo_decorrido):
        """Fase final - revelação do boss fusion."""
        self.texto_atual = "BOSS FUSION DESPERTA!"
        self.intensidade_shake = max(0, self.intensidade_shake - 1)
        self.brilho_intensidade = max(0, self.brilho_intensidade - 10)
        
        # Reduzir efeitos gradualmente
        if len(self.energia_central) > 0:
            self.energia_central = self.energia_central[:-2]  # Remove algumas energias
    
    def atualizar_efeitos(self, tempo_atual):
        """Atualiza todos os efeitos visuais."""
        # Atualizar partículas dos inimigos
        for inimigo in self.inimigos_fusao:
            for particula in inimigo.particulas_proprias[:]:
                particula['x'] += particula['dx']
                particula['y'] += particula['dy']
                particula['vida'] -= 1
                particula['tamanho'] -= 0.1
                
                if particula['vida'] <= 0 or particula['tamanho'] <= 0:
                    inimigo.particulas_proprias.remove(particula)
        
        # Atualizar partículas globais
        for particula in self.particulas[:]:
            particula['x'] += particula['dx']
            particula['y'] += particula['dy']
            particula['vida'] -= 1
            particula['tamanho'] -= 0.1
            
            if particula['vida'] <= 0 or particula['tamanho'] <= 0:
                self.particulas.remove(particula)
        
        # Atualizar energia central
        for energia in self.energia_central[:]:
            energia['x'] += energia['dx']
            energia['y'] += energia['dy']
            energia['vida'] -= 1
            
            if energia['vida'] <= 0:
                self.energia_central.remove(energia)
        
        # Atualizar ondas de energia
        for onda in self.ondas_energia[:]:
            onda['raio'] += 3
            onda['vida'] -= 1
            
            if onda['vida'] <= 0 or onda['raio'] > 200:
                self.ondas_energia.remove(onda)
    
    def desenhar(self, tela, tempo_atual):
        """Desenha a cutscene completa na arena."""
        # Aplicar shake da tela se necessário
        if self.intensidade_shake > 0:
            # Criar superfície temporária para o shake
            temp_surface = pygame.Surface((LARGURA, ALTURA_JOGO))
            temp_surface.fill((0, 0, 0))
            tela_desenho = temp_surface

            # Calcular offset do shake
            offset_x = random.randint(-int(self.intensidade_shake), int(self.intensidade_shake))
            offset_y = random.randint(-int(self.intensidade_shake), int(self.intensidade_shake))
        else:
            tela_desenho = tela
            offset_x = 0
            offset_y = 0

        # Desenhar fundo da arena (gradiente + estrelas)
        tela_desenho.fill((0, 0, 0))
        if self.gradiente_jogo is not None:
            tela_desenho.blit(self.gradiente_jogo, (0, 0))

        # Desenhar estrelas
        if self.estrelas:
            from src.utils.visual import desenhar_estrelas
            desenhar_estrelas(tela_desenho, self.estrelas)

        # Desenhar o jogador (se fornecido)
        if self.jogador is not None:
            # Salvar estados temporariamente
            invulneravel_original = self.jogador.invulneravel
            espingarda_ativa_original = getattr(self.jogador, 'espingarda_ativa', False)
            metralhadora_ativa_original = getattr(self.jogador, 'metralhadora_ativa', False)
            desert_eagle_ativa_original = getattr(self.jogador, 'desert_eagle_ativa', False)
            granada_selecionada_original = getattr(self.jogador, 'granada_selecionada', False)
            dimensional_hop_selecionado_original = getattr(self.jogador, 'dimensional_hop_selecionado', False)
            ampulheta_selecionada_original = getattr(self.jogador, 'ampulheta_selecionada', False)
            amuleto_ativo_original = getattr(self.jogador, 'amuleto_ativo', False)
            sabre_equipado_original = getattr(self.jogador, 'sabre_equipado', False)

            # Desativar invulnerabilidade e armas temporariamente
            self.jogador.invulneravel = False
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = False
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = False
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = False
            if hasattr(self.jogador, 'granada_selecionada'):
                self.jogador.granada_selecionada = False
            if hasattr(self.jogador, 'dimensional_hop_selecionado'):
                self.jogador.dimensional_hop_selecionado = False
            if hasattr(self.jogador, 'ampulheta_selecionada'):
                self.jogador.ampulheta_selecionada = False
            if hasattr(self.jogador, 'amuleto_ativo'):
                self.jogador.amuleto_ativo = False
            if hasattr(self.jogador, 'sabre_equipado'):
                self.jogador.sabre_equipado = False

            # Desenhar o jogador
            self.jogador.desenhar(tela_desenho, tempo_atual)

            # Restaurar estados
            self.jogador.invulneravel = invulneravel_original
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = espingarda_ativa_original
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = metralhadora_ativa_original
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = desert_eagle_ativa_original
            if hasattr(self.jogador, 'granada_selecionada'):
                self.jogador.granada_selecionada = granada_selecionada_original
            if hasattr(self.jogador, 'dimensional_hop_selecionado'):
                self.jogador.dimensional_hop_selecionado = dimensional_hop_selecionado_original
            if hasattr(self.jogador, 'ampulheta_selecionada'):
                self.jogador.ampulheta_selecionada = ampulheta_selecionada_original
            if hasattr(self.jogador, 'amuleto_ativo'):
                self.jogador.amuleto_ativo = amuleto_ativo_original
            if hasattr(self.jogador, 'sabre_equipado'):
                self.jogador.sabre_equipado = sabre_equipado_original

        # Desenhar ondas de energia
        for onda in self.ondas_energia:
            alpha = int(255 * (onda['vida'] / 60))
            pygame.draw.circle(tela_desenho, onda['cor'], 
                             (int(onda['x']), int(onda['y'])), 
                             int(onda['raio']), 3)
        
        # Desenhar energia central
        for energia in self.energia_central:
            if energia['tamanho'] > 0:
                pygame.draw.circle(tela_desenho, energia['cor'], 
                                 (int(energia['x']), int(energia['y'])), 
                                 int(energia['tamanho']))
        
        # Desenhar brilho central intenso
        if self.brilho_intensidade > 0:
            for raio in range(3, 100, 10):
                alpha = max(0, self.brilho_intensidade - raio * 3)
                if alpha > 0:
                    pygame.draw.circle(tela_desenho, (255, 255, 255), 
                                     (self.centro_fusao_x, self.centro_fusao_y), 
                                     raio, 2)
        
        # Desenhar inimigos em fusão
        for inimigo in self.inimigos_fusao:
            if inimigo.tamanho > 0:
                # Desenhar o inimigo manualmente (sem barra de vida)
                # Efeito de pulsação (copiado do método desenhar original)
                mod_tamanho = 0
                if hasattr(inimigo, 'pulsando'):
                    if inimigo.pulsando < 6:
                        mod_tamanho = inimigo.pulsando
                    else:
                        mod_tamanho = 12 - inimigo.pulsando

                # Desenhar sombra
                pygame.draw.rect(tela_desenho, (20, 20, 20),
                                (inimigo.x + 4, inimigo.y + 4,
                                 inimigo.tamanho, inimigo.tamanho), 0, 3)

                # Aplicar cor com brilho de fusão
                cor_uso = inimigo.cor
                if inimigo.brilho_fusao > 0:
                    cor_uso = tuple(min(255, c + int(inimigo.brilho_fusao)) for c in inimigo.cor)

                # Quadrado interior (cor escura)
                pygame.draw.rect(tela_desenho, inimigo.cor_escura,
                                (inimigo.x, inimigo.y,
                                 inimigo.tamanho + mod_tamanho, inimigo.tamanho + mod_tamanho), 0, 5)

                # Quadrado exterior (menor)
                pygame.draw.rect(tela_desenho, cor_uso,
                                (inimigo.x + 3, inimigo.y + 3,
                                 inimigo.tamanho + mod_tamanho - 6, inimigo.tamanho + mod_tamanho - 6), 0, 3)

                # Brilho no canto superior esquerdo
                pygame.draw.rect(tela_desenho, inimigo.cor_brilhante,
                                (inimigo.x + 5, inimigo.y + 5, 8, 8), 0, 2)

                # Partículas do inimigo
                for particula in inimigo.particulas_proprias:
                    if particula['tamanho'] > 0:
                        pygame.draw.circle(tela_desenho, particula['cor'],
                                         (int(particula['x']), int(particula['y'])),
                                         int(particula['tamanho']))
        
        # Desenhar partículas globais
        for particula in self.particulas:
            if particula['tamanho'] > 0:
                pygame.draw.circle(tela_desenho, particula['cor'], 
                                 (int(particula['x']), int(particula['y'])), 
                                 int(particula['tamanho']))
        
        # Desenhar texto da cutscene
        if self.mostrar_texto and self.texto_atual:
            desenhar_texto(tela_desenho, self.texto_atual, 48, 
                          (255, 255, 255), LARGURA // 2, 100)
            
            # Instrução para pular
            desenhar_texto(tela_desenho, "Pressione ESC para pular", 24, 
                          (200, 200, 200), LARGURA // 2, 140)
        
        # Indicador de música (opcional)
        if self.musica_boss_iniciada:
            desenhar_texto(tela_desenho, "♪ Boss Music ♪", 16, 
                          (100, 255, 100), LARGURA - 100, 30)
        
        # Aplicar shake se necessário
        if self.intensidade_shake > 0:
            tela.blit(temp_surface, (offset_x, offset_y))
    
    def get_boss_spawn_position(self):
        """Retorna a posição onde o boss deve aparecer após a fusão."""
        return self.centro_fusao_x - 50, self.centro_fusao_y - 50