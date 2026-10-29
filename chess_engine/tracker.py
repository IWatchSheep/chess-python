"""Track each piece by a stable ID (1..32) across moves.

The board only stores what piece type is on a square. The Tracker remembers
*which* knight/pawn it was, so calc/replies reports can say LOST/GAINED per piece.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from .constants import (
    BOARD_SIZE, TOTAL_SQUARES, CALC_MAX_ID,
    Color, EMPTY, WHITE, BLACK,
    square_index, square_text
)
from .board import Board
from .move import Move
from .movegen import legal_destination_map, make_move
from .ui import resolve_piece_after_move


class FollowCase(Enum):
    FOLLOW_STAYS = 1
    FOLLOW_MOVED = 2
    FOLLOW_CASTLING_ROOK = 3
    FOLLOW_CAPTURED = 4
    FOLLOW_PROMOTED = 5


class Snapshot:
    """Captures mobility and square control facts for a board state."""

    def __init__(self):
        self.present: List[bool] = [False] * CALC_MAX_ID
        self.row: List[int] = [0] * CALC_MAX_ID
        self.col: List[int] = [0] * CALC_MAX_ID
        self.legal: List[List[bool]] = [[False] * TOTAL_SQUARES for _ in range(CALC_MAX_ID)]
        self.legal_count: List[int] = [0] * CALC_MAX_ID
        self.reach: Dict[Color, List[bool]] = {
            WHITE: [False] * TOTAL_SQUARES,
            BLACK: [False] * TOTAL_SQUARES
        }


def follow_piece(
    before: Board, move: Move, row: int, col: int
) -> Tuple[int, int, str, FollowCase]:
    """Follows a single piece across a move for piece-tracking reports."""
    from .constants import in_bounds

    if not in_bounds(row, col):
        return -1, -1, "\0", FollowCase.FOLLOW_CAPTURED
    if not (in_bounds(move.sr, move.sc) and in_bounds(move.er, move.ec)):
        return row, col, before.grid[row][col].type, FollowCase.FOLLOW_STAYS

    piece = before.grid[row][col]
    mover = before.grid[move.sr][move.sc]

    if row == move.sr and col == move.sc:
        after_row = move.er
        after_col = move.ec
        if mover.type == 'P' and (move.er == 0 or move.er == 7):
            after_type = 'Q' if (not move.promotion or move.promotion == '\0') else move.promotion
            return after_row, after_col, after_type, FollowCase.FOLLOW_PROMOTED
        return after_row, after_col, piece.type, FollowCase.FOLLOW_MOVED

    after_row, after_col, captured = resolve_piece_after_move(before, move, row, col)
    if captured:
        return -1, -1, piece.type, FollowCase.FOLLOW_CAPTURED
    if after_col != col:
        return after_row, after_col, piece.type, FollowCase.FOLLOW_CASTLING_ROOK

    return after_row, after_col, piece.type, FollowCase.FOLLOW_STAYS


class Tracker:
    """Tracks pieces by unique ID (1..32) across moves for fact analysis."""

    def __init__(self, board: Optional[Board] = None):
        self.grid: List[List[int]] = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.color: List[Color] = [EMPTY] * CALC_MAX_ID
        self.lost: List[List[bool]] = [[False] * TOTAL_SQUARES for _ in range(CALC_MAX_ID)]
        if board:
            self.init_from_board(board)

    def clone(self) -> 'Tracker':
        new_t = Tracker()
        new_t.grid = [list(row) for row in self.grid]
        new_t.color = list(self.color)
        new_t.lost = [list(row) for row in self.lost]
        return new_t

    def init_from_board(self, board: Board) -> None:
        """Assigns unique IDs (1..32) to all pieces on the board."""
        next_id = 1
        self.grid = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.color = [EMPTY] * CALC_MAX_ID
        self.lost = [[False] * TOTAL_SQUARES for _ in range(CALC_MAX_ID)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = board.grid[r][c]
                if p.is_empty or next_id >= CALC_MAX_ID:
                    continue
                self.grid[r][c] = next_id
                self.color[next_id] = p.color
                next_id += 1

    def make_names(self, board: Board) -> Dict[int, str]:
        """Maps piece ID to its display name (e.g. 'P e2')."""
        names: Dict[int, str] = {}
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pid = self.grid[r][c]
                if 1 <= pid < CALC_MAX_ID:
                    sq = square_text(square_index(r, c))
                    names[pid] = f"{board.grid[r][c].type} {sq}"
        return names

    def take_snapshot(self, board: Board) -> Snapshot:
        """Takes a snapshot of piece mobility and square reach."""
        snap = Snapshot()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pid = self.grid[r][c]
                if pid <= 0 or pid >= CALC_MAX_ID:
                    continue

                side = board.grid[r][c].color
                destinations = legal_destination_map(board, r, c, side)

                snap.present[pid] = True
                snap.row[pid] = r
                snap.col[pid] = c

                for i in range(TOTAL_SQUARES):
                    tr, tc = i // BOARD_SIZE, i % BOARD_SIZE
                    if destinations[tr][tc]:
                        snap.legal[pid][i] = True
                        snap.legal_count[pid] += 1
                        snap.reach[side][i] = True

        return snap

    def ids_after_move(
        self, before: Board, move: Move
    ) -> Tuple[List[List[int]], List[bool]]:
        """Maps where each piece ID ends up after move."""
        after_grid = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        captured = [False] * CALC_MAX_ID

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pid = self.grid[r][c]
                if pid <= 0 or pid >= CALC_MAX_ID:
                    continue

                to_r, to_c, _, outcome = follow_piece(before, move, r, c)
                if outcome == FollowCase.FOLLOW_CAPTURED:
                    captured[pid] = True
                elif 0 <= to_r < BOARD_SIZE and 0 <= to_c < BOARD_SIZE:
                    after_grid[to_r][to_c] = pid
                # else: skip bad coordinates (defensive; should not happen)

        return after_grid, captured

    def commit(self, board: Board, move: Move) -> None:
        """Commits move into tracker, updating lost squares."""
        after_board = board.clone()
        make_move(after_board, move)

        after_grid, captured = self.ids_after_move(board, move)
        s0 = self.take_snapshot(board)

        # Build temporary tracker for s1 snapshot
        temp_tracker = Tracker()
        temp_tracker.grid = after_grid
        s1 = temp_tracker.take_snapshot(after_board)

        for pid in range(1, CALC_MAX_ID):
            if captured[pid]:
                self.lost[pid] = [False] * TOTAL_SQUARES
                continue
            if not s1.present[pid]:
                continue
            for i in range(TOTAL_SQUARES):
                if s0.legal[pid][i] and not s1.legal[pid][i]:
                    self.lost[pid][i] = True
                elif not s0.legal[pid][i] and s1.legal[pid][i]:
                    self.lost[pid][i] = False

        self.grid = after_grid


def position_after(
    board: Board, tracker: Tracker, move: Move
) -> Tuple[Board, Tracker]:
    """Computes both board and tracker state after move."""
    after_board = board.clone()
    after_tracker = tracker.clone()
    after_tracker.commit(board, move)
    make_move(after_board, move)
    return after_board, after_tracker
