"""Stage 3E and 3F: capture exchanges, move ordering and move comparison."""

from typing import Dict, List, Optional, Tuple
from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES, Color, WHITE, BLACK,
    color_name, square_index, square_text, in_bounds,
)
from ..move import Move
from ..board import Board
from ..movegen import sorted_moves, make_move, is_in_check
from ..tracker import Tracker
from .common import (
    Goal, MaterialResult, move_distance, order_label, piece_value,
)
from .calc import calc_report
from .replies import replies_report
from .search import loop_report


# ----------------------------------------------------------------------------
# Capture helpers and exchange search (Stage 3E)
# ----------------------------------------------------------------------------

def captured_type(board: Board, m: Move) -> str:
    """Returns captured piece type ('P', 'N', etc.) or empty string."""
    if not in_bounds(m.sr, m.sc) or not in_bounds(m.er, m.ec):
        return ""
    target = board.grid[m.er][m.ec]
    mover = board.grid[m.sr][m.sc]
    if not target.is_empty and target.color != mover.color:
        return target.type
    # En passant: diagonal pawn move onto an empty square.
    if mover.type == "P" and m.sc != m.ec and target.is_empty:
        return "P"
    return ""


def captures_on(board: Board, sq: int) -> List[Move]:
    """All legal captures landing on sq for side to move."""
    if not isinstance(sq, int) or sq < 0 or sq >= TOTAL_SQUARES:
        return []
    all_moves = sorted_moves(board)
    return [m for m in all_moves if (m.er * BOARD_SIZE + m.ec == sq) and captured_type(board, m)]


def _loop_match_uci(board: Board, m: Move) -> str:
    """UCI key used in LOOP FIRST lines (pawn promotions always include a letter)."""
    if m.promotion and m.promotion != "\0":
        return m.uci
    if in_bounds(m.sr, m.sc) and in_bounds(m.er, m.ec):
        piece = board.grid[m.sr][m.sc]
        if piece.type == "P" and m.er in (0, 7):
            return Move(m.sr, m.sc, m.er, m.ec, promotion="Q").uci
    return m.uci


def exchange_value(
    board: Board, mover: Color, sq: int, m: int, left: int
) -> Tuple[bool, bool, bool]:
    """Minimax exchange value evaluation: returns (forced, possible, bounded)."""
    bounded = False
    caps = captures_on(board, sq) if left > 0 else []
    if left == 0 and len(captures_on(board, sq)) > 0:
        bounded = True

    stop_ok = (m >= 0)
    any_forced = False
    all_forced = True
    any_possible = stop_ok

    for c in caps:
        next_b = board.clone()
        v = piece_value(captured_type(board, c))
        child = (m + v) if board.turn == mover else (m - v)
        make_move(next_b, c)
        f, p, bnd = exchange_value(next_b, mover, sq, child, left - 1)
        if bnd:
            bounded = True
        any_forced = any_forced or f
        all_forced = all_forced and f
        any_possible = any_possible or p

    if board.turn == mover:
        forced = stop_ok or any_forced
    else:
        forced = stop_ok and all_forced

    return forced, any_possible, bounded


def first_capture_class(
    board: Board, c: Move, limit: int
) -> Tuple[MaterialResult, bool]:
    next_b = board.clone()
    v = piece_value(captured_type(board, c))
    make_move(next_b, c)
    sq = square_index(c.er, c.ec)
    forced, possible, bounded = exchange_value(next_b, board.turn, sq, v, limit - 1)
    if forced:
        return MaterialResult.MATERIAL_FORCED, bounded
    elif possible:
        return MaterialResult.MATERIAL_POSSIBLE, bounded
    return MaterialResult.MATERIAL_ELSE, bounded


def material_text(r: MaterialResult) -> str:
    if r == MaterialResult.MATERIAL_FORCED:
        return "MATERIAL FORCED NONNEGATIVE"
    elif r == MaterialResult.MATERIAL_POSSIBLE:
        return "MATERIAL POSSIBLE NONNEGATIVE"
    return "MATERIAL ELSE"


