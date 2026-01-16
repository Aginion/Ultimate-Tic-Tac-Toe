from __future__ import annotations
import sys, time, enum
from typing import Union
from dataclasses import dataclass

# =============================================================================
# KONFIGURACJA
# =============================================================================

@dataclass(frozen=True)
class Config:
    """
    Parametry konfiguracyjne bota.
    """
    BOARD_SIZE: int = 3
    # Punkty za wygranie całej gry
    WIN_REWARD: float = 1000.0
    # Punkty za remis
    DRAW_REWARD: float = 0.0
    # Maksymalna głębokość rekurencji (ograniczona też czasem)
    MAX_DEPTH: int = 3
    # Limit czasu na ruch w sekundach (np. 90ms, aby zdążyć przed limitem 100ms platformy)
    TIME_LIMIT: float = 0.09

# =============================================================================
# STRUKTURY DANYCH
# =============================================================================

class Player(enum.Enum):
    OPPONENT = enum.auto()
    PLAYER = enum.auto()

    # Pomocnicza metoda do zmiany tury
    def opponent(self) -> Player:
        return Player.OPPONENT if self == Player.PLAYER else Player.PLAYER

class Cell(enum.Enum):
    EMPTY = enum.auto()

CellState = Union[Cell, Player]

# =============================================================================
# MAŁA PLANSZA (3x3)
# =============================================================================

class GameBoard:
    """
    Reprezentuje pojedynczą planszę 3x3 (jedną z dziewięciu w dużej grze).
    """
    def __init__(self) -> None:
        self.board: list[list[CellState]] = [
            [Cell.EMPTY for _ in range(3)] for _ in range(3)
        ]

    # Zwraca listę wolnych pól na tej konkretnej małej planszy
    def possible_moves(self) -> list[tuple[int, int]]:
        return [(r,c) for r in range(3) for c in range(3) if self.board[r][c] == Cell.EMPTY]

    # Sprawdza wygraną (linie poziome, pionowe, przekątne)
    def win(self, player: Player) -> bool:
        return any(
            all(self.board[i][j] == player for j in range(3)) or
            all(self.board[j][i] == player for j in range(3))
            for i in range(3)
        ) or all(self.board[i][i] == player for i in range(3)) \
          or all(self.board[i][2-i] == player for i in range(3))

    # Sprawdza remis (brak wygranej, ale plansza pełna)
    def draw(self) -> bool:
        if self.win(Player.PLAYER) or self.win(Player.OPPONENT):
            return False
        return all(self.board[r][c] != Cell.EMPTY for r in range(3) for c in range(3))

    # Czy gra na tej małej planszy jest zakończona (wygrana lub remis)?
    def finished(self) -> bool:
        return self.win(Player.PLAYER) or self.win(Player.OPPONENT) or self.draw()

    def make_move(self, r: int, c: int, player: Player) -> None:
        self.board[r][c] = player

    def set_empty(self, r: int, c: int) -> None:
        self.board[r][c] = Cell.EMPTY

# =============================================================================
# DUŻA PLANSZA (ULTIMATE BOARD)
# =============================================================================

