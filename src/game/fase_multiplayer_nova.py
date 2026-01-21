#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase Multiplayer - Herda de FaseBase para reaproveitar todo o código do jogo.
Adiciona apenas funcionalidade de rede e sincronização entre jogadores.
"""

import pygame
import random
import os
from src.config import *
from src.game.fase_base import FaseBase
from src.utils.display_manager import present_frame
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.tilemap import TileMap


class FaseMultiplayer(FaseBase):
    """
    Classe para fase multiplayer.
    Herda toda a lógica de jogo de FaseBase e adiciona sincronização de rede.
    """

    # Cores dos times
    COR_TIME_T = (255, 100, 100)  # Vermelho claro
    COR_TIME_Q = (100, 150, 255)  # Azul claro

    def __init__(self, tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal, cliente, nome_jogador, bots=None):
        """
        Inicializa a fase multiplayer.

        Args:
            cliente: Instância do GameClient para comunicação de rede
            nome_jogador: Nome do jogador local
            bots: Lista de dicionários com informações dos bots
        """
        # Inicializar como fase base (sem inimigos inicialmente)
        super().__init__(tela, relogio, 1, gradiente_jogo, fonte_titulo, fonte_normal)

        self.cliente = cliente
        self.nome_jogador = nome_jogador
        self.jogadores_remotos = {}  # {player_id: PlayerRemoteData}

        # Configurar nome do jogador local
        self.jogador.nome = nome_jogador

        # Cores para jogadores remotos
        self.cores_remotos = [CIANO, ROXO, LARANJA, AMARELO]
        self.proximo_cor_index = 0

        # Sistema de times
        self.time_jogador = None  # 'T' ou 'Q'
        self.selecionando_time = True  # Flag para mostrar tela de seleção
        self.bots_info = bots or []  # Guardar info dos bots para criar depois

        # Carregar mapa TMX
        caminho_mapa = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'map_tiled.tmx')
        self.tilemap = TileMap(caminho_mapa)
        print(f"[MULTIPLAYER] Mapa carregado: {self.tilemap.largura_pixels}x{self.tilemap.altura_pixels} pixels")

        # Posição inicial temporária (será atualizada após seleção de time)
        self.jogador.x = 500
        self.jogador.y = 500
        self.jogador.rect.x = 500
        self.jogador.rect.y = 500
        self.jogador.rect.width = TAMANHO_MULTIPLAYER
        self.jogador.rect.height = TAMANHO_MULTIPLAYER
        self.jogador.tamanho = TAMANHO_MULTIPLAYER

        # Sistema de câmera para mapas grandes
        self.camera_x = 0
        self.camera_y = 0
        self.camera_zoom = 2.0  # Zoom 2x para aproximar a câmera do jogador

        # Sistema de vitória
        self.jogo_terminado = False
        self.vencedor = None

        # Bots serão criados após seleção de time
        self.bots_locais = []

        # Velocidade reduzida para multiplayer
        self.jogador.velocidade = VELOCIDADE_JOGADOR * 0.35  # 35% da velocidade normal

        print(f"[MULTIPLAYER] Fase inicializada. ID local: {cliente.local_player_id}")
        print(f"[MULTIPLAYER] Aguardando seleção de time...")

    def processar_eventos(self):
        """Sobrescreve processar_eventos para usar posição do mouse convertida para mundo."""
        from src.utils.display_manager import convert_mouse_position

        pos_mouse_tela = convert_mouse_position(pygame.mouse.get_pos())
        pos_mouse_mundo = self._converter_mouse_para_mundo(pos_mouse_tela)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            # Controles durante o jogo
            if not self.mostrando_inicio and not self.pausado:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        self.pausado = True
                        pygame.mouse.set_visible(True)

                # Tiro com clique do mouse - usa posição do mundo
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    self._atirar_multiplayer(pos_mouse_mundo)

            # Controles durante pausa
            elif self.pausado:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.pausado = False
                    pygame.mouse.set_visible(False)

        return None

    def _atirar_multiplayer(self, pos_mouse_mundo):
        """Processa tiro no multiplayer usando coordenadas do mundo."""
        import math
        from src.entities.tiro import Tiro
        from src.utils.sound import gerar_som_tiro

        if self.jogador.vidas <= 0:
            return

        # Centro do jogador
        centro_x = self.jogador.x + TAMANHO_MULTIPLAYER / 2
        centro_y = self.jogador.y + TAMANHO_MULTIPLAYER / 2

        # Calcular direção para o mouse (em coordenadas do mundo)
        dx = pos_mouse_mundo[0] - centro_x
        dy = pos_mouse_mundo[1] - centro_y

        # Normalizar
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Criar tiro com o time do jogador
        tiro = Tiro(centro_x, centro_y, dx, dy, self.jogador.cor, 8)
        tiro.time_origem = self.time_jogador  # Marcar de qual time veio o tiro
        self.tiros_jogador.append(tiro)

        # Som de tiro
        pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))

    def executar(self):
        """
        Loop principal da fase multiplayer.
        Retorna: "menu" para voltar ao menu
        """
        rodando = True

        while rodando:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse = self.obter_pos_mouse()

            # Tela de seleção de time
            if self.selecionando_time:
                resultado = self._mostrar_selecao_time()
                if resultado == "menu":
                    self.limpar()
                    return "menu"
                continue

            # Mostrar/ocultar cursor
            if not self.mostrando_inicio and not self.pausado:
                pygame.mouse.set_visible(False)
            else:
                pygame.mouse.set_visible(True)

            # Processar eventos (herda de FaseBase)
            resultado = self.processar_eventos()
            if resultado == "sair":
                self.limpar()
                return "menu"
            elif resultado == "menu":
                self.limpar()
                return "menu"

            # Atualizar contador de introdução
            if self.mostrando_inicio:
                self._mostrar_introducao_multiplayer(tempo_atual)
                continue

            # Pausado
            if self.pausado:
                self._mostrar_pausa_multiplayer()
                continue

            # Atualizar jogador localmente (predição) com colisões do mapa
            self._atualizar_jogador_com_colisao(pos_mouse, tempo_atual)

            # Atualizar câmera para seguir o jogador
            self._atualizar_camera()

            # Enviar estado do jogador para o servidor
            self._enviar_estado_jogador(pos_mouse)

            # Receber estados de outros jogadores
            self._receber_estados_remotos()

            # Atualizar moedas (usa sistema existente)
            self.atualizar_moedas()

            # Atualizar tiros (sistema próprio para o mapa grande)
            self._atualizar_tiros_multiplayer()

            # Processar sabre de luz (usa sistema existente)
            self.processar_sabre_luz([])

            # Processar granadas (usa sistema existente)
            self.processar_granadas([])

            # Atualizar efeitos visuais (usa sistema existente)
            self.atualizar_efeitos_visuais()

            # Atualizar bots com colisões
            self._atualizar_bots()

            # Processar colisões de tiros com jogadores (PvP)
            self._processar_pvp()

            # Verificar condições de vitória
            self._verificar_vitoria()

            # Desenhar tudo
            self._desenhar_tudo(tempo_atual, pos_mouse)

            # Atualizar display
            present_frame()
            self.relogio.tick(60)

        return "menu"

    def _enviar_estado_jogador(self, pos_mouse):
        """Envia estado do jogador local para o servidor."""
        try:
            # Preparar estado das teclas
            teclas_pygame = pygame.key.get_pressed()
            keys = {
                'w': teclas_pygame[pygame.K_w],
                'a': teclas_pygame[pygame.K_a],
                's': teclas_pygame[pygame.K_s],
                'd': teclas_pygame[pygame.K_d]
            }

            # Enviar input para o servidor
            self.cliente.send_player_input(
                keys,
                int(pos_mouse[0]),
                int(pos_mouse[1]),
                pygame.mouse.get_pressed()[0]
            )
        except Exception as e:
            pass  # Silenciar erros de rede

    def _receber_estados_remotos(self):
        """Recebe e atualiza estados dos jogadores remotos."""
        try:
            # Obter jogadores remotos do cliente
            remote_players = self.cliente.get_remote_players()

            # Atualizar interpolação
            self.cliente.update_interpolation(1.0 / 60.0)

            # Atualizar jogadores remotos
            novos_jogadores = {}

            for player_id, remote_player in remote_players.items():
                # Criar ou atualizar jogador remoto
                if player_id not in self.jogadores_remotos:
                    # Novo jogador - atribuir cor
                    cor = self.cores_remotos[self.proximo_cor_index % len(self.cores_remotos)]
                    self.proximo_cor_index += 1

                    jogador_remoto = type('PlayerRemote', (), {})()
                    jogador_remoto.id = player_id
                    jogador_remoto.nome = remote_player.name
                    jogador_remoto.cor = cor
                    jogador_remoto.x = remote_player.x
                    jogador_remoto.y = remote_player.y
                    jogador_remoto.vida = remote_player.health
                    jogador_remoto.vivo = remote_player.alive

                    print(f"[MULTIPLAYER] Novo jogador conectado: {jogador_remoto.nome}")
                else:
                    # Atualizar jogador existente
                    jogador_remoto = self.jogadores_remotos[player_id]
                    jogador_remoto.x = remote_player.x
                    jogador_remoto.y = remote_player.y
                    jogador_remoto.vida = remote_player.health
                    jogador_remoto.vivo = remote_player.alive

                novos_jogadores[player_id] = jogador_remoto

            # Detectar jogadores desconectados
            for player_id in self.jogadores_remotos:
                if player_id not in novos_jogadores:
                    nome = self.jogadores_remotos[player_id].nome
                    print(f"[MULTIPLAYER] Jogador desconectado: {nome}")

            self.jogadores_remotos = novos_jogadores

        except Exception as e:
            print(f"[ERRO] Falha ao receber estados: {e}")

    def _mostrar_selecao_time(self):
        """Mostra a tela de seleção de time (T ou Q)."""
        from src.utils.visual import desenhar_texto
        from src.utils.display_manager import convert_mouse_position

        # Botões dos times
        btn_time_t = pygame.Rect(LARGURA // 4 - 100, ALTURA // 2 - 50, 200, 100)
        btn_time_q = pygame.Rect(3 * LARGURA // 4 - 100, ALTURA // 2 - 50, 200, 100)

        pygame.mouse.set_visible(True)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "menu"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return "menu"

            if evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_click_pos = convert_mouse_position(evento.pos)

                # Botão Time T
                if btn_time_t.collidepoint(mouse_click_pos):
                    self._selecionar_time('T')
                    return None

                # Botão Time Q
                if btn_time_q.collidepoint(mouse_click_pos):
                    self._selecionar_time('Q')
                    return None

        # Desenhar tela de seleção
        self.tela.fill((20, 20, 40))
        self.tela.blit(self.gradiente_jogo, (0, 0))

        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())

        # Título
        desenhar_texto(self.tela, "ESCOLHA SEU TIME", 60, BRANCO, LARGURA // 2, ALTURA // 4)

        # Botão Time T
        hover_t = btn_time_t.collidepoint(mouse_pos)
        cor_t = (255, 120, 120) if hover_t else self.COR_TIME_T
        pygame.draw.rect(self.tela, cor_t, btn_time_t, 0, 15)
        pygame.draw.rect(self.tela, BRANCO, btn_time_t, 3, 15)
        desenhar_texto(self.tela, "TIME T", 40, BRANCO, btn_time_t.centerx, btn_time_t.centery - 10)
        desenhar_texto(self.tela, "(Terroristas)", 20, (200, 200, 200), btn_time_t.centerx, btn_time_t.centery + 25)

        # Botão Time Q
        hover_q = btn_time_q.collidepoint(mouse_pos)
        cor_q = (120, 170, 255) if hover_q else self.COR_TIME_Q
        pygame.draw.rect(self.tela, cor_q, btn_time_q, 0, 15)
        pygame.draw.rect(self.tela, BRANCO, btn_time_q, 3, 15)
        desenhar_texto(self.tela, "TIME Q", 40, BRANCO, btn_time_q.centerx, btn_time_q.centery - 10)
        desenhar_texto(self.tela, "(Counter)", 20, (200, 200, 200), btn_time_q.centerx, btn_time_q.centery + 25)

        # Instrução
        desenhar_texto(self.tela, "Pressione ESC para voltar", 20, (150, 150, 150), LARGURA // 2, ALTURA - 50)

        present_frame()
        self.relogio.tick(60)

        return None

    def _selecionar_time(self, time):
        """Seleciona um time e inicializa o jogo."""
        self.time_jogador = time
        self.selecionando_time = False

        # Definir cor do jogador baseada no time
        if time == 'T':
            self.jogador.atualizar_cor(self.COR_TIME_T)
        else:
            self.jogador.atualizar_cor(self.COR_TIME_Q)

        # Posicionar jogador no spawn do time
        spawn_name = f"Start_{time}"
        spawn_pos = self.tilemap.get_spawn_point(spawn_name)

        if spawn_pos:
            self.jogador.x = spawn_pos[0]
            self.jogador.y = spawn_pos[1]
            self.jogador.rect.x = spawn_pos[0]
            self.jogador.rect.y = spawn_pos[1]
            print(f"[MULTIPLAYER] Jogador posicionado no spawn {spawn_name}: {spawn_pos}")
        else:
            # Fallback
            pos_inicial = self._encontrar_posicao_valida()
            self.jogador.x = pos_inicial[0]
            self.jogador.y = pos_inicial[1]
            self.jogador.rect.x = pos_inicial[0]
            self.jogador.rect.y = pos_inicial[1]
            print(f"[MULTIPLAYER] Spawn não encontrado, posição alternativa: {pos_inicial}")

        # Criar bots distribuídos entre os times
        self._criar_bots_distribuidos()

        print(f"[MULTIPLAYER] Time {time} selecionado!")
        print(f"[MULTIPLAYER] Modo: VERSUS - {len(self.bots_locais)} bots")

    def _criar_bots_distribuidos(self):
        """Cria bots distribuídos entre os dois times."""
        self.bots_locais = []

        if not self.bots_info:
            return

        # Dividir bots entre times T e Q
        metade = len(self.bots_info) // 2

        for i, bot_info in enumerate(self.bots_info):
            # Primeira metade vai pro time T, segunda pro time Q
            time_bot = 'T' if i < metade else 'Q'
            bot = self._criar_bot_com_time(bot_info, time_bot)
            self.bots_locais.append(bot)
            print(f"[MULTIPLAYER] Bot criado: {bot.nome} - Time {time_bot}")

    def _criar_bot_com_time(self, bot_info, time_bot):
        """Cria um bot para um time específico."""
        # Posição no spawn do time
        spawn_name = f"Start_{time_bot}"
        spawn_obj = self.tilemap.get_objeto(spawn_name)

        if spawn_obj:
            # Posição aleatória dentro da área de spawn
            x = spawn_obj['x'] + random.random() * spawn_obj['width']
            y = spawn_obj['y'] + random.random() * spawn_obj['height']
        else:
            x, y = self._encontrar_posicao_valida()

        # Cor baseada no time
        if time_bot == 'T':
            cor = self.COR_TIME_T
        else:
            cor = self.COR_TIME_Q

        # Criar entidade do bot com tamanho menor para o dungeon (velocidade reduzida)
        bot = Quadrado(x, y, TAMANHO_MULTIPLAYER, cor, VELOCIDADE_JOGADOR * 0.3)
        bot.nome = bot_info['nome']
        bot.vidas = 5
        bot.vidas_max = 5
        bot.time = time_bot  # Guardar o time do bot

        # IA do bot
        bot.is_bot = True
        bot.alvo_x = x
        bot.alvo_y = y
        bot.tempo_ultimo_tiro = 0
        bot.tempo_mudar_alvo = pygame.time.get_ticks()

        return bot

    def _encontrar_posicao_valida(self):
        """Encontra uma posição válida (não sólida) no mapa para spawn."""
        import random

        # Tentar encontrar uma posição válida
        for _ in range(100):
            x = random.randint(100, self.tilemap.largura_pixels - 100)
            y = random.randint(100, self.tilemap.altura_pixels - 100)

            # Verificar se a posição não é sólida (usar tamanho multiplayer menor)
            rect_teste = pygame.Rect(x, y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
            if not self.tilemap.colide_com_rect(rect_teste):
                return x, y

        # Fallback para o centro do mapa
        return self.tilemap.largura_pixels // 2, self.tilemap.altura_pixels // 2

    def _atualizar_jogador_com_colisao(self, pos_mouse, tempo_atual):
        """Atualiza o jogador com verificação de colisão do mapa."""
        import math

        if self.jogador.vidas <= 0:
            return

        # Ler teclas diretamente para evitar problemas de estado
        teclas = pygame.key.get_pressed()
        mov_x = 0
        mov_y = 0

        if teclas[pygame.K_a]:
            mov_x -= 1
        if teclas[pygame.K_d]:
            mov_x += 1
        if teclas[pygame.K_w]:
            mov_y -= 1
        if teclas[pygame.K_s]:
            mov_y += 1

        # Normalizar movimento diagonal para manter velocidade consistente
        if mov_x != 0 and mov_y != 0:
            magnitude = math.sqrt(2)  # sqrt(1^2 + 1^2)
            mov_x /= magnitude
            mov_y /= magnitude

        # Velocidade fixa para multiplayer
        velocidade = 2.0

        # Calcular velocidade de movimento
        vel_x = mov_x * velocidade
        vel_y = mov_y * velocidade

        # Usar rect com tamanho multiplayer para colisões
        rect_colisao = pygame.Rect(self.jogador.x, self.jogador.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)

        # Resolver colisão com o mapa
        novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(
            rect_colisao, vel_x, vel_y
        )

        # Aplicar nova posição
        self.jogador.x = novo_x
        self.jogador.y = novo_y
        self.jogador.rect.x = novo_x
        self.jogador.rect.y = novo_y
        self.jogador.rect.width = TAMANHO_MULTIPLAYER
        self.jogador.rect.height = TAMANHO_MULTIPLAYER

        # Atualizar outros aspectos do jogador
        self.jogador.atualizar()

    def _converter_mouse_para_mundo(self, pos_mouse):
        """Converte posição do mouse na tela para coordenadas do mundo (considerando zoom)."""
        # Converter posição da tela para coordenadas do mundo
        mundo_x = pos_mouse[0] / self.camera_zoom + self.camera_x
        mundo_y = pos_mouse[1] / self.camera_zoom + self.camera_y
        return (mundo_x, mundo_y)

    def _atualizar_camera(self):
        """Atualiza a posição da câmera para seguir o jogador com zoom."""
        # Dimensões da tela com zoom aplicado
        largura_visivel = LARGURA / self.camera_zoom
        altura_visivel = ALTURA_JOGO / self.camera_zoom

        # Centro da tela (em coordenadas do mundo)
        centro_x = largura_visivel / 2
        centro_y = altura_visivel / 2

        # Câmera segue o jogador
        self.camera_x = self.jogador.x - centro_x
        self.camera_y = self.jogador.y - centro_y

        # Limitar câmera aos limites do mapa
        self.camera_x = max(0, min(self.camera_x, self.tilemap.largura_pixels - largura_visivel))
        self.camera_y = max(0, min(self.camera_y, self.tilemap.altura_pixels - altura_visivel))

    def _atualizar_bots(self):
        """Atualiza IA dos bots com colisões do mapa."""
        import random
        import math
        tempo_atual = pygame.time.get_ticks()

        for bot in self.bots_locais[:]:
            # Bot morreu
            if bot.vidas <= 0:
                print(f"[BOT] {bot.nome} foi eliminado!")
                self.bots_locais.remove(bot)
                continue

            # Mudar alvo periodicamente (movimento aleatório)
            if tempo_atual - bot.tempo_mudar_alvo > 2000:  # A cada 2 segundos
                # Encontrar um alvo válido (não sólido)
                for _ in range(10):
                    novo_alvo_x = random.randint(100, self.tilemap.largura_pixels - 100)
                    novo_alvo_y = random.randint(100, self.tilemap.altura_pixels - 100)
                    if not self.tilemap.is_solid(novo_alvo_x, novo_alvo_y):
                        bot.alvo_x = novo_alvo_x
                        bot.alvo_y = novo_alvo_y
                        break
                bot.tempo_mudar_alvo = tempo_atual

            # Mover em direção ao alvo
            dx = bot.alvo_x - bot.x
            dy = bot.alvo_y - bot.y
            distancia = math.sqrt(dx**2 + dy**2)

            if distancia > 5:
                vel_x = (dx / distancia) * bot.velocidade
                vel_y = (dy / distancia) * bot.velocidade

                # Resolver colisão com o mapa (usar tamanho multiplayer)
                bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
                novo_x, novo_y, colidiu_x, colidiu_y = self.tilemap.resolver_colisao(
                    bot_rect, vel_x, vel_y
                )

                bot.x = novo_x
                bot.y = novo_y

                # Se colidiu, mudar alvo
                if colidiu_x or colidiu_y:
                    bot.tempo_mudar_alvo = 0  # Forçar novo alvo

            # Só atirar se for do time oposto ao jogador
            bot_time = getattr(bot, 'time', None)
            if bot_time and bot_time != self.time_jogador:
                # Atirar no jogador se estiver próximo (time oposto)
                dx_jogador = self.jogador.x - bot.x
                dy_jogador = self.jogador.y - bot.y
                dist_jogador = math.sqrt(dx_jogador**2 + dy_jogador**2)

                if dist_jogador < 400 and tempo_atual - bot.tempo_ultimo_tiro > 800:  # Atirar a cada 800ms
                    # Criar tiro do bot
                    angulo = math.atan2(dy_jogador, dx_jogador)
                    tiro_dx = math.cos(angulo)
                    tiro_dy = math.sin(angulo)

                    from src.entities.tiro import Tiro
                    tiro = Tiro(bot.x, bot.y, tiro_dx, tiro_dy, bot.cor, 7)
                    tiro.time_origem = bot_time  # Marcar de qual time veio o tiro
                    self.tiros_inimigo.append(tiro)
                    bot.tempo_ultimo_tiro = tempo_atual

    def _atualizar_tiros_multiplayer(self):
        """Atualiza tiros no mundo do multiplayer (não usa limites da tela)."""
        # Atualizar tiros do jogador
        for tiro in self.tiros_jogador[:]:
            tiro.atualizar()

            # Remover tiros que saíram do MAPA
            if (tiro.x < 0 or tiro.x > self.tilemap.largura_pixels or
                tiro.y < 0 or tiro.y > self.tilemap.altura_pixels):
                self.tiros_jogador.remove(tiro)
                continue

            # Remover tiros que colidiram com tiles sólidos
            if self.tilemap.is_solid(tiro.x, tiro.y):
                self.tiros_jogador.remove(tiro)

        # Atualizar tiros dos bots/inimigos
        for tiro in self.tiros_inimigo[:]:
            tiro.atualizar()

            # Remover tiros que saíram do MAPA
            if (tiro.x < 0 or tiro.x > self.tilemap.largura_pixels or
                tiro.y < 0 or tiro.y > self.tilemap.altura_pixels):
                self.tiros_inimigo.remove(tiro)
                continue

            # Remover tiros que colidiram com tiles sólidos
            if self.tilemap.is_solid(tiro.x, tiro.y):
                self.tiros_inimigo.remove(tiro)

    def _processar_pvp(self):
        """Processa colisões de tiros com jogadores (PvP) - só afeta times opostos."""
        # Tiros do jogador local atingindo bots do time oposto
        for tiro in self.tiros_jogador[:]:
            tiro_time = getattr(tiro, 'time_origem', self.time_jogador)
            tiro_removido = False

            # Verificar colisão com bots (só do time oposto)
            for bot in self.bots_locais:
                if tiro_removido:
                    break

                bot_time = getattr(bot, 'time', None)

                # Só causar dano se for do time oposto ao tiro
                if bot_time == tiro_time:
                    continue  # Mesmo time, não causa dano

                bot_rect = pygame.Rect(
                    bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER
                )

                if tiro.rect.colliderect(bot_rect):
                    criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                    if tiro in self.tiros_jogador:
                        self.tiros_jogador.remove(tiro)
                        tiro_removido = True
                    dano = getattr(tiro, 'dano', 1)
                    bot.vidas = max(0, bot.vidas - dano)
                    print(f"[PVP] Jogador acertou {bot.nome} (Time {bot_time})! Vida restante: {bot.vidas}")

        # Tiros de bots atingindo jogador e outros bots (só de times opostos)
        for tiro in self.tiros_inimigo[:]:
            tiro_time = getattr(tiro, 'time_origem', None)
            tiro_removido = False

            # Verificar colisão com jogador (só se for do time oposto)
            if tiro_time and tiro_time != self.time_jogador and self.jogador.vidas > 0:
                jogador_rect = pygame.Rect(
                    self.jogador.x, self.jogador.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER
                )

                if tiro.rect.colliderect(jogador_rect):
                    criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                    if tiro in self.tiros_inimigo:
                        self.tiros_inimigo.remove(tiro)
                        tiro_removido = True
                    dano = getattr(tiro, 'dano', 1)
                    self.jogador.vidas = max(0, self.jogador.vidas - dano)
                    print(f"[PVP] Bot do Time {tiro_time} acertou você! Vida restante: {self.jogador.vidas}")

            # Verificar colisão com bots do time oposto ao tiro
            if not tiro_removido:
                for bot in self.bots_locais:
                    bot_time = getattr(bot, 'time', None)

                    # Só causar dano se for do time oposto ao tiro
                    if bot_time == tiro_time:
                        continue

                    bot_rect = pygame.Rect(
                        bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER
                    )

                    if tiro.rect.colliderect(bot_rect):
                        criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                        if tiro in self.tiros_inimigo:
                            self.tiros_inimigo.remove(tiro)
                        dano = getattr(tiro, 'dano', 1)
                        bot.vidas = max(0, bot.vidas - dano)
                        print(f"[PVP] Tiro do Time {tiro_time} acertou {bot.nome} (Time {bot_time})!")
                        break

    def _verificar_vitoria(self):
        """Verifica se um time venceu (todos do time oposto eliminados)."""
        if self.jogo_terminado:
            return

        # Contar membros vivos de cada time
        time_t_vivos = 0
        time_q_vivos = 0

        # Jogador local
        if self.jogador.vidas > 0:
            if self.time_jogador == 'T':
                time_t_vivos += 1
            else:
                time_q_vivos += 1

        # Bots
        for bot in self.bots_locais:
            if bot.vidas > 0:
                bot_time = getattr(bot, 'time', None)
                if bot_time == 'T':
                    time_t_vivos += 1
                elif bot_time == 'Q':
                    time_q_vivos += 1

        # Verificar se algum time foi eliminado
        if time_t_vivos == 0 and time_q_vivos > 0:
            self.jogo_terminado = True
            self.vencedor = "Time Q"
            self.time_vencedor = 'Q'
            print(f"[VITORIA] Time Q venceu a partida!")
        elif time_q_vivos == 0 and time_t_vivos > 0:
            self.jogo_terminado = True
            self.vencedor = "Time T"
            self.time_vencedor = 'T'
            print(f"[VITORIA] Time T venceu a partida!")

    def _desenhar_tudo(self, tempo_atual, pos_mouse):
        """Desenha todos os elementos do jogo com mapa, câmera e zoom."""
        # Fundo preto
        self.tela.fill((20, 20, 30))

        # Criar superfície para o mundo (será escalada depois)
        largura_visivel = int(LARGURA / self.camera_zoom)
        altura_visivel = int(ALTURA_JOGO / self.camera_zoom)
        mundo_surface = pygame.Surface((largura_visivel, altura_visivel))
        mundo_surface.fill((20, 20, 30))

        # Desenhar o mapa com a câmera na superfície do mundo
        self.tilemap.desenhar_tiles(
            mundo_surface,
            self.camera_x,
            self.camera_y,
            cor_chao=(40, 35, 50),    # Cor do chão (tile 111)
            cor_parede=(80, 60, 45)   # Cor das paredes
        )

        # Desenhar jogador com visual melhorado (estilo fase_base)
        if self.jogador.vidas > 0:
            self._desenhar_jogador_estilizado(mundo_surface, tempo_atual)

        # Desenhar jogadores remotos
        self._desenhar_jogadores_remotos(mundo_surface, tempo_atual)

        # Desenhar bots
        self._desenhar_bots(mundo_surface, tempo_atual)

        # Desenhar tiros do jogador (POR CIMA de tudo, com borda para visibilidade)
        for tiro in self.tiros_jogador:
            tiro_x = tiro.x - self.camera_x
            tiro_y = tiro.y - self.camera_y
            # Borda preta para contraste
            pygame.draw.circle(mundo_surface, (0, 0, 0), (int(tiro_x), int(tiro_y)), 3)
            # Tiro colorido
            pygame.draw.circle(mundo_surface, tiro.cor, (int(tiro_x), int(tiro_y)), 2)

        # Desenhar tiros dos inimigos/bots (POR CIMA de tudo, com borda para visibilidade)
        for tiro in self.tiros_inimigo:
            tiro_x = tiro.x - self.camera_x
            tiro_y = tiro.y - self.camera_y
            # Borda preta para contraste
            pygame.draw.circle(mundo_surface, (0, 0, 0), (int(tiro_x), int(tiro_y)), 3)
            # Tiro colorido
            pygame.draw.circle(mundo_surface, tiro.cor, (int(tiro_x), int(tiro_y)), 2)

        # Desenhar partículas (por cima de tudo)
        for particula in self.particulas:
            particula.desenhar_offset(mundo_surface, -self.camera_x, -self.camera_y)

        # Escalar a superfície do mundo para aplicar o zoom
        mundo_escalado = pygame.transform.scale(mundo_surface, (LARGURA, ALTURA_JOGO))
        self.tela.blit(mundo_escalado, (0, 0))

        # Desenhar mira (usa método da FaseBase) - na tela principal, não escalada
        self.renderizar_mira(pos_mouse)

        # Desenhar HUD (usa método da FaseBase)
        self.renderizar_hud(tempo_atual, [])

        # Desenhar informações multiplayer
        self._desenhar_info_multiplayer()

        # Tela de vitória se o jogo acabou
        if self.jogo_terminado:
            self._desenhar_tela_vitoria()

    def _desenhar_jogador_estilizado(self, surface, tempo_atual):
        """Desenha o jogador com visual idêntico ao da fase_base (Quadrado.desenhar)."""
        jogador = self.jogador
        tela_x = jogador.x - self.camera_x
        tela_y = jogador.y - self.camera_y
        tamanho = TAMANHO_MULTIPLAYER

        # Efeito de pulsação
        if tempo_atual - jogador.tempo_pulsacao > 100:
            jogador.tempo_pulsacao = tempo_atual
            jogador.pulsando = (jogador.pulsando + 1) % 12

        mod_tamanho = 0
        if jogador.pulsando < 6:
            mod_tamanho = int(jogador.pulsando * 0.3)  # Pulsação menor para tamanho menor
        else:
            mod_tamanho = int((12 - jogador.pulsando) * 0.3)

        # Piscar se invulnerável
        if jogador.invulneravel and tempo_atual % 200 < 100:
            return

        # Desenhar sombra
        pygame.draw.rect(surface, (20, 20, 20),
                        (tela_x + 2, tela_y + 2, tamanho, tamanho), 0, 2)

        # Cor a usar (branco se tomou dano recente)
        cor_uso = jogador.cor
        if jogador.efeito_dano > 0:
            cor_uso = BRANCO
            jogador.efeito_dano -= 1

        # Quadrado interior (cor escura)
        cor_escura = jogador.cor_escura
        pygame.draw.rect(surface, cor_escura,
                        (tela_x, tela_y, tamanho + mod_tamanho, tamanho + mod_tamanho), 0, 3)

        # Quadrado exterior (cor principal, menor)
        pygame.draw.rect(surface, cor_uso,
                        (tela_x + 1, tela_y + 1, tamanho + mod_tamanho - 2, tamanho + mod_tamanho - 2), 0, 2)

        # Brilho no canto superior esquerdo
        cor_brilhante = jogador.cor_brilhante
        pygame.draw.rect(surface, cor_brilhante,
                        (tela_x + 2, tela_y + 2, 3, 3), 0, 1)

        # Barra de vida acima do jogador
        vida_largura = tamanho + 4
        altura_barra = 3
        pygame.draw.rect(surface, (40, 40, 40),
                        (tela_x - 2, tela_y - 8, vida_largura, altura_barra), 0, 1)
        vida_atual = int((jogador.vidas / jogador.vidas_max) * vida_largura)
        if vida_atual > 0:
            pygame.draw.rect(surface, jogador.cor,
                            (tela_x - 2, tela_y - 8, vida_atual, altura_barra), 0, 1)

        # Nome do jogador (fonte menor para caber)
        nome_surface = self.fonte_pequena.render(self.nome_jogador, True, VERDE)
        # Escalar a fonte para ficar menor
        nome_surface = pygame.transform.scale(nome_surface,
            (nome_surface.get_width() // 2, nome_surface.get_height() // 2))
        nome_rect = nome_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 14))
        surface.blit(nome_surface, nome_rect)

    def _desenhar_tela_vitoria(self):
        """Desenha a tela de vitória com o vencedor por time."""
        from src.utils.visual import desenhar_texto

        # Overlay escuro
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.tela.blit(overlay, (0, 0))

        # Verificar se o time do jogador venceu
        time_vencedor = getattr(self, 'time_vencedor', None)
        jogador_venceu = (time_vencedor == self.time_jogador)

        # Texto de vitória
        if jogador_venceu:
            desenhar_texto(self.tela, "VITORIA!", 90, VERDE, LARGURA // 2, ALTURA // 2 - 100)
            desenhar_texto(self.tela, f"Seu time ({self.vencedor}) venceu!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 20)
        else:
            desenhar_texto(self.tela, "DERROTA", 90, VERMELHO, LARGURA // 2, ALTURA // 2 - 100)
            desenhar_texto(self.tela, f"{self.vencedor} venceu!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 20)

        desenhar_texto(self.tela, "Pressione ESC para sair", 24, BRANCO, LARGURA // 2, ALTURA // 2 + 60)

    def _desenhar_jogadores_remotos(self, surface, tempo_atual):
        """Desenha todos os jogadores remotos com visual estilizado."""
        largura_visivel = int(LARGURA / self.camera_zoom)
        altura_visivel = int(ALTURA_JOGO / self.camera_zoom)

        for player_id, jogador_remoto in self.jogadores_remotos.items():
            # Só desenhar se estiver vivo
            if not getattr(jogador_remoto, 'vivo', True):
                continue

            # Posição na tela (com câmera)
            tela_x = jogador_remoto.x - self.camera_x
            tela_y = jogador_remoto.y - self.camera_y
            tamanho = TAMANHO_MULTIPLAYER

            # Só desenhar se estiver visível na tela
            if -50 < tela_x < largura_visivel + 50 and -50 < tela_y < altura_visivel + 50:
                # Gerar cores derivadas
                cor = jogador_remoto.cor
                cor_escura = tuple(max(0, c - 50) for c in cor)
                cor_brilhante = tuple(min(255, c + 70) for c in cor)

                # Desenhar sombra
                pygame.draw.rect(surface, (20, 20, 20),
                                (tela_x + 2, tela_y + 2, tamanho, tamanho), 0, 2)

                # Quadrado interior (cor escura)
                pygame.draw.rect(surface, cor_escura,
                                (tela_x, tela_y, tamanho, tamanho), 0, 3)

                # Quadrado exterior (cor principal)
                pygame.draw.rect(surface, cor,
                                (tela_x + 1, tela_y + 1, tamanho - 2, tamanho - 2), 0, 2)

                # Brilho no canto
                pygame.draw.rect(surface, cor_brilhante,
                                (tela_x + 2, tela_y + 2, 3, 3), 0, 1)

                # Barra de vida
                vida_largura = tamanho + 4
                altura_barra = 3
                vida_max = getattr(jogador_remoto, 'vida_max', 5)
                vida_atual_val = getattr(jogador_remoto, 'vida', vida_max)
                pygame.draw.rect(surface, (40, 40, 40),
                                (tela_x - 2, tela_y - 8, vida_largura, altura_barra), 0, 1)
                vida_barra = int((vida_atual_val / vida_max) * vida_largura)
                if vida_barra > 0:
                    pygame.draw.rect(surface, cor,
                                    (tela_x - 2, tela_y - 8, vida_barra, altura_barra), 0, 1)

                # Nome acima do jogador (fonte menor)
                nome_surface = self.fonte_pequena.render(jogador_remoto.nome, True, BRANCO)
                nome_surface = pygame.transform.scale(nome_surface,
                    (nome_surface.get_width() // 2, nome_surface.get_height() // 2))
                nome_rect = nome_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 14))
                surface.blit(nome_surface, nome_rect)

    def _desenhar_bots(self, surface, tempo_atual):
        """Desenha todos os bots com visual estilizado."""
        largura_visivel = int(LARGURA / self.camera_zoom)
        altura_visivel = int(ALTURA_JOGO / self.camera_zoom)

        for bot in self.bots_locais:
            # Posição na tela (com câmera)
            tela_x = bot.x - self.camera_x
            tela_y = bot.y - self.camera_y
            tamanho = TAMANHO_MULTIPLAYER

            # Só desenhar se estiver visível na tela
            if -50 < tela_x < largura_visivel + 50 and -50 < tela_y < altura_visivel + 50:
                # Gerar cores derivadas
                cor = bot.cor
                cor_escura = tuple(max(0, c - 50) for c in cor)
                cor_brilhante = tuple(min(255, c + 70) for c in cor)

                # Efeito de pulsação para bots
                pulsando = getattr(bot, 'pulsando', 0)
                tempo_pulsacao = getattr(bot, 'tempo_pulsacao', 0)
                if tempo_atual - tempo_pulsacao > 100:
                    bot.tempo_pulsacao = tempo_atual
                    bot.pulsando = (pulsando + 1) % 12

                mod_tamanho = 0
                if pulsando < 6:
                    mod_tamanho = int(pulsando * 0.3)
                else:
                    mod_tamanho = int((12 - pulsando) * 0.3)

                # Desenhar sombra
                pygame.draw.rect(surface, (20, 20, 20),
                                (tela_x + 2, tela_y + 2, tamanho, tamanho), 0, 2)

                # Quadrado interior (cor escura)
                pygame.draw.rect(surface, cor_escura,
                                (tela_x, tela_y, tamanho + mod_tamanho, tamanho + mod_tamanho), 0, 3)

                # Quadrado exterior (cor principal)
                pygame.draw.rect(surface, cor,
                                (tela_x + 1, tela_y + 1, tamanho + mod_tamanho - 2, tamanho + mod_tamanho - 2), 0, 2)

                # Brilho no canto
                pygame.draw.rect(surface, cor_brilhante,
                                (tela_x + 2, tela_y + 2, 3, 3), 0, 1)

                # Barra de vida
                vida_largura = tamanho + 4
                altura_barra = 3
                pygame.draw.rect(surface, (40, 40, 40),
                                (tela_x - 2, tela_y - 8, vida_largura, altura_barra), 0, 1)
                vida_atual = int((bot.vidas / bot.vidas_max) * vida_largura)
                if vida_atual > 0:
                    pygame.draw.rect(surface, cor,
                                    (tela_x - 2, tela_y - 8, vida_atual, altura_barra), 0, 1)

                # Nome acima do bot (fonte menor)
                nome_surface = self.fonte_pequena.render(bot.nome, True, (200, 200, 200))
                nome_surface = pygame.transform.scale(nome_surface,
                    (nome_surface.get_width() // 2, nome_surface.get_height() // 2))
                nome_rect = nome_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 14))
                surface.blit(nome_surface, nome_rect)

    def _desenhar_info_multiplayer(self):
        """Desenha informações específicas do multiplayer no HUD."""
        # Latência
        latencia = self.cliente.get_latency() if hasattr(self.cliente, 'get_latency') else 0
        cor_latencia = VERDE if latencia < 50 else (AMARELO if latencia < 100 else VERMELHO)
        texto_latencia = self.fonte_pequena.render(f"Ping: {latencia:.0f}ms", True, cor_latencia)
        self.tela.blit(texto_latencia, (LARGURA - 150, ALTURA_JOGO + 10))

        # Contar membros vivos de cada time
        time_t_vivos = 0
        time_q_vivos = 0

        # Jogador local
        if self.jogador.vidas > 0:
            if self.time_jogador == 'T':
                time_t_vivos += 1
            else:
                time_q_vivos += 1

        # Bots
        for bot in self.bots_locais:
            if bot.vidas > 0:
                bot_time = getattr(bot, 'time', None)
                if bot_time == 'T':
                    time_t_vivos += 1
                elif bot_time == 'Q':
                    time_q_vivos += 1

        # Mostrar contagem por time
        texto_time_t = self.fonte_pequena.render(f"Time T: {time_t_vivos}", True, self.COR_TIME_T)
        texto_time_q = self.fonte_pequena.render(f"Time Q: {time_q_vivos}", True, self.COR_TIME_Q)
        self.tela.blit(texto_time_t, (LARGURA - 150, ALTURA_JOGO + 35))
        self.tela.blit(texto_time_q, (LARGURA - 150, ALTURA_JOGO + 55))

        # Mostrar time do jogador
        cor_time = self.COR_TIME_T if self.time_jogador == 'T' else self.COR_TIME_Q
        texto_meu_time = self.fonte_pequena.render(f"Seu time: {self.time_jogador}", True, cor_time)
        self.tela.blit(texto_meu_time, (10, ALTURA_JOGO + 35))

    def _mostrar_introducao_multiplayer(self, tempo_atual):
        """Mostra a tela de introdução do multiplayer."""
        import math
        from src.utils.visual import desenhar_texto, desenhar_estrelas

        self.contador_inicio -= 1
        if self.contador_inicio <= 0:
            self.mostrando_inicio = False

        self.tela.fill((0, 0, 0))
        self.tela.blit(self.gradiente_jogo, (0, 0))

        # Desenhar estrelas
        desenhar_estrelas(self.tela, self.estrelas)

        # Texto de introdução com efeito
        tamanho = 70 + int(math.sin(tempo_atual / 200) * 5)
        desenhar_texto(self.tela, "MODO MULTIPLAYER", tamanho, BRANCO, LARGURA // 2, ALTURA_JOGO // 3)

        num_jogadores = len(self.jogadores_remotos) + 1
        desenhar_texto(self.tela, f"{num_jogadores} jogador{'es' if num_jogadores > 1 else ''} conectado{'s' if num_jogadores > 1 else ''}",
                      36, AMARELO, LARGURA // 2, ALTURA_JOGO // 2)
        desenhar_texto(self.tela, "Preparado?", 30, BRANCO, LARGURA // 2, ALTURA_JOGO * 2 // 3)

        present_frame()
        self.relogio.tick(60)

    def _mostrar_pausa_multiplayer(self):
        """Mostra a tela de pausa do multiplayer com botões."""
        from src.utils.visual import desenhar_texto
        from src.utils.display_manager import convert_mouse_position

        # Botões
        btn_continuar = pygame.Rect(LARGURA // 2 - 150, ALTURA // 2 + 20, 300, 60)
        btn_sair = pygame.Rect(LARGURA // 2 - 150, ALTURA // 2 + 100, 300, 60)

        while self.pausado:
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    mouse_click_pos = convert_mouse_position(evento.pos)

                    # Botão Continuar
                    if btn_continuar.collidepoint(mouse_click_pos):
                        self.pausado = False
                        return

                    # Botão Sair
                    if btn_sair.collidepoint(mouse_click_pos):
                        return  # Sair da fase

            # Desenhar com overlay escuro
            overlay = pygame.Surface((LARGURA, ALTURA))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.tela.blit(overlay, (0, 0))

            desenhar_texto(self.tela, "PAUSADO", 72, BRANCO, LARGURA // 2, ALTURA // 2 - 80)

            # Botão Continuar
            hover_continuar = btn_continuar.collidepoint(mouse_pos)
            cor_continuar = (60, 200, 60) if hover_continuar else (40, 150, 40)
            pygame.draw.rect(self.tela, cor_continuar, btn_continuar, 0, 15)
            pygame.draw.rect(self.tela, BRANCO, btn_continuar, 3, 15)
            texto_continuar = self.fonte_normal.render("CONTINUAR", True, BRANCO)
            self.tela.blit(texto_continuar, (btn_continuar.centerx - texto_continuar.get_width() // 2,
                                            btn_continuar.centery - texto_continuar.get_height() // 2))

            # Botão Sair
            hover_sair = btn_sair.collidepoint(mouse_pos)
            cor_sair = (200, 60, 60) if hover_sair else (150, 40, 40)
            pygame.draw.rect(self.tela, cor_sair, btn_sair, 0, 15)
            pygame.draw.rect(self.tela, BRANCO, btn_sair, 3, 15)
            texto_sair = self.fonte_normal.render("SAIR", True, BRANCO)
            self.tela.blit(texto_sair, (btn_sair.centerx - texto_sair.get_width() // 2,
                                       btn_sair.centery - texto_sair.get_height() // 2))

            present_frame()
            self.relogio.tick(60)


def jogar_fase_multiplayer(tela, relogio, gradiente_jogo, fonte_titulo, fonte_normal, cliente, nome_jogador, customizacao=None):
    """
    Função wrapper para iniciar a fase multiplayer.
    Mantém compatibilidade com o código existente.

    Args:
        customizacao: Dict com 'cor' e 'bots' para customizar o personagem e adicionar bots

    Returns:
        "menu" para voltar ao menu
    """
    print(f"[MULTIPLAYER] Criando fase multiplayer...")

    # Extrair bots da customização
    bots = customizacao.get('bots', []) if customizacao else []

    fase = FaseMultiplayer(
        tela=tela,
        relogio=relogio,
        gradiente_jogo=gradiente_jogo,
        fonte_titulo=fonte_titulo,
        fonte_normal=fonte_normal,
        cliente=cliente,
        nome_jogador=nome_jogador,
        bots=bots
    )

    # Aplicar customização se fornecida
    if customizacao and 'cor' in customizacao:
        fase.jogador.atualizar_cor(customizacao['cor'])
        print(f"[MULTIPLAYER] Cor do jogador aplicada: {customizacao.get('cor_nome', 'Custom')}")

    resultado = fase.executar()
    return resultado
