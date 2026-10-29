"""Constants, board limits, color codes, and coordinate utilities for chess."""

from enum import IntEnum
from typing import Optional, Tuple


class Color(IntEnum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2


EMPTY = Color.EMPTY
WHITE = Color.WHITE
BLACK = Color.BLACK


def opposite(color: Color) -> Color:
    """Returns the opposing player's color."""
    if color == Color.WHITE:
        return Color.BLACK
    elif color == Color.BLACK:
        return Color.WHITE
    return Color.EMPTY


def color_name(color: Color) -> str:
    """Returns a human-readable name for a color."""
    if color == Color.WHITE:
        return "White"
    elif color == Color.BLACK:
        return "Black"
    return "Empty"


# Board dimensions
BOARD_SIZE = 8
TOTAL_SQUARES = 64

# Starting rows
WHITE_PAWN_START_ROW = 6  # Rank 2
BLACK_PAWN_START_ROW = 1  # Rank 7
WHITE_BACK_ROW = 7        # Rank 1
BLACK_BACK_ROW = 0        # Rank 8

# Column indices for castling
KING_START_COL = 4                   # File 'e'
ROOK_KINGSIDE_START_COL = 7          # File 'h'
ROOK_QUEENSIDE_START_COL = 0         # File 'a'
CASTLE_KINGSIDE_KING_DEST_COL = 6    # File 'g'
CASTLE_QUEENSIDE_KING_DEST_COL = 2   # File 'c'
CASTLE_KINGSIDE_ROOK_DEST_COL = 5    # File 'f'
CASTLE_QUEENSIDE_ROOK_DEST_COL = 3   # File 'd'

# Limits and buffer constants
FEN_TEXT_SIZE = 100
CALC_MAX_ID = 33
COMPARE_WIDTH = 66
LOOP_MAX_DEPTH = 6
LOOP_MAX_FIRST = 256
GOAL_MAX_SQUARES = 16
GOAL_MAX_LIMIT = 4
GOAL_MAX_ROUTES = 512
EXCHANGE_MAX = 8
COMPARE_MAX = 6

# Piece values
PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
    '\0': 0,
    ' ': 0
}

# ANSI Escape sequences for terminal output
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

LIGHT_SQUARE_BG = "\033[48;5;180m"  # Tan background
DARK_SQUARE_BG = "\033[48;5;94m"    # Brown background
LIGHT_TEXT_FG = "\033[38;5;231m"   # Ivory piece text
DARK_TEXT_FG = "\033[38;5;232m"    # Charcoal piece text


def in_bounds(row: int, col: int) -> bool:
    """Checks whether a given row and column coordinate lies within the 8x8 chessboard."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def square_index(row: int, col: int) -> int:
    """Computes a single integer index (0 to 63) for a square on the 8x8 board."""
    return row * BOARD_SIZE + col


def index_to_row_col(index: int) -> Tuple[int, int]:
    """Converts a 0..63 square index into (row, col)."""
    return index // BOARD_SIZE, index % BOARD_SIZE


def square_text(index: int) -> str:
    """Converts a 0..63 square index into algebraic notation (e.g. 'e4')."""
    col = index % BOARD_SIZE
    row = index // BOARD_SIZE
    return f"{chr(ord('a') + col)}{8 - row}"


def parse_square(s: str) -> Optional[Tuple[int, int]]:
    """Converts an algebraic chess square string (e.g. 'e4') into (row, col) coordinates."""
    if not s or len(s) < 2:
        return None
    file_char = s[0].lower()
    rank_char = s[1]
    if not ('a' <= file_char <= 'h') or not ('1' <= rank_char <= '8'):
        return None
    col = ord(file_char) - ord('a')
    row = 8 - int(rank_char)
    return row, col


def home_row_for(side: Color) -> int:
    """Returns the starting back row index for a given side."""
    return WHITE_BACK_ROW if side == Color.WHITE else BLACK_BACK_ROW


def rook_col_for(king_side: bool) -> int:
    """Returns the starting column index for a Rook during castling."""
    return ROOK_KINGSIDE_START_COL if king_side else ROOK_QUEENSIDE_START_COL
