#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Boss Fusion - Versão BALANCEADA com ataques únicos e invocações reduzidas.
AJUSTES:
- Um ataque por vez (sem combos)
- Invocações reduzidas (1-2 inimigos)
- Cooldown de invocação aumentado
- Número de tiros reduzido em todos os ataques
- Velocidades balanceadas
"""

import pygame
import math
import random
from src.config import *
from src.entities.quadrado import Quadrado
from src.entities.tiro import Tiro
from src.entities.particula import criar_explosao
from src.utils.sound import gerar_som_explosao, gerar_som_tiro, gerar_som_dano

class BossFusion:
    """
    Boss final com movimentação dinâmica e ataques balanceados.
    """
    
    def __init__(self, x, y):
        # Propriedades básicas
        self.x = x
        self.y = y
        self.tamanho_base = TAMANHO_QUADRADO * 3
        self.tamanho = self.tamanho_base
        self.cor_principal = (120, 0, 120)
        self.cor_secundaria = (200, 0, 0)
        self.cor_brilho = (255, 100, 255)

        # Sistema de vida com fases - AJUSTADO
        self.vidas_max = 40  # REDUZIDO: era 50
        self.vidas = self.vidas_max
        self.fase_boss = 1

        # IMPORTANTE: Boss começa ativo (não congelado após morte do jogador)
        self.congelado_por_morte_jogador = False
        
        # Posicionamento
        self.rect = pygame.Rect(x, y, self.tamanho, self.tamanho)
        self.velocidade_base = 1.5
        self.velocidade = self.velocidade_base
        
        # Sistema de movimentação variada
        self.padroes_movimento = [
            "orbital", "zigzag", "perseguicao", "teleporte", 
            "linha_reta", "figura_8", "tremor", "espiral"
        ]
        self.movimento_atual = "orbital"
        self.tempo_mudanca_movimento = 0
        self.duracao_movimento = 4000
        
        # Variáveis de movimento específicas
        self.centro_orbital_x = LARGURA // 2
        self.centro_orbital_y = ALTURA_JOGO // 2
        self.raio_orbital = 200
        self.angulo_orbital = 0
        self.velocidade_orbital = 0.02
        self.direcao_x = 1
        self.direcao_y = 1
        self.zigzag_contador = 0
        self.teleporte_cooldown = 0
        self.target_x = x
        self.target_y = y
        self.movimento_suave_speed = 0.05
        
        # Sistema de ataques - SEM COMBOS
        self.tempo_ultimo_ataque = 0
        self.padroes_ataque = [
            "rajada_circular", "laser_duplo", "meteoros", "ondas_choque",
            "laser_rotativo", "chuva_energia", "explosao_presas", 
            "tornado_tiros", "barreira_espinhos", "pulso_magnetico"
        ]
        self.ataque_atual = None
        self.cooldown_ataque = 2000
        
        # Estados de ataque específicos
        self.laser_rotativo_angulo = 0
        self.tornado_centro_x = 0
        self.tornado_centro_y = 0
        self.barreira_ativa = False
        self.presas_ativas = []
        
        # Sistema de invocação - DESATIVADO
        self.pode_invocar = False  # DESATIVADO: Boss não invoca mais
        self.tempo_ultima_invocacao = 0
        self.cooldown_invocacao = 999999  # Cooldown infinito (desativado)
        self.max_invocacoes = 0  # Zero invocações permitidas
        
        # Efeitos visuais
        self.pulsacao = 0
        self.tempo_pulsacao = 0
        self.particulas_aura = []
        self.energia_acumulada = 0
        self.rastro_movimento = []
        
        # Estados especiais
        self.invulneravel = False
        self.tempo_invulneravel = 0
        self.duracao_invulneravel = 0
        self.carregando_ataque = False
        self.tempo_carregamento = 0
        self.tempo_carregamento_necessario = 1500
        
        # Sistema de combo DESATIVADO
        self.combo_ativo = False
        self.ataques_combo = []
        self.combo_index = 0
        
        # ID único
        self.id = id(self)
        
        print(f"🔥 Boss Fusion balanceado criado! Vida: {self.vidas}/{self.vidas_max}")
    
    def atualizar_fase(self):
        """Atualiza a fase do boss."""
        vida_porcentagem = self.vidas / self.vidas_max
        
        if vida_porcentagem > 0.66:
            nova_fase = 1
        elif vida_porcentagem > 0.33:
            nova_fase = 2
        else:
            nova_fase = 3
        
        if nova_fase != self.fase_boss:
            self.fase_boss = nova_fase
            self.aplicar_mudanca_fase()
    
    def aplicar_mudanca_fase(self):
        """Mudanças de fase com novos comportamentos - BALANCEADO."""
        print(f"⚡ Boss entrou na FASE {self.fase_boss}!")
        
        if self.fase_boss == 2:
            self.velocidade = self.velocidade_base * 1.2  # REDUZIDO: era 1.3
            self.cooldown_ataque = 1800  # AUMENTADO: era 1500
            self.duracao_movimento = 3500  # AUMENTADO: era 3000
            self.cor_principal = (150, 0, 0)
            self.tempo_carregamento_necessario = 1300  # AUMENTADO: era 1200
            
        elif self.fase_boss == 3:
            self.velocidade = self.velocidade_base * 1.4  # REDUZIDO: era 1.6
            self.cooldown_ataque = 1200  # AUMENTADO: era 1000
            self.duracao_movimento = 2500  # AUMENTADO: era 2000
            self.cor_principal = (200, 0, 0)
            self.tamanho = int(self.tamanho_base * 1.2)
            self.rect.width = self.tamanho
            self.rect.height = self.tamanho
            self.tempo_carregamento_necessario = 1000  # AUMENTADO: era 800
            # Fase 3 SEM combos - ataques simples apenas
            self.combo_ativo = False  # DESATIVADO
    
    def atualizar(self, tempo_atual, jogador, inimigos):
        """Atualização principal."""
        self.atualizar_fase()
        
        # Sistema de movimentação variada
        self.atualizar_movimento(tempo_atual, jogador)
        
        # Manter dentro da tela
        self.x = max(0, min(self.x, LARGURA - self.tamanho))
        self.y = max(0, min(self.y, ALTURA_JOGO - self.tamanho))
        
        # Atualizar retângulo
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Rastro de movimento
        self.atualizar_rastro()
        
        # Sistema de invulnerabilidade
        if self.invulneravel and tempo_atual - self.tempo_invulneravel > self.duracao_invulneravel:
            self.invulneravel = False
        
        # Efeitos visuais
        self.atualizar_efeitos_visuais(tempo_atual)
        
        # Sistema de ataques balanceado
        self.atualizar_sistema_ataques(tempo_atual, jogador, inimigos)
        
        # Sistema de invocação - DESATIVADO (comentado)
        # if (self.pode_invocar and 
        #     tempo_atual - self.tempo_ultima_invocacao > self.cooldown_invocacao and
        #     len([i for i in inimigos if i.vidas > 0]) < self.max_invocacoes):
        #     self.invocar_ajudantes(inimigos, tempo_atual)
    
    def atualizar_movimento(self, tempo_atual, jogador):
        """Sistema de movimentação variada."""
        if tempo_atual - self.tempo_mudanca_movimento > self.duracao_movimento:
            self.escolher_novo_movimento()
            self.tempo_mudanca_movimento = tempo_atual
        
        # Executar movimento atual
        if self.movimento_atual == "orbital":
            self.movimento_orbital()
        elif self.movimento_atual == "zigzag":
            self.movimento_zigzag()
        elif self.movimento_atual == "perseguicao":
            self.movimento_perseguicao(jogador)
        elif self.movimento_atual == "teleporte":
            self.movimento_teleporte(tempo_atual)
        elif self.movimento_atual == "linha_reta":
            self.movimento_linha_reta()
        elif self.movimento_atual == "figura_8":
            self.movimento_figura_8()
        elif self.movimento_atual == "tremor":
            self.movimento_tremor()
        elif self.movimento_atual == "espiral":
            self.movimento_espiral()
    
    def escolher_novo_movimento(self):
        """Escolhe um novo padrão de movimento."""
        padroes_disponiveis = [p for p in self.padroes_movimento if p != self.movimento_atual]
        
        if self.fase_boss == 3:
            padroes_agressivos = ["perseguicao", "teleporte", "tremor", "espiral"]
            padroes_disponiveis.extend(padroes_agressivos)
        
        self.movimento_atual = random.choice(padroes_disponiveis)
        print(f"🎯 Boss mudou para movimento: {self.movimento_atual}")
        
        if self.movimento_atual == "teleporte":
            self.teleporte_cooldown = 0
        elif self.movimento_atual == "zigzag":
            self.zigzag_contador = 0
        elif self.movimento_atual in ["figura_8", "espiral"]:
            self.angulo_orbital = 0
    
    def movimento_orbital(self):
        """Movimento orbital clássico."""
        self.angulo_orbital += self.velocidade_orbital
        self.x = self.centro_orbital_x + math.cos(self.angulo_orbital) * self.raio_orbital - self.tamanho // 2
        self.y = self.centro_orbital_y + math.sin(self.angulo_orbital) * self.raio_orbital - self.tamanho // 2
    
    def movimento_zigzag(self):
        """Movimento em zigue-zague."""
        self.zigzag_contador += 1
        self.x += self.direcao_x * self.velocidade * 2
        
        if self.zigzag_contador % 60 == 0:
            self.direcao_y *= -1
        
        self.y += self.direcao_y * self.velocidade * 3
        
        if self.x <= 0 or self.x >= LARGURA - self.tamanho:
            self.direcao_x *= -1
        if self.y <= 0 or self.y >= ALTURA_JOGO - self.tamanho:
            self.direcao_y *= -1
    
    def movimento_perseguicao(self, jogador):
        """Persegue o jogador diretamente."""
        dx = jogador.x - self.x
        dy = jogador.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            self.x += (dx / dist) * self.velocidade * 1.5
            self.y += (dy / dist) * self.velocidade * 1.5
    
    def movimento_teleporte(self, tempo_atual):
        """Teleporte para posições estratégicas."""
        if self.teleporte_cooldown <= 0:
            posicoes_possiveis = [
                (100, 100), (LARGURA - 100, 100),
                (100, ALTURA_JOGO - 100), (LARGURA - 100, ALTURA_JOGO - 100),
                (LARGURA // 2, 100), (LARGURA // 2, ALTURA_JOGO - 100)
            ]
            
            nova_pos = random.choice(posicoes_possiveis)
            self.x, self.y = nova_pos
            self.teleporte_cooldown = 120
            
            for _ in range(10):
                particula = {
                    'x': self.x + self.tamanho // 2,
                    'y': self.y + self.tamanho // 2,
                    'dx': random.uniform(-5, 5),
                    'dy': random.uniform(-5, 5),
                    'vida': 30,
                    'cor': (255, 0, 255),
                    'tamanho': 6
                }
                self.particulas_aura.append(particula)
        else:
            self.teleporte_cooldown -= 1
    
    def movimento_linha_reta(self):
        """Movimento em linha reta com ricochete."""
        self.x += self.direcao_x * self.velocidade * 3
        self.y += self.direcao_y * self.velocidade * 3
        
        if self.x <= 0 or self.x >= LARGURA - self.tamanho:
            self.direcao_x *= -1
        if self.y <= 0 or self.y >= ALTURA_JOGO - self.tamanho:
            self.direcao_y *= -1
    
    def movimento_figura_8(self):
        """Movimento em figura 8."""
        self.angulo_orbital += self.velocidade_orbital * 2
        a = 150
        self.x = self.centro_orbital_x + a * math.sin(self.angulo_orbital) - self.tamanho // 2
        self.y = self.centro_orbital_y + a * math.sin(self.angulo_orbital) * math.cos(self.angulo_orbital) - self.tamanho // 2
    
    def movimento_tremor(self):
        """Movimento errático com tremores."""
        self.x += random.uniform(-self.velocidade * 4, self.velocidade * 4)
        self.y += random.uniform(-self.velocidade * 4, self.velocidade * 4)
        
        centro_x = LARGURA // 2
        centro_y = ALTURA_JOGO // 2
        
        if abs(self.x - centro_x) > 200:
            self.x += (centro_x - self.x) * 0.01
        if abs(self.y - centro_y) > 150:
            self.y += (centro_y - self.y) * 0.01
    
    def movimento_espiral(self):
        """Movimento em espiral."""
        self.angulo_orbital += self.velocidade_orbital * 3
        raio_variavel = 100 + 80 * math.sin(self.angulo_orbital * 0.5)
        
        self.x = self.centro_orbital_x + math.cos(self.angulo_orbital) * raio_variavel - self.tamanho // 2
        self.y = self.centro_orbital_y + math.sin(self.angulo_orbital) * raio_variavel - self.tamanho // 2
    
    def atualizar_rastro(self):
        """Atualiza rastro de movimento."""
        self.rastro_movimento.append({
            'x': self.x + self.tamanho // 2,
            'y': self.y + self.tamanho // 2,
            'vida': 20
        })
        
        for rastro in self.rastro_movimento[:]:
            rastro['vida'] -= 1
            if rastro['vida'] <= 0:
                self.rastro_movimento.remove(rastro)
        
        if len(self.rastro_movimento) > 15:
            self.rastro_movimento.pop(0)
    
    def atualizar_sistema_ataques(self, tempo_atual, jogador, inimigos):
        """Sistema de ataques melhorado - um ataque por vez."""
        # BUGFIX: Não atacar se boss estiver congelado
        if self.congelado_por_morte_jogador:
            return

        # Só iniciar novo ataque se não estiver carregando
        if not self.carregando_ataque and tempo_atual - self.tempo_ultimo_ataque > self.cooldown_ataque:
            self.iniciar_ataque(tempo_atual)
    
    def iniciar_ataque(self, tempo_atual):
        """Inicia ataque - um por vez, SEM combos."""
        # Atacar apenas se não estiver carregando
        if self.carregando_ataque:
            return
            
        # Escolher um ataque aleatório simples
        padroes_disponiveis = self.padroes_ataque.copy()
        
        # Fase 3 tem ataques mais avançados
        if self.fase_boss == 3:
            ataques_avancados = ["tornado_tiros", "barreira_espinhos", "pulso_magnetico"]
            padroes_disponiveis.extend(ataques_avancados)
        
        self.ataque_atual = random.choice(padroes_disponiveis)
        
        self.carregando_ataque = True
        self.tempo_carregamento = tempo_atual
        self.energia_acumulada = 0
        
        print(f"🎯 Boss carregando: {self.ataque_atual}")
    
    def executar_ataque(self, tiros_inimigo, jogador, particulas, flashes):
        """Executa ataques com novos padrões."""
        centro_x = self.x + self.tamanho // 2
        centro_y = self.y + self.tamanho // 2
        
        # Ataques originais
        if self.ataque_atual == "rajada_circular":
            self.ataque_rajada_circular(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "laser_duplo":
            self.ataque_laser_duplo(centro_x, centro_y, tiros_inimigo, jogador)
        elif self.ataque_atual == "meteoros":
            self.ataque_meteoros(tiros_inimigo, particulas, flashes)
        elif self.ataque_atual == "ondas_choque":
            self.ataque_ondas_choque(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "laser_rotativo":
            self.ataque_laser_rotativo(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "chuva_energia":
            self.ataque_chuva_energia(tiros_inimigo, particulas, flashes)
        elif self.ataque_atual == "explosao_presas":
            self.ataque_explosao_presas(centro_x, centro_y, tiros_inimigo, particulas, flashes)
        elif self.ataque_atual == "tornado_tiros":
            self.ataque_tornado_tiros(centro_x, centro_y, tiros_inimigo, jogador)
        elif self.ataque_atual == "barreira_espinhos":
            self.ataque_barreira_espinhos(centro_x, centro_y, tiros_inimigo)
        elif self.ataque_atual == "pulso_magnetico":
            self.ataque_pulso_magnetico(centro_x, centro_y, tiros_inimigo, jogador)
        
        # Resetar sistema
        self.carregando_ataque = False
        self.tempo_ultimo_ataque = pygame.time.get_ticks()
        self.ataque_atual = None
        
        pygame.mixer.Channel(3).play(pygame.mixer.Sound(gerar_som_explosao()))
    
    # ATAQUES BALANCEADOS
    
    def ataque_rajada_circular(self, centro_x, centro_y, tiros_inimigo):
        """Rajada circular melhorada - BALANCEADA."""
        num_tiros = 16 if self.fase_boss < 3 else 24  # REDUZIDO: era 20 e 32
        
        for i in range(num_tiros):
            angulo = (2 * math.pi * i) / num_tiros
            angulo += random.uniform(-0.1, 0.1)
            
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            cor_tiro = self.cor_secundaria
            velocidade = random.randint(4, 6)  # REDUZIDO: era 5-8
            
            tiro = Tiro(centro_x, centro_y, dx, dy, cor_tiro, velocidade)
            tiros_inimigo.append(tiro)
    
    def ataque_laser_duplo(self, centro_x, centro_y, tiros_inimigo, jogador):
        """Laser duplo com predição."""
        predicao_x = jogador.x + random.randint(-50, 50)
        predicao_y = jogador.y + random.randint(-50, 50)
        
        dx = predicao_x - centro_x
        dy = predicao_y - centro_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dx /= dist
            dy /= dist
        
        for offset in [-0.3, 0, 0.3]:  # REDUZIDO: era 5 lasers
            dx_laser = dx + offset
            dy_laser = dy
            
            norm = math.sqrt(dx_laser**2 + dy_laser**2)
            if norm > 0:
                dx_laser /= norm
                dy_laser /= norm
            
            for i in range(10):  # REDUZIDO: era 12
                tiro = Tiro(centro_x + dx_laser * i * 8, 
                           centro_y + dy_laser * i * 8, 
                           dx_laser, dy_laser, 
                           (255, 0, 255), 9)
                tiros_inimigo.append(tiro)
    
    def ataque_meteoros(self, tiros_inimigo, particulas, flashes):
        """Meteoros melhorados - BALANCEADOS."""
        num_meteoros = 5 if self.fase_boss < 3 else 8  # REDUZIDO: era 8 e 15
        
        for _ in range(num_meteoros):
            x = random.randint(50, LARGURA - 50)
            y = -30
            
            dx = random.uniform(-0.5, 0.5)  # REDUZIDO
            dy = random.uniform(0.6, 1.0)  # REDUZIDO
            
            cor_meteoro = random.choice([(255, 100, 0), (255, 0, 0), (255, 150, 50)])
            velocidade = random.randint(4, 7)  # REDUZIDO
            
            meteoro = Tiro(x, y, dx, dy, cor_meteoro, velocidade)
            meteoro.raio = random.randint(8, 14)  # REDUZIDO
            meteoro.rect = pygame.Rect(x - meteoro.raio, y - meteoro.raio, 
                                     meteoro.raio * 2, meteoro.raio * 2)
            tiros_inimigo.append(meteoro)
    
    def ataque_ondas_choque(self, centro_x, centro_y, tiros_inimigo):
        """Ondas de choque melhoradas."""
        num_ondas = 3 if self.fase_boss < 3 else 5  # REDUZIDO
        
        for onda in range(num_ondas):
            tiros_por_onda = 12  # REDUZIDO: era 16
            
            for i in range(tiros_por_onda):
                angulo = (2 * math.pi * i) / tiros_por_onda
                dx = math.cos(angulo)
                dy = math.sin(angulo)
                
                velocidade = 2.5 + onda * 1.0  # REDUZIDO
                cor_onda = (80 + onda * 25, 0, 180 - onda * 20)
                
                start_x = centro_x + dx * (onda + 1) * 25
                start_y = centro_y + dy * (onda + 1) * 25
                
                tiro = Tiro(start_x, start_y, dx, dy, cor_onda, velocidade)
                tiros_inimigo.append(tiro)
    
    def ataque_laser_rotativo(self, centro_x, centro_y, tiros_inimigo):
        """Laser que gira 360 graus."""
        num_passos = 18  # REDUZIDO: era 24
        for i in range(num_passos):
            angulo = (2 * math.pi * i) / num_passos + self.laser_rotativo_angulo
            
            for dist in range(15, 280, 20):  # REDUZIDO densidade
                x = centro_x + math.cos(angulo) * dist
                y = centro_y + math.sin(angulo) * dist
                
                if 0 <= x <= LARGURA and 0 <= y <= ALTURA_JOGO:
                    tiro = Tiro(x, y, math.cos(angulo), math.sin(angulo), (0, 255, 255), 7)
                    tiros_inimigo.append(tiro)
        
        self.laser_rotativo_angulo += 0.1
    
    def ataque_chuva_energia(self, tiros_inimigo, particulas, flashes):
        """Chuva de energia que cobre toda a tela - BALANCEADA."""
        for _ in range(15):  # REDUZIDO: era 25
            x = random.randint(0, LARGURA)
            y = -50
            
            dx = random.uniform(-0.2, 0.2)  # REDUZIDO
            dy = random.uniform(2.5, 5)  # REDUZIDO
            
            cor = random.choice([(255, 0, 255), (255, 255, 0), (0, 255, 255)])
            tiro = Tiro(x, y, dx, dy, cor, random.randint(3, 6))  # REDUZIDO
            tiro.raio = random.randint(6, 12)  # REDUZIDO
            tiros_inimigo.append(tiro)
    
    def ataque_explosao_presas(self, centro_x, centro_y, tiros_inimigo, particulas, flashes):
        """Cria presas que explodem após um tempo."""
        posicoes_presas = [
            (100, 100), (LARGURA - 100, 100),
            (LARGURA // 2, ALTURA_JOGO // 2)  # REDUZIDO: eram 5, agora 3
        ]
        
        for pos in posicoes_presas:
            presa = {
                'x': pos[0],
                'y': pos[1],
                'tempo_vida': 180,
                'raio': 30,
                'cor': (255, 100, 0)
            }
            self.presas_ativas.append(presa)
    
    def ataque_tornado_tiros(self, centro_x, centro_y, tiros_inimigo, jogador):
        """Tornado de tiros que se move em direção ao jogador."""
        dx = jogador.x - centro_x
        dy = jogador.y - centro_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            dx /= dist
            dy /= dist
        
        for i in range(15):  # REDUZIDO: era 20
            angulo = (2 * math.pi * i) / 15
            raio = 50 + (i * 8)  # REDUZIDO
            
            x = centro_x + math.cos(angulo) * raio
            y = centro_y + math.sin(angulo) * raio
            
            vel_x = dx * 2.5 + math.cos(angulo + math.pi/2) * 1.5  # REDUZIDO
            vel_y = dy * 2.5 + math.sin(angulo + math.pi/2) * 1.5
            
            tiro = Tiro(x, y, vel_x, vel_y, (150, 0, 150), 5)
            tiros_inimigo.append(tiro)
    
    def ataque_barreira_espinhos(self, centro_x, centro_y, tiros_inimigo):
        """Cria barreira de tiros espinhosos ao redor do boss."""
        self.barreira_ativa = True
        
        for i in range(12):  # REDUZIDO: era 16
            angulo = (2 * math.pi * i) / 12
            x = centro_x + math.cos(angulo) * 80
            y = centro_y + math.sin(angulo) * 80
            
            tiro = Tiro(x, y, 0, 0, (100, 100, 100), 0)
            tiro.orbital = True
            tiro.angulo_orbital = angulo
            tiro.raio_orbital = 80
            tiro.centro_x = centro_x
            tiro.centro_y = centro_y
            tiros_inimigo.append(tiro)
    
    def ataque_pulso_magnetico(self, centro_x, centro_y, tiros_inimigo, jogador):
        """Pulso que empurra ou puxa tiros existentes."""
        for i in range(10):  # REDUZIDO: era 12
            angulo = (2 * math.pi * i) / 10
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            tiro = Tiro(centro_x, centro_y, dx, dy, (255, 255, 255), 3.5)
            tiro.pulso_magnetico = True
            tiros_inimigo.append(tiro)
        
        print("🧲 Pulso magnético ativado!")
    
    def atualizar_presas_ativas(self, tiros_inimigo, particulas, flashes):
        """Atualiza e explode presas ativas."""
        for presa in self.presas_ativas[:]:
            presa['tempo_vida'] -= 1
            
            if presa['tempo_vida'] % 20 < 10:
                presa['cor'] = (255, 150, 0)
            else:
                presa['cor'] = (255, 50, 0)
            
            if presa['tempo_vida'] <= 0:
                self.explodir_presa(presa, tiros_inimigo, particulas, flashes)
                self.presas_ativas.remove(presa)
    
    def explodir_presa(self, presa, tiros_inimigo, particulas, flashes):
        """Explode uma presa criando tiros em todas as direções."""
        num_tiros = 10  # REDUZIDO: era 12
        
        for i in range(num_tiros):
            angulo = (2 * math.pi * i) / num_tiros
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            
            tiro = Tiro(presa['x'], presa['y'], dx, dy, (255, 100, 0), 5)
            tiros_inimigo.append(tiro)
        
        flash = criar_explosao(presa['x'], presa['y'], (255, 100, 0), particulas, 40)
        flashes.append(flash)
    
    def atualizar_efeitos_visuais(self, tempo_atual):
        """Efeitos visuais melhorados."""
        if tempo_atual - self.tempo_pulsacao > 80:
            self.tempo_pulsacao = tempo_atual
            self.pulsacao = (self.pulsacao + 1) % 30
        
        if random.random() < 0.4:
            for _ in range(3):
                particula = {
                    'x': self.x + random.randint(0, self.tamanho),
                    'y': self.y + random.randint(0, self.tamanho),
                    'dx': random.uniform(-3, 3),
                    'dy': random.uniform(-3, 3),
                    'vida': random.randint(40, 80),
                    'cor': random.choice([self.cor_principal, self.cor_brilho, (255, 255, 255)]),
                    'tamanho': random.uniform(2, 8)
                }
                self.particulas_aura.append(particula)
        
        for particula in self.particulas_aura[:]:
            particula['x'] += particula['dx']
            particula['y'] += particula['dy']
            particula['vida'] -= 1
            particula['tamanho'] -= 0.08
            
            if particula['vida'] <= 0 or particula['tamanho'] <= 0:
                self.particulas_aura.remove(particula)
    
    def invocar_ajudantes(self, inimigos, tempo_atual):
        """Sistema de invocação melhorado - menos inimigos."""
        from src.entities.inimigo_factory import InimigoFactory
        
        self.tempo_ultima_invocacao = tempo_atual
        
        # REDUZIDO: Número baseado na fase, mas menor
        if self.fase_boss == 1:
            num_invocacoes = 1  # Fase 1: 1 inimigo
        elif self.fase_boss == 2:
            num_invocacoes = 2  # Fase 2: 2 inimigos
        else:
            num_invocacoes = 2  # Fase 3: 2 inimigos (antes era 4)
        
        for _ in range(num_invocacoes):
            cantos = [
                (50, 50), (LARGURA - 50, 50),
                (50, ALTURA_JOGO - 50), (LARGURA - 50, ALTURA_JOGO - 50)
            ]
            meio_bordas = [
                (LARGURA // 2, 50), (LARGURA // 2, ALTURA_JOGO - 50),
                (50, ALTURA_JOGO // 2), (LARGURA - 50, ALTURA_JOGO // 2)
            ]
            
            posicoes_possiveis = cantos + meio_bordas
            x, y = random.choice(posicoes_possiveis)
            
            if self.fase_boss == 1:
                ajudante = InimigoFactory.criar_inimigo_basico(x, y)
            elif self.fase_boss == 2:
                tipos = [InimigoFactory.criar_inimigo_basico, InimigoFactory.criar_inimigo_rapido]
                ajudante = random.choice(tipos)(x, y)
            else:
                tipos = [InimigoFactory.criar_inimigo_basico, InimigoFactory.criar_inimigo_rapido]
                ajudante = random.choice(tipos)(x, y)
            
            ajudante.invocado_pelo_boss = True
            inimigos.append(ajudante)
        
        print(f"Boss invocou {num_invocacoes} ajudante(s)!")
    
    def tomar_dano(self, dano=1):
        """
        Sistema de dano melhorado.

        Args:
            dano: Quantidade de dano a receber (padrão: 1)
        """
        if not self.invulneravel:
            self.vidas -= dano

            duracao_base = 100
            if self.fase_boss == 2:
                duracao_base = 80
            elif self.fase_boss == 3:
                duracao_base = 60

            self.invulneravel = True
            self.tempo_invulneravel = pygame.time.get_ticks()
            self.duracao_invulneravel = duracao_base

            for _ in range(5):
                particula = {
                    'x': self.x + self.tamanho // 2,
                    'y': self.y + self.tamanho // 2,
                    'dx': random.uniform(-4, 4),
                    'dy': random.uniform(-4, 4),
                    'vida': 25,
                    'cor': (255, 255, 255),
                    'tamanho': 6
                }
                self.particulas_aura.append(particula)
            
            print(f"Boss tomou dano! Vida: {self.vidas}/{self.vidas_max}")
            return True
        return False
    
    def desenhar(self, tela, tempo_atual):
        """Sistema de desenho melhorado."""
        # Desenhar rastro
        for rastro in self.rastro_movimento:
            if rastro['vida'] > 0:
                alpha = int(255 * (rastro['vida'] / 20))
                tamanho_rastro = max(1, int(self.tamanho * (rastro['vida'] / 20) * 0.3))
                
                rastro_surface = pygame.Surface((tamanho_rastro * 2, tamanho_rastro * 2))
                rastro_surface.set_alpha(alpha // 3)
                rastro_surface.fill(self.cor_principal)
                
                tela.blit(rastro_surface, (rastro['x'] - tamanho_rastro, rastro['y'] - tamanho_rastro))
        
        # Desenhar partículas
        for particula in self.particulas_aura:
            if particula['tamanho'] > 0:
                pygame.draw.circle(tela, particula['cor'], 
                                 (int(particula['x']), int(particula['y'])), 
                                 max(1, int(particula['tamanho'])))
        
        # Desenhar presas
        for presa in self.presas_ativas:
            pygame.draw.circle(tela, (100, 50, 0), 
                             (int(presa['x']), int(presa['y'])), 
                             presa['raio'], 3)
            pygame.draw.circle(tela, presa['cor'], 
                             (int(presa['x']), int(presa['y'])), 
                             max(5, presa['raio'] // 3))
        
        # Pulsação
        pulso = int(self.pulsacao / 3)
        tamanho_atual = self.tamanho + pulso
        
        # Sombra
        shadow_surface = pygame.Surface((tamanho_atual + 8, tamanho_atual + 8))
        shadow_surface.set_alpha(100)
        shadow_surface.fill((0, 0, 0))
        tela.blit(shadow_surface, (self.x + 4, self.y + 4))
        
        # Cor baseada no estado
        cor_uso = self.cor_principal
        if self.invulneravel and tempo_atual % 150 < 75:
            cor_uso = (255, 255, 255)
        
        # Borda externa
        pygame.draw.rect(tela, (30, 30, 30), 
                        (self.x - 3, self.y - 3, tamanho_atual + 6, tamanho_atual + 6), 0, 10)
        
        # Corpo principal com gradiente
        for i in range(3):
            cor_gradiente = tuple(max(0, c - i * 20) for c in cor_uso)
            pygame.draw.rect(tela, cor_gradiente, 
                            (self.x + i, self.y + i, 
                             tamanho_atual - i * 2, tamanho_atual - i * 2), 0, 8)
        
        # Núcleo central
        core_size = tamanho_atual // 3
        core_x = self.x + tamanho_atual // 2 - core_size // 2
        core_y = self.y + tamanho_atual // 2 - core_size // 2
        
        for i in range(3):
            core_cor = tuple(min(255, c + 80 - i * 25) for c in self.cor_brilho)
            pygame.draw.rect(tela, core_cor, 
                            (core_x + i, core_y + i, 
                             core_size - i * 2, core_size - i * 2), 0, 6)
        
        # Olhos
        olho_size = tamanho_atual // 8
        olho_y = self.y + tamanho_atual // 3
        
        pygame.draw.circle(tela, (50, 50, 50), 
                          (self.x + tamanho_atual // 4, olho_y), olho_size + 2)
        pygame.draw.circle(tela, (50, 50, 50), 
                          (self.x + 3 * tamanho_atual // 4, olho_y), olho_size + 2)
        
        cor_olho = (255, 0, 0) if self.fase_boss < 3 else (255, 100, 0)
        pygame.draw.circle(tela, cor_olho, 
                          (self.x + tamanho_atual // 4, olho_y), olho_size)
        pygame.draw.circle(tela, cor_olho, 
                          (self.x + 3 * tamanho_atual // 4, olho_y), olho_size)
        
        # Reflexo nos olhos
        pygame.draw.circle(tela, (255, 255, 255), 
                          (self.x + tamanho_atual // 4 - 2, olho_y - 2), max(1, olho_size // 3))
        pygame.draw.circle(tela, (255, 255, 255), 
                          (self.x + 3 * tamanho_atual // 4 - 2, olho_y - 2), max(1, olho_size // 3))
        
        # Detalhes por fase
        if self.fase_boss >= 2:
            for lado in [-1, 1]:
                espinho_x = self.x + tamanho_atual // 2 + lado * (tamanho_atual // 2 + 10)
                espinho_y = self.y + tamanho_atual // 2
                pygame.draw.polygon(tela, self.cor_secundaria, [
                    (espinho_x, espinho_y - 8),
                    (espinho_x + lado * 15, espinho_y),
                    (espinho_x, espinho_y + 8)
                ])
        
        if self.fase_boss == 3:
            for i in range(5):
                raio_aura = tamanho_atual // 2 + 20 + i * 8
                alpha = 50 - i * 8
                if alpha > 0:
                    aura_surface = pygame.Surface((raio_aura * 2, raio_aura * 2))
                    aura_surface.set_alpha(alpha)
                    pygame.draw.circle(aura_surface, (200, 0, 200), (raio_aura, raio_aura), raio_aura, 2)
                    tela.blit(aura_surface, (self.x + tamanho_atual // 2 - raio_aura, 
                                           self.y + tamanho_atual // 2 - raio_aura))
        
        # Barra de vida
        self.desenhar_barra_vida(tela)
        
        # Indicador de carregamento
        if self.carregando_ataque:
            self.desenhar_carregamento_ataque(tela, tempo_atual)
    
    def desenhar_barra_vida(self, tela):
        """Barra de vida melhorada."""
        barra_largura = LARGURA - 100
        barra_altura = 25
        barra_x = 50
        barra_y = 25
        
        # Fundo
        pygame.draw.rect(tela, (20, 20, 20), 
                        (barra_x - 3, barra_y - 3, barra_largura + 6, barra_altura + 6), 0, 8)
        pygame.draw.rect(tela, (80, 80, 80), 
                        (barra_x, barra_y, barra_largura, barra_altura), 0, 5)
        
        # Vida restante
        vida_porcentagem = self.vidas / self.vidas_max
        vida_largura = int(barra_largura * vida_porcentagem)
        
        if vida_porcentagem > 0.66:
            cor_vida = (255, 100, 100)
        elif vida_porcentagem > 0.33:
            cor_vida = (255, 150, 0)
        else:
            cor_vida = (255, 0, 0)
        
        if self.fase_boss >= 2:
            cor_vida = tuple(min(255, c + 30) for c in cor_vida)
        
        if vida_largura > 0:
            for i in range(vida_largura):
                alpha = 1.0 - (i / vida_largura) * 0.3
                cor_gradiente = tuple(int(c * alpha) for c in cor_vida)
                pygame.draw.line(tela, cor_gradiente, 
                               (barra_x + i, barra_y), 
                               (barra_x + i, barra_y + barra_altura))
        
        # Texto
        from src.utils.visual import desenhar_texto
        
        nome_texto = f"BOSS FUSION - FASE {self.fase_boss}"
        
        # Sombra
        desenhar_texto(tela, nome_texto, 26, (50, 50, 50), LARGURA // 2 + 2, barra_y - 17)
        # Texto principal
        cor_texto = (255, 255, 255) if self.fase_boss < 3 else (255, 200, 0)
        desenhar_texto(tela, nome_texto, 26, cor_texto, LARGURA // 2, barra_y - 15)
        
        # Vida numérica
        vida_texto = f"{self.vidas}/{self.vidas_max}"
        desenhar_texto(tela, vida_texto, 20, (255, 255, 255), LARGURA // 2, barra_y + 40)
        
        # Indicador de movimento
        movimento_texto = f"Padrão: {self.movimento_atual.title()}"
        desenhar_texto(tela, movimento_texto, 16, (200, 200, 200), LARGURA // 2, barra_y + 60)
    
    def desenhar_carregamento_ataque(self, tela, tempo_atual):
        """Indicador de carregamento melhorado."""
        tempo_carregando = tempo_atual - self.tempo_carregamento
        progresso = min(1.0, tempo_carregando / self.tempo_carregamento_necessario)
        
        if tela is not None:
            centro_x = self.x + self.tamanho // 2
            centro_y = self.y + self.tamanho // 2
            raio = self.tamanho // 2 + 30
            
            # Círculo de fundo
            pygame.draw.circle(tela, (50, 50, 50), (centro_x, centro_y), raio + 3, 3)
            
            # Arco de progresso
            if progresso > 0:
                num_pontos = int(64 * progresso)
                for i in range(num_pontos):
                    angulo = (2 * math.pi * i) / 64
                    x = centro_x + raio * math.cos(angulo - math.pi/2)
                    y = centro_y + raio * math.sin(angulo - math.pi/2)
                    
                    if progresso < 0.5:
                        cor = (255, 255 * progresso * 2, 0)
                    else:
                        cor = (255, 255, 255 * (progresso - 0.5) * 2)
                    
                    pygame.draw.circle(tela, cor, (int(x), int(y)), 4)
            
            # Texto do ataque
            if self.ataque_atual:
                from src.utils.visual import desenhar_texto
                nome_ataque = self.ataque_atual.replace("_", " ").title()
                desenhar_texto(tela, nome_ataque, 18, (255, 255, 0), centro_x, centro_y - 10)
                
                # Barra de progresso
                barra_w = 80
                barra_h = 6
                barra_x = centro_x - barra_w // 2
                barra_y = centro_y + 15
                
                pygame.draw.rect(tela, (50, 50, 50), (barra_x, barra_y, barra_w, barra_h), 0, 3)
                prog_w = int(barra_w * progresso)
                if prog_w > 0:
                    pygame.draw.rect(tela, (255, 200, 0), (barra_x, barra_y, prog_w, barra_h), 0, 3)
        
        return progresso >= 1.0