def exchange_report(board: Board, sq: int, limit: int) -> str:
    """Generates Stage 3E exchange report for square sq."""
    lines: List[str] = [
        f"EXCHANGE BEGIN {color_name(board.turn)} {square_text(sq)} LIMIT {limit}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good"
    ]
    first_caps = captures_on(board, sq)
    if not first_caps:
        lines.append("NO CAPTURES")
        lines.append("EXCHANGE END\n")
        return "\n".join(lines)

    sequences_count = 0
    was_cut = False

    def exchange_walk(b: Board, path: List[Move], taken: List[str], by: List[Color], length: int) -> None:
        nonlocal sequences_count, was_cut
        caps = captures_on(b, sq)
        cut = (length == limit and len(caps) > 0)
        if length > 0:
            path_str = " ".join(m.uci for m in path)
            took = {WHITE: 0, BLACK: 0}
            white_took = []
            black_took = []
            for i in range(length):
                took[by[i]] += piece_value(taken[i])
                if by[i] == WHITE:
                    white_took.append(taken[i])
                else:
                    black_took.append(taken[i])
            w_str = f"WHITE-TOOK {' '.join(white_took) if white_took else '-'}"
            b_str = f"BLACK-TOOK {' '.join(black_took) if black_took else '-'}"
            cut_str = " LIMIT" if cut else ""
            lines.append(f"SEQUENCE {path_str} {w_str} {b_str} MATERIAL White {took[WHITE]} Black {took[BLACK]}{cut_str}")
            sequences_count += 1
        if cut:
            was_cut = True
        if length < limit:
            for c in caps:
                next_b = b.clone()
                make_move(next_b, c)
                path.append(c)
                taken.append(captured_type(b, c))
                by.append(b.turn)
                exchange_walk(next_b, path, taken, by, length + 1)
                path.pop()
                taken.pop()
                by.pop()

    exchange_walk(board, [], [], [], 0)
    values = [piece_value(captured_type(board, c)) for c in first_caps]

    for idx, c in enumerate(first_caps):
        mat_res, bounded = first_capture_class(board, c, limit)
        bnd_str = " BOUNDED" if bounded else ""
        lines.append(f"FIRST {c.uci} TAKES {captured_type(board, c)} VALUE {values[idx]} {material_text(mat_res)} ORDER {order_label(values, values[idx])}{bnd_str}")

    lines.append(f"SUMMARY SEQUENCES {sequences_count}")
    if was_cut:
        lines.append(f"LIMIT {limit}")
    lines.append("EXCHANGE END\n")
    return "\n".join(lines)


def order_report(board: Board, limit: int) -> str:
    """Generates Stage 3E combined move ordering report."""
    lines: List[str] = [
        f"ORDER BEGIN {color_name(board.turn)} EXCHANGE LIMIT {limit}",
        "NOTE an order of listed facts (ideas 7 and 8), rebuilt in every position; not a choice of move"
    ]
    all_moves = sorted_moves(board)
    if not all_moves:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, board.turn) else 'stalemate'}")
        lines.append("ORDER END\n")
        return "\n".join(lines)

    entries = []
    has_group1 = False
    for m in all_moves:
        taken = captured_type(board, m)
        val = piece_value(taken)
        dist = move_distance(m)
        bounded = False
        if taken:
            mat, bounded = first_capture_class(board, m, limit)
        else:
            mat = MaterialResult.MATERIAL_ELSE
        if taken and mat != MaterialResult.MATERIAL_ELSE:
            has_group1 = True
        entries.append({
            'move': m, 'taken': taken, 'value': val,
            'squares': dist, 'material': mat, 'bounded': bounded
        })

    lines.append(f"HEADS {'CAPTURE' if has_group1 else 'DISTANCE'}")

    # Group 1: FORCED then POSSIBLE
    for cls in (MaterialResult.MATERIAL_FORCED, MaterialResult.MATERIAL_POSSIBLE):
        vals = [9 - e['value'] for e in entries if e['taken'] and e['material'] == cls]
        for v in range(9, 0, -1):
            for d in range(1, 8):
                for e in entries:
                    if not e['taken'] or e['material'] != cls or e['value'] != v or e['squares'] != d:
                        continue
                    bnd_str = " BOUNDED" if e['bounded'] else ""
                    lines.append(f"GROUP 1 CAPTURE {e['move'].uci} TAKES {e['taken']} VALUE {e['value']} SQUARES {e['squares']} {material_text(e['material'])} ORDER {order_label(vals, 9 - v)}{bnd_str}")

    # Group 2: Everything else by distance
    distances = [e['squares'] for e in entries if not (e['taken'] and e['material'] != MaterialResult.MATERIAL_ELSE)]
    for d in range(1, 8):
        for e in entries:
            if (e['taken'] and e['material'] != MaterialResult.MATERIAL_ELSE) or e['squares'] != d:
                continue
            line = f"GROUP 2 DISTANCE {e['move'].uci} SQUARES {d} ORDER {order_label(distances, d)}"
            if e['taken']:
                bnd_str = " BOUNDED" if e['bounded'] else ""
                line += f" TAKES {e['taken']} VALUE {e['value']} {material_text(e['material'])}{bnd_str}"
            lines.append(line)

    lines.append("ORDER END\n")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Multi-move comparison (Stage 3F)
