"""Main entry point for two-player interactive chess.

How a move works (always three steps):
  1. Type a start square   (example: e2)
  2. Type a destination    (example: e4)  -> preview appears, nothing is played yet
  3. Type F                -> the move is finalized / played

Type N at any time to cancel and pick a different piece.
Type help for a command list.
"""

from chess_engine.constants import WHITE, BLACK, CYAN, RESET
from chess_engine.movegen import is_in_check, has_king, game_over
from chess_engine.ui import display, print_selection_near_prompt, enable_windows_colors
from chess_engine.cli_session import GameSession, err
from chess_engine.cli_commands import (
    print_instructions,
    build_prompt,
    process_command,
)


def main() -> None:
    enable_windows_colors()
    print("=== Simple 2-Player Chess ===")

    session = GameSession()

    while True:
        board = session.board

        # Both kings must exist (guards against bad FEN / broken state).
        if not has_king(board, WHITE) or not has_king(board, BLACK):
            print("Invalid position: both kings must be on the board.")
            break

        display(board, session.selected_row, session.selected_col)

        is_over, is_stalemate, draw_reason = game_over(board)
        if is_over:
            if is_stalemate:
                print("Game Over! Stalemate.")
            elif draw_reason:
                print(f"Game Over! Draw by {draw_reason}.")
            else:
                # Side to move cannot move and is in check -> the other side won.
                winner = "Black" if board.turn == WHITE else "White"
                print(f"Checkmate! {winner} wins!")
            break

        if is_in_check(board, board.turn):
            print(f"{CYAN}Your king is in check!{RESET}")

        print_instructions(session)
        print_selection_near_prompt(board, session.selected_row, session.selected_col)

        try:
            line = input(build_prompt(session)).strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            break

        if not line:
            continue

        try:
            result = process_command(session, line)
        except Exception as exc:
            # process_command already catches most errors; keep the loop alive.
            err(f"Unexpected error: {exc}")
            continue

        if result == "quit":
            break
        if result == "unknown":
            err(
                "Unknown command. Enter a square, or use F, P, N, "
                "restart, quit, claim or resign."
            )


if __name__ == "__main__":
    main()
