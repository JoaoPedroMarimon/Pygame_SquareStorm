#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de resolução e tela cheia para SquareStorm
Mantém as proporções corretas em qualquer monitor
"""

import pygame

class DisplayManager:
    """Gerencia a resolução e modo de tela do jogo."""
    
    def __init__(self):
        # Resolução base do jogo (design original)
        self.BASE_WIDTH = 1480
        self.BASE_HEIGHT = 820
        self.BASE_ASPECT_RATIO = self.BASE_WIDTH / self.BASE_HEIGHT
        
        # Resolução atual da tela
        self.screen_width = self.BASE_WIDTH
        self.screen_height = self.BASE_HEIGHT
        
        # Escala para ajustar elementos da UI
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Offsets para centralizar o jogo na tela
        self.offset_x = 0
        self.offset_y = 0
        
        # Superfície principal do jogo (sempre na resolução base)
        self.game_surface = None
        self.display_surface = None
        
        # Estado do modo tela cheia
        self.fullscreen = False
        
    def initialize_display(self, fullscreen=False):
        """
        Inicializa o display do pygame com a configuração adequada.
        
        Args:
            fullscreen: Se True, inicia em modo tela cheia
        """
        self.fullscreen = fullscreen
        
        if fullscreen:
            # Obter resolução nativa do monitor
            info = pygame.display.Info()
            monitor_width = info.current_w
            monitor_height = info.current_h
            
            # Criar tela em modo tela cheia
            self.display_surface = pygame.display.set_mode(
                (monitor_width, monitor_height), 
                pygame.FULLSCREEN
            )
            
            self.screen_width = monitor_width
            self.screen_height = monitor_height
            
        else:
            # Modo janela com resolução base
            self.display_surface = pygame.display.set_mode(
                (self.BASE_WIDTH, self.BASE_HEIGHT)
            )
            
            self.screen_width = self.BASE_WIDTH
            self.screen_height = self.BASE_HEIGHT
        
        # Sempre criar a superfície do jogo na resolução base
        self.game_surface = pygame.Surface((self.BASE_WIDTH, self.BASE_HEIGHT))
        
        # Calcular escala e offsets
        self._calculate_scaling()
        
        return self.display_surface
    
    def _calculate_scaling(self):
        """Calcula a escala e offsets para manter proporções."""
        
        if not self.fullscreen:
            # Modo janela: sem escala
            self.scale_x = 1.0
            self.scale_y = 1.0
            self.offset_x = 0
            self.offset_y = 0
            return
        
        # Calcular proporção do monitor
        monitor_aspect_ratio = self.screen_width / self.screen_height
        
        if monitor_aspect_ratio > self.BASE_ASPECT_RATIO:
            # Monitor mais largo: escalar baseado na altura
            self.scale_y = self.screen_height / self.BASE_HEIGHT
            self.scale_x = self.scale_y  # Manter proporção
            
            # Calcular dimensões escaladas
            scaled_width = int(self.BASE_WIDTH * self.scale_x)
            
            # Centralizar horizontalmente
            self.offset_x = (self.screen_width - scaled_width) // 2
            self.offset_y = 0
            
        else:
            # Monitor mais alto: escalar baseado na largura
            self.scale_x = self.screen_width / self.BASE_WIDTH
            self.scale_y = self.scale_x  # Manter proporção
            
            # Calcular dimensões escaladas
            scaled_height = int(self.BASE_HEIGHT * self.scale_y)
            
            # Centralizar verticalmente
            self.offset_x = 0
            self.offset_y = (self.screen_height - scaled_height) // 2
    
    def get_game_surface(self):
        """Retorna a superfície onde o jogo deve desenhar."""
        return self.game_surface
    
    def present(self):
        """Apresenta o frame na tela com escalonamento adequado."""
        
        if not self.fullscreen:
            # Modo janela: copiar diretamente
            self.display_surface.blit(self.game_surface, (0, 0))
        else:
            # Modo tela cheia: escalar e centralizar
            
            # Preencher tela com preto (barras pretas nas bordas)
            self.display_surface.fill((0, 0, 0))
            
            # Calcular dimensões escaladas
            scaled_width = int(self.BASE_WIDTH * self.scale_x)
            scaled_height = int(self.BASE_HEIGHT * self.scale_y)
            
            # Escalar a superfície do jogo
            scaled_surface = pygame.transform.scale(
                self.game_surface, 
                (scaled_width, scaled_height)
            )
            
            # Desenhar na posição centralizada
            self.display_surface.blit(scaled_surface, (self.offset_x, self.offset_y))
        
        pygame.display.flip()
    
    def toggle_fullscreen(self):
        """Alterna entre modo janela e tela cheia."""
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # Mudar para tela cheia
            info = pygame.display.Info()
            monitor_width = info.current_w
            monitor_height = info.current_h
            
            self.display_surface = pygame.display.set_mode(
                (monitor_width, monitor_height), 
                pygame.FULLSCREEN
            )
            
            self.screen_width = monitor_width
            self.screen_height = monitor_height
            
        else:
            # Mudar para janela
            self.display_surface = pygame.display.set_mode(
                (self.BASE_WIDTH, self.BASE_HEIGHT)
            )
            
            self.screen_width = self.BASE_WIDTH
            self.screen_height = self.BASE_HEIGHT
        
        # Recalcular escala
        self._calculate_scaling()
    
    def convert_mouse_pos(self, mouse_pos):
        """
        Converte posição do mouse da tela real para coordenadas do jogo.
        
        Args:
            mouse_pos: Tupla (x, y) com posição do mouse na tela
            
        Returns:
            Tupla (x, y) com posição convertida para o jogo
        """
        if not self.fullscreen:
            return mouse_pos
        
        # Ajustar para offset e escala
        game_x = (mouse_pos[0] - self.offset_x) / self.scale_x
        game_y = (mouse_pos[1] - self.offset_y) / self.scale_y
        
        # Limitar às dimensões do jogo
        game_x = max(0, min(self.BASE_WIDTH, game_x))
        game_y = max(0, min(self.BASE_HEIGHT, game_y))
        
        return (int(game_x), int(game_y))
    
    def get_ui_scale(self):
        """
        Retorna fator de escala para elementos de UI.
        Útil para manter tamanhos de fonte e elementos proporcionais.
        """
        return min(self.scale_x, self.scale_y)
    
    def is_fullscreen(self):
        """Retorna True se estiver em modo tela cheia."""
        return self.fullscreen


# Instância global do gerenciador de display
_display_manager = DisplayManager()


def get_display_manager():
    """Retorna a instância global do gerenciador de display."""
    return _display_manager


def initialize_game_display(fullscreen=False):
    """
    Inicializa o sistema de display do jogo.
    
    Args:
        fullscreen: Se True, inicia em modo tela cheia
        
    Returns:
        Superfície onde o jogo deve desenhar
    """
    display_surface = _display_manager.initialize_display(fullscreen)
    pygame.display.set_caption("SquareStorm")
    return _display_manager.get_game_surface()


def present_frame():
    """Apresenta o frame atual na tela."""
    _display_manager.present()


def toggle_fullscreen():
    """Alterna entre modo janela e tela cheia."""
    _display_manager.toggle_fullscreen()


def convert_mouse_position(mouse_pos):
    """Converte posição do mouse para coordenadas do jogo."""
    return _display_manager.convert_mouse_pos(mouse_pos)


def get_ui_scale_factor():
    """Retorna fator de escala para elementos de UI."""
    return _display_manager.get_ui_scale()