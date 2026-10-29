"""How pieces move: attacks, legal moves, and applying a move to the board.

Beginner map:
  piece_attacks / path_clear  — can this piece hit that square?
  pseudo_legal / legal_move   — is this Move allowed right now?
  generate_moves              — every legal move for the side to play
  make_move                   — actually play it (updates clocks, EP, turn)
"""

from typing import List, Optional, Tuple, TYPE_CHECKING
from .constants import (
    BOARD_SIZE, Color, EMPTY, WHITE, BLACK,
    WHITE_PAWN_START_ROW, BLACK_PAWN_START_ROW,
    KING_START_COL, CASTLE_KINGSIDE_KING_DEST_COL, CASTLE_QUEENSIDE_KING_DEST_COL,
    CASTLE_KINGSIDE_ROOK_DEST_COL, CASTLE_QUEENSIDE_ROOK_DEST_COL,
    MAX_SLIDE_STEPS,
    in_bounds, opposite, home_row_for, rook_col_for,
)
from .piece import Piece, empty_piece
from .move import Move

if TYPE_CHECKING:
    from .board import Board


def pawn_direction(color: Color) -> int:
    """Returns step direction for pawn movement: -1 for White, +1 for Black."""
    return -1 if color == WHITE else 1


def is_knight_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) matches an L-shaped knight jump."""
    r, c = abs(dr), abs(dc)
    return (r == 2 and c == 1) or (r == 1 and c == 2)


def is_diagonal_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is diagonal."""
    return abs(dr) == abs(dc)


def is_straight_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is orthogonal (along rank or file)."""
    return dr == 0 or dc == 0


def is_queen_move(dr: int, dc: int) -> bool:
    """Checks whether (dr, dc) is straight or diagonal."""
    return is_straight_move(dr, dc) or is_diagonal_move(dr, dc)


def path_clear(board: 'Board', sr: int, sc: int, er: int, ec: int) -> bool:
    """True if every square strictly between start and end is empty.

    Only works for rook/bishop/queen rays (straight or diagonal).
    Caps steps so a bad step vector cannot loop forever.
    """
    if sr == er and sc == ec:
        return False

    step_r = 0 if er == sr else (1 if er > sr else -1)
    step_c = 0 if ec == sc else (1 if ec > sc else -1)

    delta_r = abs(er - sr)
    delta_c = abs(ec - sc)
    straight = step_r == 0 or step_c == 0
    diagonal = delta_r == delta_c
    if not straight and not diagonal:
        return False

    curr_r = sr + step_r
    curr_c = sc + step_c
    for _ in range(MAX_SLIDE_STEPS):
        if curr_r == er and curr_c == ec:
            return True
        if not in_bounds(curr_r, curr_c):
            return False
        if not board.grid[curr_r][curr_c].is_empty:
            return False
        curr_r += step_r
        curr_c += step_c

    return False


def piece_attacks(board: 'Board', sr: int, sc: int, tr: int, tc: int) -> bool:
    """Determines whether a piece on (sr, sc) attacks target square (tr, tc)."""
    p = board.grid[sr][sc]
    if p.is_empty:
        return False
    if sr == tr and sc == tc:
        return False

    dr = tr - sr
    dc = tc - sc

    ptype = p.type
    if ptype == 'P':
        return abs(dc) == 1 and dr == pawn_direction(p.color)
    elif ptype == 'N':
        return is_knight_move(dr, dc)
    elif ptype == 'B':
        return is_diagonal_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'R':
        return is_straight_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'Q':
        return is_queen_move(dr, dc) and path_clear(board, sr, sc, tr, tc)
    elif ptype == 'K':
        return abs(dr) <= 1 and abs(dc) <= 1
    return False


def square_attacked(board: 'Board', r: int, c: int, by: Color) -> bool:
    """Determines whether square (r, c) is attacked by any piece of color `by`."""
    for check_r in range(BOARD_SIZE):
        for check_c in range(BOARD_SIZE):
            attacker = board.grid[check_r][check_c]
            if attacker.color == by:
                if piece_attacks(board, check_r, check_c, r, c):
                    return True
    return False


def count_attackers(board: 'Board', r: int, c: int, by: Color) -> int:
    """Counts how many pieces of color `by` attack square (r, c)."""
    attackers = 0
    for cr in range(BOARD_SIZE):
        for cc in range(BOARD_SIZE):
            if board.grid[cr][cc].color == by and piece_attacks(board, cr, cc, r, c):
                attackers += 1
    return attackers


def find_king(board: 'Board', side: Color) -> Optional[Tuple[int, int]]:
    """Locates the King of the specified color on the board."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board.grid[r][c]
            if p.type == 'K' and p.color == side:
                return r, c
    return None


