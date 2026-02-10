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
from src.game.selecao_times import SelecaoTimes, TelaAguardandoJogadores
from src.entities.quadrado import Quadrado
from src.entities.particula import criar_explosao
from src.utils.tilemap import TileMap

# Importar funções de desenho das armas
from src.weapons.desert_eagle import desenhar_desert_eagle
from src.weapons.spas12 import desenhar_spas12
from src.weapons.metralhadora import desenhar_metralhadora
from src.weapons.sniper import desenhar_sniper


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
        # Guardar referências antes de chamar super().__init__
        self.tela = tela
        self.relogio = relogio
        self.gradiente_jogo = gradiente_jogo
        self.fonte_titulo = fonte_titulo
        self.fonte_normal = fonte_normal
        self.cliente = cliente
        self.nome_jogador = nome_jogador
        self.bots_info = bots or []

        # Sistema de times - seleção acontece ANTES de carregar o resto
        self.time_jogador = None  # 'T' ou 'Q'
        self.selecionando_time = True  # Flag para mostrar tela de seleção
        self.aguardando_jogadores = False  # Flag para aguardar outros jogadores
        self.todos_prontos = False  # Flag quando todos escolheram time
        self.mapa_carregado = False  # Flag para saber se já carregou o mapa

        # Sistema de classes (apenas para Time Q)
        self.classe_jogador = None  # "cyan", "explosive", "normal", "purple"
        self.selecionando_classe = False  # Flag para mostrar tela de seleção de classe

        # Habilidades de classe
        self.habilidade_cooldown = 0  # Tempo do último uso da habilidade
        self.habilidade_ativa = False  # Se a habilidade está ativa
        self.habilidade_tempo_inicio = 0  # Quando a habilidade foi ativada
        self.velocidade_original = 0  # Velocidade original (para restaurar após turbo)

        # === DEV MODE - Sistema de desenho de rotas ===
        self.dev_mode = False  # Ativado quando entra no modo desenvolvedor
        self.dev_rotas_t = []  # Rotas do Time T: [[(x1,y1), (x2,y2), ...], ...]
        self.dev_rotas_q = []  # Rotas do Time Q: [[(x1,y1), (x2,y2), ...], ...]
        self.dev_rotas = []  # Compatibilidade (será preenchido com rotas do time atual)
        self.dev_rota_atual = []  # Rota sendo desenhada atualmente
        self.dev_time_selecionado = 'T'  # Time atual para desenho ('T' ou 'Q')
        self.dev_arquivo_rotas = "rotas_bots.json"  # Arquivo para salvar rotas

        # Status de times de outros jogadores
        self.status_times = {}  # {player_id: {'team': 'T'/'Q', 'name': 'nome'}}

        # Cores para jogadores remotos
        self.cores_remotos = [CIANO, ROXO, LARANJA, AMARELO]
        self.proximo_cor_index = 0

        # Sistema de vitória
        self.jogo_terminado = False
        self.vencedor = None

        # Bots serão criados após seleção de time
        self.bots_locais = []

        # Jogadores remotos
        self.jogadores_remotos = {}

        # Configurar callbacks para seleção de times
        self._configurar_callbacks_time()

        print(f"[MULTIPLAYER] Fase criada. Aguardando seleção de time...")
        print(f"[MULTIPLAYER] ID local: {cliente.local_player_id}")

    def _configurar_callbacks_time(self):
        """Configura os callbacks para sincronização de seleção de times."""
        def on_team_status(status):
            self.status_times = status
            print(f"[MULTIPLAYER] Status de times atualizado: {status}")

        def on_all_ready(data):
            self.todos_prontos = True
            print("[MULTIPLAYER] Todos os jogadores escolheram time!")

        self.cliente.set_callback('on_team_status', on_team_status)
        self.cliente.set_callback('on_all_ready', on_all_ready)

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
                    # Tecla B para abrir/fechar menu de compra (só no tempo de compra)
                    elif evento.key == pygame.K_b:
                        if self.em_tempo_compra:
                            self.menu_compra_aberto = not self.menu_compra_aberto
                            pygame.mouse.set_visible(self.menu_compra_aberto)
                    # Tecla ESPAÇO para habilidade de classe (ambos os times)
                    elif evento.key == pygame.K_SPACE:
                        if self.classe_jogador:
                            self._usar_habilidade_classe()
                    # Tecla Q para selecionar granada (qualquer jogador com granadas)
                    elif evento.key == pygame.K_q:
                        if hasattr(self.jogador, 'granadas') and self.jogador.granadas > 0:
                            self.jogador.granada_selecionada = True
                            print(f"[GRANADA] Granada selecionada! ({self.jogador.granadas} disponíveis)")
                        else:
                            print("[GRANADA] Sem granadas!")
                    # Tecla E para voltar à arma (desselecionar granada)
                    elif evento.key == pygame.K_e:
                        if hasattr(self.jogador, 'granada_selecionada') and self.jogador.granada_selecionada:
                            self.jogador.granada_selecionada = False
                            print("[GRANADA] Arma equipada!")

                # Clique do mouse para alternar espectador quando morto
                if evento.type == pygame.MOUSEBUTTONDOWN and self.jogador.vidas <= 0:
                    if hasattr(self, 'espectador_ativo') and self.espectador_ativo:
                        self._alternar_espectador()
                        continue  # Não processa como tiro

                # Tiro com clique do mouse - usa posição do mundo (não atira se menu aberto)
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if not self.menu_compra_aberto:
                        # Se granada selecionada, lança granada
                        if hasattr(self.jogador, 'granada_selecionada') and self.jogador.granada_selecionada:
                            if hasattr(self.jogador, 'granadas') and self.jogador.granadas > 0:
                                self._lancar_granada_comprada(pos_mouse_mundo)
                            else:
                                self.jogador.granada_selecionada = False
                        else:
                            self._atirar_multiplayer(pos_mouse_mundo)

            # Controles durante pausa
            elif self.pausado:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    self.pausado = False
                    pygame.mouse.set_visible(False)

        return None

    def _atirar_multiplayer(self, pos_mouse_mundo):
        """Processa tiro no multiplayer usando coordenadas do mundo e arma equipada."""
        import math
        from src.entities.tiro import Tiro
        from src.utils.sound import gerar_som_tiro

        if self.jogador.vidas <= 0:
            return

        # Ghost não pode atirar enquanto invisível
        if hasattr(self.jogador, 'invisivel') and self.jogador.invisivel:
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

        # Obter propriedades da arma equipada
        if self.arma_equipada and self.arma_equipada in self.armas_disponiveis:
            arma = self.armas_disponiveis[self.arma_equipada]
            dano = arma['dano']
            velocidade = arma['velocidade']
        else:
            # Pistola padrão
            dano = 1
            velocidade = 8

        # Verificar cooldown baseado na arma
        tempo_atual = pygame.time.get_ticks()
        cooldown = self._obter_cooldown_arma()
        if tempo_atual - self.jogador.tempo_ultimo_tiro < cooldown:
            return
        self.jogador.tempo_ultimo_tiro = tempo_atual

        # Criar tiros baseado na arma
        if self.arma_equipada == 'spas12':
            # SPAS-12: múltiplos tiros em dispersão
            angulo_base = math.atan2(dy, dx)
            dispersao = 0.25
            num_tiros = 5
            for i in range(num_tiros):
                angulo_variacao = dispersao * (i / (num_tiros - 1) - 0.5) * 2
                angulo_atual = angulo_base + angulo_variacao
                tiro_dx = math.cos(angulo_atual)
                tiro_dy = math.sin(angulo_atual)
                tiro = Tiro(centro_x, centro_y, tiro_dx, tiro_dy, self.jogador.cor, velocidade)
                tiro.dano = dano
                tiro.time_origem = self.time_jogador
                self.tiros_jogador.append(tiro)
        elif self.arma_equipada == 'metralhadora':
            # Metralhadora: tiro com pequena imprecisão
            import random
            imprecisao = 0.08
            dx += random.uniform(-imprecisao, imprecisao)
            dy += random.uniform(-imprecisao, imprecisao)
            dist_nova = math.sqrt(dx * dx + dy * dy)
            if dist_nova > 0:
                dx /= dist_nova
                dy /= dist_nova
            tiro = Tiro(centro_x, centro_y, dx, dy, self.jogador.cor, velocidade)
            # Classe Metralhadora: dano dobrado (2 ao invés de 1)
            if self.classe_jogador == 'metralhadora':
                tiro.dano = 2
            else:
                tiro.dano = dano
            tiro.time_origem = self.time_jogador
            self.tiros_jogador.append(tiro)
        else:
            # Pistola padrão, Desert Eagle ou Sniper
            tiro = Tiro(centro_x, centro_y, dx, dy, self.jogador.cor, velocidade)
            tiro.dano = dano
            tiro.time_origem = self.time_jogador
            self.tiros_jogador.append(tiro)

        # Som de tiro
        pygame.mixer.Channel(1).play(pygame.mixer.Sound(gerar_som_tiro()))

    def _obter_cooldown_arma(self):
        """Retorna o cooldown da arma equipada em milissegundos."""
        cooldowns = {
            'desert_eagle': 700,   # Cadência lenta (arma poderosa)
            'spas12': 600,         # Cadência média
            'metralhadora': 200,   # Cadência muito alta (automática)
            'sniper': 1500         # Cadência baixa
        }
        if self.arma_equipada and self.arma_equipada in cooldowns:
            return cooldowns[self.arma_equipada]
        return 500  # Tiro normal (sem arma) - cadência lenta

    def executar(self):
        """
        Loop principal da fase multiplayer.
        Retorna: "menu" para voltar ao menu
        """
        rodando = True

        while rodando:
            # Tela de seleção de time (ANTES de carregar o jogo)
            if self.selecionando_time:
                resultado = self._mostrar_selecao_time()
                if resultado == "menu":
                    return "menu"
                continue

            # Tela de seleção de classe (para Time Q)
            if self.selecionando_classe:
                resultado = self._mostrar_selecao_classe()
                if resultado == "menu":
                    return "menu"
                continue

            # A partir daqui, o jogo já foi carregado
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

            # Atualizar tempo de compra
            self._atualizar_tempo_compra()

            # Menu de compra aberto
            if self.menu_compra_aberto:
                # Desenhar jogo no fundo
                self._desenhar_tudo(tempo_atual, pos_mouse)
                # Mostrar menu por cima
                resultado_menu = self._mostrar_menu_compra()
                if resultado_menu == "sair":
                    self.limpar()
                    return "menu"
                present_frame()
                self.relogio.tick(60)
                continue

            # Verificar se deve iniciar próximo round (antes de tudo)
            self._verificar_proximo_round()

            # Se round terminou, só atualizar câmera e efeitos visuais
            if self.round_terminado and not self.partida_terminada:
                self._atualizar_camera()
                self.atualizar_efeitos_visuais()
            else:
                # Atualizar jogador localmente (predição) com colisões do mapa
                self._atualizar_jogador_com_colisao(pos_mouse, tempo_atual)

                # === METRALHADORA AUTOMÁTICA - Segurar mouse para atirar ===
                if self.arma_equipada == 'metralhadora' and not self.menu_compra_aberto:
                    mouse_buttons = pygame.mouse.get_pressed()
                    if mouse_buttons[0]:  # Botão esquerdo pressionado
                        # Converter pos_mouse para coordenadas do mundo
                        pos_mouse_mundo = (
                            pos_mouse[0] / self.camera_zoom + self.camera_x,
                            pos_mouse[1] / self.camera_zoom + self.camera_y
                        )
                        self._atirar_multiplayer(pos_mouse_mundo)

                # Atualizar habilidade de classe (ambos os times)
                if self.classe_jogador:
                    self._atualizar_habilidade_classe(tempo_atual)

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

                # Processar granadas ativas (com colisão de paredes)
                self._atualizar_granadas_ativas()

                # Atualizar efeitos visuais (usa sistema existente)
                self.atualizar_efeitos_visuais()

                # Atualizar bots com colisões
                self._atualizar_bots()

                # Atualizar habilidades de classe dos bots
                tempo_atual = pygame.time.get_ticks()
                self._atualizar_habilidades_bots(tempo_atual)

                # Processar colisões de tiros com jogadores (PvP)
                self._processar_pvp()

                # Processar sistema de bomba
                self._processar_bomba(tempo_atual)

                # Verificar se alguém pegou a bomba dropada
                self._verificar_pickup_bomba()

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
        """Mostra a tela de seleção de time (T ou Q) - ANTES de carregar o jogo."""
        pygame.mouse.set_visible(True)

        # Verificar se todos estão prontos
        if self.todos_prontos:
            self.selecionando_time = False
            print("[MULTIPLAYER] Todos prontos! Carregando jogo...")
            self._carregar_jogo()
            return None

        # Se já escolheu, mostrar tela de aguardar
        if self.aguardando_jogadores:
            return self._mostrar_aguardando_jogadores()

        # Usar a nova tela de seleção de times
        if not hasattr(self, '_selecao_times_tela'):
            self._selecao_times_tela = SelecaoTimes(
                self.tela, self.relogio, self.fonte_titulo, self.fonte_normal,
                self.gradiente_jogo, self.cliente
            )

        resultado = self._selecao_times_tela.executar()

        if resultado is None:
            return "menu"
        elif resultado == 'T':
            self._selecionar_time('T')
            del self._selecao_times_tela  # Limpar para próxima vez
            return None
        elif resultado == 'Q':
            self._selecionar_time('Q')
            del self._selecao_times_tela
            return None
        elif resultado == 'dev':
            self._entrar_dev_mode()
            del self._selecao_times_tela
            return None

        return None

    def _mostrar_aguardando_jogadores(self):
        """Mostra tela de aguardar outros jogadores escolherem time."""
        # Usar a nova tela de aguardar
        if not hasattr(self, '_aguardando_tela'):
            self._aguardando_tela = TelaAguardandoJogadores(
                self.tela, self.relogio, self.fonte_titulo, self.fonte_normal,
                self.time_jogador, self.cliente
            )

        resultado = self._aguardando_tela.executar()

        if resultado is False:
            # Cancelou
            del self._aguardando_tela
            return "menu"

        return None

    def _selecionar_time(self, time):
        """Seleciona um time e envia para o servidor."""
        self.time_jogador = time

        # Ambos os times têm seleção de classe
        self.selecionando_time = False  # Sair da tela de seleção de time
        self.selecionando_classe = True  # Ir para seleção de classe
        print(f"[MULTIPLAYER] Time {time} selecionado! Escolha sua classe...")

    def _finalizar_selecao_classe(self, classe_id):
        """Finaliza a seleção de classe e continua para aguardar jogadores."""
        self.classe_jogador = classe_id
        self.selecionando_classe = False
        self.selecionando_time = True  # Voltar para tela de seleção (mostra "aguardando")
        self.aguardando_jogadores = True

        # Enviar seleção para o servidor
        self.cliente.send_team_selection(self.time_jogador, self.nome_jogador)

        print(f"[MULTIPLAYER] Classe '{classe_id}' selecionada! Aguardando outros jogadores...")

    def _mostrar_selecao_classe(self):
        """Mostra a tela de seleção de classe para o time selecionado."""
        from src.game.selecao_classes import SelecaoClasses

        # Passar o time para mostrar as classes corretas
        selecao = SelecaoClasses(self.tela, self.relogio, self.fonte_titulo, self.fonte_normal, self.time_jogador)
        classe_escolhida = selecao.executar()

        if classe_escolhida is None:
            # Cancelou - voltar para seleção de time
            self.selecionando_classe = False
            self.selecionando_time = True
            self.time_jogador = None
            return None

        # Classe selecionada!
        self._finalizar_selecao_classe(classe_escolhida)
        return None

    def _aplicar_classe_jogador(self):
        """Aplica os efeitos da classe selecionada ao jogador."""
        from src.game.selecao_classes import obter_dados_classe

        # Obter dados da classe (passar o time)
        dados = obter_dados_classe(self.classe_jogador, self.time_jogador)

        if dados:
            # Aplicar cor
            self.jogador.atualizar_cor(dados["cor"])

            # Aplicar vidas
            self.jogador.vidas = dados["vidas"]
            self.jogador.vidas_max = dados["vidas"]

            # Salvar velocidade original
            self.velocidade_original = self.jogador.velocidade

            # Aplicar modificador de velocidade base
            if "velocidade_base" in dados and dados["velocidade_base"] != 1.0:
                self.jogador.velocidade *= dados["velocidade_base"]

            # Resetar invulnerabilidade para garantir que o jogador não fique permanentemente invulnerável
            self.jogador.invulneravel = False

            # Inicializar atributos específicos de cada classe
            if self.classe_jogador == "normal":
                self.jogador.dash_ativo = False
                self.jogador.dash_frames_restantes = 0
                self.jogador.dash_direcao = (0, 0)
                self.jogador.dash_velocidade = dados.get("dash_velocidade", 25)
            elif self.classe_jogador == "mago":
                self.jogador.escudo_ativo = False
            elif self.classe_jogador == "ghost":
                self.jogador.invisivel = False
            elif self.classe_jogador == "cyan":
                self.jogador.posicoes_turbo = []

            print(f"[CLASSE] Classe '{dados['nome']}' aplicada! Vidas: {dados['vidas']}")
        else:
            # Fallback para cor padrão do time
            if self.time_jogador == 'T':
                self.jogador.atualizar_cor(self.COR_TIME_T)
            else:
                self.jogador.atualizar_cor(self.COR_TIME_Q)

    def _usar_habilidade_classe(self):
        """Usa a habilidade especial da classe selecionada (tecla ESPAÇO)."""
        from src.game.selecao_classes import obter_dados_classe
        import math

        if self.jogador.vidas <= 0:
            return

        tempo_atual = pygame.time.get_ticks()
        dados = obter_dados_classe(self.classe_jogador, self.time_jogador)

        if not dados:
            return

        cooldown = dados.get("habilidade_cooldown", 0)

        # Verificar cooldown
        if tempo_atual - self.habilidade_cooldown < cooldown:
            tempo_restante = (cooldown - (tempo_atual - self.habilidade_cooldown)) / 1000
            print(f"[CLASSE] Habilidade em cooldown! {tempo_restante:.1f}s restantes")
            return

        # ====== CYAN - VELOCIDADE TURBO ======
        if self.classe_jogador == "cyan":
            self.habilidade_ativa = True
            self.habilidade_tempo_inicio = tempo_atual
            self.velocidade_original = self.jogador.velocidade
            # Velocidade turbo: 4x a velocidade normal
            self.jogador.velocidade = self.velocidade_original * 4.0
            self.habilidade_cooldown = tempo_atual
            # Inicializar rastro do turbo
            self.jogador.posicoes_turbo = []
            print(f"[CLASSE] TURBO ATIVADO! Velocidade: {self.jogador.velocidade:.1f} (era {self.velocidade_original:.1f})")

        # ====== EXPLOSIVE - EXPLOSÃO DE TIROS ======
        elif self.classe_jogador == "explosive":
            from src.entities.tiro import Tiro

            num_tiros = dados.get("tiros_explosao", 12)
            centro_x = self.jogador.x + TAMANHO_MULTIPLAYER / 2
            centro_y = self.jogador.y + TAMANHO_MULTIPLAYER / 2

            for i in range(num_tiros):
                angulo = (2 * math.pi / num_tiros) * i
                dx = math.cos(angulo)
                dy = math.sin(angulo)

                tiro = Tiro(centro_x, centro_y, dx, dy, dados["cor"], 12)
                tiro.time = 'Q'  # Tiros do jogador Time Q
                self.tiros_jogador.append(tiro)

            self.habilidade_cooldown = tempo_atual
            print(f"[CLASSE] EXPLOSÃO! {num_tiros} tiros disparados em todas as direções!")

        # ====== NORMAL - DASH ======
        elif self.classe_jogador == "normal":
            # Obter direção do movimento
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0

            if keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_s]:
                dy = 1
            if keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_d]:
                dx = 1

            if dx == 0 and dy == 0:
                dx = 1  # Dash para a direita se parado

            # Normalizar
            magnitude = math.sqrt(dx * dx + dy * dy)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude

            # Executar dash
            dash_velocidade = dados.get("dash_velocidade", 25)
            dash_duracao = dados.get("dash_duracao", 8)

            self.habilidade_ativa = True  # Marcar habilidade como ativa
            self.jogador.dash_ativo = True
            self.jogador.dash_frames_restantes = dash_duracao
            self.jogador.dash_direcao = (dx, dy)
            self.jogador.dash_velocidade = dash_velocidade
            self.jogador.invulneravel = True

            self.habilidade_cooldown = tempo_atual
            print("[CLASSE] DASH!")

        # ====== PURPLE - SEM HABILIDADE ATIVA ======
        elif self.classe_jogador == "purple":
            print("[CLASSE] Purple não tem habilidade ativa.")

        # ============ CLASSES TIME T ============

        # ====== MAGO - ESCUDO PROTETOR ======
        elif self.classe_jogador == "mago":
            self.habilidade_ativa = True
            self.habilidade_tempo_inicio = tempo_atual
            self.jogador.escudo_ativo = True
            self.jogador.invulneravel = True
            self.habilidade_cooldown = tempo_atual
            print("[CLASSE] ESCUDO ATIVADO! Proteção por 4 segundos!")

        # ====== GHOST - INVISIBILIDADE ======
        elif self.classe_jogador == "ghost":
            self.habilidade_ativa = True
            self.habilidade_tempo_inicio = tempo_atual
            self.jogador.invisivel = True
            self.habilidade_cooldown = tempo_atual
            print("[CLASSE] INVISIBILIDADE ATIVADA! Invisível por 4 segundos!")

        # ====== GRANADA - LANÇA GRANADA COM ESPAÇO ======
        elif self.classe_jogador == "granada":
            # Verificar cooldown
            cooldown = dados.get("habilidade_cooldown", 2000)
            if tempo_atual - self.habilidade_cooldown >= cooldown:
                # Lançar granada na direção do mouse
                self._lancar_granada_classe()
                self.habilidade_cooldown = tempo_atual

        # ====== METRALHADORA - SEM HABILIDADE DE ESPAÇO ======
        elif self.classe_jogador == "metralhadora":
            pass  # Passivo: metralhadora grátis + dano dobrado

    def _atualizar_habilidade_classe(self, tempo_atual):
        """Atualiza o estado das habilidades de classe (chamado a cada frame)."""
        from src.game.selecao_classes import obter_dados_classe

        if not self.habilidade_ativa:
            return

        dados = obter_dados_classe(self.classe_jogador, self.time_jogador)
        if not dados:
            return

        # ====== CYAN - DESATIVAR TURBO APÓS DURAÇÃO ======
        if self.classe_jogador == "cyan":
            duracao = dados.get("habilidade_duracao", 5000)
            if tempo_atual - self.habilidade_tempo_inicio >= duracao:
                self.jogador.velocidade = self.velocidade_original
                self.habilidade_ativa = False
                # Limpar rastro quando turbo termina
                if hasattr(self.jogador, 'posicoes_turbo'):
                    self.jogador.posicoes_turbo.clear()
                print("[CLASSE] Turbo desativado!")

        # ====== NORMAL - ATUALIZAR DASH ======
        elif self.classe_jogador == "normal":
            if hasattr(self.jogador, 'dash_ativo') and self.jogador.dash_ativo:
                if self.jogador.dash_frames_restantes > 0:
                    # Mover na direção do dash com colisão
                    dx, dy = self.jogador.dash_direcao
                    vel_x = dx * self.jogador.dash_velocidade
                    vel_y = dy * self.jogador.dash_velocidade

                    # Usar rect com tamanho multiplayer para colisões
                    rect_colisao = pygame.Rect(self.jogador.x, self.jogador.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)

                    # Resolver colisão com o mapa
                    novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(rect_colisao, vel_x, vel_y)

                    self.jogador.x = novo_x
                    self.jogador.y = novo_y
                    self.jogador.rect.x = novo_x
                    self.jogador.rect.y = novo_y
                    self.jogador.dash_frames_restantes -= 1
                else:
                    self.jogador.dash_ativo = False
                    self.jogador.invulneravel = False
                    self.habilidade_ativa = False

        # ============ CLASSES TIME T ============

        # ====== MAGO - DESATIVAR ESCUDO APÓS DURAÇÃO ======
        elif self.classe_jogador == "mago":
            duracao = dados.get("habilidade_duracao", 4000)
            if tempo_atual - self.habilidade_tempo_inicio >= duracao:
                self.jogador.escudo_ativo = False
                self.jogador.invulneravel = False
                self.habilidade_ativa = False
                print("[CLASSE] Escudo desativado!")

        # ====== GHOST - DESATIVAR INVISIBILIDADE APÓS DURAÇÃO ======
        elif self.classe_jogador == "ghost":
            duracao = dados.get("habilidade_duracao", 4000)
            if tempo_atual - self.habilidade_tempo_inicio >= duracao:
                self.jogador.invisivel = False
                self.habilidade_ativa = False
                print("[CLASSE] Invisibilidade desativada!")

    def _lancar_granada_comprada(self, pos_mouse_mundo):
        """Lança uma granada (Q para selecionar, clique para lançar)."""
        import math
        from src.items.granada import Granada

        if not hasattr(self.jogador, 'granadas') or self.jogador.granadas <= 0:
            print("[GRANADA] Sem granadas!")
            return

        # Centro do jogador
        centro_x = self.jogador.x + TAMANHO_MULTIPLAYER / 2
        centro_y = self.jogador.y + TAMANHO_MULTIPLAYER / 2

        # Calcular direção para o mouse
        dx = pos_mouse_mundo[0] - centro_x
        dy = pos_mouse_mundo[1] - centro_y

        # Normalizar
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Criar granada com time do jogador
        granada = Granada(centro_x, centro_y, dx, dy, pertence_inimigo=False)
        granada.time = self.time_jogador  # Marcar de qual time é
        self.granadas_ativas.append(granada)

        # Decrementar contagem
        self.jogador.granadas -= 1
        print(f"[GRANADA] Granada lançada! ({self.jogador.granadas} restantes)")

        # Criar som de lançamento
        tamanho_amostra = 6000
        som_granada = pygame.mixer.Sound(bytes(bytearray(
            int(127 + 127 * (math.sin(i / 15) if i < 1500 else 0))
            for i in range(tamanho_amostra)
        )))
        som_granada.set_volume(0.15)
        pygame.mixer.Channel(4).play(som_granada)

    def _lancar_granada_classe(self):
        """Lança uma granada da habilidade da classe Granada (ESPAÇO)."""
        import math
        from src.items.granada import Granada
        from src.utils.display_manager import convert_mouse_position

        # Obter posição do mouse no mundo
        pos_mouse_tela = convert_mouse_position(pygame.mouse.get_pos())
        pos_mouse_mundo = self._converter_mouse_para_mundo(pos_mouse_tela)

        # Centro do jogador
        centro_x = self.jogador.x + TAMANHO_MULTIPLAYER / 2
        centro_y = self.jogador.y + TAMANHO_MULTIPLAYER / 2

        # Calcular direção para o mouse
        dx = pos_mouse_mundo[0] - centro_x
        dy = pos_mouse_mundo[1] - centro_y

        # Normalizar
        distancia = math.sqrt(dx * dx + dy * dy)
        if distancia > 0:
            dx /= distancia
            dy /= distancia

        # Criar granada
        granada = Granada(centro_x, centro_y, dx, dy, pertence_inimigo=False)
        granada.time = self.time_jogador
        self.granadas_ativas.append(granada)

        # Som de lançamento
        tamanho_amostra = 6000
        som_granada = pygame.mixer.Sound(bytes(bytearray(
            int(127 + 127 * (math.sin(i / 15) if i < 1500 else 0))
            for i in range(tamanho_amostra)
        )))
        som_granada.set_volume(0.15)
        pygame.mixer.Channel(4).play(som_granada)

    def _atualizar_granadas_ativas(self):
        """Atualiza todas as granadas em voo com colisão de paredes."""
        import math
        from src.entities.tiro import Tiro

        for granada in self.granadas_ativas[:]:
            # Atualizar física
            granada.dx *= granada.fricao
            granada.dy *= granada.fricao

            # Próxima posição
            nova_x = granada.x + granada.dx
            nova_y = granada.y + granada.dy

            # Verificar colisão com paredes do tilemap
            raio = granada.raio
            colidiu = False

            # Verificar colisão X
            rect_teste_x = pygame.Rect(nova_x - raio, granada.y - raio, raio * 2, raio * 2)
            colisoes_x = self.tilemap.get_colisoes_proximas(rect_teste_x)
            for rect_colisao in colisoes_x:
                if rect_teste_x.colliderect(rect_colisao):
                    # Rebater na parede
                    granada.dx = -granada.dx * granada.elasticidade
                    nova_x = granada.x
                    colidiu = True
                    break

            # Verificar colisão Y
            rect_teste_y = pygame.Rect(granada.x - raio, nova_y - raio, raio * 2, raio * 2)
            colisoes_y = self.tilemap.get_colisoes_proximas(rect_teste_y)
            for rect_colisao in colisoes_y:
                if rect_teste_y.colliderect(rect_colisao):
                    # Rebater na parede
                    granada.dy = -granada.dy * granada.elasticidade
                    nova_y = granada.y
                    colidiu = True
                    break

            # Aplicar nova posição
            granada.x = nova_x
            granada.y = nova_y

            # Atualizar retângulo de colisão
            granada.rect.x = granada.x - raio
            granada.rect.y = granada.y - raio

            # Atualizar ângulo de rotação
            granada.angulo = (granada.angulo + granada.velocidade_rotacao) % 360

            # Verificar se velocidade é muito baixa (granada parou)
            velocidade_total = math.sqrt(granada.dx**2 + granada.dy**2)
            if velocidade_total < 0.5 and granada.tempo_explosao == 0:
                granada.tempo_explosao = 30  # 0.5 segundo até explodir

            # Decrementar tempo para explosão
            if granada.tempo_explosao > 0:
                granada.tempo_explosao -= 1
                # Piscar quando perto de explodir
                if granada.tempo_explosao < 15 and granada.tempo_explosao % 3 < 2:
                    granada.cor = (200, 60, 60)
                else:
                    granada.cor = (60, 120, 60)
                # Explodir quando tempo acabar
                if granada.tempo_explosao <= 0:
                    self._explodir_granada(granada)

            # Decrementar tempo de vida
            granada.tempo_vida -= 1
            if granada.tempo_vida <= 0 and not granada.explodiu:
                self._explodir_granada(granada)

            # Remover granadas explodidas
            if granada.explodiu:
                self.granadas_ativas.remove(granada)

    def _explodir_granada(self, granada):
        """Faz a granada explodir com efeitos visuais e dano."""
        import math
        from src.entities.tiro import Tiro
        from src.entities.particula import criar_explosao

        granada.explodiu = True

        # Criar explosão visual
        cores = [(255, 100, 0), (255, 200, 0), (255, 50, 0)]
        for i in range(3):
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            flash = criar_explosao(granada.x + offset_x, granada.y + offset_y,
                                 random.choice(cores), self.particulas, 40)
            self.flashes.append(flash)

        # Explosão central maior
        flash_principal = {
            'x': granada.x,
            'y': granada.y,
            'raio': 60,
            'vida': 20,
            'cor': (255, 255, 200)
        }
        self.flashes.append(flash_principal)

        # Criar projéteis em círculo
        num_projeteis = 8
        velocidade_projetil = 8

        for i in range(num_projeteis):
            angulo = (2 * math.pi * i) / num_projeteis
            dx = math.cos(angulo)
            dy = math.sin(angulo)
            cor_projetil = (255, 150, 0)
            projetil = Tiro(granada.x, granada.y, dx, dy, cor_projetil, velocidade_projetil)
            self.tiros_jogador.append(projetil)

        # Verificar dano nos bots do time inimigo
        for bot in self.bots_locais:
            if bot.vidas <= 0:
                continue
            # Só causar dano em bots do time oposto
            if bot.time == granada.time:
                continue
            # Verificar invulnerabilidade (escudo do mago)
            if getattr(bot, 'invulneravel', False):
                continue
            # Calcular distância
            dx = granada.x - (bot.x + bot.tamanho // 2)
            dy = granada.y - (bot.y + bot.tamanho // 2)
            distancia = math.sqrt(dx**2 + dy**2)
            if distancia <= granada.raio_explosao:
                bot.tomar_dano()

        # Criar som de explosão
        tamanho_amostra = 10000
        som_explosao = pygame.mixer.Sound(bytes(bytearray(
            int(127 + 127 * random.uniform(-1, 1) * (1 - i/tamanho_amostra))
            for i in range(tamanho_amostra)
        )))
        som_explosao.set_volume(0.3)
        pygame.mixer.Channel(5).play(som_explosao)

    def _desenhar_granadas_ativas(self, surface):
        """Desenha todas as granadas em voo."""
        for granada in self.granadas_ativas:
            if granada.explodiu:
                continue

            # Posição na tela (com câmera)
            granada_x = granada.x - self.camera_x
            granada_y = granada.y - self.camera_y

            # Tamanho pequeno para a granada em voo
            raio = 4

            # Desenhar corpo da granada (simples, sem rotação complexa)
            pygame.draw.circle(surface, granada.cor, (int(granada_x), int(granada_y)), raio)
            pygame.draw.circle(surface, (40, 80, 40), (int(granada_x), int(granada_y)), raio, 1)

    # ==================== DEV MODE - SISTEMA DE DESENHO DE ROTAS ====================

    def _entrar_dev_mode(self):
        """Entra no modo desenvolvedor para desenhar rotas dos bots."""
        print("[DEV MODE] Entrando no modo desenvolvedor...")
        self.dev_mode = True
        self.selecionando_time = False

        # Carregar mapa sem iniciar o jogo normal
        self._carregar_mapa_dev_mode()

        # Carregar rotas existentes se houver
        self._carregar_rotas()

        # Iniciar loop do dev mode
        self._loop_dev_mode()

    def _carregar_mapa_dev_mode(self):
        """Carrega apenas o mapa para o dev mode."""
        caminho_mapa = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'map_tiled.tmx')
        self.tilemap = TileMap(caminho_mapa)
        print(f"[DEV MODE] Mapa carregado: {self.tilemap.largura_pixels}x{self.tilemap.altura_pixels}")

        # Configurar câmera
        self.camera_x = 0
        self.camera_y = 0
        self.camera_zoom = 1.0  # Zoom menor para ver mais do mapa

    def _loop_dev_mode(self):
        """Loop principal do modo desenvolvedor."""
        from src.utils.visual import desenhar_texto
        from src.utils.display_manager import convert_mouse_position

        rodando = True
        velocidade_camera = 10

        while rodando:
            # Eventos
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False

                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        # Salvar e sair
                        self._salvar_rotas()
                        rodando = False

                    # === TROCAR TIME COM 1 E 2 ===
                    if evento.key == pygame.K_1:
                        self.dev_time_selecionado = 'T'
                        print("[DEV MODE] Desenhando rotas para TIME T (Terroristas)")

                    if evento.key == pygame.K_2:
                        self.dev_time_selecionado = 'Q'
                        print("[DEV MODE] Desenhando rotas para TIME Q (Counter)")

                    if evento.key == pygame.K_F5:
                        # Salvar rotas
                        self._salvar_rotas()

                    if evento.key == pygame.K_c:
                        # Limpar rotas do time atual
                        if self.dev_time_selecionado == 'T':
                            self.dev_rotas_t = []
                            print("[DEV MODE] Rotas do TIME T limpas!")
                        else:
                            self.dev_rotas_q = []
                            print("[DEV MODE] Rotas do TIME Q limpas!")
                        self.dev_rota_atual = []

                    if evento.key == pygame.K_z:
                        # Desfazer último ponto da rota atual
                        if self.dev_rota_atual:
                            self.dev_rota_atual.pop()
                            print(f"[DEV MODE] Ponto removido. {len(self.dev_rota_atual)} pontos na rota atual")

                    if evento.key == pygame.K_RETURN:
                        # Finalizar rota atual e começar nova
                        if len(self.dev_rota_atual) >= 2:
                            if self.dev_time_selecionado == 'T':
                                self.dev_rotas_t.append(self.dev_rota_atual.copy())
                                print(f"[DEV MODE] Rota TIME T #{len(self.dev_rotas_t)} salva!")
                            else:
                                self.dev_rotas_q.append(self.dev_rota_atual.copy())
                                print(f"[DEV MODE] Rota TIME Q #{len(self.dev_rotas_q)} salva!")
                            self.dev_rota_atual = []

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  # Clique esquerdo
                        # Adicionar ponto na rota
                        mouse_pos = convert_mouse_position(evento.pos)
                        # Converter para coordenadas do mundo
                        mundo_x = mouse_pos[0] / self.camera_zoom + self.camera_x
                        mundo_y = mouse_pos[1] / self.camera_zoom + self.camera_y
                        self.dev_rota_atual.append((int(mundo_x), int(mundo_y)))
                        print(f"[DEV MODE] Ponto adicionado: ({int(mundo_x)}, {int(mundo_y)})")

                    if evento.button == 3:  # Clique direito
                        # Finalizar rota atual
                        if len(self.dev_rota_atual) >= 2:
                            if self.dev_time_selecionado == 'T':
                                self.dev_rotas_t.append(self.dev_rota_atual.copy())
                                print(f"[DEV MODE] Rota TIME T #{len(self.dev_rotas_t)} finalizada!")
                            else:
                                self.dev_rotas_q.append(self.dev_rota_atual.copy())
                                print(f"[DEV MODE] Rota TIME Q #{len(self.dev_rotas_q)} finalizada!")
                            self.dev_rota_atual = []

                    if evento.button == 2:  # Clique do meio (scroll) - apagar rota
                        mouse_pos = convert_mouse_position(evento.pos)
                        mundo_x = mouse_pos[0] / self.camera_zoom + self.camera_x
                        mundo_y = mouse_pos[1] / self.camera_zoom + self.camera_y

                        # Tentar apagar rota do Time T
                        rota_idx = self._encontrar_rota_clicada(mundo_x, mundo_y, self.dev_rotas_t)
                        if rota_idx is not None:
                            self.dev_rotas_t.pop(rota_idx)
                            print(f"[DEV MODE] Rota TIME T #{rota_idx + 1} apagada!")
                        else:
                            # Tentar apagar rota do Time Q
                            rota_idx = self._encontrar_rota_clicada(mundo_x, mundo_y, self.dev_rotas_q)
                            if rota_idx is not None:
                                self.dev_rotas_q.pop(rota_idx)
                                print(f"[DEV MODE] Rota TIME Q #{rota_idx + 1} apagada!")

            # Movimento da câmera com Setas
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_UP]:
                self.camera_y -= velocidade_camera
            if teclas[pygame.K_DOWN]:
                self.camera_y += velocidade_camera
            if teclas[pygame.K_LEFT]:
                self.camera_x -= velocidade_camera
            if teclas[pygame.K_RIGHT]:
                self.camera_x += velocidade_camera

            # Zoom com + e -
            if teclas[pygame.K_EQUALS] or teclas[pygame.K_KP_PLUS]:
                self.camera_zoom = min(3.0, self.camera_zoom + 0.02)
            if teclas[pygame.K_MINUS] or teclas[pygame.K_KP_MINUS]:
                self.camera_zoom = max(0.3, self.camera_zoom - 0.02)

            # Limitar câmera
            self.camera_x = max(0, min(self.camera_x, self.tilemap.largura_pixels - LARGURA / self.camera_zoom))
            self.camera_y = max(0, min(self.camera_y, self.tilemap.altura_pixels - ALTURA / self.camera_zoom))

            # Desenhar
            self.tela.fill((20, 20, 30))

            # Desenhar mapa
            self._desenhar_mapa_dev_mode()

            # Desenhar rotas
            self._desenhar_rotas_dev_mode()

            # Desenhar HUD
            self._desenhar_hud_dev_mode()

            present_frame()
            self.relogio.tick(60)

        # Ao sair, voltar para seleção de time
        self.dev_mode = False
        self.selecionando_time = True

    def _desenhar_mapa_dev_mode(self):
        """Desenha o mapa no dev mode."""
        # Criar superfície temporária com o tamanho visível
        largura_visivel = int(LARGURA / self.camera_zoom)
        altura_visivel = int(ALTURA / self.camera_zoom)

        # Desenhar tiles visíveis
        tile_inicio_x = int(self.camera_x // self.tilemap.tile_largura)
        tile_inicio_y = int(self.camera_y // self.tilemap.tile_altura)
        tile_fim_x = int((self.camera_x + largura_visivel) // self.tilemap.tile_largura) + 2
        tile_fim_y = int((self.camera_y + altura_visivel) // self.tilemap.tile_altura) + 2

        for y in range(max(0, tile_inicio_y), min(self.tilemap.altura, tile_fim_y)):
            for x in range(max(0, tile_inicio_x), min(self.tilemap.largura, tile_fim_x)):
                tile_id = self.tilemap.get_tile(x, y)
                if tile_id > 0:
                    # Posição na tela
                    tela_x = int((x * self.tilemap.tile_largura - self.camera_x) * self.camera_zoom)
                    tela_y = int((y * self.tilemap.tile_altura - self.camera_y) * self.camera_zoom)
                    tamanho = int(self.tilemap.tile_largura * self.camera_zoom)

                    # Cor baseada no tile
                    tile_base = tile_id & 0x1FFFFFFF
                    px = x * self.tilemap.tile_largura + 8
                    py = y * self.tilemap.tile_altura + 8
                    if tile_base == 322:
                        # Tile 322 - bombsite (destacar)
                        cor = (255, 200, 0)
                    elif self.tilemap.is_solid(px, py):
                        cor = (60, 60, 80)
                    else:
                        cor = (40, 40, 50)

                    pygame.draw.rect(self.tela, cor, (tela_x, tela_y, tamanho, tamanho))
                    pygame.draw.rect(self.tela, (30, 30, 40), (tela_x, tela_y, tamanho, tamanho), 1)

    def _desenhar_rotas_dev_mode(self):
        """Desenha as rotas no dev mode - rotas separadas por time."""
        from src.utils.visual import desenhar_texto

        # === ROTAS DO TIME T (VERMELHO) ===
        for i, rota in enumerate(self.dev_rotas_t):
            if len(rota) >= 2:
                pontos_tela = []
                for ponto in rota:
                    tela_x = int((ponto[0] - self.camera_x) * self.camera_zoom)
                    tela_y = int((ponto[1] - self.camera_y) * self.camera_zoom)
                    pontos_tela.append((tela_x, tela_y))

                # Desenhar linha vermelha
                pygame.draw.lines(self.tela, (255, 80, 80), False, pontos_tela, 3)

                # Desenhar pontos
                for j, ponto in enumerate(pontos_tela):
                    cor_ponto = (255, 255, 0) if j == 0 else (255, 100, 100)
                    pygame.draw.circle(self.tela, cor_ponto, ponto, 6)
                    pygame.draw.circle(self.tela, (255, 200, 200), ponto, 6, 2)

                # Desenhar número da rota no ponto inicial
                numero_texto = f"T{i + 1}"
                desenhar_texto(self.tela, numero_texto, 14, (255, 255, 255), pontos_tela[0][0], pontos_tela[0][1] - 15)

        # === ROTAS DO TIME Q (AZUL) ===
        for i, rota in enumerate(self.dev_rotas_q):
            if len(rota) >= 2:
                pontos_tela = []
                for ponto in rota:
                    tela_x = int((ponto[0] - self.camera_x) * self.camera_zoom)
                    tela_y = int((ponto[1] - self.camera_y) * self.camera_zoom)
                    pontos_tela.append((tela_x, tela_y))

                # Desenhar linha azul
                pygame.draw.lines(self.tela, (80, 150, 255), False, pontos_tela, 3)

                # Desenhar pontos
                for j, ponto in enumerate(pontos_tela):
                    cor_ponto = (255, 255, 0) if j == 0 else (100, 150, 255)
                    pygame.draw.circle(self.tela, cor_ponto, ponto, 6)
                    pygame.draw.circle(self.tela, (200, 220, 255), ponto, 6, 2)

                # Desenhar número da rota no ponto inicial
                numero_texto = f"Q{i + 1}"
                desenhar_texto(self.tela, numero_texto, 14, (255, 255, 255), pontos_tela[0][0], pontos_tela[0][1] - 15)

        # === ROTA ATUAL SENDO DESENHADA ===
        if len(self.dev_rota_atual) >= 1:
            pontos_tela = []
            for ponto in self.dev_rota_atual:
                tela_x = int((ponto[0] - self.camera_x) * self.camera_zoom)
                tela_y = int((ponto[1] - self.camera_y) * self.camera_zoom)
                pontos_tela.append((tela_x, tela_y))

            # Desenhar linha até o mouse
            mouse_pos = pygame.mouse.get_pos()
            pontos_tela.append(mouse_pos)

            # Cor da linha baseada no time selecionado
            if self.dev_time_selecionado == 'T':
                cor_linha = (255, 150, 50)  # Laranja para T
            else:
                cor_linha = (50, 200, 255)  # Ciano para Q

            if len(pontos_tela) >= 2:
                pygame.draw.lines(self.tela, cor_linha, False, pontos_tela, 2)

            # Desenhar pontos
            for j, ponto in enumerate(pontos_tela[:-1]):
                pygame.draw.circle(self.tela, cor_linha, ponto, 5)
                pygame.draw.circle(self.tela, (255, 255, 255), ponto, 5, 1)

    def _desenhar_hud_dev_mode(self):
        """Desenha o HUD do dev mode."""
        from src.utils.visual import desenhar_texto

        # Fundo semi-transparente para o HUD
        hud_surface = pygame.Surface((320, 300), pygame.SRCALPHA)
        hud_surface.fill((0, 0, 0, 180))
        self.tela.blit(hud_surface, (10, 10))

        # Título
        desenhar_texto(self.tela, "DEV MODE - Desenho de Rotas", 20, (0, 255, 0), 170, 30)

        # Indicador do time selecionado
        if self.dev_time_selecionado == 'T':
            cor_time = (255, 100, 100)
            nome_time = "TIME T (Terroristas)"
        else:
            cor_time = (100, 150, 255)
            nome_time = "TIME Q (Counter)"

        desenhar_texto(self.tela, f"Desenhando: {nome_time}", 14, cor_time, 170, 52)

        # Instruções
        instrucoes = [
            "1: Selecionar TIME T",
            "2: Selecionar TIME Q",
            "CLIQUE ESQUERDO: Adicionar ponto",
            "CLIQUE DIREITO: Finalizar rota",
            "CLIQUE MEIO: Apagar rota",
            "ENTER: Finalizar rota",
            "Z: Desfazer ultimo ponto",
            "C: Limpar rotas do time atual",
            "WASD/Setas: Mover camera",
            "+/-: Zoom",
            "S: Salvar rotas",
            "ESC: Salvar e sair",
        ]

        y = 75
        for inst in instrucoes:
            desenhar_texto(self.tela, inst, 12, (200, 200, 200), 170, y)
            y += 16

        # Status das rotas por time
        desenhar_texto(self.tela, f"Rotas TIME T: {len(self.dev_rotas_t)}", 14, (255, 100, 100), 170, 271)
        desenhar_texto(self.tela, f"Rotas TIME Q: {len(self.dev_rotas_q)}", 14, (100, 150, 255), 170, 289)

        # Pontos na rota atual
        if self.dev_rota_atual:
            desenhar_texto(self.tela, f"Rota atual: {len(self.dev_rota_atual)} pontos", 14, (255, 255, 100), LARGURA - 100, 30)

    def _salvar_rotas(self):
        """Salva as rotas em um arquivo JSON - separadas por time."""
        import json

        dados = {
            "rotas_time_t": self.dev_rotas_t,
            "rotas_time_q": self.dev_rotas_q
        }

        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.dev_arquivo_rotas)

        try:
            with open(caminho, 'w') as f:
                json.dump(dados, f, indent=2)
            print(f"[DEV MODE] Rotas salvas: TIME T={len(self.dev_rotas_t)}, TIME Q={len(self.dev_rotas_q)}")
        except Exception as e:
            print(f"[DEV MODE] Erro ao salvar rotas: {e}")

    def _carregar_rotas(self):
        """Carrega as rotas de um arquivo JSON - separadas por time."""
        import json

        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.dev_arquivo_rotas)

        try:
            if os.path.exists(caminho):
                with open(caminho, 'r') as f:
                    dados = json.load(f)

                # Carregar rotas do Time T
                self.dev_rotas_t = [[(p[0], p[1]) for p in rota] for rota in dados.get("rotas_time_t", [])]

                # Carregar rotas do Time Q
                self.dev_rotas_q = [[(p[0], p[1]) for p in rota] for rota in dados.get("rotas_time_q", [])]

                # Compatibilidade com formato antigo (campo "rotas" genérico)
                if not self.dev_rotas_t and not self.dev_rotas_q and "rotas" in dados:
                    # Se só tem o campo antigo, colocar tudo no Time T por padrão
                    self.dev_rotas_t = [[(p[0], p[1]) for p in rota] for rota in dados.get("rotas", [])]
                    print(f"[DEV MODE] Formato antigo detectado, rotas migradas para TIME T")

                print(f"[DEV MODE] Rotas carregadas: TIME T={len(self.dev_rotas_t)}, TIME Q={len(self.dev_rotas_q)}")
            else:
                print(f"[DEV MODE] Nenhum arquivo de rotas encontrado. Começando do zero.")
                self.dev_rotas_t = []
                self.dev_rotas_q = []
        except Exception as e:
            print(f"[DEV MODE] Erro ao carregar rotas: {e}")
            self.dev_rotas_t = []
            self.dev_rotas_q = []

    def _encontrar_rota_clicada(self, mundo_x, mundo_y, lista_rotas, tolerancia=15):
        """
        Encontra qual rota foi clicada baseado na proximidade do ponto aos segmentos.

        Args:
            mundo_x, mundo_y: Coordenadas do clique no mundo
            lista_rotas: Lista de rotas para verificar
            tolerancia: Distância máxima em pixels para considerar um clique

        Returns:
            Índice da rota clicada ou None se nenhuma foi clicada
        """
        for idx, rota in enumerate(lista_rotas):
            if len(rota) < 2:
                continue

            # Verificar cada segmento da rota
            for i in range(len(rota) - 1):
                p1 = rota[i]
                p2 = rota[i + 1]

                # Calcular distância do ponto ao segmento de linha
                dist = self._distancia_ponto_segmento(mundo_x, mundo_y, p1[0], p1[1], p2[0], p2[1])

                if dist <= tolerancia:
                    return idx

        return None

    def _distancia_ponto_segmento(self, px, py, x1, y1, x2, y2):
        """Calcula a distância de um ponto a um segmento de linha."""
        import math

        # Vetor do segmento
        dx = x2 - x1
        dy = y2 - y1

        # Comprimento ao quadrado do segmento
        comprimento_sq = dx * dx + dy * dy

        if comprimento_sq == 0:
            # Segmento é um ponto
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Parâmetro t da projeção do ponto no segmento (0 a 1)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / comprimento_sq))

        # Ponto mais próximo no segmento
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        # Distância do ponto ao ponto mais próximo
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    # ==================== FIM DEV MODE ====================

    def _carregar_jogo(self):
        """Carrega o mapa e inicializa o jogo após seleção de time."""
        # Inicializar como fase base (sem inimigos inicialmente)
        super().__init__(self.tela, self.relogio, 1, self.gradiente_jogo, self.fonte_titulo, self.fonte_normal)

        # Reconfigurar atributos que podem ter sido sobrescritos
        self.jogador.nome = self.nome_jogador

        # Carregar mapa TMX
        caminho_mapa = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'map_tiled.tmx')
        self.tilemap = TileMap(caminho_mapa)
        print(f"[MULTIPLAYER] Mapa carregado: {self.tilemap.largura_pixels}x{self.tilemap.altura_pixels} pixels")

        # Configurar jogador
        self.jogador.rect.width = TAMANHO_MULTIPLAYER
        self.jogador.rect.height = TAMANHO_MULTIPLAYER
        self.jogador.tamanho = TAMANHO_MULTIPLAYER
        self.jogador.velocidade = 2.5  # Velocidade fixa para multiplayer
        self.jogador.tempo_ultimo_tiro = 0  # Garantir que existe para o sistema de armas

        # Sistema de câmera para mapas grandes
        self.camera_x = 0
        self.camera_y = 0
        self.camera_zoom = 2.0  # Zoom 2x para aproximar a câmera do jogador

        # Aplicar efeitos da classe (ambos os times têm classes)
        self._aplicar_classe_jogador()

        # Posicionar jogador no spawn do time
        spawn_name = f"Start_{self.time_jogador}"
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

        # Marcar mapa como carregado
        self.mapa_carregado = True

        # Sistema de compra (estilo Counter-Strike)
        self.tempo_inicio_round = pygame.time.get_ticks()
        self.tempo_compra = 6000  # 6 segundos de tempo de compra
        self.em_tempo_compra = True  # Flag para saber se ainda está no tempo de compra
        self.menu_compra_aberto = False  # Menu de compra aberto (tecla B)
        self.moedas = 800  # Dinheiro inicial
        self.arma_equipada = None  # None = pistola padrão

        # Sistema de granadas
        self.jogador.granadas = 0  # Começa sem granadas (compra na loja)
        self.jogador.granada_selecionada = False  # Se está segurando granada
        self.granadas_ativas = []  # Lista de granadas em voo

        # Sistema de rounds (primeiro a 5 vitórias)
        self.rounds_time_t = 0
        self.rounds_time_q = 0
        self.rounds_para_vencer = 5
        self.round_atual = 1
        self.round_terminado = False  # Flag para round individual
        self.partida_terminada = False  # Flag para partida completa (5 rounds)
        self.tempo_proximo_round = 0  # Timer para próximo round

        # Sistema de espectador (câmera segue aliados quando jogador morre)
        self.espectador_ativo = False
        self.espectador_tempo_morte = 0  # Tempo quando o jogador morreu
        self.espectador_alvo_idx = 0  # Índice do aliado sendo observado
        self.espectador_delay = 2000  # 2 segundos de delay antes de seguir aliado

        # Sistema de bomba
        self.bomber_id = None  # ID do jogador/bot que é o bomber
        self.bomber_é_jogador = False  # True se o jogador local é o bomber
        self.bomba_plantada = False
        self.bomba_posicao = None  # (x, y) onde a bomba foi plantada
        self.bomba_tempo_plantio = 0  # Quando a bomba foi plantada
        self.bomba_tempo_explosao = 35000  # 35 segundos para explodir
        self.plantando_bomba = False  # Se está no processo de plantar
        self.tempo_inicio_plantar = 0  # Quando começou a plantar
        self.tempo_para_plantar = 4000  # 4 segundos para plantar
        self.defusando_bomba = False  # Se está no processo de defusar
        self.tempo_inicio_defusar = 0  # Quando começou a defusar
        self.tempo_para_defusar = 5000  # 5 segundos para defusar
        self.bomba_defusada = False
        self.bomba_explodiu = False

        # Bomba dropada no chão (quando bomber morre)
        self.bomba_dropada = False
        self.bomba_drop_posicao = None  # (x, y) onde a bomba está no chão

        # Encontrar posições dos bombsites (tile 322)
        self.bombsites = self._encontrar_bombsites()
        print(f"[MULTIPLAYER] Bombsites encontrados: {len(self.bombsites)} locais")

        # Criar mapa de navegação (grid de pontos válidos)
        self.nav_grid = self._criar_mapa_navegacao()
        print(f"[MULTIPLAYER] Mapa de navegação: {len(self.nav_grid)} pontos válidos")

        # Carregar rotas desenhadas no DEV MODE
        self._carregar_rotas()
        if self.dev_rotas_t or self.dev_rotas_q:
            print(f"[MULTIPLAYER] Rotas carregadas: TIME T={len(self.dev_rotas_t)}, TIME Q={len(self.dev_rotas_q)}")

        # Criar pontos estratégicos por time
        self.pontos_time_t = []  # Pontos para atacantes
        self.pontos_time_q = []  # Pontos para defensores
        self._criar_pontos_estrategicos()

        # Selecionar bomber inicial
        self._selecionar_bomber()

        # Definir armas disponíveis e preços
        self.armas_disponiveis = {
            'desert_eagle': {
                'nome': 'Desert Eagle',
                'preco': 500,
                'dano': 3,
                'velocidade': 15,
                'descricao': 'Pistola de alto calibre'
            },
            'spas12': {
                'nome': 'SPAS-12',
                'preco': 1200,
                'dano': 2,
                'velocidade': 8,
                'descricao': 'Shotgun tatica (5 tiros)'
            },
            'metralhadora': {
                'nome': 'Metralhadora',
                'preco': 2700,
                'dano': 1,
                'velocidade': 15,
                'descricao': 'Alta cadencia de tiro'
            },
            'sniper': {
                'nome': 'Sniper',
                'preco': 4750,
                'dano': 6,
                'velocidade': 40,
                'descricao': 'Rifle de precisao'
            }
        }

        # Definir itens disponíveis e preços
        self.itens_disponiveis = {
            'granada': {
                'nome': 'Granada',
                'preco': 300,
                'quantidade': 1,
                'max': 3,
                'descricao': 'Explosiva - dano em area'
            }
        }

        # Aba atual da loja (0 = armas, 1 = itens)
        self.aba_loja_atual = 0

        print(f"[MULTIPLAYER] Jogo carregado! Modo: VERSUS - {len(self.bots_locais)} bots (4v4)")

    def _criar_bots_distribuidos(self):
        """
        Cria bots distribuídos entre os dois times.
        Cada time SEMPRE tem 4 quadrados:
        - Time do jogador: 1 jogador + 3 bots = 4
        - Time inimigo: 4 bots = 4

        Cada bot recebe uma classe única (sem repetir no mesmo time).
        A classe do jogador é excluída dos bots do mesmo time.
        """
        from src.game.selecao_classes import CLASSES_TIME_T, CLASSES_TIME_Q

        self.bots_locais = []

        # Nomes para os bots
        nomes_time_t = ["Bernado", "Borba", "Melina", "Felipe"]
        nomes_time_q = ["Duda", "Marcelo", "João", "Emy"]

        # Classes disponíveis para cada time
        classes_t = list(CLASSES_TIME_T.keys())  # ["mago", "ghost", "granada", "metralhadora"]
        classes_q = list(CLASSES_TIME_Q.keys())  # ["cyan", "explosive", "normal", "purple"]

        # Embaralhar classes para variedade
        random.shuffle(classes_t)
        random.shuffle(classes_q)

        # Remover a classe do jogador da lista do seu time
        if self.time_jogador == 'T' and self.classe_jogador in classes_t:
            classes_t.remove(self.classe_jogador)
        elif self.time_jogador == 'Q' and self.classe_jogador in classes_q:
            classes_q.remove(self.classe_jogador)

        # Criar bots para cada time
        # Time do jogador: 3 bots (jogador é o 4º)
        # Time inimigo: 4 bots

        if self.time_jogador == 'T':
            # Jogador está no Time T -> criar 3 bots no T e 4 no Q
            for i in range(3):
                classe_bot = classes_t[i] if i < len(classes_t) else classes_t[0]
                bot_info = {'nome': nomes_time_t[i], 'classe': classe_bot}
                bot = self._criar_bot_com_time(bot_info, 'T')
                self.bots_locais.append(bot)
                print(f"[MULTIPLAYER] Bot criado: {bot.nome} ({bot.classe}) - Time T (aliado)")

            for i in range(4):
                classe_bot = classes_q[i] if i < len(classes_q) else classes_q[0]
                bot_info = {'nome': nomes_time_q[i], 'classe': classe_bot}
                bot = self._criar_bot_com_time(bot_info, 'Q')
                self.bots_locais.append(bot)
                print(f"[MULTIPLAYER] Bot criado: {bot.nome} ({bot.classe}) - Time Q (inimigo)")
        else:
            # Jogador está no Time Q -> criar 4 bots no T e 3 no Q
            for i in range(4):
                classe_bot = classes_t[i] if i < len(classes_t) else classes_t[0]
                bot_info = {'nome': nomes_time_t[i], 'classe': classe_bot}
                bot = self._criar_bot_com_time(bot_info, 'T')
                self.bots_locais.append(bot)
                print(f"[MULTIPLAYER] Bot criado: {bot.nome} ({bot.classe}) - Time T (inimigo)")

            for i in range(3):
                classe_bot = classes_q[i] if i < len(classes_q) else classes_q[0]
                bot_info = {'nome': nomes_time_q[i], 'classe': classe_bot}
                bot = self._criar_bot_com_time(bot_info, 'Q')
                self.bots_locais.append(bot)
                print(f"[MULTIPLAYER] Bot criado: {bot.nome} ({bot.classe}) - Time Q (aliado)")

        print(f"[MULTIPLAYER] Times configurados: 4v4 com classes únicas")

    def _criar_bot_com_time(self, bot_info, time_bot):
        """Cria um bot para um time específico com classe."""
        from src.game.selecao_classes import obter_dados_classe

        # Posição no spawn do time
        spawn_name = f"Start_{time_bot}"
        spawn_obj = self.tilemap.get_objeto(spawn_name)

        if spawn_obj:
            # Posição aleatória dentro da área de spawn
            x = spawn_obj['x'] + random.random() * spawn_obj['width']
            y = spawn_obj['y'] + random.random() * spawn_obj['height']
        else:
            x, y = self._encontrar_posicao_valida()

        # Obter classe do bot
        classe_id = bot_info.get('classe', None)
        dados_classe = obter_dados_classe(classe_id, time_bot) if classe_id else None

        # Cor baseada na classe (ou cor do time se não tiver classe)
        if dados_classe:
            cor = dados_classe.get('cor', self.COR_TIME_T if time_bot == 'T' else self.COR_TIME_Q)
            cor_escura = dados_classe.get('cor_escura', (cor[0] // 2, cor[1] // 2, cor[2] // 2))
            vidas = dados_classe.get('vidas', 5)
        else:
            cor = self.COR_TIME_T if time_bot == 'T' else self.COR_TIME_Q
            cor_escura = (cor[0] // 2, cor[1] // 2, cor[2] // 2)
            vidas = 5

        # Criar entidade do bot com velocidade adequada para multiplayer
        bot = Quadrado(x, y, TAMANHO_MULTIPLAYER, cor, 2.5)
        bot.nome = bot_info['nome']
        bot.vidas = vidas
        bot.vidas_max = vidas
        bot.time = time_bot  # Guardar o time do bot
        bot.cor_escura = cor_escura

        # Classe do bot
        bot.classe = classe_id
        bot.dados_classe = dados_classe

        # Sistema de habilidade do bot
        bot.habilidade_cooldown = 0  # Tempo do último uso
        bot.habilidade_ativa = False
        bot.habilidade_tempo_inicio = 0
        bot.velocidade_original = bot.velocidade

        # Atributos específicos de classe
        if classe_id == 'mago':
            bot.escudo_ativo = False
            bot.invulneravel = False
        elif classe_id == 'ghost':
            bot.invisivel = False
        elif classe_id == 'granada':
            bot.granadas_habilidade = 999  # Ilimitadas com cooldown
        elif classe_id == 'metralhadora':
            bot.metralhadora_dano_bonus = dados_classe.get('metralhadora_dano_bonus', 2)
        elif classe_id == 'cyan':
            bot.posicoes_turbo = []
        elif classe_id == 'normal':
            bot.dash_ativo = False
            bot.dash_frames_restantes = 0
            bot.dash_direcao = (0, 0)
            bot.dash_velocidade = dados_classe.get('dash_velocidade', 25)

        # IA do bot - atributos básicos
        bot.is_bot = True
        bot.alvo_x = x
        bot.alvo_y = y
        bot.tempo_ultimo_tiro = 0
        bot.tempo_mudar_alvo = pygame.time.get_ticks()

        # IA avançada - economia e armas
        bot.moedas = 800  # Dinheiro inicial igual ao jogador
        bot.arma = None  # Arma equipada (None = sem arma)
        bot.dano_arma = 1  # Dano da arma
        bot.cadencia_arma = 500  # Tempo entre tiros (ms) - tiro normal mais lento

        # Classe metralhadora: começa com metralhadora grátis e dano dobrado
        if classe_id == 'metralhadora':
            bot.arma = 'metralhadora'
            bot.dano_arma = 2
            bot.cadencia_arma = 100  # Metralhadora é rápida

        # IA avançada - comportamento
        bot.estado = 'comprando'  # Estados: comprando, movendo, atacando, plantando, defusando
        bot.bombsite_alvo = None  # Qual bombsite o bot vai (índice)
        bot.alvo_inimigo = None  # Referência ao inimigo mais próximo
        bot.é_bomber = False  # Se este bot é o bomber do round
        bot.caminho = []  # Lista de pontos para pathfinding
        bot.ultimo_caminho = 0  # Tempo do último cálculo de caminho
        bot.spawn_x = x  # Posição inicial para resetar
        bot.spawn_y = y

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

    def _encontrar_bombsites(self):
        """Encontra todas as posições dos bombsites (tile 322) no mapa."""
        bombsites = []
        tile_alvo = 322

        # Percorrer todos os tiles do mapa
        for y in range(self.tilemap.altura):
            for x in range(self.tilemap.largura):
                tile_id = self.tilemap.get_tile(x, y)
                tile_id_base = tile_id & 0x1FFFFFFF

                if tile_id_base == tile_alvo:
                    # Converter para coordenadas de pixel (centro do tile)
                    px = x * self.tilemap.tile_largura + self.tilemap.tile_largura // 2
                    py = y * self.tilemap.tile_altura + self.tilemap.tile_altura // 2
                    bombsites.append((px, py))

        # Agrupar bombsites próximos em áreas (clusters)
        if bombsites:
            areas = self._agrupar_bombsites(bombsites)
            print(f"[BOMBSITES] {len(bombsites)} tiles agrupados em {len(areas)} áreas")
            return areas

        return [(self.tilemap.largura_pixels // 2, self.tilemap.altura_pixels // 2)]

    def _agrupar_bombsites(self, tiles):
        """Agrupa tiles próximos em áreas de bombsite."""
        import math

        if not tiles:
            return []

        # Usar clustering simples - agrupar por distância
        areas = []
        tiles_restantes = list(tiles)
        distancia_agrupamento = 100  # Tiles a menos de 100px são do mesmo bombsite

        while tiles_restantes:
            # Começar nova área com primeiro tile
            area_tiles = [tiles_restantes.pop(0)]

            # Encontrar todos os tiles próximos
            mudou = True
            while mudou:
                mudou = False
                for tile in tiles_restantes[:]:
                    for area_tile in area_tiles:
                        dist = math.sqrt((tile[0] - area_tile[0])**2 + (tile[1] - area_tile[1])**2)
                        if dist < distancia_agrupamento:
                            area_tiles.append(tile)
                            tiles_restantes.remove(tile)
                            mudou = True
                            break

            # Calcular centro da área
            centro_x = sum(t[0] for t in area_tiles) // len(area_tiles)
            centro_y = sum(t[1] for t in area_tiles) // len(area_tiles)
            areas.append((centro_x, centro_y))

        return areas

    def _criar_mapa_navegacao(self):
        """Cria um grid de pontos navegáveis no mapa."""
        nav_grid = []
        ESPACAMENTO = 32  # Verificar a cada 32 pixels

        for y in range(0, self.tilemap.altura_pixels, ESPACAMENTO):
            for x in range(0, self.tilemap.largura_pixels, ESPACAMENTO):
                # Verificar se o ponto é caminhável (não sólido)
                centro_x = x + TAMANHO_MULTIPLAYER // 2
                centro_y = y + TAMANHO_MULTIPLAYER // 2

                # Verificar o centro e as bordas
                if self._ponto_navegavel(centro_x, centro_y):
                    nav_grid.append((x, y))

        return nav_grid

    def _ponto_navegavel(self, x, y):
        """Verifica se um ponto é navegável (bot cabe e não é sólido)."""
        # Verificar múltiplos pontos para garantir que o bot cabe
        margem = TAMANHO_MULTIPLAYER // 2 + 4
        pontos = [
            (x, y),
            (x - margem, y - margem),
            (x + margem, y - margem),
            (x - margem, y + margem),
            (x + margem, y + margem),
        ]

        for px, py in pontos:
            if self.tilemap.is_solid(px, py):
                return False

        return True

    def _criar_pontos_estrategicos(self):
        """Cria pontos estratégicos para cada time baseado nos spawns e bombsites."""
        # Pontos de defesa (Time Q) - ao redor dos bombsites
        for bombsite in self.bombsites:
            # Adicionar pontos ao redor do bombsite
            for angulo in range(0, 360, 45):
                import math
                rad = math.radians(angulo)
                for dist in [60, 100, 140]:
                    px = int(bombsite[0] + math.cos(rad) * dist)
                    py = int(bombsite[1] + math.sin(rad) * dist)
                    if self._ponto_navegavel(px, py):
                        self.pontos_time_q.append((px, py))

        # Pontos de ataque (Time T) - caminho para os bombsites
        spawn_t = self.tilemap.get_objeto("Start_T")
        if spawn_t:
            spawn_centro = (spawn_t['x'] + spawn_t['width'] // 2,
                           spawn_t['y'] + spawn_t['height'] // 2)

            # Criar pontos intermediários entre spawn e cada bombsite
            for bombsite in self.bombsites:
                for t in [0.25, 0.5, 0.75]:
                    px = int(spawn_centro[0] + (bombsite[0] - spawn_centro[0]) * t)
                    py = int(spawn_centro[1] + (bombsite[1] - spawn_centro[1]) * t)
                    # Encontrar ponto navegável mais próximo
                    ponto_nav = self._encontrar_ponto_navegavel_proximo(px, py)
                    if ponto_nav:
                        self.pontos_time_t.append(ponto_nav)

        # Adicionar bombsites como destino final para Time T
        for bombsite in self.bombsites:
            ponto_nav = self._encontrar_ponto_navegavel_proximo(bombsite[0], bombsite[1])
            if ponto_nav:
                self.pontos_time_t.append(ponto_nav)

        print(f"[NAV] Pontos Time T: {len(self.pontos_time_t)}, Time Q: {len(self.pontos_time_q)}")

    def _encontrar_ponto_navegavel_proximo(self, x, y):
        """Encontra o ponto navegável mais próximo de uma posição."""
        import math

        if not self.nav_grid:
            return None

        menor_dist = float('inf')
        ponto_proximo = None

        for ponto in self.nav_grid:
            dist = math.sqrt((ponto[0] - x)**2 + (ponto[1] - y)**2)
            if dist < menor_dist:
                menor_dist = dist
                ponto_proximo = ponto

        return ponto_proximo

    def _atualizar_jogador_com_colisao(self, pos_mouse, tempo_atual):
        """Atualiza o jogador com verificação de colisão do mapa."""
        import math

        if self.jogador.vidas <= 0:
            return

        # Bloquear movimento durante tempo de compra
        if self.em_tempo_compra:
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

        # Normalizar APENAS movimento diagonal (quando ambos X e Y são pressionados)
        # Isso evita que diagonal seja mais rápido que cardinal
        if mov_x != 0 and mov_y != 0:
            # Diagonal: dividir por sqrt(2) para manter mesma velocidade
            mov_x *= 0.7071  # 1/sqrt(2) ≈ 0.7071
            mov_y *= 0.7071

        # Usar velocidade do jogador (permite modificação por habilidades de classe)
        velocidade = getattr(self.jogador, 'velocidade', 2.0)
        # Garantir velocidade mínima de 2.0 se não estiver definida corretamente
        if velocidade < 0.5:
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

        # ====== CYAN TURBO - RASTRO ======
        # Salvar posição para o rastro quando turbo está ativo
        if self.classe_jogador == "cyan" and self.habilidade_ativa:
            if hasattr(self.jogador, 'posicoes_turbo'):
                self.jogador.posicoes_turbo.insert(0, (novo_x, novo_y))
                # Limitar a 15 posições
                if len(self.jogador.posicoes_turbo) > 15:
                    self.jogador.posicoes_turbo.pop()

        # Atualizar outros aspectos do jogador
        self.jogador.atualizar()

    def _converter_mouse_para_mundo(self, pos_mouse):
        """Converte posição do mouse na tela para coordenadas do mundo (considerando zoom)."""
        # Converter posição da tela para coordenadas do mundo
        mundo_x = pos_mouse[0] / self.camera_zoom + self.camera_x
        mundo_y = pos_mouse[1] / self.camera_zoom + self.camera_y
        return (mundo_x, mundo_y)

    def _atualizar_camera(self):
        """Atualiza a posição da câmera para seguir o jogador (ou aliado se espectador)."""
        # Dimensões da tela com zoom aplicado
        largura_visivel = LARGURA / self.camera_zoom
        altura_visivel = ALTURA_JOGO / self.camera_zoom

        # Centro da tela (em coordenadas do mundo)
        centro_x = largura_visivel / 2
        centro_y = altura_visivel / 2

        # Determinar alvo da câmera
        alvo_x = self.jogador.x
        alvo_y = self.jogador.y

        # Se jogador morreu, ativar modo espectador
        if self.jogador.vidas <= 0:
            tempo_atual = pygame.time.get_ticks()

            # Primeira vez que detecta morte - registrar tempo
            if not self.espectador_ativo:
                self.espectador_ativo = True
                self.espectador_tempo_morte = tempo_atual
                self.espectador_alvo_idx = 0

            # Após o delay, seguir um aliado vivo
            if tempo_atual - self.espectador_tempo_morte >= self.espectador_delay:
                aliado = self._obter_aliado_espectador()
                if aliado:
                    alvo_x = aliado.x
                    alvo_y = aliado.y

        # Câmera segue o alvo
        self.camera_x = alvo_x - centro_x
        self.camera_y = alvo_y - centro_y

        # Limitar câmera aos limites do mapa
        self.camera_x = max(0, min(self.camera_x, self.tilemap.largura_pixels - largura_visivel))
        self.camera_y = max(0, min(self.camera_y, self.tilemap.altura_pixels - altura_visivel))

    def _obter_aliado_espectador(self):
        """Retorna o bot que a câmera deve seguir no modo espectador."""
        # Filtrar todos os bots vivos (de qualquer time)
        bots_vivos = [
            bot for bot in self.bots_locais
            if bot.vidas > 0
        ]

        if not bots_vivos:
            return None

        # Ajustar índice se necessário
        if self.espectador_alvo_idx >= len(bots_vivos):
            self.espectador_alvo_idx = 0

        return bots_vivos[self.espectador_alvo_idx]

    def _alternar_espectador(self):
        """Alterna para o próximo bot vivo no modo espectador."""
        if not self.espectador_ativo or self.jogador.vidas > 0:
            return

        # Contar todos os bots vivos
        bots_vivos = [
            bot for bot in self.bots_locais
            if bot.vidas > 0
        ]

        if len(bots_vivos) > 0:
            self.espectador_alvo_idx = (self.espectador_alvo_idx + 1) % len(bots_vivos)
            bot = bots_vivos[self.espectador_alvo_idx]
            time_bot = getattr(bot, 'time', '?')
            print(f"[ESPECTADOR] Observando: {bot.nome} (Time {time_bot})")

    # ==================================================================================
    # ================================ SISTEMA DE IA v2.0 =============================
    # ==================================================================================


    IA_DISTANCIA_VISAO = 200      # Distância máxima para detectar inimigos
    IA_DISTANCIA_TIRO = 180       # Distância máxima para atirar
    IA_WAYPOINT_THRESHOLD = 20    # Distância para considerar waypoint alcançado
    IA_STUCK_TEMPO = 500          # Tempo em ms para verificar stuck
    IA_STUCK_DISTANCIA = 5        # Distância mínima para não ser considerado stuck
    IA_STUCK_MAX = 3              # Vezes seguidas parado para ser considerado stuck
    IA_RECALC_INTERVALO = 2000    # Intervalo mínimo entre recálculos de rota (ms)

    # ==================== NAVEGAÇÃO SIMPLIFICADA (SEM A* PESADO) ====================

    def _criar_caminho_simples(self, inicio, destino):
        """
        Cria um caminho simples do início ao destino.
        Usa apenas o destino como waypoint (navegação direta com desvio local).

        Args:
            inicio: Tupla (x, y) posição inicial
            destino: Tupla (x, y) posição destino

        Returns:
            Lista com o destino como único waypoint
        """
        if not destino:
            return []
        return [destino]

    # ==================== SELEÇÃO DE TILE 322 ====================

    def _obter_tiles_322(self):
        """
        Encontra todas as posições dos tiles com ID 322 no mapa.

        Returns:
            Lista de tuplas (x, y) com coordenadas de mundo dos tiles 322
        """
        tiles_322 = []
        TILE_ALVO = 322

        for y in range(self.tilemap.altura):
            for x in range(self.tilemap.largura):
                tile_id = self.tilemap.get_tile(x, y)
                tile_id_base = tile_id & 0x1FFFFFFF  # Remove flags de rotação

                if tile_id_base == TILE_ALVO:
                    # Converter para coordenadas de mundo (centro do tile)
                    px = x * self.tilemap.tile_largura + self.tilemap.tile_largura // 2
                    py = y * self.tilemap.tile_altura + self.tilemap.tile_altura // 2
                    tiles_322.append((px, py))

        return tiles_322

    def _encontrar_tile_322_mais_proximo(self, bot):
        """
        Encontra o tile 322 mais próximo do bot.

        Args:
            bot: Referência ao bot

        Returns:
            Tupla (x, y) do tile mais próximo ou None se não existir
        """
        import math

        tiles = self._obter_tiles_322()
        if not tiles:
            # Fallback para bombsites se tiles 322 não encontrados
            if self.bombsites:
                tiles = self.bombsites

        if not tiles:
            return None

        menor_dist = float('inf')
        tile_proximo = None

        for tile in tiles:
            dist = math.sqrt((tile[0] - bot.x)**2 + (tile[1] - bot.y)**2)
            if dist < menor_dist:
                menor_dist = dist
                tile_proximo = tile

        return tile_proximo

    def _escolher_outro_tile_322(self, bot, tile_atual):
        """
        Escolhe outro tile 322 diferente do atual (usado quando preso).

        Args:
            bot: Referência ao bot
            tile_atual: Tile que deve ser evitado

        Returns:
            Tupla (x, y) de outro tile ou o mais próximo se só houver um
        """
        import math
        import random

        tiles = self._obter_tiles_322()
        if not tiles:
            if self.bombsites:
                tiles = list(self.bombsites)
            else:
                return None

        # Filtrar o tile atual
        tiles_disponiveis = [t for t in tiles if t != tile_atual]

        if not tiles_disponiveis:
            # Se só tem um tile, retornar ele mesmo
            return tile_atual

        # Escolher aleatoriamente entre os disponíveis (com peso para mais próximos)
        tiles_com_dist = []
        for tile in tiles_disponiveis:
            dist = math.sqrt((tile[0] - bot.x)**2 + (tile[1] - bot.y)**2)
            tiles_com_dist.append((tile, dist))

        # Ordenar por distância e pegar um dos 3 mais próximos
        tiles_com_dist.sort(key=lambda x: x[1])
        candidatos = tiles_com_dist[:min(3, len(tiles_com_dist))]

        return random.choice(candidatos)[0]

    # ==================== SISTEMA DE VISÃO ====================

    def _tem_linha_de_visao(self, x1, y1, x2, y2):
        """
        Verifica se há linha de visão entre dois pontos (raycast tile a tile).

        Args:
            x1, y1: Ponto de origem
            x2, y2: Ponto de destino

        Returns:
            True se há linha de visão livre, False se há obstáculo
        """
        import math

        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1:
            return True

        # Normalizar direção
        dx /= dist
        dy /= dist

        # Verificar a cada 8 pixels (resolução do raycast)
        passos = int(dist / 8)
        for i in range(1, passos + 1):
            check_x = x1 + dx * (i * 8)
            check_y = y1 + dy * (i * 8)
            if self.tilemap.is_solid(check_x, check_y):
                return False

        return True

    def _pode_ver_inimigo(self, bot, alvo):
        """
        Verifica se o bot pode ver um inimigo (distância + linha de visão).

        Args:
            bot: Bot que está olhando
            alvo: Entidade alvo (jogador ou outro bot)

        Returns:
            Tupla (pode_ver: bool, distancia: float)
        """
        import math

        bot_cx = bot.x + TAMANHO_MULTIPLAYER // 2
        bot_cy = bot.y + TAMANHO_MULTIPLAYER // 2
        alvo_cx = alvo.x + TAMANHO_MULTIPLAYER // 2
        alvo_cy = alvo.y + TAMANHO_MULTIPLAYER // 2

        # Calcular distância
        dist = math.sqrt((alvo_cx - bot_cx)**2 + (alvo_cy - bot_cy)**2)

        # Verificar se está dentro do raio de visão
        if dist > self.IA_DISTANCIA_VISAO:
            return False, dist

        # Verificar linha de visão
        if not self._tem_linha_de_visao(bot_cx, bot_cy, alvo_cx, alvo_cy):
            return False, dist

        return True, dist

    # ==================== STUCK DETECTION ====================

    def _ia_verificar_stuck(self, bot, tempo_atual):
        """
        Verifica se o bot está preso (não está se movendo).

        Critérios:
        - Verifica a cada IA_STUCK_TEMPO ms
        - Se moveu menos que IA_STUCK_DISTANCIA pixels
        - Se aconteceu IA_STUCK_MAX vezes seguidas -> está stuck

        Args:
            bot: Bot a verificar
            tempo_atual: Tempo atual em ms

        Returns:
            True se o bot está preso, False caso contrário
        """
        import math

        # Inicializar variáveis de stuck se não existirem
        if not hasattr(bot, 'ia_pos_anterior'):
            bot.ia_pos_anterior = (bot.x, bot.y)
            bot.ia_tempo_pos_anterior = tempo_atual
            bot.ia_stuck_contador = 0
            return False

        # Verificar apenas a cada intervalo definido
        if tempo_atual - bot.ia_tempo_pos_anterior < self.IA_STUCK_TEMPO:
            return bot.ia_stuck_contador >= self.IA_STUCK_MAX

        # Calcular distância movida desde última verificação
        dist_movida = math.sqrt(
            (bot.x - bot.ia_pos_anterior[0])**2 +
            (bot.y - bot.ia_pos_anterior[1])**2
        )

        # Se moveu menos que o mínimo, incrementar contador
        if dist_movida < self.IA_STUCK_DISTANCIA:
            bot.ia_stuck_contador += 1
        else:
            # Se moveu, decrementar contador (mas não abaixo de 0)
            bot.ia_stuck_contador = max(0, bot.ia_stuck_contador - 1)

        # Atualizar posição e tempo anterior
        bot.ia_pos_anterior = (bot.x, bot.y)
        bot.ia_tempo_pos_anterior = tempo_atual

        return bot.ia_stuck_contador >= self.IA_STUCK_MAX

    def _ia_recuperar_stuck(self, bot, tempo_atual):
        """
        Recupera o bot quando está preso.

        Ações:
        1. Limpar caminho atual
        2. Escolher outro tile 322 como alvo
        3. Recalcular rota
        4. Se falhar, forçar movimento em direção livre

        Args:
            bot: Bot preso
            tempo_atual: Tempo atual em ms
        """
        import math

        # Resetar contador e estado
        bot.ia_stuck_contador = 0
        bot.ia_estado = 'recalculando_rota'

        # Limpar caminho atual
        bot.ia_caminho = []
        bot.ia_waypoint_atual = 0

        # Tentar escolher outro tile 322
        tile_atual = getattr(bot, 'ia_tile_alvo', None)
        novo_tile = self._escolher_outro_tile_322(bot, tile_atual)

        if novo_tile:
            bot.ia_tile_alvo = novo_tile

            # Recalcular caminho para novo alvo
            caminho = self._criar_caminho_simples((bot.x, bot.y), novo_tile)

            if caminho and len(caminho) > 1:
                bot.ia_caminho = caminho
                bot.ia_waypoint_atual = 0
                bot.ia_estado = 'movendo'
                bot.ia_ultimo_recalculo = tempo_atual
                print(f"[IA] {bot.nome} recalculou rota para novo tile 322")
                return

        # Se não conseguiu rota, forçar movimento em direção livre
        self._ia_forcar_movimento_livre(bot)

    def _ia_forcar_movimento_livre(self, bot):
        """
        Força movimento em uma direção livre quando todas outras opções falham.

        Se está em loop (muitas tentativas), usa wandering que move diretamente.

        Args:
            bot: Bot a mover
        """
        tempo_atual = pygame.time.get_ticks()

        # Incrementar contador de tentativas
        bot.ia_tentativas_escape = getattr(bot, 'ia_tentativas_escape', 0) + 1

        # Se está em loop (mais de 2 tentativas), usar wandering que move diretamente
        if bot.ia_tentativas_escape > 2:
            self._ia_wandering_aleatorio(bot, tempo_atual)
            return

        # Tentar ir para rota do devmode mais próxima
        ponto_rota, rota_idx, waypoint_idx = self._encontrar_ponto_rota_acessivel(bot, dist_maxima=500, retornar_info_rota=True)
        if ponto_rota:
            # Mover diretamente na direção da rota também
            self._ia_mover_direto(bot, ponto_rota)

            # Pegar rotas do time do bot
            rotas_time = self.dev_rotas_t if bot.time == 'T' else self.dev_rotas_q

            # === RESETAR TODOS OS CONTADORES DE BLOQUEIO ===
            bot.ia_bloqueado_contador = 0
            bot.ia_tempo_parado = tempo_atual
            bot.ia_pos_parado = (bot.x, bot.y)
            bot.ia_tentativas_escape = 0  # Resetar tentativas

            # Configurar para seguir a rota a partir do waypoint encontrado
            bot.ia_rota_idx = rota_idx
            bot.ia_caminho = list(rotas_time[rota_idx][waypoint_idx:])  # Rota a partir do waypoint
            bot.ia_waypoint_atual = 0
            bot.ia_estado = 'movendo'
            bot.ia_tempo_inicio_rota = tempo_atual
            # Ativar modo escape por 3 segundos (mais tempo para chegar)
            bot.ia_modo_escape = True
            bot.ia_escape_tempo_fim = tempo_atual + 3000
            print(f"[IA] {bot.nome} preso, entrando na rota {rota_idx+1} waypoint {waypoint_idx+1}")
            return

        # Fallback: usar wandering aleatório
        self._ia_wandering_aleatorio(bot, tempo_atual)

    # ==================== MÁQUINA DE ESTADOS DA IA ====================

    def _ia_inicializar_bot(self, bot):
        """
        Inicializa os atributos de IA de um bot.
        Deve ser chamado quando o bot é criado.

        Args:
            bot: Bot a inicializar
        """
        # Estado da máquina de estados
        bot.ia_estado = 'spawn'

        # Pathfinding
        bot.ia_caminho = []           # Lista de waypoints [(x,y), ...]
        bot.ia_waypoint_atual = 0     # Índice do waypoint atual
        bot.ia_tile_alvo = None       # Tile 322 atual como alvo
        bot.ia_ultimo_recalculo = 0   # Tempo do último recálculo de rota

        # Stuck detection
        bot.ia_pos_anterior = (bot.x, bot.y)
        bot.ia_tempo_pos_anterior = 0
        bot.ia_stuck_contador = 0

        # Detecção de parado (para escolher novo destino)
        bot.ia_tempo_parado = pygame.time.get_ticks()
        bot.ia_pos_parado = (bot.x, bot.y)

        # Timeout de rota (resetar se não chegar em 10 segundos)
        bot.ia_tempo_inicio_rota = pygame.time.get_ticks()

        # Detecção de bloqueio (forçando movimento sem conseguir)
        bot.ia_bloqueado_contador = 0

        # Contador de tentativas de escape (para detectar loop)
        bot.ia_tentativas_escape = 0

        # Modo escape (quando está tentando sair de onde está preso)
        bot.ia_modo_escape = False
        bot.ia_escape_tempo_fim = 0

        # Rota do devmode
        bot.ia_rota_idx = None

        # Flags de ação
        bot.bot_defusando = False
        bot.bot_plantando = False

        # Movimento suavizado
        bot.ia_vel_x = 0
        bot.ia_vel_y = 0
        bot.ia_dir_x = 0
        bot.ia_dir_y = 0

        # Combate
        bot.ia_alvo_inimigo = None
        bot.ia_dist_inimigo = float('inf')

    def _atualizar_bots(self):
        """
        Loop principal de atualização da IA dos bots.

        Executa a máquina de estados para cada bot vivo.
        """
        import math
        tempo_atual = pygame.time.get_ticks()

        for bot in self.bots_locais[:]:
            # Bot morreu - pular
            if bot.vidas <= 0:
                continue

            # Inicializar IA se necessário
            if not hasattr(bot, 'ia_estado'):
                self._ia_inicializar_bot(bot)

            bot_time = getattr(bot, 'time', None)

            # === FASE DE COMPRA (estado especial) ===
            if self.em_tempo_compra:
                bot.ia_estado = 'spawn'
                bot.estado = 'comprando'  # Compatibilidade
                if not getattr(bot, 'ja_comprou', False):
                    self._bot_comprar_arma(bot)
                    bot.ja_comprou = True
                continue

            # === TIMEOUT DE SEGURANÇA - TELEPORT SE PRESO POR MUITO TEMPO ===
            # Se o bot está tentando escapar há mais de 5 segundos, teleportar para ponto seguro
            # IGNORAR se o bot está defusando a bomba
            if getattr(bot, 'bot_defusando', False):
                bot.ia_tempo_preso_total = 0
                bot.ia_tentativas_escape = 0

            tempo_preso_total = getattr(bot, 'ia_tempo_preso_total', 0)
            if getattr(bot, 'ia_tentativas_escape', 0) > 0 and not getattr(bot, 'bot_defusando', False):
                bot.ia_tempo_preso_total = tempo_preso_total + 16  # ~16ms por frame
                if bot.ia_tempo_preso_total > 5000:  # 5 segundos preso
                    # Encontrar ponto seguro em uma rota
                    rotas_time = self.dev_rotas_t if bot.time == 'T' else self.dev_rotas_q
                    if rotas_time and len(rotas_time) > 0:
                        import random
                        rota = random.choice(rotas_time)
                        if rota and len(rota) > 0:
                            ponto = random.choice(rota)
                            bot.x = ponto[0]
                            bot.y = ponto[1]
                            print(f"[IA] {bot.nome} TELEPORTADO para rota (preso por 5s+)")
                    # Resetar tudo
                    bot.ia_tempo_preso_total = 0
                    bot.ia_tentativas_escape = 0
                    bot.ia_bloqueado_contador = 0
                    bot.ia_modo_escape = False
                    bot.ia_tempo_parado = tempo_atual
                    bot.ia_pos_parado = (bot.x, bot.y)
                    continue
            else:
                bot.ia_tempo_preso_total = 0

            # === MODO ESCAPE - PRIORIDADE MÁXIMA ===
            # Se bot está em modo escape, ignorar TODAS outras lógicas e seguir para a rota
            # EXCEÇÃO: Time Q quando bomba plantada precisa ir defusar (prioridade ainda maior)
            if getattr(bot, 'ia_modo_escape', False):
                # Desativar escape se precisa defusar bomba
                if bot.time == 'Q' and self.bomba_plantada and not self.bomba_defusada:
                    bot.ia_modo_escape = False
                # Verificar se o modo escape expirou
                elif tempo_atual > getattr(bot, 'ia_escape_tempo_fim', 0):
                    bot.ia_modo_escape = False
                elif bot.ia_caminho and bot.ia_waypoint_atual < len(bot.ia_caminho):
                    # Seguir waypoint de escape - PRIORIDADE ABSOLUTA
                    self._ia_seguir_waypoints(bot, tempo_atual)
                    continue  # Pular TODAS outras lógicas
                else:
                    # Chegou ao destino, desativar modo escape
                    bot.ia_modo_escape = False
                    bot.ia_tentativas_escape = 0  # Resetar contador

            # === TRANSIÇÃO DE SPAWN PARA PATRULHANDO ===
            if bot.ia_estado == 'spawn':
                bot.ia_estado = 'patrulhando'
                # Resetar flags que podem estar travando o bot
                bot.bot_defusando = False
                bot.bot_plantando = False
                bot.ia_modo_escape = False
                bot.ia_tentativas_escape = 0
                bot.ia_bloqueado_contador = 0
                bot.ia_rota_idx = None  # Forçar escolha de nova rota
                bot.ia_caminho = []
                bot.ia_waypoint_atual = 0
                bot.ia_tempo_parado = tempo_atual
                bot.ia_pos_parado = (bot.x, bot.y)
                # Encontrar tile 322 mais próximo como alvo inicial
                bot.ia_tile_alvo = self._encontrar_tile_322_mais_proximo(bot)
                print(f"[IA] {bot.nome} saiu do spawn, iniciando patrulha")

            # === STUCK DETECTION ===
            # Ignorar stuck detection se o bot está defusando
            if not getattr(bot, 'bot_defusando', False):
                if self._ia_verificar_stuck(bot, tempo_atual):
                    bot.ia_estado = 'stuck'
                    self._ia_recuperar_stuck(bot, tempo_atual)

            # === DETECÇÃO DE INIMIGOS ===
            inimigo_visivel, dist_inimigo = self._ia_detectar_inimigo(bot, bot_time)
            bot.ia_alvo_inimigo = inimigo_visivel
            bot.ia_dist_inimigo = dist_inimigo
            bot.alvo_inimigo = inimigo_visivel  # Compatibilidade

            # === MÁQUINA DE ESTADOS ===
            if bot.ia_estado == 'stuck':
                # Estado temporário, já tratado acima
                bot.ia_estado = 'recalculando_rota'

            # === BOT ESTÁ DEFUSANDO BOMBA (PRIORIDADE MÁXIMA) ===
            elif getattr(bot, 'bot_defusando', False):
                # Bot fica parado defusando - não fazer nada mais
                # O defuse é processado em _processar_bomba
                pass

            # === BOT ESTÁ PLANTANDO BOMBA ===
            elif getattr(bot, 'bot_plantando', False):
                # Se inimigo se aproximou muito (< 150 pixels), cancelar plantio
                if inimigo_visivel and dist_inimigo < 150:
                    bot.bot_plantando = False
                    bot.ia_estado = 'atacando'
                    print(f"[BOMBA] {bot.nome} cancelou plantio - inimigo detectado!")
                    self._ia_estado_atacando(bot, tempo_atual)
                else:
                    # Continuar plantando (bot não se move)
                    self._bot_plantar_bomba(bot)

            elif inimigo_visivel and dist_inimigo < self.IA_DISTANCIA_VISAO:
                # EXCEÇÃO: Time Q com bomba plantada prioriza defuse sobre ataque
                # A menos que o inimigo esteja MUITO perto (< 100 pixels)
                if bot.time == 'Q' and self.bomba_plantada and not self.bomba_defusada and dist_inimigo > 100:
                    # Ir defusar ao invés de atacar
                    bot.ia_estado = 'patrulhando'
                    self._ia_estado_patrulhando(bot, tempo_atual)
                else:
                    # Inimigo visível - entrar em combate
                    bot.ia_estado = 'atacando'
                    bot.estado = 'atacando'  # Compatibilidade
                    self._ia_estado_atacando(bot, tempo_atual)

            elif bot.ia_estado == 'recalculando_rota':
                # Recalcular caminho
                self._ia_estado_recalculando(bot, tempo_atual)

            elif bot.ia_estado in ['patrulhando', 'movendo']:
                # Sem inimigo - patrulhar até tile 322
                bot.estado = 'patrulhando'  # Compatibilidade
                self._ia_estado_patrulhando(bot, tempo_atual)

            elif bot.ia_estado == 'atacando':
                # Estava atacando mas perdeu o alvo
                bot.ia_estado = 'patrulhando'

            # === ATIRAR SE EM COMBATE ===
            if inimigo_visivel and dist_inimigo < self.IA_DISTANCIA_TIRO:
                bot_cx = bot.x + TAMANHO_MULTIPLAYER // 2
                bot_cy = bot.y + TAMANHO_MULTIPLAYER // 2
                alvo_cx = inimigo_visivel.x + TAMANHO_MULTIPLAYER // 2
                alvo_cy = inimigo_visivel.y + TAMANHO_MULTIPLAYER // 2

                if self._tem_linha_de_visao(bot_cx, bot_cy, alvo_cx, alvo_cy):
                    self._bot_atirar(bot, inimigo_visivel, tempo_atual)

    def _ia_detectar_inimigo(self, bot, bot_time):
        """
        Detecta o inimigo visível mais próximo.

        Args:
            bot: Bot que está procurando
            bot_time: Time do bot

        Returns:
            Tupla (inimigo, distancia) ou (None, inf)
        """
        inimigo_visivel = None
        menor_distancia = float('inf')

        # Verificar jogador (se for do time oposto e não invisível)
        jogador_invisivel = getattr(self.jogador, 'invisivel', False)
        if self.jogador.vidas > 0 and self.time_jogador != bot_time and not jogador_invisivel:
            pode_ver, dist = self._pode_ver_inimigo(bot, self.jogador)
            if pode_ver and dist < menor_distancia:
                menor_distancia = dist
                inimigo_visivel = self.jogador

        # Verificar outros bots (do time oposto)
        for outro_bot in self.bots_locais:
            if outro_bot == bot or outro_bot.vidas <= 0:
                continue
            outro_time = getattr(outro_bot, 'time', None)
            if outro_time == bot_time:
                continue

            pode_ver, dist = self._pode_ver_inimigo(bot, outro_bot)
            if pode_ver and dist < menor_distancia:
                menor_distancia = dist
                inimigo_visivel = outro_bot

        return inimigo_visivel, menor_distancia

    # ==================== ESTADOS DA IA ====================

    def _ia_estado_patrulhando(self, bot, tempo_atual):
        """
        Estado PATRULHANDO: Bot segue as rotas desenhadas no DEV MODE.

        Comportamento:
        1. Se há rotas desenhadas para o time do bot, escolher uma e seguir
        2. Se não há rotas, usar navegação simples para tile 322
        3. Ao terminar rota, escolher outra
        """
        import math
        import random

        # === DESATIVAR ESCAPE SE PRECISA DEFUSAR (prioridade máxima) ===
        if bot.time == 'Q' and self.bomba_plantada and not self.bomba_defusada:
            bot.ia_modo_escape = False

        # === TIME Q: PRIORIDADE DEFUSE SE BOMBA PLANTADA ===
        if bot.time == 'Q' and self.bomba_plantada and not self.bomba_defusada:
            # Bot do time Q vai correndo para a bomba para defusar
            if self.bomba_posicao:
                dist_bomba = math.sqrt((bot.x - self.bomba_posicao[0])**2 +
                                       (bot.y - self.bomba_posicao[1])**2)

                # Se está perto da bomba, começar a defusar
                if dist_bomba < 30:
                    # Marcar que está defusando (para visual)
                    bot.bot_defusando = True
                    # Bot fica parado defusando
                    return
                else:
                    # Verificar posições da bomba e do bot em relação aos sites
                    bomba_no_site_A = False
                    bomba_no_site_B = False
                    bot_perto_site_B = False

                    if hasattr(self, 'bombsites') and len(self.bombsites) >= 2:
                        # Distância da bomba até cada site
                        dist_bomba_site_A = math.sqrt((self.bomba_posicao[0] - self.bombsites[0][0])**2 +
                                                      (self.bomba_posicao[1] - self.bombsites[0][1])**2)
                        dist_bomba_site_B = math.sqrt((self.bomba_posicao[0] - self.bombsites[1][0])**2 +
                                                      (self.bomba_posicao[1] - self.bombsites[1][1])**2)

                        # Distância do bot até cada site
                        dist_bot_site_B = math.sqrt((bot.x - self.bombsites[1][0])**2 +
                                                    (bot.y - self.bombsites[1][1])**2)

                        bomba_no_site_A = dist_bomba_site_A < 150
                        bomba_no_site_B = dist_bomba_site_B < 150
                        bot_perto_site_B = dist_bot_site_B < 200  # Bot está perto do site B

                    # CASO 1: Bomba no site A e bot perto do site B -> usar rota q10 (índice 9)
                    if bomba_no_site_A and bot_perto_site_B and dist_bomba > 200 and len(self.dev_rotas_q) >= 10:
                        if not hasattr(bot, 'ia_rota_idx') or bot.ia_rota_idx != 9 or not bot.ia_caminho:
                            bot.ia_rota_idx = 3
                            bot.ia_caminho = list(self.dev_rotas_q[3])
                            bot.ia_waypoint_atual = 0
                            bot.ia_tempo_inicio_rota = tempo_atual
                            print(f"[IA] {bot.nome} priorizando rota Q10 (bot no B, bomba no A)")

                        if bot.ia_caminho and bot.ia_waypoint_atual < len(bot.ia_caminho):
                            self._ia_seguir_waypoints(bot, tempo_atual)
                            return

                    # CASO 2: Bomba no site B e bot longe -> usar rota q6 (índice 5)
                    elif bomba_no_site_B and dist_bomba > 200 and len(self.dev_rotas_q) >= 6:
                        if not hasattr(bot, 'ia_rota_idx') or bot.ia_rota_idx != 5 or not bot.ia_caminho:
                            bot.ia_rota_idx = 5
                            bot.ia_caminho = list(self.dev_rotas_q[5])
                            bot.ia_waypoint_atual = 0
                            bot.ia_tempo_inicio_rota = tempo_atual
                            print(f"[IA] {bot.nome} priorizando rota Q6 para bomba no site B")

                        if bot.ia_caminho and bot.ia_waypoint_atual < len(bot.ia_caminho):
                            self._ia_seguir_waypoints(bot, tempo_atual)
                            return

                    # Ir direto para a bomba (quando perto ou sem rota especial)
                    bot.bot_defusando = False
                    self._ia_mover_direto(bot, self.bomba_posicao)
                    return

        # === TIME T: PEGAR BOMBA DROPADA ===
        if bot.time == 'T' and self.bomba_dropada and self.bomba_drop_posicao:
            # Bot do time T vai correndo para pegar a bomba
            dist_bomba = math.sqrt((bot.x - self.bomba_drop_posicao[0])**2 +
                                   (bot.y - self.bomba_drop_posicao[1])**2)

            # Ir direto para a bomba
            if dist_bomba > 25:
                self._ia_mover_direto(bot, self.bomba_drop_posicao)
                return

        # === TIME T: GUARDAR BOMBA PLANTADA ===
        if bot.time == 'T' and self.bomba_plantada and not self.bomba_defusada:
            if self.bomba_posicao:
                dist_bomba = math.sqrt((bot.x - self.bomba_posicao[0])**2 +
                                       (bot.y - self.bomba_posicao[1])**2)

                # Se está perto da bomba (< 150 pixels), ficar guardando
                if dist_bomba < 150:
                    # Ficar na região, não se distanciar
                    # Apenas se movimenta levemente para não ficar totalmente parado
                    if not hasattr(bot, 'ia_tempo_guard') or tempo_atual - bot.ia_tempo_guard > 2000:
                        # A cada 2 segundos, escolher uma posição próxima da bomba
                        angulo = random.uniform(0, 2 * math.pi)
                        raio = random.uniform(30, 100)
                        novo_x = self.bomba_posicao[0] + math.cos(angulo) * raio
                        novo_y = self.bomba_posicao[1] + math.sin(angulo) * raio
                        bot.ia_pos_guard = (novo_x, novo_y)
                        bot.ia_tempo_guard = tempo_atual

                    # Mover para posição de guarda
                    if hasattr(bot, 'ia_pos_guard'):
                        self._ia_mover_direto(bot, bot.ia_pos_guard)
                    return

        # === DETECÇÃO DE BOT PARADO POR 2 SEGUNDOS ===
        # Ignorar se o bot está defusando a bomba (deve ficar parado)
        if getattr(bot, 'bot_defusando', False):
            bot.ia_tempo_parado = tempo_atual
            bot.ia_pos_parado = (bot.x, bot.y)
        else:
            dist_desde_parado = math.sqrt((bot.x - bot.ia_pos_parado[0])**2 +
                                          (bot.y - bot.ia_pos_parado[1])**2)

            # Se moveu mais de 15 pixels, resetar tempo parado e contador de escape
            if dist_desde_parado > 15:
                bot.ia_pos_parado = (bot.x, bot.y)
                bot.ia_tempo_parado = tempo_atual
                bot.ia_tentativas_escape = 0  # Resetar contador quando consegue se mover
            elif bot.ia_tempo_parado > 0 and tempo_atual - bot.ia_tempo_parado > 2000:
                # Se não moveu por 2 segundos, tentar escapar
                bot.ia_tempo_parado = tempo_atual
                bot.ia_pos_parado = (bot.x, bot.y)
                bot.ia_tentativas_escape = getattr(bot, 'ia_tentativas_escape', 0) + 1

                # Se está em loop (mais de 3 tentativas), fazer wandering
                if bot.ia_tentativas_escape > 3:
                    self._ia_wandering_aleatorio(bot, tempo_atual)
                    return

                # Procurar ponto de rota mais próximo (busca até 500 pixels)
                ponto_proximo, rota_idx, waypoint_idx = self._encontrar_ponto_rota_acessivel(bot, dist_maxima=500, retornar_info_rota=True)

                if ponto_proximo:
                    # Verificar distância real do ponto
                    dist_ponto = math.sqrt((bot.x - ponto_proximo[0])**2 + (bot.y - ponto_proximo[1])**2)

                    # Se o ponto está longe (> 150px), fazer wandering ao invés de ir para rota
                    if dist_ponto > 150:
                        print(f"[IA] {bot.nome} parado por 2s, ponto de rota longe ({dist_ponto:.0f}px), movimento livre")
                        self._ia_wandering_aleatorio(bot, tempo_atual)
                        return

                    # Pegar rotas do time do bot
                    rotas_time = self.dev_rotas_t if bot.time == 'T' else self.dev_rotas_q

                    # === RESETAR TODOS OS CONTADORES DE BLOQUEIO ===
                    bot.ia_bloqueado_contador = 0
                    bot.ia_tentativas_escape = 0
                    bot.ia_tempo_parado = tempo_atual
                    bot.ia_pos_parado = (bot.x, bot.y)

                    # Configurar para seguir a rota a partir do waypoint encontrado
                    bot.ia_rota_idx = rota_idx
                    bot.ia_caminho = list(rotas_time[rota_idx][waypoint_idx:])  # Rota a partir do waypoint
                    bot.ia_waypoint_atual = 0
                    bot.ia_tempo_inicio_rota = tempo_atual
                    # Ativar modo escape por 2 segundos
                    bot.ia_modo_escape = True
                    bot.ia_escape_tempo_fim = tempo_atual + 2000
                    print(f"[IA] {bot.nome} parado por 2s, entrando na rota {rota_idx+1} no waypoint {waypoint_idx+1} ({dist_ponto:.0f}px)")
                    return
                else:
                    # Nenhum ponto acessível, fazer wandering
                    self._ia_wandering_aleatorio(bot, tempo_atual)
                    return

        # === TIMEOUT DE ROTA (10 SEGUNDOS) ===
        # Ignorar timeout se o bot está defusando a bomba
        if not getattr(bot, 'bot_defusando', False):
            if hasattr(bot, 'ia_tempo_inicio_rota') and bot.ia_caminho:
                if tempo_atual - bot.ia_tempo_inicio_rota > 10000:
                    # Resetar rota e caminho para forçar escolha de novo destino
                    bot.ia_rota_idx = None
                    bot.ia_caminho = []
                    bot.ia_waypoint_atual = 0
                    bot.ia_tile_alvo = None
                    bot.ia_tempo_inicio_rota = tempo_atual
                    bot.ia_tempo_parado = tempo_atual
                    bot.ia_pos_parado = (bot.x, bot.y)
                    print(f"[IA] {bot.nome} não chegou em 10s, escolhendo nova rota")

        # === DETECÇÃO DE BLOQUEIO (forçando movimento sem conseguir) ===
        # Ignorar se o bot está defusando a bomba
        if getattr(bot, 'bot_defusando', False):
            bot.ia_bloqueado_contador = 0
        elif getattr(bot, 'ia_bloqueado_contador', 0) >= 30:  # ~0.5 segundo bloqueado
            bot.ia_bloqueado_contador = 0
            bot.ia_tentativas_escape = getattr(bot, 'ia_tentativas_escape', 0) + 1

            # Se está em loop (mais de 3 tentativas), fazer wandering
            if bot.ia_tentativas_escape > 3:
                self._ia_wandering_aleatorio(bot, tempo_atual)
                return

            # Procurar ponto de rota mais próximo acessível (busca até 500 pixels)
            ponto_proximo, rota_idx, waypoint_idx = self._encontrar_ponto_rota_acessivel(bot, dist_maxima=500, retornar_info_rota=True)

            if ponto_proximo:
                # Verificar distância real do ponto
                dist_ponto = math.sqrt((bot.x - ponto_proximo[0])**2 + (bot.y - ponto_proximo[1])**2)

                # Se o ponto está longe (> 150px), fazer wandering ao invés de ir para rota
                if dist_ponto > 150:
                    print(f"[IA] {bot.nome} bloqueado, ponto de rota longe ({dist_ponto:.0f}px), movimento livre")
                    self._ia_wandering_aleatorio(bot, tempo_atual)
                    return

                # Pegar rotas do time do bot
                rotas_time = self.dev_rotas_t if bot.time == 'T' else self.dev_rotas_q

                # === RESETAR TODOS OS CONTADORES DE BLOQUEIO ===
                bot.ia_bloqueado_contador = 0
                bot.ia_tentativas_escape = 0
                bot.ia_tempo_parado = tempo_atual
                bot.ia_pos_parado = (bot.x, bot.y)

                # Configurar para seguir a rota a partir do waypoint encontrado
                bot.ia_rota_idx = rota_idx
                bot.ia_caminho = list(rotas_time[rota_idx][waypoint_idx:])  # Rota a partir do waypoint
                bot.ia_waypoint_atual = 0
                bot.ia_tempo_inicio_rota = tempo_atual
                # Ativar modo escape por 2 segundos
                bot.ia_modo_escape = True
                bot.ia_escape_tempo_fim = tempo_atual + 2000
                print(f"[IA] {bot.nome} bloqueado, entrando na rota {rota_idx+1} no waypoint {waypoint_idx+1} ({dist_ponto:.0f}px)")
                return
            else:
                # Nenhum ponto próximo acessível, fazer wandering
                self._ia_wandering_aleatorio(bot, tempo_atual)
                return

        # === SELECIONAR ROTAS DO TIME DO BOT ===
        if hasattr(bot, 'time') and bot.time == 'T':
            rotas_time = self.dev_rotas_t
        else:
            rotas_time = self.dev_rotas_q

        # === USAR ROTAS DESENHADAS NO DEV MODE ===
        if rotas_time and len(rotas_time) > 0:
            # Se não tem rota atribuída, escolher uma
            if not hasattr(bot, 'ia_rota_idx') or bot.ia_rota_idx is None:
                # BOMBER: só escolhe rota 1 ou 2 (índices 0 ou 1)
                if getattr(bot, 'é_bomber', False) and len(rotas_time) >= 2:
                    bot.ia_rota_idx = random.randint(0, 1)  # Apenas rotas 1 ou 2
                    print(f"[IA] {bot.nome} (BOMBER) seguindo rota {bot.ia_rota_idx + 1}")
                else:
                    bot.ia_rota_idx = random.randint(0, len(rotas_time) - 1)
                    print(f"[IA] {bot.nome} (Time {bot.time}) seguindo rota {bot.ia_rota_idx + 1}")
                bot.ia_caminho = list(rotas_time[bot.ia_rota_idx])
                bot.ia_waypoint_atual = 0
                bot.ia_tempo_inicio_rota = tempo_atual  # Resetar timer de rota

            # Se caminho acabou, escolher nova rota
            if not bot.ia_caminho or bot.ia_waypoint_atual >= len(bot.ia_caminho):
                # BOMBER: só escolhe rota 1 ou 2
                if getattr(bot, 'é_bomber', False) and len(rotas_time) >= 2:
                    rotas_disponiveis = [0, 1]
                else:
                    rotas_disponiveis = list(range(len(rotas_time)))
                if len(rotas_disponiveis) > 1 and bot.ia_rota_idx in rotas_disponiveis:
                    rotas_disponiveis.remove(bot.ia_rota_idx)
                bot.ia_rota_idx = random.choice(rotas_disponiveis)
                bot.ia_caminho = list(rotas_time[bot.ia_rota_idx])
                bot.ia_waypoint_atual = 0
                bot.ia_tempo_inicio_rota = tempo_atual  # Resetar timer de rota

            # === BOMBER: Verificar se está perto do tile 322 para plantar ===
            if getattr(bot, 'é_bomber', False) and not self.bomba_plantada:
                tile_322_pos = self._encontrar_tile_322_mais_proximo(bot)
                if tile_322_pos:
                    dist_bombsite = math.sqrt((bot.x - tile_322_pos[0])**2 + (bot.y - tile_322_pos[1])**2)

                    # Se está perto do bombsite (< 100 pixels)
                    if dist_bombsite < 100:
                        # Verificar se há inimigos muito perto (< 200 pixels)
                        inimigo_perto = False
                        for inimigo in self.bots_locais:
                            if inimigo.vidas <= 0 or getattr(inimigo, 'time', '') == bot.time:
                                continue
                            dist_inimigo = math.sqrt((bot.x - inimigo.x)**2 + (bot.y - inimigo.y)**2)
                            if dist_inimigo < 200:
                                inimigo_perto = True
                                break

                        # Verificar jogador também se for do time oposto
                        if self.time_jogador != bot.time and self.jogador.vidas > 0:
                            dist_jogador = math.sqrt((bot.x - self.jogador.x)**2 + (bot.y - self.jogador.y)**2)
                            if dist_jogador < 200:
                                inimigo_perto = True

                        # Se não há inimigos perto, ir para o tile 322 e plantar
                        if not inimigo_perto:
                            # Salvar posição do tile 322 para plantar exatamente lá
                            bot.tile_322_alvo = tile_322_pos

                            # Se está em cima do tile 322 (< 10 pixels), começar a plantar
                            if dist_bombsite < 10:
                                self._bot_plantar_bomba(bot, tile_322_pos)
                                return
                            else:
                                # Mover para exatamente em cima do tile 322
                                self._ia_mover_direto(bot, tile_322_pos)
                                return

            # Seguir waypoints da rota
            self._ia_seguir_waypoints(bot, tempo_atual)
            return

        # === FALLBACK: NAVEGAÇÃO PARA TILE 322 (se não há rotas desenhadas) ===
        if not bot.ia_tile_alvo:
            bot.ia_tile_alvo = self._encontrar_tile_322_mais_proximo(bot)
            if not bot.ia_tile_alvo:
                return

        if not bot.ia_caminho or bot.ia_waypoint_atual >= len(bot.ia_caminho):
            if tempo_atual - bot.ia_ultimo_recalculo < self.IA_RECALC_INTERVALO:
                self._ia_mover_direto(bot, bot.ia_tile_alvo)
                return

            caminho = self._criar_caminho_simples((bot.x, bot.y), bot.ia_tile_alvo)
            if caminho:
                bot.ia_caminho = caminho
                bot.ia_waypoint_atual = 0
                bot.ia_ultimo_recalculo = tempo_atual
                bot.ia_estado = 'movendo'
            else:
                bot.ia_tile_alvo = self._escolher_outro_tile_322(bot, bot.ia_tile_alvo)
                bot.ia_ultimo_recalculo = tempo_atual
                return

        self._ia_seguir_waypoints(bot, tempo_atual)

        if bot.ia_tile_alvo:
            dist_alvo = math.sqrt(
                (bot.x - bot.ia_tile_alvo[0])**2 +
                (bot.y - bot.ia_tile_alvo[1])**2
            )
            if dist_alvo < 50:
                bot.ia_tile_alvo = self._escolher_outro_tile_322(bot, bot.ia_tile_alvo)
                bot.ia_caminho = []
                bot.ia_waypoint_atual = 0

    def _ia_estado_atacando(self, bot, tempo_atual):
        """
        Estado ATACANDO: Bot viu um inimigo e está em combate.

        Comportamento:
        1. Parar avanço ao tile 322
        2. Movimento de combate (strafe)
        3. Usar habilidade de classe (se disponível)
        4. Atirar (feito no loop principal)
        5. Retornar a patrulhar se perder o alvo
        """
        if not bot.ia_alvo_inimigo:
            bot.ia_estado = 'patrulhando'
            return

        # Tentar usar habilidade de classe (chance aleatória durante combate)
        self._bot_tentar_usar_habilidade(bot, tempo_atual)

        # Movimento de combate
        self._ia_mover_combate(bot, tempo_atual)

    def _bot_tentar_usar_habilidade(self, bot, tempo_atual):
        """
        Tenta usar a habilidade de classe do bot durante combate.
        Uso aleatório baseado em cooldown e situação.
        """
        from src.game.selecao_classes import obter_dados_classe
        import math

        classe = getattr(bot, 'classe', None)
        if not classe:
            return

        dados = obter_dados_classe(classe, bot.time)
        if not dados:
            return

        cooldown = dados.get('habilidade_cooldown', 0)
        if cooldown == 0:
            return  # Classe sem habilidade ativa (purple, metralhadora passiva)

        # Verificar cooldown
        if tempo_atual - bot.habilidade_cooldown < cooldown:
            return

        # Chance de usar habilidade baseada na classe e situação
        chance_uso = 0.03  # Base: 3% por frame

        if classe == 'mago':
            # Mago usa escudo quando está com pouca vida ou inimigo perto
            if bot.vidas <= bot.vidas_max * 0.6:
                chance_uso = 0.20  # 20% quando com pouca vida
            elif bot.ia_dist_inimigo < 100:
                chance_uso = 0.15  # 15% quando inimigo perto
            else:
                chance_uso = 0.08
        elif classe == 'granada':
            # Granada usa frequentemente em combate
            chance_uso = 0.10  # 10% por frame
        elif classe == 'ghost':
            # Ghost usa quando está em perigo
            if bot.vidas <= bot.vidas_max * 0.5:
                chance_uso = 0.15
            else:
                chance_uso = 0.05
        elif classe == 'explosive':
            chance_uso = 0.06
        elif classe == 'cyan':
            chance_uso = 0.05
        elif classe == 'normal':
            chance_uso = 0.08

        if random.random() > chance_uso:
            return

        # ====== USAR HABILIDADE BASEADA NA CLASSE ======

        # === MAGO - ESCUDO PROTETOR ===
        if classe == 'mago':
            bot.escudo_ativo = True
            bot.invulneravel = True
            bot.habilidade_ativa = True
            bot.habilidade_tempo_inicio = tempo_atual
            bot.habilidade_cooldown = tempo_atual
            print(f"[BOT IA] {bot.nome} (Mago) ativou ESCUDO!")

        # === GHOST - INVISIBILIDADE ===
        elif classe == 'ghost':
            bot.invisivel = True
            bot.habilidade_ativa = True
            bot.habilidade_tempo_inicio = tempo_atual
            bot.habilidade_cooldown = tempo_atual
            print(f"[BOT IA] {bot.nome} (Ghost) ficou INVISÍVEL!")

        # === GRANADA - LANÇAR GRANADA ===
        elif classe == 'granada':
            self._bot_lancar_granada_classe(bot, tempo_atual)
            bot.habilidade_cooldown = tempo_atual
            print(f"[BOT IA] {bot.nome} (Granada) lançou GRANADA!")

        # === CYAN - TURBO VELOCIDADE ===
        elif classe == 'cyan':
            bot.velocidade_original = bot.velocidade
            bot.velocidade = bot.velocidade * 4.0
            bot.habilidade_ativa = True
            bot.habilidade_tempo_inicio = tempo_atual
            bot.habilidade_cooldown = tempo_atual
            bot.posicoes_turbo = []
            print(f"[BOT IA] {bot.nome} (Cyan) ativou TURBO!")

        # === EXPLOSIVE - EXPLOSÃO DE TIROS ===
        elif classe == 'explosive':
            self._bot_explosao_tiros(bot, tempo_atual)
            bot.habilidade_cooldown = tempo_atual
            print(f"[BOT IA] {bot.nome} (Explosive) usou EXPLOSÃO!")

        # === NORMAL - DASH ===
        elif classe == 'normal':
            # Dash na direção do inimigo ou oposta (fuga)
            if bot.ia_alvo_inimigo:
                dx = bot.ia_alvo_inimigo.x - bot.x
                dy = bot.ia_alvo_inimigo.y - bot.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    # 50% chance de ir em direção ao inimigo, 50% fugir
                    mult = 1 if random.random() > 0.5 else -1
                    bot.dash_direcao = (mult * dx / dist, mult * dy / dist)
                    bot.dash_ativo = True
                    bot.dash_frames_restantes = dados.get('dash_duracao', 8)
                    bot.invulneravel = True
                    bot.habilidade_ativa = True
                    bot.habilidade_tempo_inicio = tempo_atual
                    bot.habilidade_cooldown = tempo_atual
                    print(f"[BOT IA] {bot.nome} (Normal) usou DASH!")

    def _bot_lancar_granada_classe(self, bot, tempo_atual):
        """Bot lança granada da habilidade de classe."""
        from src.items.granada import Granada
        import math

        if not bot.ia_alvo_inimigo:
            return

        centro_x = bot.x + TAMANHO_MULTIPLAYER / 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER / 2

        # Direção para o inimigo
        alvo_x = bot.ia_alvo_inimigo.x + TAMANHO_MULTIPLAYER / 2
        alvo_y = bot.ia_alvo_inimigo.y + TAMANHO_MULTIPLAYER / 2

        dx = alvo_x - centro_x
        dy = alvo_y - centro_y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > 0:
            dx /= dist
            dy /= dist

        granada = Granada(centro_x, centro_y, dx, dy)
        granada.time = bot.time  # Marcar time da granada
        self.granadas_ativas.append(granada)

    def _bot_explosao_tiros(self, bot, tempo_atual):
        """Bot usa habilidade explosive - tiros em todas direções."""
        from src.entities.tiro import Tiro
        from src.game.selecao_classes import obter_dados_classe
        import math

        dados = obter_dados_classe('explosive', bot.time)
        num_tiros = dados.get('tiros_explosao', 12) if dados else 12

        centro_x = bot.x + TAMANHO_MULTIPLAYER / 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER / 2

        for i in range(num_tiros):
            angulo = (2 * math.pi * i) / num_tiros
            dx = math.cos(angulo)
            dy = math.sin(angulo)

            tiro = Tiro(centro_x, centro_y, dx, dy, bot.cor, 8)
            tiro.dano = 1
            tiro.time_origem = bot.time
            self.tiros_inimigo.append(tiro)

    def _atualizar_habilidades_bots(self, tempo_atual):
        """Atualiza estado das habilidades ativas dos bots."""
        from src.game.selecao_classes import obter_dados_classe

        for bot in self.bots_locais:
            if bot.vidas <= 0:
                continue

            classe = getattr(bot, 'classe', None)

            # ====== NORMAL - ATUALIZAR DASH A CADA FRAME ======
            # O dash usa frames, não tempo, então precisa ser atualizado independentemente
            if classe == 'normal' and hasattr(bot, 'dash_ativo') and bot.dash_ativo:
                if bot.dash_frames_restantes > 0:
                    # Mover na direção do dash com colisão
                    dx, dy = bot.dash_direcao
                    vel_x = dx * bot.dash_velocidade
                    vel_y = dy * bot.dash_velocidade

                    # Usar rect com tamanho multiplayer para colisões
                    rect_colisao = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)

                    # Resolver colisão com o mapa
                    novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(rect_colisao, vel_x, vel_y)

                    bot.x = novo_x
                    bot.y = novo_y
                    bot.rect.x = novo_x
                    bot.rect.y = novo_y
                    bot.dash_frames_restantes -= 1
                else:
                    # Dash terminou
                    bot.dash_ativo = False
                    bot.invulneravel = False
                    bot.habilidade_ativa = False
                continue  # Dash já foi processado, próximo bot

            if not classe or not getattr(bot, 'habilidade_ativa', False):
                continue

            dados = obter_dados_classe(classe, bot.time)
            if not dados:
                continue

            duracao = dados.get('habilidade_duracao', 0)
            if duracao == 0:
                continue

            # Verificar se a habilidade expirou
            if tempo_atual - bot.habilidade_tempo_inicio >= duracao:
                # Desativar habilidade baseada na classe
                if classe == 'mago':
                    bot.escudo_ativo = False
                    bot.invulneravel = False
                    bot.habilidade_ativa = False
                elif classe == 'ghost':
                    bot.invisivel = False
                    bot.habilidade_ativa = False
                elif classe == 'cyan':
                    bot.velocidade = bot.velocidade_original
                    bot.habilidade_ativa = False
                    if hasattr(bot, 'posicoes_turbo'):
                        bot.posicoes_turbo.clear()

    def _ia_estado_recalculando(self, bot, tempo_atual):
        """
        Estado RECALCULANDO_ROTA: Recalcular caminho após obstáculo.
        """
        # Limpar caminho atual
        bot.ia_caminho = []
        bot.ia_waypoint_atual = 0

        # Forçar recálculo
        bot.ia_ultimo_recalculo = 0
        bot.ia_estado = 'patrulhando'

    # ==================== MOVIMENTO POR WAYPOINTS ====================

    def _ia_seguir_waypoints(self, bot, tempo_atual):
        """
        Segue o caminho de waypoints calculado pelo A*.

        Args:
            bot: Bot a mover
            tempo_atual: Tempo atual em ms
        """
        import math

        if not bot.ia_caminho or bot.ia_waypoint_atual >= len(bot.ia_caminho):
            return

        # Waypoint atual
        waypoint = bot.ia_caminho[bot.ia_waypoint_atual]

        # Calcular distância ao waypoint
        dx = waypoint[0] - bot.x
        dy = waypoint[1] - bot.y
        dist = math.sqrt(dx**2 + dy**2)

        # Chegou ao waypoint - ir para próximo
        if dist < self.IA_WAYPOINT_THRESHOLD:
            bot.ia_waypoint_atual += 1
            if bot.ia_waypoint_atual >= len(bot.ia_caminho):
                # Caminho completo
                bot.ia_caminho = []
                bot.ia_waypoint_atual = 0
            return

        # Mover em direção ao waypoint
        self._ia_mover_suave(bot, waypoint, tempo_atual)

    def _ia_mover_suave(self, bot, destino, tempo_atual):
        """
        Move o bot suavemente em direção a um destino.

        Inclui:
        - Normalização de direção
        - Suavização (lerp)
        - Dead zone
        - Evitar outros bots

        Args:
            bot: Bot a mover
            destino: Tupla (x, y) destino
            tempo_atual: Tempo atual
        """
        import math

        # Calcular direção
        dx = destino[0] - bot.x
        dy = destino[1] - bot.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1:
            return

        # Normalizar
        dir_x = dx / dist
        dir_y = dy / dist

        # Evitar paredes à frente
        centro_x = bot.x + TAMANHO_MULTIPLAYER // 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER // 2
        check_dist = 25

        if self.tilemap.is_solid(centro_x + dir_x * check_dist, centro_y + dir_y * check_dist):
            # Tentar desviar
            for angulo_off in [30, -30, 60, -60, 90, -90]:
                rad = math.atan2(dir_y, dir_x) + math.radians(angulo_off)
                test_x = math.cos(rad)
                test_y = math.sin(rad)
                if not self.tilemap.is_solid(centro_x + test_x * check_dist,
                                              centro_y + test_y * check_dist):
                    dir_x, dir_y = test_x, test_y
                    break

        # Evitar outros bots
        for outro_bot in self.bots_locais:
            if outro_bot == bot or outro_bot.vidas <= 0:
                continue
            bx = bot.x - outro_bot.x
            by = bot.y - outro_bot.y
            bd = math.sqrt(bx**2 + by**2)
            if bd < 40 and bd > 0:
                dir_x += (bx / bd) * 0.3
                dir_y += (by / bd) * 0.3

        # Re-normalizar
        mag = math.sqrt(dir_x**2 + dir_y**2)
        if mag > 0:
            dir_x /= mag
            dir_y /= mag

        # Suavização de direção (lerp) - mais responsivo
        TAXA_SUAVIZACAO = 0.4
        bot.ia_dir_x += (dir_x - bot.ia_dir_x) * TAXA_SUAVIZACAO
        bot.ia_dir_y += (dir_y - bot.ia_dir_y) * TAXA_SUAVIZACAO

        # Re-normalizar após lerp
        mag = math.sqrt(bot.ia_dir_x**2 + bot.ia_dir_y**2)
        if mag > 0.1:
            bot.ia_dir_x /= mag
            bot.ia_dir_y /= mag
        else:
            # Dead zone - direção muito pequena
            return

        # Calcular velocidade
        vel_x = bot.ia_dir_x * bot.velocidade
        vel_y = bot.ia_dir_y * bot.velocidade

        # Suavização de velocidade (mais responsivo)
        TAXA_VEL = 0.6
        bot.ia_vel_x += (vel_x - bot.ia_vel_x) * TAXA_VEL
        bot.ia_vel_y += (vel_y - bot.ia_vel_y) * TAXA_VEL

        # Dead zone para velocidade
        if abs(bot.ia_vel_x) < 0.1:
            bot.ia_vel_x = 0
        if abs(bot.ia_vel_y) < 0.1:
            bot.ia_vel_y = 0

        # Aplicar movimento com colisão
        if abs(bot.ia_vel_x) > 0.1 or abs(bot.ia_vel_y) > 0.1:
            pos_antes_x, pos_antes_y = bot.x, bot.y
            bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
            novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(
                bot_rect, bot.ia_vel_x, bot.ia_vel_y
            )
            bot.x = novo_x
            bot.y = novo_y

            # Detectar bloqueio: tentou mover mas não conseguiu
            movimento_real = math.sqrt((novo_x - pos_antes_x)**2 + (novo_y - pos_antes_y)**2)
            movimento_esperado = math.sqrt(bot.ia_vel_x**2 + bot.ia_vel_y**2)

            if movimento_esperado > 0.5 and movimento_real < movimento_esperado * 0.2:
                # Bot está bloqueado - tentando mover mas não consegue
                bot.ia_bloqueado_contador = getattr(bot, 'ia_bloqueado_contador', 0) + 1
            else:
                bot.ia_bloqueado_contador = 0

    def _ia_mover_direto(self, bot, destino):
        """
        Move o bot diretamente para um destino (sem pathfinding).
        Usado como fallback quando não pode recalcular caminho.
        """
        import math

        dx = destino[0] - bot.x
        dy = destino[1] - bot.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1:
            return

        dir_x = dx / dist
        dir_y = dy / dist

        # Movimento simples
        vel_x = dir_x * bot.velocidade
        vel_y = dir_y * bot.velocidade

        pos_antes_x, pos_antes_y = bot.x, bot.y
        bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
        novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(bot_rect, vel_x, vel_y)
        bot.x = novo_x
        bot.y = novo_y

        # Detectar bloqueio: tentou mover mas não conseguiu
        movimento_real = math.sqrt((novo_x - pos_antes_x)**2 + (novo_y - pos_antes_y)**2)
        movimento_esperado = math.sqrt(vel_x**2 + vel_y**2)

        if movimento_esperado > 0.5 and movimento_real < movimento_esperado * 0.2:
            # Bot está bloqueado - tentando mover mas não consegue
            bot.ia_bloqueado_contador = getattr(bot, 'ia_bloqueado_contador', 0) + 1
        else:
            bot.ia_bloqueado_contador = 0

    def _encontrar_ponto_rota_acessivel(self, bot, dist_maxima=300, retornar_info_rota=False):
        """
        Encontra o ponto de rota do devmode mais próximo que seja acessível
        (sem paredes no caminho).

        Args:
            bot: Bot que precisa encontrar um ponto
            dist_maxima: Distância máxima para procurar
            retornar_info_rota: Se True, retorna também índice da rota e waypoint

        Returns:
            Se retornar_info_rota=False: Tupla (x, y) do ponto mais próximo ou None
            Se retornar_info_rota=True: Tupla (ponto, rota_idx, waypoint_idx) ou (None, None, None)
        """
        import math

        # Pegar rotas do time do bot
        if hasattr(bot, 'time') and bot.time == 'T':
            rotas = self.dev_rotas_t
        else:
            rotas = self.dev_rotas_q

        if not rotas:
            return (None, None, None) if retornar_info_rota else None

        ponto_mais_proximo = None
        menor_dist = float('inf')
        melhor_rota_idx = None
        melhor_waypoint_idx = None

        centro_x = bot.x + TAMANHO_MULTIPLAYER // 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER // 2

        for rota_idx, rota in enumerate(rotas):
            for waypoint_idx, ponto in enumerate(rota):
                dist_ponto = math.sqrt((bot.x - ponto[0])**2 + (bot.y - ponto[1])**2)

                # Verificar se o ponto está a uma distância razoável
                if dist_ponto < menor_dist and dist_ponto > 20 and dist_ponto < dist_maxima:
                    # Verificar se consegue ir direto (sem parede no caminho inteiro)
                    dir_x = (ponto[0] - bot.x)
                    dir_y = (ponto[1] - bot.y)

                    # Checar múltiplos pontos ao longo do caminho
                    caminho_livre = True
                    num_checks = max(5, int(dist_ponto / 20))  # Check a cada ~20 pixels
                    for i in range(1, num_checks + 1):
                        t = i / num_checks
                        check_x = centro_x + dir_x * t
                        check_y = centro_y + dir_y * t
                        if self.tilemap.is_solid(check_x, check_y):
                            caminho_livre = False
                            break

                    if caminho_livre:
                        menor_dist = dist_ponto
                        ponto_mais_proximo = ponto
                        melhor_rota_idx = rota_idx
                        melhor_waypoint_idx = waypoint_idx

        if retornar_info_rota:
            return (ponto_mais_proximo, melhor_rota_idx, melhor_waypoint_idx)
        return ponto_mais_proximo

    def _ia_wandering_aleatorio(self, bot, tempo_atual):
        """
        Move o bot em uma direção aleatória não sólida para tentar sair de onde está preso.
        Move DIRETAMENTE o bot, não apenas cria waypoint.

        Args:
            bot: Bot a mover
            tempo_atual: Tempo atual em ms
        """
        import math
        import random

        centro_x = bot.x + TAMANHO_MULTIPLAYER // 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER // 2

        # Coletar todas as direções livres
        direcoes_livres = []

        for angulo in range(0, 360, 30):  # Testar mais direções (12 em vez de 8)
            rad = math.radians(angulo)
            dir_x = math.cos(rad)
            dir_y = math.sin(rad)

            # Verificar quão longe pode ir nessa direção
            dist_livre = 0
            for d in range(10, 250, 10):
                check_x = centro_x + dir_x * d
                check_y = centro_y + dir_y * d
                if self.tilemap.is_solid(check_x, check_y):
                    break
                dist_livre = d

            if dist_livre >= 40:
                direcoes_livres.append((dir_x, dir_y, dist_livre))

        if direcoes_livres:
            # Escolher direção aleatória entre as livres
            escolha = random.choice(direcoes_livres)
            dir_x, dir_y, dist_livre = escolha

            # MOVER DIRETAMENTE o bot na direção escolhida (forçar movimento)
            destino_x = bot.x + dir_x * dist_livre * 0.8
            destino_y = bot.y + dir_y * dist_livre * 0.8

            # Mover o bot diretamente por vários frames
            vel_x = dir_x * bot.velocidade * 2  # Velocidade dobrada para escapar
            vel_y = dir_y * bot.velocidade * 2

            bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
            novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(bot_rect, vel_x, vel_y)
            bot.x = novo_x
            bot.y = novo_y

            # Também criar waypoint para continuar movimento
            bot.ia_caminho = [(destino_x, destino_y)]
            bot.ia_waypoint_atual = 0
            bot.ia_estado = 'movendo'
            bot.ia_tempo_inicio_rota = tempo_atual
            bot.ia_rota_idx = None
            bot.ia_tentativas_escape = 0  # Resetar após mover
            bot.ia_bloqueado_contador = 0  # Resetar contador de bloqueio

            # Ativar modo escape por 2 segundos (não sobrescrever waypoints)
            bot.ia_modo_escape = True
            bot.ia_escape_tempo_fim = tempo_atual + 2000

            print(f"[IA] {bot.nome} wandering aleatório para escapar")
        else:
            # Sem direções livres, tentar micro-movimento em qualquer direção
            for angulo in range(0, 360, 15):
                rad = math.radians(angulo)
                dir_x = math.cos(rad)
                dir_y = math.sin(rad)

                # Tentar mover só um pouco
                vel_x = dir_x * bot.velocidade
                vel_y = dir_y * bot.velocidade

                bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
                novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(bot_rect, vel_x, vel_y)

                # Se conseguiu mover
                if abs(novo_x - bot.x) > 0.5 or abs(novo_y - bot.y) > 0.5:
                    bot.x = novo_x
                    bot.y = novo_y
                    print(f"[IA] {bot.nome} micro-movimento para escapar")
                    break

            bot.ia_rota_idx = None
            bot.ia_caminho = []
            bot.ia_waypoint_atual = 0
            bot.ia_tile_alvo = None
            bot.ia_tempo_inicio_rota = tempo_atual

    def _ia_mover_combate(self, bot, tempo_atual):
        """
        Movimento durante combate - strafe e evasão.
        """
        import math

        if not bot.ia_alvo_inimigo:
            return

        inimigo = bot.ia_alvo_inimigo
        dx = inimigo.x - bot.x
        dy = inimigo.y - bot.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1:
            return

        dir_x = dx / dist
        dir_y = dy / dist

        # Strafe perpendicular
        bot_id = id(bot) % 100
        strafe_dir = 1 if ((tempo_atual // 800) + bot_id) % 2 == 0 else -1

        mover_x = -dir_y * strafe_dir
        mover_y = dir_x * strafe_dir

        # Ajustar distância
        if dist < 80:
            mover_x -= dir_x * 0.5
            mover_y -= dir_y * 0.5
        elif dist > 150:
            mover_x += dir_x * 0.3
            mover_y += dir_y * 0.3

        # Evitar paredes
        centro_x = bot.x + TAMANHO_MULTIPLAYER // 2
        centro_y = bot.y + TAMANHO_MULTIPLAYER // 2

        for angulo in range(0, 360, 45):
            rad = math.radians(angulo)
            check_x = centro_x + math.cos(rad) * 35
            check_y = centro_y + math.sin(rad) * 35

            if self.tilemap.is_solid(check_x, check_y):
                mover_x -= math.cos(rad) * 0.6
                mover_y -= math.sin(rad) * 0.6

        # Normalizar
        mag = math.sqrt(mover_x**2 + mover_y**2)
        if mag > 0:
            mover_x /= mag
            mover_y /= mag

        # Aplicar movimento
        vel_x = mover_x * bot.velocidade
        vel_y = mover_y * bot.velocidade

        bot_rect = pygame.Rect(bot.x, bot.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER)
        novo_x, novo_y, _, _ = self.tilemap.resolver_colisao(bot_rect, vel_x, vel_y)
        bot.x = novo_x
        bot.y = novo_y

    # ==================== FUNÇÕES DE COMPATIBILIDADE ====================

    def _bot_comprar_arma(self, bot):
        """Bot compra arma aleatória baseado no dinheiro disponível."""
        moedas = getattr(bot, 'moedas', 8000)

        # Lista de armas disponíveis
        armas_disponiveis = [
            ('sniper', 4750, 6, 1200),      # nome, preço, dano, cadência
            ('metralhadora', 2700, 1, 100),  # Cadência muito alta
            ('spas12', 1200, 2, 600),
            ('desert_eagle', 500, 3, 700),  # Cadência lenta
        ]

        # Filtrar armas que o bot pode comprar
        armas_possiveis = [(a, p, d, c) for a, p, d, c in armas_disponiveis if p <= moedas]

        if armas_possiveis:
            # Escolher aleatoriamente entre as armas que pode comprar
            arma_nome, preco, dano, cadencia = random.choice(armas_possiveis)
            bot.moedas = moedas - preco
            bot.arma = arma_nome
            bot.dano_arma = dano
            bot.cadencia_arma = cadencia
            print(f"[BOT COMPRA] {bot.nome} comprou {arma_nome} por ${preco} (Saldo: ${bot.moedas})")
            return

        # Se não tem dinheiro, fica sem arma (tiro normal)
        bot.arma = None
        bot.dano_arma = 1
        bot.cadencia_arma = 500  # Tiro normal mais lento

    def _bot_atirar(self, bot, alvo, tempo_atual):
        """Bot atira no alvo."""
        import math
        from src.entities.tiro import Tiro

        # Verificar cadência
        cadencia = getattr(bot, 'cadencia_arma', 800)
        if tempo_atual - bot.tempo_ultimo_tiro < cadencia:
            return

        # Calcular direção
        dx = alvo.x - bot.x
        dy = alvo.y - bot.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 10:
            return

        # Adicionar um pouco de imprecisão baseado na distância
        imprecisao = min(dist / 800, 0.3)  # Máximo 30% de imprecisão
        angulo = math.atan2(dy, dx)
        angulo += random.uniform(-imprecisao, imprecisao)

        tiro_dx = math.cos(angulo)
        tiro_dy = math.sin(angulo)

        # Criar tiro
        dano = getattr(bot, 'dano_arma', 1)
        tiro = Tiro(bot.x + TAMANHO_MULTIPLAYER // 2, bot.y + TAMANHO_MULTIPLAYER // 2,
                   tiro_dx, tiro_dy, bot.cor, 7)
        tiro.dano = dano
        tiro.time_origem = bot.time
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

                # Ignorar bots mortos - tiro passa através
                if bot.vidas <= 0:
                    continue

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
                    # Verificar invulnerabilidade (escudo do mago, dash, etc)
                    if getattr(bot, 'invulneravel', False):
                        print(f"[PVP] {bot.nome} bloqueou o dano (ESCUDO ATIVO)!")
                        break
                    dano = getattr(tiro, 'dano', 1)
                    vida_antes = bot.vidas
                    bot.vidas = max(0, bot.vidas - dano)
                    print(f"[PVP] Jogador acertou {bot.nome} (Time {bot_time})! Vida restante: {bot.vidas}")

                    # Recompensa por eliminacao
                    if vida_antes > 0 and bot.vidas <= 0:
                        self.moedas += 300  # Recompensa por kill
                        print(f"[RECOMPENSA] +$300 por eliminar {bot.nome}! Saldo: ${self.moedas}")

                        # Se era o bomber, dropar a bomba
                        if getattr(bot, 'é_bomber', False) and not self.bomba_plantada:
                            self._dropar_bomba(bot.x, bot.y)

        # Tiros de bots atingindo jogador e outros bots (só de times opostos)
        for tiro in self.tiros_inimigo[:]:
            tiro_time = getattr(tiro, 'time_origem', None)
            tiro_removido = False

            # Verificar colisão com jogador (só se for do time oposto e não invulnerável)
            if tiro_time and tiro_time != self.time_jogador and self.jogador.vidas > 0:
                # Verificar se jogador está invulnerável (escudo do mago ou dash)
                if getattr(self.jogador, 'invulneravel', False):
                    continue  # Pular dano se invulnerável

                jogador_rect = pygame.Rect(
                    self.jogador.x, self.jogador.y, TAMANHO_MULTIPLAYER, TAMANHO_MULTIPLAYER
                )

                if tiro.rect.colliderect(jogador_rect):
                    criar_explosao(tiro.x, tiro.y, tiro.cor, self.particulas)
                    if tiro in self.tiros_inimigo:
                        self.tiros_inimigo.remove(tiro)
                        tiro_removido = True
                    dano = getattr(tiro, 'dano', 1)
                    vida_antes = self.jogador.vidas
                    self.jogador.vidas = max(0, self.jogador.vidas - dano)
                    print(f"[PVP] Bot do Time {tiro_time} acertou você! Vida restante: {self.jogador.vidas}")

                    # Se jogador morreu e era o bomber, dropar a bomba
                    if vida_antes > 0 and self.jogador.vidas <= 0:
                        if self.bomber_é_jogador and not self.bomba_plantada:
                            self._dropar_bomba(self.jogador.x, self.jogador.y)

            # Verificar colisão com bots do time oposto ao tiro
            if not tiro_removido:
                for bot in self.bots_locais:
                    # Ignorar bots mortos - tiro passa através
                    if bot.vidas <= 0:
                        continue

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
                        # Verificar invulnerabilidade (escudo do mago, dash, etc)
                        if getattr(bot, 'invulneravel', False):
                            print(f"[PVP] {bot.nome} bloqueou o dano (ESCUDO ATIVO)!")
                            break
                        dano = getattr(tiro, 'dano', 1)
                        vida_antes = bot.vidas
                        bot.vidas = max(0, bot.vidas - dano)
                        print(f"[PVP] Tiro do Time {tiro_time} acertou {bot.nome} (Time {bot_time})!")

                        # Se era o bomber e morreu, dropar a bomba
                        if vida_antes > 0 and bot.vidas <= 0:
                            if getattr(bot, 'é_bomber', False) and not self.bomba_plantada:
                                self._dropar_bomba(bot.x, bot.y)
                        break

    def _verificar_vitoria(self):
        """Verifica se um time venceu o round (todos do time oposto eliminados)."""
        if self.partida_terminada or self.round_terminado:
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

        # Verificar se algum time foi eliminado neste round
        if time_t_vivos == 0 and time_q_vivos > 0:
            # Se a bomba está plantada, Time Q precisa defusar para vencer
            # Se não defusar, a bomba explode e Time T vence
            if self.bomba_plantada and not self.bomba_defusada:
                # Não declarar vitória ainda - bomba precisa ser defusada ou explodir
                pass
            else:
                self._time_venceu_round('Q')
        elif time_q_vivos == 0 and time_t_vivos > 0:
            self._time_venceu_round('T')

    def _time_venceu_round(self, time_vencedor):
        """Processa a vitória de um time no round."""
        self.round_terminado = True
        self.time_vencedor = time_vencedor

        # Adicionar ponto ao time vencedor
        if time_vencedor == 'T':
            self.rounds_time_t += 1
            print(f"[ROUND] Time T venceu o round {self.round_atual}! Placar: T {self.rounds_time_t} x {self.rounds_time_q} Q")
        else:
            self.rounds_time_q += 1
            print(f"[ROUND] Time Q venceu o round {self.round_atual}! Placar: T {self.rounds_time_t} x {self.rounds_time_q} Q")

        # Recompensa por vitória/derrota do round
        if self.time_jogador == time_vencedor:
            self.moedas += 3000  # Bônus por vencer round
            print(f"[RECOMPENSA] +$3000 por vencer o round! Saldo: ${self.moedas}")
        else:
            self.moedas += 1000  # Consolação por perder round
            print(f"[RECOMPENSA] +$1000 (derrota). Saldo: ${self.moedas}")

        # Verificar se algum time venceu a partida (primeiro a 5)
        if self.rounds_time_t >= self.rounds_para_vencer:
            self.partida_terminada = True
            self.jogo_terminado = True
            self.vencedor = "Time T"
            print(f"[PARTIDA] Time T VENCEU A PARTIDA! {self.rounds_time_t} x {self.rounds_time_q}")
        elif self.rounds_time_q >= self.rounds_para_vencer:
            self.partida_terminada = True
            self.jogo_terminado = True
            self.vencedor = "Time Q"
            print(f"[PARTIDA] Time Q VENCEU A PARTIDA! {self.rounds_time_t} x {self.rounds_time_q}")
        else:
            # Preparar próximo round
            self.tempo_proximo_round = pygame.time.get_ticks() + 3000  # 3 segundos até próximo round

    def _verificar_proximo_round(self):
        """Verifica se é hora de iniciar o próximo round."""
        if not self.round_terminado or self.partida_terminada:
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual >= self.tempo_proximo_round:
            self._iniciar_novo_round()

    def _iniciar_novo_round(self):
        """Inicia um novo round, resetando posições e vidas."""
        self.round_atual += 1
        self.round_terminado = False
        print(f"[ROUND] Iniciando round {self.round_atual}!")

        # Resetar jogador
        self.jogador.vidas = self.jogador.vidas_max
        spawn_name = f"Start_{self.time_jogador}"
        spawn_pos = self.tilemap.get_spawn_point(spawn_name)
        if spawn_pos:
            self.jogador.x = spawn_pos[0]
            self.jogador.y = spawn_pos[1]
            self.jogador.rect.x = spawn_pos[0]
            self.jogador.rect.y = spawn_pos[1]

        # Resetar atributos de classe do jogador
        self.jogador.invulneravel = False
        self.habilidade_ativa = False
        self.habilidade_cooldown = 0
        self.habilidade_tempo_inicio = 0

        if self.classe_jogador == "normal":
            self.jogador.dash_ativo = False
            self.jogador.dash_frames_restantes = 0
        elif self.classe_jogador == "mago":
            self.jogador.escudo_ativo = False
        elif self.classe_jogador == "ghost":
            self.jogador.invisivel = False
        elif self.classe_jogador == "cyan":
            self.jogador.velocidade = self.velocidade_original
            if hasattr(self.jogador, 'posicoes_turbo'):
                self.jogador.posicoes_turbo.clear()

        # Resetar bots
        for bot in self.bots_locais:
            bot.vidas = bot.vidas_max
            bot_time = getattr(bot, 'time', 'T')
            spawn_name = f"Start_{bot_time}"
            spawn_obj = self.tilemap.get_objeto(spawn_name)
            if spawn_obj:
                bot.x = spawn_obj['x'] + random.random() * spawn_obj['width']
                bot.y = spawn_obj['y'] + random.random() * spawn_obj['height']

            # Resetar atributos de IA
            bot.estado = 'comprando'
            bot.ja_comprou = False
            bot.alvo_inimigo = None
            bot.é_bomber = False
            # Escolher novo bombsite alvo
            if hasattr(self, 'bombsites') and self.bombsites:
                bot.bombsite_alvo = random.randint(0, len(self.bombsites) - 1)
            # Dar recompensa de round
            bot.moedas = getattr(bot, 'moedas', 0) + 1400  # Bônus por round

            # Resetar rota - bot vai escolher nova rota aleatória no início do round
            bot.ia_rota_idx = None

            # Resetar atributos de classe
            bot.habilidade_cooldown = 0
            bot.habilidade_ativa = False
            bot.habilidade_tempo_inicio = 0

            classe = getattr(bot, 'classe', None)
            if classe == 'mago':
                bot.escudo_ativo = False
                bot.invulneravel = False
            elif classe == 'ghost':
                bot.invisivel = False
            elif classe == 'cyan':
                bot.velocidade = 2.5  # Velocidade base
                bot.velocidade_original = 2.5
                if hasattr(bot, 'posicoes_turbo'):
                    bot.posicoes_turbo.clear()
            elif classe == 'normal':
                bot.dash_ativo = False
                bot.dash_frames_restantes = 0
                bot.invulneravel = False
            bot.ia_caminho = []
            bot.ia_waypoint_atual = 0

            # Resetar estado de plantio
            bot.bot_plantando = False
            bot.bot_tempo_inicio_plantar = 0

        # Limpar tiros e granadas
        self.tiros_jogador.clear()
        self.tiros_inimigo.clear()
        self.particulas.clear()
        self.granadas_ativas.clear()
        self.jogador.granada_selecionada = False

        # Resetar tempo de compra
        self.tempo_inicio_round = pygame.time.get_ticks()
        self.em_tempo_compra = True
        self.menu_compra_aberto = False

        # Resetar sistema de bomba
        self.bomba_plantada = False
        self.bomba_posicao = None
        self.bomba_tempo_plantio = 0
        self.plantando_bomba = False
        self.defusando_bomba = False
        self.bomba_defusada = False
        self.bomba_explodiu = False
        self.bomba_dropada = False
        self.bomba_drop_posicao = None

        # Resetar sistema de espectador (câmera segue aliados quando jogador morre)
        self.espectador_ativo = False
        self.espectador_tempo_morte = 0  # Tempo quando o jogador morreu
        self.espectador_alvo_idx = 0  # Índice do aliado sendo observado
        self.espectador_delay = 2000  # 2 segundos de delay antes de seguir aliado

        # Selecionar novo bomber
        self._selecionar_bomber()

    def _selecionar_bomber(self):
        """Seleciona aleatoriamente um membro do time T para ser o bomber."""
        # Resetar flag de bomber de todos os bots
        for bot in self.bots_locais:
            bot.é_bomber = False

        candidatos = []

        # Adicionar jogador se for do time T
        if self.time_jogador == 'T':
            candidatos.append({'tipo': 'jogador', 'id': 'local'})

        # Adicionar bots do time T
        for i, bot in enumerate(self.bots_locais):
            if getattr(bot, 'time', None) == 'T' and bot.vidas > 0:
                candidatos.append({'tipo': 'bot', 'id': i, 'nome': bot.nome, 'bot': bot})

        if candidatos:
            escolhido = random.choice(candidatos)
            if escolhido['tipo'] == 'jogador':
                self.bomber_id = 'local'
                self.bomber_é_jogador = True
                print(f"[BOMBA] Você é o BOMBER! Plante a bomba no local marcado (tile 322)")
            else:
                self.bomber_id = escolhido['id']
                self.bomber_é_jogador = False
                # Marcar o bot como bomber
                escolhido['bot'].é_bomber = True
                bot_nome = escolhido.get('nome', f'Bot {escolhido["id"]}')
                print(f"[BOMBA] {bot_nome} é o BOMBER!")
        else:
            self.bomber_id = None
            self.bomber_é_jogador = False
            print("[BOMBA] Nenhum membro do time T disponível para ser bomber")

    def _verificar_no_bombsite(self, x, y):
        """Verifica se a posição está no tile 322 (bombsite)."""
        tile_id = self.tilemap.get_tile_at_pixel(x + TAMANHO_MULTIPLAYER // 2,
                                                  y + TAMANHO_MULTIPLAYER // 2)
        tile_id_base = tile_id & 0x1FFFFFFF
        return tile_id_base == 322

    def _processar_bomba(self, tempo_atual):
        """Processa toda a lógica da bomba (plantar, defusar, explodir)."""
        teclas = pygame.key.get_pressed()
        tecla_f = teclas[pygame.K_f]

        # Se bomba não foi plantada ainda
        if not self.bomba_plantada and not self.bomba_explodiu:
            # Verificar se o bomber (jogador) está tentando plantar
            if self.bomber_é_jogador and self.jogador.vidas > 0:
                no_bombsite = self._verificar_no_bombsite(self.jogador.x, self.jogador.y)

                if tecla_f and no_bombsite:
                    if not self.plantando_bomba:
                        self.plantando_bomba = True
                        self.tempo_inicio_plantar = tempo_atual
                        print("[BOMBA] Plantando bomba...")
                    else:
                        # Verificar se completou o plantio
                        tempo_plantando = tempo_atual - self.tempo_inicio_plantar
                        if tempo_plantando >= self.tempo_para_plantar:
                            self._plantar_bomba(self.jogador.x, self.jogador.y)
                else:
                    if self.plantando_bomba:
                        print("[BOMBA] Plantio cancelado!")
                    self.plantando_bomba = False

        # Se bomba foi plantada
        elif self.bomba_plantada and not self.bomba_defusada and not self.bomba_explodiu:
            # Verificar explosão por tempo
            tempo_desde_plantio = tempo_atual - self.bomba_tempo_plantio
            if tempo_desde_plantio >= self.bomba_tempo_explosao:
                self._explodir_bomba()
                return

            # Verificar se jogador do time Q está tentando defusar
            if self.time_jogador == 'Q' and self.jogador.vidas > 0:
                # Verificar se está perto da bomba
                if self.bomba_posicao:
                    dist_x = abs(self.jogador.x - self.bomba_posicao[0])
                    dist_y = abs(self.jogador.y - self.bomba_posicao[1])
                    perto_bomba = dist_x < 30 and dist_y < 30

                    if tecla_f and perto_bomba:
                        if not self.defusando_bomba:
                            self.defusando_bomba = True
                            self.tempo_inicio_defusar = tempo_atual
                            print("[BOMBA] Defusando bomba...")
                        else:
                            # Verificar se completou o defuse
                            tempo_defusando = tempo_atual - self.tempo_inicio_defusar
                            if tempo_defusando >= self.tempo_para_defusar:
                                self._defusar_bomba()
                    else:
                        if self.defusando_bomba:
                            print("[BOMBA] Defuse cancelado!")
                        self.defusando_bomba = False

            # === BOTS DO TIME Q DEFUSANDO ===
            for bot in self.bots_locais:
                if bot.vidas <= 0 or getattr(bot, 'time', '') != 'Q':
                    continue

                if self.bomba_posicao:
                    dist_x = abs(bot.x - self.bomba_posicao[0])
                    dist_y = abs(bot.y - self.bomba_posicao[1])
                    perto_bomba = dist_x < 30 and dist_y < 30

                    if perto_bomba and getattr(bot, 'bot_defusando', False):
                        # Iniciar ou continuar defuse
                        if not hasattr(bot, 'bot_tempo_inicio_defusar'):
                            bot.bot_tempo_inicio_defusar = tempo_atual
                            print(f"[BOMBA] {bot.nome} começou a defusar!")

                        tempo_defusando = tempo_atual - bot.bot_tempo_inicio_defusar
                        if tempo_defusando >= self.tempo_para_defusar:
                            print(f"[BOMBA] {bot.nome} defusou a bomba!")
                            self._defusar_bomba()
                            break
                    else:
                        # Resetar tempo de defuse se saiu de perto
                        if hasattr(bot, 'bot_tempo_inicio_defusar'):
                            del bot.bot_tempo_inicio_defusar

    def _plantar_bomba(self, x, y):
        """Planta a bomba na posição especificada."""
        self.bomba_plantada = True
        self.bomba_posicao = (x, y)
        self.bomba_tempo_plantio = pygame.time.get_ticks()
        self.plantando_bomba = False
        print(f"[BOMBA] BOMBA PLANTADA! Time Q tem {self.bomba_tempo_explosao // 1000}s para defusar!")

    def _bot_plantar_bomba(self, bot, tile_pos=None):
        """Bot inicia ou continua o processo de plantar bomba no tile 322."""
        tempo_atual = pygame.time.get_ticks()

        # Se não está plantando ainda, começar
        if not getattr(bot, 'bot_plantando', False):
            bot.bot_plantando = True
            bot.bot_tempo_inicio_plantar = tempo_atual
            # Salvar posição do tile 322 para plantar exatamente lá
            if tile_pos:
                bot.bot_tile_plantio = tile_pos
            print(f"[BOMBA] {bot.nome} começou a plantar a bomba no tile 322!")
            return

        # Calcular progresso do plantio
        tempo_plantando = tempo_atual - bot.bot_tempo_inicio_plantar
        if tempo_plantando >= self.tempo_para_plantar:
            # Terminou de plantar - plantar no tile 322!
            pos_plantio = getattr(bot, 'bot_tile_plantio', (bot.x, bot.y))
            self._plantar_bomba(pos_plantio[0], pos_plantio[1])
            bot.bot_plantando = False
            bot.é_bomber = False  # Não é mais o bomber após plantar
            print(f"[BOMBA] {bot.nome} plantou a bomba no tile 322!")

    def _defusar_bomba(self):
        """Defusa a bomba - Time Q vence o round."""
        self.bomba_defusada = True
        self.defusando_bomba = False
        print("[BOMBA] BOMBA DEFUSADA! Time Q vence o round!")
        self._time_venceu_round('Q')

    def _explodir_bomba(self):
        """Explode a bomba - Time T vence o round."""
        self.bomba_explodiu = True
        print("[BOMBA] BOMBA EXPLODIU! Time T vence o round!")
        # Criar explosão visual
        if self.bomba_posicao:
            for _ in range(50):
                criar_explosao(self.bomba_posicao[0], self.bomba_posicao[1],
                             (255, 100, 0), self.particulas)
        self._time_venceu_round('T')

    def _dropar_bomba(self, x, y):
        """Dropa a bomba no chão quando o bomber morre."""
        if self.bomba_plantada:
            return  # Bomba já foi plantada, não dropar

        self.bomba_dropada = True
        self.bomba_drop_posicao = (x, y)
        self.bomber_é_jogador = False

        # Remover status de bomber de todos
        for bot in self.bots_locais:
            bot.é_bomber = False

        print(f"[BOMBA] Bomber morreu! Bomba dropada em ({int(x)}, {int(y)})")

    def _pegar_bomba_dropada(self, entidade, é_jogador=False):
        """Entidade do time T pega a bomba dropada."""
        if not self.bomba_dropada:
            return

        self.bomba_dropada = False
        self.bomba_drop_posicao = None

        if é_jogador:
            self.bomber_é_jogador = True
            print(f"[BOMBA] Você pegou a bomba! Agora é o bomber!")
        else:
            entidade.é_bomber = True
            print(f"[BOMBA] {entidade.nome} pegou a bomba! Agora é o bomber!")

    def _verificar_pickup_bomba(self):
        """Verifica se alguém do time T pegou a bomba dropada."""
        if not self.bomba_dropada or not self.bomba_drop_posicao:
            return

        bomba_x, bomba_y = self.bomba_drop_posicao
        raio_pickup = 30  # Distância para pegar a bomba

        # Verificar jogador (se for do time T)
        if self.time_jogador == 'T' and self.jogador.vidas > 0:
            dist = ((self.jogador.x - bomba_x)**2 + (self.jogador.y - bomba_y)**2)**0.5
            if dist < raio_pickup:
                self._pegar_bomba_dropada(self.jogador, é_jogador=True)
                return

        # Verificar bots do time T
        for bot in self.bots_locais:
            if getattr(bot, 'time', '') != 'T' or bot.vidas <= 0:
                continue
            dist = ((bot.x - bomba_x)**2 + (bot.y - bomba_y)**2)**0.5
            if dist < raio_pickup:
                self._pegar_bomba_dropada(bot, é_jogador=False)
                return

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
            # Desenhar arma na mão do jogador
            self._desenhar_arma_jogador(mundo_surface, tempo_atual)

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

        # Desenhar granadas em voo
        self._desenhar_granadas_ativas(mundo_surface)

        # Desenhar bomba se plantada
        if self.bomba_plantada and self.bomba_posicao and not self.bomba_explodiu:
            bomba_x = self.bomba_posicao[0] - self.camera_x
            bomba_y = self.bomba_posicao[1] - self.camera_y
            # Bomba pulsando
            pulso = (tempo_atual % 500) / 500
            tamanho_bomba = 8 + int(pulso * 3)
            # Desenhar bomba
            pygame.draw.rect(mundo_surface, (50, 50, 50),
                           (bomba_x - tamanho_bomba//2, bomba_y - tamanho_bomba//2,
                            tamanho_bomba, tamanho_bomba), 0, 3)
            pygame.draw.rect(mundo_surface, (200, 50, 50),
                           (bomba_x - tamanho_bomba//2, bomba_y - tamanho_bomba//2,
                            tamanho_bomba, tamanho_bomba), 2, 3)
            # Luz piscando
            if tempo_atual % 1000 < 500:
                pygame.draw.circle(mundo_surface, (255, 0, 0),
                                 (int(bomba_x), int(bomba_y - tamanho_bomba//2 - 3)), 3)

        # Desenhar bomba dropada no chão
        if self.bomba_dropada and self.bomba_drop_posicao:
            bomba_x = self.bomba_drop_posicao[0] - self.camera_x
            bomba_y = self.bomba_drop_posicao[1] - self.camera_y
            # Bomba pulsando (mais devagar que plantada)
            pulso = (tempo_atual % 800) / 800
            tamanho_bomba = 10 + int(pulso * 4)

            # Círculo de destaque ao redor
            pygame.draw.circle(mundo_surface, (255, 200, 0),
                             (int(bomba_x), int(bomba_y)), tamanho_bomba + 8, 2)

            # Desenhar bomba (cor diferente - amarela/laranja)
            pygame.draw.rect(mundo_surface, (80, 60, 20),
                           (bomba_x - tamanho_bomba//2, bomba_y - tamanho_bomba//2,
                            tamanho_bomba, tamanho_bomba), 0, 3)
            pygame.draw.rect(mundo_surface, (255, 180, 0),
                           (bomba_x - tamanho_bomba//2, bomba_y - tamanho_bomba//2,
                            tamanho_bomba, tamanho_bomba), 2, 3)

            # Texto "BOMBA" acima
            fonte_bomba = pygame.font.Font(None, 16)
            texto = fonte_bomba.render("BOMBA", True, (255, 200, 0))
            texto_rect = texto.get_rect(center=(int(bomba_x), int(bomba_y) - 18))
            mundo_surface.blit(texto, texto_rect)

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

        # Tela de vitória/round se o round ou partida acabou
        if self.round_terminado or self.partida_terminada:
            self._desenhar_tela_vitoria()

    def _desenhar_jogador_estilizado(self, surface, tempo_atual):
        """Desenha o jogador com visual idêntico ao da fase_base (Quadrado.desenhar)."""
        import math

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

        # ===== GHOST - INVISIBILIDADE =====
        # Se invisível, desenha apenas um contorno fantasmagórico
        if hasattr(jogador, 'invisivel') and jogador.invisivel:
            # Contorno fantasmagórico semi-transparente
            ghost_surface = pygame.Surface((tamanho + 10, tamanho + 10), pygame.SRCALPHA)
            # Desenha apenas contorno com efeito
            alpha = 60 + int(30 * math.sin(tempo_atual / 200))  # Pulsa entre 30-90
            cor_fantasma = (150, 150, 200, alpha)
            pygame.draw.rect(ghost_surface, cor_fantasma, (5, 5, tamanho, tamanho), 2, 3)
            # Partículas fantasmagóricas
            for i in range(3):
                px = 5 + int((tempo_atual / 100 + i * 30) % tamanho)
                py = 5 + int((tempo_atual / 150 + i * 20) % tamanho)
                pygame.draw.circle(ghost_surface, (200, 200, 255, alpha // 2), (px, py), 2)
            surface.blit(ghost_surface, (tela_x - 5, tela_y - 5))

            # Nome do jogador (mais transparente)
            nome_surface = self.fonte_pequena.render(self.nome_jogador, True, (100, 100, 150))
            nome_surface = pygame.transform.scale(nome_surface,
                (nome_surface.get_width() // 2, nome_surface.get_height() // 2))
            nome_surface.set_alpha(alpha)
            nome_rect = nome_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 14))
            surface.blit(nome_surface, nome_rect)
            return  # Não desenha o jogador normal

        # Piscar se invulnerável (mas não se for escudo do mago)
        escudo_ativo = hasattr(jogador, 'escudo_ativo') and jogador.escudo_ativo
        if jogador.invulneravel and not escudo_ativo and tempo_atual % 200 < 100:
            return

        # ====== CYAN TURBO - DESENHAR RASTRO ======
        if self.classe_jogador == "cyan" and hasattr(jogador, 'posicoes_turbo') and jogador.posicoes_turbo:
            for i, (pos_x, pos_y) in enumerate(jogador.posicoes_turbo):
                # Converter para coordenadas de tela
                rastro_tela_x = pos_x - self.camera_x
                rastro_tela_y = pos_y - self.camera_y

                # Calcular alpha (mais antigo = mais transparente)
                alpha = int(180 * (1 - i / len(jogador.posicoes_turbo)))

                # Calcular tamanho (mais antigo = menor)
                rastro_tamanho = int(tamanho * (1 - i / len(jogador.posicoes_turbo) * 0.7))

                # Cor do rastro (cyan mais escuro)
                cor_rastro = (0, max(0, jogador.cor[1] - 80), max(0, jogador.cor[2] - 80))

                # Desenhar rastro
                offset_x = (tamanho - rastro_tamanho) // 2
                offset_y = (tamanho - rastro_tamanho) // 2
                pygame.draw.rect(surface, cor_rastro,
                               (rastro_tela_x + offset_x, rastro_tela_y + offset_y,
                                rastro_tamanho, rastro_tamanho), 0, 2)

        # ====== EXPLOSIVE - EFEITO DE CHAMAS ======
        if self.classe_jogador == "explosive":
            import random
            for i in range(6):
                # Variação no tamanho e posição (proporcional ao tamanho menor)
                offset_x = random.uniform(-tamanho / 3, tamanho / 3)
                offset_y = random.uniform(-tamanho / 3, tamanho / 3)

                # Cores variando de laranja a amarelo
                cor_r = min(255, jogador.cor[0] + random.randint(-40, 40))
                cor_g = min(255, jogador.cor[1] + random.randint(-40, 20))
                cor_b = 0  # Sem componente azul para manter o visual de fogo

                tamanho_particula = random.randint(2, 5)

                # Desenhar partícula de fogo
                particula_x = int(tela_x - offset_x + random.uniform(0, tamanho))
                particula_y = int(tela_y - offset_y + random.uniform(0, tamanho))
                pygame.draw.circle(surface, (cor_r, cor_g, cor_b),
                                 (particula_x, particula_y), tamanho_particula)

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

        # ===== MAGO - ESCUDO PROTETOR =====
        if escudo_ativo:
            centro_x = tela_x + tamanho // 2
            centro_y = tela_y + tamanho // 2
            raio = tamanho + 8

            # Efeito de pulso do escudo
            pulso = math.sin(tempo_atual / 100) * 3
            raio_atual = int(raio + pulso)

            # Círculo externo do escudo (brilhante)
            for i in range(3):
                alpha = 100 - i * 30
                cor_escudo = (100, 150, 255)
                pygame.draw.circle(surface, cor_escudo,
                                  (centro_x, centro_y), raio_atual + i * 2, 2)

            # Aura interna
            shield_surface = pygame.Surface((raio_atual * 2 + 10, raio_atual * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (100, 150, 255, 50),
                              (raio_atual + 5, raio_atual + 5), raio_atual)
            surface.blit(shield_surface,
                        (centro_x - raio_atual - 5, centro_y - raio_atual - 5))

            # Partículas de energia ao redor do escudo
            num_particulas = 8
            for i in range(num_particulas):
                angulo = (tempo_atual / 500 + i * (2 * math.pi / num_particulas))
                px = centro_x + int(math.cos(angulo) * raio_atual)
                py = centro_y + int(math.sin(angulo) * raio_atual)
                pygame.draw.circle(surface, (200, 220, 255), (px, py), 3)

        # ===== MAGO - CHAPÉU DE MAGO =====
        if self.classe_jogador == "mago":
            chapeu_x = tela_x + tamanho // 2
            chapeu_y = tela_y - 2
            # Triângulo do chapéu (menor)
            pontos = [(chapeu_x, chapeu_y - 8), (chapeu_x - 7, chapeu_y + 3), (chapeu_x + 7, chapeu_y + 3)]
            pygame.draw.polygon(surface, (100, 50, 150), pontos)  # Roxo escuro
            pygame.draw.polygon(surface, (150, 100, 200), pontos, 1)  # Borda
            # Aba do chapéu (menor)
            pygame.draw.ellipse(surface, (100, 50, 150), (chapeu_x - 9, chapeu_y + 1, 18, 5))
            # Estrela animada (menor)
            brilho = 150 + int(50 * math.sin(tempo_atual / 200))
            pygame.draw.circle(surface, (255, 255, brilho), (chapeu_x, chapeu_y - 3), 2)

        # ===== GHOST - ROSTO ASSUSTADOR =====
        if self.classe_jogador == "ghost":
            # Aura fantasmagórica ao redor
            for i in range(2):
                aura_alpha = 40 - i * 15
                pygame.draw.rect(surface, (180, 180, 220),
                               (tela_x - i - 1, tela_y - i - 1, tamanho + i * 2 + 2, tamanho + i * 2 + 2), 1, 3)

            # Olhos vermelhos assustadores (pequenos, ajustados ao tamanho)
            olho_esquerdo_x = tela_x + tamanho // 3
            olho_direito_x = tela_x + 2 * tamanho // 3
            olho_y = tela_y + tamanho // 3

            # Brilho dos olhos
            pygame.draw.circle(surface, (255, 150, 150), (olho_esquerdo_x, olho_y), 3)
            pygame.draw.circle(surface, (255, 150, 150), (olho_direito_x, olho_y), 3)

            # Olhos internos (vermelho)
            pygame.draw.circle(surface, (255, 30, 30), (olho_esquerdo_x, olho_y), 2)
            pygame.draw.circle(surface, (255, 30, 30), (olho_direito_x, olho_y), 2)

            # Pupilas
            pygame.draw.circle(surface, (0, 0, 0), (olho_esquerdo_x, olho_y), 1)
            pygame.draw.circle(surface, (0, 0, 0), (olho_direito_x, olho_y), 1)

            # Boca assustadora (pequena)
            boca_x = tela_x + tamanho // 2
            boca_y = tela_y + 2 * tamanho // 3
            pygame.draw.ellipse(surface, (30, 0, 0), (boca_x - 4, boca_y, 8, 5))

            # Dentes pequenos
            for i in range(3):
                dente_x = boca_x - 3 + i * 3
                pygame.draw.rect(surface, (255, 255, 200), (dente_x, boca_y, 1, 2))

        # ===== GRANADA - CINTO COM GRANADAS =====
        if self.classe_jogador == "granada":
            # Cinto na cintura (65% da altura)
            cinto_y = tela_y + int(tamanho * 0.65)

            # Linha do cinto (dourado)
            pygame.draw.line(surface, (200, 150, 50),
                           (tela_x + 2, cinto_y),
                           (tela_x + tamanho - 2, cinto_y), 2)

            # 3 granadas penduradas no cinto (pequenas)
            num_granadas = 3
            espacamento = tamanho // (num_granadas + 1)

            for i in range(num_granadas):
                granada_x = tela_x + espacamento * (i + 1)
                granada_y = cinto_y + 3

                # Corpo da granada (pequeno)
                pygame.draw.circle(surface, (60, 120, 60), (granada_x, granada_y), 2)
                pygame.draw.circle(surface, (40, 80, 40), (granada_x, granada_y), 2, 1)

                # Bocal (topo)
                pygame.draw.rect(surface, (150, 150, 150),
                               (granada_x - 1, granada_y - 3, 2, 2))

        # ===== METRALHADORA - VISUAL TÁTICO =====
        if self.classe_jogador == "metralhadora":
            centro_x = tela_x + tamanho // 2

            # Padrão de camuflagem (manchas pequenas)
            import random
            random.seed(42)  # Seed fixa para não piscar
            for _ in range(4):
                mancha_x = tela_x + random.randint(2, tamanho - 2)
                mancha_y = tela_y + random.randint(2, tamanho - 2)
                cor_mancha = random.choice([(70, 80, 55), (50, 60, 40)])
                pygame.draw.circle(surface, cor_mancha, (mancha_x, mancha_y), 2)

            # Colete tático (contorno)
            colete_x = tela_x + 2
            colete_y = tela_y + 3
            colete_w = tamanho - 4
            colete_h = tamanho - 5
            pygame.draw.rect(surface, (30, 35, 25), (colete_x, colete_y, colete_w, colete_h), 1, 2)

            # Faixas MOLLE no colete
            for i in range(2):
                faixa_y = colete_y + 4 + i * 5
                pygame.draw.line(surface, (100, 100, 110),
                               (colete_x + 2, faixa_y),
                               (colete_x + colete_w - 2, faixa_y), 1)

            # NVG (óculos de visão noturna) - acima da cabeça
            nvg_y = tela_y - 1
            nvg_esq_x = centro_x - 4
            nvg_dir_x = centro_x + 3

            # Suporte
            pygame.draw.line(surface, (100, 100, 110),
                           (centro_x - 5, nvg_y), (centro_x + 5, nvg_y), 1)

            # Lentes NVG
            pygame.draw.circle(surface, (20, 20, 40), (nvg_esq_x, nvg_y + 2), 2)
            pygame.draw.circle(surface, (0, 255, 100), (nvg_esq_x, nvg_y + 2), 1)
            pygame.draw.circle(surface, (20, 20, 40), (nvg_dir_x, nvg_y + 2), 2)
            pygame.draw.circle(surface, (0, 255, 100), (nvg_dir_x, nvg_y + 2), 1)

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

    def _desenhar_granada_mao(self, surface, tempo_atual):
        """Desenha uma granada na mão do jogador (classe granada do Time T)."""
        import math
        from src.utils.display_manager import convert_mouse_position

        # Posição do jogador na tela
        jogador_tela_x = self.jogador.x - self.camera_x
        jogador_tela_y = self.jogador.y - self.camera_y
        centro_x = jogador_tela_x + TAMANHO_MULTIPLAYER // 2
        centro_y = jogador_tela_y + TAMANHO_MULTIPLAYER // 2

        # Converter posição do mouse para obter direção
        pos_mouse_tela = convert_mouse_position(pygame.mouse.get_pos())
        pos_mouse_mundo = self._converter_mouse_para_mundo(pos_mouse_tela)
        pos_mouse_relativo = (
            pos_mouse_mundo[0] - self.camera_x,
            pos_mouse_mundo[1] - self.camera_y
        )

        # Calcular direção para o mouse
        dx = pos_mouse_relativo[0] - centro_x
        dy = pos_mouse_relativo[1] - centro_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist

        # Posição da mão (em frente ao jogador)
        distancia_mao = 20
        mao_x = centro_x + dx * distancia_mao
        mao_y = centro_y + dy * distancia_mao

        # Desenhar braço
        pygame.draw.line(surface, (101, 67, 33), (centro_x, centro_y),
                        (mao_x - dx * 5, mao_y - dy * 5), 4)
        pygame.draw.line(surface, (180, 140, 100),
                        (mao_x - dx * 5, mao_y - dy * 5), (mao_x, mao_y), 3)

        # Desenhar mão
        pygame.draw.circle(surface, (180, 140, 100), (int(mao_x), int(mao_y)), 4)

        # Desenhar granada na mão
        granada_x = mao_x + dx * 8
        granada_y = mao_y + dy * 8

        # Corpo da granada
        pygame.draw.circle(surface, (60, 120, 60), (int(granada_x), int(granada_y)), 7)
        pygame.draw.circle(surface, (40, 80, 40), (int(granada_x), int(granada_y)), 7, 1)

        # Detalhes da granada
        pygame.draw.line(surface, (40, 80, 40),
                        (granada_x - 5, granada_y), (granada_x + 5, granada_y), 2)
        pygame.draw.line(surface, (40, 80, 40),
                        (granada_x, granada_y - 5), (granada_x, granada_y + 5), 2)

        # Topo da granada (bocal)
        pygame.draw.rect(surface, (150, 150, 150),
                        (granada_x - 3, granada_y - 11, 6, 4), 0, 2)

        # Pino amarelo
        pygame.draw.circle(surface, (220, 220, 100), (int(granada_x + 6), int(granada_y - 8)), 3, 2)

        # Efeito de brilho/pulso
        if (tempo_atual // 200) % 2 == 0:
            pygame.draw.circle(surface, (100, 255, 100), (int(granada_x), int(granada_y)), 10, 2)

    def _desenhar_granada_selecionada(self, surface, tempo_atual):
        """Desenha a granada selecionada com trajetória prevista (igual granada.py)."""
        import math
        from src.utils.display_manager import convert_mouse_position

        # Posição do jogador na tela
        jogador_tela_x = self.jogador.x - self.camera_x
        jogador_tela_y = self.jogador.y - self.camera_y
        centro_x = jogador_tela_x + TAMANHO_MULTIPLAYER // 2
        centro_y = jogador_tela_y + TAMANHO_MULTIPLAYER // 2

        # Converter posição do mouse para obter direção
        pos_mouse_tela = convert_mouse_position(pygame.mouse.get_pos())
        pos_mouse_mundo = self._converter_mouse_para_mundo(pos_mouse_tela)
        pos_mouse_relativo = (
            pos_mouse_mundo[0] - self.camera_x,
            pos_mouse_mundo[1] - self.camera_y
        )

        # Calcular direção para o mouse
        dx = pos_mouse_relativo[0] - centro_x
        dy = pos_mouse_relativo[1] - centro_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist

        # Calcular trajetória prevista
        trajetoria = self._calcular_trajetoria_granada(centro_x, centro_y, dx, dy)

        # Desenhar linha da trajetória (pontilhada)
        if len(trajetoria) > 1:
            for i in range(len(trajetoria) - 1):
                if i % 2 == 0:
                    pygame.draw.line(surface, (100, 200, 100), trajetoria[i], trajetoria[i + 1], 1)

            # Desenhar indicador de explosão no ponto final
            if trajetoria:
                pos_final = trajetoria[-1]

                # Círculo pequeno mostrando ponto de impacto
                pulso = int(3 * abs(math.sin(tempo_atual / 200)))
                pygame.draw.circle(surface, (255, 100, 100), pos_final, 8 + pulso, 1)

                # X pequeno marcando o ponto
                tamanho_x = 4
                pygame.draw.line(surface, (255, 80, 80),
                               (pos_final[0] - tamanho_x, pos_final[1] - tamanho_x),
                               (pos_final[0] + tamanho_x, pos_final[1] + tamanho_x), 1)
                pygame.draw.line(surface, (255, 80, 80),
                               (pos_final[0] + tamanho_x, pos_final[1] - tamanho_x),
                               (pos_final[0] - tamanho_x, pos_final[1] + tamanho_x), 1)

        # Posição da granada na mão
        distancia_desenho = 12
        granada_x = centro_x + dx * distancia_desenho
        granada_y = centro_y + dy * distancia_desenho

        # Tamanho e cores da granada (pequena)
        tamanho_granada = 3
        cor_granada = (60, 120, 60)

        # Desenhar corpo da granada
        pygame.draw.circle(surface, cor_granada, (int(granada_x), int(granada_y)), tamanho_granada)
        pygame.draw.circle(surface, (40, 80, 40), (int(granada_x), int(granada_y)), tamanho_granada, 1)

    def _calcular_trajetoria_granada(self, centro_x, centro_y, dx, dy):
        """Calcula a trajetória prevista da granada com colisão nas paredes."""
        import math

        velocidade_base = 10.0
        vel_x = dx * velocidade_base
        vel_y = dy * velocidade_base
        fricao = 0.99
        elasticidade = 0.7
        raio = 4

        # Posição inicial (em coordenadas de tela)
        pos_x = centro_x + dx * TAMANHO_MULTIPLAYER
        pos_y = centro_y + dy * TAMANHO_MULTIPLAYER

        trajetoria = []

        # Simular até 90 frames
        for frame in range(90):
            vel_x *= fricao
            vel_y *= fricao

            # Próxima posição
            nova_x = pos_x + vel_x
            nova_y = pos_y + vel_y

            # Converter para coordenadas do mundo para checar colisão
            mundo_x = nova_x + self.camera_x
            mundo_y = nova_y + self.camera_y

            # Verificar colisão X
            rect_teste_x = pygame.Rect(mundo_x - raio, pos_y + self.camera_y - raio, raio * 2, raio * 2)
            colisoes_x = self.tilemap.get_colisoes_proximas(rect_teste_x)
            colidiu_x = False
            for rect_colisao in colisoes_x:
                if rect_teste_x.colliderect(rect_colisao):
                    vel_x = -vel_x * elasticidade
                    nova_x = pos_x
                    colidiu_x = True
                    break

            # Verificar colisão Y
            rect_teste_y = pygame.Rect(pos_x + self.camera_x - raio, mundo_y - raio, raio * 2, raio * 2)
            colisoes_y = self.tilemap.get_colisoes_proximas(rect_teste_y)
            colidiu_y = False
            for rect_colisao in colisoes_y:
                if rect_teste_y.colliderect(rect_colisao):
                    vel_y = -vel_y * elasticidade
                    nova_y = pos_y
                    colidiu_y = True
                    break

            # Aplicar nova posição
            pos_x = nova_x
            pos_y = nova_y

            # Adicionar ponto à trajetória (a cada 3 frames)
            if frame % 3 == 0:
                trajetoria.append((int(pos_x), int(pos_y)))

            # Parar se a velocidade for muito baixa
            velocidade_total = math.sqrt(vel_x**2 + vel_y**2)
            if velocidade_total < 0.5:
                break

        return trajetoria

    def _desenhar_arma_jogador(self, surface, tempo_atual):
        """Desenha a arma equipada (pequena) com laser funcional."""
        import math

        if self.jogador.vidas <= 0:
            return

        # Se ghost invisível, não desenha arma
        if hasattr(self.jogador, 'invisivel') and self.jogador.invisivel:
            return

        # Se granada selecionada, desenha granada ao invés de arma
        if hasattr(self.jogador, 'granada_selecionada') and self.jogador.granada_selecionada:
            if hasattr(self.jogador, 'granadas') and self.jogador.granadas > 0:
                self._desenhar_granada_selecionada(surface, tempo_atual)
                return

        # Se não tem arma equipada, não desenha nada
        if not self.arma_equipada:
            return

        # Escala para reduzir o tamanho das armas
        escala_arma = 0.35
        tamanho_temp = 150

        # Posição do jogador na tela
        jogador_tela_x = self.jogador.x - self.camera_x
        jogador_tela_y = self.jogador.y - self.camera_y
        centro_jogador_x = jogador_tela_x + TAMANHO_MULTIPLAYER // 2
        centro_jogador_y = jogador_tela_y + TAMANHO_MULTIPLAYER // 2

        # Converter posição do mouse
        from src.utils.display_manager import convert_mouse_position
        pos_mouse_tela = convert_mouse_position(pygame.mouse.get_pos())
        pos_mouse_mundo = self._converter_mouse_para_mundo(pos_mouse_tela)
        pos_mouse_relativo = (
            pos_mouse_mundo[0] - self.camera_x,
            pos_mouse_mundo[1] - self.camera_y
        )

        # Calcular direção para o mouse
        dx = pos_mouse_relativo[0] - centro_jogador_x
        dy = pos_mouse_relativo[1] - centro_jogador_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist

        # --- PARTE 1: Desenhar arma escalada ---
        temp_surface = pygame.Surface((tamanho_temp, tamanho_temp), pygame.SRCALPHA)

        class JogadorTemp:
            pass

        jogador_temp = JogadorTemp()
        jogador_temp.x = tamanho_temp // 2 - TAMANHO_MULTIPLAYER // 2
        jogador_temp.y = tamanho_temp // 2 - TAMANHO_MULTIPLAYER // 2
        jogador_temp.tamanho = TAMANHO_MULTIPLAYER
        jogador_temp.cor = self.jogador.cor
        jogador_temp.tempo_ultimo_tiro = self.jogador.tempo_ultimo_tiro
        jogador_temp.tempo_cooldown = self._obter_cooldown_arma()

        # Mouse na direção certa mas perto (para arma apontar certo)
        pos_mouse_temp = (
            tamanho_temp // 2 + dx * 60,
            tamanho_temp // 2 + dy * 60
        )

        # Desenhar arma na superfície temporária (desativar laser)
        if self.arma_equipada == 'desert_eagle':
            jogador_temp.desert_eagle_ativa = True
            desenhar_desert_eagle(temp_surface, jogador_temp, pos_mouse_temp)
        elif self.arma_equipada == 'spas12':
            jogador_temp.spas12_ativa = True
            jogador_temp.recuo_spas12 = getattr(self.jogador, 'recuo_spas12', 0)
            jogador_temp.tempo_recuo = getattr(self.jogador, 'tempo_recuo', 0)
            desenhar_spas12(temp_surface, jogador_temp, tempo_atual, pos_mouse_temp)
        elif self.arma_equipada == 'metralhadora':
            jogador_temp.metralhadora_ativa = False  # Desativa laser na temp
            jogador_temp.tiros_metralhadora = 100
            desenhar_metralhadora(temp_surface, jogador_temp, tempo_atual, pos_mouse_temp)
        elif self.arma_equipada == 'sniper':
            jogador_temp.sniper_ativa = False  # Desativa laser na temp
            jogador_temp.sniper_mirando = False
            jogador_temp.recuo_sniper = getattr(self.jogador, 'recuo_sniper', 0)
            desenhar_sniper(temp_surface, jogador_temp, tempo_atual, pos_mouse_temp)

        # Escalar e desenhar arma
        novo_tamanho = int(tamanho_temp * escala_arma)
        arma_reduzida = pygame.transform.scale(temp_surface, (novo_tamanho, novo_tamanho))
        arma_x = centro_jogador_x - novo_tamanho // 2
        arma_y = centro_jogador_y - novo_tamanho // 2
        surface.blit(arma_reduzida, (arma_x, arma_y))

        # --- PARTE 2: Desenhar laser separadamente ---
        comprimento_arma_escalado = 12
        ponta_x = centro_jogador_x + dx * comprimento_arma_escalado
        ponta_y = centro_jogador_y + dy * comprimento_arma_escalado

        if self.arma_equipada == 'metralhadora':
            # Laser vermelho pontilhado
            cor_laser = (200, 50, 50)
            passos = int(dist // 6)
            for i in range(0, passos, 2):
                laser_x = ponta_x + dx * (i * 6)
                laser_y = ponta_y + dy * (i * 6)
                pygame.draw.circle(surface, cor_laser, (int(laser_x), int(laser_y)), 1)

        elif self.arma_equipada == 'sniper':
            # Laser vermelho pontilhado (só aparece quando mira com botão direito)
            if pygame.mouse.get_pressed()[2]:  # Botão direito pressionado
                cor_laser = (200, 50, 50)
                passos = int(dist // 6)
                for i in range(0, passos, 2):
                    laser_x = ponta_x + dx * (i * 6)
                    laser_y = ponta_y + dy * (i * 6)
                    pygame.draw.circle(surface, cor_laser, (int(laser_x), int(laser_y)), 1)

    def _desenhar_arma_bot(self, surface, bot, tempo_atual):
        """Desenha a arma equipada do bot seguindo a direção da mira."""
        import math

        if bot.vidas <= 0:
            return

        # Se não tem arma equipada, não desenha nada
        arma = getattr(bot, 'arma', None)
        if not arma:
            return

        # Escala para reduzir o tamanho das armas
        escala_arma = 0.35
        tamanho_temp = 150

        # Posição do bot na tela
        bot_tela_x = bot.x - self.camera_x
        bot_tela_y = bot.y - self.camera_y
        centro_bot_x = bot_tela_x + TAMANHO_MULTIPLAYER // 2
        centro_bot_y = bot_tela_y + TAMANHO_MULTIPLAYER // 2

        # Calcular direção da mira (para o inimigo ou para o alvo)
        alvo_x = bot.alvo_x
        alvo_y = bot.alvo_y

        # Se tem inimigo, mirar nele
        if bot.alvo_inimigo and bot.alvo_inimigo.vidas > 0:
            alvo_x = bot.alvo_inimigo.x + TAMANHO_MULTIPLAYER // 2
            alvo_y = bot.alvo_inimigo.y + TAMANHO_MULTIPLAYER // 2

        # Converter alvo para coordenadas de tela
        alvo_tela_x = alvo_x - self.camera_x
        alvo_tela_y = alvo_y - self.camera_y

        # Calcular direção
        dx = alvo_tela_x - centro_bot_x
        dy = alvo_tela_y - centro_bot_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist
        else:
            dx, dy = 1, 0  # Default para direita

        # Criar superfície temporária para a arma
        temp_surface = pygame.Surface((tamanho_temp, tamanho_temp), pygame.SRCALPHA)

        class BotTemp:
            pass

        bot_temp = BotTemp()
        bot_temp.x = tamanho_temp // 2 - TAMANHO_MULTIPLAYER // 2
        bot_temp.y = tamanho_temp // 2 - TAMANHO_MULTIPLAYER // 2
        bot_temp.tamanho = TAMANHO_MULTIPLAYER
        bot_temp.cor = bot.cor
        bot_temp.tempo_ultimo_tiro = getattr(bot, 'tempo_ultimo_tiro', 0)
        bot_temp.tempo_cooldown = getattr(bot, 'cadencia_arma', 800)

        # Posição do mouse temp (direção da mira)
        pos_mouse_temp = (
            tamanho_temp // 2 + dx * 60,
            tamanho_temp // 2 + dy * 60
        )

        # Desenhar arma na superfície temporária
        if arma == 'desert_eagle':
            bot_temp.desert_eagle_ativa = True
            desenhar_desert_eagle(temp_surface, bot_temp, pos_mouse_temp)
        elif arma == 'spas12':
            bot_temp.spas12_ativa = True
            bot_temp.recuo_spas12 = 0
            bot_temp.tempo_recuo = 0
            desenhar_spas12(temp_surface, bot_temp, tempo_atual, pos_mouse_temp)
        elif arma == 'metralhadora':
            bot_temp.metralhadora_ativa = False  # Sem laser
            bot_temp.tiros_metralhadora = 100
            desenhar_metralhadora(temp_surface, bot_temp, tempo_atual, pos_mouse_temp)
        elif arma == 'sniper':
            bot_temp.sniper_ativa = False  # Sem laser
            bot_temp.sniper_mirando = False
            bot_temp.recuo_sniper = 0
            desenhar_sniper(temp_surface, bot_temp, tempo_atual, pos_mouse_temp)

        # Escalar e desenhar arma
        novo_tamanho = int(tamanho_temp * escala_arma)
        arma_reduzida = pygame.transform.scale(temp_surface, (novo_tamanho, novo_tamanho))
        arma_x = centro_bot_x - novo_tamanho // 2
        arma_y = centro_bot_y - novo_tamanho // 2
        surface.blit(arma_reduzida, (arma_x, arma_y))

    def _desenhar_tela_vitoria(self):
        """Desenha a tela de vitória com o vencedor por time."""
        from src.utils.visual import desenhar_texto

        # Overlay escuro
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.tela.blit(overlay, (0, 0))

        # Verificar se é fim de partida ou fim de round
        if self.partida_terminada:
            # Fim de partida - tela final
            time_vencedor = getattr(self, 'time_vencedor', None)
            jogador_venceu = (time_vencedor == self.time_jogador)

            if jogador_venceu:
                desenhar_texto(self.tela, "VITORIA!", 90, VERDE, LARGURA // 2, ALTURA // 2 - 120)
                desenhar_texto(self.tela, f"Seu time ({self.vencedor}) venceu a partida!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 40)
            else:
                desenhar_texto(self.tela, "DERROTA", 90, VERMELHO, LARGURA // 2, ALTURA // 2 - 120)
                desenhar_texto(self.tela, f"{self.vencedor} venceu a partida!", 36, AMARELO, LARGURA // 2, ALTURA // 2 - 40)

            # Placar final
            desenhar_texto(self.tela, f"PLACAR FINAL", 30, BRANCO, LARGURA // 2, ALTURA // 2 + 20)
            desenhar_texto(self.tela, f"Time T  {self.rounds_time_t}  x  {self.rounds_time_q}  Time Q", 50, BRANCO, LARGURA // 2, ALTURA // 2 + 70)
            desenhar_texto(self.tela, "Pressione ESC para sair", 24, (150, 150, 150), LARGURA // 2, ALTURA // 2 + 130)
        else:
            # Fim de round - mostrar quem venceu e tempo para próximo
            time_vencedor = getattr(self, 'time_vencedor', None)
            jogador_venceu = (time_vencedor == self.time_jogador)

            if jogador_venceu:
                desenhar_texto(self.tela, "ROUND VENCIDO!", 70, VERDE, LARGURA // 2, ALTURA // 2 - 80)
            else:
                desenhar_texto(self.tela, "ROUND PERDIDO", 70, VERMELHO, LARGURA // 2, ALTURA // 2 - 80)

            # Placar atual
            desenhar_texto(self.tela, f"Time T  {self.rounds_time_t}  x  {self.rounds_time_q}  Time Q", 45, BRANCO, LARGURA // 2, ALTURA // 2)

            # Tempo para próximo round
            tempo_restante = max(0, (self.tempo_proximo_round - pygame.time.get_ticks()) // 1000 + 1)
            desenhar_texto(self.tela, f"Proximo round em {tempo_restante}s...", 28, AMARELO, LARGURA // 2, ALTURA // 2 + 60)

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
            # Não desenhar bots mortos
            if bot.vidas <= 0:
                continue

            # Posição na tela (com câmera)
            tela_x = bot.x - self.camera_x
            tela_y = bot.y - self.camera_y
            tamanho = TAMANHO_MULTIPLAYER

            # Só desenhar se estiver visível na tela
            if -50 < tela_x < largura_visivel + 50 and -50 < tela_y < altura_visivel + 50:
                # === GHOST - INVISIBILIDADE (VERIFICAR ANTES DE DESENHAR!) ===
                if getattr(bot, 'invisivel', False):
                    bot_time = getattr(bot, 'time', None)
                    # Se o bot é do time INIMIGO, fica COMPLETAMENTE invisível - NÃO DESENHAR NADA
                    if bot_time != self.time_jogador:
                        continue  # Pular completamente este bot
                    else:
                        # Aliado invisível - desenhar apenas contorno fantasmagórico
                        import math
                        ghost_surface = pygame.Surface((tamanho + 10, tamanho + 10), pygame.SRCALPHA)
                        alpha = 60 + int(30 * math.sin(tempo_atual / 200))
                        cor_fantasma = (150, 150, 200, alpha)
                        pygame.draw.rect(ghost_surface, cor_fantasma, (5, 5, tamanho, tamanho), 2, 3)
                        surface.blit(ghost_surface, (tela_x - 5, tela_y - 5))
                        # Desenhar nome do aliado invisível (para identificar)
                        nome_surface = self.fonte_pequena.render(bot.nome, True, (150, 150, 200))
                        nome_surface = pygame.transform.scale(nome_surface,
                            (nome_surface.get_width() // 2, nome_surface.get_height() // 2))
                        nome_surface.set_alpha(alpha)
                        nome_rect = nome_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 14))
                        surface.blit(nome_surface, nome_rect)
                        continue  # Pular o resto do desenho

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

                # ====== VISUAIS DE CLASSE DO BOT ======
                classe_bot = getattr(bot, 'classe', None)

                # === MAGO - ESCUDO PROTETOR ===
                if getattr(bot, 'escudo_ativo', False):
                    import math
                    centro_x = tela_x + tamanho // 2
                    centro_y = tela_y + tamanho // 2
                    raio = tamanho + 8
                    pulso = math.sin(tempo_atual / 100) * 3
                    raio_atual = int(raio + pulso)
                    for i in range(3):
                        pygame.draw.circle(surface, (100, 150, 255),
                                          (centro_x, centro_y), raio_atual + i * 2, 2)

                # === MAGO - CHAPÉU ===
                if classe_bot == 'mago':
                    chapeu_x = tela_x + tamanho // 2
                    chapeu_y = tela_y - 2
                    pontos = [(chapeu_x, chapeu_y - 8), (chapeu_x - 7, chapeu_y + 3), (chapeu_x + 7, chapeu_y + 3)]
                    pygame.draw.polygon(surface, (100, 50, 150), pontos)
                    pygame.draw.polygon(surface, (150, 100, 200), pontos, 1)
                    pygame.draw.ellipse(surface, (100, 50, 150), (chapeu_x - 9, chapeu_y + 1, 18, 5))
                    import math
                    brilho = 150 + int(50 * math.sin(tempo_atual / 200))
                    pygame.draw.circle(surface, (255, 255, brilho), (chapeu_x, chapeu_y - 3), 2)

                # === GHOST - ROSTO ASSUSTADOR ===
                elif classe_bot == 'ghost' and not getattr(bot, 'invisivel', False):
                    # Aura
                    for i in range(2):
                        pygame.draw.rect(surface, (180, 180, 220),
                                       (tela_x - i - 1, tela_y - i - 1, tamanho + i * 2 + 2, tamanho + i * 2 + 2), 1, 3)
                    # Olhos vermelhos
                    olho_esq_x = tela_x + tamanho // 3
                    olho_dir_x = tela_x + 2 * tamanho // 3
                    olho_y = tela_y + tamanho // 3
                    pygame.draw.circle(surface, (255, 150, 150), (olho_esq_x, olho_y), 3)
                    pygame.draw.circle(surface, (255, 150, 150), (olho_dir_x, olho_y), 3)
                    pygame.draw.circle(surface, (255, 30, 30), (olho_esq_x, olho_y), 2)
                    pygame.draw.circle(surface, (255, 30, 30), (olho_dir_x, olho_y), 2)
                    pygame.draw.circle(surface, (0, 0, 0), (olho_esq_x, olho_y), 1)
                    pygame.draw.circle(surface, (0, 0, 0), (olho_dir_x, olho_y), 1)
                    # Boca
                    boca_x = tela_x + tamanho // 2
                    boca_y = tela_y + 2 * tamanho // 3
                    pygame.draw.ellipse(surface, (30, 0, 0), (boca_x - 4, boca_y, 8, 5))

                # === GRANADA - CINTO ===
                elif classe_bot == 'granada':
                    cinto_y = tela_y + int(tamanho * 0.65)
                    pygame.draw.line(surface, (200, 150, 50),
                                   (tela_x + 2, cinto_y), (tela_x + tamanho - 2, cinto_y), 2)
                    num_granadas = 3
                    espacamento = tamanho // (num_granadas + 1)
                    for i in range(num_granadas):
                        granada_x = tela_x + espacamento * (i + 1)
                        granada_y = cinto_y + 3
                        pygame.draw.circle(surface, (60, 120, 60), (granada_x, granada_y), 2)

                # === METRALHADORA - VISUAL TÁTICO ===
                elif classe_bot == 'metralhadora':
                    centro_x = tela_x + tamanho // 2

                    # Padrão de camuflagem (manchas pequenas)
                    import random
                    random.seed(id(bot))  # Seed fixa baseada no bot para não piscar
                    for _ in range(4):
                        mancha_x = tela_x + random.randint(2, tamanho - 2)
                        mancha_y = tela_y + random.randint(2, tamanho - 2)
                        cor_mancha = random.choice([(70, 80, 55), (50, 60, 40)])
                        pygame.draw.circle(surface, cor_mancha, (mancha_x, mancha_y), 2)

                    # Colete tático (contorno)
                    colete_x = tela_x + 2
                    colete_y = tela_y + 3
                    colete_w = tamanho - 4
                    colete_h = tamanho - 5
                    pygame.draw.rect(surface, (30, 35, 25), (colete_x, colete_y, colete_w, colete_h), 1, 2)

                    # Faixas MOLLE no colete
                    for i in range(2):
                        faixa_y = colete_y + 4 + i * 5
                        pygame.draw.line(surface, (100, 100, 110),
                                       (colete_x + 2, faixa_y),
                                       (colete_x + colete_w - 2, faixa_y), 1)

                    # NVG (óculos de visão noturna) - acima da cabeça
                    nvg_y = tela_y - 1
                    nvg_esq_x = centro_x - 4
                    nvg_dir_x = centro_x + 3

                    # Suporte
                    pygame.draw.line(surface, (100, 100, 110),
                                   (centro_x - 5, nvg_y), (centro_x + 5, nvg_y), 1)

                    # Lentes NVG
                    pygame.draw.circle(surface, (20, 20, 40), (nvg_esq_x, nvg_y + 2), 2)
                    pygame.draw.circle(surface, (0, 255, 100), (nvg_esq_x, nvg_y + 2), 1)
                    pygame.draw.circle(surface, (20, 20, 40), (nvg_dir_x, nvg_y + 2), 2)
                    pygame.draw.circle(surface, (0, 255, 100), (nvg_dir_x, nvg_y + 2), 1)

                # === EXPLOSIVE - CHAMAS ===
                elif classe_bot == 'explosive':
                    import random
                    for _ in range(6):
                        offset_x = random.uniform(-tamanho / 3, tamanho / 3)
                        offset_y = random.uniform(-tamanho / 3, tamanho / 3)
                        cor_r = min(255, cor[0] + random.randint(-40, 40))
                        cor_g = min(255, cor[1] + random.randint(-40, 20))
                        cor_b = 0
                        tamanho_particula = random.randint(2, 5)
                        particula_x = int(tela_x - offset_x + random.uniform(0, tamanho))
                        particula_y = int(tela_y - offset_y + random.uniform(0, tamanho))
                        pygame.draw.circle(surface, (cor_r, cor_g, cor_b),
                                         (particula_x, particula_y), tamanho_particula)

                # === CYAN - RASTRO TURBO ===
                elif classe_bot == 'cyan':
                    if getattr(bot, 'habilidade_ativa', False) and hasattr(bot, 'posicoes_turbo'):
                        # Salvar posição para rastro
                        bot.posicoes_turbo.insert(0, (bot.x, bot.y))
                        if len(bot.posicoes_turbo) > 15:
                            bot.posicoes_turbo.pop()
                        # Desenhar rastro
                        for i, (pos_x, pos_y) in enumerate(bot.posicoes_turbo):
                            rastro_tela_x = pos_x - self.camera_x
                            rastro_tela_y = pos_y - self.camera_y
                            rastro_tamanho = int(tamanho * (1 - i / len(bot.posicoes_turbo) * 0.7))
                            cor_rastro = (0, max(0, cor[1] - 80), max(0, cor[2] - 80))
                            offset_x = (tamanho - rastro_tamanho) // 2
                            offset_y = (tamanho - rastro_tamanho) // 2
                            pygame.draw.rect(surface, cor_rastro,
                                           (rastro_tela_x + offset_x, rastro_tela_y + offset_y,
                                            rastro_tamanho, rastro_tamanho), 0, 2)

                # Desenhar arma do bot (se tiver)
                self._desenhar_arma_bot(surface, bot, tempo_atual)

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

                # Indicador "BOMBER" se for o bomber (em cima do nome)
                if getattr(bot, 'é_bomber', False) and not self.bomba_plantada:
                    bomber_surface = self.fonte_pequena.render("BOMBER", True, (255, 150, 0))
                    bomber_surface = pygame.transform.scale(bomber_surface,
                        (bomber_surface.get_width() // 2, bomber_surface.get_height() // 2))
                    bomber_rect = bomber_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 22))
                    surface.blit(bomber_surface, bomber_rect)

                # Indicador de plantio com barra de progresso
                if getattr(bot, 'bot_plantando', False):
                    # Calcular progresso
                    tempo_plantando = tempo_atual - getattr(bot, 'bot_tempo_inicio_plantar', tempo_atual)
                    progresso = min(1.0, tempo_plantando / self.tempo_para_plantar)

                    # Desenhar barra de progresso acima do bot
                    barra_largura = tamanho + 10
                    barra_altura = 5
                    barra_x = tela_x - 5
                    barra_y = tela_y - 30

                    # Fundo da barra
                    pygame.draw.rect(surface, (50, 50, 50), (barra_x, barra_y, barra_largura, barra_altura), 0, 2)

                    # Progresso (verde)
                    progresso_largura = int(barra_largura * progresso)
                    if progresso_largura > 0:
                        pygame.draw.rect(surface, (100, 255, 100), (barra_x, barra_y, progresso_largura, barra_altura), 0, 2)

                    # Texto "PLANTANDO"
                    plant_surface = self.fonte_pequena.render("PLANTANDO", True, (255, 200, 50))
                    plant_surface = pygame.transform.scale(plant_surface,
                        (plant_surface.get_width() // 2, plant_surface.get_height() // 2))
                    plant_rect = plant_surface.get_rect(center=(tela_x + tamanho // 2, tela_y - 38))
                    surface.blit(plant_surface, plant_rect)

    def _desenhar_info_multiplayer(self):
        """Desenha informações específicas do multiplayer no HUD."""
        from src.utils.visual import desenhar_texto

        # Mostrar tempo de compra e dinheiro no topo da tela
        if self.em_tempo_compra:
            tempo_restante = max(0, (self.tempo_compra - (pygame.time.get_ticks() - self.tempo_inicio_round)) // 1000)
            # Barra de tempo de compra
            pygame.draw.rect(self.tela, (50, 50, 80), (LARGURA // 2 - 150, 10, 300, 40), 0, 10)
            pygame.draw.rect(self.tela, AMARELO, (LARGURA // 2 - 150, 10, 300, 40), 3, 10)
            desenhar_texto(self.tela, f"TEMPO DE COMPRA: {tempo_restante}s", 22, AMARELO, LARGURA // 2, 22)
            desenhar_texto(self.tela, "Pressione B para abrir loja", 14, BRANCO, LARGURA // 2, 40)

        # Mostrar dinheiro
        pygame.draw.rect(self.tela, (40, 60, 40), (10, 10, 150, 35), 0, 8)
        pygame.draw.rect(self.tela, VERDE, (10, 10, 150, 35), 2, 8)
        desenhar_texto(self.tela, f"${self.moedas}", 24, VERDE, 85, 28)

        # Mostrar arma equipada ou granadas
        granada_selecionada = getattr(self.jogador, 'granada_selecionada', False)
        granadas = getattr(self.jogador, 'granadas', 0)

        if granada_selecionada and granadas > 0:
            # Mostra granadas selecionadas
            pygame.draw.rect(self.tela, (80, 60, 30), (10, 50, 150, 25), 0, 5)
            pygame.draw.rect(self.tela, (60, 255, 60), (10, 50, 150, 25), 2, 5)
            desenhar_texto(self.tela, f"GRANADA x{granadas}", 16, (60, 255, 60), 85, 63)
        elif self.arma_equipada:
            arma_nome = self.armas_disponiveis[self.arma_equipada]['nome']
            pygame.draw.rect(self.tela, (60, 50, 40), (10, 50, 150, 25), 0, 5)
            desenhar_texto(self.tela, arma_nome, 16, LARANJA, 85, 63)

        # Mostrar classe e habilidade (para classes com habilidade)
        if self.classe_jogador:
            from src.game.selecao_classes import obter_dados_classe
            dados = obter_dados_classe(self.classe_jogador, self.time_jogador)
            if dados:
                # Nome da classe
                nome_classe = dados.get("nome", self.classe_jogador)
                cor_classe = dados.get("cor", (255, 255, 255))
                pygame.draw.rect(self.tela, (30, 30, 50), (10, 80, 150, 25), 0, 5)
                pygame.draw.rect(self.tela, cor_classe, (10, 80, 150, 25), 2, 5)
                desenhar_texto(self.tela, nome_classe, 14, cor_classe, 85, 93)

                # Cooldown da habilidade (se tiver)
                cooldown = dados.get("habilidade_cooldown", 0)
                if cooldown > 0:
                    tempo_atual = pygame.time.get_ticks()
                    tempo_desde_uso = tempo_atual - self.habilidade_cooldown
                    if tempo_desde_uso < cooldown:
                        # Mostrar barra de cooldown
                        progresso = tempo_desde_uso / cooldown
                        barra_largura = 150
                        pygame.draw.rect(self.tela, (40, 40, 40), (10, 108, barra_largura, 8), 0, 3)
                        pygame.draw.rect(self.tela, cor_classe, (10, 108, int(barra_largura * progresso), 8), 0, 3)
                        tempo_restante = (cooldown - tempo_desde_uso) / 1000
                        desenhar_texto(self.tela, f"{tempo_restante:.1f}s", 10, (150, 150, 150), 85, 122)
                    elif not self.habilidade_ativa:
                        # Habilidade pronta
                        desenhar_texto(self.tela, "ESPACO: Pronto!", 10, (100, 255, 100), 85, 112)

        # Mostrar granadas disponíveis (para qualquer classe)
        granadas_disponiveis = getattr(self.jogador, 'granadas', 0)
        if granadas_disponiveis > 0:
            granada_selecionada = getattr(self.jogador, 'granada_selecionada', False)
            # Posição no canto inferior esquerdo
            if granada_selecionada:
                cor_fundo = (80, 100, 80)
                cor_borda = (100, 255, 100)
                texto = f"GRANADA x{granadas_disponiveis} (E: Arma)"
            else:
                cor_fundo = (50, 80, 50)
                cor_borda = (100, 200, 100)
                texto = f"Q: Granada x{granadas_disponiveis}"

            pygame.draw.rect(self.tela, cor_fundo, (10, ALTURA_JOGO - 50, 150, 40), 0, 8)
            pygame.draw.rect(self.tela, cor_borda, (10, ALTURA_JOGO - 50, 150, 40), 2, 8)
            desenhar_texto(self.tela, texto, 14, (100, 255, 100), 85, ALTURA_JOGO - 30)

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

        # Mostrar classe e habilidade (ambos os times)
        if self.classe_jogador:
            from src.game.selecao_classes import obter_dados_classe
            dados_classe = obter_dados_classe(self.classe_jogador, self.time_jogador)

            if dados_classe:
                # Nome da classe
                texto_classe = self.fonte_pequena.render(f"Classe: {dados_classe['nome']}", True, dados_classe['cor'])
                self.tela.blit(texto_classe, (10, ALTURA_JOGO + 55))

                # Barra de cooldown da habilidade
                cooldown = dados_classe.get("habilidade_cooldown", 0)
                tempo_atual = pygame.time.get_ticks()
                tempo_desde_uso = tempo_atual - self.habilidade_cooldown

                if cooldown > 0:
                    barra_x = 10
                    barra_y = ALTURA_JOGO + 75
                    barra_largura = 120
                    barra_altura = 8

                    # Fundo da barra
                    pygame.draw.rect(self.tela, (40, 40, 40), (barra_x, barra_y, barra_largura, barra_altura), 0, 3)

                    if self.habilidade_ativa:
                        # Barra de duração (quando a habilidade está ativa)
                        duracao = dados_classe.get("habilidade_duracao", 0)
                        if duracao > 0:
                            tempo_ativo = tempo_atual - self.habilidade_tempo_inicio
                            progresso = max(0, 1 - (tempo_ativo / duracao))
                            pygame.draw.rect(self.tela, (100, 255, 100), (barra_x, barra_y, int(barra_largura * progresso), barra_altura), 0, 3)
                            texto_hab = self.fonte_pequena.render("ATIVO!", True, (100, 255, 100))
                        else:
                            texto_hab = self.fonte_pequena.render("ATIVO!", True, (100, 255, 100))
                    elif tempo_desde_uso < cooldown:
                        # Barra de cooldown
                        progresso = tempo_desde_uso / cooldown
                        pygame.draw.rect(self.tela, (100, 100, 100), (barra_x, barra_y, int(barra_largura * progresso), barra_altura), 0, 3)
                        tempo_restante = (cooldown - tempo_desde_uso) / 1000
                        texto_hab = self.fonte_pequena.render(f"ESPACO ({tempo_restante:.1f}s)", True, (150, 150, 150))
                    else:
                        # Pronto para usar
                        pygame.draw.rect(self.tela, dados_classe['cor'], (barra_x, barra_y, barra_largura, barra_altura), 0, 3)
                        texto_hab = self.fonte_pequena.render("ESPACO (Pronto!)", True, dados_classe['cor'])

                    self.tela.blit(texto_hab, (barra_x, barra_y + 12))

        # Mostrar placar de rounds no centro superior
        placar_text = f"T  {self.rounds_time_t}  :  {self.rounds_time_q}  Q"
        pygame.draw.rect(self.tela, (30, 30, 40), (LARGURA // 2 - 80, 55, 160, 35), 0, 8)
        pygame.draw.rect(self.tela, BRANCO, (LARGURA // 2 - 80, 55, 160, 35), 2, 8)
        desenhar_texto(self.tela, placar_text, 24, BRANCO, LARGURA // 2, 73)
        desenhar_texto(self.tela, f"Round {self.round_atual}", 14, (150, 150, 150), LARGURA // 2, 95)

        # === HUD DO SISTEMA DE BOMBA ===
        tempo_atual = pygame.time.get_ticks()

        # Indicador de bomber (se o jogador é o bomber)
        if self.bomber_é_jogador and not self.bomba_plantada:
            pygame.draw.rect(self.tela, (80, 40, 0), (LARGURA // 2 - 100, 110, 200, 30), 0, 8)
            pygame.draw.rect(self.tela, LARANJA, (LARGURA // 2 - 100, 110, 200, 30), 2, 8)
            desenhar_texto(self.tela, "VOCÊ É O BOMBER", 18, LARANJA, LARGURA // 2, 125)

        # Barra de progresso - Plantando bomba
        if self.plantando_bomba and self.bomber_é_jogador:
            progresso = (tempo_atual - self.tempo_inicio_plantar) / self.tempo_para_plantar
            progresso = min(1.0, max(0.0, progresso))
            barra_largura = 250
            barra_altura = 25
            barra_x = LARGURA // 2 - barra_largura // 2
            barra_y = ALTURA_JOGO // 2 + 50

            # Fundo da barra
            pygame.draw.rect(self.tela, (30, 30, 30), (barra_x, barra_y, barra_largura, barra_altura), 0, 5)
            # Progresso
            pygame.draw.rect(self.tela, LARANJA, (barra_x, barra_y, int(barra_largura * progresso), barra_altura), 0, 5)
            # Borda
            pygame.draw.rect(self.tela, BRANCO, (barra_x, barra_y, barra_largura, barra_altura), 2, 5)
            # Texto
            desenhar_texto(self.tela, "PLANTANDO BOMBA...", 20, BRANCO, LARGURA // 2, barra_y - 15)
            desenhar_texto(self.tela, f"{progresso * 100:.0f}%", 16, BRANCO, LARGURA // 2, barra_y + barra_altura // 2)

        # Barra de progresso - Defusando bomba
        if self.defusando_bomba and self.time_jogador == 'Q':
            progresso = (tempo_atual - self.tempo_inicio_defusar) / self.tempo_para_defusar
            progresso = min(1.0, max(0.0, progresso))
            barra_largura = 250
            barra_altura = 25
            barra_x = LARGURA // 2 - barra_largura // 2
            barra_y = ALTURA_JOGO // 2 + 50

            # Fundo da barra
            pygame.draw.rect(self.tela, (30, 30, 30), (barra_x, barra_y, barra_largura, barra_altura), 0, 5)
            # Progresso (azul para defuse)
            pygame.draw.rect(self.tela, (50, 100, 200), (barra_x, barra_y, int(barra_largura * progresso), barra_altura), 0, 5)
            # Borda
            pygame.draw.rect(self.tela, BRANCO, (barra_x, barra_y, barra_largura, barra_altura), 2, 5)
            # Texto
            desenhar_texto(self.tela, "DEFUSANDO BOMBA...", 20, BRANCO, LARGURA // 2, barra_y - 15)
            desenhar_texto(self.tela, f"{progresso * 100:.0f}%", 16, BRANCO, LARGURA // 2, barra_y + barra_altura // 2)

        # Timer da bomba (quando plantada)
        if self.bomba_plantada and not self.bomba_explodiu and not self.bomba_defusada:
            tempo_restante = max(0, self.bomba_tempo_explosao - (tempo_atual - self.bomba_tempo_plantio))
            segundos = tempo_restante // 1000

            # Piscar quando menos de 10 segundos
            if segundos < 10 and tempo_atual % 500 < 250:
                cor_timer = VERMELHO
            else:
                cor_timer = LARANJA if segundos < 15 else BRANCO

            # Caixa do timer
            pygame.draw.rect(self.tela, (60, 20, 20), (LARGURA // 2 - 60, 140, 120, 35), 0, 8)
            pygame.draw.rect(self.tela, VERMELHO, (LARGURA // 2 - 60, 140, 120, 35), 2, 8)
            desenhar_texto(self.tela, f"BOMBA: {segundos}s", 22, cor_timer, LARGURA // 2, 158)

        # Indicador de bombsite (mostrar se está no local correto para plantar)
        if self.bomber_é_jogador and not self.bomba_plantada:
            no_bombsite = self._verificar_no_bombsite(self.jogador.x, self.jogador.y)
            if no_bombsite:
                # Mostrar instrução para plantar
                pygame.draw.rect(self.tela, (0, 60, 0), (LARGURA // 2 - 120, ALTURA_JOGO - 60, 240, 30), 0, 8)
                pygame.draw.rect(self.tela, VERDE, (LARGURA // 2 - 120, ALTURA_JOGO - 60, 240, 30), 2, 8)
                desenhar_texto(self.tela, "Segure F para plantar", 18, VERDE, LARGURA // 2, ALTURA_JOGO - 45)

        # Indicador para defusar (time Q perto da bomba)
        if self.bomba_plantada and not self.bomba_explodiu and not self.bomba_defusada and self.time_jogador == 'Q':
            if self.bomba_posicao:
                import math
                dist_bomba = math.sqrt((self.jogador.x - self.bomba_posicao[0])**2 +
                                       (self.jogador.y - self.bomba_posicao[1])**2)
                if dist_bomba < 50 and not self.defusando_bomba:
                    pygame.draw.rect(self.tela, (0, 40, 80), (LARGURA // 2 - 120, ALTURA_JOGO - 60, 240, 30), 0, 8)
                    pygame.draw.rect(self.tela, (50, 150, 255), (LARGURA // 2 - 120, ALTURA_JOGO - 60, 240, 30), 2, 8)
                    desenhar_texto(self.tela, "Segure F para defusar", 18, (50, 150, 255), LARGURA // 2, ALTURA_JOGO - 45)

        # === INDICADOR DE MODO ESPECTADOR ===
        if hasattr(self, 'espectador_ativo') and self.espectador_ativo and self.jogador.vidas <= 0:
            tempo_atual = pygame.time.get_ticks()
            tempo_desde_morte = tempo_atual - self.espectador_tempo_morte

            if tempo_desde_morte < self.espectador_delay:
                # Ainda no delay - mostrar "VOCÊ MORREU"
                pygame.draw.rect(self.tela, (80, 20, 20), (LARGURA // 2 - 100, ALTURA_JOGO // 2 - 30, 200, 60), 0, 10)
                pygame.draw.rect(self.tela, VERMELHO, (LARGURA // 2 - 100, ALTURA_JOGO // 2 - 30, 200, 60), 3, 10)
                desenhar_texto(self.tela, "VOCÊ MORREU", 24, VERMELHO, LARGURA // 2, ALTURA_JOGO // 2 - 5)
                segundos_restantes = (self.espectador_delay - tempo_desde_morte) / 1000
                desenhar_texto(self.tela, f"Espectador em {segundos_restantes:.1f}s", 14, BRANCO, LARGURA // 2, ALTURA_JOGO // 2 + 18)
            else:
                # Modo espectador ativo - mostrar quem está observando
                bot_obs = self._obter_aliado_espectador()
                if bot_obs:
                    nome_bot = getattr(bot_obs, 'nome', 'Bot')
                    time_bot = getattr(bot_obs, 'time', '?')
                    # Cor baseada no time
                    if time_bot == 'T':
                        cor_time = (255, 150, 50)  # Laranja para T
                        cor_borda = (255, 100, 0)
                    else:
                        cor_time = (50, 200, 255)  # Azul para Q
                        cor_borda = (0, 150, 255)

                    pygame.draw.rect(self.tela, (20, 40, 60), (LARGURA // 2 - 120, 10, 240, 55), 0, 10)
                    pygame.draw.rect(self.tela, cor_borda, (LARGURA // 2 - 120, 10, 240, 55), 2, 10)
                    desenhar_texto(self.tela, "ESPECTADOR", 14, (150, 150, 150), LARGURA // 2, 20)
                    desenhar_texto(self.tela, f"{nome_bot} (Time {time_bot})", 18, cor_time, LARGURA // 2, 40)
                    desenhar_texto(self.tela, "Clique para alternar", 12, (100, 100, 100), LARGURA // 2, 58)
                else:
                    # Sem bots vivos
                    pygame.draw.rect(self.tela, (40, 40, 40), (LARGURA // 2 - 100, ALTURA_JOGO // 2 - 20, 200, 40), 0, 10)
                    desenhar_texto(self.tela, "Sem jogadores vivos", 18, (150, 150, 150), LARGURA // 2, ALTURA_JOGO // 2)

    def _mostrar_menu_compra(self):
        """Mostra o menu de compra de armas e itens estilo Counter-Strike."""
        from src.utils.visual import desenhar_texto
        from src.utils.display_manager import convert_mouse_position

        # Overlay semi-transparente
        overlay = pygame.Surface((LARGURA, ALTURA_JOGO))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.tela.blit(overlay, (0, 0))

        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        tempo_restante = max(0, (self.tempo_compra - (pygame.time.get_ticks() - self.tempo_inicio_round)) // 1000)

        # Título do menu
        desenhar_texto(self.tela, "MENU DE COMPRA", 50, AMARELO, LARGURA // 2, 40)
        desenhar_texto(self.tela, f"Tempo restante: {tempo_restante}s", 20, BRANCO, LARGURA // 2, 75)
        desenhar_texto(self.tela, f"Dinheiro: ${self.moedas}", 26, VERDE, LARGURA // 2, 100)

        # === ABAS ===
        aba_largura = 150
        aba_altura = 40
        aba_y = 130
        aba_armas_x = LARGURA // 2 - aba_largura - 10
        aba_itens_x = LARGURA // 2 + 10

        # Aba Armas
        aba_armas_rect = pygame.Rect(aba_armas_x, aba_y, aba_largura, aba_altura)
        cor_aba_armas = (60, 80, 100) if self.aba_loja_atual == 0 else (40, 50, 60)
        borda_aba_armas = (100, 150, 255) if self.aba_loja_atual == 0 else (80, 100, 120)
        pygame.draw.rect(self.tela, cor_aba_armas, aba_armas_rect, 0, 8)
        pygame.draw.rect(self.tela, borda_aba_armas, aba_armas_rect, 2, 8)
        desenhar_texto(self.tela, "ARMAS", 22, BRANCO if self.aba_loja_atual == 0 else (150, 150, 150),
                      aba_armas_rect.centerx, aba_armas_rect.centery)

        # Aba Itens
        aba_itens_rect = pygame.Rect(aba_itens_x, aba_y, aba_largura, aba_altura)
        cor_aba_itens = (60, 100, 60) if self.aba_loja_atual == 1 else (40, 60, 40)
        borda_aba_itens = (100, 255, 100) if self.aba_loja_atual == 1 else (80, 120, 80)
        pygame.draw.rect(self.tela, cor_aba_itens, aba_itens_rect, 0, 8)
        pygame.draw.rect(self.tela, borda_aba_itens, aba_itens_rect, 2, 8)
        desenhar_texto(self.tela, "ITENS", 22, BRANCO if self.aba_loja_atual == 1 else (150, 150, 150),
                      aba_itens_rect.centerx, aba_itens_rect.centery)

        # Dimensões dos botões
        btn_largura = 280
        btn_altura = 100
        espacamento = 20
        inicio_y = 190
        num_colunas = 2
        coluna_esquerda_x = LARGURA // 4
        coluna_direita_x = 3 * LARGURA // 4

        # === ABA DE ARMAS ===
        if self.aba_loja_atual == 0:
            armas_lista = list(self.armas_disponiveis.items())

            for i, (arma_id, arma_info) in enumerate(armas_lista):
                col = i % num_colunas
                row = i // num_colunas

                if col == 0:
                    btn_x = coluna_esquerda_x - btn_largura // 2
                else:
                    btn_x = coluna_direita_x - btn_largura // 2

                btn_y = inicio_y + row * (btn_altura + espacamento)
                btn_rect = pygame.Rect(btn_x, btn_y, btn_largura, btn_altura)

                hover = btn_rect.collidepoint(mouse_pos)

                # Classe Metralhadora: metralhadora é grátis
                preco = arma_info['preco']
                is_gratis = (arma_id == 'metralhadora' and self.classe_jogador == 'metralhadora')
                if is_gratis:
                    preco = 0

                pode_comprar = self.moedas >= preco

                if self.arma_equipada == arma_id:
                    cor_btn = (0, 100, 50)
                    cor_borda = VERDE
                elif hover and pode_comprar:
                    cor_btn = (60, 80, 60)
                    cor_borda = VERDE
                elif pode_comprar:
                    cor_btn = (40, 50, 40)
                    cor_borda = (100, 150, 100)
                else:
                    cor_btn = (50, 30, 30)
                    cor_borda = (150, 80, 80)

                pygame.draw.rect(self.tela, cor_btn, btn_rect, 0, 10)
                pygame.draw.rect(self.tela, cor_borda, btn_rect, 3, 10)

                cor_nome = BRANCO if pode_comprar else (150, 150, 150)
                desenhar_texto(self.tela, arma_info['nome'], 26, cor_nome, btn_rect.centerx, btn_y + 25)

                # Mostrar preço ou GRÁTIS
                if is_gratis:
                    desenhar_texto(self.tela, "GRATIS!", 22, (100, 255, 100), btn_rect.centerx, btn_y + 50)
                else:
                    cor_preco = VERDE if pode_comprar else VERMELHO
                    desenhar_texto(self.tela, f"${preco}", 22, cor_preco, btn_rect.centerx, btn_y + 50)

                desenhar_texto(self.tela, arma_info['descricao'], 16, (180, 180, 180), btn_rect.centerx, btn_y + 75)

                if self.arma_equipada == arma_id:
                    desenhar_texto(self.tela, "[EQUIPADA]", 14, VERDE, btn_rect.centerx, btn_y + 90)

        # === ABA DE ITENS ===
        else:
            itens_lista = list(self.itens_disponiveis.items())

            for i, (item_id, item_info) in enumerate(itens_lista):
                col = i % num_colunas
                row = i // num_colunas

                if col == 0:
                    btn_x = coluna_esquerda_x - btn_largura // 2
                else:
                    btn_x = coluna_direita_x - btn_largura // 2

                btn_y = inicio_y + row * (btn_altura + espacamento)
                btn_rect = pygame.Rect(btn_x, btn_y, btn_largura, btn_altura)

                hover = btn_rect.collidepoint(mouse_pos)
                pode_comprar = self.moedas >= item_info['preco']

                # Verificar quantidade atual
                quantidade_atual = 0
                if item_id == 'granada':
                    quantidade_atual = getattr(self.jogador, 'granadas', 0)
                max_quantidade = item_info.get('max', 3)
                no_limite = quantidade_atual >= max_quantidade

                if no_limite:
                    cor_btn = (80, 80, 40)
                    cor_borda = AMARELO
                elif hover and pode_comprar:
                    cor_btn = (60, 80, 60)
                    cor_borda = VERDE
                elif pode_comprar:
                    cor_btn = (40, 50, 40)
                    cor_borda = (100, 150, 100)
                else:
                    cor_btn = (50, 30, 30)
                    cor_borda = (150, 80, 80)

                pygame.draw.rect(self.tela, cor_btn, btn_rect, 0, 10)
                pygame.draw.rect(self.tela, cor_borda, btn_rect, 3, 10)

                cor_nome = BRANCO if pode_comprar and not no_limite else (150, 150, 150)
                desenhar_texto(self.tela, item_info['nome'], 26, cor_nome, btn_rect.centerx, btn_y + 20)

                cor_preco = VERDE if pode_comprar else VERMELHO
                desenhar_texto(self.tela, f"${item_info['preco']}", 22, cor_preco, btn_rect.centerx, btn_y + 45)

                desenhar_texto(self.tela, item_info['descricao'], 16, (180, 180, 180), btn_rect.centerx, btn_y + 68)

                # Mostrar quantidade atual
                desenhar_texto(self.tela, f"[{quantidade_atual}/{max_quantidade}]", 16,
                              AMARELO if no_limite else (150, 200, 150), btn_rect.centerx, btn_y + 88)

        # Instruções
        desenhar_texto(self.tela, "Clique para comprar | TAB para trocar aba | B para fechar", 18,
                      (150, 150, 150), LARGURA // 2, ALTURA_JOGO - 40)

        # Processar cliques no menu
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_b or evento.key == pygame.K_ESCAPE:
                    self.menu_compra_aberto = False
                    pygame.mouse.set_visible(False)
                    return None
                # TAB para trocar de aba
                if evento.key == pygame.K_TAB:
                    self.aba_loja_atual = 1 - self.aba_loja_atual
                # Atalhos numéricos
                if self.aba_loja_atual == 0:
                    if evento.key == pygame.K_1:
                        self._comprar_arma('desert_eagle')
                    elif evento.key == pygame.K_2:
                        self._comprar_arma('spas12')
                    elif evento.key == pygame.K_3:
                        self._comprar_arma('metralhadora')
                    elif evento.key == pygame.K_4:
                        self._comprar_arma('sniper')
                else:
                    if evento.key == pygame.K_1:
                        self._comprar_item('granada')

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mouse_click_pos = convert_mouse_position(evento.pos)

                # Verificar clique nas abas
                if aba_armas_rect.collidepoint(mouse_click_pos):
                    self.aba_loja_atual = 0
                elif aba_itens_rect.collidepoint(mouse_click_pos):
                    self.aba_loja_atual = 1

                # Verificar clique nos itens/armas
                if self.aba_loja_atual == 0:
                    armas_lista = list(self.armas_disponiveis.items())
                    for i, (arma_id, arma_info) in enumerate(armas_lista):
                        col = i % num_colunas
                        row = i // num_colunas
                        if col == 0:
                            btn_x = coluna_esquerda_x - btn_largura // 2
                        else:
                            btn_x = coluna_direita_x - btn_largura // 2
                        btn_y = inicio_y + row * (btn_altura + espacamento)
                        btn_rect = pygame.Rect(btn_x, btn_y, btn_largura, btn_altura)
                        if btn_rect.collidepoint(mouse_click_pos):
                            self._comprar_arma(arma_id)
                            break
                else:
                    itens_lista = list(self.itens_disponiveis.items())
                    for i, (item_id, item_info) in enumerate(itens_lista):
                        col = i % num_colunas
                        row = i // num_colunas
                        if col == 0:
                            btn_x = coluna_esquerda_x - btn_largura // 2
                        else:
                            btn_x = coluna_direita_x - btn_largura // 2
                        btn_y = inicio_y + row * (btn_altura + espacamento)
                        btn_rect = pygame.Rect(btn_x, btn_y, btn_largura, btn_altura)
                        if btn_rect.collidepoint(mouse_click_pos):
                            self._comprar_item(item_id)
                            break

        return None

    def _comprar_arma(self, arma_id):
        """Compra uma arma se tiver dinheiro suficiente."""
        if arma_id not in self.armas_disponiveis:
            return False

        arma_info = self.armas_disponiveis[arma_id]

        # Verificar se já está equipada
        if self.arma_equipada == arma_id:
            print(f"[COMPRA] {arma_info['nome']} ja esta equipada")
            return False

        # Classe Metralhadora: metralhadora é grátis
        preco = arma_info['preco']
        if arma_id == 'metralhadora' and self.classe_jogador == 'metralhadora':
            preco = 0

        # Verificar se tem dinheiro
        if self.moedas < preco:
            print(f"[COMPRA] Dinheiro insuficiente para {arma_info['nome']}")
            return False

        # Comprar a arma
        self.moedas -= preco
        self.arma_equipada = arma_id
        if preco == 0:
            print(f"[COMPRA] {arma_info['nome']} GRATIS (classe metralhadora)!")
        else:
            print(f"[COMPRA] Comprou {arma_info['nome']} por ${preco}! Saldo: ${self.moedas}")

        return True

    def _comprar_item(self, item_id):
        """Compra um item se tiver dinheiro suficiente."""
        if item_id not in self.itens_disponiveis:
            return False

        item_info = self.itens_disponiveis[item_id]

        # Verificar se tem dinheiro
        if self.moedas < item_info['preco']:
            print(f"[COMPRA] Dinheiro insuficiente para {item_info['nome']}")
            return False

        # Verificar limite de quantidade
        if item_id == 'granada':
            quantidade_atual = getattr(self.jogador, 'granadas', 0)
            max_quantidade = item_info.get('max', 3)

            if quantidade_atual >= max_quantidade:
                print(f"[COMPRA] Limite de {item_info['nome']} atingido ({max_quantidade})")
                return False

            # Comprar granada
            self.moedas -= item_info['preco']
            if not hasattr(self.jogador, 'granadas'):
                self.jogador.granadas = 0
            self.jogador.granadas += item_info.get('quantidade', 1)
            print(f"[COMPRA] Comprou {item_info['nome']} por ${item_info['preco']}! Total: {self.jogador.granadas}")

        return True

    def _atualizar_tempo_compra(self):
        """Atualiza o estado do tempo de compra."""
        if not self.mapa_carregado:
            return

        tempo_atual = pygame.time.get_ticks()
        tempo_decorrido = tempo_atual - self.tempo_inicio_round

        if tempo_decorrido >= self.tempo_compra:
            if self.em_tempo_compra:
                self.em_tempo_compra = False
                self.menu_compra_aberto = False
                pygame.mouse.set_visible(False)
                print("[MULTIPLAYER] Tempo de compra encerrado!")

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

    # A cor do jogador é determinada pelo time escolhido na tela de seleção
    # Não aplicar customização de cor aqui

    resultado = fase.executar()
    return resultado
