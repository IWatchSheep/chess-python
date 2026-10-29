"""Stage 3A: the fact calculator (CALC report).

calc_report describes everything that changes when one move is played:
captures, lost/gained squares, protect/attack links, checks and mate-in-one.
"""

from typing import Dict, List
from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES, CALC_MAX_ID,
    Color, WHITE, BLACK,
    color_name, square_index, square_text,
)
from ..move import Move
from ..board import Board
from ..movegen import (
    generate_moves, make_move, is_in_check, piece_attacks, pseudo_legal,
)
from ..tracker import Tracker


def zero_move_cause(board: Board, row: int, col: int) -> str:
    """Diagnoses why a piece has 0 legal moves: BLOCKED, CHECK, or PIN."""
    view = board.clone()
    view.turn = board.grid[row][col].color
    pseudo_count = 0
    for er in range(BOARD_SIZE):
        for ec in range(BOARD_SIZE):
            m = Move(sr=row, sc=col, er=er, ec=ec)
            if pseudo_legal(view, m):
                pseudo_count += 1

    if pseudo_count == 0:
        return "BLOCKED"
    return "CHECK" if is_in_check(view, view.turn) else "PIN"


def linked(board: Board, pr: int, pc: int, qr: int, qc: int, protect: bool) -> bool:
    """Checks whether piece (pr, pc) protects (if friendly) or attacks (if enemy) piece (qr, qc)."""
    p = board.grid[pr][pc]
    q = board.grid[qr][qc]
    if p.is_empty or q.is_empty or q.type == 'K' or (pr == qr and pc == qc):
        return False
    same_color = (p.color == q.color)
    if same_color != protect:
        return False
    return piece_attacks(board, pr, pc, qr, qc)


def report_mates(board: Board, side: Color) -> List[str]:
    """Finds all immediate checkmate moves available for `side`."""
    view = board.clone()
    view.turn = side
    moves = generate_moves(view)
    mates = []
    for m in moves:
        next_b = view.clone()
        make_move(next_b, m)
        replies = generate_moves(next_b)
        if len(replies) == 0 and is_in_check(next_b, next_b.turn):
            mates.append(m.uci)
    return mates


def count_mate_in_one(board: Board, side: Color) -> int:
    return len(report_mates(board, side))


