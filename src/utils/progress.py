import json
import os

class ProgressManager:
    """Gerencia o progresso do jogador no jogo."""
    
    def __init__(self):
        self.arquivo_progresso = "data/progresso.json"
        self.fase_maxima = 1
        self._criar_diretorio()
        self._carregar_progresso()
    
    def _criar_diretorio(self):
        """Cria o diretório data se não existir."""
        if not os.path.exists("data"):
            os.makedirs("data")
    
    def _carregar_progresso(self):
        """Carrega o progresso salvo."""
        try:
            with open(self.arquivo_progresso, 'r') as f:
                dados = json.load(f)
                self.fase_maxima = dados.get('fase_maxima', 1)
        except (FileNotFoundError, json.JSONDecodeError):
            self.fase_maxima = 1
            self._salvar_progresso()
    
    def _salvar_progresso(self):
        """Salva o progresso atual."""
        with open(self.arquivo_progresso, 'w') as f:
            json.dump({'fase_maxima': self.fase_maxima}, f)
    
    def atualizar_progresso(self, fase_alcancada):
        """Atualiza o progresso se a fase alcançada for maior que a atual."""
        if fase_alcancada > self.fase_maxima:
            self.fase_maxima = fase_alcancada
            self._salvar_progresso()
    
    def pode_jogar_fase(self, fase):
        """Verifica se o jogador pode jogar uma determinada fase."""
        return fase <= self.fase_maxima
    
    def obter_fase_maxima(self):
        """Retorna a fase máxima alcançada."""
        return self.fase_maxima