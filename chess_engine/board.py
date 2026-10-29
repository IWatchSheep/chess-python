"""Board state: pieces, turn, castling, en passant, draws, FEN.

Think of Board as the whole game position — not just the 8x8 grid.

history: list of position keys for threefold / fivefold claims.
  Cleared on pawn moves and captures (those cannot repeat a prior key path).
  Capped at HISTORY_MAX_LEN so it cannot grow without bound.
"""

from typing import List, Optional, Tuple

from .constants import (
    BOARD_SIZE, Color, EMPTY, WHITE, BLACK,
    HISTORY_MAX_LEN, FEN_NUMBER_MAX_DIGITS,
    in_bounds, opposite, parse_square, parse_nonneg_int,
)
from .piece import Piece, empty_piece


class Board:
    """Represents the complete, self-contained state of a chess game."""

    def __init__(self):
        # 8x8 grid of Piece objects
        self.grid: List[List[Piece]] = [
            [empty_piece() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]
        self.turn: Color = WHITE

        # Castling rights tracking
        self.white_king_moved: bool = False
        self.black_king_moved: bool = False
        self.white_rook_a_moved: bool = False  # Queenside
        self.white_rook_h_moved: bool = False  # Kingside
        self.black_rook_a_moved: bool = False  # Queenside
        self.black_rook_h_moved: bool = False  # Kingside

        # En passant target square (-1 if none)
        self.ep_row: int = -1
        self.ep_col: int = -1

        # Halfmove clock (50-move rule counter) and fullmove number
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

        # Repetition history: list of position key strings
        self.history: List[str] = []

    def clone(self) -> 'Board':
        """Creates a deep copy of the board."""
        new_b = Board()
        new_b.grid = [[self.grid[r][c] for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]
        new_b.turn = self.turn
        new_b.white_king_moved = self.white_king_moved
        new_b.black_king_moved = self.black_king_moved
        new_b.white_rook_a_moved = self.white_rook_a_moved
        new_b.white_rook_h_moved = self.white_rook_h_moved
        new_b.black_rook_a_moved = self.black_rook_a_moved
        new_b.black_rook_h_moved = self.black_rook_h_moved
        new_b.ep_row = self.ep_row
        new_b.ep_col = self.ep_col
        new_b.halfmove_clock = self.halfmove_clock
        new_b.fullmove_number = self.fullmove_number
        new_b.history = list(self.history)
        return new_b

    def reset_board(self) -> None:
        """Resets the board to the standard starting chess position."""
        back_row = "RNBQKBNR"
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                self.grid[r][c] = empty_piece()

        for c in range(BOARD_SIZE):
            self.grid[0][c] = Piece(type=back_row[c], color=BLACK)
            self.grid[1][c] = Piece(type='P', color=BLACK)
            self.grid[6][c] = Piece(type='P', color=WHITE)
            self.grid[7][c] = Piece(type=back_row[c], color=WHITE)

        self.turn = WHITE
        self.white_king_moved = False
        self.black_king_moved = False
        self.white_rook_a_moved = False
        self.white_rook_h_moved = False
        self.black_rook_a_moved = False
        self.black_rook_h_moved = False
        self.ep_row = -1
        self.ep_col = -1
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.history = []
        self.record_position()

    def record_position(self) -> None:
        """Remember this position for repetition draws (oldest dropped if full)."""
        self.history.append(self.position_key())
        # Cap length so a long quiet game cannot grow memory without bound.
        if len(self.history) > HISTORY_MAX_LEN:
            overflow = len(self.history) - HISTORY_MAX_LEN
            del self.history[:overflow]

    def position_key(self) -> str:
        """Computes a standardized 72-character key representing the position."""
        # Avoid circular import by importing legal_move locally
        from .movegen import legal_move
        from .move import Move

        chars = []
        # 1. 64 characters for piece positions
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                chars.append(self.grid[r][c].key_char)

        # 2. Side to move
        chars.append('W' if self.turn == WHITE else 'B')

        # 3. Castling rights: White Q, White K, Black Q, Black K
        chars.append('1' if (not self.white_king_moved and not self.white_rook_a_moved) else '0')
        chars.append('1' if (not self.white_king_moved and not self.white_rook_h_moved) else '0')
        chars.append('1' if (not self.black_king_moved and not self.black_rook_a_moved) else '0')
        chars.append('1' if (not self.black_king_moved and not self.black_rook_h_moved) else '0')

        # 4. En passant: only included if an en passant capture is legally possible
        legal_ep = False
        if in_bounds(self.ep_row, self.ep_col):
            dir_step = 1 if self.turn == WHITE else -1
            starting_row = self.ep_row + dir_step
            for delta_col in (-1, 1):
                sc = self.ep_col + delta_col
                if in_bounds(starting_row, sc):
                    candidate = Move(sr=starting_row, sc=sc, er=self.ep_row, ec=self.ep_col)
                    if legal_move(self, candidate):
                        legal_ep = True
                        break

        if legal_ep:
            chars.append(str(self.ep_row))
            chars.append(str(self.ep_col))
        else:
            chars.append('-')

        return "".join(chars)

    def repetition_count(self, key: Optional[str] = None) -> int:
        """Counts how many times key (or current position) appears in history."""
        target_key = key if key is not None else self.position_key()
        return self.history.count(target_key)

    def dead_position(self) -> bool:
        """Checks for insufficient material to deliver checkmate under FIDE rules."""
        minors = 0
        bishops = 0
        bishop_color = -1
        bishops_same_color = True

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.grid[r][c]
                if p.is_empty or p.type == 'K':
                    continue
                # If there are pawns, rooks, or queens, mate is possible
                if p.type not in ('B', 'N'):
                    return False
                minors += 1
                if p.type == 'B':
                    bishops += 1
                    sq_color = (r + c) % 2
                    if bishop_color == -1:
                        bishop_color = sq_color
                    elif bishop_color != sq_color:
                        bishops_same_color = False

        # King vs King, or King + Minor vs King
        if minors <= 1:
            return True

        # Only bishops present, and all bishops travel on the same square color
        if bishops == minors and bishops_same_color:
            return True

        return False

    def automatic_draw(self) -> Tuple[bool, Optional[str]]:
        """Checks mandatory draw conditions: 75-move rule, 5-fold repetition, dead position."""
        if self.halfmove_clock >= 150:
            return True, "75-move rule"
        if self.repetition_count() >= 5:
            return True, "fivefold repetition"
        if self.dead_position():
            return True, "dead position"
        return False, None

    def claimable_draw(self, intended_move: Optional['Move'] = None) -> Tuple[bool, Optional[str]]:
        """Checks whether a player can claim a draw (50-move rule or 3-fold repetition)."""
        from .movegen import legal_move, make_move
        from .move import Move

        pos = self
        has_intended = (intended_move is not None and intended_move.sr >= 0)
        if has_intended:
            if not legal_move(self, intended_move):
                return False, None
            after_move = self.clone()
            make_move(after_move, intended_move)
            pos = after_move

        if pos.halfmove_clock >= 100:
            return True, "50-move rule"

        needed = 2 if has_intended else 3
        if pos.repetition_count() >= needed:
            return True, "threefold repetition"

        return False, None

    def to_fen(self) -> str:
        """Serializes current board state into FEN notation."""
        parts = []
        # 1. Piece placement
        placement = []
        for r in range(BOARD_SIZE):
            empty_count = 0
            row_chars = []
            for c in range(BOARD_SIZE):
                p = self.grid[r][c]
                if p.is_empty:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_chars.append(str(empty_count))
                        empty_count = 0
                    row_chars.append(p.symbol)
            if empty_count > 0:
                row_chars.append(str(empty_count))
            placement.append("".join(row_chars))
        parts.append("/".join(placement))

        # 2. Side to move
        parts.append("w" if self.turn == WHITE else "b")

        # 3. Castling rights
        castling = []
        if not self.white_king_moved and not self.white_rook_h_moved:
            castling.append("K")
        if not self.white_king_moved and not self.white_rook_a_moved:
            castling.append("Q")
        if not self.black_king_moved and not self.black_rook_h_moved:
            castling.append("k")
        if not self.black_king_moved and not self.black_rook_a_moved:
            castling.append("q")
        parts.append("".join(castling) if castling else "-")

        # 4. En passant target square
        if in_bounds(self.ep_row, self.ep_col):
            parts.append(f"{chr(ord('a') + self.ep_col)}{8 - self.ep_row}")
        else:
            parts.append("-")

        # 5. Halfmove clock
        parts.append(str(self.halfmove_clock))

        # 6. Fullmove number
        parts.append(str(self.fullmove_number))

        return " ".join(parts)

    def load_fen(self, fen: str) -> Tuple[bool, Optional[str]]:
        """Parses, validates, and loads a chess position from a FEN string."""
        from .movegen import find_king, is_in_check, count_attackers

        if not fen:
            return False, "FEN text is missing"

        fields = fen.strip().split()
        if len(fields) not in (4, 6):
            return False, "a FEN has 6 fields (or 4) separated by single spaces"

        new_b = Board()

        # Field 1: Piece placement
        ranks = fields[0].split('/')
        if len(ranks) != 8:
            return False, "the board must have exactly 8 ranks of 8 squares"

        for r, rank_str in enumerate(ranks):
            col = 0
            for ch in rank_str:
                if ch.isdigit():
                    digit = int(ch)
                    if digit < 1 or digit > 8:
                        return False, "a rank does not have exactly 8 squares"
                    col += digit
                    if col > 8:
                        return False, "a rank does not have exactly 8 squares"
                else:
                    upper = ch.upper()
                    if upper not in "PNBRQK":
                        return False, "unknown piece letter"
                    if col >= 8:
                        return False, "a rank does not have exactly 8 squares"
                    piece_color = WHITE if ch.isupper() else BLACK
                    new_b.grid[r][col] = Piece(type=upper, color=piece_color)
                    col += 1
            if col != 8:
                return False, "a rank does not have exactly 8 squares"

        # Field 2: Side to move
        if fields[1] not in ("w", "b"):
            return False, "side to move must be w or b"
        new_b.turn = WHITE if fields[1] == "w" else BLACK

        # Validate piece material counts
        for side in (WHITE, BLACK):
            counts = {p: 0 for p in "PNBRQK"}
            total = 0
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    p = new_b.grid[r][c]
                    if p.color == side:
                        counts[p.type] += 1
                        total += 1
                        if p.type == 'P' and (r == 0 or r == 7):
                            return False, "a pawn is on the first or last rank"

            if counts['K'] != 1:
                return False, "White must have exactly one king" if side == WHITE else "Black must have exactly one king"

            promoted = (
                max(0, counts['Q'] - 1) +
                max(0, counts['R'] - 2) +
                max(0, counts['B'] - 2) +
                max(0, counts['N'] - 2)
            )
            if counts['P'] > 8 or total > 16 or promoted > (8 - counts['P']):
                return False, "White has more pieces than a game allows" if side == WHITE else "Black has more pieces than a game allows"

        # Field 3: Castling rights
        castling_field = fields[2]
        wk = wq = bk = bq = False
        if castling_field != "-":
            order = "KQkq"
            curr_idx = 0
            for ch in castling_field:
                pos = order.find(ch, curr_idx)
                if pos == -1:
                    return False, "castling field must be - or letters from KQkq in that order"
                curr_idx = pos + 1
                if ch == 'K': wk = True
                elif ch == 'Q': wq = True
                elif ch == 'k': bk = True
                elif ch == 'q': bq = True

        def piece_at(r, c, t, colr):
            return new_b.grid[r][c].type == t and new_b.grid[r][c].color == colr

        if (wk or wq) and not piece_at(7, 4, 'K', WHITE):
            return False, "White castling right without the king on e1"
        if (bk or bq) and not piece_at(0, 4, 'K', BLACK):
            return False, "Black castling right without the king on e8"
        if (wk and not piece_at(7, 7, 'R', WHITE)) or (wq and not piece_at(7, 0, 'R', WHITE)) or \
           (bk and not piece_at(0, 7, 'R', BLACK)) or (bq and not piece_at(0, 0, 'R', BLACK)):
            return False, "castling right without the rook on its starting square"

        new_b.white_king_moved = not (wk or wq)
        new_b.black_king_moved = not (bk or bq)
        new_b.white_rook_h_moved = not wk
        new_b.white_rook_a_moved = not wq
        new_b.black_rook_h_moved = not bk
        new_b.black_rook_a_moved = not bq

        # Field 4: En passant
        ep_field = fields[3]
        if ep_field != "-":
            parsed = parse_square(ep_field)
            if not parsed or len(ep_field) != 2:
                return False, "en passant field must be - or a square"
            r, c = parsed
            expected_row = 2 if new_b.turn == WHITE else 5
            pawn_row = 3 if new_b.turn == WHITE else 4
            start_row = 1 if new_b.turn == WHITE else 6
            mover = opposite(new_b.turn)
            if r != expected_row:
                return False, "en passant square is on the wrong rank for the side to move"
            if not piece_at(pawn_row, c, 'P', mover) or \
               new_b.grid[r][c].color != EMPTY or \
               new_b.grid[start_row][c].color != EMPTY:
                return False, "en passant square does not match a pawn that just moved two squares"
            new_b.ep_row = r
            new_b.ep_col = c
        else:
            new_b.ep_row = -1
            new_b.ep_col = -1

        # Fields 5 & 6 (digit-length capped — avoids huge-int DoS from bad FEN)
        if len(fields) == 6:
            halfmove = parse_nonneg_int(fields[4], FEN_NUMBER_MAX_DIGITS)
            fullmove = parse_nonneg_int(fields[5], FEN_NUMBER_MAX_DIGITS)
            if halfmove is None or fullmove is None or fullmove < 1:
                return False, (
                    "halfmove clock and move number must be whole numbers "
                    "(move number at least 1)"
                )
            new_b.halfmove_clock = halfmove
            new_b.fullmove_number = fullmove

        # Verify king presence and legality
        if is_in_check(new_b, opposite(new_b.turn)):
            return False, "the side that is not to move is in check"

        king_pos = find_king(new_b, new_b.turn)
        if not king_pos:
            return False, "the side to move has no king"

        if count_attackers(new_b, king_pos[0], king_pos[1], opposite(new_b.turn)) > 2:
            return False, "the king to move is attacked by more than two pieces"

        # Transfer loaded state to self
        self.grid = new_b.grid
        self.turn = new_b.turn
        self.white_king_moved = new_b.white_king_moved
        self.black_king_moved = new_b.black_king_moved
        self.white_rook_a_moved = new_b.white_rook_a_moved
        self.white_rook_h_moved = new_b.white_rook_h_moved
        self.black_rook_a_moved = new_b.black_rook_a_moved
        self.black_rook_h_moved = new_b.black_rook_h_moved
        self.ep_row = new_b.ep_row
        self.ep_col = new_b.ep_col
        self.halfmove_clock = new_b.halfmove_clock
        self.fullmove_number = new_b.fullmove_number
        self.history = []
        self.record_position()
        return True, None
