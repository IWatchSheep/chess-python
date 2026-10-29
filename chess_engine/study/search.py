"""Stage 3C: game tree search (LOOP and TRACE reports)."""

from typing import List, Tuple
from ..constants import BOARD_SIZE, WHITE, BLACK, color_name
from ..move import Move, parse_move_text
from ..board import Board
from ..movegen import generate_moves, sorted_moves, legal_move, make_move, is_in_check
from ..tracker import Tracker
from .calc import calc_report


def zero_move_pieces(board: Board, moves: List[Move]) -> int:
    """Counts pieces of side to move that have 0 legal moves."""
    moves_from = {m.sr * BOARD_SIZE + m.sc for m in moves}
    zero = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c].color == board.turn and (r * BOARD_SIZE + c) not in moves_from:
                zero += 1
    return zero


def mate_forced(board: Board, n: int) -> bool:
    """Minimax search checking if side to move can force checkmate in n plies."""
    if n < 1:
        return False

    moves = generate_moves(board)
    for m in moves:
        next_b = board.clone()
        make_move(next_b, m)
        replies = generate_moves(next_b)
        if len(replies) == 0:
            if is_in_check(next_b, next_b.turn):
                return True
        elif n >= 3:
            all_forced = True
            for rep in replies:
                after_rep = next_b.clone()
                make_move(after_rep, rep)
                if not mate_forced(after_rep, n - 2):
                    all_forced = False
                    break
            if all_forced:
                return True
    return False


def first_move_forces(after_board: Board, n: int) -> bool:
    """Checks whether first move forces checkmate in n plies."""
    replies = generate_moves(after_board)
    if not replies:
        return is_in_check(after_board, after_board.turn)
    if n < 3:
        return False
    for rep in replies:
        after_rep = after_board.clone()
        make_move(after_rep, rep)
        if not mate_forced(after_rep, n - 2):
            return False
    return True


def loop_report(board: Board, depth: int, zero_k: int = 0) -> str:
    """Exhaustive game tree search up to `depth` plies."""
    lines: List[str] = []
    mover = board.turn

    # Guard depth so positions[ply] / current_line[ply] cannot underflow.
    if depth < 1:
        lines.append(f"LOOP BEGIN {color_name(mover)} DEPTH {depth}")
        lines.append("LOOP END\n")
        return "\n".join(lines)

    first = sorted_moves(board)

    hdr = f"LOOP BEGIN {color_name(mover)} DEPTH {depth}"
    if zero_k > 0:
        hdr += f" ZERO {zero_k}"
    lines.append(hdr)

    if not first:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, mover) else 'stalemate'}")
        lines.append("LOOP END\n")
        return "\n".join(lines)

    positions = [0] * (depth + 1)
    mated = {WHITE: [0] * (depth + 1), BLACK: [0] * (depth + 1)}
    stalemates = [0] * (depth + 1)
    zero_counts = [0] * (depth + 1)
    first_mated = [{WHITE: 0, BLACK: 0} for _ in range(len(first))]
    replies_with_mate = [0] * len(first)
    # One slot per ply index 0..depth-1; never share Move objects across slots.
    current_line: List[Move] = [Move(0, 0, 0, 0) for _ in range(depth)]
    reply_reaches_mate = [False]

    def loop_walk(b: Board, ply: int, first_idx: int) -> None:
        moves = sorted_moves(b)
        positions[ply] += 1
        if zero_k > 0 and zero_move_pieces(b, moves) >= zero_k:
            zero_counts[ply] += 1

        if not moves:
            if is_in_check(b, b.turn):
                mated[b.turn][ply] += 1
                first_mated[first_idx][b.turn] += 1
                if b.turn != mover and ply >= 3:
                    reply_reaches_mate[0] = True
                path_str = " ".join(current_line[i].uci for i in range(ply))
                lines.append(f"MATE {ply} {path_str} MATED {color_name(b.turn)}")
            else:
                stalemates[ply] += 1
        elif ply < depth:
            for m in moves:
                next_b = b.clone()
                make_move(next_b, m)
                current_line[ply] = m
                if ply == 1:
                    reply_reaches_mate[0] = False
                loop_walk(next_b, ply + 1, first_idx)
                if ply == 1 and reply_reaches_mate[0]:
                    replies_with_mate[first_idx] += 1

    for idx, m in enumerate(first):
        next_b = board.clone()
        make_move(next_b, m)
        current_line[0] = m
        loop_walk(next_b, 1, idx)

    for p in range(1, depth + 1):
        line = f"PLY {p} POSITIONS {positions[p]} MATED White {mated[WHITE][p]} Black {mated[BLACK][p]} STALEMATES {stalemates[p]}"
        if zero_k > 0:
            line += f" ZERO {zero_counts[p]}"
        lines.append(line)

    any_forced = False
    any_possible = False
    for idx, m in enumerate(first):
        next_b = board.clone()
        make_move(next_b, m)
        replies = generate_moves(next_b)
        prefix = f"FIRST {m.uci} "
        if first_move_forces(next_b, depth):
            status = "FORCED"
            any_forced = True
        elif replies_with_mate[idx] > 0:
            status = f"POSSIBLE {replies_with_mate[idx]} OF {len(replies)}"
            any_possible = True
        else:
            status = "NOT-FOUND"
        lines.append(f"{prefix}{status} MATED White {first_mated[idx][WHITE]} Black {first_mated[idx][BLACK]}")

    result_str = "FORCED" if any_forced else ("POSSIBLE" if any_possible else "NOT-FOUND")
    lines.append(f"RESULT {color_name(mover)} {result_str}")
    if not any_forced:
        lines.append(f"LIMIT {depth}")
    lines.append("LOOP END\n")
    return "\n".join(lines)


def trace_report(
    board: Board, tracker: Tracker, moves_text: str
) -> Tuple[bool, str, int]:
    """Replays a series of moves and prints CALC reports."""
    tokens = moves_text.strip().split()
    if not tokens:
        return False, "", 1

    sim_b = board.clone()
    parsed_moves = []
    for idx, tok in enumerate(tokens):
        m = parse_move_text(tok)
        if not m or not legal_move(sim_b, m):
            return False, "", idx + 1
        make_move(sim_b, m)
        parsed_moves.append(m)

    lines: List[str] = [f"TRACE BEGIN {len(parsed_moves)}"]
    cur_b = board.clone()
    cur_t = tracker.clone()

    for idx, m in enumerate(parsed_moves):
        lines.append(f"TRACE PLY {idx + 1} {m.uci}")
        lines.append(calc_report(cur_b, cur_t, m).rstrip())
        cur_t.commit(cur_b, m)
        make_move(cur_b, m)

    lines.append("TRACE END\n")
    return True, "\n".join(lines), 0
