"""CLI commands: how the player types moves and analysis tools.

Read this file top-down:
  1. Help text
  2. Move flow (select square, preview, F / P / N, fen, promotion)
  3. Analysis handlers (r, replies, loop, goal, memory, ...)
  4. Command tables used by process_command

Play always goes: start square -> destination preview -> F to finalize.
Analysis commands only print facts; they never choose a move for you.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from .constants import (
    EXCHANGE_MAX, COMPARE_MAX, FEN_TEXT_SIZE,
    opposite, color_name, parse_square, square_index, in_bounds,
)
from .move import Move, parse_move_text
from .movegen import legal_move, make_move
from .ui import print_selection_near_prompt
from .analysis import (
    parse_goal, goal_text,
    calc_report, replies_report, reply_detail,
    loop_report, trace_report,
    routes_report_with, routes_real_report, support_report,
    goal_marks_selection, distance_selection,
    exchange_report, order_report, compare_report,
    set_goal_show_risk, get_goal_show_risk,
)
from .cli_session import (
    GameSession, Step, err, move_label, warn_slow_search,
    MAX_COMMAND_CHARS, parse_bounded_int, sanitize_display_text,
)

Handler = Callable[[GameSession, str], bool]


@dataclass(frozen=True)
class CommandSpec:
    """One named command family for dispatch and help text."""

    name: str
    summary: str
    handler: Handler
    topic: str = "analysis"  # "move" or "analysis"
    usage: str = ""


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

def print_help(topic: str = "") -> None:
    """Print command help. topic may be empty, 'goal', or another command name."""
    topic = topic.strip().lower()

    if not topic:
        print("=== Help: how to move ===")
        print("  1. Enter a start square (e2)")
        print("  2. Enter a destination (e4)  -> preview only, nothing is played")
        print("  3. Type F to finalize / play the move")
        print("  N / NEW  cancel selection     P  clear preview, keep piece")
        print("  restart  quit  claim  resign  fen  fen <text>")
        print("")
        print("=== Help: analysis (optional) ===")
        for spec in ANALYSIS_COMMANDS:
            print(f"  {spec.name:<14} {spec.summary}")
        print("")
        print("Type help <name> for details, for example: help goal")
        print("Note: typing distance or risk alone shows status;")
        print("      use distance on/off and risk on/off to change them.")
        return

    if topic in ("goal", "goal2"):
        print("goal / goal2: set target squares and a limit of own moves (1 to 4).")
        print("  Examples: goal f7 2 | goal f7 g7 h7 3 | goal king 2 | goal off")
        print("  goal2 d5 2 | goal2 off")
        print("  Then: routes   or   routes real 3")
        return

    for spec in ALL_HELP_SPECS:
        if spec.name == topic or topic in spec.name.split():
            print(f"{spec.name}: {spec.summary}")
            if spec.usage:
                print(f"  {spec.usage}")
            return

    safe = sanitize_display_text(topic)
    print(f"No help topic named '{safe}'. Type help for the full list.")


def handle_help(_session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "help" and not lower.startswith("help "):
        return False
    topic = cmd[5:].strip() if lower.startswith("help ") else ""
    print_help(topic)
    return True


# ---------------------------------------------------------------------------
# Move-flow handlers
# ---------------------------------------------------------------------------

def handle_cancel(session: GameSession, cmd: str) -> bool:
    """N / NEW / select none -> clear selection."""
    lower = cmd.lower()
    is_new = lower in ("new", "select none")
    is_n = lower == "n" and not session.promotion_pending
    if not (is_new or is_n):
        return False
    session.clear_selection()
    print("Selection cleared. Enter a new start square.")
    return True


def handle_fen(session: GameSession, cmd: str) -> bool:
    """fen  -> print position;  fen <text>  -> load a practice position."""
    lower = cmd.lower()
    if lower == "fen":
        print(f"FEN: {session.board.to_fen()}")
        return True
    if not lower.startswith("fen "):
        return False

    fen_str = cmd[4:].strip()
    # FEN_TEXT_SIZE comes from the C port buffer; allow a little headroom.
    if len(fen_str) > max(FEN_TEXT_SIZE, 256):
        err("FEN rejected: text is too long. The position is unchanged.")
        return True
    ok, reason = session.board.load_fen(fen_str)
    if ok:
        session.clear_selection()
        session.clear_analysis_options()
        session.memory.clear()
        session.tracker.init_from_board(session.board)
        print("FEN loaded: practice position set up.")
    else:
        err(f"FEN rejected: {reason}. The position is unchanged.")
    return True


def handle_promotion_choice(session: GameSession, cmd: str) -> bool:
    """If a promotion piece is required, accept Q/R/B/N (or keep waiting)."""
    if not session.promotion_pending:
        return False

    # Game-control commands are handled later by handle_game_control.
    if cmd.lower() in ("quit", "exit", "restart", "resign", "claim"):
        return False

    if len(cmd) == 1 and cmd.upper() in "QRBN":
        pending = session.pending_promotion
        if not (in_bounds(pending.sr, pending.sc) and in_bounds(pending.er, pending.ec)):
            err("Promotion state is invalid. Type NEW to cancel and start over.")
            session.clear_selection()
            return True
        move = Move(
            pending.sr, pending.sc, pending.er, pending.ec,
            promotion=cmd.upper(),
        )
        session.set_preview(move)
        return True

    err("Choose Q, R, B or N; or type NEW to cancel.")
    return True


def handle_finalize(session: GameSession, cmd: str) -> bool:
    """F -> play the previewed move for real."""
    if cmd.lower() != "f":
        return False

    if not session.preview_shown or not session.has_selection():
        err("No preview to finalize. Select a piece and preview a destination first.")
        return True

    if not legal_move(session.board, session.preview_move):
        err("Preview is no longer legal. Start a new selection.")
        session.invalidate_preview()
        return True

    print(f"FINALIZED: {move_label(session.preview_move)}")
    session.memory.record_finalized()
    session.tracker.commit(session.board, session.preview_move)
    make_move(session.board, session.preview_move)
    session.board.record_position()
    session.clear_selection()
    return True


def handle_discard_preview(session: GameSession, cmd: str) -> bool:
    """P -> keep the selected piece, clear only the destination preview."""
    if cmd.lower() != "p":
        return False
    if not session.has_selection():
        err("Select a piece first.")
    else:
        session.clear_preview_keep_piece()
        print("Preview cleared. Enter another destination for the selected piece.")
    return True


def handle_square_entry(session: GameSession, cmd: str) -> bool:
    """Two-character input: pick a start square, or a destination."""
    if len(cmd) != 2:
        return False

    parsed = parse_square(cmd)
    if not parsed:
        return False

    if session.preview_shown:
        err("Preview already shown. Press F, P or N, then Enter.")
        return True

    row, col = parsed

    if not session.has_selection():
        piece = session.board.grid[row][col]
        if piece.color != session.board.turn:
            err("Choose a square containing your own piece.")
            return True
        session.select_piece(row, col)
        print_selection_near_prompt(session.board, row, col)
        print("Piece selected. BEFORE/AFTER lists will appear after you enter a destination.")
        if session.goal.active:
            print(goal_marks_selection(session.board, session.goal, row, col), end="")
        if session.distance_view:
            print(distance_selection(session.board, row, col), end="")
        return True

    chosen = Move(
        sr=session.selected_row,
        sc=session.selected_col,
        er=row,
        ec=col,
    )
    if not legal_move(session.board, chosen):
        err("Not a legal destination. Press N then Enter to select a different piece.")
        return True

    piece = session.board.grid[session.selected_row][session.selected_col]
    if piece.type == "P" and row in (0, 7):
        session.begin_promotion(chosen)
        print("PROMOTION: choose Q (Queen), R (Rook), B (Bishop), or N (Knight).")
        print("Type NEW to cancel and choose a different starting piece.")
        return True

    session.set_preview(chosen)
    return True


def handle_game_control(session: GameSession, cmd: str) -> Optional[str]:
    """quit / restart / resign / claim.

    Returns 'quit', 'handled', or None if not a game-control command.
    """
    lower = cmd.lower()

    if lower in ("quit", "exit"):
        return "quit"

    if lower == "restart":
        session.restart()
        print("Game restarted.")
        return "handled"

    if lower == "resign":
        winner = opposite(session.board.turn)
        print(f"{color_name(session.board.turn)} resigns. {color_name(winner)} wins.")
        return "quit"

    if lower == "claim":
        can_claim, draw_reason = session.board.claimable_draw()
        if can_claim:
            print(f"Game Over! Draw claimed by {draw_reason}.")
            return "quit"
        err("No draw claim is currently available.")
        return "handled"

    return None


# ---------------------------------------------------------------------------
# Analysis handlers
# ---------------------------------------------------------------------------

def handle_calc_report(session: GameSession, cmd: str) -> bool:
    if cmd.lower() != "r":
        return False
    if not session.preview_shown:
        err("No preview to report. Select a piece and preview a destination, then type R.")
    else:
        print(calc_report(session.board, session.tracker, session.preview_move), end="")
    return True


def handle_replies(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "replies" and not lower.startswith("replies "):
        return False

    if not session.preview_shown:
        err("No preview to answer. Select a piece and preview a destination, then type replies.")
        return True

    if lower == "replies":
        print(replies_report(session.board, session.tracker, session.preview_move), end="")
        return True

    reply_tok = cmd.split(None, 1)[1].strip()
    rep_move = parse_move_text(reply_tok)
    if not rep_move:
        err("Not a legal reply. Type replies to list them, or replies e7e5 for one.")
        return True

    detail = reply_detail(session.board, session.tracker, session.preview_move, rep_move)
    if detail:
        print(detail, end="")
    else:
        err("Not a legal reply. Type replies to list them, or replies e7e5 for one.")
    return True


def handle_loop(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "loop" and not lower.startswith("loop "):
        return False

    parts = cmd.split()
    usage = (
        "Type loop and a depth from 1 to 6, for example loop 3 "
        "(or loop 3 6 to also count pieces that can't move)."
    )
    if len(parts) not in (2, 3):
        err(usage)
        return True
    depth_val = parse_bounded_int(parts[1], 1, 6)
    if depth_val is None:
        err(usage)
        return True
    zero_k = 0
    if len(parts) == 3:
        zero_k = parse_bounded_int(parts[2], 1, 16)
        if zero_k is None:
            err(usage)
            return True
    if depth_val >= 5:
        print(
            f"Searching {depth_val} plies. This can take minutes "
            "(5 plies: about half a minute to a few minutes; 6: much longer)."
        )
    print(loop_report(session.board, depth_val, zero_k), end="")
    return True


def handle_goal(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "goal" and not lower.startswith("goal "):
        return False

    if lower == "goal":
        if session.goal.active:
            print(f"GOAL ACTIVE {goal_text(session.goal)} LIMIT {session.goal.limit} PASS")
        else:
            print("No goal is active. Type goal f7 2 (squares, then a limit of own moves 1 to 4).")
        return True

    if lower == "goal off":
        session.goal.active = False
        print("Goal cleared.")
        return True

    parsed = parse_goal(cmd[5:])
    if parsed:
        session.goal = parsed
        print(f"GOAL ACTIVE {goal_text(session.goal)} LIMIT {session.goal.limit} PASS")
    else:
        err(
            "Type goal, squares and a limit from 1 to 4, for example "
            "goal f7 2, goal f7 g7 h7 3 or goal king 2; goal off clears it."
        )
    return True


def handle_goal2(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "goal2" and not lower.startswith("goal2 "):
        return False

    if lower == "goal2":
        if session.second_goal.active:
            print(
                f"SECOND GOAL ACTIVE {goal_text(session.second_goal)} "
                f"LIMIT {session.second_goal.limit} PASS"
            )
        else:
            print(
                "No second goal is active. Type goal2 d5 2 "
                "(squares, then a limit of own moves 1 to 4)."
            )
        return True

    if lower == "goal2 off":
        session.second_goal.active = False
        print("Second goal cleared.")
        return True

    parsed = parse_goal(cmd[6:])
    if parsed:
        session.second_goal = parsed
        print(
            f"SECOND GOAL ACTIVE {goal_text(session.second_goal)} "
            f"LIMIT {session.second_goal.limit} PASS"
        )
    else:
        err(
            "Type goal2, squares and a limit from 1 to 4, "
            "for example goal2 d5 2; goal2 off clears it."
        )
    return True


def handle_distance(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower not in ("distance", "distance on", "distance off"):
        return False
    if " " in lower:
        session.distance_view = lower.split()[1] == "on"
    print(f"DISTANCE ORDER {'ON' if session.distance_view else 'OFF'}")
    return True


def handle_routes(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower == "routes":
        if not session.goal.active:
            err("No goal is active. Type goal f7 2 first, then routes.")
        else:
            second = session.second_goal if session.second_goal.active else None
            print(routes_report_with(session.board, session.goal, second), end="")
        return True

    if not lower.startswith("routes real"):
        return False

    parts = cmd.split()
    depth_val = parse_bounded_int(parts[2], 1, 6) if len(parts) == 3 else None
    if not session.goal.active:
        err("No goal is active. Type goal f7 2 first, then routes.")
    elif depth_val is None:
        err(
            "Type routes (PASS), or routes real and a depth from 1 to 6, "
            "for example routes real 3."
        )
    else:
        warn_slow_search(depth_val)
        print(routes_real_report(session.board, session.goal, depth_val), end="")
    return True


def handle_support(session: GameSession, cmd: str) -> bool:
    if cmd.lower() != "support":
        return False
    if not session.preview_shown:
        err("No preview to support. Select a piece and preview a destination, then type support.")
    else:
        print(support_report(session.board, session.preview_move), end="")
    return True


def handle_exchange(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "exchange" and not lower.startswith("exchange "):
        return False

    parts = cmd.split()
    usage = (
        "Type exchange, a square and a limit of captures from 1 to 8, "
        "for example exchange e5 4."
    )
    if len(parts) != 3:
        err(usage)
        return True

    parsed_sq = parse_square(parts[1])
    lim = parse_bounded_int(parts[2], 1, EXCHANGE_MAX)
    if parsed_sq is None or lim is None:
        err(usage)
        return True

    sq_idx = square_index(parsed_sq[0], parsed_sq[1])
    print(exchange_report(session.board, sq_idx, lim), end="")
    return True


def handle_order(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "order" and not lower.startswith("order "):
        return False

    parts = cmd.split()
    usage = "Type order and an exchange limit from 1 to 8, for example order 4."
    lim = parse_bounded_int(parts[1], 1, EXCHANGE_MAX) if len(parts) == 2 else None
    if lim is None:
        err(usage)
    else:
        print(order_report(session.board, lim), end="")
    return True


def handle_compare(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "compare" and not lower.startswith("compare "):
        return False

    parts = cmd.split()
    usage = (
        "Type compare, a depth from 1 to 5, then 2 to 6 different legal moves, "
        "for example compare 3 d1h5 d1f3 g1f3."
    )
    # depth + 2..COMPARE_MAX moves => 3 .. 1+COMPARE_MAX extra tokens after "compare"
    if not (4 <= len(parts) <= 2 + COMPARE_MAX):
        err(usage)
        return True

    depth_val = parse_bounded_int(parts[1], 1, 5)
    if depth_val is None:
        err(usage)
        return True

    cand_moves: List[Move] = []
    valid = True
    for m_str in parts[2:]:
        pm = parse_move_text(m_str)
        if not pm or not legal_move(session.board, pm) or pm in cand_moves:
            valid = False
            break
        cand_moves.append(pm)

    if not valid or not (2 <= len(cand_moves) <= COMPARE_MAX):
        err(usage)
        return True

    warn_slow_search(depth_val)
    active_goal = session.goal if session.goal.active else None
    print(
        compare_report(session.board, session.tracker, active_goal, depth_val, cand_moves),
        end="",
    )
    return True


def handle_risk(_session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower not in ("risk", "risk on", "risk off"):
        return False
    if " " in lower:
        set_goal_show_risk(lower.split()[1] == "on")
    print(f"AT-RISK {'ON' if get_goal_show_risk() else 'OFF'}")
    return True


def handle_trace(session: GameSession, cmd: str) -> bool:
    lower = cmd.lower()
    if lower != "trace" and not lower.startswith("trace "):
        return False

    arg_str = cmd[6:].strip() if lower.startswith("trace ") else ""
    ok, report_text, bad_ply = trace_report(session.board, session.tracker, arg_str)
    if ok:
        print(report_text, end="")
    else:
        err(
            f"Not a legal sequence (move {bad_ply}). "
            "Type trace and moves, for example trace e2e4 e7e5."
        )
    return True


def handle_memory(session: GameSession, cmd: str) -> bool:
    """memory -> print the five-move window (past + optional current preview)."""
    if cmd.lower() != "memory":
        return False
    session.memory.print_report()
    return True


# ---------------------------------------------------------------------------
# Command tables (dispatch order + help)
# ---------------------------------------------------------------------------

ANALYSIS_COMMANDS: Sequence[CommandSpec] = (
    CommandSpec("r", "calculator report for the current preview", handle_calc_report,
                usage="Preview a move, then type R."),
    CommandSpec("replies", "list or inspect opponent replies to the preview", handle_replies,
                usage="replies   or   replies e7e5"),
    CommandSpec("loop", "count positions to a given depth", handle_loop,
                usage="loop 3   or   loop 3 6"),
    CommandSpec("goal", "set / show / clear the primary goal", handle_goal,
                usage="goal f7 2 | goal off"),
    CommandSpec("distance", "show or set distance-order view", handle_distance,
                usage="distance | distance on | distance off"),
    CommandSpec("goal2", "set / show / clear the second goal", handle_goal2,
                usage="goal2 d5 2 | goal2 off"),
    CommandSpec("routes", "PASS routes for the active goal", handle_routes,
                usage="routes   or   routes real 3"),
    CommandSpec("support", "support report for the current preview", handle_support,
                usage="Preview a move, then type support."),
    CommandSpec("exchange", "exchange analysis on a square", handle_exchange,
                usage="exchange e5 4"),
    CommandSpec("order", "order report for exchange limit", handle_order,
                usage="order 4"),
    CommandSpec("compare", "compare several legal moves at a depth", handle_compare,
                usage="compare 3 d1h5 d1f3 g1f3"),
    CommandSpec("risk", "show or set AT-RISK display", handle_risk,
                usage="risk | risk on | risk off"),
    CommandSpec("trace", "step through a move sequence", handle_trace,
                usage="trace e2e4 e7e5"),
    CommandSpec("memory", "show the five-move window (past + current preview)", handle_memory,
                usage="memory"),
)

# Play / session commands (checked before analysis table in dispatch).
PLAY_HANDLERS: Sequence[Handler] = (
    handle_help,
    handle_cancel,
    handle_fen,
    handle_promotion_choice,
    handle_finalize,
    handle_discard_preview,
)

ALL_HELP_SPECS: Sequence[CommandSpec] = (
    CommandSpec("help", "show this help", handle_help, topic="move",
                usage="help   or   help goal"),
    CommandSpec("f", "finalize the previewed move", handle_finalize, topic="move"),
    CommandSpec("p", "clear preview, keep selected piece", handle_discard_preview, topic="move"),
    CommandSpec("n", "cancel selection / pick a new piece", handle_cancel, topic="move"),
    CommandSpec("fen", "print or load a FEN position", handle_fen, topic="move",
                usage="fen   or   fen <fen-text>"),
    *ANALYSIS_COMMANDS,
)


def dispatch_named_command(session: GameSession, cmd: str) -> bool:
    """Run the first matching play or analysis handler. True if handled."""
    for handler in PLAY_HANDLERS:
        if handler(session, cmd):
            return True
    for spec in ANALYSIS_COMMANDS:
        if spec.handler(session, cmd):
            return True
    return False


# ---------------------------------------------------------------------------
# Screen text (used by main)
# ---------------------------------------------------------------------------

def print_instructions(session: GameSession) -> None:
    """Tell the player what to type next."""
    print("How to move: select a piece, preview a destination, then type F to play it.")

    if session.step == Step.CHOOSE_PROMOTION:
        print("PROMOTION: choose the new piece")
        print("  Q = Queen   R = Rook   B = Bishop   N = Knight")
        print("  Type NEW to cancel and pick a different piece.")
    elif session.step == Step.PICK_PIECE:
        print("Step 1: enter a start square (example: e2), then press Enter.")
    elif session.step == Step.PICK_DESTINATION:
        print("Step 2: enter a destination (example: e4), then press Enter.")
        print("  BEFORE/AFTER lists will appear. The move is NOT played yet.")
        print("  Type N then Enter to pick a different piece.")
    else:
        print(f"PREVIEW READY: {move_label(session.preview_move)} (NOT played yet).")
        print("  F = Finalize (play the move)")
        print("  P = Pick a different destination for the same piece")
        print("  N = Pick a different piece")

    if session.step not in (Step.CONFIRM_PREVIEW, Step.CHOOSE_PROMOTION):
        print("Every move needs a preview, then F + Enter.")
        print("Other commands: restart, quit, claim, resign, help")


def build_prompt(session: GameSession) -> str:
    """Build the input prompt for the current step."""
    turn = color_name(session.board.turn)
    if session.step == Step.CHOOSE_PROMOTION:
        return f"{turn} - choose promotion (Q/R/B/N): "
    if session.step == Step.CONFIRM_PREVIEW:
        return f"{turn} - Enter command (F/P/N): "
    if session.step == Step.PICK_DESTINATION:
        return f"{turn} - enter destination square: "
    return f"{turn} - enter START square: "


def process_promotion_command(session: GameSession, cmd: str) -> Optional[str]:
    """Restrict input while a promotion piece must be chosen.

    Only Q/R/B/N, NEW/select none, and quit/exit/restart/resign/claim are allowed.
    This prevents help/fen/analysis/F/P from running mid-promotion.
    """
    lower = cmd.lower()

    if lower in ("new", "select none"):
        session.clear_selection()
        print("Selection cleared. Enter a new start square.")
        return None

    if lower in ("quit", "exit", "restart", "resign", "claim"):
        control = handle_game_control(session, cmd)
        if control == "quit":
            return "quit"
        return None

    # Q/R/B/N or a rejection message for anything else.
    handle_promotion_choice(session, cmd)
    return None


def process_command(session: GameSession, cmd: str) -> Optional[str]:
    """Handle one user command.

    Returns:
      None      -> keep playing (command handled or error shown)
      'quit'    -> end the game loop
      'unknown' -> caller should show the unknown-command message
    """
    if len(cmd) > MAX_COMMAND_CHARS:
        err(f"Command too long (max {MAX_COMMAND_CHARS} characters).")
        return None

    # Promotion must be answered before any other play/analysis command.
    if session.promotion_pending:
        return process_promotion_command(session, cmd)

    try:
        if dispatch_named_command(session, cmd):
            return None

        if handle_square_entry(session, cmd):
            return None

        control = handle_game_control(session, cmd)
        if control == "quit":
            return "quit"
        if control == "handled":
            return None

        if (
            len(cmd) in (4, 5)
            or cmd.lower().startswith("offer ")
            or cmd.lower().startswith("claim ")
        ):
            err(
                "Direct moves are disabled. Enter the START square, then the destination, "
                "review BEFORE/AFTER, and press F + Enter."
            )
            return None

        return "unknown"
    except Exception as exc:
        # Analysis helpers can be heavy; never let an unexpected error kill the game loop.
        err(f"Command failed: {sanitize_display_text(str(exc), 120)}")
        return None
