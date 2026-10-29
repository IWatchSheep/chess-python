"""Comprehensive unit tests for chess_engine."""

import unittest
from chess_engine.constants import (
    WHITE, BLACK, EMPTY,
    square_index, parse_square, square_text
)
from chess_engine.piece import Piece
from chess_engine.move import Move, parse_move_text
from chess_engine.board import Board
from chess_engine.movegen import (
    generate_moves, sorted_moves, legal_move, make_move,
    is_in_check, game_over
)
from chess_engine.tracker import Tracker
from chess_engine.analysis import (
    Goal, parse_goal, calc_report, replies_report, loop_report,
    exchange_report, order_report, routes_report_with
)


class TestChessEngine(unittest.TestCase):

    def setUp(self):
        self.board = Board()
        self.board.reset_board()

    def test_initial_position(self):
        self.assertEqual(len(sorted_moves(self.board)), 20)
        self.assertEqual(self.board.to_fen(), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.assertFalse(is_in_check(self.board, WHITE))
        self.assertFalse(is_in_check(self.board, BLACK))

    def test_fools_mate(self):
        # 1. f3 e5 2. g4 Qh4#
        m1 = parse_move_text("f2f3")
        m2 = parse_move_text("e7e5")
        m3 = parse_move_text("g2g4")
        m4 = parse_move_text("d8h4")

        self.assertTrue(legal_move(self.board, m1))
        make_move(self.board, m1)
        self.assertTrue(legal_move(self.board, m2))
        make_move(self.board, m2)
        self.assertTrue(legal_move(self.board, m3))
        make_move(self.board, m3)
        self.assertTrue(legal_move(self.board, m4))
        make_move(self.board, m4)

        self.assertTrue(is_in_check(self.board, WHITE))
        is_over, is_stalemate, reason = game_over(self.board)
        self.assertTrue(is_over)
        self.assertFalse(is_stalemate)
        self.assertIsNone(reason)  # Checkmate

    def test_scholar_mate(self):
        # 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
        moves = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
        for uci in moves:
            m = parse_move_text(uci)
            self.assertTrue(legal_move(self.board, m), f"Move {uci} was expected to be legal")
            make_move(self.board, m)

        is_over, is_stalemate, _ = game_over(self.board)
        self.assertTrue(is_over)
        self.assertFalse(is_stalemate)
        self.assertTrue(is_in_check(self.board, BLACK))

    def test_castling(self):
        # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O
        for uci in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]:
            make_move(self.board, parse_move_text(uci))

        # White kingside castle: e1g1
        castle_ks = parse_move_text("e1g1")
        self.assertTrue(legal_move(self.board, castle_ks))
        make_move(self.board, castle_ks)

        # King should be on g1 (row 7, col 6) and Rook on f1 (row 7, col 5)
        self.assertEqual(self.board.grid[7][6].type, 'K')
        self.assertEqual(self.board.grid[7][5].type, 'R')
        self.assertTrue(self.board.white_king_moved)
        self.assertTrue(self.board.white_rook_h_moved)

    def test_en_passant(self):
        # 1. e4 a6 2. e5 d5 3. exd6
        make_move(self.board, parse_move_text("e2e4"))
        make_move(self.board, parse_move_text("a7a6"))
        make_move(self.board, parse_move_text("e4e5"))
        make_move(self.board, parse_move_text("d7d5"))

        # En passant target square should be d6 (row 2, col 3)
        self.assertEqual((self.board.ep_row, self.board.ep_col), (2, 3))
        ep_move = parse_move_text("e5d6")
        self.assertTrue(legal_move(self.board, ep_move))
        make_move(self.board, ep_move)

        # Captured pawn on d5 (row 3, col 3) should be empty
        self.assertTrue(self.board.grid[3][3].is_empty)
        # White pawn should be on d6 (row 2, col 3)
        self.assertEqual(self.board.grid[2][3].type, 'P')
        self.assertEqual(self.board.grid[2][3].color, WHITE)

    def test_fen_roundtrip(self):
        fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ok, reason = self.board.load_fen(fen_start)
        self.assertTrue(ok)
        self.assertEqual(self.board.to_fen(), fen_start)

        # Custom FEN
        fen_custom = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 5"
        ok, reason = self.board.load_fen(fen_custom)
        self.assertTrue(ok, f"Failed loading valid FEN: {reason}")
        self.assertEqual(self.board.to_fen(), fen_custom)

    def test_repetition_threefold(self):
        # 1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 Ng8
        moves = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
        for uci in moves:
            make_move(self.board, parse_move_text(uci))
            self.board.record_position()

        can_claim, reason = self.board.claimable_draw()
        self.assertTrue(can_claim)
        self.assertEqual(reason, "threefold repetition")

    def test_analysis_reports(self):
        tracker = Tracker(self.board)
        e2e4 = parse_move_text("e2e4")

        # Stage 3A Calc report
        calc_out = calc_report(self.board, tracker, e2e4)
        self.assertIn("CALC BEGIN e2e4", calc_out)
        self.assertIn("MOVED White P e2 e4", calc_out)
        self.assertIn("CALC END", calc_out)

        # Stage 3B Replies report
        rep_out = replies_report(self.board, tracker, e2e4)
        self.assertIn("REPLIES BEGIN e2e4", rep_out)
        self.assertIn("SUMMARY REPLIES 20", rep_out)
        self.assertIn("REPLIES END", rep_out)

        # Stage 3C Loop report
        loop_out = loop_report(self.board, depth=1)
        self.assertIn("LOOP BEGIN White DEPTH 1", loop_out)
        self.assertIn("PLY 1 POSITIONS 20", loop_out)
        self.assertIn("LOOP END", loop_out)

        # Stage 3D Goal & PASS routes
        goal = parse_goal("e4 1")
        self.assertIsNotNone(goal)
        routes_out = routes_report_with(self.board, goal)
        self.assertIn("ROUTES BEGIN White GOAL e4 LIMIT 1 PASS", routes_out)

        # Stage 3E Exchange & Order
        order_out = order_report(self.board, limit=2)
        self.assertIn("ORDER BEGIN White EXCHANGE LIMIT 2", order_out)


if __name__ == "__main__":
    unittest.main()
