"""Shared building blocks for the study tools.

Holds the small data types (Goal, RouteVector, ...), the global "show risk"
switch, and helper functions that several study modules use.
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import List
from ..constants import BOARD_SIZE, TOTAL_SQUARES, Color
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, make_move, piece_attacks


# ----------------------------------------------------------------------------
# Data types
# ----------------------------------------------------------------------------

class GoalCondition(Enum):
    COND_REACH = 0
    COND_PROTECTED = 1


@dataclass
class Goal:
    active: bool = False
    king: bool = False
    count: int = 0
    squares: List[int] = field(default_factory=list)
    limit: int = 1


class RealResult(IntEnum):
    REAL_ELSE = 0
    REAL_POSSIBLE = 1
    REAL_FORCED = 2


class MaterialResult(IntEnum):
    MATERIAL_ELSE = 0
    MATERIAL_POSSIBLE = 1
    MATERIAL_FORCED = 2


@dataclass
class RouteVector:
    own: int = 0
    protectors: int = 0
    attackers: int = 0
    path: List[Move] = field(default_factory=list)
    length: int = 0
    dominated: bool = False
    raw_text: str = ""


# ----------------------------------------------------------------------------
# Risk toggle (shared by routes and the CLI)
# ----------------------------------------------------------------------------

# Global risk toggle for Stage 3D/3E
goal_show_risk = False


def set_goal_show_risk(val: bool) -> None:
    global goal_show_risk
    goal_show_risk = val


def get_goal_show_risk() -> bool:
    global goal_show_risk
    return goal_show_risk


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def move_distance(m: Move) -> int:
    """Chebyshev distance (King distance): max(|dr|, |dc|)."""
    return max(abs(m.er - m.sr), abs(m.ec - m.sc))


def order_label(values: List[int], value: int) -> str:
    """Returns IF (if no valid element is smaller), ELSE (if no valid element is larger), or ELSE IF."""
    has_smaller = any(v >= 0 and v < value for v in values)
    has_larger = any(v >= 0 and v > value for v in values)
    if not has_smaller:
        return "IF"
    elif not has_larger:
        return "ELSE"
    return "ELSE IF"


def pass_moves(board: Board, side: Color) -> List[Move]:
    """Moves available for `side` evaluated as if it were its turn."""
    view = board.clone()
    view.turn = side
    return sorted_moves(view)


def pass_play(board: Board, move: Move, side: Color) -> None:
    """Plays move in PASS mode where opponent passes."""
    board.turn = side
    make_move(board, move)
    board.turn = side
    board.ep_row = -1
    board.ep_col = -1


def pieces_on_square(board: Board, sq: int, side: Color) -> int:
    """Counts friendly pieces attacking/defending sq (excluding piece on sq itself)."""
    # Reject bad indexes: Python would accept grid[-1] and give a wrong answer.
    if not isinstance(sq, int) or sq < 0 or sq >= TOTAL_SQUARES:
        return 0
    count = 0
    tr, tc = sq // BOARD_SIZE, sq % BOARD_SIZE
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            curr_sq = r * BOARD_SIZE + c
            if curr_sq != sq and board.grid[r][c].color == side:
                if piece_attacks(board, r, c, tr, tc):
                    count += 1
    return count


def piece_value(ptype: str) -> int:
    return {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}.get(ptype, 0)
