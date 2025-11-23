#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase Multiplayer - Herda de FaseBase para reaproveitar todo o código do jogo.
Adiciona apenas funcionalidade de rede e sincronização entre jogadores.
"""

import pygame
import random
from src.config import *
from src.game.fase_base import FaseBase
from src.utils.display_manager import present_frame
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.entities.item_drop import ItemDrop, spawnar_item_aleatorio
from src.game.inventario import InventarioManager


class FaseMultiplayer(FaseBase):
    """
    Classe para fase multiplayer.
    Herda toda a lógica de jogo de FaseBase e adiciona sincronização de rede.
    """

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

        # Sistema de drops de itens (Battle Royale)
        self.itens_no_chao = []
        self.tempo_ultimo_drop = pygame.time.get_ticks()
        self.intervalo_drop = 5000  # Spawn a cada 5 segundos

        # Sistema de vitória
        self.jogo_terminado = False
        self.vencedor = None

        # Criar bots locais
        self.bots_locais = []
        if bots:
            print(f"[MULTIPLAYER] Criando {len(bots)} bots...")
            for bot_info in bots:
                bot = self._criar_bot(bot_info)
                self.bots_locais.append(bot)
                print(f"[MULTIPLAYER] Bot criado: {bot.nome}")

        print(f"[MULTIPLAYER] Fase inicializada. ID local: {cliente.local_player_id}")
        print(f"[MULTIPLAYER] Modo: VERSUS - Battle Royale - {len(self.bots_locais)} bots")

    def executar(self):
        """
        Loop principal da fase multiplayer.
        Retorna: "menu" para voltar ao menu
        """
        rodando = True

        while rodando:
            tempo_atual = self.obter_tempo_atual()
            pos_mouse = self.obter_pos_mouse()

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

            # Atualizar jogador localmente (predição)
            self.atualizar_jogador(pos_mouse, tempo_atual)

            # Enviar estado do jogador para o servidor
            self._enviar_estado_jogador(pos_mouse)

            # Receber estados de outros jogadores
            self._receber_estados_remotos()

            # Atualizar moedas (usa sistema existente)
            self.atualizar_moedas()

            # Atualizar tiros (usa sistema existente)
            # No multiplayer, não há inimigos, então passamos lista vazia ou jogadores remotos
            self.atualizar_tiros_jogador([])
            self.atualizar_tiros_inimigo()

            # Processar sabre de luz (usa sistema existente)
            self.processar_sabre_luz([])

            # Processar granadas (usa sistema existente)
            self.processar_granadas([])

            # Atualizar efeitos visuais (usa sistema existente)
            self.atualizar_efeitos_visuais()

            # Atualizar bots
            self._atualizar_bots()

            # Atualizar sistema de drops
            self._atualizar_drops(tempo_atual)

            # Verificar colisão com itens no chão
            self._processar_coleta_itens()

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

    def _criar_bot(self, bot_info):
        """Cria um bot local (IA simples)."""
        import random

        # Posição aleatória na arena
        x = random.randint(100, LARGURA - 100)
        y = random.randint(100, ALTURA_JOGO - 100)

        # Criar entidade do bot
        bot = Quadrado(x, y, TAMANHO_QUADRADO, bot_info['cor'], VELOCIDADE_JOGADOR * 0.7)
        bot.nome = bot_info['nome']
        bot.vidas = 5
        bot.vidas_max = 5

        # IA do bot
        bot.is_bot = True
        bot.alvo_x = x
        bot.alvo_y = y
        bot.tempo_ultimo_tiro = 0
        bot.tempo_mudar_alvo = pygame.time.get_ticks()

        return bot

    def _atualizar_bots(self):
        """Atualiza IA dos bots."""
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
                bot.alvo_x = random.randint(100, LARGURA - 100)
                bot.alvo_y = random.randint(100, ALTURA_JOGO - 100)
                bot.tempo_mudar_alvo = tempo_atual

            # Mover em direção ao alvo
            dx = bot.alvo_x - bot.x
            dy = bot.alvo_y - bot.y
            distancia = math.sqrt(dx**2 + dy**2)

            if distancia > 5:
                bot.x += (dx / distancia) * bot.velocidade
                bot.y += (dy / distancia) * bot.velocidade

            # Atirar no jogador se estiver próximo
            dx_jogador = self.jogador.x - bot.x
            dy_jogador = self.jogador.y - bot.y
            dist_jogador = math.sqrt(dx_jogador**2 + dy_jogador**2)

            if dist_jogador < 300 and tempo_atual - bot.tempo_ultimo_tiro > 800:  # Atirar a cada 800ms
                # Criar tiro do bot
                angulo = math.atan2(dy_jogador, dx_jogador)
                tiro_dx = math.cos(angulo)
                tiro_dy = math.sin(angulo)

                from src.entities.tiro import Tiro
                tiro = Tiro(bot.x, bot.y, tiro_dx, tiro_dy, bot.cor, 7)
                self.tiros_inimigo.append(tiro)
                bot.tempo_ultimo_tiro = tempo_atual

    def _atualizar_drops(self, tempo_atual):
        """Spawna novos itens e atualiza os existentes."""
        # Spawnar novo item a cada intervalo
        if tempo_atual - self.tempo_ultimo_drop > self.intervalo_drop:
            novo_item = spawnar_item_aleatorio(LARGURA, ALTURA_JOGO)
            self.itens_no_chao.append(novo_item)
            self.tempo_ultimo_drop = tempo_atual

        # Atualizar animação de todos os itens
        for item in self.itens_no_chao:
            item.atualizar()

    def _processar_coleta_itens(self):
        """Verifica se o jogador coletou algum item."""
        inventario = InventarioManager()

        for item in self.itens_no_chao[:]:
            if item.colidiu_com(self.jogador):
                # Coletar item baseado no tipo
                if item.tipo == 'arma':
                    self._equipar_arma(item.subtipo)
                    print(f"[ITEM] Coletado: {item.subtipo}")
                elif item.tipo == 'item':
                    self._coletar_item(item.subtipo)
                    print(f"[ITEM] Coletado: {item.subtipo}")

                # Remover do chão
                self.itens_no_chao.remove(item)

    def _equipar_arma(self, nome_arma):
        """Equipa uma arma no jogador."""
        if nome_arma == 'espingarda':
            self.jogador.espingarda_ativa = True
            self.jogador.tiros_espingarda = 20
        elif nome_arma == 'metralhadora':
            self.jogador.metralhadora_ativa = True
            self.jogador.tiros_metralhadora = 100
        elif nome_arma == 'desert_eagle':
            self.jogador.desert_eagle_ativa = True
            self.jogador.tiros_desert_eagle = 15

    def _coletar_item(self, nome_item):
        """Coleta um item consumível."""
        if nome_item == 'granada':
            # Adicionar granadas ao jogador
            self.jogador.granadas = min(self.jogador.granadas + 3, 10)
            print(f"[GRANADA] +3 granadas! Total: {self.jogador.granadas}")
        elif nome_item == 'vida':
            # Curar o jogador
            self.jogador.vidas = min(self.jogador.vidas + 2, self.jogador.vidas_max)
            print(f"[VIDA] Curado! Vida atual: {self.jogador.vidas}")
        elif nome_item == 'sabre':
            # Adicionar usos de sabre
            self.jogador.sabre_uses = min(self.jogador.sabre_uses + 5, 20)
            self.jogador.sabre_equipado = True
            print(f"[SABRE] +5 usos! Total: {self.jogador.sabre_uses}")

    def _processar_pvp(self):
        """Processa colisões de tiros com jogadores (PvP)."""
        # Tiros do jogador local atingindo jogadores remotos
        for tiro in self.tiros_jogador[:]:
            # Verificar colisão com jogadores remotos
            for player_id, jogador_remoto in self.jogadores_remotos.items():
                jogador_rect = pygame.Rect(
                    jogador_remoto.x - TAMANHO_QUADRADO // 2,
                    jogador_remoto.y - TAMANHO_QUADRADO // 2,
                    TAMANHO_QUADRADO,
                    TAMANHO_QUADRADO
                )

                if tiro.rect.colliderect(jogador_rect):
                    criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                    self.tiros_jogador.remove(tiro)
                    dano = getattr(tiro, 'dano', 1)
                    jogador_remoto.vida = max(0, jogador_remoto.vida - dano)
                    print(f"[PVP] Acertou {jogador_remoto.nome}! Vida restante: {jogador_remoto.vida}")
                    break

            # Verificar colisão com bots
            for bot in self.bots_locais:
                bot_rect = pygame.Rect(
                    bot.x - TAMANHO_QUADRADO // 2,
                    bot.y - TAMANHO_QUADRADO // 2,
                    TAMANHO_QUADRADO,
                    TAMANHO_QUADRADO
                )

                if tiro.rect.colliderect(bot_rect):
                    criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                    if tiro in self.tiros_jogador:
                        self.tiros_jogador.remove(tiro)
                    dano = getattr(tiro, 'dano', 1)
                    bot.vidas = max(0, bot.vidas - dano)
                    print(f"[PVP] Acertou {bot.nome}! Vida restante: {bot.vidas}")
                    break

        # Tiros de bots atingindo jogador
        for tiro in self.tiros_inimigo[:]:
            jogador_rect = pygame.Rect(
                self.jogador.x - TAMANHO_QUADRADO // 2,
                self.jogador.y - TAMANHO_QUADRADO // 2,
                TAMANHO_QUADRADO,
                TAMANHO_QUADRADO
            )

            if tiro.rect.colliderect(jogador_rect):
                criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                self.tiros_inimigo.remove(tiro)
                dano = getattr(tiro, 'dano', 1)
                self.jogador.vidas = max(0, self.jogador.vidas - dano)
                print(f"[PVP] Bot acertou você! Vida restante: {self.jogador.vidas}")

    def _verificar_vitoria(self):
        """Verifica se há um vencedor (último sobrevivente)."""
        if self.jogo_terminado:
            return

        # Contar jogadores vivos
        jogadores_vivos = []

        # Jogador local
        if self.jogador.vidas > 0:
            jogadores_vivos.append(('local', self.nome_jogador))

        # Jogadores remotos
        for player_id, jogador_remoto in self.jogadores_remotos.items():
            if jogador_remoto.vida > 0 and getattr(jogador_remoto, 'vivo', True):
                jogadores_vivos.append((player_id, jogador_remoto.nome))

        # Bots
        for bot in self.bots_locais:
            if bot.vidas > 0:
                jogadores_vivos.append(('bot', bot.nome))

        # Se só sobrou 1, temos um vencedor!
        if len(jogadores_vivos) == 1:
            self.jogo_terminado = True
            self.vencedor = jogadores_vivos[0][1]
            print(f"[VITORIA] {self.vencedor} venceu a partida!")

    def _desenhar_tudo(self, tempo_atual, pos_mouse):
        """Desenha todos os elementos do jogo."""
        # Fundo (usa método da FaseBase)
        self.renderizar_fundo()

        # Desenhar objetos do jogo (jogador, tiros, granadas, partículas)
        # No multiplayer, passamos lista vazia de alvos (sem inimigos)
        self.renderizar_objetos_jogo(tempo_atual, [])

        # Desenhar itens no chão
        for item in self.itens_no_chao:
            item.desenhar(self.tela)

        # Desenhar jogadores remotos
        self._desenhar_jogadores_remotos()

        # Desenhar bots
        self._desenhar_bots()

        # Desenhar mira (usa método da FaseBase)
        self.renderizar_mira(pos_mouse)

        # Desenhar HUD (usa método da FaseBase)
        # No multiplayer, passamos lista vazia de alvos
        self.renderizar_hud(tempo_atual, [])

        # Desenhar informações multiplayer
        self._desenhar_info_multiplayer()

        # Tela de vitória se o jogo acabou
        if self.jogo_terminado:
            self._desenhar_tela_vitoria()

    def _desenhar_tela_vitoria(self):
        """Desenha a tela de vitória com o vencedor."""
        from src.utils.visual import desenhar_texto

        # Overlay escuro
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.tela.blit(overlay, (0, 0))

        # Texto de vitória
        if self.vencedor == self.nome_jogador:
            desenhar_texto(self.tela, "VITORIA!", 90, VERDE, LARGURA // 2, ALTURA // 2 - 100)
            desenhar_texto(self.tela, "Voce venceu a partida!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 20)
        else:
            desenhar_texto(self.tela, "DERROTA", 90, VERMELHO, LARGURA // 2, ALTURA // 2 - 100)
            desenhar_texto(self.tela, f"{self.vencedor} venceu!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 20)

        desenhar_texto(self.tela, "Pressione ESC para sair", 24, BRANCO, LARGURA // 2, ALTURA // 2 + 60)

    def _desenhar_jogadores_remotos(self):
        """Desenha todos os jogadores remotos."""
        for player_id, jogador_remoto in self.jogadores_remotos.items():
            # Só desenhar se estiver vivo
            if not getattr(jogador_remoto, 'vivo', True):
                continue

            # Criar um objeto temporário Quadrado para reaproveitar o desenho
            quadrado_temp = Quadrado(
                jogador_remoto.x,
                jogador_remoto.y,
                TAMANHO_QUADRADO,
                jogador_remoto.cor,
                VELOCIDADE_JOGADOR
            )
            quadrado_temp.vidas = jogador_remoto.vida
            quadrado_temp.vidas_max = 5

            # Desenhar o quadrado (reusa o método de desenho do Quadrado)
            quadrado_temp.desenhar(self.tela)

            # Nome acima do jogador
            nome_surface = self.fonte_pequena.render(jogador_remoto.nome, True, BRANCO)
            nome_rect = nome_surface.get_rect(center=(jogador_remoto.x, jogador_remoto.y - 35))
            self.tela.blit(nome_surface, nome_rect)

    def _desenhar_bots(self):
        """Desenha todos os bots."""
        for bot in self.bots_locais:
            # Desenhar o bot
            bot.desenhar(self.tela)

            # Nome acima do bot
            nome_surface = self.fonte_pequena.render(bot.nome, True, (200, 200, 200))
            nome_rect = nome_surface.get_rect(center=(bot.x, bot.y - 35))
            self.tela.blit(nome_surface, nome_rect)

    def _desenhar_info_multiplayer(self):
        """Desenha informações específicas do multiplayer no HUD."""
        # Latência
        latencia = self.cliente.get_latency() if hasattr(self.cliente, 'get_latency') else 0
        cor_latencia = VERDE if latencia < 50 else (AMARELO if latencia < 100 else VERMELHO)
        texto_latencia = self.fonte_pequena.render(f"Ping: {latencia:.0f}ms", True, cor_latencia)
        self.tela.blit(texto_latencia, (LARGURA - 150, ALTURA_JOGO + 10))

        # Número de jogadores (incluindo bots vivos)
        num_jogadores = len(self.jogadores_remotos) + 1 + len([b for b in self.bots_locais if b.vidas > 0])
        texto_jogadores = self.fonte_pequena.render(f"Vivos: {num_jogadores}", True, BRANCO)
        self.tela.blit(texto_jogadores, (LARGURA - 150, ALTURA_JOGO + 35))

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
