"""Five-move memory: up to 4 finished moves + the move being previewed.

This is NOT Board.history (that list is only for threefold / fivefold draws).
A pawn move or capture clears Board.history, so it cannot be this window.

How to read a memory entry:
  BEFORE / AFTER  — FEN strings (no live Board objects kept)
  GAINED / LOST   — destination squares other pieces gained or lost
  UNCHANGED COUNT — how many other-piece destinations stayed the same
  BOARD SQUARES CHANGED — squares whose piece type/color changed
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .board import Board
from .constants import BOARD_SIZE, WHITE, BLACK, color_name, row_col_text
from .move import Move
from .movegen import make_move, legal_destination_map
from .ui import resolve_piece_after_move

MAX_PAST_MOVES = 4


def _squares_or_none(squares: Sequence[str]) -> str:
    return " ".join(squares) if squares else "(none)"


def _piece_changed_squares(before: Board, after: Board) -> Tuple[str, ...]:
    """List squares where the piece (type or color) differs."""
    out: List[str] = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            a = before.grid[row][col]
            b = after.grid[row][col]
            if a.type != b.type or a.color != b.color:
                out.append(row_col_text(row, col))
    return tuple(out)


def _other_piece_destination_changes(
    before: Board, after: Board, move: Move
) -> Tuple[Tuple[str, ...], Tuple[str, ...], int]:
    """Same gained/lost/unchanged rules as the Step-2 preview for every other piece."""
    gained: List[str] = []
    lost: List[str] = []
    seen_gained = set()
    seen_lost = set()
    unchanged = 0

    for side in (WHITE, BLACK):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = before.grid[row][col]
                # Skip empty, wrong color, and the piece that is moving.
                if piece.color != side:
                    continue
                if row == move.sr and col == move.sc:
                    continue

                after_row, after_col, captured = resolve_piece_after_move(
                    before, move, row, col
                )
                if captured:
                    continue

                old_map = legal_destination_map(before, row, col, side)
                new_map = legal_destination_map(after, after_row, after_col, side)

                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        was = old_map[r][c]
                        now = new_map[r][c]
                        name = row_col_text(r, c)
                        if now and not was:
                            if name not in seen_gained:
                                seen_gained.add(name)
                                gained.append(name)
                        elif was and not now:
                            if name not in seen_lost:
                                seen_lost.add(name)
                                lost.append(name)
                        elif was and now:
                            unchanged += 1

    return tuple(gained), tuple(lost), unchanged


def _board_from_fen(fen: str) -> Optional[Board]:
    board = Board()
    ok, _ = board.load_fen(fen)
    return board if ok else None


@dataclass(frozen=True, slots=True)
class MoveMemoryEntry:
    """One remembered move (either a past move or the current preview)."""

    move_uci: str
    side_name: str
    fen_before: str
    fen_after: str
    gained: Tuple[str, ...]
    lost: Tuple[str, ...]
    unchanged_count: int
    board_squares_changed: Tuple[str, ...]


def build_entry(board: Board, move: Move) -> MoveMemoryEntry:
    """Clone the board, play the move on the copy, collect facts. Live board unchanged."""
    fen_before = board.to_fen()
    after = board.clone()
    make_move(after, move)
    fen_after = after.to_fen()

    gained, lost, unchanged = _other_piece_destination_changes(board, after, move)
    changed = _piece_changed_squares(board, after)

    return MoveMemoryEntry(
        move_uci=move.uci,
        side_name=color_name(board.turn),
        fen_before=fen_before,
        fen_after=fen_after,
        gained=gained,
        lost=lost,
        unchanged_count=unchanged,
        board_squares_changed=changed,
    )


def _entry_lines(entry: MoveMemoryEntry) -> List[str]:
    return [
        f"  BEFORE: {entry.fen_before}",
        f"  AFTER: {entry.fen_after}",
        f"  GAINED: {_squares_or_none(entry.gained)}",
        f"  LOST: {_squares_or_none(entry.lost)}",
        f"  UNCHANGED COUNT: {entry.unchanged_count}",
        f"  BOARD SQUARES CHANGED: {_squares_or_none(entry.board_squares_changed)}",
    ]


class MoveMemory:
    """At most 4 past moves (oldest first) plus an optional current preview."""

    def __init__(self) -> None:
        self.past: List[MoveMemoryEntry] = []
        self.current: Optional[MoveMemoryEntry] = None

    def clear(self) -> None:
        self.past.clear()
        self.current = None

    def clear_current(self) -> None:
        self.current = None

    def set_current(self, board: Board, move: Move) -> None:
        self.current = build_entry(board, move)

    def record_finalized(self) -> None:
        """On F: store the preview as a past move; drop the oldest if we exceed 4."""
        if self.current is None:
            return
        self.past.append(self.current)
        self.current = None
        while len(self.past) > MAX_PAST_MOVES:
            self.past.pop(0)

    def print_report(self) -> None:
        lines = ["MEMORY BEGIN"]

        for i, entry in enumerate(self.past, start=1):
            lines.append(f"PAST {i} {entry.move_uci} {entry.side_name}")
            lines.extend(_entry_lines(entry))

        if self.current is not None:
            lines.append(f"CURRENT {self.current.move_uci} {self.current.side_name}")
            lines.extend(_entry_lines(self.current))
            lines.append(f"WINDOW: {len(self.past)} PAST + CURRENT")
            span = "FROM OLDEST BEFORE TO CURRENT AFTER"
        else:
            lines.append("CURRENT: none (preview a destination first).")
            lines.append(f"WINDOW: {len(self.past)} PAST")
            span = "FROM OLDEST BEFORE TO LATEST AFTER"

        lines.append(f"{span}: {_squares_or_none(self._window_squares())}")
        lines.append("MEMORY END")
        print("\n".join(lines))

    def _window_squares(self) -> Tuple[str, ...]:
        """Squares that differ from the oldest before-FEN to the latest after-FEN."""
        oldest_before: Optional[str] = None
        latest_after: Optional[str] = None

        if self.past:
            oldest_before = self.past[0].fen_before
            latest_after = self.past[-1].fen_after
        if self.current is not None:
            if oldest_before is None:
                oldest_before = self.current.fen_before
            latest_after = self.current.fen_after

        if oldest_before is None or latest_after is None:
            return ()

        before = _board_from_fen(oldest_before)
        after = _board_from_fen(latest_after)
        if before is None or after is None:
            return ()
        return _piece_changed_squares(before, after)