# ----------------------------------------------------------------------------

def compare_report(
    board: Board, tracker: Tracker, goal: Optional[Goal], depth: int, moves: List[Move]
) -> str:
    """Side-by-side comparative analysis of candidate moves."""
    lines: List[str] = [
        f"COMPARE BEGIN {color_name(board.turn)} DEPTH {depth}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good"
    ]

    # LOOP report once (shared by every candidate). Do not call order_report /
    # routes_real_report here — those results were never used and routes_real
    # at depth 5 can take a very long time.
    loop_txt = loop_report(board, depth) if depth >= 1 else ""

    candidates = []
    all_values = []
    all_distances = []
    for m in moves:
        taken = captured_type(board, m)
        all_values.append(piece_value(taken))
        all_distances.append(move_distance(m))

    for m in moves:
        c: Dict = {'move': m, 'text': m.uci}
        r_txt = calc_report(board, tracker, m)
        c['r_white'] = "-"
        c['r_black'] = "-"
        c['check'] = "none"
        c['mate1_white'] = "none"
        c['mate1_black'] = "none"
        c['links'] = [0, 0, 0, 0]

        for line in r_txt.splitlines():
            if line.startswith("COUNT White "): c['r_white'] = line[12:]
            elif line.startswith("COUNT Black "): c['r_black'] = line[12:]
            elif line.startswith("CHECK "): c['check'] = line[6:]
            elif line.startswith("MATE1 White "): c['mate1_white'] = line[12:]
            elif line.startswith("MATE1 Black "): c['mate1_black'] = line[12:]
            elif line.startswith("PROTECT+ "): c['links'][0] += 1
            elif line.startswith("PROTECT- "): c['links'][1] += 1
            elif line.startswith("ATTACK+ "): c['links'][2] += 1
            elif line.startswith("ATTACK- "): c['links'][3] += 1

        rep_txt = replies_report(board, tracker, m)
        c['threat'] = "-"
        c['replies'] = "-"
        for line in rep_txt.splitlines():
            if line.startswith("NO REPLIES "): c['threat'] = f"GAME-OVER {line[11:]}"
            elif line.startswith("THREAT "): c['threat'] = line[7:]
            elif line.startswith("SUMMARY REPLIES "): c['replies'] = line[16:]

        # LOOP lines always use a promotion letter for pawns on the last rank.
        # Candidate moves typed as a7a8 (promo '\0') must look up as a7a8q.
        loop_uci = _loop_match_uci(board, m)
        prefix = f"FIRST {loop_uci} "
        c['loop_status'] = "-"
        c['loop_level'] = -1
        for line in loop_txt.splitlines():
            if line.startswith(prefix):
                rem = line[len(prefix):]
                c['loop_status'] = rem
                c['loop_level'] = 2 if "FORCED" in rem else (1 if "POSSIBLE" in rem else 0)
                break

        c['taken'] = captured_type(board, m)
        c['value'] = piece_value(c['taken'])
        c['squares'] = move_distance(m)
        c['squares_label'] = order_label(all_distances, c['squares'])

        if c['taken']:
            # Rank captures only against other captures (ignore non-capture 0s).
            capture_vals = [v for v in all_values if v > 0]
            neg_vals = [9 - v for v in capture_vals] if capture_vals else [9 - c['value']]
            c['value_label'] = order_label(neg_vals, 9 - c['value'])
            c['material'], c['bounded'] = first_capture_class(board, m, depth)
            c['material_known'] = True
        else:
            c['value_label'] = "none"
            c['material_known'] = False
            c['material'] = MaterialResult.MATERIAL_ELSE
            c['bounded'] = False

        candidates.append(c)

    # Pairs comparison
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a = candidates[i]
            b = candidates[j]
            lines.append(f"COMPARE {a['text']} {b['text']} MOVE-PAIR")
            lines.append(f"COMPARE {a['text']} {b['text']} R White {a['r_white']} | {b['r_white']} {'SAME' if a['r_white'] == b['r_white'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} R Black {a['r_black']} | {b['r_black']} {'SAME' if a['r_black'] == b['r_black'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} CHECK {a['check']} | {b['check']} {'SAME' if a['check'] == b['check'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} THREAT {a['threat']} | {b['threat']} {'SAME' if a['threat'] == b['threat'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} REPLIES {a['replies']} | {b['replies']} {'SAME' if a['replies'] == b['replies'] else 'DIFFERENT'}")
            lines.append(f"COMPARE {a['text']} {b['text']} LOOP {a['loop_status']} | {b['loop_status']} {'SAME' if a['loop_status'] == b['loop_status'] else 'DIFFERENT'}")

    lines.append("COMPARE END\n")
    return "\n".join(lines)