class UltimateBoard:
    """
    Główna plansza składająca się z 9 małych plansz (GameBoard).
    Zarządza logiką, która mała plansza jest aktywna w następnym ruchu.
    """
    def __init__(self) -> None:
        self.board: list[list[GameBoard]] = [
            [GameBoard() for _ in range(3)] for _ in range(3)
        ]
        # next_board: krotka (wiersz, kolumna) wskazująca małą planszę, 
        # na której trzeba wykonać ruch. Jeśli None -> można grać wszędzie.
        self.next_board: tuple[int,int]|None = None

    def update_next_board(self, r:int, c:int) -> None:
        """
        Kluczowa zasada Ultimate Tic-Tac-Toe:
        Ruch na polu (r, c) małej planszy wysyła przeciwnika na dużą planszę o współrzędnych (r, c).
        Jeśli tamta plansza jest już skończona (finished), przeciwnik ma wolny wybór (None).
        """
        if self.board[r][c].finished():
            self.next_board = None
        else:
            self.next_board = (r,c)

    def possible_moves(self) -> list[tuple[int,int]]:
        """Generuje wszystkie legalne ruchy w skali globalnej (0-8, 0-8)."""
        moves_list = []
        
        # Sytuacja 1: Jesteśmy zmuszeni grać na konkretnej małej planszy
        if self.next_board is not None:
            r,c = self.next_board
            # Dodatkowe sprawdzenie, czy plansza nie została właśnie zamknięta
            if not self.board[r][c].finished():
                for sr,sc in self.board[r][c].possible_moves():
                    # Przeliczenie współrzędnych lokalnych na globalne
                    moves_list.append((r*3+sr, c*3+sc))
                if moves_list:
                    return moves_list
        
        # Sytuacja 2: Mamy wolny wybór (next_board is None lub wskazana plansza jest pełna)
        # Generujemy ruchy ze wszystkich aktywnych plansz.
        for br in range(3):
            for bc in range(3):
                sb = self.board[br][bc]
                if not sb.finished():
                    for sr,sc in sb.possible_moves():
                        moves_list.append((br*3+sr, bc*3+sc))
        return moves_list

    def make_move(self,row:int,col:int,player:Player)->None:
        # divmod zamienia współrzędne globalne (np. 4, 5) na:
        # br, bc (indeks dużej planszy) oraz sr, sc (indeks wewnątrz małej planszy)
        br,sr = divmod(row,3)
        bc,sc = divmod(col,3)
        self.board[br][bc].make_move(sr,sc,player)
        self.update_next_board(sr,sc)

    def set_empty(self,row:int,col:int)->None:
        br,sr = divmod(row,3)
        bc,sc = divmod(col,3)
        self.board[br][bc].set_empty(sr,sc)

    def win(self,player:Player)->bool:
        # Sprawdza czy gracz wygrał dużą grę (ułożył linię z wygranych małych plansz)
        return any(
            all(self.board[i][j].win(player) for j in range(3)) or
            all(self.board[j][i].win(player) for j in range(3))
            for i in range(3)
        ) or all(self.board[i][i].win(player) for i in range(3)) \
          or all(self.board[i][2-i].win(player) for i in range(3))

    def draw(self)->bool:
        if self.win(Player.PLAYER) or self.win(Player.OPPONENT):
            return False
        # Remis w Ultimate: wszystkie małe plansze są zakończone
        return all(self.board[r][c].finished() for r in range(3) for c in range(3))

# =============================================================================
# HEURYSTYKA (OCENA STANU GRY)
# =============================================================================

def score_small(board:GameBoard, player:Player)->float:
    """Ocena punktowa pojedynczej małej planszy."""
    if board.win(player):
        return 100
    if board.win(player.opponent()):
        return -100
    
    score = 0
    # Analiza linii (wiersze i kolumny)
    for r in range(3):
        row = [board.board[r][c] for c in range(3)]
        col = [board.board[c][r] for c in range(3)]
        for line in [row,col]:
            # Jeśli mamy 2 swoje i 1 puste -> duża szansa (+10)
            if line.count(player)==2 and line.count(Cell.EMPTY)==1:
                score += 10
            # Jeśli przeciwnik ma 2 i 1 puste -> zagrożenie (-10)
            if line.count(player.opponent())==2 and line.count(Cell.EMPTY)==1:
                score -= 10
    
    # Analiza przekątnych
    diag1=[board.board[i][i] for i in range(3)]
    diag2=[board.board[i][2-i] for i in range(3)]
    for diag in [diag1,diag2]:
        if diag.count(player)==2 and diag.count(Cell.EMPTY)==1:
            score+=10
        if diag.count(player.opponent())==2 and diag.count(Cell.EMPTY)==1:
            score-=10
            
    # Bonus za środek (+3) i rogi (+1)
    if board.board[1][1]==player: score+=3
    for r,c in [(0,0),(0,2),(2,0),(2,2)]:
        if board.board[r][c]==player: score+=1
    return score

def score(board:UltimateBoard)->float:
    """Główna funkcja oceniająca całą planszę."""
    if board.win(Player.PLAYER): return 1000
    if board.win(Player.OPPONENT): return -1000
    if board.draw(): return 0
    
    total=0
    for br in range(3):
        for bc in range(3):
            sb=board.board[br][bc]
            total+=score_small(sb,Player.PLAYER)
            # Zachęta do grania na aktywnych planszach (+5), aby nie zamykać gry zbyt szybko,
            # jeśli nie jest to konieczne
            if not sb.finished():
                total+=5 
    return total

