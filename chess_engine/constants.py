"""Shared chess constants and safe square helpers.

Board layout reminder (row, col):
  row 0 = rank 8 (Black's back rank)
  row 7 = rank 1 (White's back rank)
  col 0 = file a ... col 7 = file h

Square index 0..63 = row * 8 + col  (a8=0, h1=63).
"""

from enum import IntEnum
from typing import Optional, Tuple


class Color(IntEnum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2


EMPTY = Color.EMPTY
WHITE = Color.WHITE
BLACK = Color.BLACK

BOARD_SIZE = 8
TOTAL_SQUARES = 64

# Starting rows
WHITE_PAWN_START_ROW = 6  # rank 2
BLACK_PAWN_START_ROW = 1  # rank 7
WHITE_BACK_ROW = 7        # rank 1
BLACK_BACK_ROW = 0        # rank 8

# Castling columns (0=a ... 7=h)
KING_START_COL = 4
ROOK_KINGSIDE_START_COL = 7
ROOK_QUEENSIDE_START_COL = 0
CASTLE_KINGSIDE_KING_DEST_COL = 6
CASTLE_QUEENSIDE_KING_DEST_COL = 2
CASTLE_KINGSIDE_ROOK_DEST_COL = 5
CASTLE_QUEENSIDE_ROOK_DEST_COL = 3

# Size limits (guard against huge input / runaway lists)
FEN_TEXT_SIZE = 100
FEN_NUMBER_MAX_DIGITS = 9
HISTORY_MAX_LEN = 512
CALC_MAX_ID = 33
COMPARE_WIDTH = 66
LOOP_MAX_DEPTH = 6
LOOP_MAX_FIRST = 256
GOAL_MAX_SQUARES = 16
GOAL_MAX_LIMIT = 4
GOAL_MAX_ROUTES = 512
EXCHANGE_MAX = 8
COMPARE_MAX = 6
MAX_COMMAND_CHARS = 512
MAX_SLIDE_STEPS = 7  # longest clear path on an 8x8 board

PIECE_VALUES = {
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
    "K": 0,
    "\0": 0,
    " ": 0,
}

# Terminal colors
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"
LIGHT_SQUARE_BG = "\033[48;5;180m"
DARK_SQUARE_BG = "\033[48;5;94m"
LIGHT_TEXT_FG = "\033[38;5;231m"
DARK_TEXT_FG = "\033[38;5;232m"


def opposite(color: Color) -> Color:
    """White <-> Black. Empty stays Empty."""
    if color == Color.WHITE:
        return Color.BLACK
    if color == Color.BLACK:
        return Color.WHITE
    return Color.EMPTY


def color_name(color: Color) -> str:
    if color == Color.WHITE:
        return "White"
    if color == Color.BLACK:
        return "Black"
    return "Empty"


def in_bounds(row: int, col: int) -> bool:
    """True if (row, col) is on the 8x8 board."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def square_index(row: int, col: int) -> int:
    """(row, col) -> 0..63. Returns -1 if out of bounds (avoids bad indexing)."""
    if not in_bounds(row, col):
        return -1
    return row * BOARD_SIZE + col


def index_to_row_col(index: int) -> Optional[Tuple[int, int]]:
    """0..63 -> (row, col). Returns None if index is out of range."""
    if not isinstance(index, int) or index < 0 or index >= TOTAL_SQUARES:
        return None
    return index // BOARD_SIZE, index % BOARD_SIZE


def square_text(index: int) -> str:
    """0..63 -> algebraic like 'e4'. Returns '??' if index is bad."""
    coords = index_to_row_col(index)
    if coords is None:
        return "??"
    row, col = coords
    return f"{chr(ord('a') + col)}{8 - row}"


def row_col_text(row: int, col: int) -> str:
    """(row, col) -> algebraic like 'e4'. Returns '??' if out of bounds."""
    return square_text(square_index(row, col))


def parse_square(s: str) -> Optional[Tuple[int, int]]:
    """'e4' -> (row, col). Exact two characters only; rejects longer junk."""
    if not s or len(s) != 2 or not s.isascii():
        return None
    file_char = s[0].lower()
    rank_char = s[1]
    if not ("a" <= file_char <= "h") or not ("1" <= rank_char <= "8"):
        return None
    col = ord(file_char) - ord("a")
    row = 8 - int(rank_char)
    if not in_bounds(row, col):
        return None
    return row, col


def home_row_for(side: Color) -> int:
    """Back-rank row for castling / rook home checks."""
    return WHITE_BACK_ROW if side == Color.WHITE else BLACK_BACK_ROW


def rook_col_for(king_side: bool) -> int:
    """Starting rook file for kingside (h) or queenside (a)."""
    return ROOK_KINGSIDE_START_COL if king_side else ROOK_QUEENSIDE_START_COL


def parse_nonneg_int(text: str, max_digits: int = FEN_NUMBER_MAX_DIGITS) -> Optional[int]:
    """Parse a non-negative ASCII integer with a digit-length cap (no huge ints)."""
    if not text or not text.isascii() or not text.isdigit():
        return None
    if len(text) > max_digits:
        return None
    try:
        return int(text, 10)
    except ValueError:
        return None
