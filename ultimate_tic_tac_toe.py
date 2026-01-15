from __future__ import annotations
import sys, time, enum
from typing import Union
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    BOARD_SIZE: int = 3
    WIN_REWARD: float = 1000.0
    DRAW_REWARD: float = 0.0
    MAX_DEPTH: int = 3
    TIME_LIMIT: float = 0.09  # 90ms

class Player(enum.Enum):
    OPPONENT = enum.auto()
    PLAYER = enum.auto()

    def opponent(self) -> Player:
        return Player.OPPONENT if self == Player.PLAYER else Player.PLAYER

class Cell(enum.Enum):
    EMPTY = enum.auto()

CellState = Union[Cell, Player]

class GameBoard:
    def __init__(self) -> None:
        self.board: list[list[CellState]] = [
            [Cell.EMPTY for _ in range(3)] for _ in range(3)
        ]

    def possible_moves(self) -> list[tuple[int, int]]:
        return [(r,c) for r in range(3) for c in range(3) if self.board[r][c] == Cell.EMPTY]

    def win(self, player: Player) -> bool:
        return any(
            all(self.board[i][j] == player for j in range(3)) or
            all(self.board[j][i] == player for j in range(3))
            for i in range(3)
        ) or all(self.board[i][i] == player for i in range(3)) \
          or all(self.board[i][2-i] == player for i in range(3))

    def draw(self) -> bool:
        if self.win(Player.PLAYER) or self.win(Player.OPPONENT):
            return False
        return all(self.board[r][c] != Cell.EMPTY for r in range(3) for c in range(3))

    def finished(self) -> bool:
        return self.win(Player.PLAYER) or self.win(Player.OPPONENT) or self.draw()

    def make_move(self, r: int, c: int, player: Player) -> None:
        self.board[r][c] = player

    def set_empty(self, r: int, c: int) -> None:
        self.board[r][c] = Cell.EMPTY

class UltimateBoard:
    def __init__(self) -> None:
        self.board: list[list[GameBoard]] = [
            [GameBoard() for _ in range(3)] for _ in range(3)
        ]
        self.next_board: tuple[int,int]|None = None

    def update_next_board(self, r:int, c:int) -> None:
        if self.board[r][c].finished():
            self.next_board = None
        else:
            self.next_board = (r,c)

    def possible_moves(self) -> list[tuple[int,int]]:
        moves_list = []
        if self.next_board is not None:
            r,c = self.next_board
            if not self.board[r][c].finished():
                for sr,sc in self.board[r][c].possible_moves():
                    moves_list.append((r*3+sr, c*3+sc))
                if moves_list:
                    return moves_list
        for br in range(3):
            for bc in range(3):
                sb = self.board[br][bc]
                if not sb.finished():
                    for sr,sc in sb.possible_moves():
                        moves_list.append((br*3+sr, bc*3+sc))
        return moves_list

    def make_move(self,row:int,col:int,player:Player)->None:
        br,sr = divmod(row,3)
        bc,sc = divmod(col,3)
        self.board[br][bc].make_move(sr,sc,player)
        self.update_next_board(sr,sc)

    def set_empty(self,row:int,col:int)->None:
        br,sr = divmod(row,3)
        bc,sc = divmod(col,3)
        self.board[br][bc].set_empty(sr,sc)

    def win(self,player:Player)->bool:
        return any(
            all(self.board[i][j].win(player) for j in range(3)) or
            all(self.board[j][i].win(player) for j in range(3))
            for i in range(3)
        ) or all(self.board[i][i].win(player) for i in range(3)) \
          or all(self.board[i][2-i].win(player) for i in range(3))

    def draw(self)->bool:
        if self.win(Player.PLAYER) or self.win(Player.OPPONENT):
            return False
        return all(self.board[r][c].finished() for r in range(3) for c in range(3))

def score_small(board:GameBoard, player:Player)->float:
    if board.win(player):
        return 100
    if board.win(player.opponent()):
        return -100
    score = 0
    for r in range(3):
        row = [board.board[r][c] for c in range(3)]
        col = [board.board[c][r] for c in range(3)]
        for line in [row,col]:
            if line.count(player)==2 and line.count(Cell.EMPTY)==1:
                score += 10
            if line.count(player.opponent())==2 and line.count(Cell.EMPTY)==1:
                score -= 10
    diag1=[board.board[i][i] for i in range(3)]
    diag2=[board.board[i][2-i] for i in range(3)]
    for diag in [diag1,diag2]:
        if diag.count(player)==2 and diag.count(Cell.EMPTY)==1:
            score+=10
        if diag.count(player.opponent())==2 and diag.count(Cell.EMPTY)==1:
            score-=10
    if board.board[1][1]==player: score+=3
    for r,c in [(0,0),(0,2),(2,0),(2,2)]:
        if board.board[r][c]==player: score+=1
    return score

def score(board:UltimateBoard)->float:
    if board.win(Player.PLAYER): return 1000
    if board.win(Player.OPPONENT): return -1000
    if board.draw(): return 0
    total=0
    for br in range(3):
        for bc in range(3):
            sb=board.board[br][bc]
            total+=score_small(sb,Player.PLAYER)
            if not sb.finished():
                total+=5 
    return total

start_time=0.0
timeout=False

def minimax(board:UltimateBoard,player:Player,alpha:float,beta:float,depth:int):
    global timeout
    if time.perf_counter()-start_time>Config.TIME_LIMIT:
        timeout=True
        return score(board),None
    if depth==0 or board.win(Player.PLAYER) or board.win(Player.OPPONENT) or board.draw():
        return score(board),None
    best_move=None
    if player==Player.PLAYER:
        value=-float('inf')
        for move in board.possible_moves():
            prev_next=board.next_board
            board.make_move(*move,player)
            eval_score,_=minimax(board,player.opponent(),alpha,beta,depth-1)
            board.set_empty(*move)
            board.next_board=prev_next
            if timeout: break
            if eval_score>value:
                value=eval_score
                best_move=move
            alpha=max(alpha,value)
            if alpha>=beta: break
        return value,best_move
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
            beta=min(beta,value)
            if beta<=alpha: break
        return value,best_move


def game_loop()->None:
    board=UltimateBoard()
    while True:
        opponent_row,opponent_col=map(int,input().split())
        valid_action_count=int(input())
        valid_moves=set()
        for _ in range(valid_action_count):
            r,c=map(int,input().split())
            valid_moves.add((r,c))
        if opponent_row!=-1:
            board.make_move(opponent_row,opponent_col,Player.OPPONENT)
        global start_time,timeout
        start_time=time.perf_counter()
        best_move=None
        for depth in range(1,Config.MAX_DEPTH+1):
            timeout=False
            _,move=minimax(board,Player.PLAYER,-float('inf'),float('inf'),depth)
            if not timeout and move is not None:
                best_move=move
            else:
                break
        if best_move is None:
            best_move=next(iter(valid_moves))
        row,col=best_move
        board.make_move(row,col,Player.PLAYER)
        print(f"{row} {col}",file=sys.stderr,flush=True)
        print(f"{row} {col}",flush=True)

game_loop()
