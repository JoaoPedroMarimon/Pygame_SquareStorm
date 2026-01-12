#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cutscene do Misterioso após vitória da fase 25.
Sequência cinemática onde o jogador enfrenta o Misterioso.
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


class MisteriosoFase25Cutscene:
    """
    Cutscene do Misterioso após vitória da fase 25.
    O jogador diz "finalmente, apenas eu e você", pega a Desert Eagle e atira 3 vezes.
    O Misterioso desvia se teleportando, depois usa poderes mentais para destruir a arma
    e cria um portal que faz o jogador cair no mar.
    """

    def __init__(self, jogador_pos, jogador=None):
        """
        Inicializa a cutscene.

        Args:
            jogador_pos: Posição (x, y) do jogador
            jogador: Objeto do jogador (opcional)
        """
        self.estado = "fade_in"
        self.tempo_inicio = 0
        self.jogador_x, self.jogador_y = jogador_pos
        self.jogador = jogador

        # Criar inimigo misterioso no centro da arena
        self.misterioso = InimigoMisterioso(LARGURA - 250, ALTURA_JOGO // 2)

        # Efeitos visuais
        self.particulas = []
        self.flashes = []
        self.alpha_fade = 255  # Fade in começa totalmente preto

        # Sistema de diálogo
        self.texto_dialogo_jogador = "Finalmente, apenas eu e você"
        self.texto_visivel = ""
        self.indice_texto = 0
        self.tempo_ultima_letra = 0
        self.velocidade_texto = 50  # ms por letra

        # Desert Eagle
        self.desert_eagle_pos = None
        self.desert_eagle_angulo = 0  # Ângulo de rotação da Desert Eagle
        self.desert_eagle_visivel = False
        self.tiros_disparados = 0
        self.tempo_ultimo_tiro = 0
        self.tiros_visiveis = []  # Lista de tiros ativos na tela

        # Poderes mentais
        self.desert_eagle_flutuando = False
        self.desert_eagle_explodida = False
        self.particulas_explosao = []

        # Portal
        self.portal_pos = None
        self.portal_raio = 0
        self.portal_ativo = False
        self.jogador_caindo = False
        self.jogador_vel_queda = 0
        self.jogador_no_portal = False
        self.jogador_sumindo = False
        self.alpha_jogador = 255
        self.jogador_angulo = 0  # Ângulo de rotação do jogador durante a queda

        # Ambiente novo (céu com sol e mar)
        self.ambiente_novo = False
        self.sol_pos = (LARGURA // 2, ALTURA_JOGO // 4)
        self.mar_y = ALTURA_JOGO * 0.5  # Mar mais alto para cobrir toda a parte de baixo
        self.portal_novo_raio = 0
        self.portal_novo_aberto = False
        self.splash_particulas = []
        self.splash_ativo = False

        # Configurações de timing
        self.duracao_fade_in = 1500
        self.duracao_total = 18000  # 18 segundos total
        self.tempo_chegada_jogador = 3500  # Aumentado de 2000 para 3500 (mais lento)
        self.tempo_dialogo_jogador = 3000
        self.tempo_pegar_arma = 1000
        self.tempo_entre_tiros = 800
        self.tempo_poderes = 2000
        self.tempo_explosao_arma = 1000
        self.tempo_criar_portal = 1500
        self.tempo_entrar_portal = 1000
        self.tempo_corte_ambiente = 1000
        self.tempo_pausa_ambiente = 2000  # 2 segundos mostrando o novo ambiente
        self.tempo_portal_abre = 1500
        self.tempo_queda = 2000
        self.tempo_splash_agua = 2000  # 2 segundos após splash

        # Posições fixas de teleporte do Misterioso (3 posições)
        self.posicoes_teleporte = [
            (LARGURA - 200, ALTURA_JOGO // 4),      # Superior direita
            (LARGURA - 150, ALTURA_JOGO // 2),      # Centro direita
            (LARGURA - 200, 3 * ALTURA_JOGO // 4),  # Inferior direita
        ]
        self.indice_teleporte = 0  # Índice da próxima posição de teleporte

        self.concluida = False

    def iniciar(self, tempo_atual):
        """Inicia a cutscene."""
        self.tempo_inicio = tempo_atual
        self.estado = "fade_in"
        print("🎬 Cutscene Misterioso Fase 25 iniciada!")

    def atualizar(self, tempo_atual):
        """
        Atualiza a cutscene.

        Returns:
            True se a cutscene terminou, False caso contrário
        """
        tempo_decorrido = tempo_atual - self.tempo_inicio

        # ESTADO: FADE IN
        if self.estado == "fade_in":
            if tempo_decorrido < self.duracao_fade_in:
                progresso = tempo_decorrido / self.duracao_fade_in
                self.alpha_fade = int(255 * (1 - progresso))
            else:
                self.alpha_fade = 0
                self.estado = "chegada_jogador"
                self.tempo_estado = tempo_atual
                print("👤 Fade in completo")

        # ESTADO: CHEGADA DO JOGADOR (movimento em direção ao Misterioso)
        elif self.estado == "chegada_jogador":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_chegada_jogador:
                # Mover jogador em direção ao misterioso
                progresso = tempo_estado_dec / self.tempo_chegada_jogador
                # Ease-in-out mais suave (cubic) para movimento mais lento e cinematográfico
                if progresso < 0.5:
                    progresso_suave = 4 * progresso ** 3  # Aceleração suave
                else:
                    progresso_suave = 1 - (-2 * progresso + 2) ** 3 / 2  # Desaceleração suave

                pos_inicial_x = self.jogador_x
                pos_final_x = LARGURA // 2 - 100  # Centro da arena (um pouco à esquerda)
                self.jogador_x = pos_inicial_x + (pos_final_x - pos_inicial_x) * progresso_suave

                # Mover jogador para o centro vertical da arena
                pos_inicial_y = self.jogador_y
                pos_final_y = ALTURA_JOGO // 2  # Centro vertical da arena
                self.jogador_y = pos_inicial_y + (pos_final_y - pos_inicial_y) * progresso_suave

                # Atualizar posição do jogador real se disponível
                if self.jogador:
                    self.jogador.x = self.jogador_x
                    self.jogador.y = self.jogador_y
                    self.jogador.rect.x = self.jogador_x
                    self.jogador.rect.y = self.jogador_y
            else:
                self.estado = "dialogo_jogador"
                self.tempo_estado = tempo_atual
                print("💬 Diálogo do jogador")

        # ESTADO: DIÁLOGO DO JOGADOR
        elif self.estado == "dialogo_jogador":
            tempo_estado_dec = tempo_atual - self.tempo_estado

            # Animação de texto letra por letra
            if tempo_atual - self.tempo_ultima_letra > self.velocidade_texto:
                if self.indice_texto < len(self.texto_dialogo_jogador):
                    self.texto_visivel += self.texto_dialogo_jogador[self.indice_texto]
                    self.indice_texto += 1
                    self.tempo_ultima_letra = tempo_atual

            if tempo_estado_dec >= self.tempo_dialogo_jogador:
                self.estado = "pegar_arma"
                self.tempo_estado = tempo_atual
                self.texto_visivel = ""
                print("🔫 Pegando Desert Eagle")

        # ESTADO: PEGAR DESERT EAGLE
        elif self.estado == "pegar_arma":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_pegar_arma:
                # Fazer Desert Eagle aparecer na mão do jogador
                progresso = tempo_estado_dec / self.tempo_pegar_arma
                self.desert_eagle_visivel = True
                self.desert_eagle_pos = (self.jogador_x + TAMANHO_QUADRADO, self.jogador_y + TAMANHO_QUADRADO // 2)

                # Calcular ângulo para apontar para o Misterioso
                centro_misterioso_x = self.misterioso.x + self.misterioso.tamanho // 2
                centro_misterioso_y = self.misterioso.y + self.misterioso.tamanho // 2
                dx = centro_misterioso_x - self.desert_eagle_pos[0]
                dy = centro_misterioso_y - self.desert_eagle_pos[1]
                self.desert_eagle_angulo = math.atan2(dy, dx)
            else:
                self.estado = "atirar"
                self.tempo_estado = tempo_atual
                print("💥 Atirando!")

        # ESTADO: ATIRAR 3 VEZES
        elif self.estado == "atirar":
            tempo_estado_dec = tempo_atual - self.tempo_estado

            # Atualizar posição e ângulo da Desert Eagle para seguir o Misterioso
            if self.desert_eagle_visivel and self.desert_eagle_pos:
                self.desert_eagle_pos = (self.jogador_x + TAMANHO_QUADRADO, self.jogador_y + TAMANHO_QUADRADO // 2)

                # Calcular ângulo para apontar para o Misterioso
                centro_misterioso_x = self.misterioso.x + self.misterioso.tamanho // 2
                centro_misterioso_y = self.misterioso.y + self.misterioso.tamanho // 2
                dx = centro_misterioso_x - self.desert_eagle_pos[0]
                dy = centro_misterioso_y - self.desert_eagle_pos[1]
                self.desert_eagle_angulo = math.atan2(dy, dx)

            # Atirar 3 vezes com intervalo
            if self.tiros_disparados < 3:
                if tempo_estado_dec >= self.tiros_disparados * self.tempo_entre_tiros:
                    self.disparar_tiro(tempo_atual)
                    self.tiros_disparados += 1
                    print(f"💥 Tiro {self.tiros_disparados}")

            # Atualizar tiros (movimento)
            for tiro in self.tiros_visiveis[:]:
                tiro['x'] += tiro['vel_x']
                tiro['y'] += tiro['vel_y']

                # Verificar se o tiro chegou perto do Misterioso (apenas para teleporte)
                dist_x = tiro['x'] - (self.misterioso.x + self.misterioso.tamanho // 2)
                dist_y = tiro['y'] - (self.misterioso.y + self.misterioso.tamanho // 2)
                distancia = math.sqrt(dist_x**2 + dist_y**2)

                if distancia < 50 and not tiro['desviado']:
                    # Misterioso se teletransporta para desviar
                    self.teletransportar_misterioso()
                    tiro['desviado'] = True
                    # Tiro continua seguindo em frente

                # Remover tiro se saiu da tela
                if tiro['x'] > LARGURA or tiro['x'] < 0 or tiro['y'] > ALTURA_JOGO or tiro['y'] < 0:
                    self.tiros_visiveis.remove(tiro)

            # Após 3 tiros, passar para poderes mentais
            if tempo_estado_dec >= 3 * self.tempo_entre_tiros + 500:
                self.estado = "poderes_mentais"
                self.tempo_estado = tempo_atual
                print("🧠 Poderes mentais!")

        # ESTADO: PODERES MENTAIS (fazer arma flutuar)
        elif self.estado == "poderes_mentais":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_poderes:
                self.desert_eagle_flutuando = True
                # Fazer arma flutuar e se mover em direção ao misterioso
                progresso = tempo_estado_dec / self.tempo_poderes
                if self.desert_eagle_pos:
                    # Interpolar posição da arma em direção ao misterioso
                    pos_final_x = self.misterioso.x - 30
                    pos_final_y = self.misterioso.y - 40
                    dx = (pos_final_x - self.desert_eagle_pos[0]) * 0.05
                    dy = (pos_final_y - self.desert_eagle_pos[1]) * 0.05
                    self.desert_eagle_pos = (self.desert_eagle_pos[0] + dx, self.desert_eagle_pos[1] + dy)

                    # Criar partículas de energia psíquica
                    if random.random() < 0.3:
                        self.criar_particulas_psiquicas()
            else:
                self.estado = "explosao_arma"
                self.tempo_estado = tempo_atual
                print("💥 Arma explode!")

        # ESTADO: EXPLOSÃO DA ARMA
        elif self.estado == "explosao_arma":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_explosao_arma:
                if not self.desert_eagle_explodida:
                    self.explodir_desert_eagle()
                    self.desert_eagle_explodida = True
            else:
                self.estado = "criar_portal"
                self.tempo_estado = tempo_atual
                print("🌀 Criando portal!")

        # ESTADO: CRIAR PORTAL (embaixo da arena)
        elif self.estado == "criar_portal":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_criar_portal:
                # Expandir portal embaixo na arena
                progresso = tempo_estado_dec / self.tempo_criar_portal
                self.portal_pos = (self.jogador_x + TAMANHO_QUADRADO // 2, ALTURA_JOGO - 80)
                self.portal_raio = int(80 * progresso)
                self.portal_ativo = True

                # Criar partículas do portal
                self.criar_particulas_portal()
            else:
                self.estado = "jogador_entrando_portal"
                self.tempo_estado = tempo_atual
                print("🚶 Jogador indo ao portal!")

        # ESTADO: JOGADOR INDO ATÉ O CENTRO DO PORTAL
        elif self.estado == "jogador_entrando_portal":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_entrar_portal:
                # Mover jogador em direção ao portal
                progresso = tempo_estado_dec / self.tempo_entrar_portal
                pos_final_x = self.portal_pos[0] - TAMANHO_QUADRADO // 2
                pos_final_y = self.portal_pos[1] - TAMANHO_QUADRADO // 2

                pos_inicial_x = self.jogador_x
                pos_inicial_y = self.jogador_y

                self.jogador_x = pos_inicial_x + (pos_final_x - pos_inicial_x) * progresso
                self.jogador_y = pos_inicial_y + (pos_final_y - pos_inicial_y) * progresso

                if self.jogador:
                    self.jogador.x = self.jogador_x
                    self.jogador.y = self.jogador_y
                    self.jogador.rect.x = self.jogador_x
                    self.jogador.rect.y = self.jogador_y

                # Criar partículas do portal
                self.criar_particulas_portal()

                # Fazer jogador sumir quando estiver no centro
                if progresso > 0.7:
                    self.jogador_sumindo = True
                    self.alpha_jogador = int(255 * (1 - (progresso - 0.7) / 0.3))
            else:
                self.estado = "corte_ambiente"
                self.tempo_estado = tempo_atual
                print("🌅 Cortando para novo ambiente!")

        # ESTADO: CORTE PARA NOVO AMBIENTE (céu com sol e mar)
        elif self.estado == "corte_ambiente":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_corte_ambiente:
                # Fade out
                progresso = tempo_estado_dec / self.tempo_corte_ambiente
                self.alpha_fade = int(255 * progresso)
            else:
                # Mudar para ambiente novo
                self.ambiente_novo = True
                self.portal_ativo = False
                self.jogador_sumindo = False
                self.alpha_jogador = 255
                self.estado = "pausa_ambiente"
                self.tempo_estado = tempo_atual
                print("🌅 Mostrando novo ambiente!")

        # ESTADO: PAUSA NO NOVO AMBIENTE (2 segundos)
        elif self.estado == "pausa_ambiente":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_pausa_ambiente:
                # Fade in do novo ambiente
                if tempo_estado_dec < self.tempo_corte_ambiente:
                    progresso_fade = tempo_estado_dec / self.tempo_corte_ambiente
                    self.alpha_fade = int(255 * (1 - progresso_fade))
                else:
                    self.alpha_fade = 0
            else:
                self.estado = "portal_abrindo"
                self.tempo_estado = tempo_atual
                print("🌀 Portal abrindo no céu!")

        # ESTADO: PORTAL ABRINDO NO NOVO AMBIENTE
        elif self.estado == "portal_abrindo":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_portal_abre:
                # Expandir portal no céu (mais alto)
                progresso = tempo_estado_dec / self.tempo_portal_abre
                self.portal_pos = (LARGURA // 2, ALTURA_JOGO // 4)  # Mais alto (era // 3)
                self.portal_novo_raio = int(80 * progresso)
                self.portal_novo_aberto = True

                # Criar partículas do portal
                if progresso > 0.5:
                    self.criar_particulas_portal_novo()
            else:
                self.estado = "jogador_caindo_portal"
                self.tempo_estado = tempo_atual
                # Posicionar jogador no portal (inicialmente invisível)
                self.portal_pos = (LARGURA // 2, ALTURA_JOGO // 4)  # Mais alto
                self.jogador_x = self.portal_pos[0] - TAMANHO_QUADRADO // 2
                self.jogador_y = self.portal_pos[1] - TAMANHO_QUADRADO // 2
                self.jogador_vel_queda = 0  # Resetar velocidade de queda
                self.jogador_angulo = 0  # Resetar ângulo de rotação
                if self.jogador:
                    self.jogador.x = self.jogador_x
                    self.jogador.y = self.jogador_y
                    self.jogador.rect.x = self.jogador_x
                    self.jogador.rect.y = self.jogador_y
                print("🌊 Jogador caindo do portal!")

        # ESTADO: JOGADOR CAINDO DO PORTAL NA ÁGUA
        elif self.estado == "jogador_caindo_portal":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if tempo_estado_dec < self.tempo_queda:
                self.jogador_caindo = True
                # Acelerar queda
                self.jogador_vel_queda += 0.5
                self.jogador_y += self.jogador_vel_queda

                # Girar o jogador enquanto cai
                self.jogador_angulo += 8  # Rotação de 8 graus por frame

                if self.jogador:
                    self.jogador.y = self.jogador_y
                    self.jogador.rect.y = self.jogador_y

                # Criar partículas do portal
                if self.jogador_y < self.portal_pos[1] + 100:
                    self.criar_particulas_portal_novo()

                # Verificar se chegou no mar
                if self.jogador_y >= self.mar_y:
                    self.estado = "splash"
                    self.tempo_estado = tempo_atual
                    print("💦 Splash na água!")
            else:
                # Caso não tenha atingido o mar ainda
                if not self.splash_ativo:
                    self.estado = "splash"
                    self.tempo_estado = tempo_atual
                    print("💦 Splash na água!")

        # ESTADO: SPLASH NA ÁGUA (2 segundos)
        elif self.estado == "splash":
            tempo_estado_dec = tempo_atual - self.tempo_estado
            if not self.splash_ativo:
                self.criar_splash()
                self.splash_ativo = True

            if tempo_estado_dec >= self.tempo_splash_agua:
                self.estado = "final"
                self.concluida = True
                print("🎬 Cutscene concluída!")
                return True

        # Atualizar partículas
        for particula in self.particulas[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas.remove(particula)

        for particula in self.particulas_explosao[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.particulas_explosao.remove(particula)

        for particula in self.splash_particulas[:]:
            particula.atualizar()
            if particula.vida <= 0:
                self.splash_particulas.remove(particula)

        return self.concluida

    def disparar_tiro(self, tempo_atual):
        """Cria efeito visual de tiro."""
        if self.desert_eagle_pos:
            # Calcular direção do tiro (do jogador para o Misterioso)
            centro_misterioso_x = self.misterioso.x + self.misterioso.tamanho // 2
            centro_misterioso_y = self.misterioso.y + self.misterioso.tamanho // 2

            dx = centro_misterioso_x - self.desert_eagle_pos[0]
            dy = centro_misterioso_y - self.desert_eagle_pos[1]
            distancia = math.sqrt(dx**2 + dy**2)

            if distancia > 0:
                dx /= distancia
                dy /= distancia

            # Criar tiro visível
            tiro = {
                'x': self.desert_eagle_pos[0] + 40,
                'y': self.desert_eagle_pos[1],
                'vel_x': dx * 15,  # Velocidade do tiro
                'vel_y': dy * 15,
                'raio': 4,
                'cor': (255, 200, 0),
                'desviado': False
            }
            self.tiros_visiveis.append(tiro)

            # Flash do tiro
            flash = {
                'x': self.desert_eagle_pos[0] + 40,
                'y': self.desert_eagle_pos[1],
                'raio': 15,
                'vida': 8,
                'cor': (255, 200, 0)
            }
            self.flashes.append(flash)

            # Partículas do tiro
            for _ in range(10):
                particula = Particula(
                    self.desert_eagle_pos[0] + 40,
                    self.desert_eagle_pos[1],
                    random.choice([(255, 220, 0), (255, 180, 0), (255, 100, 0)])
                )
                particula.velocidade_x = random.uniform(5, 10)
                particula.velocidade_y = random.uniform(-2, 2)
                particula.vida = random.randint(8, 15)
                particula.tamanho = random.uniform(2, 4)
                self.particulas.append(particula)

    def teletransportar_misterioso(self):
        """Teletransporta o Misterioso para uma posição fixa da sequência."""
        # Criar efeito de teleporte na posição antiga
        self.criar_efeito_teleporte_misterioso()

        # Escolher próxima posição da lista de posições fixas
        nova_x, nova_y = self.posicoes_teleporte[self.indice_teleporte]

        # Avançar para próxima posição (circular)
        self.indice_teleporte = (self.indice_teleporte + 1) % len(self.posicoes_teleporte)

        # Atualizar posição do Misterioso
        self.misterioso.x = nova_x
        self.misterioso.y = nova_y
        self.misterioso.rect.x = nova_x
        self.misterioso.rect.y = nova_y

        # Criar efeito de teleporte na posição nova
        self.criar_efeito_teleporte_misterioso()

    def criar_efeito_teleporte_misterioso(self):
        """Cria efeito visual de teleporte do Misterioso."""
        centro_x = self.misterioso.x + self.misterioso.tamanho // 2
        centro_y = self.misterioso.y + self.misterioso.tamanho // 2

        for _ in range(20):
            angulo = random.uniform(0, math.pi * 2)
            distancia = random.uniform(20, 60)
            x = centro_x + math.cos(angulo) * distancia
            y = centro_y + math.sin(angulo) * distancia

            particula = Particula(x, y, (200, 0, 100))
            particula.velocidade_x = -math.cos(angulo) * 3
            particula.velocidade_y = -math.sin(angulo) * 3
            particula.vida = random.randint(10, 20)
            particula.tamanho = random.uniform(3, 6)
            self.particulas.append(particula)

    def criar_particulas_psiquicas(self):
        """Cria partículas de energia psíquica ao redor da arma."""
        if self.desert_eagle_pos:
            for _ in range(3):
                angulo = random.uniform(0, math.pi * 2)
                raio = random.uniform(20, 40)
                x = self.desert_eagle_pos[0] + math.cos(angulo) * raio
                y = self.desert_eagle_pos[1] + math.sin(angulo) * raio

                particula = Particula(x, y, (150, 0, 200))
                particula.velocidade_x = math.cos(angulo) * 0.5
                particula.velocidade_y = math.sin(angulo) * 0.5
                particula.vida = random.randint(20, 30)
                particula.tamanho = random.uniform(3, 5)
                self.particulas.append(particula)

    def explodir_desert_eagle(self):
        """Cria explosão da Desert Eagle."""
        if self.desert_eagle_pos:
            # Explosão com muitas partículas
            for _ in range(50):
                angulo = random.uniform(0, math.pi * 2)
                velocidade = random.uniform(3, 10)

                particula = Particula(
                    self.desert_eagle_pos[0],
                    self.desert_eagle_pos[1],
                    random.choice([(255, 0, 0), (255, 100, 0), (200, 200, 200)])
                )
                particula.velocidade_x = math.cos(angulo) * velocidade
                particula.velocidade_y = math.sin(angulo) * velocidade
                particula.vida = random.randint(20, 40)
                particula.tamanho = random.uniform(2, 6)
                self.particulas_explosao.append(particula)

            # Remover desert eagle
            self.desert_eagle_visivel = False

    def criar_particulas_portal(self):
        """Cria partículas em espiral do portal."""
        if self.portal_pos:
            for i in range(5):
                angulo = (pygame.time.get_ticks() / 100 + i * math.pi / 2.5) % (math.pi * 2)
                raio = self.portal_raio * 0.8
                x = self.portal_pos[0] + math.cos(angulo) * raio
                y = self.portal_pos[1] + math.sin(angulo) * raio

                particula = Particula(x, y, (100, 0, 200))
                particula.velocidade_x = -math.cos(angulo) * 2
                particula.velocidade_y = -math.sin(angulo) * 2
                particula.vida = random.randint(10, 20)
                particula.tamanho = random.uniform(3, 6)
                self.particulas.append(particula)

    def criar_particulas_portal_novo(self):
        """Cria partículas em espiral do portal no novo ambiente."""
        if self.portal_pos:
            for i in range(5):
                angulo = (pygame.time.get_ticks() / 100 + i * math.pi / 2.5) % (math.pi * 2)
                raio = self.portal_novo_raio * 0.8
                x = self.portal_pos[0] + math.cos(angulo) * raio
                y = self.portal_pos[1] + math.sin(angulo) * raio

                particula = Particula(x, y, (100, 0, 200))
                particula.velocidade_x = -math.cos(angulo) * 2
                particula.velocidade_y = -math.sin(angulo) * 2
                particula.vida = random.randint(10, 20)
                particula.tamanho = random.uniform(3, 6)
                self.particulas.append(particula)

    def criar_splash(self):
        """Cria efeito de splash na água quando o jogador cai."""
        splash_x = self.jogador_x + TAMANHO_QUADRADO // 2
        splash_y = self.mar_y

        # Muitas partículas de água
        for _ in range(100):
            angulo = random.uniform(-math.pi / 2, -math.pi / 6)
            velocidade = random.uniform(5, 15)

            particula = Particula(
                splash_x,
                splash_y,
                random.choice([(100, 150, 255), (120, 180, 255), (80, 120, 200)])
            )
            particula.velocidade_x = math.cos(angulo) * velocidade * random.choice([-1, 1])
            particula.velocidade_y = math.sin(angulo) * velocidade
            particula.vida = random.randint(30, 60)
            particula.tamanho = random.uniform(2, 5)
            self.splash_particulas.append(particula)

    def desenhar(self, tela, tempo_atual):
        """Desenha a cutscene."""
        # Se estiver no ambiente novo, desenhar céu com sol e mar
        if self.ambiente_novo:
            # Céu azul claro
            tela.fill((135, 206, 250))

            # Sol
            pygame.draw.circle(tela, (255, 255, 100), self.sol_pos, 60)
            # Brilho do sol
            for i in range(3):
                superficie_brilho = pygame.Surface((150 + i * 40, 150 + i * 40), pygame.SRCALPHA)
                alpha = int(30 - i * 8)
                pygame.draw.circle(superficie_brilho, (255, 255, 150, alpha),
                                 (75 + i * 20, 75 + i * 20), 75 + i * 20)
                tela.blit(superficie_brilho,
                         (self.sol_pos[0] - (75 + i * 20), self.sol_pos[1] - (75 + i * 20)))

            # Mar azul escuro (cobrir toda a parte de baixo)
            altura_mar = ALTURA_JOGO - int(self.mar_y) + 100  # +100 para garantir que cubra tudo
            pygame.draw.rect(tela, (20, 50, 120), (0, int(self.mar_y), LARGURA, altura_mar))
            # Ondas
            for i in range(0, LARGURA, 50):
                onda_y = self.mar_y + math.sin((tempo_atual + i * 10) / 200) * 8
                pygame.draw.line(tela, (40, 100, 180), (i, int(onda_y)), (i + 50, int(onda_y)), 4)

            # Portal no novo ambiente
            if self.portal_novo_aberto and self.portal_pos:
                pulso = math.sin(tempo_atual / 100) * 0.3 + 0.7
                # Círculo externo
                pygame.draw.circle(tela, (100, 0, 200), (int(self.portal_pos[0]), int(self.portal_pos[1])), self.portal_novo_raio, 3)
                # Círculo médio
                pygame.draw.circle(tela, (150, 50, 200), (int(self.portal_pos[0]), int(self.portal_pos[1])), int(self.portal_novo_raio * 0.7), 2)
                # Centro brilhante
                superficie_brilho = pygame.Surface((self.portal_novo_raio * 2, self.portal_novo_raio * 2), pygame.SRCALPHA)
                alpha_brilho = int(100 * pulso)
                pygame.draw.circle(superficie_brilho, (200, 100, 255, alpha_brilho),
                                 (self.portal_novo_raio, self.portal_novo_raio), int(self.portal_novo_raio * 0.5))
                tela.blit(superficie_brilho,
                         (int(self.portal_pos[0]) - self.portal_novo_raio, int(self.portal_pos[1]) - self.portal_novo_raio))

        # Desenhar o Misterioso (apenas no ambiente antigo)
        if not self.ambiente_novo and self.estado not in ("final",):
            self.misterioso.desenhar_com_aura(tela, tempo_atual)

        # Desenhar o jogador (ocultar durante corte, pausa, splash e final)
        if self.jogador and self.estado not in ("corte_ambiente", "pausa_ambiente", "portal_abrindo", "splash", "final"):
            # Salvar estados temporariamente
            invulneravel_original = self.jogador.invulneravel
            espingarda_ativa_original = getattr(self.jogador, 'espingarda_ativa', False)
            metralhadora_ativa_original = getattr(self.jogador, 'metralhadora_ativa', False)
            desert_eagle_ativa_original = getattr(self.jogador, 'desert_eagle_ativa', False)

            # Desativar armas temporariamente
            self.jogador.invulneravel = False
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = False
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = False
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = False

            # Desenhar o jogador com rotação se estiver caindo, ou com alpha se estiver sumindo
            if self.estado == "jogador_caindo_portal":
                # Criar superfície temporária para rotação (maior para evitar cortes)
                tamanho_surf = int(TAMANHO_QUADRADO * 2)
                temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)

                # Desenhar jogador completo no centro da superfície (com bordas e tudo)
                offset_x = tamanho_surf // 2 - TAMANHO_QUADRADO // 2
                offset_y = tamanho_surf // 2 - TAMANHO_QUADRADO // 2

                # Desenhar quadrado principal
                jogador_rect = pygame.Rect(offset_x, offset_y, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
                pygame.draw.rect(temp_surface, self.jogador.cor, jogador_rect)

                # Desenhar borda do jogador
                pygame.draw.rect(temp_surface, (255, 255, 255), jogador_rect, 2)

                # Se o jogador tiver efeitos especiais, desenhar também
                if hasattr(self.jogador, 'invulneravel') and self.jogador.invulneravel:
                    # Aura de invulnerabilidade
                    pygame.draw.rect(temp_surface, (255, 255, 0),
                                   (offset_x - 2, offset_y - 2,
                                    TAMANHO_QUADRADO + 4, TAMANHO_QUADRADO + 4), 2)

                # Rotacionar a superfície
                temp_surface_rotated = pygame.transform.rotate(temp_surface, -self.jogador_angulo)
                # Obter o retângulo centralizado
                rect_rotated = temp_surface_rotated.get_rect(center=(self.jogador_x + TAMANHO_QUADRADO // 2,
                                                                      self.jogador_y + TAMANHO_QUADRADO // 2))
                # Blit na tela
                tela.blit(temp_surface_rotated, rect_rotated)
            elif self.jogador_sumindo:
                # Criar superfície temporária para aplicar alpha
                temp_surface = pygame.Surface((TAMANHO_QUADRADO, TAMANHO_QUADRADO), pygame.SRCALPHA)
                # Desenhar jogador na superfície temporária
                jogador_rect = pygame.Rect(0, 0, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
                cor_com_alpha = (*self.jogador.cor[:3], self.alpha_jogador)
                pygame.draw.rect(temp_surface, cor_com_alpha, jogador_rect)
                # Blit na tela
                tela.blit(temp_surface, (self.jogador_x, self.jogador_y))
            else:
                # Desenhar normalmente
                self.jogador.desenhar(tela, tempo_atual)

            # Restaurar estados
            self.jogador.invulneravel = invulneravel_original
            if hasattr(self.jogador, 'espingarda_ativa'):
                self.jogador.espingarda_ativa = espingarda_ativa_original
            if hasattr(self.jogador, 'metralhadora_ativa'):
                self.jogador.metralhadora_ativa = metralhadora_ativa_original
            if hasattr(self.jogador, 'desert_eagle_ativa'):
                self.jogador.desert_eagle_ativa = desert_eagle_ativa_original
        elif not self.jogador and self.estado not in ("corte_ambiente", "pausa_ambiente", "portal_abrindo", "splash", "final"):
            # Fallback: desenhar quadrado simples
            if self.estado == "jogador_caindo_portal":
                # Criar superfície temporária para rotação
                tamanho_surf = int(TAMANHO_QUADRADO * 2)
                temp_surface = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)
                offset_x = tamanho_surf // 2 - TAMANHO_QUADRADO // 2
                offset_y = tamanho_surf // 2 - TAMANHO_QUADRADO // 2

                jogador_rect = pygame.Rect(offset_x, offset_y, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
                pygame.draw.rect(temp_surface, AZUL, jogador_rect)
                # Desenhar borda
                pygame.draw.rect(temp_surface, (255, 255, 255), jogador_rect, 2)

                # Rotacionar
                temp_surface_rotated = pygame.transform.rotate(temp_surface, -self.jogador_angulo)
                rect_rotated = temp_surface_rotated.get_rect(center=(self.jogador_x + TAMANHO_QUADRADO // 2,
                                                                      self.jogador_y + TAMANHO_QUADRADO // 2))
                tela.blit(temp_surface_rotated, rect_rotated)
            elif self.jogador_sumindo:
                temp_surface = pygame.Surface((TAMANHO_QUADRADO, TAMANHO_QUADRADO), pygame.SRCALPHA)
                jogador_rect = pygame.Rect(0, 0, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
                cor_com_alpha = (*AZUL[:3], self.alpha_jogador)
                pygame.draw.rect(temp_surface, cor_com_alpha, jogador_rect)
                tela.blit(temp_surface, (self.jogador_x, self.jogador_y))
            else:
                jogador_rect = pygame.Rect(self.jogador_x, self.jogador_y, TAMANHO_QUADRADO, TAMANHO_QUADRADO)
                pygame.draw.rect(tela, AZUL, jogador_rect)

        # Desenhar Desert Eagle
        if self.desert_eagle_visivel and self.desert_eagle_pos:
            self.desenhar_desert_eagle_simples(tela, self.desert_eagle_pos[0], self.desert_eagle_pos[1])

        # Desenhar flashes
        for flash in self.flashes[:]:
            flash['vida'] -= 1
            if flash['vida'] <= 0:
                self.flashes.remove(flash)
            else:
                alpha = int(255 * flash['vida'] / 8)
                superficie_flash = pygame.Surface((flash['raio'] * 2, flash['raio'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(superficie_flash, (*flash['cor'], alpha), (flash['raio'], flash['raio']), flash['raio'])
                tela.blit(superficie_flash, (flash['x'] - flash['raio'], flash['y'] - flash['raio']))

        # Desenhar tiros
        for tiro in self.tiros_visiveis:
            # Desenhar tiro como círculo brilhante
            pygame.draw.circle(tela, tiro['cor'], (int(tiro['x']), int(tiro['y'])), tiro['raio'])
            # Borda mais escura
            pygame.draw.circle(tela, (200, 150, 0), (int(tiro['x']), int(tiro['y'])), tiro['raio'], 1)
            # Rastro do tiro
            for i in range(3):
                rastro_x = tiro['x'] - tiro['vel_x'] * (i + 1) * 0.3
                rastro_y = tiro['y'] - tiro['vel_y'] * (i + 1) * 0.3
                alpha = int(150 - i * 50)
                superficie_rastro = pygame.Surface((tiro['raio'] * 2, tiro['raio'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(superficie_rastro, (*tiro['cor'], alpha), (tiro['raio'], tiro['raio']), tiro['raio'] - i)
                tela.blit(superficie_rastro, (int(rastro_x) - tiro['raio'], int(rastro_y) - tiro['raio']))

        # Desenhar partículas
        for particula in self.particulas:
            particula.desenhar(tela)

        for particula in self.particulas_explosao:
            particula.desenhar(tela)

        # Desenhar partículas de splash
        for particula in self.splash_particulas:
            particula.desenhar(tela)

        # Desenhar portal (ambiente antigo)
        if self.portal_ativo and self.portal_pos and not self.ambiente_novo:
            pulso = math.sin(tempo_atual / 100) * 0.3 + 0.7
            # Círculo externo
            pygame.draw.circle(tela, (100, 0, 200), (int(self.portal_pos[0]), int(self.portal_pos[1])), self.portal_raio, 3)
            # Círculo médio
            pygame.draw.circle(tela, (150, 50, 200), (int(self.portal_pos[0]), int(self.portal_pos[1])), int(self.portal_raio * 0.7), 2)
            # Centro brilhante
            superficie_brilho = pygame.Surface((self.portal_raio * 2, self.portal_raio * 2), pygame.SRCALPHA)
            alpha_brilho = int(100 * pulso)
            pygame.draw.circle(superficie_brilho, (200, 100, 255, alpha_brilho),
                             (self.portal_raio, self.portal_raio), int(self.portal_raio * 0.5))
            tela.blit(superficie_brilho,
                     (int(self.portal_pos[0]) - self.portal_raio, int(self.portal_pos[1]) - self.portal_raio))

        # Desenhar diálogo
        if self.estado == "dialogo_jogador" and self.texto_visivel:
            # Fundo semi-transparente para o texto
            largura_caixa = 800
            altura_caixa = 100
            x_caixa = LARGURA // 2 - largura_caixa // 2
            y_caixa = ALTURA_JOGO - 150

            superficie_caixa = pygame.Surface((largura_caixa, altura_caixa), pygame.SRCALPHA)
            pygame.draw.rect(superficie_caixa, (0, 0, 50, 200), (0, 0, largura_caixa, altura_caixa))
            pygame.draw.rect(superficie_caixa, AZUL, (0, 0, largura_caixa, altura_caixa), 3)
            tela.blit(superficie_caixa, (x_caixa, y_caixa))

            # Nome do jogador
            desenhar_texto(tela, "Você", 24, AZUL, x_caixa + 50, y_caixa + 25)

            # Texto do diálogo
            desenhar_texto(tela, self.texto_visivel, 28, BRANCO,
                          LARGURA // 2, y_caixa + altura_caixa // 2 + 10)

        # Efeito de fade in
        if self.alpha_fade > 0:
            fade_surface = pygame.Surface((LARGURA, ALTURA))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self.alpha_fade)
            tela.blit(fade_surface, (0, 0))

    def desenhar_desert_eagle_simples(self, tela, x, y):
        """Desenha a Desert Eagle com rotação (idêntica ao desert_eagle.py)."""
        # Cores realistas da Desert Eagle (aço inoxidável/cromado)
        cor_metal_claro = (180, 180, 190)
        cor_metal_medio = (120, 120, 130)
        cor_metal_escuro = (60, 60, 70)
        cor_punho_preto = (30, 30, 35)
        cor_detalhes_punho = (50, 50, 55)
        cor_cano_interno = (20, 20, 25)

        # Criar superfície temporária para desenhar a arma
        tamanho_surf = 100
        surf = pygame.Surface((tamanho_surf, tamanho_surf), pygame.SRCALPHA)

        # Offset para centralizar na superfície
        offset_x = 50
        offset_y = 50

        # === SLIDE (parte superior massiva da Desert Eagle) ===
        slide_x = offset_x - 18
        slide_y = offset_y - 5
        slide_largura = 38
        slide_altura = 8

        # Slide principal
        slide_rect = pygame.Rect(slide_x, slide_y, slide_largura, slide_altura)
        pygame.draw.rect(surf, cor_metal_medio, slide_rect, 0, 2)

        # Brilho superior do slide
        pygame.draw.line(surf, cor_metal_claro,
                        (slide_x + 2, slide_y + 1),
                        (slide_x + slide_largura - 4, slide_y + 1), 2)

        # Sombra inferior do slide
        pygame.draw.line(surf, cor_metal_escuro,
                        (slide_x + 2, slide_y + slide_altura - 2),
                        (slide_x + slide_largura - 4, slide_y + slide_altura - 2), 1)

        # Ranhuras de ventilação
        for i in range(5):
            ranhura_x = slide_x + 20 + i * 3
            pygame.draw.line(surf, cor_metal_escuro,
                            (ranhura_x, slide_y + 2),
                            (ranhura_x, slide_y + slide_altura - 2), 2)
            pygame.draw.line(surf, cor_metal_claro,
                            (ranhura_x + 1, slide_y + 2),
                            (ranhura_x + 1, slide_y + slide_altura - 2), 1)

        # === CANO MASSIVO ===
        cano_x = slide_x + slide_largura
        cano_y = offset_y
        cano_raio = 4

        pygame.draw.circle(surf, cor_metal_medio, (cano_x, cano_y), cano_raio)
        pygame.draw.circle(surf, cor_metal_claro, (cano_x, cano_y - 1), cano_raio - 1)
        pygame.draw.circle(surf, cor_cano_interno, (cano_x, cano_y), cano_raio - 2)
        pygame.draw.circle(surf, (10, 10, 15), (cano_x, cano_y), cano_raio - 3)
        pygame.draw.circle(surf, cor_metal_escuro, (cano_x, cano_y), cano_raio, 1)

        # === FRAME ===
        frame_x = slide_x + 3
        frame_y = offset_y
        frame_largura = 26
        frame_altura = 12

        frame_rect = pygame.Rect(frame_x, frame_y - frame_altura//2, frame_largura, frame_altura)
        pygame.draw.rect(surf, cor_metal_escuro, frame_rect, 0, 2)
        pygame.draw.rect(surf, cor_metal_medio,
                        (frame_x + 1, frame_y - frame_altura//2 + 1, frame_largura - 2, 2), 0, 1)

        # === TRILHO PICATINNY ===
        trilho_y = slide_y - 2
        for i in range(3):
            trilho_x = slide_x + 15 + i * 4
            pygame.draw.rect(surf, cor_metal_escuro, (trilho_x, trilho_y, 2, 2))

        # === GUARDA-MATO ===
        guarda_centro_x = frame_x + 10
        guarda_centro_y = offset_y + 6

        pygame.draw.ellipse(surf, cor_metal_medio,
                           (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 2)
        pygame.draw.ellipse(surf, cor_metal_claro,
                           (guarda_centro_x - 5, guarda_centro_y - 4, 10, 8), 1)

        # === GATILHO ===
        gatilho_x = guarda_centro_x
        gatilho_y = guarda_centro_y
        pygame.draw.rect(surf, cor_metal_claro, (gatilho_x - 2, gatilho_y - 1, 4, 3), 0, 1)
        pygame.draw.line(surf, cor_metal_escuro, (gatilho_x - 1, gatilho_y + 1), (gatilho_x + 1, gatilho_y + 1), 1)

        # === PUNHO ERGONÔMICO ===
        punho_x = frame_x - 1
        punho_y = offset_y + 3

        punho_pontos = [
            (punho_x, punho_y - 4),
            (punho_x + 12, punho_y - 3),
            (punho_x + 10, punho_y + 12),
            (punho_x - 4, punho_y + 10)
        ]

        pygame.draw.polygon(surf, cor_punho_preto, punho_pontos)
        pygame.draw.polygon(surf, cor_metal_escuro, punho_pontos, 1)

        # Textura do punho
        for i in range(6):
            textura_y = punho_y + i * 2
            pygame.draw.line(surf, cor_detalhes_punho,
                            (punho_x + 2, textura_y),
                            (punho_x + 8, textura_y), 1)

        # === MARTELO ===
        martelo_x = frame_x + 5
        martelo_y = offset_y - 8
        pygame.draw.circle(surf, cor_metal_medio, (martelo_x, martelo_y), 3)
        pygame.draw.rect(surf, cor_metal_escuro, (martelo_x - 1, martelo_y - 5, 2, 5))

        # === MIRA FRONTAL ===
        mira_x = cano_x - 5
        mira_y = offset_y - 6
        pygame.draw.rect(surf, (255, 215, 0), (mira_x - 1, mira_y, 2, 4))

        # === MIRA TRASEIRA ===
        mira_tras_x = frame_x + 20
        mira_tras_y = offset_y - 7
        pygame.draw.rect(surf, cor_metal_escuro, (mira_tras_x - 3, mira_tras_y, 6, 4))
        pygame.draw.rect(surf, (100, 255, 100), (mira_tras_x - 1, mira_tras_y + 1, 2, 2))

        # Rotacionar a superfície usando o ângulo calculado
        angulo_graus = math.degrees(self.desert_eagle_angulo)
        surf_rotacionada = pygame.transform.rotate(surf, -angulo_graus)

        # Obter o retângulo e posicionar na posição da arma
        rect = surf_rotacionada.get_rect()
        rect.center = (x, y)

        # Desenhar na tela
        tela.blit(surf_rotacionada, rect)


def executar_cutscene_misterioso_fase25(tela, relogio, gradiente_jogo, estrelas, jogador_pos, jogador=None):
    """
    Executa a cutscene do Misterioso após a fase 25.

    Args:
        tela: Superfície de renderização
        relogio: Clock do pygame
        gradiente_jogo: Gradiente de fundo
        estrelas: Lista de estrelas de fundo
        jogador_pos: Posição (x, y) do jogador
        jogador: Objeto do jogador (opcional)

    Returns:
        True quando a cutscene termina
    """
    cutscene = MisteriosoFase25Cutscene(jogador_pos, jogador)
    cutscene.iniciar(pygame.time.get_ticks())

    rodando = True
    while rodando:
        tempo_atual = pygame.time.get_ticks()

        # Processar eventos (permitir pular)
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

        # Texto de instrução
        desenhar_texto(tela, "Pressione ESPAÇO para pular", 18, (150, 150, 150),
                      LARGURA // 2, ALTURA_JOGO - 30)

        present_frame()
        relogio.tick(FPS)

    return True
