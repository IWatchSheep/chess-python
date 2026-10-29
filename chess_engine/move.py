"""Move representation, parsing, serialization, and deterministic sorting."""

from dataclasses import dataclass
from typing import Optional
from .constants import parse_square


def promotion_rank(promotion: str) -> int:
    """Helper for ordering moves: maps promotion piece to sort rank."""
    if promotion == 'Q':
        return 1
    elif promotion == 'R':
        return 2
    elif promotion == 'B':
        return 3
    elif promotion == 'N':
        return 4
    return 0


@dataclass(frozen=True, slots=True)
class Move:
    sr: int
    sc: int
    er: int
    ec: int
    promotion: str = '\0'  # 'Q', 'R', 'B', 'N' or '\0'

    @property
    def is_kingside_castle(self) -> bool:
        return self.ec > self.sc

    @property
    def uci(self) -> str:
        """Returns standard algebraic notation e.g. 'e2e4' or 'e7e8q'."""
        promo = self.promotion.lower() if self.promotion and self.promotion != '\0' else ""
        from_sq = f"{chr(ord('a') + self.sc)}{8 - self.sr}"
        to_sq = f"{chr(ord('a') + self.ec)}{8 - self.er}"
        return f"{from_sq}{to_sq}{promo}"

    def sort_key(self) -> tuple:
        """Canonical sort key matching C compare_moves:
        (sr, sc, er, ec, promotion_rank)
        """
        return (self.sr, self.sc, self.er, self.ec, promotion_rank(self.promotion))

    def __lt__(self, other: 'Move') -> bool:
        return self.sort_key() < other.sort_key()


def parse_move_text(text: str) -> Optional[Move]:
    """Parses move text like 'e2e4' or 'e7e8q' into a Move object."""
    if not text:
        return None
    length = len(text)
    if length not in (4, 5):
        return None

    start = parse_square(text[:2])
    end = parse_square(text[2:4])
    if not start or not end:
        return None

    sr, sc = start
    er, ec = end
    promo = '\0'
    if length == 5:
        p = text[4].upper()
        if p not in ("Q", "R", "B", "N"):
            return None
        promo = p

    return Move(sr=sr, sc=sc, er=er, ec=ec, promotion=promo)
