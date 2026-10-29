"""Study/analysis tools, split into small modules.

common    shared types and helpers (Goal, RouteVector, risk toggle, ...)
calc      Stage 3A  CALC report
replies   Stage 3B  REPLIES report
search    Stage 3C  LOOP and TRACE reports
goals     Stage 3D  goals, routes, marks, distance order, support
exchange  Stage 3E/3F  exchanges, move order, compare
"""

from .common import (
    GoalCondition, Goal, RealResult, MaterialResult, RouteVector,
    set_goal_show_risk, get_goal_show_risk,
    move_distance, order_label, pass_moves, pass_play, pieces_on_square,
)
from .calc import (
    zero_move_cause, linked, report_mates, count_mate_in_one, calc_report,
)
from .replies import replies_report, reply_detail
from .search import (
    zero_move_pieces, mate_forced, first_move_forces, loop_report, trace_report,
)
from .goals import (
    goal_squares, goal_text, goal_holds, piece_distance, side_within,
    side_distance, parse_goal, mark_dominated, routes_report_with,
    second_from, second_goal_report, goal_marks_selection, goal_marks_after,
    distance_lines, distance_selection, distance_after, routes_real_report,
    support_report,
)
from .exchange import (
    piece_value, captured_type, captures_on, exchange_value,
    first_capture_class, material_text, exchange_report, order_report,
    compare_report,
)

__all__ = [
    # common
    "GoalCondition", "Goal", "RealResult", "MaterialResult", "RouteVector",
    "set_goal_show_risk", "get_goal_show_risk",
    "move_distance", "order_label", "pass_moves", "pass_play", "pieces_on_square",
    # calc
    "zero_move_cause", "linked", "report_mates", "count_mate_in_one", "calc_report",
    # replies
    "replies_report", "reply_detail",
    # search
    "zero_move_pieces", "mate_forced", "first_move_forces", "loop_report", "trace_report",
    # goals
    "goal_squares", "goal_text", "goal_holds", "piece_distance", "side_within",
    "side_distance", "parse_goal", "mark_dominated", "routes_report_with",
    "second_from", "second_goal_report", "goal_marks_selection", "goal_marks_after",
    "distance_lines", "distance_selection", "distance_after", "routes_real_report",
    "support_report",
    # exchange
    "piece_value", "captured_type", "captures_on", "exchange_value",
    "first_capture_class", "material_text", "exchange_report", "order_report",
    "compare_report",
]