def has_king(board: 'Board', side: Color) -> bool:
    """Returns True if the specified side has a King on the board."""
    return find_king(board, side) is not None


def is_in_check(board: 'Board', side: Color) -> bool:
    """Checks whether the King of the specified side is currently under attack."""
    pos = find_king(board, side)
    if not pos:
        return False
    return square_attacked(board, pos[0], pos[1], opposite(side))


def can_castle(board: 'Board', move: Move, side: Color) -> bool:
    """Validates whether the proposed castling move satisfies all chess rules."""
    home_row = home_row_for(side)
    king_moved = board.white_king_moved if side == WHITE else board.black_king_moved
    enemy = opposite(side)
    castle_kingside = move.is_kingside_castle

    rook_col = rook_col_for(castle_kingside)
    transit_col = CASTLE_KINGSIDE_ROOK_DEST_COL if castle_kingside else CASTLE_QUEENSIDE_ROOK_DEST_COL
    dest_col = CASTLE_KINGSIDE_KING_DEST_COL if castle_kingside else CASTLE_QUEENSIDE_KING_DEST_COL

    # King must start on e-file home square and land on the castling destination.
    if (
        move.sr != home_row
        or move.er != home_row
        or move.sc != KING_START_COL
        or move.ec != dest_col
        or king_moved
    ):
        return False

    rook_moved = (
        (board.white_rook_h_moved if castle_kingside else board.white_rook_a_moved)
        if side == WHITE else
        (board.black_rook_h_moved if castle_kingside else board.black_rook_a_moved)
    )

    corner_piece = board.grid[home_row][rook_col]
    if rook_moved or corner_piece.type != 'R' or corner_piece.color != side:
        return False

    first_empty = 5 if castle_kingside else 1
    last_empty = 6 if castle_kingside else 3
    for col in range(first_empty, last_empty + 1):
        if not board.grid[home_row][col].is_empty:
            return False

    if square_attacked(board, home_row, transit_col, enemy) or \
       square_attacked(board, home_row, dest_col, enemy):
        return False

    return True


def move_is_en_passant(board: 'Board', move: Move, piece: Piece) -> bool:
    """Returns True if move made by piece is an en passant capture."""
    if piece.type != "P":
        return False
    if not in_bounds(move.sr, move.sc) or not in_bounds(move.er, move.ec):
        return False
    if not in_bounds(move.sr, move.ec):
        return False
    matches_ep = move.er == board.ep_row and move.ec == board.ep_col
    dest_empty = board.grid[move.er][move.ec].is_empty
    side_pawn = board.grid[move.sr][move.ec]
    enemy_pawn = side_pawn.type == "P" and side_pawn.color == opposite(piece.color)
    return matches_ep and dest_empty and enemy_pawn


def pawn_move_is_pseudo_legal(board: 'Board', move: Move, pawn: Piece, target: Piece) -> bool:
    """Validates the geometric rules for pawn moves."""
    direction = pawn_direction(pawn.color)
    starting_row = WHITE_PAWN_START_ROW if pawn.color == WHITE else BLACK_PAWN_START_ROW
    row_change = move.er - move.sr
    col_change = move.ec - move.sc

    # Straight forward
    if col_change == 0 and target.is_empty:
        if row_change == direction:
            return True
        intermediate_row = move.sr + direction
        if (
            row_change == 2 * direction
            and move.sr == starting_row
            and in_bounds(intermediate_row, move.sc)
            and board.grid[intermediate_row][move.sc].is_empty
        ):
            return True

    # Diagonal captures
    if abs(col_change) != 1 or row_change != direction:
        return False

    if not target.is_empty:
        return True

    # En passant
    if not in_bounds(move.sr, move.ec):
        return False
    lands_on_ep = move.er == board.ep_row and move.ec == board.ep_col
    side_pawn = board.grid[move.sr][move.ec]
    enemy_pawn_present = side_pawn.type == "P" and side_pawn.color == opposite(pawn.color)
    return lands_on_ep and enemy_pawn_present


def king_move_is_pseudo_legal(board: 'Board', move: Move) -> bool:
    """Validates king motion: 1 square in any direction, or castling."""
    if piece_attacks(board, move.sr, move.sc, move.er, move.ec):
        return True

    is_two_horizontal = (move.sr == move.er and abs(move.ec - move.sc) == 2)
    if not is_two_horizontal:
        return False

    if is_in_check(board, board.turn):
        return False

    return can_castle(board, move, board.turn)


def promotion_is_valid(move: Move, piece: Piece) -> bool:
    """Checks that pawn promotion specifies a valid piece when reaching the end rank."""
    if not move.promotion or move.promotion == '\0':
        return True
    is_pawn = (piece.type == 'P')
    reached_end = (move.er == 0 or move.er == 7)
    valid_char = move.promotion in ("Q", "R", "B", "N")
    return is_pawn and reached_end and valid_char


