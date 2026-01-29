#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de carregamento e renderização de mapas TMX (Tiled).
Implementa colisões baseadas em tiles e renderização com tileset.
"""

import pygame
import xml.etree.ElementTree as ET
import os


class TileMap:
    """
    Classe para carregar e gerenciar mapas TMX do Tiled.
    Suporta tileset com imagem para renderização correta.
    """

    # Tiles que são considerados "chão" (onde pode andar)
    TILES_CHAO = [182, 114, 322,96,97,98,99,100,419,416,216, 250, 284, 318, 216,1621,1622,1623,1624,1625]  # 182, 114 e 322 são pisos caminháveis

    def __init__(self, caminho_tmx):
        """
        Carrega um mapa TMX.

        Args:
            caminho_tmx: Caminho para o arquivo .tmx
        """
        self.caminho = caminho_tmx
        self.diretorio = os.path.dirname(caminho_tmx)
        self.largura = 0  # Em tiles
        self.altura = 0   # Em tiles
        self.tile_largura = 16
        self.tile_altura = 16
        self.dados = []   # Lista 2D de IDs de tiles
        self.rects_colisao = []  # Lista de pygame.Rect para colisões

        # Tilesets (suporte a múltiplos)
        self.tilesets = []  # Lista de {'firstgid': int, 'imagem': Surface, 'colunas': int, 'linhas': int}
        self.tiles_cache = {}  # Cache de superfícies de tiles individuais

        # Objetos do mapa (spawn points, etc.)
        self.objetos = {}  # {nome: {'x': x, 'y': y, 'width': w, 'height': h}}

        self._carregar_mapa()
        self._gerar_colisoes()

    def _carregar_mapa(self):
        """Carrega os dados do mapa TMX e o tileset."""
        try:
            tree = ET.parse(self.caminho)
            root = tree.getroot()

            # Obter dimensões do mapa
            self.largura = int(root.get('width', 0))
            self.altura = int(root.get('height', 0))
            self.tile_largura = int(root.get('tilewidth', 16))
            self.tile_altura = int(root.get('tileheight', 16))

            print(f"[TILEMAP] Mapa carregado: {self.largura}x{self.altura} tiles")
            print(f"[TILEMAP] Tamanho tile: {self.tile_largura}x{self.tile_altura}")

            # Carregar todos os tilesets
            for tileset in root.findall('tileset'):
                firstgid = int(tileset.get('firstgid', 1))
                source = tileset.get('source')

                if source:
                    # Tileset externo (.tsx)
                    tsx_path = os.path.join(self.diretorio, source)
                    self._carregar_tileset_externo(tsx_path, firstgid)
                else:
                    # Tileset embutido
                    self._carregar_tileset_embutido(tileset, firstgid)

            # Encontrar a camada de dados
            for layer in root.findall('.//layer'):
                data_elem = layer.find('data')
                if data_elem is not None:
                    encoding = data_elem.get('encoding', '')

                    if encoding == 'csv':
                        # Parse CSV
                        csv_data = data_elem.text.strip()
                        linhas = csv_data.split('\n')

                        self.dados = []
                        for linha in linhas:
                            linha = linha.strip().rstrip(',')
                            if linha:
                                tiles = [int(t) for t in linha.split(',') if t.strip()]
                                self.dados.append(tiles)

                        print(f"[TILEMAP] Dados carregados: {len(self.dados)} linhas")
                    break

            # Carregar objetos (spawn points, etc.)
            for objectgroup in root.findall('.//objectgroup'):
                for obj in objectgroup.findall('object'):
                    nome = obj.get('name', '')
                    if nome:
                        self.objetos[nome] = {
                            'x': float(obj.get('x', 0)),
                            'y': float(obj.get('y', 0)),
                            'width': float(obj.get('width', 0)),
                            'height': float(obj.get('height', 0))
                        }
                        print(f"[TILEMAP] Objeto carregado: {nome} em ({self.objetos[nome]['x']}, {self.objetos[nome]['y']})")

        except Exception as e:
            print(f"[TILEMAP] Erro ao carregar mapa: {e}")
            import traceback
            traceback.print_exc()
            # Criar mapa vazio em caso de erro
            self.dados = [[self.TILE_CHAO] * self.largura for _ in range(self.altura)]

    def _carregar_tileset_externo(self, tsx_path, firstgid):
        """Carrega um tileset de um arquivo .tsx externo."""
        try:
            print(f"[TILEMAP] Carregando tileset: {tsx_path} (firstgid={firstgid})")

            # Verificar se o arquivo existe
            if not os.path.exists(tsx_path):
                print(f"[TILEMAP] AVISO: Tileset não encontrado: {tsx_path}")
                return

            tree = ET.parse(tsx_path)
            root = tree.getroot()

            tsx_dir = os.path.dirname(tsx_path)

            # Obter informações do tileset
            colunas = int(root.get('columns', 1))
            tilecount = int(root.get('tilecount', 1))
            linhas = tilecount // colunas

            # Carregar imagem
            image_elem = root.find('image')
            if image_elem is not None:
                image_source = image_elem.get('source')
                image_path = os.path.join(tsx_dir, image_source)

                if not os.path.exists(image_path):
                    print(f"[TILEMAP] AVISO: Imagem não encontrada: {image_path}")
                    return

                print(f"[TILEMAP] Carregando imagem: {image_path}")
                tileset_imagem = pygame.image.load(image_path).convert_alpha()
                print(f"[TILEMAP] Tileset carregado: {colunas} colunas, {linhas} linhas")

                # Adicionar à lista de tilesets
                tileset_info = {
                    'firstgid': firstgid,
                    'imagem': tileset_imagem,
                    'colunas': colunas,
                    'linhas': linhas
                }
                self.tilesets.append(tileset_info)

                # Pré-cachear todos os tiles deste tileset
                self._cachear_tiles_tileset(tileset_info)

        except Exception as e:
            print(f"[TILEMAP] Erro ao carregar tileset externo: {e}")
            import traceback
            traceback.print_exc()

    def _carregar_tileset_embutido(self, tileset_elem, firstgid):
        """Carrega um tileset embutido no TMX."""
        try:
            colunas = int(tileset_elem.get('columns', 1))
            tilecount = int(tileset_elem.get('tilecount', 1))
            linhas = tilecount // colunas

            image_elem = tileset_elem.find('image')
            if image_elem is not None:
                image_source = image_elem.get('source')
                image_path = os.path.join(self.diretorio, image_source)

                if not os.path.exists(image_path):
                    print(f"[TILEMAP] AVISO: Imagem não encontrada: {image_path}")
                    return

                tileset_imagem = pygame.image.load(image_path).convert_alpha()
                print(f"[TILEMAP] Tileset embutido carregado: {colunas}x{linhas}")

                tileset_info = {
                    'firstgid': firstgid,
                    'imagem': tileset_imagem,
                    'colunas': colunas,
                    'linhas': linhas
                }
                self.tilesets.append(tileset_info)

                self._cachear_tiles_tileset(tileset_info)

        except Exception as e:
            print(f"[TILEMAP] Erro ao carregar tileset embutido: {e}")

    def _cachear_tiles_tileset(self, tileset_info):
        """Pré-cacheia todos os tiles de um tileset específico."""
        imagem = tileset_info['imagem']
        colunas = tileset_info['colunas']
        linhas = tileset_info['linhas']
        firstgid = tileset_info['firstgid']

        count = 0
        for y in range(linhas):
            for x in range(colunas):
                tile_id = y * colunas + x + firstgid

                # Recortar o tile da imagem
                rect = pygame.Rect(
                    x * self.tile_largura,
                    y * self.tile_altura,
                    self.tile_largura,
                    self.tile_altura
                )

                try:
                    tile_surface = imagem.subsurface(rect).copy()
                    self.tiles_cache[tile_id] = tile_surface
                    count += 1
                except ValueError:
                    # Tile fora dos limites da imagem
                    pass

        print(f"[TILEMAP] {count} tiles cacheados do tileset (firstgid={firstgid})")

    def _is_tile_walkable(self, tile_id_base):
        """Verifica se um tile é caminhável (chão)."""
        return tile_id_base in self.TILES_CHAO

    def _gerar_colisoes(self):
        """Gera retângulos de colisão para tiles sólidos."""
        self.rects_colisao = []

        for y, linha in enumerate(self.dados):
            for x, tile_id in enumerate(linha):
                # Extrair o ID base do tile (remover flags de flip)
                tile_id_base = tile_id & 0x1FFFFFFF

                # Se não for tile caminhável nem vazio, é colisão
                if not self._is_tile_walkable(tile_id_base) and tile_id_base != 0:
                    rect = pygame.Rect(
                        x * self.tile_largura,
                        y * self.tile_altura,
                        self.tile_largura,
                        self.tile_altura
                    )
                    self.rects_colisao.append(rect)

        print(f"[TILEMAP] {len(self.rects_colisao)} tiles de colisão gerados")

    def get_tile(self, x, y):
        """
        Retorna o ID do tile na posição (x, y) em coordenadas de tile.
        """
        if 0 <= y < len(self.dados) and 0 <= x < len(self.dados[y]):
            return self.dados[y][x]
        return 0

    def get_tile_at_pixel(self, px, py):
        """
        Retorna o ID do tile na posição em pixels.
        """
        tile_x = int(px // self.tile_largura)
        tile_y = int(py // self.tile_altura)
        return self.get_tile(tile_x, tile_y)

    def is_solid(self, px, py):
        """
        Verifica se a posição em pixels é sólida (colisão).
        """
        tile_id = self.get_tile_at_pixel(px, py)
        tile_id_base = tile_id & 0x1FFFFFFF
        return not self._is_tile_walkable(tile_id_base) and tile_id_base != 0

    def get_objeto(self, nome):
        """
        Retorna um objeto do mapa pelo nome.
        """
        return self.objetos.get(nome)

    def get_spawn_point(self, nome):
        """
        Retorna a posição central de um objeto de spawn.
        """
        obj = self.get_objeto(nome)
        if obj:
            return (
                obj['x'] + obj['width'] / 2,
                obj['y'] + obj['height'] / 2
            )
        return None

    def colide_com_rect(self, rect):
        """
        Verifica se um retângulo colide com algum tile sólido.
        """
        for tile_rect in self.rects_colisao:
            if rect.colliderect(tile_rect):
                return True
        return False

    def get_colisoes_proximas(self, rect, margem=64):
        """
        Retorna apenas os retângulos de colisão próximos ao rect dado.
        """
        area_busca = rect.inflate(margem * 2, margem * 2)
        return [r for r in self.rects_colisao if r.colliderect(area_busca)]

    def resolver_colisao(self, rect, vel_x, vel_y):
        """
        Resolve colisão movendo o retângulo para fora dos tiles sólidos.
        """
        novo_x = rect.x
        novo_y = rect.y
        colidiu_x = False
        colidiu_y = False

        colisoes_proximas = self.get_colisoes_proximas(rect)

        # Verificar colisão horizontal
        rect_teste = pygame.Rect(rect.x + vel_x, rect.y, rect.width, rect.height)
        for tile_rect in colisoes_proximas:
            if rect_teste.colliderect(tile_rect):
                colidiu_x = True
                if vel_x > 0:
                    novo_x = tile_rect.left - rect.width
                elif vel_x < 0:
                    novo_x = tile_rect.right
                break

        if not colidiu_x:
            novo_x = rect.x + vel_x

        # Verificar colisão vertical
        rect_teste = pygame.Rect(novo_x, rect.y + vel_y, rect.width, rect.height)
        for tile_rect in colisoes_proximas:
            if rect_teste.colliderect(tile_rect):
                colidiu_y = True
                if vel_y > 0:
                    novo_y = tile_rect.top - rect.height
                elif vel_y < 0:
                    novo_y = tile_rect.bottom
                break

        if not colidiu_y:
            novo_y = rect.y + vel_y

        return novo_x, novo_y, colidiu_x, colidiu_y

    def _obter_tile_surface(self, tile_id):
        """
        Obtém a superfície do tile, considerando flags de flip.
        """
        if tile_id == 0:
            return None

        # Flags de flip do Tiled
        FLIPPED_HORIZONTALLY = 0x80000000
        FLIPPED_VERTICALLY = 0x40000000
        FLIPPED_DIAGONALLY = 0x20000000

        flip_h = bool(tile_id & FLIPPED_HORIZONTALLY)
        flip_v = bool(tile_id & FLIPPED_VERTICALLY)
        flip_d = bool(tile_id & FLIPPED_DIAGONALLY)

        # Remover flags para obter ID real
        tile_id_base = tile_id & 0x1FFFFFFF

        if tile_id_base not in self.tiles_cache:
            return None

        tile_surface = self.tiles_cache[tile_id_base]

        # Aplicar transformações se necessário
        if flip_h or flip_v or flip_d:
            tile_surface = tile_surface.copy()

            if flip_d:
                # Rotação diagonal (90 graus + flip)
                tile_surface = pygame.transform.rotate(tile_surface, 90)
                tile_surface = pygame.transform.flip(tile_surface, True, False)

            if flip_h:
                tile_surface = pygame.transform.flip(tile_surface, True, False)

            if flip_v:
                tile_surface = pygame.transform.flip(tile_surface, False, True)

        return tile_surface

    def desenhar_tiles(self, tela, camera_x=0, camera_y=0, cor_chao=None, cor_parede=None):
        """
        Desenha o mapa de tiles usando o tileset carregado.

        Args:
            tela: Superfície do pygame
            camera_x: Offset X da câmera
            camera_y: Offset Y da câmera
            cor_chao: (Ignorado se tileset carregado) Cor para tiles vazios
            cor_parede: (Ignorado se tileset carregado) Cor para tiles sólidos
        """
        # Calcular quais tiles estão visíveis
        tile_inicio_x = max(0, int(camera_x // self.tile_largura))
        tile_inicio_y = max(0, int(camera_y // self.tile_altura))
        tile_fim_x = min(self.largura, int((camera_x + tela.get_width()) // self.tile_largura) + 2)
        tile_fim_y = min(self.altura, int((camera_y + tela.get_height()) // self.tile_altura) + 2)

        # Se temos tileset, usar texturas
        if self.tilesets and self.tiles_cache:
            for y in range(tile_inicio_y, tile_fim_y):
                for x in range(tile_inicio_x, tile_fim_x):
                    tile_id = self.get_tile(x, y)

                    if tile_id == 0:
                        continue

                    tile_surface = self._obter_tile_surface(tile_id)

                    if tile_surface:
                        px = x * self.tile_largura - camera_x
                        py = y * self.tile_altura - camera_y
                        tela.blit(tile_surface, (px, py))
        else:
            # Fallback: desenhar com cores sólidas
            cor_chao = cor_chao or (40, 35, 50)
            cor_parede = cor_parede or (80, 60, 45)

            for y in range(tile_inicio_y, tile_fim_y):
                for x in range(tile_inicio_x, tile_fim_x):
                    tile_id = self.get_tile(x, y)
                    tile_id_base = tile_id & 0x1FFFFFFF

                    px = x * self.tile_largura - camera_x
                    py = y * self.tile_altura - camera_y

                    if self._is_tile_walkable(tile_id_base):
                        cor = cor_chao
                    else:
                        cor = cor_parede

                    pygame.draw.rect(tela, cor, (px, py, self.tile_largura, self.tile_altura))

    def desenhar_debug(self, tela, camera_x=0, camera_y=0):
        """
        Desenha os tiles de colisão para debug.
        """
        for rect in self.rects_colisao:
            rect_tela = pygame.Rect(
                rect.x - camera_x,
                rect.y - camera_y,
                rect.width,
                rect.height
            )
            if rect_tela.right > 0 and rect_tela.left < tela.get_width():
                if rect_tela.bottom > 0 and rect_tela.top < tela.get_height():
                    pygame.draw.rect(tela, (255, 0, 0), rect_tela, 1)

    @property
    def largura_pixels(self):
        """Retorna a largura do mapa em pixels."""
        return self.largura * self.tile_largura

    @property
    def altura_pixels(self):
        """Retorna a altura do mapa em pixels."""
        return self.altura * self.tile_altura


def carregar_mapa(caminho):
    """
    Função auxiliar para carregar um mapa TMX.
    """
    return TileMap(caminho)
