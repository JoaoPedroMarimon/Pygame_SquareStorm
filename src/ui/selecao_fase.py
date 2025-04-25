import pygame
import sys
from ..config import *
from ..utils.visual import criar_botao, desenhar_texto, criar_estrelas, desenhar_estrelas
from ..utils.progress import ProgressManager
import random

def tela_selecao_fase(tela, relogio, gradiente_selecao, fonte_titulo, fonte_normal):
    """
    Exibe a tela de seleção de fases.
    
    Returns:
        Número da fase selecionada ou None se cancelar
    """
    pygame.mouse.set_visible(True)
    progress_manager = ProgressManager()
    fase_maxima = progress_manager.obter_fase_maxima()
    
    # Criar efeitos visuais
    estrelas = criar_estrelas(50)
    
    # Posições dos botões de fases
    cols = 3
    rows = 2
    tamanho_botao = 100
    espacamento = 30
    inicio_x = LARGURA // 2 - (cols * (tamanho_botao + espacamento) - espacamento) // 2
    inicio_y = ALTURA // 3
    
    # Loop principal
    while True:
        clique_ocorreu = False
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clique_ocorreu = True
        
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
        desenhar_texto(tela, "SELECIONE A FASE", 60, BRANCO, LARGURA // 2, ALTURA // 6, fonte_titulo)
        
        # Desenhar botões de fases
        mouse_pos = pygame.mouse.get_pos()
        
        for fase in range(1, 7):
            row = (fase - 1) // cols
            col = (fase - 1) % cols
            x = inicio_x + col * (tamanho_botao + espacamento)
            y = inicio_y + row * (tamanho_botao + espacamento)
            
            # Verificar se a fase está desbloqueada
            desbloqueada = progress_manager.pode_jogar_fase(fase)
            
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
            
            # Verificar hover
            hover = rect.collidepoint(mouse_pos) and desbloqueada
            
            # Desenhar botão
            pygame.draw.rect(tela, cor_hover if hover else cor_normal, rect, 0, 10)
            pygame.draw.rect(tela, BRANCO if desbloqueada else (80, 80, 80), rect, 2, 10)
            
            # Texto do botão
            desenhar_texto(tela, str(fase), 36, cor_texto, x + tamanho_botao // 2, y + tamanho_botao // 2, fonte_normal)
            
            # Verificar clique
            if clique_ocorreu and hover and desbloqueada:
                return fase
        
        # Botão de voltar
        largura_voltar = 200
        altura_voltar = 50
        x_voltar = LARGURA // 2
        y_voltar = ALTURA - 100
        
        rect_voltar = pygame.Rect(x_voltar - largura_voltar // 2, y_voltar - altura_voltar // 2, 
                                  largura_voltar, altura_voltar)
        
        criar_botao(tela, "VOLTAR", x_voltar, y_voltar, largura_voltar, altura_voltar, 
                   (100, 50, 50), (150, 70, 70), BRANCO)
        
        if clique_ocorreu and rect_voltar.collidepoint(mouse_pos):
            return None
        
        pygame.display.flip()
        relogio.tick(FPS)