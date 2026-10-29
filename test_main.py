"""CLI / GameSession tests (non-interactive)."""

import io
import contextlib
import unittest

from chess_engine.cli_session import GameSession, Step
from chess_engine.cli_commands import (
    process_command,
    handle_square_entry,
    handle_finalize,
    handle_cancel,
    handle_promotion_choice,
    handle_discard_preview,
    handle_exchange,
    handle_order,
    handle_compare,
    handle_goal,
    handle_goal2,
    handle_game_control,
    handle_help,
    print_help,
    move_label,
)
from chess_engine.analysis import get_goal_show_risk


class TestMainCli(unittest.TestCase):

    def setUp(self) -> None:
        self.buf = io.StringIO()

    def run_cmd(self, session: GameSession, cmd: str):
        with contextlib.redirect_stdout(self.buf):
            return process_command(session, cmd)

    def test_select_preview_finalize(self) -> None:
        s = GameSession()
        self.assertEqual(s.step, Step.PICK_PIECE)

        with contextlib.redirect_stdout(self.buf):
            self.assertTrue(handle_square_entry(s, "e2"))
        self.assertEqual(s.step, Step.PICK_DESTINATION)
        self.assertTrue(s.has_selection())

        with contextlib.redirect_stdout(self.buf):
            self.assertTrue(handle_square_entry(s, "e4"))
        self.assertEqual(s.step, Step.CONFIRM_PREVIEW)
        self.assertEqual(move_label(s.preview_move), "e2 -> e4")

        with contextlib.redirect_stdout(self.buf):
            self.assertTrue(handle_finalize(s, "F"))
        self.assertEqual(s.step, Step.PICK_PIECE)
        self.assertEqual(s.board.grid[4][4].type, "P")

    def test_cancel_n(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "e2")
            handle_cancel(s, "n")
        self.assertEqual(s.step, Step.PICK_PIECE)
        self.assertFalse(s.has_selection())

    def test_discard_preview_keeps_piece(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "e2")
            handle_square_entry(s, "e4")
            handle_discard_preview(s, "p")
        self.assertEqual(s.step, Step.PICK_DESTINATION)
        self.assertTrue(s.has_selection())

    def test_promotion_n_is_knight_not_cancel(self) -> None:
        s = GameSession()
        ok, _ = s.board.load_fen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        self.assertTrue(ok)
        s.tracker.init_from_board(s.board)

        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "a7")
            handle_square_entry(s, "a8")
        self.assertEqual(s.step, Step.CHOOSE_PROMOTION)

        with contextlib.redirect_stdout(self.buf):
            # bare n must not cancel while promoting
            self.assertFalse(handle_cancel(s, "n"))
            self.assertTrue(handle_promotion_choice(s, "N"))
        self.assertEqual(s.step, Step.CONFIRM_PREVIEW)
        self.assertEqual(s.preview_move.promotion, "N")

        with contextlib.redirect_stdout(self.buf):
            handle_finalize(s, "f")
        self.assertEqual(s.board.grid[0][0].type, "N")

    def test_new_clears_promotion(self) -> None:
        s = GameSession()
        s.board.load_fen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        s.tracker.init_from_board(s.board)
        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "a7")
            handle_square_entry(s, "a8")
            handle_cancel(s, "NEW")
        self.assertEqual(s.step, Step.PICK_PIECE)

    def test_exchange_order_compare_no_nameerror(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            self.assertTrue(handle_exchange(s, "exchange e5 4"))
            self.assertTrue(handle_order(s, "order 4"))
            self.assertTrue(handle_compare(s, "compare 1 e2e4 d2d4"))

    def test_goal_vs_goal2(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_goal(s, "goal f7 2")
            handle_goal2(s, "goal2 d5 2")
        self.assertTrue(s.goal.active)
        self.assertTrue(s.second_goal.active)
        self.assertFalse(handle_goal(s, "goal2 d5 2"))

    def test_restart_clears_goals_and_risk(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_goal(s, "goal f7 2")
            process_command(s, "risk on")
            handle_game_control(s, "restart")
        self.assertFalse(s.goal.active)
        self.assertFalse(s.second_goal.active)
        self.assertFalse(get_goal_show_risk())
        self.assertEqual(s.step, Step.PICK_PIECE)

    def test_direct_move_still_blocked(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            result = process_command(s, "e2e4")
        self.assertIsNone(result)  # handled as blocked direct move, not unknown
        self.assertIn("Direct moves are disabled", self.buf.getvalue())

    def test_help_command(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            self.assertTrue(handle_help(s, "help"))
            self.assertTrue(handle_help(s, "help goal"))
            print_help("distance")
        out = self.buf.getvalue()
        self.assertIn("how to move", out)
        self.assertIn("goal / goal2", out)
        self.assertIn("distance", out)

    def test_illegal_destination_keeps_selection(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "e2")
            handle_square_entry(s, "e5")
        self.assertEqual(s.step, Step.PICK_DESTINATION)
        self.assertTrue(s.has_selection())
        self.assertFalse(s.preview_shown)

    def test_quit(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            self.assertEqual(handle_game_control(s, "quit"), "quit")

    def test_promotion_blocks_help_and_fen(self) -> None:
        s = GameSession()
        s.board.load_fen("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        s.tracker.init_from_board(s.board)
        with contextlib.redirect_stdout(self.buf):
            handle_square_entry(s, "a7")
            handle_square_entry(s, "a8")
            self.assertEqual(s.step, Step.CHOOSE_PROMOTION)
            process_command(s, "help")
            self.assertEqual(s.step, Step.CHOOSE_PROMOTION)
            process_command(s, "fen")
            self.assertEqual(s.step, Step.CHOOSE_PROMOTION)
            process_command(s, "loop 1")
            self.assertEqual(s.step, Step.CHOOSE_PROMOTION)
        self.assertIn("Choose Q, R, B or N", self.buf.getvalue())

    def test_fen_load_clears_goals(self) -> None:
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            handle_goal(s, "goal f7 2")
            process_command(
                s,
                "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            )
        self.assertFalse(s.goal.active)
        self.assertEqual(s.step, Step.PICK_PIECE)

    def test_command_too_long_rejected(self) -> None:
        from chess_engine.cli_session import MAX_COMMAND_CHARS
        s = GameSession()
        with contextlib.redirect_stdout(self.buf):
            result = process_command(s, "x" * (MAX_COMMAND_CHARS + 1))
        self.assertIsNone(result)
        self.assertIn("too long", self.buf.getvalue())

    def test_bounded_int_rejects_garbage(self) -> None:
        from chess_engine.cli_session import parse_bounded_int
        self.assertIsNone(parse_bounded_int("-1", 1, 6))
        self.assertIsNone(parse_bounded_int("0", 1, 6))
        self.assertIsNone(parse_bounded_int("7", 1, 6))
        self.assertIsNone(parse_bounded_int("99999999999999999999", 1, 6))
        self.assertEqual(parse_bounded_int("3", 1, 6), 3)


if __name__ == "__main__":
    unittest.main()