def calc_report(board: Board, tracker: Tracker, move: Move) -> str:
    """Generates the complete Stage 3A Calculator report for `move`."""
    lines: List[str] = []
    after_board = board.clone()
    make_move(after_board, move)

    after_id, captured = tracker.ids_after_move(board, move)
    s0 = tracker.take_snapshot(board)

    temp_t = Tracker()
    temp_t.grid = after_id
    s1 = temp_t.take_snapshot(after_board)

    names = tracker.make_names(board)
    mover = board.grid[move.sr][move.sc]
    from_sq = square_text(square_index(move.sr, move.sc))
    to_sq = square_text(square_index(move.er, move.ec))

    # Header
    lines.append(f"CALC BEGIN {move.uci}")
    lines.append(f"MOVED {color_name(mover.color)} {mover.type} {from_sq} {to_sq}")

    if mover.type == 'K' and abs(move.ec - move.sc) == 2:
        is_ks = move.is_kingside_castle
        rf = square_text(square_index(move.sr, 7 if is_ks else 0))
        rt = square_text(square_index(move.sr, 5 if is_ks else 3))
        lines.append(f"CASTLE {color_name(mover.color)} {rf} {rt}")

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            pid = tracker.grid[r][c]
            if pid != 0 and captured[pid]:
                sq = square_text(square_index(r, c))
                lines.append(f"CAPTURED {color_name(tracker.color[pid])} {board.grid[r][c].type} {sq}")

    if mover.type == 'P' and (move.er == 0 or move.er == 7):
        promo_char = move.promotion if move.promotion and move.promotion != '\0' else 'Q'
        lines.append(f"PROMOTED {color_name(mover.color)} {from_sq} {to_sq} {promo_char}")

    # ZERO
    for side in (WHITE, BLACK):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                pid = tracker.grid[r][c]
                if pid == 0 or tracker.color[pid] != side or not s1.present[pid]:
                    continue
                before_zero = (s0.legal_count[pid] == 0)
                after_zero = (s1.legal_count[pid] == 0)
                if not before_zero and not after_zero:
                    continue

                pname = f"{board.grid[r][c].type} {square_text(square_index(r, c))}"
                cause = zero_move_cause(after_board, s1.row[pid], s1.col[pid]) if after_zero else zero_move_cause(board, r, c)
                when = "both" if (before_zero and after_zero) else ("after" if after_zero else "before")
                lines.append(f"ZERO {color_name(side)} {pname} {cause} {when}")

    # LOST, GAINED, RESTORED
    lost_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    gained_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    restored_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}

    for keyword, target_dict in (("LOST", lost_counts), ("GAINED", gained_counts), ("RESTORED", restored_counts)):
        for side in (WHITE, BLACK):
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    pid = tracker.grid[r][c]
                    if pid == 0 or tracker.color[pid] != side or not s1.present[pid]:
                        continue
                    sq_list = []
                    for i in range(TOTAL_SQUARES):
                        is_lost = s0.legal[pid][i] and not s1.legal[pid][i]
                        is_new = not s0.legal[pid][i] and s1.legal[pid][i]
                        wanted = False
                        if keyword == "LOST" and is_lost:
                            wanted = True
                        elif keyword == "GAINED" and is_new and not tracker.lost[pid][i]:
                            wanted = True
                        elif keyword == "RESTORED" and is_new and tracker.lost[pid][i]:
                            wanted = True

                        if wanted:
                            sq_list.append(square_text(i))
                            target_dict[side] += 1

                    if sq_list:
                        lines.append(f"{keyword} {color_name(side)} {names[pid]} {' '.join(sq_list)}")

    # DENIED & OPENED
    denied_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}
    opened_counts: Dict[Color, int] = {WHITE: 0, BLACK: 0}

    for denied_mode, target_dict in ((True, denied_counts), (False, opened_counts)):
        kw = "DENIED" if denied_mode else "OPENED"
        for side in (WHITE, BLACK):
            for i in range(TOTAL_SQUARES):
                chg = (s0.reach[side][i] and not s1.reach[side][i]) if denied_mode else (not s0.reach[side][i] and s1.reach[side][i])
                if not chg:
                    continue

                only_captured = denied_mode
                if denied_mode:
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            pid = tracker.grid[r][c]
                            if pid != 0 and board.grid[r][c].color == side and s0.legal[pid][i] and not captured[pid]:
                                only_captured = False
                                break
                        if not only_captured:
                            break

                cap_suffix = " by-capture" if only_captured else ""
                lines.append(f"{kw} {color_name(side)} {square_text(i)}{cap_suffix}")
                target_dict[side] += 1

    # LINKS: PROTECT+, PROTECT-, ATTACK+, ATTACK-
    for side in (WHITE, BLACK):
        for pr in range(BOARD_SIZE):
            for pc in range(BOARD_SIZE):
                p = after_id[pr][pc]
                if p == 0 or after_board.grid[pr][pc].color != side:
                    continue
                for qr in range(BOARD_SIZE):
                    for qc in range(BOARD_SIZE):
                        q = after_id[qr][qc]
                        if q == 0 or not linked(after_board, pr, pc, qr, qc, True):
                            continue
                        in_other = (s0.present[p] and s0.present[q] and
                                    linked(board, s0.row[p], s0.col[p], s0.row[q], s0.col[q], True))
                        if not in_other:
                            lines.append(f"PROTECT+ {color_name(side)} {names[p]} {names[q]}")

    for side in (WHITE, BLACK):
        for pr in range(BOARD_SIZE):
            for pc in range(BOARD_SIZE):
                p = tracker.grid[pr][pc]
                if p == 0 or board.grid[pr][pc].color != side:
                    continue
                for qr in range(BOARD_SIZE):
                    for qc in range(BOARD_SIZE):
                        q = tracker.grid[qr][qc]
                        if q == 0 or not linked(board, pr, pc, qr, qc, True):
                            continue
                        in_other = (s1.present[p] and s1.present[q] and
                                    linked(after_board, s1.row[p], s1.col[p], s1.row[q], s1.col[q], True))
                        if not in_other:
                            lines.append(f"PROTECT- {color_name(side)} {names[p]} {names[q]}")

    for side in (WHITE, BLACK):
        for pr in range(BOARD_SIZE):
            for pc in range(BOARD_SIZE):
                p = after_id[pr][pc]
                if p == 0 or after_board.grid[pr][pc].color != side:
                    continue
                for qr in range(BOARD_SIZE):
                    for qc in range(BOARD_SIZE):
                        q = after_id[qr][qc]
                        if q == 0 or not linked(after_board, pr, pc, qr, qc, False):
                            continue
                        in_other = (s0.present[p] and s0.present[q] and
                                    linked(board, s0.row[p], s0.col[p], s0.row[q], s0.col[q], False))
                        if not in_other:
                            lines.append(f"ATTACK+ {color_name(side)} {names[p]} {names[q]}")

    for side in (WHITE, BLACK):
        for pr in range(BOARD_SIZE):
            for pc in range(BOARD_SIZE):
                p = tracker.grid[pr][pc]
                if p == 0 or board.grid[pr][pc].color != side:
                    continue
                for qr in range(BOARD_SIZE):
                    for qc in range(BOARD_SIZE):
                        q = tracker.grid[qr][qc]
                        if q == 0 or not linked(board, pr, pc, qr, qc, False):
                            continue
                        in_other = (s1.present[p] and s1.present[q] and
                                    linked(after_board, s1.row[p], s1.col[p], s1.row[q], s1.col[q], False))
                        if not in_other:
                            lines.append(f"ATTACK- {color_name(side)} {names[p]} {names[q]}")

    # CHECK
    for side in (WHITE, BLACK):
        if is_in_check(after_board, side):
            lines.append(f"CHECK {color_name(side)}")

    # MATE1
    answers = generate_moves(after_board)
    game_ended = (len(answers) == 0)
    if not game_ended:
        for side in (WHITE, BLACK):
            mates = report_mates(after_board, side)
            if mates:
                lines.append(f"MATE1 {color_name(side)} {' '.join(mates)}")

    # COUNT
    for side in (WHITE, BLACK):
        u1 = sum(1 for pid in range(1, CALC_MAX_ID) if s1.present[pid] and tracker.color[pid] == side and s1.legal_count[pid] == 0)
        u2 = lost_counts[side]
        u3 = denied_counts[side]
        g = gained_counts[side]
        r = restored_counts[side]
        opn = opened_counts[side]
        lines.append(f"COUNT {color_name(side)} U1 {u1} U2 {u2} U3 {u3} GAINED {g} RESTORED {r} OPENED {opn}")

    lines.append("CALC END\n")
    return "\n".join(lines)
