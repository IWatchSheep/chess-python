"""Piece representations and helper methods."""

from dataclasses import dataclass
from .constants import Color, EMPTY, WHITE, BLACK, PIECE_VALUES


@dataclass(frozen=True, slots=True)
class Piece:
    type: str  # 'P', 'N', 'B', 'R', 'Q', 'K' or '\0'
    color: Color

    @property
    def is_empty(self) -> bool:
        return self.color == EMPTY or self.type == '\0'

    @property
    def symbol(self) -> str:
        """Returns the display character: uppercase for White, lowercase for Black, space for Empty."""
        if self.is_empty:
            return ' '
        if self.color == WHITE:
            return self.type
        return self.type.lower()

    @property
    def key_char(self) -> str:
        """Character used in position hash keys (following C implementation):
        Empty = '.', White = lowercase, Black = uppercase.
        """
        if self.is_empty:
            return '.'
        if self.color == WHITE:
            return self.type.lower()
        return self.type.upper()

    @property
    def value(self) -> int:
        return PIECE_VALUES.get(self.type, 0)


def empty_piece() -> Piece:
    """Returns an empty piece."""
    return Piece(type='\0', color=EMPTY)