# =============================================================================
# SILNIK MINIMAX
# =============================================================================

start_time=0.0
timeout=False

def minimax(board:UltimateBoard,player:Player,alpha:float,beta:float,depth:int):
    """
    Algorytm Minimax z przycinaniem Alpha-Beta i kontrolą czasu.
    """
    global timeout
    # Przerwanie, jeśli przekroczyliśmy limit czasu
    if time.perf_counter()-start_time>Config.TIME_LIMIT:
        timeout=True
        return score(board),None

    # Warunki końcowe rekurencji
    if depth==0 or board.win(Player.PLAYER) or board.win(Player.OPPONENT) or board.draw():
        return score(board),None

    best_move=None

    # --- TURA BOTA (MAX) ---
    if player==Player.PLAYER:
        value=-float('inf')
        for move in board.possible_moves():
            # Zapisujemy stan next_board, aby go potem przywrócić
            prev_next=board.next_board
            
            board.make_move(*move,player)
            eval_score,_=minimax(board,player.opponent(),alpha,beta,depth-1)
            
            # Cofanie ruchu (Backtracking)
            board.set_empty(*move)
            board.next_board=prev_next
            
            if timeout: break # Szybkie wyjście po timeout
            
            if eval_score>value:
                value=eval_score
                best_move=move
            
            # Alpha: najlepszy wynik, jaki gracz MAX może sobie zagwarantować
            alpha=max(alpha,value)
            if alpha>=beta: break # Beta cutoff
        return value,best_move

    # --- TURA PRZECIWNIKA (MIN) ---
    else:
        value=float('inf')
        for move in board.possible_moves():
            prev_next=board.next_board
            
            board.make_move(*move,player)
            eval_score,_=minimax(board,player.opponent(),alpha,beta,depth-1)
            
            board.set_empty(*move)
            board.next_board=prev_next
            
            if timeout: break
            
            if eval_score<value:
                value=eval_score
                best_move=move
            
            # Beta: najlepszy wynik, jaki gracz MIN może wymusić (najniższy)
            beta=min(beta,value)
            if beta<=alpha: break # Alpha cutoff
        return value,best_move

# =============================================================================
# PĘTLA GRY
# =============================================================================

def game_loop()->None:
    board=UltimateBoard()
    while True:
        # Odczyt danych wejściowych (format typowy dla platform typu CodinGame)
        opponent_row,opponent_col=map(int,input().split())
        valid_action_count=int(input())
        valid_moves=set()
        for _ in range(valid_action_count):
            r,c=map(int,input().split())
            valid_moves.add((r,c))
            
        # Aktualizacja planszy ruchem przeciwnika (jeśli to nie 1. tura)
        if opponent_row!=-1:
            board.make_move(opponent_row,opponent_col,Player.OPPONENT)
            
        # Iterative Deepening (Pogłębianie iteracyjne)
        # Zamiast od razu szukać na głębokość MAX, szukamy na 1, potem 2, itd.
        # Dzięki temu jeśli skończy się czas, mamy gotowy wynik z płytszego poziomu.
        global start_time,timeout
        start_time=time.perf_counter()
        best_move=None
        
        for depth in range(1,Config.MAX_DEPTH+1):
            timeout=False
            _,move=minimax(board,Player.PLAYER,-float('inf'),float('inf'),depth)
            
            # Zapisujemy wynik tylko jeśli nie było timeoutu
            if not timeout and move is not None:
                best_move=move
            else:
                break
        
        # Fallback: jeśli algorytm nie znalazł nic (np. natychmiastowy timeout), bierzemy pierwszy lepszy ruch
        if best_move is None:
            best_move=next(iter(valid_moves))
            
        # Wykonanie i wypisanie ruchu
        row,col=best_move
        board.make_move(row,col,Player.PLAYER)
        print(f"{row} {col}",file=sys.stderr,flush=True) # Logi debugowania
        print(f"{row} {col}",flush=True) # Właściwy ruch dla gry

game_loop()