def pseudo_legal(board: 'Board', m: Move) -> bool:
    """Checks whether move m is geometrically valid for the piece type."""
    if not in_bounds(m.sr, m.sc) or not in_bounds(m.er, m.ec):
        return False

    piece = board.grid[m.sr][m.sc]
    target = board.grid[m.er][m.ec]

    if piece.color != board.turn:
        return False
    if target.color == board.turn:
        return False
    if target.type == 'K':
        return False
    if not promotion_is_valid(m, piece):
        return False

    if piece.type == 'P':
        return pawn_move_is_pseudo_legal(board, m, piece, target)
    if piece.type == 'K':
        return king_move_is_pseudo_legal(board, m)

    return piece_attacks(board, m.sr, m.sc, m.er, m.ec)


def apply_move_to_board(board: 'Board', move: Move) -> None:
    """Update only the piece grid for this move (EP, castle rook, promote).

    Does not change turn, clocks, or castling flags — make_move does that.
    """
    if not in_bounds(move.sr, move.sc) or not in_bounds(move.er, move.ec):
        return

    piece = board.grid[move.sr][move.sc]

    # En passant: remove the pawn that was jumped past.
    if move_is_en_passant(board, move, piece):
        if in_bounds(move.sr, move.ec):
            board.grid[move.sr][move.ec] = empty_piece()

    # Castling: also slide the rook.
    if piece.type == "K" and abs(move.ec - move.sc) == 2:
        king_side = move.ec > move.sc
        rook_from_col = rook_col_for(king_side)
        rook_to_col = (
            CASTLE_KINGSIDE_ROOK_DEST_COL if king_side else CASTLE_QUEENSIDE_ROOK_DEST_COL
        )
        board.grid[move.sr][rook_to_col] = board.grid[move.sr][rook_from_col]
        board.grid[move.sr][rook_from_col] = empty_piece()

    board.grid[move.sr][move.sc] = empty_piece()
    board.grid[move.er][move.ec] = piece

    # Pawn on last rank becomes the chosen piece (default Queen).
    if piece.type == "P" and move.er in (0, 7):
        promo_type = (
            "Q" if (not move.promotion or move.promotion == "\0") else move.promotion
        )
        board.grid[move.er][move.ec] = Piece(type=promo_type, color=piece.color)


def legal_move(board: 'Board', move: Move) -> bool:
    """Determines whether a move is fully legal in chess."""
    if not pseudo_legal(board, move):
        return False

    after_move = board.clone()
    apply_move_to_board(after_move, move)
    return not is_in_check(after_move, board.turn)


def mark_rook_at_home_square(board: 'Board', row: int, col: int, side: Color) -> None:
    """Revokes castling rights if a rook moves or is captured on its home square."""
    home_row = home_row_for(side)
    if row != home_row or (col != 0 and col != 7):
        return
    is_kingside = (col == 7)
    if side == WHITE:
        if is_kingside:
            board.white_rook_h_moved = True
        else:
            board.white_rook_a_moved = True
    else:
        if is_kingside:
            board.black_rook_h_moved = True
        else:
            board.black_rook_a_moved = True


def update_castle_state(board: 'Board', piece: Piece, m: Move) -> None:
    """Updates the board's castling flags when a king or rook moves."""
    if piece.type == 'K' and abs(m.ec - m.sc) == 2:
        is_ks = m.is_kingside_castle
        if piece.color == WHITE:
            if is_ks: board.white_rook_h_moved = True
            else: board.white_rook_a_moved = True
        else:
            if is_ks: board.black_rook_h_moved = True
            else: board.black_rook_a_moved = True

    if piece.type == 'K':
        if piece.color == WHITE:
            board.white_king_moved = True
        else:
            board.black_king_moved = True

    if piece.type == 'R':
        mark_rook_at_home_square(board, m.sr, m.sc, piece.color)


