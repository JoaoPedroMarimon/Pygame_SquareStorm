#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para inimigo mago.
O mago usa um chapéu de mago, segura um cajado que aponta para o jogador,
possui um escudo protetor que cicla a cada 4 segundos,
atira bolas de fogo e invoca inimigos básicos.
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.entities.particula import Particula
from src.utils.sound import gerar_som_tiro


class InimigoMago(Quadrado):
    """
    Inimigo mago com escudo protetor cíclico, ataque de bolas de fogo e invocação de inimigos.
    """

    def __init__(self, x, y):
        """Inicializa o inimigo mago."""
        # Cor branca para o mago
        cor_mago = (255, 255, 255)
        velocidade = VELOCIDADE_INIMIGO_BASE * 0.9  # Mais ágil

        super().__init__(x, y, TAMANHO_QUADRADO, cor_mago, velocidade)

        # Atributos básicos
        self.vidas = 5
        self.vidas_max = 5

        # Sistema de escudo protetor (cicla 4s ativo, 4s inativo)
        self.duracao_escudo_ativo = 4000  # 4 segundos
        self.duracao_escudo_inativo = 6000  # 4 segundos
        self.escudo_ativo = False  # Começa com escudo
        self.tempo_inicio_ciclo_escudo = pygame.time.get_ticks()

        # Propriedades do escudo
        self.raio_escudo = TAMANHO_QUADRADO + 15
        self.cor_escudo = (100, 200, 255)  # Azul ciano

        # Sistema de ataque com bolas de fogo
        self.cooldown_bola_fogo = 800  # 0.8 segundos entre tiros
        self.tempo_ultimo_tiro = 0
        self.cor_bola_fogo = (255, 100, 0)  # Laranja fogo

        # Sistema de invocação
        self.tiros_desde_invocacao = 0
        self.tiros_para_invocar = random.randint(8, 30)  # Quantidade aleatória entre 4-15
        self.esta_invocando = False
        self.tempo_inicio_invocacao = 0
        self.duracao_invocacao = 3000  # 2 segundos invocando
        self.invocacao_completa = False

        # Cajado (reto, segue o jogador como sabre de luz)
        self.comprimento_cajado = 60  # Aumentado de 40 para 60
        self.largura_cajado = 4
        self.cor_cajado = (101, 67, 33)  # Marrom madeira escuro
        self.cor_cajado_claro = (139, 90, 43)  # Marrom mais claro para detalhes
        self.angulo_cajado = 0  # Ângulo atual do cajado

        # Animação de aparecimento do cajado (como sabre de luz)
        self.cajado_visivel = True  # Visível desde o início (contagem regressiva)
        self.animacao_cajado = 0  # 0 a 100 (progresso da animação)
        self.tempo_criacao = pygame.time.get_ticks()  # Começa a aparecer imediatamente

        # Flag para identificar tipo
        self.tipo_mago = True

        # Cooldown de movimento (movimento normal)
        self.tempo_cooldown = 999999  # Não usa tiro normal

    def atualizar_escudo(self):
        """Atualiza o estado do escudo (ciclo de 4s ativo, 4s inativo)."""
        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_inicio_ciclo_escudo

        if self.escudo_ativo:
            # Escudo está ativo
            if tempo_decorrido >= self.duracao_escudo_ativo:
                # Tempo de desativar
                self.escudo_ativo = False
                self.tempo_inicio_ciclo_escudo = tempo_atual
        else:
            # Escudo está inativo
            if tempo_decorrido >= self.duracao_escudo_inativo:
                # Tempo de reativar
                self.escudo_ativo = True
                self.tempo_inicio_ciclo_escudo = tempo_atual

    def tomar_dano(self, dano=1):
        """
        Sobrescreve o método de tomar dano para considerar o escudo.
        Se o escudo está ativo, não toma dano.
        """
        if self.escudo_ativo:
            # Escudo bloqueia o dano
            return False
        else:
            # Sem escudo, toma dano normalmente
            return super().tomar_dano(dano)

    def pode_atirar(self):
        """Verifica se o mago pode atirar (não está invocando)."""
        return not self.esta_invocando

    def atirar_bola_fogo(self, jogador, tiros_inimigo, particulas=None, flashes=None):
        """
        Atira uma bola de fogo na direção do jogador.

        Args:
            jogador: Objeto do jogador (alvo)
            tiros_inimigo: Lista de tiros inimigos
            particulas: Lista de partículas (opcional)
            flashes: Lista de flashes (opcional)
        """
        # Verificar se pode atirar
        if not self.pode_atirar():
            return

        # Verificar cooldown entre tiros
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_tiro < self.cooldown_bola_fogo:
            return

        self.tempo_ultimo_tiro = tempo_atual

        # Incrementar contador de tiros
        self.tiros_desde_invocacao += 1

        # Verificar se deve invocar
        if self.tiros_desde_invocacao >= self.tiros_para_invocar:
            self.iniciar_invocacao()
            return

        # Posição central do mago (com offset vertical para baixo - mesmo do cajado)
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2 + 8  # 8 pixels mais abaixo

        # Calcular direção para o jogador (para atirar)
        jogador_centro_x = jogador.x + jogador.tamanho // 2
        jogador_centro_y = jogador.y + jogador.tamanho // 2

        dx = jogador_centro_x - centro_x
        dy = jogador_centro_y - centro_y

        # Normalizar
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Som de tiro
        try:
            som_fogo = pygame.mixer.Sound(gerar_som_tiro())
            som_fogo.set_volume(0.15)
            pygame.mixer.Channel(5).play(som_fogo)
        except:
            pass

        # Atualizar ângulo do cajado
        self.atualizar_angulo_cajado(jogador)

        # MODO DEFESA: Calcular base do cajado (à frente do mago)
        distancia_base_cajado = 15  # Mais próximo (era 35)
        base_x = centro_x + math.cos(self.angulo_cajado) * distancia_base_cajado
        base_y = centro_y + math.sin(self.angulo_cajado) * distancia_base_cajado

        # Calcular posição da ponta do cajado (modo defesa - perpendicular)
        angulo_defesa = self.angulo_cajado + math.pi / 2  # SOMA para inverter
        cajado_dx = math.cos(angulo_defesa)
        cajado_dy = math.sin(angulo_defesa)

        # Comprimento atual do cajado (considerar animação)
        comprimento_atual = self.comprimento_cajado * (self.animacao_cajado / 100) if hasattr(self, 'animacao_cajado') else self.comprimento_cajado

        ponta_cajado_x = base_x + cajado_dx * comprimento_atual
        ponta_cajado_y = base_y + cajado_dy * comprimento_atual

        # Criar efeito de partículas de fogo
        if particulas is not None:
            for _ in range(8):
                vari_x = random.uniform(-3, 3)
                vari_y = random.uniform(-3, 3)
                pos_x = ponta_cajado_x + vari_x
                pos_y = ponta_cajado_y + vari_y

                particula = Particula(pos_x, pos_y, self.cor_bola_fogo)
                particula.velocidade_x = dx * random.uniform(1, 3) + random.uniform(-0.5, 0.5)
                particula.velocidade_y = dy * random.uniform(1, 3) + random.uniform(-0.5, 0.5)
                particula.vida = random.randint(5, 10)
                particula.tamanho = random.uniform(2, 4)
                particula.gravidade = -0.01  # Partículas sobem um pouco (fogo)

                particulas.append(particula)

        # Flash de tiro
        if flashes is not None:
            flash = {
                'x': ponta_cajado_x,
                'y': ponta_cajado_y,
                'raio': 10,
                'vida': 3,
                'cor': (255, 150, 0)
            }
            flashes.append(flash)

        # Criar bola de fogo (tiro maior que normal)
        bola_fogo = Tiro(ponta_cajado_x, ponta_cajado_y, dx, dy, self.cor_bola_fogo, 6)
        bola_fogo.raio = 10  # Bola de fogo maior
        bola_fogo.rect = pygame.Rect(ponta_cajado_x - 10, ponta_cajado_y - 10, 20, 20)
        # Marcar como bola de fogo para desenho especial
        bola_fogo.tipo_bola_fogo = True
        tiros_inimigo.append(bola_fogo)

    def iniciar_invocacao(self):
        """Inicia o processo de invocação de inimigos."""
        self.esta_invocando = True
        self.tempo_inicio_invocacao = pygame.time.get_ticks()
        self.invocacao_completa = False
        print(f"🧙 Mago iniciando invocação!")

    def atualizar_invocacao(self, inimigos):
        """
        Atualiza o processo de invocação.

        Args:
            inimigos: Lista de inimigos (para adicionar os invocados)

        Returns:
            True se a invocação terminou, False caso contrário
        """
        if not self.esta_invocando:
            return False

        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_inicio_invocacao

        # Verificar se completou a invocação (criar inimigos uma vez)
        if tempo_decorrido >= self.duracao_invocacao / 2 and not self.invocacao_completa:
            self.invocar_inimigos(inimigos)
            self.invocacao_completa = True

        # Verificar se terminou a invocação completa
        if tempo_decorrido >= self.duracao_invocacao:
            self.esta_invocando = False
            self.tiros_desde_invocacao = 0
            self.tiros_para_invocar = random.randint(8, 30)  # Novo alvo aleatório
            print(f"🧙 Mago terminou invocação! Próxima em {self.tiros_para_invocar} tiros")
            return True

        return False

    def invocar_inimigos(self, inimigos):
        """
        Invoca 2 perseguidores e 1 inimigo básico em volta do mago.

        Args:
            inimigos: Lista de inimigos para adicionar os invocados
        """
        from src.entities.inimigo_factory import InimigoFactory

        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # Distância dos inimigos invocados
        raio_invocacao = 80

        # Criar 3 inimigos em círculo ao redor do mago
        # 2 perseguidores e 1 básico
        for i in range(3):
            angulo = (2 * math.pi * i) / 3  # Dividir círculo em 3 partes

            pos_x = centro_x + math.cos(angulo) * raio_invocacao
            pos_y = centro_y + math.sin(angulo) * raio_invocacao

            # Garantir que estão dentro da tela
            pos_x = max(TAMANHO_QUADRADO, min(pos_x, LARGURA - TAMANHO_QUADRADO))
            pos_y = max(TAMANHO_QUADRADO, min(pos_y, ALTURA_JOGO - TAMANHO_QUADRADO))

            # Criar perseguidor para i=0 e i=1, básico para i=2
            if i < 2:
                inimigo = InimigoFactory.criar_inimigo_perseguidor(pos_x, pos_y)
            else:
                inimigo = InimigoFactory.criar_inimigo_basico(pos_x, pos_y)

            inimigo.invocado_por_mago = True
            inimigos.append(inimigo)

        print(f"🧙 Mago invocou 2 perseguidores e 1 inimigo básico!")

    def atualizar_angulo_cajado(self, jogador):
        """
        Atualiza o ângulo do cajado para seguir o jogador.

        Args:
            jogador: Objeto do jogador (alvo)
        """
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        jogador_centro_x = jogador.x + jogador.tamanho // 2
        jogador_centro_y = jogador.y + jogador.tamanho // 2

        dx = jogador_centro_x - centro_x
        dy = jogador_centro_y - centro_y

        # Calcular ângulo
        self.angulo_cajado = math.atan2(dy, dx)

    def desenhar_cajado(self, tela, tempo_atual, jogador):
        """
        Desenha o cajado do mago reto (como sabre de luz modo defesa), mas rotacionando para o jogador.

        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual para animações
            jogador: Objeto do jogador (para orientação)
        """
        # Atualizar animação de aparecimento do cajado
        tempo_desde_criacao = tempo_atual - self.tempo_criacao
        if tempo_desde_criacao < 1500:  # Aparece nos primeiros 1.5 segundos
            # Fazer o cajado aparecer gradualmente
            self.animacao_cajado = min(100, (tempo_desde_criacao / 1500) * 100)
        else:
            self.animacao_cajado = 100

        # Se ainda não está visível ou animação não começou, não desenhar
        if not self.cajado_visivel or self.animacao_cajado <= 0:
            return

        # Atualizar ângulo do cajado para seguir o jogador
        self.atualizar_angulo_cajado(jogador)

        # Calcular centro do mago (com offset vertical para baixo)
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2 + 8  # 8 pixels mais abaixo

        # MODO DEFESA: Cajado fica à frente do mago (como sabre de luz modo defesa)
        # Distância do cajado à frente do mago (REDUZIDA)
        distancia_base_cajado = 15  # Mais próximo que o sabre (era 35)

        # Calcular posição da base do cajado (à frente do mago)
        base_x = centro_x + math.cos(self.angulo_cajado) * distancia_base_cajado
        base_y = centro_y + math.sin(self.angulo_cajado) * distancia_base_cajado

        # MODO DEFESA: Cajado perpendicular à direção do jogador
        # SOMA 90 graus (pi/2) para ficar perpendicular (invertido)
        angulo_defesa = self.angulo_cajado + math.pi / 2
        dx = math.cos(angulo_defesa)
        dy = math.sin(angulo_defesa)

        # Comprimento atual do cajado baseado na animação
        comprimento_atual = self.comprimento_cajado * (self.animacao_cajado / 100)

        # Posição da ponta do cajado (perpendicular à direção do jogador)
        ponta_x = base_x + dx * comprimento_atual
        ponta_y = base_y + dy * comprimento_atual

        # 1. Desenhar bengala/cajado (linha grossa como sabre de luz)
        # Sombra do cajado
        pygame.draw.line(tela, (50, 30, 10),
                        (base_x + 2, base_y + 2),
                        (ponta_x + 2, ponta_y + 2), self.largura_cajado + 2)

        # Cajado principal (madeira)
        pygame.draw.line(tela, self.cor_cajado,
                        (base_x, base_y),
                        (ponta_x, ponta_y), self.largura_cajado)

        # Detalhe de luz (lado da madeira)
        pygame.draw.line(tela, self.cor_cajado_claro,
                        (base_x, base_y),
                        (ponta_x, ponta_y), 2)

        # 2. Ponta do cajado com brilho durante invocação
        if self.esta_invocando:
            # Pulsar durante invocação
            progresso = (tempo_atual - self.tempo_inicio_invocacao) / self.duracao_invocacao
            brilho_invocacao = int(55 * abs(math.sin(progresso * math.pi * 6)))  # Pulsa mais rápido

            # Brilho intenso na ponta
            for i in range(3):
                raio_brilho = 12 - i * 3
                alpha_brilho = 150 - i * 50
                cor_brilho = (min(255, 200 + brilho_invocacao), min(255, 100 + brilho_invocacao), 255)

                # Criar superfície com alpha para o brilho
                brilho_surface = pygame.Surface((raio_brilho * 2, raio_brilho * 2), pygame.SRCALPHA)
                pygame.draw.circle(brilho_surface, (*cor_brilho, alpha_brilho),
                                 (raio_brilho, raio_brilho), raio_brilho)
                tela.blit(brilho_surface, (int(ponta_x - raio_brilho), int(ponta_y - raio_brilho)))

            # Partículas mágicas girando
            for i in range(8):
                angulo = (2 * math.pi * i) / 8 + (tempo_atual / 150)
                raio_particula = 18 + math.sin(tempo_atual / 100 + i) * 4

                part_x = ponta_x + math.cos(angulo) * raio_particula
                part_y = ponta_y + math.sin(angulo) * raio_particula

                cor_particula = (min(255, 180 + brilho_invocacao), 80, 255)
                pygame.draw.circle(tela, cor_particula, (int(part_x), int(part_y)), 4)
                # Brilho interno
                pygame.draw.circle(tela, (255, 200, 255), (int(part_x), int(part_y)), 2)
        else:
            # Ponta normal do cajado (pequena esfera)
            pygame.draw.circle(tela, (80, 50, 20), (int(ponta_x), int(ponta_y)), 5)
            pygame.draw.circle(tela, (120, 80, 40), (int(ponta_x), int(ponta_y)), 3)

    def desenhar_chapeu(self, tela):
        """
        Desenha o chapéu de mago clássico em cima do quadrado.

        Args:
            tela: Superfície onde desenhar
        """
        centro_x = self.x + self.tamanho // 2
        topo_y = self.y - 3  # Um pouco acima do quadrado

        # Cores do chapéu
        cor_chapeu = (25, 25, 112)  # Azul meia-noite (midnight blue)
        cor_aba = (15, 15, 70)  # Azul mais escuro para sombra
        cor_borda_chapeu = (100, 100, 200)  # Azul mais claro para borda
        cor_estrela = (255, 215, 0)  # Dourado
        cor_lua = (230, 230, 250)  # Lavanda claro

        # 1. Aba do chapéu (mais larga e definida)
        # Sombra da aba
        pygame.draw.ellipse(tela, (0, 0, 40),
                           (centro_x - 24, topo_y + 2, 48, 10))
        # Aba principal
        pygame.draw.ellipse(tela, cor_aba,
                           (centro_x - 22, topo_y, 44, 8))
        # Topo da aba
        pygame.draw.ellipse(tela, cor_chapeu,
                           (centro_x - 22, topo_y - 2, 44, 6))

        # 2. Cone do chapéu (mais alto e curvado)
        ponta_chapeu_y = topo_y - 30

        # Base do cone (cilindro)
        pygame.draw.rect(tela, cor_chapeu,
                        (centro_x - 12, topo_y - 3, 24, 5))

        # Cone principal (polígono curvado)
        pontos_cone = [
            (centro_x, ponta_chapeu_y),      # Ponta
            (centro_x - 14, topo_y - 2),     # Base esquerda
            (centro_x - 12, topo_y),         #
            (centro_x + 12, topo_y),         #
            (centro_x + 14, topo_y - 2)      # Base direita
        ]
        pygame.draw.polygon(tela, cor_chapeu, pontos_cone)

        # Contorno do cone
        pygame.draw.polygon(tela, cor_borda_chapeu, pontos_cone, 1)

        # Linha vertical central (detalhe)
        pygame.draw.line(tela, cor_borda_chapeu,
                        (centro_x, ponta_chapeu_y),
                        (centro_x, topo_y), 1)

        # 3. Decorações mágicas no chapéu
        # Estrelas pequenas
        estrelas_pos = [
            (centro_x - 8, ponta_chapeu_y + 8),
            (centro_x + 8, ponta_chapeu_y + 12),
            (centro_x - 6, ponta_chapeu_y + 18)
        ]

        for pos in estrelas_pos:
            # Estrela de 4 pontas
            for i in range(4):
                angulo = (math.pi / 2 * i) + math.pi / 4
                x = pos[0] + math.cos(angulo) * 3
                y = pos[1] + math.sin(angulo) * 3
                pygame.draw.line(tela, cor_estrela, pos, (int(x), int(y)), 1)
            # Centro da estrela
            pygame.draw.circle(tela, cor_estrela, pos, 2)

        # 4. Lua crescente no chapéu
        lua_x = centro_x + 4
        lua_y = ponta_chapeu_y + 6
        # Círculo externo
        pygame.draw.circle(tela, cor_lua, (lua_x, lua_y), 4)
        # Círculo interno (para criar crescente)
        pygame.draw.circle(tela, cor_chapeu, (lua_x + 2, lua_y), 3)

    def desenhar_escudo(self, tela, tempo_atual):
        """
        Desenha o escudo protetor ao redor do mago (se ativo).

        Args:
            tela: Superfície onde desenhar
            tempo_atual: Tempo atual para animações
        """
        if not self.escudo_ativo:
            return

        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2

        # Efeito de pulsação
        pulsacao = math.sin(tempo_atual / 200) * 3
        raio_atual = self.raio_escudo + pulsacao

        # Desenhar múltiplas camadas do escudo para efeito de brilho
        for i in range(3):
            alpha = 100 - i * 30
            raio_camada = raio_atual + i * 3

            # Criar superfície temporária com alpha
            escudo_surface = pygame.Surface((raio_camada * 2 + 10, raio_camada * 2 + 10), pygame.SRCALPHA)
            cor_com_alpha = (*self.cor_escudo, alpha)
            pygame.draw.circle(escudo_surface, cor_com_alpha, (raio_camada + 5, raio_camada + 5), int(raio_camada), 3)

            tela.blit(escudo_surface, (centro_x - raio_camada - 5, centro_y - raio_camada - 5))

        # Partículas do escudo (efeito hexagonal)
        for i in range(6):
            angulo = (2 * math.pi * i) / 6 + (tempo_atual / 500)
            hex_x = centro_x + math.cos(angulo) * raio_atual
            hex_y = centro_y + math.sin(angulo) * raio_atual

            pygame.draw.circle(tela, self.cor_escudo, (int(hex_x), int(hex_y)), 4)
            pygame.draw.circle(tela, (200, 255, 255), (int(hex_x), int(hex_y)), 2)

    def desenhar(self, tela, tempo_atual):
        """Sobrescreve o método desenhar para incluir todos os visuais do mago."""
        # 1. Desenhar escudo (por trás)
        self.desenhar_escudo(tela, tempo_atual)

        # 2. Desenhar o quadrado base
        super().desenhar(tela, tempo_atual)

        # 3. Desenhar chapéu de mago
        self.desenhar_chapeu(tela)

        # O cajado será desenhado separadamente com referência ao jogador
        # (feito na IA do inimigo)

        # 4. Indicador de invocação (círculo de progresso)
        if self.esta_invocando:
            tempo_decorrido = tempo_atual - self.tempo_inicio_invocacao
            progresso = min(1.0, tempo_decorrido / self.duracao_invocacao)

            centro_x = self.x + self.tamanho // 2
            centro_y = self.y + self.tamanho // 2

            # Desenhar círculo de progresso
            raio_progresso = 40
            num_pontos = int(32 * progresso)

            for i in range(num_pontos):
                angulo = (2 * math.pi * i) / 32 - math.pi / 2
                px = centro_x + math.cos(angulo) * raio_progresso
                py = centro_y + math.sin(angulo) * raio_progresso

                cor_progresso = (200, 50, 255)
                pygame.draw.circle(tela, cor_progresso, (int(px), int(py)), 3)

    def obter_info_estado(self):
        """
        Retorna informações sobre o estado atual do mago.
        Útil para UI ou debugging.
        """
        info = {
            'escudo_ativo': self.escudo_ativo,
            'esta_invocando': self.esta_invocando,
            'tiros_ate_invocar': self.tiros_para_invocar - self.tiros_desde_invocacao
        }
        return info
