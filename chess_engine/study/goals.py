"""Stage 3D: goals, routes, PASS mode, distance order and support.

A "goal" is a set of squares (or the enemy king's neighbours) that the side to
move wants to reach or protect. This module parses goals and builds the
ROUTES, GOAL MARKS, DISTANCE ORDER and SUPPORT reports.
"""

from typing import List, Optional
from ..constants import (
    BOARD_SIZE, TOTAL_SQUARES,
    Color, WHITE, BLACK,
    GOAL_MAX_SQUARES, GOAL_MAX_LIMIT, GOAL_MAX_ROUTES,
    in_bounds, opposite, color_name, square_index, square_text, parse_square,
)
from ..move import Move
from ..board import Board
from ..movegen import (
    generate_moves, sorted_moves, make_move, is_in_check, piece_attacks, find_king,
)
from .common import (
    Goal, GoalCondition, RealResult, RouteVector,
    get_goal_show_risk, move_distance, order_label,
    pass_moves, pass_play, pieces_on_square, piece_value,
)


# ----------------------------------------------------------------------------
# Goal basics: squares, text, "does it hold?", distances
# ----------------------------------------------------------------------------

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
    from ..constants import TOTAL_SQUARES
    if not isinstance(sq, int) or sq < 0 or sq >= TOTAL_SQUARES:
        return False
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


# ----------------------------------------------------------------------------
# Parsing a goal from user text
# ----------------------------------------------------------------------------

def parse_goal(text: str) -> Optional[Goal]:
    """Parses 'f7 2', 'f7 g7 3', or 'king 2'.

    Squares (or 'king') come first; the final token is the move limit 1..4.
    Once the limit appears, no further tokens are allowed.
    """
    tokens = text.strip().split()
    if not tokens:
        return None

    g = Goal()
    limit_set = False
    for tok in tokens:
        # After the limit is set, any extra token is a parse error.
        if limit_set:
            return None

        if tok == "king" and g.count == 0 and not g.king:
            g.king = True
        elif len(tok) == 2 and not g.king:
            parsed = parse_square(tok)
            if not parsed or g.count >= GOAL_MAX_SQUARES:
                return None
            sq = square_index(parsed[0], parsed[1])
            # square_index returns -1 when out of bounds; never store that.
            if sq < 0 or sq in g.squares:
                return None
            g.squares.append(sq)
            g.count += 1
        elif tok.isascii() and tok.isdigit() and (g.count > 0 or g.king):
            # Limit is 1..4 — reject long / non-ASCII digit strings before int().
            if len(tok) > 2:
                return None
            val = int(tok, 10)
            if 1 <= val <= GOAL_MAX_LIMIT:
                g.limit = val
                limit_set = True
            else:
                return None
        else:
            return None

    # Default limit stays 1 when the user omits it (Goal.limit default).
    # An explicit limit still locks the parse so "f7 1 g7" is rejected.
    if g.count == 0 and not g.king:
        return None

    g.active = True
    return g


# ----------------------------------------------------------------------------
# Routes report (PASS mode)
# ----------------------------------------------------------------------------

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
                    if show_risk or get_goal_show_risk():
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
                            if show_risk or get_goal_show_risk():
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
        """True if side can force the goal in n plies against every reply."""
        if n < 1:
            return False
        moves = generate_moves(b)
        for m in moves:
            next_b = b.clone()
            make_move(next_b, m)
            if goal_holds(next_b, side, sq, cond):
                return True
            if n < 3:
                continue
            replies = generate_moves(next_b)
            if not replies:
                continue
            # Each reply needs its own clone — do not reuse one board.
            if all(
                goal_forced_real(_after_reply(next_b, rep), sq, cond, n - 2)
                for rep in replies
            ):
                return True
        return False

    def _after_reply(position: Board, rep: Move) -> Board:
        after = position.clone()
        make_move(after, rep)
        return after

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
