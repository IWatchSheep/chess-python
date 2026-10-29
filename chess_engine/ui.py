"""Terminal user interface, chessboard rendering, and comparative move preview."""

import os
from typing import List, Tuple
from .constants import (
    BOARD_SIZE, WHITE, BLACK,
    RESET,
    LIGHT_SQUARE_BG, DARK_SQUARE_BG, LIGHT_TEXT_FG, DARK_TEXT_FG,
    COMPARE_WIDTH,
    in_bounds, color_name, row_col_text,
    CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    ROOK_KINGSIDE_START_COL, ROOK_QUEENSIDE_START_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL,
)
from .move import Move
from .board import Board
from .movegen import generate_moves, legal_destination_map, make_move


def enable_windows_colors() -> None:
    """Turn on ANSI color codes in the Windows console, if possible."""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def selected_destinations(board: Board, row: int, col: int) -> List[List[bool]]:
    """Returns destination map for selected piece, verifying ownership."""
    if not in_bounds(row, col) or board.grid[row][col].color != board.turn:
        return [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    return legal_destination_map(board, row, col, board.turn)


def print_selection_near_prompt(board: Board, row: int, col: int) -> None:
    """Prints available legal moves next to the input prompt."""
    if not in_bounds(row, col):
        return

    destinations = selected_destinations(board, row, col)
    from_sq = row_col_text(row, col)
    dest_list = []
    # List destinations rank 8 -> 1, file a -> h (easy to scan).
    for r in range(BOARD_SIZE - 1, -1, -1):
        for c in range(BOARD_SIZE):
            if destinations[r][c]:
                dest_list.append(row_col_text(r, c))

    if dest_list:
        print(f"Selected {from_sq} -> {' '.join(dest_list)}")
    else:
        print(f"Selected {from_sq} -> (no legal moves)")


def display(board: Board, selected_row: int = -1, selected_col: int = -1) -> None:
    """Renders the 8x8 chessboard to the console with ANSI 256 colors."""
    destinations = selected_destinations(board, selected_row, selected_col)

    print("\n    a   b   c   d   e   f   g   h")
    print("  +---+---+---+---+---+---+---+---+")

    for row in range(BOARD_SIZE):
        line_parts = [f"{8 - row} |"]
        for col in range(BOARD_SIZE):
            piece = board.grid[row][col]
            light_square = ((row + col) % 2 == 0)

            background = LIGHT_SQUARE_BG if light_square else DARK_SQUARE_BG
            foreground = DARK_TEXT_FG if light_square else LIGHT_TEXT_FG

            symbol = piece.symbol
            left = ' '
            right = ' '

            if row == selected_row and col == selected_col:
                left = '['
                right = ']'
            elif destinations[row][col]:
                if piece.is_empty:
                    symbol = '*'
                else:
                    left = '('
                    right = ')'

            line_parts.append(f"{background}{foreground}{left}{symbol}{right}{RESET}|")

        line_parts.append(f" {8 - row}")
        print("".join(line_parts))
        print("  +---+---+---+---+---+---+---+---+")

    print("    a   b   c   d   e   f   g   h\n")

    if in_bounds(selected_row, selected_col):
        piece = board.grid[selected_row][selected_col]
        dest_sqs = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if destinations[r][c]:
                    dest_sqs.append(row_col_text(r, c))

        at = row_col_text(selected_row, selected_col)
        print(f"SELECTED: {color_name(piece.color)} {piece.type} at {at}")
        if dest_sqs:
            print(f"LEGAL DESTINATIONS: {' '.join(dest_sqs)}")
        else:
            print("LEGAL DESTINATIONS: (none)")
        print(f"TOTAL: {len(dest_sqs)} square(s)")
        print("LEGEND: [P]=selected piece, *=empty legal destination, (p)=legal capture")
        print("Selection is informational: no piece has moved.\n")


def list_piece_moves(position: Board, row: int, col: int) -> str:
    """Returns the legal destinations for a piece as a space-separated string."""
    piece = position.grid[row][col]
    if piece.is_empty:
        return ""

    view = position.clone()
    view.turn = piece.color
    moves = generate_moves(view)

    seen = set()
    result = []
    for m in moves:
        if m.sr == row and m.sc == col and (m.er, m.ec) not in seen:
            seen.add((m.er, m.ec))
            result.append(row_col_text(m.er, m.ec))

    return " ".join(result) if result else "(none)"


def next_chunk(source: str, at: int, width: int = COMPARE_WIDTH) -> Tuple[str, int]:
    """Extracts the next word-wrapped chunk of text up to width characters."""
    length = len(source)
    while at < length and source[at] == ' ':
        at += 1

    if at >= length:
        return "", at

    words = []
    curr_len = 0
    curr_at = at

    while curr_at < length:
        # Find next space
        space_idx = source.find(' ', curr_at)
        word = source[curr_at:] if space_idx == -1 else source[curr_at:space_idx]
        word_len = len(word)
        sep_len = 1 if words else 0

        if curr_len + sep_len + word_len > width:
            if not words:
                # Word itself exceeds width, take substring
                chunk = word[:width]
                return chunk, curr_at + width
            break

        words.append(word)
        curr_len += sep_len + word_len
        curr_at += word_len
        while curr_at < length and source[curr_at] == ' ':
            curr_at += 1

    return " ".join(words), curr_at


def print_side_by_side(before: str, after: str, width: int = COMPARE_WIDTH) -> None:
    """Prints two strings side-by-side in aligned columns."""
    left_offset = 0
    right_offset = 0
    before_len = len(before)
    after_len = len(after)

    while left_offset < before_len or right_offset < after_len:
        left_chunk, left_offset = next_chunk(before, left_offset, width)
        right_chunk, right_offset = next_chunk(after, right_offset, width)
        print(f"{left_chunk:<{width}} | {right_chunk}")


def is_en_passant_capture(before: Board, proposed: Move, row: int, col: int) -> bool:
    """Checks if the piece on (row, col) is captured by en passant during proposed move."""
    if not in_bounds(proposed.sr, proposed.sc):
        return False
    moving_piece = before.grid[proposed.sr][proposed.sc]
    return (
        moving_piece.type == "P"
        and proposed.er == before.ep_row
        and proposed.ec == before.ep_col
        and row == proposed.sr
        and col == proposed.ec
    )


def resolve_piece_after_move(
    before: Board, proposed: Move, row: int, col: int
) -> Tuple[int, int, bool]:
    """Where the piece on (row, col) ends up after `proposed`, plus captured flag.

    Returns (after_row, after_col, captured). Captured pieces keep their old
    square coords; callers should ignore destination maps for them.
    """
    if not in_bounds(row, col):
        return row, col, False
    if not (in_bounds(proposed.sr, proposed.sc) and in_bounds(proposed.er, proposed.ec)):
        return row, col, False

    after_row = row
    after_col = col
    captured = False

    if row == proposed.er and col == proposed.ec:
        captured = True

    if is_en_passant_capture(before, proposed, row, col):
        captured = True

    moving_piece = before.grid[proposed.sr][proposed.sc]
    is_castling = (
        moving_piece.type == "K"
        and abs(proposed.ec - proposed.sc) == 2
        and row == proposed.sr
    )
    if is_castling:
        if proposed.ec == CASTLE_KINGSIDE_KING_DEST_COL and col == ROOK_KINGSIDE_START_COL:
            after_col = CASTLE_KINGSIDE_ROOK_DEST_COL
        if proposed.ec == CASTLE_QUEENSIDE_KING_DEST_COL and col == ROOK_QUEENSIDE_START_COL:
            after_col = CASTLE_QUEENSIDE_ROOK_DEST_COL

    return after_row, after_col, captured


def print_piece_changes(
    before: Board, after: Board,
    before_row: int, before_col: int,
    after_row: int, after_col: int,
    captured: bool
) -> None:
    """Compares destinations before and after move, reporting GAINED, LOST, UNCHANGED."""
    if captured:
        print("    CHANGE: CAPTURED - this piece has no AFTER moves.")
        return

    side = before.grid[before_row][before_col].color
    old_dest = legal_destination_map(before, before_row, before_col, side)
    new_dest = legal_destination_map(after, after_row, after_col, side)

    gained = []
    lost = []
    unchanged = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            in_new = new_dest[r][c]
            in_old = old_dest[r][c]
            sq = row_col_text(r, c)
            if in_new and not in_old:
                gained.append(sq)
            elif in_old and not in_new:
                lost.append(sq)
            elif in_old and in_new:
                unchanged.append(sq)

    if not gained and not lost:
        print("    CHANGE: UNCHANGED - no destinations gained or lost.")
    else:
        print("    CHANGE: destinations changed.")

    print(f"    GAINED: {' '.join(gained) if gained else '(none)'}")
    print(f"    LOST: {' '.join(lost) if lost else '(none)'}")
    print(f"    UNCHANGED: {' '.join(unchanged) if unchanged else '(none)'}")


def compare_all_other_pieces(before: Board, after: Board, proposed: Move) -> None:
    """Generates the complete side-by-side comparative report for every other piece."""
    for side in (WHITE, BLACK):
        side_name = "WHITE" if side == WHITE else "BLACK"
        print("")
        print(f"{side_name} PIECES (excluding selected piece)")
        print_side_by_side(
            "BEFORE: square piece -> legal destinations",
            "AFTER: square piece -> legal destinations"
        )
        print("-" * COMPARE_WIDTH + "+" + "-" * COMPARE_WIDTH)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = before.grid[row][col]
                if piece.color != side or (row == proposed.sr and col == proposed.sc):
                    continue

                after_row, after_col, captured = resolve_piece_after_move(before, proposed, row, col)

                before_moves = list_piece_moves(before, row, col)
                before_desc = f"{row_col_text(row, col)} {piece.symbol}: {before_moves}"

                if captured:
                    after_desc = f"(captured at {row_col_text(row, col)})"
                else:
                    after_piece = after.grid[after_row][after_col]
                    after_moves = list_piece_moves(after, after_row, after_col)
                    after_desc = (
                        f"{row_col_text(after_row, after_col)} "
                        f"{after_piece.symbol}: {after_moves}"
                    )

                print_side_by_side(before_desc, after_desc)
                print_piece_changes(before, after, row, col, after_row, after_col, captured)


def show_step2_after(board: Board, proposed: Move) -> None:
    """Preview a move: print BEFORE/AFTER for every other piece. Board is not changed."""
    simulated = board.clone()
    start = row_col_text(proposed.sr, proposed.sc)
    end = row_col_text(proposed.er, proposed.ec)
    print(f"\nPREVIEW ONLY: {start} -> {end} (NOT PLAYED)")
    make_move(simulated, proposed)

    print("Widen your console to about 140 columns for the two-column report.")
    print("CHANGE shows gained, lost, and unchanged destinations for each other piece.")
    print("LEGAL MOVE LIST NOTE: Each side is evaluated as if it were that side's turn.")
    print("Black and White possibilities are shown for comparison; only the actual")
    print("side to move can play immediately. Check restrictions still apply.")

    compare_all_other_pieces(board, simulated, proposed)

    print("\nThe real board and player turn have NOT changed.")
    print("Press F then Enter to FINALIZE this previewed move.")
    print("Press P then Enter to preview another destination, or N for a new piece.")
