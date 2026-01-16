from __future__ import annotations
import sys
import enum
from typing import Union
from dataclasses import dataclass

# =============================================================================
# KONFIGURACJA I STAŁE
# =============================================================================

@dataclass(frozen=True)
class Config:
    # Rozmiar planszy (3x3)
    BOARD_SIZE: int = 3
    # Punkty przyznawane za wygraną
    WIN_REWARD: float = 1.0
    # Punkty przyznawane za remis
    DRAW_REWARD: float = 0.0


# =============================================================================
# STRUKTURY DANYCH (GRACZ I KOMÓRKA)
# =============================================================================

class Player(enum.Enum):
    OPPONENT = enum.auto()
    PLAYER = enum.auto()

    # Zwraca przeciwnika dla aktualnego gracza
    def opponent(self) -> Player:
        return Player.OPPONENT if self == Player.PLAYER else Player.PLAYER


class Cell(enum.Enum):
    EMPTY = enum.auto()


CellState = Union[Cell, Player]


# =============================================================================
# KLASA PLANSZY
# =============================================================================

class GameBoard:
    def __init__(self) -> None:
        # Inicjalizacja pustej planszy 3x3
        self.board: list[list[CellState]] = [
            [Cell.EMPTY for _ in range(Config.BOARD_SIZE)] for _ in range(Config.BOARD_SIZE)
        ]

    # Zwraca listę wszystkich pustych pól (możliwych ruchów)
    # Jeśli gra jest już zakończona (ktoś wygrał), zwraca pustą listę.
    def possible_moves(self) -> list[tuple[int, int]]:
        if self.win(Player.OPPONENT) or self.win(Player.PLAYER):
            return []
        return [
            (r, c)
            for r in range(Config.BOARD_SIZE)
            for c in range(Config.BOARD_SIZE)
            if self.board[r][c] == Cell.EMPTY
        ]

    # Sprawdza, czy podany gracz wygrał (wiersze, kolumny, przekątne)
    def win(self, player: Player) -> bool:
        return any(
            all(self.board[i][j] == player for j in range(Config.BOARD_SIZE)) or
            all(self.board[j][i] == player for j in range(Config.BOARD_SIZE))
            for i in range(Config.BOARD_SIZE)
        ) or all(self.board[i][i] == player for i in range(Config.BOARD_SIZE)) or all(self.board[i][2 - i] == player for i in range(Config.BOARD_SIZE))

    # Sprawdza remis: brak wygranych i brak wolnych pól
    def draw(self) -> bool:
        return not self.win(Player.PLAYER) and not self.win(Player.OPPONENT) and not self.possible_moves()

    # Wykonuje ruch na planszy (ustawia pionek gracza)
    def make_move(self, row: int, col: int, player: Player) -> None:
        if self.board[row][col] != Cell.EMPTY:
            raise ValueError("Cell is already taken")
        self.board[row][col] = player

    # Cofa ruch (ustawia pole z powrotem na puste) - kluczowe dla algorytmu Minimax
    def set_empty(self, row: int, col: int) -> None:
        self.board[row][col] = Cell.EMPTY


# =============================================================================
# ALGORYTM MINIMAX (SILNIK GRY)
# =============================================================================

