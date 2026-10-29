"""One chess piece (or an empty square).

Pieces are frozen (immutable). To "change" a square, put a new Piece there.
"""

from dataclasses import dataclass

from .constants import Color, EMPTY, WHITE, BLACK, PIECE_VALUES


@dataclass(frozen=True, slots=True)
class Piece:
    type: str   # 'P','N','B','R','Q','K' or '\0' for empty
    color: Color

    @property
    def is_empty(self) -> bool:
        return self.color == EMPTY or self.type == "\0"

    @property
    def symbol(self) -> str:
        """Board display: 'P' white, 'p' black, ' ' empty."""
        if self.is_empty:
            return " "
        if self.color == WHITE:
            return self.type
        return self.type.lower()

    @property
    def key_char(self) -> str:
        """Character used inside repetition keys (C port style)."""
        if self.is_empty:
            return "."
        # White = lowercase, Black = uppercase (matches original C hash).
        if self.color == WHITE:
            return self.type.lower()
        return self.type.upper()

    @property
    def value(self) -> int:
        return PIECE_VALUES.get(self.type, 0)


def empty_piece() -> Piece:
    """A blank square."""
    return Piece(type="\0", color=EMPTY)