def make_move(board: 'Board', m: Move) -> None:
    """Play move on the board: pieces, castling rights, EP, clocks, turn.

    Caller must already know the move is legal. Does not append to history;
    the CLI calls board.record_position() after a finalized move.
    """
    if not in_bounds(m.sr, m.sc) or not in_bounds(m.er, m.ec):
        return

    piece = board.grid[m.sr][m.sc]
    target = board.grid[m.er][m.ec]
    pawn_move = piece.type == "P"
    capture = (not target.is_empty) or move_is_en_passant(board, m, piece)

    # Capturing a rook on its home square removes that castling right.
    if target.type == "R":
        mark_rook_at_home_square(board, m.er, m.ec, target.color)

    update_castle_state(board, piece, m)
    apply_move_to_board(board, m)

    # Double pawn push sets the en-passant target; anything else clears it.
    if pawn_move and abs(m.er - m.sr) == 2:
        board.ep_row = (m.sr + m.er) // 2
        board.ep_col = m.sc
    else:
        board.ep_row = -1
        board.ep_col = -1

    # Pawn move or capture resets the 50-move clock and repetition list.
    if pawn_move or capture:
        board.halfmove_clock = 0
        board.history = []
    else:
        board.halfmove_clock += 1

    if board.turn == BLACK:
        board.fullmove_number += 1

    board.turn = opposite(board.turn)


def consider_move(board: 'Board', moves: List[Move], sr: int, sc: int, er: int, ec: int) -> None:
    """Considers candidate move from (sr, sc) to (er, ec) and appends if legal."""
    if not in_bounds(er, ec):
        return

    m = Move(sr=sr, sc=sc, er=er, ec=ec)
    if not legal_move(board, m):
        return

    # Check for pawn promotion
    if board.grid[sr][sc].type == 'P' and (er == 0 or er == 7):
        for promo in ("Q", "R", "B", "N"):
            moves.append(Move(sr=sr, sc=sc, er=er, ec=ec, promotion=promo))
    else:
        moves.append(m)


def generate_sliding_moves(board: 'Board', moves: List[Move], row: int, col: int, directions: List[Tuple[int, int]]) -> None:
    """Generates sliding moves along rays."""
    for dr, dc in directions:
        step = 1
        while True:
            er = row + dr * step
            ec = col + dc * step
            if not in_bounds(er, ec):
                break
            consider_move(board, moves, row, col, er, ec)
            if not board.grid[er][ec].is_empty:
                break
            step += 1


def generate_pawn_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates all candidate moves for the pawn at (row, col)."""
    d = pawn_direction(board.grid[row][col].color)
    consider_move(board, moves, row, col, row + d, col)
    consider_move(board, moves, row, col, row + 2 * d, col)
    consider_move(board, moves, row, col, row + d, col - 1)
    consider_move(board, moves, row, col, row + d, col + 1)


def generate_knight_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates knight jumps."""
    jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in jumps:
        consider_move(board, moves, row, col, row + dr, col + dc)


def generate_king_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates king moves and castling."""
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            consider_move(board, moves, row, col, row + dr, col + dc)

    consider_move(board, moves, row, col, row, col + 2)
    consider_move(board, moves, row, col, row, col - 2)


def generate_piece_moves(board: 'Board', moves: List[Move], row: int, col: int) -> None:
    """Generates all legal moves for a piece at (row, col)."""
    ptype = board.grid[row][col].type
    if ptype == 'P':
        generate_pawn_moves(board, moves, row, col)
    elif ptype == 'N':
        generate_knight_moves(board, moves, row, col)
    elif ptype == 'B':
        generate_sliding_moves(board, moves, row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    elif ptype == 'R':
        generate_sliding_moves(board, moves, row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    elif ptype == 'Q':
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        generate_sliding_moves(board, moves, row, col, directions)
    elif ptype == 'K':
        generate_king_moves(board, moves, row, col)


def generate_moves(board: 'Board') -> List[Move]:
    """Generates all legal moves for the player whose turn it currently is."""
    moves: List[Move] = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c].color == board.turn:
                generate_piece_moves(board, moves, r, c)
    return moves


def sorted_moves(board: 'Board') -> List[Move]:
    """Generates and canonically sorts all legal moves."""
    moves = generate_moves(board)
    moves.sort()
    return moves


def legal_destination_map(board: 'Board', row: int, col: int, side_to_move: Color) -> List[List[bool]]:
    """Returns an 8x8 boolean matrix where [r][c] is True if piece can legally move to (r, c)."""
    destinations = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    if not in_bounds(row, col) or board.grid[row][col].is_empty:
        return destinations

    view = board.clone()
    view.turn = side_to_move
    moves = generate_moves(view)
    for m in moves:
        if m.sr == row and m.sc == col:
            destinations[m.er][m.ec] = True
    return destinations


def game_over(board: 'Board') -> Tuple[bool, bool, Optional[str]]:
    """Determines if the game has ended.
    Returns: (is_game_over, is_stalemate, draw_reason)
    """
    moves = generate_moves(board)
    if len(moves) == 0:
        in_chk = is_in_check(board, board.turn)
        if in_chk:
            return True, False, None  # Checkmate
        else:
            return True, True, None   # Stalemate

    auto_draw, reason = board.automatic_draw()
    if auto_draw:
        return True, False, reason

    return False, False, None