# Funkcja realizująca algorytm Minimax z przycinaniem Alpha-Beta.
# Parametry:
# - game_board: aktualny stan gry
# - player: gracz, którego ruch jest symulowany
# - alpha: najlepszy wynik gwarantowany dla gracza maksymalizującego (nasz bot)
# - beta: najlepszy wynik gwarantowany dla gracza minimalizującego (przeciwnik)
# - depth: głębokość rekurencji (im głębiej, tym więcej ruchów do przodu)
def minimax(
    game_board: GameBoard,
    player: Player,
    alpha: float,
    beta: float,
    depth: int = 0
) -> tuple[float, tuple[int, int] | None]:

    # 1. BAZA REKURENCJI - SPRAWDZENIE STANU KOŃCOWEGO
    
    # Jeśli wygrał nasz bot (PLAYER):
    # Odejmujemy głębokość od nagrody, aby preferować szybsze zwycięstwa.
    # (Wygrałem w 1 ruchu > Wygrałem w 5 ruchach)
    if game_board.win(Player.PLAYER):
        return Config.WIN_REWARD - (depth * 0.01), None
    
    # Jeśli wygrał przeciwnik (OPPONENT):
    # Dodajemy głębokość do kary, aby preferować późniejsze przegrane.
    # (Przegram za 10 ruchów > Przegram w następnym ruchu) - czyli "bronimy się"
    if game_board.win(Player.OPPONENT):
        return -Config.WIN_REWARD + (depth * 0.01), None

    # Pobranie listy dostępnych ruchów
    moves = [
        (r, c) 
        for r in range(Config.BOARD_SIZE) 
        for c in range(Config.BOARD_SIZE) 
        if game_board.board[r][c] == Cell.EMPTY
    ]

    # Jeśli nie ma ruchów, a nikt nie wygrał, to mamy remis
    if not moves:
        return Config.DRAW_REWARD, None

    best_move: tuple[int, int] | None = None

    # 2. RUCH GRACZA MAKSYMALIZUJĄCEGO (TO MY - PLAYER)
    if player == Player.PLAYER:
        max_eval = -float("inf") # Szukamy najwyższego możliwego wyniku
        
        for row, col in moves:
            # Wykonaj symulowany ruch
            game_board.make_move(row, col, player)
            
            # Rekurencyjne wywołanie dla przeciwnika (zwiększamy głębokość)
            eval_score, _ = minimax(game_board, player.opponent(), alpha, beta, depth + 1)
            
            # Cofnij ruch (Backtracking), aby przywrócić planszę do stanu pierwotnego
            game_board.set_empty(row, col)

            # Jeśli znaleziony wynik jest lepszy od dotychczasowego maksimum, zapisz go
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (row, col)

            # Aktualizacja Alpha (najlepszy wynik, jaki my możemy sobie zagwarantować)
            alpha = max(alpha, eval_score)
            
            # Przycinanie Beta (Beta Cutoff):
            # Jeśli nasza najlepsza opcja (alpha) jest lepsza lub równa temu, 
            # na co pozwoli przeciwnik w innej gałęzi (beta), to przeciwnik 
            # nigdy nie pozwoli nam wejść w tę odnogę drzewa. Przerywamy pętlę.
            if beta <= alpha:
                break

        return max_eval, best_move

    # 3. RUCH GRACZA MINIMALIZUJĄCEGO (TO PRZECIWNIK - OPPONENT)
    else:
        min_eval = float("inf") # Szukamy najniższego możliwego wyniku (najlepszego dla wroga)
        
        for row, col in moves:
            # Wykonaj symulowany ruch
            game_board.make_move(row, col, player)
            
            # Rekurencyjne wywołanie dla nas (zwiększamy głębokość)
            eval_score, _ = minimax(game_board, player.opponent(), alpha, beta, depth + 1)
            
            # Cofnij ruch (Backtracking)
            game_board.set_empty(row, col)

            # Jeśli wynik jest gorszy dla nas (lepszy dla wroga), zapisz go
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (row, col)

            # Aktualizacja Beta (najlepszy wynik, jaki przeciwnik może wymusić - czyli najniższy dla nas)
            beta = min(beta, eval_score)
            
            # Przycinanie Alpha (Alpha Cutoff):
            # Jeśli przeciwnik znalazł ruch (beta), który jest dla nas fatalny (gorszy niż 
            # to, co już mamy zagwarantowane w alpha), to my nigdy nie wybierzemy 
            # tej ścieżki prowadzącej do obecnego węzła. Przerywamy.
            if beta <= alpha:
                break

        return min_eval, best_move


# =============================================================================
# GŁÓWNA PĘTLA GRY
# =============================================================================

def game_loop() -> None:
    game_board: GameBoard = GameBoard()
    while True:
        # Odczyt danych wejściowych (ruch przeciwnika)
        opponent_row, opponent_col = [int(i) for i in input().split()]
        valid_action_count = int(input())
        for _ in range(valid_action_count):
            row, col = [int(j) for j in input().split()]

        # Jeśli to nie jest pierwsza runda (przeciwnik wykonał ruch)
        if opponent_row != -1:
            game_board.make_move(opponent_row, opponent_col, Player.OPPONENT)

        # Uruchomienie Minimaxa (startujemy z -inf i +inf dla alphy i bety)
        _, move = minimax(game_board, Player.PLAYER, -float("inf"), float("inf"))
        
        # Wykonanie naszego najlepszego ruchu
        row, col = move
        game_board.make_move(row, col, Player.PLAYER)

        # Wysłanie ruchu na wyjście (stderr dla logów, stdout dla systemu gry)
        print(str(row) + ' ' + str(col), file=sys.stderr, flush=True)
        print(str(row) + ' ' + str(col))


if __name__ == "__main__":
    game_loop()