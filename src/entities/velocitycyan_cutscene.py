#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cutscene do VelocityCyan - Fase 20
O jogador entra na arena, vê um único inimigo elite, comenta que será fácil,
mas o Misterioso aparece por um portal e o transforma em um boss gigante e ameaçador.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.particula import Particula
from src.utils.visual import desenhar_texto, desenhar_estrelas
from src.utils.display_manager import present_frame


class InimigoMisterioso(Quadrado):
    """Classe para o inimigo misterioso preto."""

    def __init__(self, x, y):
        """Inicializa o inimigo misterioso."""
        # Cor preta profunda com aura vermelha
        cor_preta = (20, 20, 20)
        super().__init__(x, y, TAMANHO_QUADRADO * 1.2, cor_preta, 3)

        self.vidas = 999
        self.vidas_max = 999
        self.aura_intensidade = 0
        self.particulas_sombra = []

    def desenhar_com_aura(self, tela, tempo_atual):
        """Desenha o inimigo com uma aura sinistra."""
        # Aura vermelha pulsante
        pulso = math.sin(tempo_atual / 300) * 0.3 + 0.7
        cor_aura = (int(180 * pulso), 0, int(50 * pulso))

        # Desenhar múltiplas camadas de aura
        for i in range(5, 0, -1):
            alpha = int(50 * (6 - i) / 5 * pulso)
            raio = int(self.tamanho // 2 + i * 8)
            superficie_aura = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(superficie_aura, (*cor_aura, alpha), (raio, raio), raio)
            tela.blit(superficie_aura,
                     (self.x + self.tamanho // 2 - raio,
                      self.y + self.tamanho // 2 - raio))

        # Desenhar o quadrado principal
        self.desenhar(tela, tempo_atual)

        # Borda vermelha brilhante
        pygame.draw.rect(tela, (200, 0, 0), self.rect, 3)

        # Partículas de sombra
        if random.random() < 0.3:
            particula = Particula(
                self.x + random.randint(0, int(self.tamanho)),
                self.y + random.randint(0, int(self.tamanho)),
                (50, 0, 0)
            )
            particula.velocidade_x = random.uniform(-1, 1)
            particula.velocidade_y = random.uniform(-2, -0.5)
            particula.vida = random.randint(20, 40)
            particula.tamanho = random.uniform(2, 4)
            self.particulas_sombra.append(particula)

        # Atualizar e desenhar partículas
        for particula in self.particulas_sombra[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas_sombra.remove(particula)
            else:
                particula.desenhar(tela)


class VelocityCyanCutscene:
    """
    Cutscene de introdução da boss fight do VelocityCyan - Fase 20.
    """

    def __init__(self, gradiente_jogo=None, estrelas=None, jogador=None):
        """
        Inicializa a cutscene.

        Args:
            gradiente_jogo: Gradiente de fundo da arena
            estrelas: Lista de estrelas de fundo
            jogador: Objeto do jogador (opcional)
        """
        # Fundo da arena
        self.gradiente_jogo = gradiente_jogo
        self.estrelas = estrelas if estrelas is not None else []

        # Jogador
        self.jogador = jogador

        # Posição do jogador será definida na inicialização
        self.jogador_x = 100
        self.jogador_y = ALTURA_JOGO // 2

        # Sistema de música
        self.musica_boss_iniciada = False
        self.musica_boss_path = "song_boss2.mp3"

        self.estado = "fade_in"  # fade_in -> corrida_elite -> ida_centro -> dialogo_jogador -> teletransporte_misterioso ->
                                  # laser -> transformacao -> saida_misterioso -> final
        self.tempo_inicio = 0

        # Criar inimigo elite (ciano) começando no canto superior esquerdo
        margem = 50
        self.elite = Quadrado(margem, margem, TAMANHO_QUADRADO, CIANO, 3)
        self.elite.vidas = 1
        self.elite.vidas_max = 1
        self.elite_mostrar_vida = True  # Controla se mostra a barra de vida

        # Tamanho original do elite para a transformação
        self.elite_tamanho_original = TAMANHO_QUADRADO

        # Rastro de movimento do elite
        self.rastro_elite = []

        # Efeito de vibração (similar ao boss)
        self.elite_vibrar_offset_x = 0
        self.elite_vibrar_offset_y = 0

        # Variações orgânicas na corrida
        self.variacao_corrida = 0
        self.tempo_variacao = 0

        # Misterioso (será criado depois)
        self.misterioso = None

        # Efeitos visuais
        self.particulas = []
        self.particulas_transformacao = []
        self.alpha_fade = 255  # Fade in começa totalmente preto

        # Sistema de diálogo
        self.texto_dialogo_jogador = "Só 1? Há, vai ser facil!"
        self.texto_visivel_jogador = ""
        self.indice_texto_jogador = 0
        self.tempo_ultima_letra = 0
        self.velocidade_texto = 50  # ms por letra

        # Configurações de timing
        self.duracao_fade_in = 800  # Fade in rápido (0.8 segundos)
        self.tempo_corrida_elite = 2000  # 2.0 segundos para dar a volta (mais lento e orgânico)
        self.tempo_ida_centro = 700  # 0.7 segundos para ir ao centro
        self.tempo_dialogo_jogador = 2500  # Jogador fala
        self.tempo_teletransporte_misterioso = 1200  # Efeito de teletransporte
        self.tempo_laser = 1000  # Laser atinge o elite
        self.tempo_transformacao = 2500  # Elite cresce e fica ameaçador
        self.tempo_saida_misterioso = 1500
        self.tempo_espera_final = 500

        # Teletransporte do misterioso (sem portal)
        self.misterioso_alpha = 0  # Transparência para efeito de materialização
        self.particulas_teletransporte = []

        # Laser
        self.laser_ativo = False
        self.laser_particulas = []

        # Transformação
        self.elite_transformado = False
        self.elite_escala = 1.0
        self.elite_escala_final = 3.0  # Fica 3x maior

        self.concluida = False

    def carregar_musica_boss(self):
        """Carrega e inicializa a música do boss."""
        try:
            import os
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
                pygame.mixer.music.set_volume(0.6)  # Volume a 60%

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

    def parar_musica_definitivamente(self):
        """Para a música do boss definitivamente."""
        self.parar_musica_boss()

    def get_boss_spawn_position(self):
        """Retorna a posição onde o boss deve aparecer."""
        # Boss aparece no centro onde o elite estava
        return (LARGURA // 2 - TAMANHO_QUADRADO * 1.5, ALTURA_JOGO // 2 - TAMANHO_QUADRADO * 1.5)

    def iniciar(self, tempo_atual):
        """Inicia a cutscene."""
        self.tempo_inicio = tempo_atual
        self.estado = "fade_in"

        # INICIAR A MÚSICA DO BOSS
        self.iniciar_musica_boss()

        print("🎬 Cutscene do VelocityCyan iniciada!")

    def atualizar(self, tempo_atual, tela, relogio):
        """
        Atualiza e executa a cutscene com renderização.

        Args:
            tempo_atual: Tempo atual em milissegundos
            tela: Superfície de renderização
            relogio: Clock do pygame

        Returns:
            True se a cutscene terminou, False caso contrário
        """
        # Processar eventos (permitir pular com ESC ou ENTER)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return True
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    print("⏭️ Cutscene pulada pelo jogador")
                    return True

        tempo_decorrido = tempo_atual - self.tempo_inicio

        # ESTADO: FADE IN (transição rápida do preto) + CORRIDA já começando
        if self.estado == "fade_in":
            if tempo_decorrido < self.duracao_fade_in:
                # Fade in gradual
                progresso = tempo_decorrido / self.duracao_fade_in
                self.alpha_fade = int(255 * (1 - progresso))

                # Elite já começa correndo durante o fade in
                self.atualizar_corrida_elite(tempo_decorrido)
            else:
                self.alpha_fade = 0
                self.estado = "corrida_elite"
                self.tempo_estado_atual = tempo_atual - self.duracao_fade_in  # Continua a corrida
                print("💨 Elite correndo pela arena!")

        # ESTADO: CORRIDA ELITE (elite dá uma volta pela arena)
        elif self.estado == "corrida_elite":
            tempo_estado = tempo_atual - self.tempo_inicio  # Tempo desde o início total
            if tempo_estado < self.tempo_corrida_elite:
                # Atualiza a posição da corrida
                self.atualizar_corrida_elite(tempo_estado)
            else:
                # Guarda posição final da corrida
                self.elite_pos_inicial_centro_x = self.elite.x
                self.elite_pos_inicial_centro_y = self.elite.y
                self.estado = "ida_centro"
                self.tempo_estado_atual = tempo_atual
                print("🎯 Elite indo para o centro!")

        # ESTADO: IDA AO CENTRO (elite se move ao centro após completar a volta)
        elif self.estado == "ida_centro":
            tempo_estado = tempo_atual - self.tempo_estado_atual
            if tempo_estado < self.tempo_ida_centro:
                # Movimento suave ao centro
                progresso = tempo_estado / self.tempo_ida_centro
                progresso_suave = 1 - (1 - progresso) ** 3  # Cubic ease-out

                centro_x = LARGURA // 2 - TAMANHO_QUADRADO // 2
                centro_y = ALTURA_JOGO // 2 - TAMANHO_QUADRADO // 2

                self.elite.x = self.elite_pos_inicial_centro_x + (centro_x - self.elite_pos_inicial_centro_x) * progresso_suave
                self.elite.y = self.elite_pos_inicial_centro_y + (centro_y - self.elite_pos_inicial_centro_y) * progresso_suave
                self.elite.rect.x = self.elite.x
                self.elite.rect.y = self.elite.y

                # Continua atualizando rastro
                self.atualizar_rastro_elite()
            else:
                # Para exatamente no centro da arena
                centro_x = LARGURA // 2 - TAMANHO_QUADRADO // 2
                centro_y = ALTURA_JOGO // 2 - TAMANHO_QUADRADO // 2
                self.elite.x = centro_x
                self.elite.y = centro_y
                self.elite.rect.x = self.elite.x
                self.elite.rect.y = self.elite.y

                # Limpa o rastro quando para
                self.rastro_elite = []

                self.estado = "dialogo_jogador"
                self.tempo_estado_atual = tempo_atual
                print("💬 Jogador falando...")

        # ESTADO: DIÁLOGO JOGADOR
        elif self.estado == "dialogo_jogador":
            tempo_estado = tempo_atual - self.tempo_estado_atual

            # Animação de texto (letra por letra)
            if tempo_atual - self.tempo_ultima_letra > self.velocidade_texto:
                if self.indice_texto_jogador < len(self.texto_dialogo_jogador):
                    self.texto_visivel_jogador += self.texto_dialogo_jogador[self.indice_texto_jogador]
                    self.indice_texto_jogador += 1
                    self.tempo_ultima_letra = tempo_atual

            if tempo_estado >= self.tempo_dialogo_jogador:
                self.estado = "teletransporte_misterioso"
                self.tempo_estado_atual = tempo_atual
                # Criar misterioso na posição final (lado direito)
                self.misterioso = InimigoMisterioso(LARGURA - 150, ALTURA_JOGO // 2)
                self.misterioso_alpha = 0
                print("⚡ Misterioso se teletransportando...")

        # ESTADO: TELETRANSPORTE MISTERIOSO (materialização)
        elif self.estado == "teletransporte_misterioso":
            tempo_estado = tempo_atual - self.tempo_estado_atual
            if tempo_estado < self.tempo_teletransporte_misterioso:
                # Efeito de materialização gradual
                progresso = tempo_estado / self.tempo_teletransporte_misterioso
                self.misterioso_alpha = int(255 * progresso)

                # Criar partículas de teletransporte
                self.criar_particulas_teletransporte(progresso)
            else:
                self.misterioso_alpha = 255
                self.estado = "laser"
                self.tempo_estado_atual = tempo_atual
                self.laser_ativo = True
                print("⚡ Laser ativado!")

        # ESTADO: LASER
        elif self.estado == "laser":
            tempo_estado = tempo_atual - self.tempo_estado_atual

            # Ocultar barra de vida no início do laser
            if tempo_estado == 0 or not hasattr(self, 'vida_ocultada'):
                self.elite_mostrar_vida = False
                self.vida_ocultada = True

            if tempo_estado < self.tempo_laser:
                # Criar efeito de laser
                self.criar_efeito_laser(tempo_atual)
            else:
                self.laser_ativo = False
                self.estado = "transformacao"
                self.tempo_estado_atual = tempo_atual
                print("💥 Elite transformando!")

        # ESTADO: TRANSFORMAÇÃO
        elif self.estado == "transformacao":
            tempo_estado = tempo_atual - self.tempo_estado_atual
            if tempo_estado < self.tempo_transformacao:
                # Elite cresce
                progresso = tempo_estado / self.tempo_transformacao
                progresso_suave = progresso ** 2  # Quadratic ease-in

                self.elite_escala = 1.0 + (self.elite_escala_final - 1.0) * progresso_suave
                novo_tamanho = int(self.elite_tamanho_original * self.elite_escala)
                self.elite.tamanho = novo_tamanho
                self.elite.rect.width = novo_tamanho
                self.elite.rect.height = novo_tamanho

                # Centralizar o elite enquanto cresce
                centro_x = LARGURA // 2
                centro_y = ALTURA_JOGO // 2
                self.elite.x = centro_x - novo_tamanho // 2
                self.elite.y = centro_y - novo_tamanho // 2
                self.elite.rect.x = self.elite.x
                self.elite.rect.y = self.elite.y

                # Mudar cor gradualmente para mais escura/ameaçadora
                progresso_cor = progresso_suave
                r = int(CIANO[0] * (1 - progresso_cor) + 50 * progresso_cor)
                g = int(CIANO[1] * (1 - progresso_cor) + 150 * progresso_cor)
                b = int(CIANO[2] * (1 - progresso_cor) + 200 * progresso_cor)
                self.elite.cor = (r, g, b)

                # Partículas de transformação
                self.criar_particulas_transformacao(tempo_atual)
            else:
                self.elite_transformado = True
                self.estado = "saida_misterioso"
                self.tempo_estado_atual = tempo_atual
                print("🌀 Misterioso indo embora...")

        # ESTADO: SAÍDA MISTERIOSO (desmaterialização)
        elif self.estado == "saida_misterioso":
            tempo_estado = tempo_atual - self.tempo_estado_atual
            if tempo_estado < self.tempo_saida_misterioso:
                # Efeito de desmaterialização gradual
                progresso = tempo_estado / self.tempo_saida_misterioso
                self.misterioso_alpha = int(255 * (1 - progresso))

                # Criar partículas de teletransporte reverso
                self.criar_particulas_teletransporte(1 - progresso)
            else:
                self.misterioso_alpha = 0
                self.estado = "espera_final"
                self.tempo_estado_atual = tempo_atual
                print("⏱️ Aguardando finalização...")

        # ESTADO: ESPERA FINAL
        elif self.estado == "espera_final":
            tempo_estado = tempo_atual - self.tempo_estado_atual
            if tempo_estado >= self.tempo_espera_final:
                self.estado = "final"
                self.concluida = True
                print("✅ Cutscene concluída!")
                return True

        # Atualizar rastro do elite
        for rastro in self.rastro_elite[:]:
            rastro['vida'] -= 1
            if rastro['vida'] <= 0:
                self.rastro_elite.remove(rastro)

        # Atualizar partículas
        for particula in self.particulas[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas.remove(particula)

        for particula in self.particulas_transformacao[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas_transformacao.remove(particula)

        for particula in self.laser_particulas[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.laser_particulas.remove(particula)

        # Renderizar
        tela.fill((0, 0, 0))
        if self.gradiente_jogo:
            tela.blit(self.gradiente_jogo, (0, 0))
        from src.utils.visual import desenhar_estrelas
        if self.estrelas:
            desenhar_estrelas(tela, self.estrelas)

        # Desenhar cutscene
        self.desenhar(tela, tempo_atual)

        # Texto de instrução (pode pular)
        desenhar_texto(tela, "Pressione ESC para pular", 18, (150, 150, 150),
                      LARGURA // 2, ALTURA_JOGO - 30)

        present_frame()
        relogio.tick(FPS)

        return self.concluida

    def atualizar_corrida_elite(self, tempo_estado):
        """Atualiza a posição do elite durante a corrida pela arena."""
        # Elite corre em um retângulo pela borda da arena
        progresso = tempo_estado / self.tempo_corrida_elite

        # Adiciona aceleração e desaceleração suave
        # Ease in-out para movimento mais natural
        if progresso < 0.5:
            progresso_suave = 2 * progresso * progresso
        else:
            progresso_suave = 1 - 2 * (1 - progresso) * (1 - progresso)

        # Define margens da arena
        margem = 50

        # Perímetro total da arena
        largura_arena = LARGURA - 2 * margem
        altura_arena = ALTURA_JOGO - 2 * margem
        perimetro_total = 2 * (largura_arena + altura_arena)

        # Distância percorrida com suavização
        distancia_percorrida = perimetro_total * progresso_suave

        # Calcula posição base no retângulo
        if distancia_percorrida < largura_arena:  # Lado superior (esquerda -> direita)
            self.elite.x = margem + distancia_percorrida
            self.elite.y = margem
        elif distancia_percorrida < largura_arena + altura_arena:  # Lado direito (cima -> baixo)
            self.elite.x = LARGURA - margem - TAMANHO_QUADRADO
            self.elite.y = margem + (distancia_percorrida - largura_arena)
        elif distancia_percorrida < 2 * largura_arena + altura_arena:  # Lado inferior (direita -> esquerda)
            self.elite.x = LARGURA - margem - TAMANHO_QUADRADO - (distancia_percorrida - largura_arena - altura_arena)
            self.elite.y = ALTURA_JOGO - margem - TAMANHO_QUADRADO
        else:  # Lado esquerdo (baixo -> cima)
            self.elite.x = margem
            self.elite.y = ALTURA_JOGO - margem - TAMANHO_QUADRADO - (distancia_percorrida - 2 * largura_arena - altura_arena)

        # Adiciona variação orgânica (ondulação senoidal)
        variacao_tempo = tempo_estado * 0.015  # Frequência da ondulação
        variacao_amplitude = 8  # Amplitude da ondulação em pixels

        # Ondulação perpendicular ao movimento
        if distancia_percorrida < largura_arena:  # Lado superior
            self.elite.y += math.sin(variacao_tempo) * variacao_amplitude
        elif distancia_percorrida < largura_arena + altura_arena:  # Lado direito
            self.elite.x += math.sin(variacao_tempo) * variacao_amplitude
        elif distancia_percorrida < 2 * largura_arena + altura_arena:  # Lado inferior
            self.elite.y += math.sin(variacao_tempo) * variacao_amplitude
        else:  # Lado esquerdo
            self.elite.x += math.sin(variacao_tempo) * variacao_amplitude

        self.elite.rect.x = self.elite.x
        self.elite.rect.y = self.elite.y

        # Atualizar rastro de movimento
        self.atualizar_rastro_elite()

    def atualizar_rastro_elite(self):
        """Atualiza rastro de movimento do elite (similar ao boss)."""
        self.rastro_elite.append({
            'x': self.elite.x + self.elite.tamanho // 2,
            'y': self.elite.y + self.elite.tamanho // 2,
            'vida': 15
        })

        for rastro in self.rastro_elite[:]:
            rastro['vida'] -= 1
            if rastro['vida'] <= 0:
                self.rastro_elite.remove(rastro)

        if len(self.rastro_elite) > 30:
            self.rastro_elite.pop(0)

    def desenhar_elite_customizado(self, tela, tempo_atual):
        """Desenha o elite com controle sobre a barra de vida."""
        # Salvar vidas temporariamente se não devemos mostrar a barra
        if not self.elite_mostrar_vida:
            vidas_originais = self.elite.vidas
            vidas_max_originais = self.elite.vidas_max
            # Definir vidas como 0 para que a barra não seja desenhada
            self.elite.vidas = 0
            self.elite.vidas_max = 1

        # Desenhar o elite
        self.elite.desenhar(tela, tempo_atual)

        # Restaurar vidas se foram modificadas
        if not self.elite_mostrar_vida:
            self.elite.vidas = vidas_originais
            self.elite.vidas_max = vidas_max_originais

    def criar_particulas_spawn(self, tempo_atual, entidade):
        """Cria partículas de spawn/materialização."""
        for _ in range(5):
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(30, 80)
            x = entidade.x + entidade.tamanho // 2 + math.cos(angulo) * distancia
            y = entidade.y + entidade.tamanho // 2 + math.sin(angulo) * distancia

            particula = Particula(x, y, entidade.cor)
            particula.velocidade_x = -math.cos(angulo) * 2
            particula.velocidade_y = -math.sin(angulo) * 2
            particula.vida = random.randint(20, 40)
            particula.tamanho = random.uniform(3, 6)
            self.particulas.append(particula)

    def criar_trilha_movimento(self, entidade):
        """Cria trilha de partículas durante o movimento."""
        particula = Particula(
            entidade.x + entidade.tamanho // 2,
            entidade.y + entidade.tamanho // 2,
            (80, 0, 0)
        )
        particula.velocidade_x = random.uniform(-0.5, 0.5)
        particula.velocidade_y = random.uniform(-0.5, 0.5)
        particula.vida = random.randint(15, 30)
        particula.tamanho = random.uniform(2, 4)
        self.particulas.append(particula)

    def criar_particulas_teletransporte(self, intensidade):
        """Cria partículas de teletransporte (materialização/desmaterialização)."""
        if random.random() < 0.8:
            centro_x = self.misterioso.x + self.misterioso.tamanho // 2
            centro_y = self.misterioso.y + self.misterioso.tamanho // 2

            # Partículas em espiral convergindo/divergindo
            for i in range(5):
                angulo = random.uniform(0, math.pi * 2)
                raio = random.uniform(20, 80)
                x = centro_x + math.cos(angulo) * raio
                y = centro_y + math.sin(angulo) * raio

                particula = Particula(x, y, (200, 0, 100))
                # Partículas convergem para o centro durante materialização
                particula.velocidade_x = -math.cos(angulo) * 4 * intensidade
                particula.velocidade_y = -math.sin(angulo) * 4 * intensidade
                particula.vida = random.randint(10, 20)
                particula.tamanho = random.uniform(3, 7)
                self.particulas.append(particula)

            # Partículas brilhantes no centro
            if random.random() < 0.5:
                for _ in range(3):
                    offset_x = random.uniform(-20, 20)
                    offset_y = random.uniform(-20, 20)
                    particula = Particula(centro_x + offset_x, centro_y + offset_y, (255, 100, 200))
                    particula.velocidade_x = random.uniform(-2, 2)
                    particula.velocidade_y = random.uniform(-2, 2)
                    particula.vida = random.randint(8, 15)
                    particula.tamanho = random.uniform(4, 8)
                    self.particulas.append(particula)

    def criar_efeito_laser(self, tempo_atual):
        """Cria efeito visual do laser do misterioso para o elite."""
        # Posição inicial (misterioso) e final (elite)
        origem_x = self.misterioso.x + self.misterioso.tamanho // 2
        origem_y = self.misterioso.y + self.misterioso.tamanho // 2
        destino_x = self.elite.x + self.elite.tamanho // 2
        destino_y = self.elite.y + self.elite.tamanho // 2

        # Criar partículas ao longo do laser
        for i in range(10):
            t = i / 10
            x = origem_x + (destino_x - origem_x) * t
            y = origem_y + (destino_y - origem_y) * t

            particula = Particula(x, y, (255, 0, 0))
            particula.velocidade_x = random.uniform(-2, 2)
            particula.velocidade_y = random.uniform(-2, 2)
            particula.vida = random.randint(10, 20)
            particula.tamanho = random.uniform(4, 8)
            self.laser_particulas.append(particula)

    def criar_particulas_transformacao(self, tempo_atual):
        """Cria partículas durante a transformação do elite."""
        centro_x = self.elite.x + self.elite.tamanho // 2
        centro_y = self.elite.y + self.elite.tamanho // 2

        for _ in range(8):
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(0, self.elite.tamanho // 2)
            x = centro_x + math.cos(angulo) * distancia
            y = centro_y + math.sin(angulo) * distancia

            particula = Particula(x, y, self.elite.cor)
            particula.velocidade_x = math.cos(angulo) * random.uniform(3, 6)
            particula.velocidade_y = math.sin(angulo) * random.uniform(3, 6)
            particula.vida = random.randint(20, 40)
            particula.tamanho = random.uniform(4, 8)
            self.particulas_transformacao.append(particula)

    def desenhar(self, tela, tempo_atual):
        """Desenha a cutscene."""
        # Desenhar rastro do elite (se estiver correndo)
        if self.estado in ("fade_in", "corrida_elite", "ida_centro"):
            for rastro in self.rastro_elite:
                if rastro['vida'] > 0:
                    alpha = int(255 * (rastro['vida'] / 15))
                    tamanho_rastro = max(1, int(TAMANHO_QUADRADO * (rastro['vida'] / 15) * 0.4))

                    rastro_surface = pygame.Surface((tamanho_rastro * 2, tamanho_rastro * 2), pygame.SRCALPHA)
                    rastro_surface.set_alpha(alpha // 2)
                    # Usa cor ciano brilhante (cor secundária do boss)
                    pygame.draw.rect(rastro_surface, (0, 255, 255), (0, 0, tamanho_rastro * 2, tamanho_rastro * 2))

                    tela.blit(rastro_surface, (rastro['x'] - tamanho_rastro, rastro['y'] - tamanho_rastro))

        # Desenhar o jogador (sempre visível)
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
            spas12_ativa_original = getattr(self.jogador, 'spas12_ativa', False)

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
            if hasattr(self.jogador, 'spas12_ativa'):
                self.jogador.spas12_ativa = False

            # Desenhar o jogador
            self.jogador.desenhar(tela, tempo_atual)

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
            if hasattr(self.jogador, 'spas12_ativa'):
                self.jogador.spas12_ativa = spas12_ativa_original
        else:
            # Fallback: desenhar um quadrado azul simples
            jogador_rect = pygame.Rect(self.jogador_x, self.jogador_y, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
            pygame.draw.rect(tela, AZUL, jogador_rect)
            pygame.draw.rect(tela, AZUL_ESCURO, jogador_rect, 3)

        # Desenhar elite (sempre visível)
        # Aplicar vibração durante corrida
        if self.estado in ("fade_in", "corrida_elite", "ida_centro"):
            # Vibração rápida (similar ao boss em movimento)
            self.elite_vibrar_offset_x = random.uniform(-2, 2)
            self.elite_vibrar_offset_y = random.uniform(-2, 2)

            # Salvar posição original
            pos_original_x = self.elite.x
            pos_original_y = self.elite.y

            # Aplicar vibração
            self.elite.x += self.elite_vibrar_offset_x
            self.elite.y += self.elite_vibrar_offset_y
            self.elite.rect.x = self.elite.x
            self.elite.rect.y = self.elite.y

            # Desenhar com vibração
            self.desenhar_elite_customizado(tela, tempo_atual)

            # Restaurar posição
            self.elite.x = pos_original_x
            self.elite.y = pos_original_y
            self.elite.rect.x = self.elite.x
            self.elite.rect.y = self.elite.y
        else:
            # Desenhar normalmente
            self.desenhar_elite_customizado(tela, tempo_atual)

        # Aura e efeitos especiais durante estados específicos
        if self.estado not in ("fade_in",):

            # Aura durante transformação
            if self.estado == "transformacao":
                centro_x = self.elite.x + self.elite.tamanho // 2
                centro_y = self.elite.y + self.elite.tamanho // 2
                pulso = math.sin(tempo_atual / 100) * 0.3 + 0.7

                for i in range(5, 0, -1):
                    alpha = int(80 * (6 - i) / 5 * pulso)
                    raio = int(self.elite.tamanho // 2 + i * 15)
                    superficie_aura = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                    pygame.draw.circle(superficie_aura, (*self.elite.cor, alpha), (raio, raio), raio)
                    tela.blit(superficie_aura, (centro_x - raio, centro_y - raio))

        # Desenhar misterioso (se visível) com efeito de transparência
        if self.misterioso is not None and self.estado in ("teletransporte_misterioso", "laser", "transformacao", "saida_misterioso"):
            if self.misterioso_alpha > 0:
                # Criar superfície temporária para aplicar alpha
                temp_surface = pygame.Surface((int(self.misterioso.tamanho * 2), int(self.misterioso.tamanho * 2)), pygame.SRCALPHA)

                # Desenhar o misterioso na superfície temporária
                # Salvar posição original
                pos_x_original = self.misterioso.x
                pos_y_original = self.misterioso.y

                # Desenhar na superfície temporária (ajustar posição relativa)
                self.misterioso.x = self.misterioso.tamanho // 2
                self.misterioso.y = self.misterioso.tamanho // 2
                self.misterioso.rect.x = self.misterioso.x
                self.misterioso.rect.y = self.misterioso.y

                self.misterioso.desenhar_com_aura(temp_surface, tempo_atual)

                # Restaurar posição
                self.misterioso.x = pos_x_original
                self.misterioso.y = pos_y_original
                self.misterioso.rect.x = self.misterioso.x
                self.misterioso.rect.y = self.misterioso.y

                # Aplicar alpha e desenhar na tela
                temp_surface.set_alpha(self.misterioso_alpha)
                tela.blit(temp_surface, (pos_x_original - self.misterioso.tamanho // 2,
                                        pos_y_original - self.misterioso.tamanho // 2))

        # Desenhar laser (se ativo)
        if self.laser_ativo:
            origem_x = self.misterioso.x + self.misterioso.tamanho // 2
            origem_y = self.misterioso.y + self.misterioso.tamanho // 2
            destino_x = self.elite.x + self.elite.tamanho // 2
            destino_y = self.elite.y + self.elite.tamanho // 2

            # Linha do laser
            pygame.draw.line(tela, (255, 0, 0), (int(origem_x), int(origem_y)),
                           (int(destino_x), int(destino_y)), 5)
            pygame.draw.line(tela, (255, 100, 100), (int(origem_x), int(origem_y)),
                           (int(destino_x), int(destino_y)), 2)

        # Desenhar partículas
        for particula in self.particulas:
            particula.desenhar(tela)

        for particula in self.particulas_transformacao:
            particula.desenhar(tela)

        for particula in self.laser_particulas:
            particula.desenhar(tela)

        # Desenhar diálogo do jogador
        if self.estado == "dialogo_jogador" and self.texto_visivel_jogador:
            # Fundo semi-transparente para o texto
            largura_caixa = 600
            altura_caixa = 80
            x_caixa = LARGURA // 2 - largura_caixa // 2
            y_caixa = ALTURA_JOGO - 120

            superficie_caixa = pygame.Surface((largura_caixa, altura_caixa), pygame.SRCALPHA)
            pygame.draw.rect(superficie_caixa, (0, 0, 100, 200), (0, 0, largura_caixa, altura_caixa))
            pygame.draw.rect(superficie_caixa, (0, 100, 255), (0, 0, largura_caixa, altura_caixa), 3)
            tela.blit(superficie_caixa, (x_caixa, y_caixa))

            # Nome do jogador
            desenhar_texto(tela, "Você", 22, (100, 200, 255), x_caixa + 40, y_caixa + 20)

            # Texto do diálogo
            desenhar_texto(tela, self.texto_visivel_jogador, 24, BRANCO,
                          LARGURA // 2, y_caixa + altura_caixa // 2 + 5)

        # Efeito de fade in (tela preta no início)
        if self.alpha_fade > 0:
            fade_surface = pygame.Surface((LARGURA, ALTURA))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.alpha_fade)
            tela.blit(fade_surface, (0, 0))


def executar_cutscene_velocitycyan(tela, relogio, gradiente_jogo, estrelas, jogador_pos, jogador=None, musica_path=None):
    """
    Executa a cutscene do VelocityCyan.

    Args:
        tela: Superfície de renderização
        relogio: Clock do pygame
        gradiente_jogo: Gradiente de fundo
        estrelas: Lista de estrelas de fundo
        jogador_pos: Posição (x, y) do jogador
        jogador: Objeto do jogador (opcional)
        musica_path: Caminho para a música de fundo (opcional)

    Returns:
        True quando a cutscene termina
    """
    cutscene = VelocityCyanCutscene(jogador_pos, jogador)
    cutscene.iniciar(pygame.time.get_ticks())

    # Tocar música de fundo se fornecida
    if musica_path:
        try:
            pygame.mixer.music.load(musica_path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)  # Loop infinito
            print(f"🎵 Música de fundo iniciada: {musica_path}")
        except Exception as e:
            print(f"⚠️ Erro ao carregar música: {e}")

    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()

        # Processar eventos (permitir pular com ESC ou ENTER)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    print("⏭️ Cutscene pulada pelo jogador")
                    return True

        # Atualizar cutscene
        if cutscene.atualizar(tempo_atual):
            rodando = False

        # Renderizar
        tela.fill((0, 0, 0))
        tela.blit(gradiente_jogo, (0, 0))
        desenhar_estrelas(tela, estrelas)

        # Desenhar cutscene
        cutscene.desenhar(tela, tempo_atual)

        # Texto de instrução (pode pular)
        desenhar_texto(tela, "Pressione ESPAÇO para pular", 18, (150, 150, 150),
                      LARGURA // 2, ALTURA_JOGO - 30)

        present_frame()
        relogio.tick(FPS)

    return True
