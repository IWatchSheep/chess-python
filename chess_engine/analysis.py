"""Advanced analytical and study engines: Stages 3A through 3F."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Set, Tuple
from .constants import (
    BOARD_SIZE, TOTAL_SQUARES, CALC_MAX_ID,
    Color, EMPTY, WHITE, BLACK,
    GOAL_MAX_SQUARES, GOAL_MAX_LIMIT, GOAL_MAX_ROUTES,
    LOOP_MAX_DEPTH, LOOP_MAX_FIRST, EXCHANGE_MAX, COMPARE_MAX,
    in_bounds, opposite, color_name, square_index, square_text,
    parse_square, home_row_for, rook_col_for,
    CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL
)
from .piece import Piece, empty_piece
from .move import Move, parse_move_text
from .board import Board
from .movegen import (
    generate_moves, sorted_moves, legal_move, make_move,
    is_in_check, piece_attacks, pseudo_legal, find_king
)
from .tracker import Tracker, Snapshot, FollowCase, follow_piece, position_after


# ============================================================================
# STAGE 3D: GOALS AND ROUTES DATA STRUCTURES
# ============================================================================

class GoalCondition(Enum):
    COND_REACH = 0
    COND_PROTECTED = 1


@dataclass
class Goal:
    active: bool = False
    king: bool = False
    count: int = 0
    squares: List[int] = field(default_factory=list)
    limit: int = 1


class RealResult(IntEnum):
    REAL_ELSE = 0
    REAL_POSSIBLE = 1
    REAL_FORCED = 2


class MaterialResult(IntEnum):
    MATERIAL_ELSE = 0
    MATERIAL_POSSIBLE = 1
    MATERIAL_FORCED = 2


@dataclass
class RouteVector:
    own: int = 0
    protectors: int = 0
    attackers: int = 0
    path: List[Move] = field(default_factory=list)
    length: int = 0
    dominated: bool = False
    raw_text: str = ""


# Global risk toggle for Stage 3D/3E
goal_show_risk = False


def set_goal_show_risk(val: bool) -> None:
    global goal_show_risk
    goal_show_risk = val


def get_goal_show_risk() -> bool:
    global goal_show_risk
    return goal_show_risk


def move_distance(m: Move) -> int:
    """Chebyshev distance (King distance): max(|dr|, |dc|)."""
    return max(abs(m.er - m.sr), abs(m.ec - m.sc))


def order_label(values: List[int], value: int) -> str:
    """Returns IF (if no valid element is smaller), ELSE (if no valid element is larger), or ELSE IF."""
    has_smaller = any(v >= 0 and v < value for v in values)
    has_larger = any(v >= 0 and v > value for v in values)
    if not has_smaller:
        return "IF"
    elif not has_larger:
        return "ELSE"
    return "ELSE IF"


def pass_moves(board: Board, side: Color) -> List[Move]:
    """Moves available for `side` evaluated as if it were its turn."""
    view = board.clone()
    view.turn = side
    return sorted_moves(view)


def pass_play(board: Board, move: Move, side: Color) -> None:
    """Plays move in PASS mode where opponent passes."""
    board.turn = side
    make_move(board, move)
    board.turn = side
    board.ep_row = -1
    board.ep_col = -1


def pieces_on_square(board: Board, sq: int, side: Color) -> int:
    """Counts friendly pieces attacking/defending sq (excluding piece on sq itself)."""
    count = 0
    tr, tc = sq // BOARD_SIZE, sq % BOARD_SIZE
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            curr_sq = r * BOARD_SIZE + c
            if curr_sq != sq and board.grid[r][c].color == side:
                if piece_attacks(board, r, c, tr, tc):
                    count += 1
    return count


def goal_squares(goal: Goal, board: Board, side: Color) -> List[int]:
    """Resolves target square indices for a goal."""
    if not goal.king:
        return list(goal.squares[:goal.count])

    enemy = opposite(side)
    kpos = find_king(board, enemy)
    if not kpos:
        return []
    kr, kc = kpos
    squares = []
    for r in range(kr - 1, kr + 2):
        for c in range(kc - 1, kc + 2):
            if in_bounds(r, c) and (r != kr or c != kc):
                squares.append(r * BOARD_SIZE + c)
    return squares


def goal_text(goal: Goal) -> str:
    """Formats goal description."""
    if goal.king:
        return "king"
    return " ".join(square_text(sq) for sq in goal.squares[:goal.count])


def goal_holds(board: Board, side: Color, sq: int, cond: GoalCondition) -> bool:
    """Checks whether a goal condition currently holds on square sq."""
    r, c = sq // BOARD_SIZE, sq % BOARD_SIZE
    if board.grid[r][c].color != side:
        return False
    if cond == GoalCondition.COND_REACH:
        return True
    return pieces_on_square(board, sq, side) > 0


def piece_distance(board: Board, r: int, c: int, side: Color, sq: int, max_depth: int) -> int:
    """Shortest number of moves for piece on (r, c) alone to reach sq."""
    if r * BOARD_SIZE + c == sq:
        return 0
    if max_depth <= 0:
        return -1

    best = -1
    moves = pass_moves(board, side)

    # 1-ply check first
    for m in moves:
        if m.sr == r and m.sc == c and (m.er * BOARD_SIZE + m.ec == sq):
            return 1

    # Recursive check
    for m in moves:
        if m.sr != r or m.sc != c:
            continue
        next_b = board.clone()
        pass_play(next_b, m, side)
        rem_max = (max_depth - 1) if best == -1 else (best - 2)
        d = piece_distance(next_b, m.er, m.ec, side, sq, rem_max)
        if d >= 0 and (best == -1 or d + 1 < best):
            best = d + 1

    return best


def side_within(board: Board, side: Color, sq: int, cond: GoalCondition, depth: int) -> bool:
    """Checks if any team piece can satisfy goal on sq within depth moves."""
    if goal_holds(board, side, sq, cond):
        return True
    if depth <= 0:
        return False

    moves = pass_moves(board, side)
    for m in moves:
        next_b = board.clone()
        pass_play(next_b, m, side)
        if side_within(next_b, side, sq, cond, depth - 1):
            return True
    return False


def side_distance(board: Board, side: Color, sq: int, cond: GoalCondition, max_depth: int) -> int:
    """Shortest number of moves for any team pieces to satisfy goal on sq."""
    for d in range(max_depth + 1):
        if side_within(board, side, sq, cond, d):
            return d
    return -1


def parse_goal(text: str) -> Optional[Goal]:
    """Parses 'f7 2', 'f7 g7 3', or 'king 2'."""
    tokens = text.strip().split()
    if not tokens:
        return None

    g = Goal()
    for tok in tokens:
        if g.limit > 1 and g.limit != -1:
            return None

        if tok == "king" and g.count == 0 and not g.king:
            g.king = True
        elif len(tok) == 2 and not g.king:
            parsed = parse_square(tok)
            if not parsed or g.count >= GOAL_MAX_SQUARES:
                return None
            sq = square_index(parsed[0], parsed[1])
            if sq in g.squares:
                return None
            g.squares.append(sq)
            g.count += 1
        elif tok.isdigit() and (g.count > 0 or g.king):
            val = int(tok)
            if 1 <= val <= GOAL_MAX_LIMIT:
                g.limit = val
            else:
                return None
        else:
            return None

    if g.limit == -1 or (g.count == 0 and not g.king):
        return None

    g.active = True
    return g


# ============================================================================
# STAGE 3A: FACT CALCULATOR
# ============================================================================

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


# ============================================================================
# STAGE 3B: OPPONENT REPLY ANALYSIS
# ============================================================================

def replies_report(board: Board, tracker: Tracker, move: Move) -> str:
    """Generates the Stage 3B Replies report for `move`."""
    lines: List[str] = []
    mover = board.grid[move.sr][move.sc].color
    after_board, tracker_after = position_after(board, tracker, move)

    lines.append(f"REPLIES BEGIN {move.uci}")
    replies = sorted_moves(after_board)

    threat_mates = report_mates(after_board, mover)
    threat = len(threat_mates) > 0

    if not replies:
        status = "checkmate" if is_in_check(after_board, after_board.turn) else "stalemate"
        lines.append(f"NO REPLIES {status}")
    else:
        if threat:
            lines.append(f"THREAT {color_name(mover)} {' '.join(threat_mates)}")
        else:
            lines.append(f"THREAT {color_name(mover)} none")

    stops = leaves = allows = no_threat = 0

    for rep in replies:
        after_rep = after_board.clone()
        make_move(after_rep, rep)
        still_threat = (count_mate_in_one(after_rep, mover) > 0)

        if threat and still_threat:
            label = "LEAVES"
            leaves += 1
        elif threat:
            label = "STOPS"
            stops += 1
        elif still_threat:
            label = "ALLOWS"
            allows += 1
        else:
            label = "NO-THREAT"
            no_threat += 1

        # Calculate counts for this reply
        rep_report_text = calc_report(after_board, tracker_after, rep)
        count_white = ""
        count_black = ""
        for line in rep_report_text.splitlines():
            if line.startswith("COUNT White "):
                count_white = line
            elif line.startswith("COUNT Black "):
                count_black = line

        lines.append(f"REPLY {rep.uci} {label} {count_white} {count_black}")

    lines.append(f"SUMMARY REPLIES {len(replies)} STOPS {stops} LEAVES {leaves} NO-THREAT {no_threat} ALLOWS {allows}")
    lines.append("REPLIES END\n")
    return "\n".join(lines)


def reply_detail(board: Board, tracker: Tracker, move: Move, reply: Move) -> Optional[str]:
    """Generates full CALC report for a single specific reply."""
    after_board, tracker_after = position_after(board, tracker, move)
    if not legal_move(after_board, reply):
        return None
    return calc_report(after_board, tracker_after, reply)


# ============================================================================
# STAGE 3C: GAME TREE SEARCH (LOOP AND TRACE)
# ============================================================================

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
    first = sorted_moves(board)
    mover = board.turn

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
    current_line: List[Move] = [Move(0, 0, 0, 0)] * depth
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


# ============================================================================
# STAGE 3D: ROUTES, PASS MODE, AND SUPPORT
# ============================================================================

def mark_dominated(routes: List[RouteVector]) -> None:
    """Marks routes as dominated if another route is strictly better or equal in all metrics."""
    for i, a in enumerate(routes):
        for j, b in enumerate(routes):
            if i == j:
                continue
            no_worse = (b.own <= a.own and b.protectors >= a.protectors and b.attackers <= a.attackers)
            better = (b.own < a.own or b.protectors > a.protectors or b.attackers < a.attackers)
            if no_worse and better:
                a.dominated = True
                break


def routes_report_with(
    board: Board, goal: Goal, second_goal: Optional[Goal] = None, show_risk: bool = False
) -> str:
    """Generates the Stage 3D routes report."""
    lines: List[str] = []
    side = board.turn
    enemy = opposite(side)
    squares = goal_squares(goal, board, side)

    lines.append(f"ROUTES BEGIN {color_name(side)} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS")
    lines.append(f"NOTE PASS is hypothetical: only {color_name(side)} moves, {color_name(enemy)} passes; not a real sequence of turns")

    reach: List[int] = []
    prot: List[int] = []
    first_reach = -1
    saved_routes: List[RouteVector] = []

    for sq in squares:
        sq_str = square_text(sq)
        lines.append(f"GOAL {sq_str} NOW White {pieces_on_square(board, sq, WHITE)} Black {pieces_on_square(board, sq, BLACK)}")

        # PIECE routes
        distances: List[int] = [-2] * 64
        for i in range(64):
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            if board.grid[r][c].color == side:
                distances[i] = piece_distance(board, r, c, side, sq, goal.limit)

        for i in range(64):
            if distances[i] == -2:
                continue
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            at = square_text(i)
            ptype = board.grid[r][c].type
            if distances[i] >= 0:
                lines.append(f"PIECE {ptype} {at} CONDITION IF MOVES {distances[i]} ORDER {order_label(distances, distances[i])}")
            else:
                lines.append(f"PIECE {ptype} {at} CONDITION ELSE ORDER NONE")

        route_list: List[RouteVector] = []
        extra_count = 0

        # Recursive search for routes of length distance[i]
        def find_piece_routes(b: Board, r: int, c: int, path: List[Move], length: int, kind: str) -> None:
            nonlocal extra_count
            if len(path) == length:
                if r * BOARD_SIZE + c == sq:
                    if len(route_list) >= GOAL_MAX_ROUTES:
                        extra_count += 1
                        return
                    end_b = b
                    rv = RouteVector(
                        own=length,
                        length=length,
                        path=list(path),
                        protectors=pieces_on_square(end_b, sq, side),
                        attackers=pieces_on_square(end_b, sq, enemy)
                    )
                    path_str = " ".join(m.uci for m in path)
                    raw = f"ROUTE {kind} {path_str} OWN {length} PROTECTORS {rv.protectors} ATTACKERS {rv.attackers}"
                    if show_risk or goal_show_risk:
                        at_risk_val = piece_value(end_b.grid[sq // 8][sq % 8].type) if rv.attackers > 0 else 0
                        raw += f" AT-RISK {at_risk_val}"
                    rv.raw_text = raw
                    route_list.append(rv)
                return
            if r * BOARD_SIZE + c == sq:
                return

            moves = pass_moves(b, side)
            for m in moves:
                if m.sr == r and m.sc == c:
                    next_b = b.clone()
                    pass_play(next_b, m, side)
                    path.append(m)
                    find_piece_routes(next_b, m.er, m.ec, path, length, kind)
                    path.pop()

        for i in range(64):
            if distances[i] >= 1:
                r, c = i // BOARD_SIZE, i % BOARD_SIZE
                at = square_text(i)
                kind_str = f"PIECE {board.grid[r][c].type} {at}"
                find_piece_routes(board, r, c, [], distances[i], kind_str)

        # SIDE routes
        r_dist = side_distance(board, side, sq, GoalCondition.COND_REACH, goal.limit)
        p_dist = side_distance(board, side, sq, GoalCondition.COND_PROTECTED, goal.limit)
        reach.append(r_dist)
        prot.append(p_dist)

        lines.append(f"SIDE REACH CONDITION {'IF MOVES ' + str(r_dist) if r_dist >= 0 else 'ELSE'}")
        if p_dist >= 0:
            lines.append(f"SIDE PROTECTED CONDITION IF MOVES {p_dist}")
            if p_dist >= 1:
                def find_side_routes(b: Board, path: List[Move], length: int) -> None:
                    nonlocal extra_count
                    holds = goal_holds(b, side, sq, GoalCondition.COND_PROTECTED)
                    if len(path) == length:
                        if holds:
                            if len(route_list) >= GOAL_MAX_ROUTES:
                                extra_count += 1
                                return
                            rv = RouteVector(
                                own=length,
                                length=length,
                                path=list(path),
                                protectors=pieces_on_square(b, sq, side),
                                attackers=pieces_on_square(b, sq, enemy)
                            )
                            path_str = " ".join(m.uci for m in path)
                            raw = f"ROUTE SIDE PROTECTED {path_str} OWN {length} PROTECTORS {rv.protectors} ATTACKERS {rv.attackers}"
                            if show_risk or goal_show_risk:
                                at_risk_val = piece_value(b.grid[sq // 8][sq % 8].type) if rv.attackers > 0 else 0
                                raw += f" AT-RISK {at_risk_val}"
                            rv.raw_text = raw
                            route_list.append(rv)
                        return
                    if holds:
                        return
                    moves = pass_moves(b, side)
                    for m in moves:
                        next_b = b.clone()
                        pass_play(next_b, m, side)
                        path.append(m)
                        find_side_routes(next_b, path, length)
                        path.pop()

                find_side_routes(board, [], p_dist)
        else:
            lines.append("SIDE PROTECTED CONDITION ELSE")

        mark_dominated(route_list)
        for rv in route_list:
            if rv.dominated:
                lines.append(f"{rv.raw_text} DOMINATED")
            else:
                lines.append(rv.raw_text)

        if r_dist >= 0 and first_reach < 0:
            first_reach = sq
            saved_routes = list(route_list)

        if extra_count > 0:
            lines.append(f"MORE ROUTES {extra_count} not listed")

    if not squares:
        lines.append("NO SQUARES")

    for k, sq in enumerate(squares):
        lines.append(f"SQUARE {square_text(sq)} REACH CONDITION {'IF' if reach[k] >= 0 else 'ELSE'} PROTECTED CONDITION {'IF' if prot[k] >= 0 else 'ELSE'}")

    for cond_name, dist_arr in (("REACH", reach), ("PROTECTED", prot)):
        first_idx = next((k for k, d in enumerate(dist_arr) if d >= 0), -1)
        if first_idx >= 0:
            lines.append(f"FIRST-IF {cond_name} {square_text(squares[first_idx])}")
        else:
            lines.append(f"FIRST-IF {cond_name} none (ELSE)")

    if second_goal and second_goal.active:
        lines.append(second_goal_report(board, second_goal, first_reach if first_reach >= 0 else None, saved_routes).rstrip())

    lines.append("ROUTES END\n")
    return "\n".join(lines)


def second_from(board: Board, second: Goal, label: str) -> List[str]:
    squares = goal_squares(second, board, board.turn)
    lines = []
    for sq in squares:
        r_dist = side_distance(board, board.turn, sq, GoalCondition.COND_REACH, second.limit)
        p_dist = side_distance(board, board.turn, sq, GoalCondition.COND_PROTECTED, second.limit)
        r_str = f"CONDITION IF MOVES {r_dist}" if r_dist >= 0 else "CONDITION ELSE"
        p_str = f"CONDITION IF MOVES {p_dist}" if p_dist >= 0 else "CONDITION ELSE"
        lines.append(f"FROM {label} SQUARE {square_text(sq)} REACH {r_str} PROTECTED {p_str}")
    return lines


def second_goal_report(
    board: Board, second: Goal, first_square: Optional[int], routes: List[RouteVector]
) -> str:
    lines = [f"SECOND GOAL {goal_text(second)} LIMIT {second.limit} PASS AFTER {square_text(first_square) if first_square is not None else 'none (ELSE)'}"]
    lines.extend(second_from(board, second, "START"))

    if first_square is not None:
        seen_paths = set()
        for rv in routes:
            if rv.dominated:
                continue
            path_tuple = tuple((m.sr, m.sc, m.er, m.ec, m.promotion) for m in rv.path)
            if path_tuple in seen_paths:
                continue
            seen_paths.add(path_tuple)

            end_b = board.clone()
            for m in rv.path:
                pass_play(end_b, m, board.turn)
            label = " ".join(m.uci for m in rv.path)
            lines.extend(second_from(end_b, second, label))

    lines.append("SECOND END")
    return "\n".join(lines)


def goal_marks_selection(board: Board, goal: Goal, r: int, c: int) -> str:
    """Marks destinations of selected piece according to goal progress."""
    squares = goal_squares(goal, board, board.turn)
    at = square_text(square_index(r, c))
    lines = [f"GOAL MARKS {board.grid[r][c].type} {at} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"]

    moves = sorted_moves(board)
    for m in moves:
        if m.sr != r or m.sc != c:
            continue
        after = board.clone()
        pass_play(after, m, board.turn)
        line = f"MARK {m.uci}"

        # Piece condition
        p_done = False
        left = goal.limit - 1
        for sq in squares:
            if left >= 0:
                d = piece_distance(after, m.er, m.ec, after.turn, sq, left)
                if d >= 0:
                    line += f" PIECE CONDITION IF {square_text(sq)} MOVES {1 + d}"
                    p_done = True
                    break
        if not p_done:
            line += " PIECE CONDITION ELSE"

        # Side condition
        s_done = False
        for sq in squares:
            if left >= 0:
                d = side_distance(after, after.turn, sq, GoalCondition.COND_REACH, left)
                if d >= 0:
                    line += f" SIDE CONDITION IF {square_text(sq)} MOVES {1 + d}"
                    s_done = True
                    break
        if not s_done:
            line += " SIDE CONDITION ELSE"

        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)


def goal_marks_after(board: Board, goal: Goal, move: Move) -> str:
    """Marks progress after proposed move."""
    after = board.clone()
    pass_play(after, move, board.turn)
    squares = goal_squares(goal, after, after.turn)
    lines = [f"GOAL MARKS AFTER {move.uci} GOAL {goal_text(goal)} LIMIT {goal.limit} PASS"]

    for sq in squares:
        if goal_holds(after, after.turn, sq, GoalCondition.COND_REACH):
            lines.append(f"REACHED {square_text(sq)} 1")

    moves = pass_moves(after, after.turn)
    for n in moves:
        next_b = after.clone()
        pass_play(next_b, n, after.turn)
        at = square_text(square_index(n.sr, n.sc))
        line = f"MARK {after.grid[n.sr][n.sc].type} {at} {n.uci}"

        p_done = False
        left = goal.limit - 2
        for sq in squares:
            if left >= 0:
                d = piece_distance(next_b, n.er, n.ec, after.turn, sq, left)
                if d >= 0:
                    line += f" PIECE CONDITION IF {square_text(sq)} MOVES {2 + d}"
                    p_done = True
                    break
        if not p_done:
            line += " PIECE CONDITION ELSE"

        s_done = False
        for sq in squares:
            if left >= 0:
                d = side_distance(next_b, after.turn, sq, GoalCondition.COND_REACH, left)
                if d >= 0:
                    line += f" SIDE CONDITION IF {square_text(sq)} MOVES {2 + d}"
                    s_done = True
                    break
        if not s_done:
            line += " SIDE CONDITION ELSE"

        lines.append(line)

    lines.append("GOAL MARKS END\n")
    return "\n".join(lines)


def distance_lines(board: Board, r: int, c: int, label: str) -> List[str]:
    """Generates distance order lines for piece on (r, c)."""
    view = board.clone()
    view.turn = board.grid[r][c].color
    all_moves = sorted_moves(view)
    piece_moves = [m for m in all_moves if m.sr == r and m.sc == c]
    if not piece_moves:
        return [f"NO-MOVES{label[4:]}"]

    distances = [move_distance(m) for m in piece_moves]
    lines = []
    for d in range(1, 8):
        for idx, m in enumerate(piece_moves):
            if distances[idx] != d:
                continue
            line = f"{label} {m.uci} DISTANCE {d} ORDER {order_label(distances, d)}"
            ptype = board.grid[r][c].type
            if ptype == 'N':
                line += " JUMP"
            elif ptype == 'K' and d == 2:
                is_ks = (m.ec > m.sc)
                rf = square_text(square_index(r, 7 if is_ks else 0))
                rt = square_text(square_index(r, 5 if is_ks else 3))
                line += f" CASTLE {rf}{rt}"
            lines.append(line)
    return lines


def distance_selection(board: Board, r: int, c: int) -> str:
    at = square_text(square_index(r, c))
    lines = [f"DISTANCE ORDER {board.grid[r][c].type} {at}"]
    lines.extend(distance_lines(board, r, c, "MOVE"))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)


def distance_after(board: Board, move: Move) -> str:
    after = board.clone()
    make_move(after, move)
    lines = [f"DISTANCE ORDER AFTER {move.uci}"]
    for side in (WHITE, BLACK):
        for i in range(TOTAL_SQUARES):
            r, c = i // BOARD_SIZE, i % BOARD_SIZE
            if after.grid[r][c].color == side:
                at = square_text(i)
                label = f"MOVE {color_name(side)} {after.grid[r][c].type} {at}"
                lines.extend(distance_lines(after, r, c, label))
    lines.append("DISTANCE ORDER END\n")
    return "\n".join(lines)


def routes_real_report(board: Board, goal: Goal, depth: int) -> str:
    """Generates Stage 3D real goal report."""
    side = board.turn
    enemy = opposite(side)
    squares = goal_squares(goal, board, side)
    lines = [
        f"ROUTES BEGIN {color_name(side)} GOAL {goal_text(goal)} DEPTH {depth} REAL",
        f"NOTE REAL: {color_name(enemy)} answers with every legal move; FORCED = reached whatever {color_name(enemy)} does"
    ]

    all_moves = generate_moves(board)
    if not all_moves:
        lines.append(f"NO MOVES {'checkmate' if is_in_check(board, side) else 'stalemate'}")
        lines.append("ROUTES END\n")
        return "\n".join(lines)

    def goal_forced_real(b: Board, sq: int, cond: GoalCondition, n: int) -> bool:
        if n < 1: return False
        moves = generate_moves(b)
        for m in moves:
            next_b = b.clone()
            make_move(next_b, m)
            if goal_holds(next_b, side, sq, cond):
                return True
            if n < 3:
                continue
            replies = generate_moves(next_b)
            if replies and all(goal_forced_real(after_rep, sq, cond, n - 2)
                               for after_rep in [next_b.clone()] for rep in replies
                               if (make_move(after_rep, rep) is None)):
                return True
        return False

    def goal_possible_real(b: Board, sq: int, cond: GoalCondition, n: int) -> bool:
        if n < 1: return False
        moves = generate_moves(b)
        for m in moves:
            next_b = b.clone()
            make_move(next_b, m)
            if goal_holds(next_b, side, sq, cond):
                return True
            if n >= 3:
                replies = generate_moves(next_b)
                for rep in replies:
                    after_rep = next_b.clone()
                    make_move(after_rep, rep)
                    if goal_possible_real(after_rep, sq, cond, n - 2):
                        return True
        return False

    def real_text(r: RealResult) -> str:
        if r == RealResult.REAL_FORCED: return "CONDITION IF FORCED"
        elif r == RealResult.REAL_POSSIBLE: return "CONDITION IF POSSIBLE"
        return "CONDITION ELSE"

    first_moves = sorted_moves(board)
    results: List[List[RealResult]] = []
    all_forced = True

    for sq in squares:
        sq_str = square_text(sq)
        sq_results = []
        for cond_idx, (cond, cond_name) in enumerate(((GoalCondition.COND_REACH, "REACH"),
                                                      (GoalCondition.COND_PROTECTED, "PROTECTED"))):
            lines.append(f"GOAL {sq_str} {cond_name}")
            best = RealResult.REAL_ELSE
            for m in first_moves:
                next_b = board.clone()
                make_move(next_b, m)
                if goal_holds(next_b, side, sq, cond):
                    lines.append(f"FIRST {m.uci} CONDITION IF FORCED MOVES 1")
                    best = RealResult.REAL_FORCED
                    continue

                replies = generate_moves(next_b)
                forced = (depth >= 3 and len(replies) > 0)
                k = 0
                for rep in replies:
                    after_rep = next_b.clone()
                    make_move(after_rep, rep)
                    can = goal_possible_real(after_rep, sq, cond, depth - 2)
                    if can: k += 1
                    if forced and (not can or not goal_forced_real(after_rep, sq, cond, depth - 2)):
                        forced = False

                if forced:
                    lines.append(f"FIRST {m.uci} CONDITION IF FORCED")
                    best = RealResult.REAL_FORCED
                elif k > 0:
                    lines.append(f"FIRST {m.uci} CONDITION IF POSSIBLE {k} OF {len(replies)}")
                    if best == RealResult.REAL_ELSE:
                        best = RealResult.REAL_POSSIBLE
                else:
                    lines.append(f"FIRST {m.uci} CONDITION ELSE")

            sq_results.append(best)
            lines.append(f"RESULT {sq_str} {cond_name} {real_text(best)}")
            if best != RealResult.REAL_FORCED:
                all_forced = False
        results.append(sq_results)

    if not squares:
        lines.append("NO SQUARES")

    for k, sq in enumerate(squares):
        sq_str = square_text(sq)
        lines.append(f"SQUARE {sq_str} REACH {real_text(results[k][0])} PROTECTED {real_text(results[k][1])}")

    for cond_idx, cond_name in enumerate(("REACH", "PROTECTED")):
        first_idx = next((k for k in range(len(squares)) if results[k][cond_idx] != RealResult.REAL_ELSE), -1)
        if first_idx >= 0:
            res_word = "FORCED" if results[first_idx][cond_idx] == RealResult.REAL_FORCED else "POSSIBLE"
            lines.append(f"FIRST-IF {cond_name} {square_text(squares[first_idx])} {res_word}")
        else:
            lines.append(f"FIRST-IF {cond_name} none (ELSE)")

    if not all_forced or not squares:
        lines.append(f"LIMIT {depth}")
    lines.append("ROUTES END\n")
    return "\n".join(lines)


def support_report(board: Board, move: Move) -> str:
    """Generates Stage 3D SUPPORT report."""
    side = board.turn
    enemy = opposite(side)
    after = board.clone()
    pass_play(after, move, side)
    sq = square_index(move.er, move.ec)
    ptype = after.grid[move.er][move.ec].type
    at = square_text(sq)

    lines = [
        f"SUPPORT BEGIN {move.uci} PASS",
        f"NOTE PASS is hypothetical: {color_name(side)} moves again, {color_name(enemy)} passes",
        f"SUPPORT NOW {ptype} {at} PROTECTORS {pieces_on_square(after, sq, side)}"
    ]

    follows = 0
    moves = pass_moves(after, side)
    for f in moves:
        if f.sr == move.er and f.sc == move.ec:
            continue
        next_b = after.clone()
        pass_play(next_b, f, side)
        if next_b.grid[move.er][move.ec].color != side:
            continue

        before_att = piece_attacks(after, f.sr, f.sc, move.er, move.ec)
        now_att = piece_attacks(next_b, f.er, f.ec, move.er, move.ec)
        if now_att and not before_att:
            from_sq = square_text(square_index(f.sr, f.sc))
            ftype = after.grid[f.sr][f.sc].type
            prots = pieces_on_square(next_b, sq, side)
            lines.append(f"FOLLOW {f.uci} {ftype} {from_sq} PROTECTS {ptype} {at} PROTECTORS {prots}")
            follows += 1

    lines.append(f"SUMMARY FOLLOWS {follows}")
    lines.append("SUPPORT END\n")
    return "\n".join(lines)


# ============================================================================
# STAGE 3E: CAPTURE SEQUENCES, EXCHANGES, AND MOVE ORDERING
# ============================================================================

def piece_value(ptype: str) -> int:
    return {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}.get(ptype, 0)


def captured_type(board: Board, m: Move) -> str:
    """Returns captured piece type ('P', 'N', etc.) or empty string."""
    target = board.grid[m.er][m.ec]
    if not target.is_empty and target.color != board.grid[m.sr][m.sc].color:
        return target.type
    if board.grid[m.sr][m.sc].type == 'P' and m.sc != m.ec and target.is_empty:
        return 'P'
    return ""


def captures_on(board: Board, sq: int) -> List[Move]:
    """All legal captures landing on sq for side to move."""
    all_moves = sorted_moves(board)
    return [m for m in all_moves if (m.er * BOARD_SIZE + m.ec == sq) and captured_type(board, m)]


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
        mat = first_capture_class(board, m, limit)[0] if taken else MaterialResult.MATERIAL_ELSE
        if taken:
            mat, bounded = first_capture_class(board, m, limit)
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


# ============================================================================
# STAGE 3F: MULTI-MOVE COMPARISON REPORT
# ============================================================================

def compare_report(
    board: Board, tracker: Tracker, goal: Optional[Goal], depth: int, moves: List[Move]
) -> str:
    """Side-by-side comparative analysis of candidate moves."""
    lines: List[str] = [
        f"COMPARE BEGIN {color_name(board.turn)} DEPTH {depth}",
        "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good"
    ]

    # Pre-compute reports
    loop_txt = loop_report(board, depth)
    order_txt = order_report(board, depth)
    real_txt = routes_real_report(board, goal, depth) if (goal and goal.active) else ""

    candidates = []
    all_values = []
    all_distances = []
    for m in moves:
        taken = captured_type(board, m)
        val = piece_value(taken)
        dist = move_distance(m)
        all_values.append(val)
        all_distances.append(dist)

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

        prefix = f"FIRST {m.uci} "
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
            neg_vals = [9 - v for v in all_values]
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
