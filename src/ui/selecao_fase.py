import pygame
import sys
from ..config import *
from ..utils.visual import criar_botao, desenhar_texto, criar_estrelas, desenhar_estrelas
from ..utils.progress import ProgressManager
import random
import math
from src.utils.display_manager import convert_mouse_position,present_frame
class ScrollBar:
    """Classe para criar e gerenciar uma barra de rolagem."""
    
    def __init__(self, x, y, width, height, content_height, viewport_height):
        """
        Inicializa a barra de rolagem.
        
        Args:
            x, y: Posição do canto superior esquerdo da área da scrollbar
            width, height: Dimensões da área da scrollbar
            content_height: Altura total do conteúdo a ser rolado
            viewport_height: Altura visível da área de visualização
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.content_height = content_height
        self.viewport_height = viewport_height
        
        # Calcular altura da alça da scrollbar
        self.handle_ratio = min(1.0, viewport_height / content_height)
        self.handle_height = max(30, int(height * self.handle_ratio))
        
        # Posição de rolagem (0.0 a 1.0)
        self.scroll_pos = 0.0
        self.is_dragging = False
        self.hover = False
    
    def update(self, mouse_pos, mouse_pressed, mouse_wheel=0):
        """
        Atualiza o estado da scrollbar com base nas interações do mouse.
        
        Args:
            mouse_pos: Posição atual do mouse (x, y)
            mouse_pressed: Se o botão esquerdo do mouse está pressionado
            mouse_wheel: Valor da rolagem do mouse (positivo = para cima, negativo = para baixo)
            
        Returns:
            int: Deslocamento atual do conteúdo em pixels
        """
        # Verificar se o mouse está sobre a scrollbar
        self.hover = self.x <= mouse_pos[0] <= self.x + self.width and self.y <= mouse_pos[1] <= self.y + self.height
        
        # Calcular posição atual da alça
        handle_y = self.y + (self.height - self.handle_height) * self.scroll_pos
        
        # Verificar clique na alça para iniciar arrasto
        handle_hover = self.x <= mouse_pos[0] <= self.x + self.width and handle_y <= mouse_pos[1] <= handle_y + self.handle_height
        
        # Iniciar arrasto
        if handle_hover and mouse_pressed and not self.is_dragging:
            self.is_dragging = True
            self.drag_offset = mouse_pos[1] - handle_y
        
        # Terminar arrasto
        if not mouse_pressed:
            self.is_dragging = False
        
        # Atualizar posição durante arrasto
        if self.is_dragging:
            new_handle_y = mouse_pos[1] - self.drag_offset
            self.scroll_pos = max(0.0, min(1.0, (new_handle_y - self.y) / (self.height - self.handle_height)))
        
        # Processar rolagem do mouse
        if self.hover and mouse_wheel != 0:
            # Inverter direção: rolar para cima (-1) move o conteúdo para baixo
            scroll_amount = 0.08 * -mouse_wheel  # 8% de movimento por clique da roda
            self.scroll_pos = max(0.0, min(1.0, self.scroll_pos + scroll_amount))
        
        # Calcular o deslocamento em pixels para o conteúdo
        max_scroll = max(0, self.content_height - self.viewport_height)
        return int(max_scroll * self.scroll_pos)
    
    def draw(self, screen):
        """
        Desenha a scrollbar na tela.
        
        Args:
            screen: Superfície onde desenhar a scrollbar
        """
        # Desenhar fundo da scrollbar
        pygame.draw.rect(screen, (40, 40, 60), (self.x, self.y, self.width, self.height))
        
        # Calcular posição da alça
        handle_y = self.y + (self.height - self.handle_height) * self.scroll_pos
        
        # Desenhar a alça
        cor_alca = (100, 100, 180) if self.hover else (80, 80, 150)
        pygame.draw.rect(screen, cor_alca, (self.x, handle_y, self.width, self.handle_height), 0, 5)
        pygame.draw.rect(screen, (150, 150, 220), (self.x, handle_y, self.width, self.handle_height), 2, 5)

def tela_selecao_fase(tela, relogio, gradiente_selecao, fonte_titulo, fonte_normal):
    """
    Exibe a tela de seleção de fases com scrollbar para comportar mais níveis.
    
    Returns:
        Número da fase selecionada ou None se cancelar
    """
    pygame.mouse.set_visible(True)
    progress_manager = ProgressManager()
    fase_maxima = progress_manager.obter_fase_maxima()
    
    # Número total de fases que queremos exibir
    total_fases = 20  # Aumentado para testar rolagem
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(50)
    
    # Posições dos botões de fases - definir primeiro para calcular dimensões
    cols = 3
    rows = math.ceil(total_fases / cols)
    tamanho_botao = 90
    espacamento = 20
    
    # Calcular largura ideal para a área de botões
    largura_conteudo = cols * tamanho_botao + (cols + 1) * espacamento
    
    # Definir área de botões de fases - tamanho fixo e posição para garantir que caiba na tela
    area_botoes_x = (LARGURA - largura_conteudo - 30) // 2  # Centralizar, considerando espaço para scrollbar
    area_botoes_y = ALTURA // 4  # Posicionar mais acima (1/4 da altura)
    area_botoes_largura = largura_conteudo
    area_botoes_altura = 350  # Altura fixa menor para garantir que o botão voltar seja visível
    
    # Altura total do conteúdo (todos os botões organizados em grade)
    content_height = rows * (tamanho_botao + espacamento) + espacamento
    
    # Criar scrollbar se o conteúdo for maior que a área visível
    scrollbar = None
    if content_height > area_botoes_altura:
        scrollbar = ScrollBar(
            area_botoes_x + area_botoes_largura + 10,  # Posição X (adjacente à área de botões)
            area_botoes_y,  # Posição Y
            20,            # Largura
            area_botoes_altura,  # Altura
            content_height,  # Altura total do conteúdo
            area_botoes_altura   # Altura visível
        )
    
    # Variáveis para controle da rolagem
    scroll_offset = 0
    mouse_wheel = 0  # Direção da rolagem do mouse neste frame

    # Loop principal
    while True:
        clique_ocorreu = False
        mouse_wheel = 0  # Resetar a rolagem do mouse
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Botão esquerdo
                    clique_ocorreu = True
                elif evento.button == 4:  # Roda para cima
                    mouse_wheel = 1
                elif evento.button == 5:  # Roda para baixo
                    mouse_wheel = -1
            # Capturar eventos de rolagem do mouse também nos sistemas macOS
            if evento.type == pygame.MOUSEWHEEL:
                mouse_wheel = evento.y
                
            # Verificar se o mouse está sobre a área da grade para rolagem
            mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
            mouse_na_grade = (area_botoes_x <= mouse_pos[0] <= area_botoes_x + area_botoes_largura and
                             area_botoes_y <= mouse_pos[1] <= area_botoes_y + area_botoes_altura)
            
            # Permitir rolagem mesmo quando o mouse não está diretamente sobre a scrollbar
            if mouse_na_grade and mouse_wheel != 0 and scrollbar:
                scroll_amount = 0.08 * -mouse_wheel  # 8% de movimento por clique da roda
                scrollbar.scroll_pos = max(0.0, min(1.0, scrollbar.scroll_pos + scroll_amount))
        
        # Obter posição do mouse e estado dos botões
        mouse_pos = convert_mouse_position(pygame.mouse.get_pos())
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Botão esquerdo
        
        # Atualizar scrollbar se existir
        if scrollbar:
            scroll_offset = scrollbar.update(mouse_pos, mouse_pressed, mouse_wheel)
        
        # Atualizar estrelas
        for estrela in estrelas:
            estrela[0] -= estrela[4]
            if estrela[0] < 0:
                estrela[0] = LARGURA
                estrela[1] = random.randint(0, ALTURA)
        
        # Desenhar fundo
        tela.blit(gradiente_selecao, (0, 0))
        
        # Desenhar estrelas
        desenhar_estrelas(tela, estrelas)
        
        # Título
        desenhar_texto(tela, "SELECIONE A FASE", 60, BRANCO, LARGURA // 2, ALTURA // 8, fonte_titulo)
        
        # Criar uma superfície para recortar apenas a área visível dos botões (para scrolling)
        botoes_surf = pygame.Surface((area_botoes_largura, area_botoes_altura), pygame.SRCALPHA)
        botoes_surf.fill((0, 0, 0, 0))  # Transparente
        
        # Desenhar retângulo de fundo para a área de botões
        pygame.draw.rect(botoes_surf, (10, 10, 30, 150), (0, 0, area_botoes_largura, area_botoes_altura), 0, 10)
        pygame.draw.rect(botoes_surf, (50, 50, 100, 200), (0, 0, area_botoes_largura, area_botoes_altura), 2, 10)
        
        # Desenhar retângulo de clipagem para conter os botões dentro da área
        cliprect = pygame.Rect(0, 0, area_botoes_largura, area_botoes_altura)
        botoes_surf.set_clip(cliprect)
        
        # Desenhar botões de fases na superfície de botões
        fase_selecionada = None
        
        for fase in range(1, total_fases + 1):
            # Calcular posição na grade
            col = (fase - 1) % cols
            row = (fase - 1) // cols
            
            # Calcular posição X e Y (com deslocamento vertical pela rolagem)
            posicao_real_y = row * (tamanho_botao + espacamento) + espacamento - scroll_offset
            
            # Se o botão está fora da área visível, não desenhar
            if posicao_real_y + tamanho_botao < 0 or posicao_real_y > area_botoes_altura:
                continue
            
            x = espacamento + col * (tamanho_botao + espacamento)
            y = posicao_real_y
            
            # Verificar se a fase está desbloqueada
            desbloqueada = fase <= fase_maxima
            
            # Criar retângulo do botão
            rect = pygame.Rect(x, y, tamanho_botao, tamanho_botao)
            
            # Cores do botão
            if desbloqueada:
                cor_normal = (50, 50, 150)
                cor_hover = (70, 70, 200)
                cor_texto = BRANCO
            else:
                cor_normal = (50, 50, 50)
                cor_hover = (50, 50, 50)
                cor_texto = (100, 100, 100)
            
            # Verificar hover (considerando a posição real na tela)
            hover = (
                area_botoes_x + x <= mouse_pos[0] <= area_botoes_x + x + tamanho_botao and
                area_botoes_y + y <= mouse_pos[1] <= area_botoes_y + y + tamanho_botao and
                desbloqueada
            )
            
            # Desenhar botão
            pygame.draw.rect(botoes_surf, cor_hover if hover else cor_normal, rect, 0, 10)
            pygame.draw.rect(botoes_surf, BRANCO if desbloqueada else (80, 80, 80), rect, 2, 10)
            
            # Texto do botão
            desenhar_texto(botoes_surf, str(fase), 36, cor_texto, x + tamanho_botao // 2, y + tamanho_botao // 2, fonte_normal)
            
            # Verificar clique
            if clique_ocorreu and hover and desbloqueada:
                fase_selecionada = fase
        
        # Resetar clipping
        botoes_surf.set_clip(None)
        
        # Aplicar a superfície de botões à tela
        tela.blit(botoes_surf, (area_botoes_x, area_botoes_y))
        
        # Desenhar scrollbar se existir
        if scrollbar:
            # Ajustar posição X para ficar ao lado da área de botões
            scrollbar.x = area_botoes_x + area_botoes_largura + 10
            scrollbar.draw(tela)
        
        # Botão de voltar (posicionado abaixo da área de botões com espaço adequado)
        largura_voltar = 200
        altura_voltar = 50
        x_voltar = LARGURA // 2
        y_voltar = area_botoes_y + area_botoes_altura + 30  # 30px abaixo da grade
        
        rect_voltar = pygame.Rect(x_voltar - largura_voltar // 2, y_voltar - altura_voltar // 2, 
                                  largura_voltar, altura_voltar)
        
        criar_botao(tela, "VOLTAR", x_voltar, y_voltar, largura_voltar, altura_voltar, 
                   (100, 50, 50), (150, 70, 70), BRANCO)
        
        if clique_ocorreu and rect_voltar.collidepoint(mouse_pos):
            return None
        
        # Se uma fase foi selecionada, retornar seu número
        if fase_selecionada is not None:
            return fase_selecionada
        
        present_frame()
        relogio.tick(FPS)