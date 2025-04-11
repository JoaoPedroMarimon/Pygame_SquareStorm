# SQUARE VERSUS SQUARE

Um jogo de batalha espacial entre formas geométricas com sistema de fases progressivas.

## Descrição

Neste jogo, você controla um quadrado azul que deve enfrentar quadrados inimigos vermelhos. A cada fase, um novo inimigo é adicionado, aumentando a dificuldade. Você precisa derrotar todos os inimigos para avançar para a próxima fase.

## Controles

- **WASD**: Movimentação
- **ESPAÇO**: Atirar para a direita
- **Setas**: Atirar em direções específicas
- **P**: Pausar o jogo
- **ESC**: Sair

## Requisitos

- Python 3.x
- Pygame

## Instalação

1. Clone este repositório
2. Instale as dependências: `pip install pygame`
3. Execute o jogo: `python main.py`

## Estrutura do Projeto

O jogo foi organizado em módulos para facilitar a manutenção e extensão:

- `entities/`: Classes de entidades (quadrados, tiros, partículas)
- `game/`: Lógica do jogo e gerenciamento de fases
- `ui/`: Interface com o usuário e menus
- `utils/`: Ferramentas auxiliares (efeitos visuais, sons)