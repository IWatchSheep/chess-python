/* ============================================================================
 *                    BEGINNER-FRIENDLY TWO-PLAYER CHESS IN C99
 * ============================================================================
 *
 * Welcome to this complete chess implementation written in standard C (C99)!
 *
 * This codebase is structured and commented so that even a beginner C
 * programmer can read, understand, modify, and learn from every single part
 * of the code. Dense expressions, clever pointer tricks, and compressed logic
 * have been intentionally unrolled into clear, step-by-step instructions.
 *
 * ----------------------------------------------------------------------------
 * TABLE OF CONTENTS:
 * ----------------------------------------------------------------------------
 * 1. HOW CHESS WORKS ON A COMPUTER BOARD (THE COORDINATE SYSTEM)
 * 2. TWO-STEP INTERACTIVE MOVE WORKFLOW (SELECTION -> PREVIEW -> FINALIZE)
 * 3. ADVANCED ANALYTICAL AND STUDY STAGES INCLUDED
 * 4. SECTION 1: INCLUDES AND PLATFORM CONFIGURATION
 * 5. SECTION 2: CONSTANTS, MACROS, AND TERMINAL COLOR CODES
 * 6. SECTION 3: DATA STRUCTURES (ENUMS AND STRUCTS)
 * 7. SECTION 4: COORDINATE AND HELPER UTILITIES
 * 8. SECTION 5: PIECE ATTACK DETECTION AND MOVEMENT GEOMETRY
 * 9. SECTION 6: KING SAFETY AND CHECK DETECTION
 * 10. SECTION 7: CASTLING VALIDATION
 * 11. SECTION 8: MOVE LEGALITY AND RULES (PSEUDO-LEGAL VS LEGAL)
 * 12. SECTION 9: APPLYING MOVES TO THE BOARD
 * 13. SECTION 10: MOVE GENERATION
 * 14. SECTION 11: REPETITION TRACKING AND DRAW DETECTION
 * 15. SECTION 12: TERMINAL BOARD DISPLAY AND STEP 1 SELECTION
 * 16. SECTION 13: STEP 2 MOVE PREVIEW AND IMPACT ANALYSIS
 * 17. SECTION 14: STAGE 3S - PRACTICE BOARDS (FEN IMPORT AND EXPORT)
 * 18. SECTION 15: STAGE 3A - FACT CALCULATOR REPORT AND PIECE TRACKER
 * 19. SECTION 16: STAGE 3B - OPPONENT REPLY ANALYSIS
 * 20. SECTION 17: STAGE 3C - GAME TREE SEARCH (LOOP AND TRACE)
 * 21. SECTION 18: STAGE 3D - GOALS, PASS MODE, ROUTES, SUPPORT, SECOND GOAL
 * 22. SECTION 19: STAGE 3E - CAPTURE SEQUENCES, PIECE VALUES, EXCHANGES
 * 23. SECTION 20: STAGE 3F - MULTI-MOVE COMPARISON REPORT
 * 24. SECTION 21: MAIN PROGRAM AND INTERACTIVE COMMAND LOOP
 *
 * ----------------------------------------------------------------------------
 * 1. HOW CHESS WORKS ON A COMPUTER BOARD (THE COORDINATE SYSTEM)
 * ----------------------------------------------------------------------------
 * A standard chessboard is a grid of 64 squares arranged in 8 rows and 8 columns.
 *
 * In chess notation:
 *   - Columns are called "FILES" and are labeled with letters 'a' through 'h'.
 *   - Rows are called "RANKS" and are numbered 1 through 8.
 *
 * In C programming, arrays are 0-indexed:
 *   Piece board[8][8];  // board[row][col]
 *
 * Here is how the 2D array row and column indices map to the chessboard:
 *
 *   Array Row 0  = Chess Rank 8  (Black major pieces start here: a8 to h8)
 *   Array Row 1  = Chess Rank 7  (Black pawns start here: a7 to h7)
 *   Array Row 2  = Chess Rank 6
 *   Array Row 3  = Chess Rank 5
 *   Array Row 4  = Chess Rank 4
 *   Array Row 5  = Chess Rank 3
 *   Array Row 6  = Chess Rank 2  (White pawns start here: a2 to h2)
 *   Array Row 7  = Chess Rank 1  (White major pieces start here: a1 to h1)
 *
 *   Array Col 0 = File 'a'    Array Col 4 = File 'e'
 *   Array Col 1 = File 'b'    Array Col 5 = File 'f'
 *   Array Col 2 = File 'c'    Array Col 6 = File 'g'
 *   Array Col 3 = File 'd'    Array Col 7 = File 'h'
 *
 * Conversions:
 *   - To get rank number from array row:    rank_number  = 8 - array_row
 *   - To get array row from rank number:    array_row    = 8 - rank_number
 *   - To get file letter from array column: file_letter  = 'a' + array_col
 *   - To get array column from file letter: array_col    = file_letter - 'a'
 *
 * ----------------------------------------------------------------------------
 * 2. TWO-STEP INTERACTIVE MOVE WORKFLOW
 * ----------------------------------------------------------------------------
 * To help players understand move consequences, this program uses a two-step
 * workflow before any move is finalized:
 *
 * Step 1: Piece Selection
 *   - Enter a starting square (for example, "d2" or "e2").
 *   - The board redraws with:
 *       [P] = Your selected piece enclosed in square brackets.
 *       *   = An empty square that this piece can legally move to.
 *       (p) = An opponent piece that your piece can legally capture.
 *
 * Step 2: Move Preview & Comparative Analysis
 *   - Enter a destination square (for example, "d4" or "e4").
 *   - The move is NOT committed yet!
 *   - A temporary simulation of the board is created.
 *   - A two-column report compares every other piece on the board BEFORE
 *     and AFTER your proposed move, showing newly GAINED destination squares,
 *     LOST destination squares, and UNCHANGED squares.
 *
 * Finalization:
 *   - Press 'F' (or 'f') then Enter to finalize and commit the previewed move.
 *   - Press 'P' (or 'p') then Enter to clear the preview and test another destination.
 *   - Press 'N' (or 'n') then Enter to cancel piece selection and choose another piece.
 *
 * ----------------------------------------------------------------------------
 * 3. ADVANCED ANALYTICAL STAGES
 * ----------------------------------------------------------------------------
 * - FEN ("fen <string>" / "fen"): Set up or inspect arbitrary board positions.
 * - R Report ("r" or "R"): Detailed fact report after previewing a move.
 * - Replies ("replies" / "replies <move>"): Analysis of all opponent responses.
 * - Loop ("loop N" / "loop N K"): Exhaustive game tree search up to N plies.
 * - Trace ("trace <moves>"): Replay a sequence of moves with full fact logs.
 * - Goals & Routes ("goal <squares> <N>", "routes", "support"): Pathfinding.
 * - Exchanges ("exchange <square> <N>", "order <N>", "risk on"): Material calculus.
 * - Compare ("compare N m1 m2 ..."): Side-by-side comparison of candidate moves.
 * ============================================================================
 */

/* ============================================================================
 * SECTION 1: INCLUDES AND PLATFORM CONFIGURATION
 * ============================================================================
 */

#include <stdio.h>    /* Standard I/O: printf, puts, fgets, snprintf, vsnprintf */
#include <stdlib.h>   /* Standard Library: malloc, realloc, free, exit, abs, qsort */
#include <stddef.h>   /* Standard Definitions: size_t, ptrdiff_t, NULL */
#include <string.h>   /* String manipulation: strlen, strcmp, strncmp, strcpy, memcpy, strchr */
#include <ctype.h>    /* Character checks: tolower, toupper, isdigit, isupper */
#include <stdbool.h>  /* Boolean type: bool, true, false */
#include <stdarg.h>   /* Variadic functions: va_list, va_start, va_end */

#ifdef _WIN32
#include <io.h>       /* Windows low-level I/O: _isatty, used in main */
#define WIN32_LEAN_AND_MEAN /* Only the basic parts of windows.h */
#include <windows.h>  /* Windows console: GetStdHandle, GetConsoleMode, SetConsoleMode */
#endif

/* ============================================================================
 * SECTION 2: CONSTANTS, MACROS, AND TERMINAL COLOR CODES
 * ============================================================================
 */

/* ANSI Text Color Escape Codes for Terminal Highlighting */
#define RED   "\033[31m"  /* Used for warning and error messages */
#define CYAN  "\033[36m"  /* Used for in-check notification */
#define RESET "\033[0m"   /* Resets terminal styling back to default */

/*
 * Wooden Chessboard Visual Theme: ANSI 256-color escape sequences.
 * Tan background (color 180) for light squares.
 * Brown background (color 94) for dark squares.
 * Ivory foreground (color 231) for readable text on dark squares.
 * Charcoal foreground (color 232) for readable text on light squares.
 */
#define LIGHT_SQUARE_BG "\033[48;5;180m"  /* Tan square background */
#define DARK_SQUARE_BG  "\033[48;5;94m"   /* Brown square background */
#define LIGHT_TEXT_FG   "\033[38;5;231m"  /* Ivory piece text */
#define DARK_TEXT_FG    "\033[38;5;232m"  /* Charcoal piece text */

/* Board Dimensions */
#define BOARD_SIZE    8   /* 8 ranks (rows) and 8 files (columns) */
#define TOTAL_SQUARES 64  /* 8 * 8 = 64 squares on a standard chessboard */

/* Starting Rows for Pawns */
#define WHITE_PAWN_START_ROW 6  /* Row index 6 corresponds to Rank 2 */
#define BLACK_PAWN_START_ROW 1  /* Row index 1 corresponds to Rank 7 */

/* Back Rows (Starting ranks for Kings, Queens, Rooks, Bishops, Knights) */
#define WHITE_BACK_ROW 7  /* Row index 7 corresponds to Rank 1 */
#define BLACK_BACK_ROW 0  /* Row index 0 corresponds to Rank 8 */

/* Column Indices for Castling Operations */
#define KING_START_COL                  4  /* File 'e' */
#define ROOK_KINGSIDE_START_COL          7  /* File 'h' */
#define ROOK_QUEENSIDE_START_COL         0  /* File 'a' */
#define CASTLE_KINGSIDE_KING_DEST_COL    6  /* King lands on File 'g' */
#define CASTLE_QUEENSIDE_KING_DEST_COL   2  /* King lands on File 'c' */
#define CASTLE_KINGSIDE_ROOK_DEST_COL    5  /* Rook lands on File 'f' */
#define CASTLE_QUEENSIDE_ROOK_DEST_COL   3  /* Rook lands on File 'd' */

/* Buffer Sizes and Limits */
#define FEN_TEXT_SIZE      100  /* Maximum length for a FEN position string */
#define INPUT_BUFFER_SIZE  128  /* Maximum length for keyboard input lines */
#define CALC_MAX_ID        33   /* Maximum 32 pieces on board, indexed 1..32 (0 is empty) */
#define COMPARE_WIDTH      66   /* Text width per column for side-by-side Step 2 display */
#define LOOP_MAX_DEPTH     6    /* Maximum search depth in plies (half-moves) */
#define LOOP_MAX_FIRST     256  /* Maximum candidate moves tracked from root position */
#define GOAL_MAX_SQUARES   16   /* Maximum squares in a goal set */
#define GOAL_MAX_LIMIT     4    /* Maximum own moves limit in PASS mode */
#define GOAL_MAX_ROUTES    512  /* Maximum unique routes stored */
#define EXCHANGE_MAX       8    /* Maximum depth of capture sequence exchanges */
#define COMPARE_MAX        6    /* Maximum candidate moves compared simultaneously */

/* ============================================================================
 * SECTION 3: DATA STRUCTURES (ENUMS AND STRUCTS)
 * ============================================================================
 */

/*
 * Color
 * Represents the color of a piece, a player, or an empty square.
 *   EMPTY = 0 (No piece occupies the square)
 *   WHITE = 1 (White player / White piece)
 *   BLACK = 2 (Black player / Black piece)
 */
typedef enum {
    EMPTY = 0,
    WHITE = 1,
    BLACK = 2
} Color;

/*
 * Piece
 * Represents a single chess piece on the board.
 *   type:  'P' = Pawn, 'N' = Knight, 'B' = Bishop,
 *          'R' = Rook, 'Q' = Queen,  'K' = King,
 *          or '\0' if the square has no piece.
 *   color: EMPTY, WHITE, or BLACK.
 */
typedef struct {
    char type;
    Color color;
} Piece;

/*
 * Move
 * Represents a move from a starting square to an ending square.
 *   sr: Start Row (0 to 7)
 *   sc: Start Column (0 to 7)
 *   er: End Row (0 to 7)
 *   ec: End Column (0 to 7)
 *   promotion: Promotion piece character ('Q', 'R', 'B', 'N') if a pawn
 *              advances to the last rank, or '\0' if not a promotion.
 */
typedef struct {
    int sr;
    int sc;
    int er;
    int ec;
    char promotion;
} Move;

/*
 * Position
 * Stores an encoded string representation (hash key) of a board state.
 * Used to detect threefold repetition (draw) and fivefold repetition.
 */
typedef struct {
    char key[80];
} Position;

/*
 * Board
 * Represents the complete, self-contained state of a chess game.
 */
typedef struct {
    /* The 8x8 grid of chess squares */
    Piece board[BOARD_SIZE][BOARD_SIZE];

    /* Whose turn it is to move next: WHITE or BLACK */
    Color turn;

    /*
     * Castling availability tracking:
     * In chess rules:
     * 1. If the King moves, castling rights for that side are permanently lost.
     * 2. If a Rook moves or is captured on its home square, castling with that
     *    specific Rook is permanently lost.
     */
    bool white_king_moved;
    bool black_king_moved;
    bool white_rook_a_moved; /* Queenside rook (column 'a') */
    bool white_rook_h_moved; /* Kingside rook (column 'h') */
    bool black_rook_a_moved; /* Queenside rook (column 'a') */
    bool black_rook_h_moved; /* Kingside rook (column 'h') */

    /*
     * En Passant Target Square:
     * When a pawn moves 2 squares forward from its starting rank, it skips
     * over a square. If an opponent pawn is positioned adjacent to it, the
     * opponent may capture it "in passing" (en passant) by moving to the
     * skipped square.
     * If en passant is possible on the next move, ep_row and ep_col store
     * the skipped square. If not available, both are set to -1.
     */
    int ep_row;
    int ep_col;

    /*
     * Fifty-Move Rule (Halfmove Clock):
     * Counts the number of half-moves (turns) since the last pawn advance or piece capture.
     * If this counter reaches 100 (50 full moves without pawn move or capture),
     * a player may claim a draw. At 150 (75 full moves), a draw is mandatory.
     */
    int halfmove_clock;

    /*
     * Fullmove Number:
     * The move number in standard chess score sheets. Starts at 1 and increments
     * every time Black completes a move.
     */
    int fullmove_number;

    /*
     * Move History:
     * Dynamically allocated array storing the position key of every state in the game.
     * Used to detect threefold repetition (draw) and fivefold repetition.
     */
    Position *history;
    size_t history_size;
    size_t history_capacity;
} Board;

/*
 * MoveList
 * A dynamic array that can hold an arbitrary number of Move structs.
 * Automatically grows its capacity when more moves are added.
 */
typedef struct {
    Move *items;
    size_t count;
    size_t capacity;
} MoveList;

/*
 * Direction
 * Represents a row step and column step on the grid (e.g. {-1, 0} = up).
 */
typedef struct {
    int row;
    int col;
} Direction;

/*
 * InputResult
 * Status returned when reading a line of text from standard input.
 */
typedef enum {
    INPUT_READ_OK,
    INPUT_READ_TOO_LONG,
    INPUT_READ_EOF
} InputResult;

/*
 * Command
 * Represents recognized user commands entered in the terminal.
 */
typedef enum {
    COMMAND_OTHER,      /* Square entry, FEN, analysis commands, etc. */
    COMMAND_SHORT_NEW,  /* "n" or "N" to cancel piece selection */
    COMMAND_NEW,        /* "new", "NEW", or "select none" */
    COMMAND_FINALIZE,   /* "f" or "F" to finalize previewed move */
    COMMAND_PREVIEW,    /* "p" or "P" to clear preview */
    COMMAND_QUIT,       /* "quit" or "exit" */
    COMMAND_RESTART,    /* "restart" */
    COMMAND_RESIGN,     /* "resign" */
    COMMAND_CLAIM       /* "claim" draw by 50-move rule or threefold repetition */
} Command;

/*
 * FollowCase
 * Tracks what happened to a piece across a move for the Calculator (Stage 3S/3A).
 */
typedef enum {
    FOLLOW_STAYS,          /* The piece stayed on its current square */
    FOLLOW_MOVED,          /* This piece made the move */
    FOLLOW_CASTLING_ROOK,  /* This piece was the rook moved during castling */
    FOLLOW_CAPTURED,       /* This piece was captured */
    FOLLOW_PROMOTED        /* This piece was a pawn that reached promotion rank */
} FollowCase;

/*
 * TextBuffer
 * A dynamic string builder that automatically resizes its buffer when text
 * is appended. Used for generating multi-line analysis reports cleanly.
 */
typedef struct {
    char *text;
    size_t length;
    size_t capacity;
} TextBuffer;

/*
 * IdGrid
 * Stores unique piece IDs (1..32) for each square on the 8x8 board.
 * 0 indicates an empty square.
 */
typedef struct {
    int id[BOARD_SIZE][BOARD_SIZE];
} IdGrid;

/*
 * Tracker
 * Tracks individual pieces by unique ID across moves for Stage 3A fact analysis.
 */
typedef struct {
    IdGrid grid;                           /* Piece ID on each board square */
    Color color[CALC_MAX_ID];              /* Color of each piece ID */
    bool lost[CALC_MAX_ID][TOTAL_SQUARES]; /* (piece, square) pairs lost and not yet regained */
} Tracker;

/*
 * Snapshot
 * Captures all mobility and square control facts for a board state.
 */
typedef struct {
    bool present[CALC_MAX_ID];
    int row[CALC_MAX_ID];
    int col[CALC_MAX_ID];
    bool legal[CALC_MAX_ID][TOTAL_SQUARES]; /* Legal destinations for piece ID */
    int legal_count[CALC_MAX_ID];           /* Total count of legal destinations */
    bool reach[3][TOTAL_SQUARES];           /* Squares reachable by each team color */
} Snapshot;

/*
 * Names
 * Human-readable text label for each piece ID before a move (e.g. "P e2").
 */
typedef struct {
    char name[CALC_MAX_ID][8];
} Names;

/*
 * SideCounts
 * Fact counters for the Stage 3A/3B reports (COUNT line).
 */
typedef struct {
    int zero_after; /* Pieces with 0 legal moves after the move */
    int lost;       /* Destinations lost by this side */
    int denied;     /* Squares denied to team reach */
    int gained;     /* Newly gained destinations */
    int restored;   /* Previously lost destinations now regained */
    int opened;     /* Newly opened squares for team reach */
} SideCounts;

/*
 * LoopState
 * State accumulator for Stage 3C recursive game tree exploration ("loop N").
 */
typedef struct {
    int depth;
    int zero_k;
    Color mover;
    long positions[LOOP_MAX_DEPTH + 1];
    long mated[LOOP_MAX_DEPTH + 1][3];
    long stalemates[LOOP_MAX_DEPTH + 1];
    long zero[LOOP_MAX_DEPTH + 1];
    long first_mated[LOOP_MAX_FIRST][3];
    int first_index;
    bool reply_reaches_mate;
    int replies_with_mate[LOOP_MAX_FIRST];
    Move line[LOOP_MAX_DEPTH];
    TextBuffer *out;
} LoopState;

/*
 * Goal & GoalCondition
 * Defines target destination squares for Stage 3D route planning.
 */
typedef struct {
    bool active;
    bool king;                          /* Target squares adjacent to enemy king */
    int count;                          /* Number of squares in goal set */
    int square[GOAL_MAX_SQUARES];       /* Square indices (0..63) */
    int limit;                          /* Max own moves in PASS mode */
} Goal;

typedef enum {
    COND_REACH,     /* A piece reaches the target square */
    COND_PROTECTED  /* A piece reaches target AND another friendly piece protects it */
} GoalCondition;

/*
 * RouteVector
 * Stores a single path to a goal in Stage 3D.
 */
typedef struct {
    int own;
    int protectors;
    int attackers;
    size_t line_start;
    size_t line_end;
    Move path[GOAL_MAX_LIMIT];
    int length;
    bool dominated;
} RouteVector;

/*
 * RouteState
 * Accumulator for finding routes to a goal.
 */
typedef struct {
    TextBuffer *out;
    Color side;
    int sq;
    Move path[GOAL_MAX_LIMIT];
    RouteVector routes[GOAL_MAX_ROUTES];
    int route_count;
    int extra;
} RouteState;

/*
 * RealResult
 * Outcome of real game-tree goal search where opponent replies with legal moves.
 */
typedef enum {
    REAL_ELSE,     /* Goal cannot be reached */
    REAL_POSSIBLE, /* Goal reached in some branches */
    REAL_FORCED    /* Goal reached in all branches regardless of opponent defense */
} RealResult;

/*
 * MaterialResult
 * Classification of material outcome in Stage 3E exchange analysis.
 */
typedef enum {
    MATERIAL_ELSE,     /* Negative material outcome */
    MATERIAL_POSSIBLE, /* Non-negative material possible */
    MATERIAL_FORCED    /* Non-negative material guaranteed */
} MaterialResult;

/*
 * ExchangeState
 * Accumulator for Stage 3E recursive capture tree search on one square.
 */
typedef struct {
    Color mover;
    int sq;
    int limit;
    Move line[EXCHANGE_MAX];
    char taken[EXCHANGE_MAX];
    Color by[EXCHANGE_MAX];
    int sequences;
    bool cut;
    TextBuffer *out;
} ExchangeState;

/*
 * OrderEntry
 * Move entry for Stage 3E combined move ordering (ideas 7 & 8).
 */
typedef struct {
    Move move;
    char taken;
    int value;
    int squares;
    MaterialResult material;
    bool bounded;
} OrderEntry;

/*
 * Candidate
 * Facts gathered for one move in Stage 3F candidate move comparison.
 */
typedef struct {
    Move move;
    char text[6];
    char r_white[256];
    char r_black[256];
    char check[256];
    char mate1_white[256];
    char mate1_black[256];
    int links[4];
    char threat[256];
    char replies[256];
    char loop_status[256];
    char loop_mated[256];
    int loop_level;
    char goal_text[GOAL_MAX_SQUARES][2][48];
    int goal_level[GOAL_MAX_SQUARES][2];
    char taken;
    int value;
    int squares;
    int value_rank;
    int squares_rank;
    const char *value_label;
    const char *squares_label;
    MaterialResult material;
    bool material_known;
    bool bounded;
    char stop[3];
    int group;
    int group_class;
    const char *group_label;
} Candidate;

/* ============================================================================
 * SECTION 4: COORDINATE AND HELPER UTILITIES
 * ============================================================================
 */

/*
 * in_bounds
 * Checks whether a given row and column coordinate lies within the 8x8 chessboard.
 *
 * Parameters:
 *   row - The row index to check (0 to 7)
 *   col - The column index to check (0 to 7)
 *
 * Returns:
 *   true if both row and column are within 0..7; false otherwise.
 */
static bool in_bounds(int row, int col) {
    bool row_is_valid = (row >= 0 && row < BOARD_SIZE);
    bool col_is_valid = (col >= 0 && col < BOARD_SIZE);
    return row_is_valid && col_is_valid;
}

/*
 * empty_piece
 * Constructs and returns a Piece struct representing an empty square.
 */
static Piece empty_piece(void) {
    Piece piece;
    piece.type = '\0';
    piece.color = EMPTY;
    return piece;
}

/* Forward declaration of piece_symbol so it can be used anywhere */
static char piece_symbol(Piece piece);

/*
 * opposite
 * Returns the opposing player's color.
 *
 * Parameters:
 *   color - WHITE or BLACK
 *
 * Returns:
 *   BLACK if given WHITE, WHITE if given BLACK, or EMPTY if given EMPTY.
 */
static Color opposite(Color color) {
    if (color == WHITE) {
        return BLACK;
    } else if (color == BLACK) {
        return WHITE;
    }
    return EMPTY;
}

/*
 * color_name
 * Returns a human-readable string for a piece/player color.
 */
static const char *color_name(Color color) {
    if (color == WHITE) {
        return "White";
    } else if (color == BLACK) {
        return "Black";
    }
    return "Empty";
}

/*
 * home_row_for
 * Returns the starting back row index for a given side.
 * White pieces start on Rank 1 (Row index 7).
 * Black pieces start on Rank 8 (Row index 0).
 */
static int home_row_for(Color side) {
    if (side == WHITE) {
        return WHITE_BACK_ROW; /* Row 7 */
    } else {
        return BLACK_BACK_ROW; /* Row 0 */
    }
}

/*
 * rook_col_for
 * Returns the starting column index for a Rook during castling.
 * Kingside rook is on File 'h' (Column index 7).
 * Queenside rook is on File 'a' (Column index 0).
 */
static int rook_col_for(bool king_side) {
    if (king_side) {
        return ROOK_KINGSIDE_START_COL;  /* Column 7 ('h') */
    } else {
        return ROOK_QUEENSIDE_START_COL; /* Column 0 ('a') */
    }
}

/*
 * king_side_castle
 * Determines whether a castling move is towards the kingside or queenside.
 * Kingside castling moves the King to the right (higher column index).
 */
static bool king_side_castle(Move move) {
    return move.ec > move.sc;
}

/*
 * mark_rook_moved
 * Marks the specified rook as having moved, revoking castling rights on that side.
 */
static void mark_rook_moved(Board *b, Color side, bool king_side) {
    if (side == WHITE) {
        if (king_side) {
            b->white_rook_h_moved = true;
        } else {
            b->white_rook_a_moved = true;
        }
    } else {
        if (king_side) {
            b->black_rook_h_moved = true;
        } else {
            b->black_rook_a_moved = true;
        }
    }
}

/*
 * square_index
 * Computes a single integer index (0 to 63) for a square on the 8x8 board.
 * Index 0 is a8, 7 is h8, 56 is a1, 63 is h1.
 */
static int square_index(int row, int col) {
    return row * BOARD_SIZE + col;
}

/*
 * square_text
 * Converts a 0..63 square index into two-character algebraic notation (e.g. "e4").
 * Writes to out buffer (must have room for at least 3 chars including null terminator).
 */
static void square_text(int index, char out[3]) {
    int col = index % BOARD_SIZE;
    int row = index / BOARD_SIZE;
    out[0] = (char)('a' + col);
    out[1] = (char)('0' + (8 - row));
    out[2] = '\0';
}

/*
 * parse_square
 * Converts an algebraic chess square string (e.g. "e4" or "E4") into
 * 0-indexed row and column coordinates.
 *
 * Parameters:
 *   s   - Input string with at least 2 characters (e.g. "e4")
 *   row - Pointer where resulting row index (0..7) will be stored
 *   col - Pointer where resulting col index (0..7) will be stored
 *
 * Returns:
 *   true if the square is well-formed ('a'-'h' and '1'-'8'), false otherwise.
 */
static bool parse_square(const char *s, int *row, int *col) {
    if (s == NULL || s[0] == '\0' || s[1] == '\0') {
        return false;
    }
    char file_char = (char)tolower((unsigned char)s[0]);
    char rank_char = s[1];

    if (file_char < 'a' || file_char > 'h') {
        return false;
    }
    if (rank_char < '1' || rank_char > '8') {
        return false;
    }

    *col = file_char - 'a';
    *row = 8 - (rank_char - '0');
    return true;
}

/*
 * piece_symbol
 * Returns the display character for a piece.
 * White pieces are uppercase ('P', 'N', 'B', 'R', 'Q', 'K').
 * Black pieces are lowercase ('p', 'n', 'b', 'r', 'q', 'k').
 * Empty squares return a space (' ').
 */
static char piece_symbol(Piece piece) {
    if (piece.color == EMPTY) {
        return ' ';
    }
    if (piece.color == WHITE) {
        return piece.type;
    }
    return (char)tolower((unsigned char)piece.type);
}
/* ============================================================================
 * SECTION 5: PIECE ATTACK DETECTION AND MOVEMENT GEOMETRY
 * ============================================================================
 */

/*
 * path_clear
 * Checks whether all intermediate squares between (start_row, start_col) and
 * (end_row, end_col) are completely empty (no pieces blocking the path).
 *
 * This is used for sliding pieces: Rooks, Bishops, and Queens.
 *
 * NOTE FOR BEGINNERS:
 * In C, we determine the step direction (-1, 0, or +1) for rows and columns.
 * We step square by square from the starting square towards the destination.
 * If any intermediate square is occupied by ANY piece, the path is blocked!
 * Note that the destination square itself is NOT checked by path_clear, because
 * capturing an opponent piece on the destination square is allowed.
 *
 * Parameters:
 *   b  - Pointer to the current Board
 *   sr - Start Row
 *   sc - Start Column
 *   er - End Row
 *   ec - End Column
 *
 * Returns:
 *   true if all intermediate squares are empty; false if blocked or not aligned.
 */
static bool path_clear(const Board *b, int sr, int sc, int er, int ec) {
    /* If start and end are identical, this is not a valid move */
    if (sr == er && sc == ec) {
        return false;
    }

    /* Calculate the step direction for row and column:
     * step = +1 if moving forward/down
     * step = -1 if moving backward/up
     * step =  0 if staying in the same row or column
     */
    int step_row = 0;
    if (er > sr) {
        step_row = 1;
    } else if (er < sr) {
        step_row = -1;
    }

    int step_col = 0;
    if (ec > sc) {
        step_col = 1;
    } else if (ec < sc) {
        step_col = -1;
    }

    /* Verify that the start and end squares are aligned along a straight line
     * or a perfect 45-degree diagonal.
     */
    int delta_row = abs(er - sr);
    int delta_col = abs(ec - sc);
    bool is_straight = (step_row == 0 || step_col == 0);
    bool is_diagonal = (delta_row == delta_col);
    if (!is_straight && !is_diagonal) {
        return false;
    }

    /* Walk along the path, square by square, from start + step towards destination */
    int current_row = sr + step_row;
    int current_col = sc + step_col;

    while (current_row != er || current_col != ec) {
        /* Safety check: ensure coordinates remain on the board */
        if (!in_bounds(current_row, current_col)) {
            return false;
        }

        /* If this intermediate square is not empty, the path is blocked */
        if (b->board[current_row][current_col].color != EMPTY) {
            return false;
        }

        /* Advance to the next square along the ray */
        current_row += step_row;
        current_col += step_col;
    }

    /* All intermediate squares were empty */
    return true;
}

/*
 * pawn_direction
 * Returns the direction of forward pawn movement for a player.
 * White pawns start on Rank 2 (Row 6) and move towards Rank 8 (Row 0): step is -1.
 * Black pawns start on Rank 7 (Row 1) and move towards Rank 1 (Row 7): step is +1.
 */
static int pawn_direction(Color color) {
    if (color == WHITE) {
        return -1;
    } else {
        return 1;
    }
}

/*
 * is_knight_move
 * Checks whether a row change and column change match the Knight's L-shaped jump:
 * 2 squares in one dimension and 1 square in the other.
 */
static bool is_knight_move(int row_change, int col_change) {
    int rows = abs(row_change);
    int cols = abs(col_change);
    bool two_by_one = (rows == 2 && cols == 1);
    bool one_by_two = (rows == 1 && cols == 2);
    return two_by_one || one_by_two;
}

/*
 * is_diagonal_move
 * Checks whether a move is diagonal: absolute row change equals absolute column change.
 */
static bool is_diagonal_move(int row_change, int col_change) {
    return abs(row_change) == abs(col_change);
}

/*
 * is_straight_move
 * Checks whether a move is along a rank or file (horizontal or vertical):
 * either row change is 0 or column change is 0.
 */
static bool is_straight_move(int row_change, int col_change) {
    return (row_change == 0 || col_change == 0);
}

/*
 * is_queen_move
 * Queens combine the movement of Rooks and Bishops: straight or diagonal.
 */
static bool is_queen_move(int row_change, int col_change) {
    return is_straight_move(row_change, col_change) ||
           is_diagonal_move(row_change, col_change);
}

/*
 * piece_attacks
 * Determines whether a piece on (start_row, start_col) attacks target square (target_row, target_col).
 *
 * NOTE FOR BEGINNERS:
 * In chess, a piece "attacks" a square if it could capture an enemy piece on that square.
 * For pawns, attacks are ALWAYS diagonal forward by 1 square (regardless of whether the target
 * square is empty or occupied).
 * For sliding pieces (Bishop, Rook, Queen), the attack requires a clear path.
 *
 * Parameters:
 *   b  - Current board
 *   sr - Start Row of attacking piece
 *   sc - Start Column of attacking piece
 *   tr - Target Row being attacked
 *   tc - Target Column being attacked
 *
 * Returns:
 *   true if the piece on (sr, sc) attacks (tr, tc); false otherwise.
 */
static bool piece_attacks(const Board *b, int sr, int sc, int tr, int tc) {
    Piece piece = b->board[sr][sc];
    int delta_row = tr - sr;
    int delta_col = tc - sc;

    /* An empty square cannot attack anything */
    if (piece.color == EMPTY) {
        return false;
    }

    /* A piece cannot attack the square it is already standing on */
    if (sr == tr && sc == tc) {
        return false;
    }

    switch (piece.type) {
        case 'P':
            /* Pawns attack 1 square diagonally in their forward direction */
            return (abs(delta_col) == 1 && delta_row == pawn_direction(piece.color));

        case 'N':
            /* Knights jump in an L-shape regardless of obstacles */
            return is_knight_move(delta_row, delta_col);

        case 'B':
            /* Bishops attack diagonally if the intervening path is clear */
            return is_diagonal_move(delta_row, delta_col) && path_clear(b, sr, sc, tr, tc);

        case 'R':
            /* Rooks attack horizontally or vertically if the intervening path is clear */
            return is_straight_move(delta_row, delta_col) && path_clear(b, sr, sc, tr, tc);

        case 'Q':
            /* Queens attack straight or diagonally if the intervening path is clear */
            return is_queen_move(delta_row, delta_col) && path_clear(b, sr, sc, tr, tc);

        case 'K':
            /* Kings attack any adjacent square (1 square in any direction) */
            return (abs(delta_row) <= 1 && abs(delta_col) <= 1);

        default:
            return false;
    }
}

/* ============================================================================
 * SECTION 6: KING SAFETY AND CHECK DETECTION
 * ============================================================================
 */

/*
 * square_attacked
 * Determines whether square (row, col) is attacked by ANY piece of color `by`.
 * Scans all 64 squares of the board looking for pieces of that color.
 */
static bool square_attacked(const Board *b, int r, int c, Color by) {
    for (int check_row = 0; check_row < BOARD_SIZE; ++check_row) {
        for (int check_col = 0; check_col < BOARD_SIZE; ++check_col) {
            Piece attacker = b->board[check_row][check_col];
            if (attacker.color == by) {
                if (piece_attacks(b, check_row, check_col, r, c)) {
                    return true;
                }
            }
        }
    }
    return false;
}

/*
 * find_king
 * Locates the King of the specified color on the board.
 *
 * Parameters:
 *   b        - Current board
 *   side     - WHITE or BLACK
 *   king_row - Pointer where the King's row index will be stored
 *   king_col - Pointer where the King's column index will be stored
 *
 * Returns:
 *   true if the King was found on the board; false if missing.
 */
static bool find_king(const Board *b, Color side, int *king_row, int *king_col) {
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            Piece piece = b->board[row][col];
            if (piece.type == 'K' && piece.color == side) {
                *king_row = row;
                *king_col = col;
                return true;
            }
        }
    }
    return false;
}

/*
 * has_king
 * Helper function returning true if the specified side has a King on the board.
 */
static bool has_king(const Board *b, Color side) {
    int row, col;
    return find_king(b, side, &row, &col);
}

/*
 * is_in_check
 * Checks whether the King of the specified side is currently under attack (in check).
 *
 * Parameters:
 *   b    - Current board state
 *   side - The player side to test (WHITE or BLACK)
 *
 * Returns:
 *   true if that player's King is under attack by the opponent; false otherwise.
 */
static bool is_in_check(const Board *b, Color side) {
    int king_row, king_col;
    if (!find_king(b, side, &king_row, &king_col)) {
        return false;
    }
    Color enemy = opposite(side);
    return square_attacked(b, king_row, king_col, enemy);
}

/* ============================================================================
 * SECTION 7: CASTLING VALIDATION
 * ============================================================================
 */

/*
 * can_castle
 * Validates whether the proposed castling move satisfies all official FIDE chess rules:
 *
 * Rule 1: The King must never have moved previously.
 * Rule 2: The chosen Rook must never have moved previously.
 * Rule 3: The Rook must still be on its original corner square.
 * Rule 4: All squares between the King and Rook must be empty.
 * Rule 5: The King must not currently be in check. (Checked in king_move_is_pseudo_legal).
 * Rule 6: The square the King passes through (transit square) must NOT be under enemy attack.
 * Rule 7: The square the King lands on (destination square) must NOT be under enemy attack.
 *
 * Parameters:
 *   b    - Current board state
 *   move - The proposed castling move (King moving 2 squares horizontally)
 *   side - WHITE or BLACK
 *
 * Returns:
 *   true if all castling requirements are met; false otherwise.
 */
static bool can_castle(const Board *b, Move move, Color side) {
    int home_row = home_row_for(side);
    bool king_moved = (side == WHITE) ? b->white_king_moved : b->black_king_moved;
    Color enemy = opposite(side);
    bool castle_kingside = king_side_castle(move);
    bool rook_moved = false;

    int rook_col = rook_col_for(castle_kingside);
    int transit_col = castle_kingside ? CASTLE_KINGSIDE_ROOK_DEST_COL : CASTLE_QUEENSIDE_ROOK_DEST_COL;
    int destination_col = castle_kingside ? CASTLE_KINGSIDE_KING_DEST_COL : CASTLE_QUEENSIDE_KING_DEST_COL;

    /* King must start from home row, column 4 (e1 for White, e8 for Black), and have not moved */
    if (move.sr != home_row || move.sc != KING_START_COL || king_moved) {
        return false;
    }

    /* Check if the rook has already moved */
    if (side == WHITE) {
        rook_moved = castle_kingside ? b->white_rook_h_moved : b->white_rook_a_moved;
    } else {
        rook_moved = castle_kingside ? b->black_rook_h_moved : b->black_rook_a_moved;
    }

    /* The rook must not have moved, and must actually be a Rook of our color */
    if (rook_moved ||
        b->board[home_row][rook_col].type != 'R' ||
        b->board[home_row][rook_col].color != side) {
        return false;
    }

    /* All squares between King and Rook must be empty:
     * Kingside: columns 5 (f) and 6 (g) must be empty.
     * Queenside: columns 1 (b), 2 (c), and 3 (d) must be empty.
     */
    int first_empty_col = castle_kingside ? 5 : 1;
    int last_empty_col  = castle_kingside ? 6 : 3;
    for (int col = first_empty_col; col <= last_empty_col; ++col) {
        if (b->board[home_row][col].color != EMPTY) {
            return false;
        }
    }

    /* Transit and destination squares must NOT be under attack by the enemy */
    bool transit_attacked = square_attacked(b, home_row, transit_col, enemy);
    bool destination_attacked = square_attacked(b, home_row, destination_col, enemy);

    if (transit_attacked || destination_attacked) {
        return false;
    }

    return true;
}

/* ============================================================================
 * SECTION 8: MOVE LEGALITY AND RULES (PSEUDO-LEGAL VS LEGAL)
 * ============================================================================
 */

/*
 * pawn_move_is_pseudo_legal
 * Validates the geometric rules for pawn moves:
 *   1. 1 square forward to an empty square.
 *   2. 2 squares forward from the starting rank (both squares empty).
 *   3. 1 square diagonal forward to capture an enemy piece.
 *   4. 1 square diagonal forward to capture en passant.
 */
static bool pawn_move_is_pseudo_legal(const Board *b, Move move, Piece pawn, Piece target) {
    int direction = pawn_direction(pawn.color);
    int starting_row = (pawn.color == WHITE) ? WHITE_PAWN_START_ROW : BLACK_PAWN_START_ROW;
    int row_change = move.er - move.sr;
    int col_change = move.ec - move.sc;

    /* Case A: Moving straight forward (column change is 0) */
    if (col_change == 0 && target.color == EMPTY) {
        /* Single step forward */
        if (row_change == direction) {
            return true;
        }

        /* Double step forward from starting rank */
        int intermediate_row = move.sr + direction;
        if (row_change == (2 * direction) &&
            move.sr == starting_row &&
            b->board[intermediate_row][move.sc].color == EMPTY) {
            return true;
        }
    }

    /* Case B: Diagonal forward motion (captures) */
    if (abs(col_change) != 1 || row_change != direction) {
        return false;
    }

    /* Normal capture: destination square contains an enemy piece */
    if (target.color != EMPTY) {
        return true;
    }

    /* En Passant capture:
     * The pawn moves diagonally to an empty square, but that square matches
     * the board's en passant target square (b->ep_row, b->ep_col), and the
     * skipped square contains an opponent pawn.
     */
    bool lands_on_ep_square = (move.er == b->ep_row && move.ec == b->ep_col);
    bool captured_pawn_present = (b->board[move.sr][move.ec].type == 'P' &&
                                  b->board[move.sr][move.ec].color == opposite(pawn.color));

    return lands_on_ep_square && captured_pawn_present;
}

/*
 * king_move_is_pseudo_legal
 * Validates king motion: 1 square in any direction, or castling (2 squares horizontally).
 */
static bool king_move_is_pseudo_legal(const Board *b, Move move) {
    /* Normal 1-square king move */
    if (piece_attacks(b, move.sr, move.sc, move.er, move.ec)) {
        return true;
    }

    /* Castling: King moves exactly 2 squares horizontally on the same rank */
    bool is_two_square_horizontal = (move.sr == move.er && abs(move.ec - move.sc) == 2);
    if (!is_two_square_horizontal) {
        return false;
    }

    /* The King cannot castle while currently in check */
    if (is_in_check(b, b->turn)) {
        return false;
    }

    return can_castle(b, move, b->turn);
}

/*
 * promotion_is_valid
 * Checks that pawn promotion specifies a valid piece ('Q', 'R', 'B', 'N')
 * when reaching the opposite end rank (Row 0 for White, Row 7 for Black).
 */
static bool promotion_is_valid(Move move, Piece piece) {
    /* If no promotion piece was specified, it is valid as pseudo-legal
     * (the generator expands promotions into Q, R, B, N later, and default is Q).
     */
    if (move.promotion == '\0') {
        return true;
    }

    /* Must be a Pawn reaching the 8th rank (Row 0 for White, Row 7 for Black) */
    bool is_pawn = (piece.type == 'P');
    bool reached_end_rank = (move.er == 0 || move.er == 7);
    bool valid_promotion_char = (strchr("QRBN", move.promotion) != NULL);

    return is_pawn && reached_end_rank && valid_promotion_char;
}

/*
 * pseudo_legal
 * Checks whether a move is geometrically valid according to the piece movement rules,
 * without testing whether the move leaves the player's own king in check.
 *
 * Rules checked:
 *   1. Start and end squares must be within board boundaries.
 *   2. The piece moving must belong to the player whose turn it is.
 *   3. The destination cannot be occupied by a friendly piece.
 *   4. The destination cannot contain a King (Kings cannot be captured).
 *   5. Promotion character validity.
 *   6. Piece-specific movement geometry (Pawns, Knights, Sliding pieces, King).
 */
static bool pseudo_legal(const Board *b, Move m) {
    if (!in_bounds(m.sr, m.sc) || !in_bounds(m.er, m.ec)) {
        return false;
    }

    Piece piece = b->board[m.sr][m.sc];
    Piece target = b->board[m.er][m.ec];

    /* Must move our own piece */
    if (piece.color != b->turn) {
        return false;
    }

    /* Cannot capture our own piece */
    if (target.color == b->turn) {
        return false;
    }

    /* Kings can never be captured in chess */
    if (target.type == 'K') {
        return false;
    }

    /* Validate promotion rules */
    if (!promotion_is_valid(m, piece)) {
        return false;
    }

    /* Delegate to piece-specific logic */
    if (piece.type == 'P') {
        return pawn_move_is_pseudo_legal(b, m, piece, target);
    }

    if (piece.type == 'K') {
        return king_move_is_pseudo_legal(b, m);
    }

    return piece_attacks(b, m.sr, m.sc, m.er, m.ec);
}

/*
 * move_is_en_passant
 * Returns true if move `move` made by `piece` is an en passant capture.
 */
static bool move_is_en_passant(const Board *b, Move move, Piece piece) {
    if (piece.type != 'P') {
        return false;
    }
    bool matches_ep_square = (move.er == b->ep_row && move.ec == b->ep_col);
    bool dest_is_empty = (b->board[move.er][move.ec].color == EMPTY);
    bool enemy_pawn_adjacent = (b->board[move.sr][move.ec].type == 'P' &&
                                b->board[move.sr][move.ec].color == opposite(piece.color));

    return matches_ep_square && dest_is_empty && enemy_pawn_adjacent;
}

/* Forward declaration of apply_move_to_board */
static void apply_move_to_board(Board *b, Move move);

/*
 * legal_move
 * Determines whether a move is fully legal in chess:
 *   1. It must be pseudo-legal (geometrically valid).
 *   2. Making the move on a simulated board must NOT leave the player's
 *      own King in check!
 */
static bool legal_move(const Board *b, Move move) {
    if (!pseudo_legal(b, move)) {
        return false;
    }

    /* Test the move on a temporary copy of the board */
    Board after_move = *b;
    apply_move_to_board(&after_move, move);

    /* If our own King is in check after the move, the move is ILLEGAL! */
    return !is_in_check(&after_move, b->turn);
}

/* ============================================================================
 * SECTION 9: APPLYING MOVES TO THE BOARD
 * ============================================================================
 */

/*
 * apply_move_to_board
 * Modifies the 8x8 piece grid to reflect the execution of `move`.
 *
 * Handles:
 *   - Normal piece movement: clears start square, puts piece on destination.
 *   - En passant capture: clears the captured enemy pawn on (sr, ec).
 *   - Castling: moves the Rook from its corner to the transit square.
 *   - Pawn promotion: changes the pawn's type to the promotion piece (default 'Q').
 */
static void apply_move_to_board(Board *b, Move move) {
    Piece piece = b->board[move.sr][move.sc];

    /* 1. Handle en passant capture: remove the captured enemy pawn */
    if (move_is_en_passant(b, move, piece)) {
        b->board[move.sr][move.ec] = empty_piece();
    }

    /* 2. Handle castling: move the rook alongside the king */
    if (piece.type == 'K' && abs(move.ec - move.sc) == 2) {
        bool king_side = (move.ec > move.sc);
        int rook_from_col = rook_col_for(king_side);
        int rook_to_col   = king_side ? CASTLE_KINGSIDE_ROOK_DEST_COL : CASTLE_QUEENSIDE_ROOK_DEST_COL;

        /* Move the rook */
        b->board[move.sr][rook_to_col] = b->board[move.sr][rook_from_col];
        b->board[move.sr][rook_from_col] = empty_piece();
    }

    /* 3. Move the piece to its destination square */
    b->board[move.sr][move.sc] = empty_piece();
    b->board[move.er][move.ec] = piece;

    /* 4. Handle pawn promotion */
    if (piece.type == 'P' && (move.er == 0 || move.er == 7)) {
        b->board[move.er][move.ec].type = (move.promotion == '\0') ? 'Q' : move.promotion;
    }
}

/*
 * mark_rook_at_home_square
 * If a Rook on its home square moves or is captured, revoke castling rights for that rook.
 */
static void mark_rook_at_home_square(Board *b, int row, int col, Color side) {
    int home_row = home_row_for(side);
    if (row != home_row || (col != 0 && col != 7)) {
        return;
    }
    bool is_kingside = (col == 7);
    mark_rook_moved(b, side, is_kingside);
}

/*
 * update_castle_state
 * Updates the board's castling flags when a king or rook moves.
 */
static void update_castle_state(Board *b, Piece piece, Move m) {
    /* If the king castled, mark the corresponding rook as moved */
    if (piece.type == 'K' && abs(m.ec - m.sc) == 2) {
        mark_rook_moved(b, piece.color, king_side_castle(m));
    }

    /* If the king moves at all, revoke all castling for this side */
    if (piece.type == 'K') {
        if (piece.color == WHITE) {
            b->white_king_moved = true;
        } else {
            b->black_king_moved = true;
        }
    }

    /* If a rook moves from its home square, revoke castling on that side */
    if (piece.type == 'R') {
        mark_rook_at_home_square(b, m.sr, m.sc, piece.color);
    }
}

/*
 * make_move
 * Fully executes a move on the game board and updates all game state:
 *   - Castling flags (if king or rook moved, or rook captured)
 *   - Piece grid positions
 *   - En passant target square
 *   - Halfmove clock (50-move rule)
 *   - Fullmove number
 *   - Current player turn
 */
static void make_move(Board *b, Move m) {
    Piece piece = b->board[m.sr][m.sc];
    Piece target = b->board[m.er][m.ec];
    bool pawn_move = (piece.type == 'P');
    bool capture = (target.color != EMPTY || move_is_en_passant(b, m, piece));

    /* If an opponent's rook on its starting square was captured, revoke its castling right */
    if (target.type == 'R') {
        mark_rook_at_home_square(b, m.er, m.ec, target.color);
    }

    /* Update castling rights for the moving player */
    update_castle_state(b, piece, m);

    /* Move the pieces on the board array */
    apply_move_to_board(b, m);

    /* Update the en passant target square:
     * If a pawn moved 2 squares forward, record the skipped square.
     * Otherwise, reset en passant target to -1.
     */
    if (pawn_move && abs(m.er - m.sr) == 2) {
        b->ep_row = (m.sr + m.er) / 2;
        b->ep_col = m.sc;
    } else {
        b->ep_row = -1;
        b->ep_col = -1;
    }

    /* Update Fifty-Move clock and history:
     * A pawn move or piece capture resets the clock to 0 and clears repetition history
     * (because pawn moves and captures are irreversible in chess).
     * Any other move increments the clock.
     */
    if (pawn_move || capture) {
        b->halfmove_clock = 0;
        b->history_size = 0;
    } else {
        b->halfmove_clock++;
    }

    /* Fullmove counter increments after Black's move */
    if (b->turn == BLACK) {
        b->fullmove_number++;
    }

    /* Switch turn to the other player */
    b->turn = opposite(b->turn);
}

/* Forward declaration of record_position */
static void record_position(Board *b);

/*
 * reset_board
 * Resets the chessboard to the standard starting position for a new game.
 */
static void reset_board(Board *b) {
    static const char back_row[] = "RNBQKBNR";

    /* Clear all 64 squares */
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            b->board[r][c] = empty_piece();
        }
    }

    /* Set up starting piece layout */
    for (int c = 0; c < BOARD_SIZE; ++c) {
        Piece black_major = {back_row[c], BLACK};
        Piece black_pawn  = {'P', BLACK};
        Piece white_pawn  = {'P', WHITE};
        Piece white_major = {back_row[c], WHITE};

        b->board[0][c] = black_major; /* Rank 8: Black major pieces */
        b->board[1][c] = black_pawn;  /* Rank 7: Black pawns */
        b->board[6][c] = white_pawn;  /* Rank 2: White pawns */
        b->board[7][c] = white_major; /* Rank 1: White major pieces */
    }

    /* White moves first */
    b->turn = WHITE;

    /* Initialize castling flags */
    b->white_king_moved = false;
    b->black_king_moved = false;
    b->white_rook_a_moved = false;
    b->white_rook_h_moved = false;
    b->black_rook_a_moved = false;
    b->black_rook_h_moved = false;

    /* No en passant available at game start */
    b->ep_row = -1;
    b->ep_col = -1;

    /* Reset clocks */
    b->halfmove_clock = 0;
    b->fullmove_number = 1;
    b->history_size = 0;

    /* Record initial starting position for repetition detection */
    record_position(b);
}
/* ============================================================================
 * SECTION 10: MOVE GENERATION
 * ============================================================================
 */

/*
 * append_move
 * Appends a Move to a dynamic MoveList.
 * If the list is full (count == capacity), it doubles the capacity using realloc.
 *
 * NOTE FOR BEGINNERS:
 * A dynamic array in C manages its own heap memory. When the allocated buffer
 * is full, realloc() allocates a larger chunk of memory and copies existing
 * elements over. If allocation fails, the program logs an error and exits safely.
 */
static void append_move(MoveList *list, Move move) {
    if (list->count == list->capacity) {
        size_t next_capacity;
        if (list->capacity == 0) {
            next_capacity = 32;
        } else {
            next_capacity = list->capacity * 2;
        }

        Move *more = (Move *)realloc(list->items, next_capacity * sizeof(Move));
        if (!more) {
            fputs("Out of memory generating moves.\n", stderr);
            exit(EXIT_FAILURE);
        }
        list->items = more;
        list->capacity = next_capacity;
    }
    list->items[list->count++] = move;
}

/*
 * consider_move
 * Evaluates candidate move from (sr, sc) to (er, ec).
 * If the move is in-bounds and legal:
 *   - If it is a pawn reaching the last rank, appends 4 promotion options ('Q', 'R', 'B', 'N').
 *   - Otherwise, appends the move as-is.
 */
static void consider_move(const Board *b, MoveList *list, int sr, int sc, int er, int ec) {
    Move m = {sr, sc, er, ec, '\0'};

    /* Destination must be on the board */
    if (!in_bounds(er, ec)) {
        return;
    }

    /* Move must be legal (not leaving king in check) */
    if (!legal_move(b, m)) {
        return;
    }

    /* Check for pawn promotion */
    if (b->board[sr][sc].type == 'P' && (er == 0 || er == 7)) {
        static const char promos[] = "QRBN";
        for (size_t i = 0; i < sizeof(promos) - 1; ++i) {
            m.promotion = promos[i];
            append_move(list, m);
        }
    } else {
        append_move(list, m);
    }
}

/*
 * generate_sliding_moves
 * Generates sliding moves along rays (used for Bishops, Rooks, and Queens).
 * Continues stepping along each direction until running off the board or hitting a piece.
 */
static void generate_sliding_moves(const Board *b, MoveList *list, int row, int col,
                                  const Direction *directions, size_t direction_count) {
    for (size_t i = 0; i < direction_count; ++i) {
        int step = 1;

        for (;;) {
            int end_row = row + (directions[i].row * step);
            int end_col = col + (directions[i].col * step);

            /* Stop if we step off the board edge */
            if (!in_bounds(end_row, end_col)) {
                break;
            }

            /* Consider this square as a destination */
            consider_move(b, list, row, col, end_row, end_col);

            /* If the square is occupied (by any piece), we cannot slide further through it! */
            if (b->board[end_row][end_col].color != EMPTY) {
                break;
            }

            ++step;
        }
    }
}

/*
 * generate_pawn_moves
 * Generates all candidate moves for the pawn at (row, col):
 *   1. 1 square forward
 *   2. 2 squares forward
 *   3. Diagonal left capture (or en passant)
 *   4. Diagonal right capture (or en passant)
 */
static void generate_pawn_moves(const Board *b, MoveList *list, int row, int col) {
    int dir = pawn_direction(b->board[row][col].color);

    consider_move(b, list, row, col, row + dir, col);
    consider_move(b, list, row, col, row + 2 * dir, col);
    consider_move(b, list, row, col, row + dir, col - 1);
    consider_move(b, list, row, col, row + dir, col + 1);
}

/*
 * generate_knight_moves
 * Generates all 8 candidate L-shaped jumps for the knight at (row, col).
 */
static void generate_knight_moves(const Board *b, MoveList *list, int row, int col) {
    static const Direction jumps[] = {
        {-2, -1}, {-2,  1}, {-1, -2}, {-1,  2},
        { 1, -2}, { 1,  2}, { 2, -1}, { 2,  1}
    };
    size_t num_jumps = sizeof(jumps) / sizeof(jumps[0]);

    for (size_t i = 0; i < num_jumps; ++i) {
        consider_move(b, list, row, col, row + jumps[i].row, col + jumps[i].col);
    }
}

/*
 * generate_king_moves
 * Generates all 8 adjacent moves and 2 castling moves for the king at (row, col).
 */
static void generate_king_moves(const Board *b, MoveList *list, int row, int col) {
    /* 8 adjacent squares */
    for (int delta_row = -1; delta_row <= 1; ++delta_row) {
        for (int delta_col = -1; delta_col <= 1; ++delta_col) {
            if (delta_row == 0 && delta_col == 0) {
                continue;
            }
            consider_move(b, list, row, col, row + delta_row, col + delta_col);
        }
    }

    /* Castling: 2 squares right (kingside) or 2 squares left (queenside) */
    consider_move(b, list, row, col, row, col + 2);
    consider_move(b, list, row, col, row, col - 2);
}

/*
 * generate_piece_moves
 * Generates all moves for a single piece at (row, col) based on its piece type.
 */
static void generate_piece_moves(const Board *b, MoveList *list, int row, int col) {
    static const Direction orthogonal[] = {
        {-1, 0}, {1, 0}, {0, -1}, {0, 1}
    };
    static const Direction diagonal[] = {
        {-1, -1}, {-1, 1}, {1, -1}, {1, 1}
    };
    static const Direction queen_directions[] = {
        {-1, 0}, {1, 0}, {0, -1}, {0, 1},
        {-1, -1}, {-1, 1}, {1, -1}, {1, 1}
    };

    switch (b->board[row][col].type) {
        case 'P':
            generate_pawn_moves(b, list, row, col);
            break;
        case 'N':
            generate_knight_moves(b, list, row, col);
            break;
        case 'B':
            generate_sliding_moves(b, list, row, col, diagonal,
                                   sizeof(diagonal) / sizeof(diagonal[0]));
            break;
        case 'R':
            generate_sliding_moves(b, list, row, col, orthogonal,
                                   sizeof(orthogonal) / sizeof(orthogonal[0]));
            break;
        case 'Q':
            generate_sliding_moves(b, list, row, col, queen_directions,
                                   sizeof(queen_directions) / sizeof(queen_directions[0]));
            break;
        case 'K':
            generate_king_moves(b, list, row, col);
            break;
        default:
            break;
    }
}

/*
 * generate_moves
 * Generates all legal moves for the player whose turn it currently is.
 *
 * Scans the board for pieces belonging to b->turn and collects their moves.
 *
 * NOTE FOR BEGINNERS:
 * The caller of generate_moves is responsible for freeing list.items when done:
 *   MoveList moves = generate_moves(&board);
 *   ... use moves ...
 *   free(moves.items);
 */
static MoveList generate_moves(const Board *b) {
    MoveList list = {NULL, 0, 0};

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            if (b->board[row][col].color == b->turn) {
                generate_piece_moves(b, &list, row, col);
            }
        }
    }

    return list;
}

/*
 * promotion_rank
 * Helper for ordering moves: maps promotion piece to sort rank.
 *   None: 0
 *   'Q':  1
 *   'R':  2
 *   'B':  3
 *   'N':  4
 */
static int promotion_rank(char promotion) {
    if (promotion == 'Q') {
        return 1;
    } else if (promotion == 'R') {
        return 2;
    } else if (promotion == 'B') {
        return 3;
    } else if (promotion == 'N') {
        return 4;
    }
    return 0;
}

/*
 * compare_moves
 * Canonical sort comparator for qsort to sort moves deterministically.
 *
 * Sort order:
 *   1. Start square (row 0 to 7, then col 0 to 7)
 *   2. End square (row 0 to 7, then col 0 to 7)
 *   3. Promotion piece rank (None, then Q, R, B, N)
 */
static int compare_moves(const void *left, const void *right) {
    const Move *a = (const Move *)left;
    const Move *b = (const Move *)right;

    /* Compare starting row */
    if (a->sr != b->sr) {
        return a->sr - b->sr;
    }
    /* Compare starting column */
    if (a->sc != b->sc) {
        return a->sc - b->sc;
    }
    /* Compare destination row */
    if (a->er != b->er) {
        return a->er - b->er;
    }
    /* Compare destination column */
    if (a->ec != b->ec) {
        return a->ec - b->ec;
    }
    /* Compare promotion rank */
    int rank_a = promotion_rank(a->promotion);
    int rank_b = promotion_rank(b->promotion);
    if (rank_a != rank_b) {
        return rank_a - rank_b;
    }

    return 0;
}

/*
 * sorted_moves
 * Generates all legal moves for current player and sorts them canonically.
 */
static MoveList sorted_moves(const Board *b) {
    MoveList moves = generate_moves(b);
    if (moves.count > 1) {
        qsort(moves.items, moves.count, sizeof(Move), compare_moves);
    }
    return moves;
}

/* ============================================================================
 * SECTION 11: REPETITION TRACKING AND DRAW DETECTION
 * ============================================================================
 */

/*
 * piece_key_char
 * Maps a piece to its character in the position hash key:
 *   Empty square: '.'
 *   White piece:  lowercase letter ('p', 'n', 'b', 'r', 'q', 'k')
 *   Black piece:  uppercase letter ('P', 'N', 'B', 'R', 'Q', 'K')
 */
static char piece_key_char(Piece piece) {
    if (piece.color == EMPTY) {
        return '.';
    }
    if (piece.color == WHITE) {
        return (char)tolower((unsigned char)piece.type);
    }
    return piece.type;
}

/*
 * position_key
 * Computes a standardized 72-character key representing the position.
 *
 * Components of the key (following FIDE Article 9.2):
 *   1. 64 characters for piece positions on all squares.
 *   2. 1 character for player to move ('W' or 'B').
 *   3. 4 characters for castling rights (White Q, White K, Black Q, Black K: '1' or '0').
 *   4. En passant square ('row' and 'col' digits if an en passant capture is legally possible; '-' otherwise).
 *   5. Null terminator.
 */
static void position_key(const Board *b, char key[80]) {
    size_t n = 0;

    /* 1. Encode all 64 squares */
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            key[n++] = piece_key_char(b->board[r][c]);
        }
    }

    /* 2. Side to move */
    key[n++] = (b->turn == WHITE) ? 'W' : 'B';

    /* 3. Castling availability */
    key[n++] = (!b->white_king_moved && !b->white_rook_a_moved) ? '1' : '0';
    key[n++] = (!b->white_king_moved && !b->white_rook_h_moved) ? '1' : '0';
    key[n++] = (!b->black_king_moved && !b->black_rook_a_moved) ? '1' : '0';
    key[n++] = (!b->black_king_moved && !b->black_rook_h_moved) ? '1' : '0';

    /* 4. En passant: only included if an en passant capture is actually legally possible */
    bool legal_ep = false;
    if (in_bounds(b->ep_row, b->ep_col)) {
        int dir = (b->turn == WHITE) ? 1 : -1;
        int starting_row = b->ep_row + dir;

        for (int delta_col = -1; delta_col <= 1; delta_col += 2) {
            int sc = b->ep_col + delta_col;
            if (!in_bounds(starting_row, sc)) {
                continue;
            }

            Move candidate = {starting_row, sc, b->ep_row, b->ep_col, '\0'};
            if (legal_move(b, candidate)) {
                legal_ep = true;
                break;
            }
        }
    }

    if (legal_ep) {
        key[n++] = (char)('0' + b->ep_row);
        key[n++] = (char)('0' + b->ep_col);
    } else {
        key[n++] = '-';
    }

    key[n] = '\0';
}

/*
 * record_position
 * Appends the current position's key into the board's dynamic history array.
 */
static void record_position(Board *b) {
    char key[80];
    position_key(b, key);

    if (b->history_size == b->history_capacity) {
        size_t next_capacity;
        if (b->history_capacity == 0) {
            next_capacity = 32;
        } else {
            next_capacity = b->history_capacity * 2;
        }
        Position *new_history = (Position *)realloc(b->history, next_capacity * sizeof(Position));
        if (!new_history) {
            fputs("Out of memory storing chess history.\n", stderr);
            exit(EXIT_FAILURE);
        }
        b->history = new_history;
        b->history_capacity = next_capacity;
    }
    strcpy(b->history[b->history_size++].key, key);
}

/*
 * repetition_count
 * Counts how many times `key` appears in the game's position history.
 */
static unsigned repetition_count(const Board *b, const char *key) {
    unsigned count = 0;
    for (size_t i = 0; i < b->history_size; ++i) {
        if (strcmp(key, b->history[i].key) == 0) {
            ++count;
        }
    }
    return count;
}

/*
 * dead_position
 * Checks for insufficient material to deliver checkmate under FIDE rules:
 *   1. King vs King
 *   2. King + Bishop vs King
 *   3. King + Knight vs King
 *   4. King + Bishop vs King + Bishop where both bishops are on the same square color.
 */
static bool dead_position(const Board *b) {
    int minors = 0;
    int bishops = 0;
    int bishop_color = -1;
    bool bishops_same_color = true;

    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            Piece p = b->board[r][c];
            if (p.color == EMPTY || p.type == 'K') {
                continue;
            }

            /* If there are any Pawns, Rooks, or Queens, checkmate is possible */
            if (p.type != 'B' && p.type != 'N') {
                return false;
            }

            ++minors;
            if (p.type == 'B') {
                ++bishops;
                int sq_color = (r + c) % 2;
                if (bishop_color == -1) {
                    bishop_color = sq_color;
                } else if (bishop_color != sq_color) {
                    bishops_same_color = false;
                }
            }
        }
    }

    /* King vs King, or King + Minor vs King */
    if (minors == 0 || minors == 1) {
        return true;
    }

    /* Only bishops present, and all bishops travel on the same square color */
    if (bishops == minors && bishops_same_color) {
        return true;
    }

    return false;
}

/*
 * automatic_draw
 * Checks mandatory draw conditions:
 *   1. 75-move rule (150 half-moves)
 *   2. Fivefold repetition
 *   3. Dead position (insufficient material)
 */
static bool automatic_draw(const Board *b, const char **reason) {
    if (b->halfmove_clock >= 150) {
        *reason = "75-move rule";
        return true;
    }

    char key[80];
    position_key(b, key);
    if (repetition_count(b, key) >= 5) {
        *reason = "fivefold repetition";
        return true;
    }

    if (dead_position(b)) {
        *reason = "dead position";
        return true;
    }

    return false;
}

/*
 * claimable_draw
 * Checks whether a player can claim a draw:
 *   1. 50-move rule (100 half-moves)
 *   2. Threefold repetition
 */
static bool claimable_draw(const Board *b, Move intended, bool has_intended,
                           const char **reason) {
    const Board *position = b;
    Board after_move = {0};
    char key[80];

    if (has_intended) {
        if (!legal_move(b, intended)) {
            return false;
        }
        after_move = *b;
        make_move(&after_move, intended);
        position = &after_move;
    }

    if (position->halfmove_clock >= 100) {
        *reason = "50-move rule";
        return true;
    }

    position_key(position, key);
    unsigned repetitions_needed = has_intended ? 2u : 3u;
    if (repetition_count(position, key) >= repetitions_needed) {
        *reason = "threefold repetition";
        return true;
    }

    return false;
}

/*
 * game_over
 * Determines if the game has ended:
 *   - Checkmate: Player to move is in check and has 0 legal moves.
 *   - Stalemate: Player to move is NOT in check, but has 0 legal moves.
 *   - Automatic Draw: 75-move rule, fivefold repetition, or dead position.
 */
static bool game_over(const Board *b, bool *stalemate, const char **draw_reason) {
    MoveList moves = generate_moves(b);
    bool no_moves = (moves.count == 0);
    free(moves.items);

    *stalemate = false;
    if (no_moves) {
        *stalemate = !is_in_check(b, b->turn);
        return true;
    }
    return automatic_draw(b, draw_reason);
}

/* ============================================================================
 * SECTION 12: TERMINAL BOARD DISPLAY AND STEP 1 SELECTION
 * ============================================================================
 */

/*
 * read_input_line
 * Safely reads a line of text from standard input (stdin) into `input` buffer.
 * Strips trailing newline ('\n') and carriage return ('\r').
 * If input exceeds buffer capacity, discards remaining characters on line and returns error.
 */
static InputResult read_input_line(char *input, int capacity) {
    if (!fgets(input, capacity, stdin)) {
        return INPUT_READ_EOF;
    }

    size_t length = strlen(input);

    /* Strip trailing newline character */
    if (length > 0 && input[length - 1] == '\n') {
        input[--length] = '\0';
    } else if (length == (size_t)(capacity - 1)) {
        /* Line was longer than buffer: consume remaining line from stdin */
        int ch = getchar();
        if (ch != '\n' && ch != EOF) {
            while ((ch = getchar()) != '\n' && ch != EOF) { }
            puts(RED "Input too long." RESET);
            return INPUT_READ_TOO_LONG;
        }
    }

    /* Strip trailing Windows carriage return if present */
    if (length > 0 && input[length - 1] == '\r') {
        input[length - 1] = '\0';
    }

    return INPUT_READ_OK;
}

/*
 * parse_command
 * Matches user input against recognized command words.
 */
static Command parse_command(const char *input) {
    if (!strcmp(input, "n") || !strcmp(input, "N")) {
        return COMMAND_SHORT_NEW;
    }
    if (!strcmp(input, "new") || !strcmp(input, "NEW") ||
        !strcmp(input, "select none")) {
        return COMMAND_NEW;
    }
    if (!strcmp(input, "f") || !strcmp(input, "F")) {
        return COMMAND_FINALIZE;
    }
    if (!strcmp(input, "p") || !strcmp(input, "P")) {
        return COMMAND_PREVIEW;
    }
    if (!strcmp(input, "quit") || !strcmp(input, "exit")) {
        return COMMAND_QUIT;
    }
    if (!strcmp(input, "restart")) {
        return COMMAND_RESTART;
    }
    if (!strcmp(input, "resign")) {
        return COMMAND_RESIGN;
    }
    if (!strcmp(input, "claim")) {
        return COMMAND_CLAIM;
    }
    return COMMAND_OTHER;
}

/*
 * is_game_command
 * Returns true if command is a game control command (quit, restart, resign, claim).
 */
static bool is_game_command(Command command) {
    return command == COMMAND_QUIT || command == COMMAND_RESTART ||
           command == COMMAND_RESIGN || command == COMMAND_CLAIM;
}

/*
 * legal_destination_map
 * Fills an 8x8 boolean array where destinations[row][col] is true if the piece
 * on (row, col) can legally move to that square.
 */
static void legal_destination_map(const Board *position, int row, int col,
                                  Color side_to_move,
                                  bool destinations[BOARD_SIZE][BOARD_SIZE]) {
    memset(destinations, 0, sizeof(bool) * BOARD_SIZE * BOARD_SIZE);

    if (!in_bounds(row, col)) {
        return;
    }
    if (position->board[row][col].color == EMPTY) {
        return;
    }

    Board view = *position;
    view.turn = side_to_move;
    MoveList moves = generate_moves(&view);

    for (size_t i = 0; i < moves.count; ++i) {
        Move move = moves.items[i];
        if (move.sr == row && move.sc == col) {
            destinations[move.er][move.ec] = true;
        }
    }
    free(moves.items);
}

/*
 * selected_destinations
 * Fills destinations for the currently selected piece, verifying ownership.
 */
static void selected_destinations(const Board *b, int row, int col,
                                  bool destinations[BOARD_SIZE][BOARD_SIZE]) {
    if (!in_bounds(row, col) || b->board[row][col].color != b->turn) {
        memset(destinations, 0, sizeof(bool) * BOARD_SIZE * BOARD_SIZE);
        return;
    }
    legal_destination_map(b, row, col, b->turn, destinations);
}

/*
 * print_selection_near_prompt
 * Prints available legal moves next to the input prompt (e.g. "Selected e2 -> e3 e4").
 */
static void print_selection_near_prompt(const Board *b, int row, int col) {
    bool destinations[BOARD_SIZE][BOARD_SIZE];
    unsigned count = 0;

    if (!in_bounds(row, col)) {
        return;
    }

    selected_destinations(b, row, col, destinations);
    printf("Selected %c%d ->", 'a' + col, 8 - row);

    for (int r = 7; r >= 0; --r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            if (destinations[r][c]) {
                printf(" %c%d", 'a' + c, 8 - r);
                ++count;
            }
        }
    }
    if (count == 0) {
        printf(" (no legal moves)");
    }
    puts("");
}

/*
 * display
 * Renders the 8x8 chessboard to the terminal using ANSI colors.
 * Highlights the selected piece with brackets [P], empty destinations with *,
 * and captures with parentheses (p).
 */
static void display(const Board *b, int selected_row, int selected_col) {
    bool destinations[BOARD_SIZE][BOARD_SIZE];
    selected_destinations(b, selected_row, selected_col, destinations);

    puts("\n    a   b   c   d   e   f   g   h");
    puts("  +---+---+---+---+---+---+---+---+");

    for (int row = 0; row < BOARD_SIZE; ++row) {
        printf("%d |", 8 - row);

        for (int col = 0; col < BOARD_SIZE; ++col) {
            Piece piece = b->board[row][col];
            bool light_square = ((row + col) % 2 == 0);
            const char *background;
            const char *foreground;
            char symbol = ' ';
            char left = ' ';
            char right = ' ';

            if (light_square) {
                background = LIGHT_SQUARE_BG;
                foreground = DARK_TEXT_FG;
            } else {
                background = DARK_SQUARE_BG;
                foreground = LIGHT_TEXT_FG;
            }

            symbol = piece_symbol(piece);

            /* Highlight selected piece or legal destinations */
            if (row == selected_row && col == selected_col) {
                left = '[';
                right = ']';
            } else if (destinations[row][col]) {
                if (piece.color == EMPTY) {
                    symbol = '*';
                } else {
                    left = '(';
                    right = ')';
                }
            }

            /* Print 3 characters per cell to keep board columns aligned */
            printf("%s%s%c%c%c%s|", background, foreground, left, symbol, right, RESET);
        }

        printf(" %d\n", 8 - row);
        puts("  +---+---+---+---+---+---+---+---+");
    }
    puts("    a   b   c   d   e   f   g   h\n");

    /* If a piece is currently selected, show summary of its destinations */
    if (in_bounds(selected_row, selected_col)) {
        Piece piece = b->board[selected_row][selected_col];
        unsigned unique_squares = 0;

        printf("SELECTED: %s %c at %c%d\n", color_name(piece.color),
               piece.type, 'a' + selected_col, 8 - selected_row);
        printf("LEGAL DESTINATIONS:");
        for (int row = 0; row < BOARD_SIZE; ++row) {
            for (int col = 0; col < BOARD_SIZE; ++col) {
                if (destinations[row][col]) {
                    printf(" %c%d", 'a' + col, 8 - row);
                    ++unique_squares;
                }
            }
        }
        if (unique_squares == 0) {
            printf(" (none)");
        }
        printf("\nTOTAL: %u square(s)\n", unique_squares);
        puts("LEGEND: [P]=selected piece, *=empty legal destination, (p)=legal capture");
        puts("Selection is informational: no piece has moved.\n");
    }
}

/* ============================================================================
 * SECTION 13: STEP 2 MOVE PREVIEW AND IMPACT ANALYSIS
 * ============================================================================
 */

/*
 * list_piece_moves
 * Returns the destination squares for a specific piece as a text string.
 * Evaluates move legality as if it were currently that piece's turn to move.
 */
static void list_piece_moves(const Board *position, int row, int col,
                             char *output, size_t capacity) {
    Board view = *position;
    MoveList moves;
    size_t used = 0;
    bool seen[BOARD_SIZE][BOARD_SIZE] = {{false}};
    Piece piece = position->board[row][col];

    output[0] = '\0';
    if (piece.color == EMPTY) {
        return;
    }

    view.turn = piece.color;
    moves = generate_moves(&view);

    for (size_t i = 0; i < moves.count; ++i) {
        Move m = moves.items[i];
        bool is_this_piece = (m.sr == row && m.sc == col);
        bool destination_was_listed = seen[m.er][m.ec];
        if (!is_this_piece || destination_was_listed) {
            continue;
        }

        seen[m.er][m.ec] = true;
        if (used < capacity) {
            const char *separator = (used == 0) ? "" : " ";
            int n = snprintf(output + used, capacity - used,
                             "%s%c%d", separator, 'a' + m.ec, 8 - m.er);
            if (n < 0) {
                break;
            }
            if ((size_t)n >= capacity - used) {
                used = capacity - 1;
                break;
            }
            used += (size_t)n;
        }
    }

    free(moves.items);
    if (used == 0) {
        snprintf(output, capacity, "(none)");
    }
}

/*
 * next_chunk
 * Extracts the next word-wrapped chunk of text from source up to COMPARE_WIDTH chars.
 * Used for aligning the two columns of the Step 2 preview report.
 */
static size_t next_chunk(const char *source, size_t at, char *out) {
    size_t length = strlen(source);
    size_t copied = 0;

    while (at < length && source[at] == ' ') {
        ++at;
    }
    while (at < length) {
        size_t word_length = strcspn(source + at, " ");
        size_t separator_length = (copied == 0) ? 0 : 1;

        if (copied + separator_length + word_length > COMPARE_WIDTH) {
            if (copied == 0) {
                memcpy(out, source + at, COMPARE_WIDTH);
                at += COMPARE_WIDTH;
                copied = COMPARE_WIDTH;
            }
            break;
        }

        if (separator_length != 0) {
            out[copied++] = ' ';
        }
        memcpy(out + copied, source + at, word_length);
        copied += word_length;
        at += word_length;

        while (at < length && source[at] == ' ') {
            ++at;
        }
    }

    out[copied] = '\0';
    return at;
}

/*
 * print_side_by_side
 * Prints two text strings side-by-side in columns formatted to COMPARE_WIDTH.
 */
static void print_side_by_side(const char *before, const char *after) {
    size_t left_offset = 0;
    size_t right_offset = 0;
    size_t before_length = strlen(before);
    size_t after_length = strlen(after);
    char left_chunk[COMPARE_WIDTH + 1];
    char right_chunk[COMPARE_WIDTH + 1];

    do {
        left_offset = next_chunk(before, left_offset, left_chunk);
        right_offset = next_chunk(after, right_offset, right_chunk);

        printf("%-*s | %s\n", COMPARE_WIDTH, left_chunk, right_chunk);
    } while (left_offset < before_length || right_offset < after_length);
}

/*
 * make_piece_description
 * Formats a piece description line: "square piece: destinations" (e.g. "e2 P: e3 e4").
 */
static void make_piece_description(const Board *position, int row, int col,
                                   char *output, size_t capacity) {
    char destinations[256];
    Piece piece = position->board[row][col];
    if (piece.color == EMPTY) {
        snprintf(output, capacity, "(captured)");
        return;
    }

    list_piece_moves(position, row, col, destinations, sizeof(destinations));
    char displayed_piece = piece_symbol(piece);

    snprintf(output, capacity, "%c%d %c: %s",
             'a' + col, 8 - row, displayed_piece, destinations);
}

/*
 * piece_destination_map
 * Fills destination map for a single piece.
 */
static void piece_destination_map(const Board *position, int row, int col,
                                  bool destination[BOARD_SIZE][BOARD_SIZE]) {
    Color side_to_move = position->board[row][col].color;
    legal_destination_map(position, row, col, side_to_move, destination);
}

/*
 * append_destination
 * Helper to append a square coordinate to a text buffer.
 */
static void append_destination(char *output, size_t capacity, int row, int col) {
    size_t used = strlen(output);
    if (used >= capacity) {
        return;
    }
    snprintf(output + used, capacity - used, "%s%c%d",
             used ? " " : "", 'a' + col, 8 - row);
}

/*
 * print_piece_changes
 * Compares destinations of a piece before and after a proposed move.
 * Reports GAINED, LOST, and UNCHANGED destination squares.
 */
static void print_piece_changes(const Board *before, const Board *after,
                                int before_row, int before_col,
                                int after_row, int after_col, bool captured) {
    bool old_destinations[BOARD_SIZE][BOARD_SIZE];
    bool new_destinations[BOARD_SIZE][BOARD_SIZE];
    char gained[256] = "";
    char lost[256] = "";
    char unchanged[256] = "";

    if (captured) {
        puts("    CHANGE: CAPTURED - this piece has no AFTER moves.");
        return;
    }

    piece_destination_map(before, before_row, before_col, old_destinations);
    piece_destination_map(after, after_row, after_col, new_destinations);

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            bool in_new = new_destinations[row][col];
            bool in_old = old_destinations[row][col];

            if (in_new && !in_old) {
                append_destination(gained, sizeof(gained), row, col);
            } else if (in_old && !in_new) {
                append_destination(lost, sizeof(lost), row, col);
            } else if (in_old && in_new) {
                append_destination(unchanged, sizeof(unchanged), row, col);
            }
        }
    }

    if (gained[0] == '\0' && lost[0] == '\0') {
        puts("    CHANGE: UNCHANGED - no destinations gained or lost.");
    } else {
        puts("    CHANGE: destinations changed.");
    }
    printf("    GAINED: %s\n", gained[0] ? gained : "(none)");
    printf("    LOST: %s\n", lost[0] ? lost : "(none)");
    printf("    UNCHANGED: %s\n", unchanged[0] ? unchanged : "(none)");
}

/*
 * is_en_passant_capture
 * Checks if the piece on (row, col) is captured by en passant during proposed move.
 */
static bool is_en_passant_capture(const Board *before, Move proposed,
                                 int row, int col) {
    Piece moving_piece = before->board[proposed.sr][proposed.sc];
    return moving_piece.type == 'P' &&
           proposed.er == before->ep_row &&
           proposed.ec == before->ep_col &&
           row == proposed.sr &&
           col == proposed.ec;
}

/*
 * resolve_piece_after_move
 * Determines where a piece on (row, col) ends up after `proposed` move is made.
 * Accounts for direct captures, en passant captures, and castling rook relocation.
 */
static void resolve_piece_after_move(const Board *before, Move proposed,
                                   int row, int col,
                                   int *after_row, int *after_col,
                                   bool *captured) {
    *after_row = row;
    *after_col = col;
    *captured = false;

    /* Direct capture */
    if (row == proposed.er && col == proposed.ec) {
        *captured = true;
    }
    /* En passant capture */
    if (is_en_passant_capture(before, proposed, row, col)) {
        *captured = true;
    }

    /* Castling rook relocation */
    Piece moving_piece = before->board[proposed.sr][proposed.sc];
    bool is_castling = (moving_piece.type == 'K' &&
                        abs(proposed.ec - proposed.sc) == 2 &&
                        row == proposed.sr);
    if (is_castling) {
        if (proposed.ec == CASTLE_KINGSIDE_KING_DEST_COL && col == ROOK_KINGSIDE_START_COL) {
            *after_col = CASTLE_KINGSIDE_ROOK_DEST_COL;
        }
        if (proposed.ec == CASTLE_QUEENSIDE_KING_DEST_COL && col == ROOK_QUEENSIDE_START_COL) {
            *after_col = CASTLE_QUEENSIDE_ROOK_DEST_COL;
        }
    }
}

/*
 * compare_all_other_pieces
 * Generates the complete side-by-side comparative report for every piece
 * on the board (other than the piece being moved) before and after the move.
 */
static void compare_all_other_pieces(const Board *before, const Board *after,
                                     Move proposed) {
    for (Color side = WHITE; side <= BLACK; side = (Color)(side + 1)) {
        const char *side_name = (side == WHITE) ? "WHITE" : "BLACK";

        puts("");
        printf("%s PIECES (excluding selected piece)\n", side_name);
        print_side_by_side("BEFORE: square piece -> legal destinations",
                           "AFTER: square piece -> legal destinations");
        puts("-------------------------------------------------------------------+-------------------------------------------------------------------");

        for (int row = 0; row < BOARD_SIZE; ++row) {
            for (int col = 0; col < BOARD_SIZE; ++col) {
                Piece piece = before->board[row][col];
                bool is_moving_side = (piece.color == side);
                bool is_selected_piece = (row == proposed.sr && col == proposed.sc);

                if (!is_moving_side || is_selected_piece) {
                    continue;
                }

                int after_row = row;
                int after_col = col;
                char before_description[320];
                char after_description[320];
                bool captured = false;

                resolve_piece_after_move(before, proposed, row, col,
                                        &after_row, &after_col, &captured);

                make_piece_description(before, row, col,
                                       before_description, sizeof(before_description));
                if (captured) {
                    snprintf(after_description, sizeof(after_description),
                             "(captured at %c%d)", 'a' + col, 8 - row);
                } else {
                    make_piece_description(after, after_row, after_col,
                                           after_description, sizeof(after_description));
                }

                print_side_by_side(before_description, after_description);
                print_piece_changes(before, after, row, col,
                                    after_row, after_col, captured);
            }
        }
    }
}

/*
 * show_step2_after
 * Creates a simulated position with `proposed` played, and displays the
 * two-column comparative analysis report.
 */
static void show_step2_after(const Board *board, Move proposed) {
    Board simulated = *board;
    printf("\nPREVIEW ONLY: %c%d -> %c%d (NOT PLAYED)\n",
           'a' + proposed.sc, 8 - proposed.sr, 'a' + proposed.ec, 8 - proposed.er);
    make_move(&simulated, proposed);
    puts("Widen your console to about 140 columns for the two-column report.");
    puts("CHANGE shows gained, lost, and unchanged destinations for each other piece.");
    puts("LEGAL MOVE LIST NOTE: Each side is evaluated as if it were that side's turn.");
    puts("Black and White possibilities are shown for comparison; only the actual");
    puts("side to move can play immediately. Check restrictions still apply.");
    compare_all_other_pieces(board, &simulated, proposed);
    puts("\nThe real board and player turn have NOT changed.");
    puts("Press F then Enter to FINALIZE this previewed move.");
    puts("Press P then Enter to preview another destination, or N for a new piece.");
}
/* ============================================================================
 * SECTION 14: STAGE 3S - PRACTICE BOARDS (FEN IMPORT AND EXPORT)
 * ============================================================================
 */

/*
 * split_fen_fields
 * Splits a FEN string at single spaces into up to max_fields substrings.
 * Modifies `text` in-place by replacing space delimiters with null terminators ('\0').
 *
 * NOTE FOR BEGINNERS:
 * In C, strings are arrays of characters ending with '\0'. By changing a space ' '
 * character in the string into '\0', we turn one string into multiple strings without
 * allocating any new memory!
 *
 * Parameters:
 *   text       - Null-terminated string to split
 *   fields     - Array of char pointers where each field's start address is stored
 *   max_fields - Maximum number of fields expected (6 for FEN)
 *
 * Returns:
 *   Number of fields parsed, or -1 if formatting is invalid.
 */
static int split_fen_fields(char *text, char *fields[], int max_fields) {
    int count = 0;
    char *start = text;

    for (;;) {
        char *space = strchr(start, ' ');

        /* Reject empty fields or too many fields */
        if (count == max_fields || *start == '\0' || *start == ' ') {
            return -1;
        }

        fields[count] = start;
        ++count;

        /* If no more spaces, this was the final field */
        if (space == NULL) {
            return count;
        }

        /* Replace space with null terminator to end this field string */
        *space = '\0';
        /* Advance start pointer to the beginning of the next field */
        start = space + 1;
    }
}

/*
 * fen_piece_from_char
 * Converts a FEN character ('P', 'p', 'N', 'n', etc.) into a Piece struct.
 * Uppercase = WHITE, lowercase = BLACK.
 */
static bool fen_piece_from_char(char symbol, Piece *piece) {
    char upper = (char)toupper((unsigned char)symbol);
    if (strchr("PNBRQK", upper) == NULL) {
        return false;
    }
    piece->type = upper;
    piece->color = isupper((unsigned char)symbol) ? WHITE : BLACK;
    return true;
}

/*
 * fen_read_placement
 * Parses Field 1 of a FEN string: the 8 ranks of piece placements separated by '/'.
 */
static const char *fen_read_placement(Board *b, const char *text) {
    int row = 0;
    int col = 0;

    for (const char *p = text; *p != '\0'; ++p) {
        if (*p == '/') {
            if (col != BOARD_SIZE) {
                return "a rank does not have exactly 8 squares";
            }
            ++row;
            col = 0;
            if (row > 7) {
                return "more than 8 ranks";
            }
        } else if (*p >= '1' && *p <= '8') {
            col += (*p - '0');
            if (col > BOARD_SIZE) {
                return "a rank does not have exactly 8 squares";
            }
        } else if (isdigit((unsigned char)*p)) {
            return "a rank does not have exactly 8 squares"; /* '0' or '9' empty squares */
        } else {
            Piece piece;
            if (!fen_piece_from_char(*p, &piece)) {
                return "unknown piece letter";
            }
            if (col > 7) {
                return "a rank does not have exactly 8 squares";
            }
            b->board[row][col] = piece;
            ++col;
        }
    }

    if (row != 7 || col != BOARD_SIZE) {
        return "the board must have exactly 8 ranks of 8 squares";
    }
    return NULL;
}

/*
 * piece_at
 * Helper returning true if the piece on (row, col) matches given type and color.
 */
static bool piece_at(const Board *b, int row, int col, char type, Color color) {
    return (b->board[row][col].type == type && b->board[row][col].color == color);
}

/*
 * fen_read_castling
 * Parses Field 3 of a FEN string: castling rights ("-" or letters from "KQkq" in order).
 * Ensures that the King and corresponding Rook are actually on their home squares.
 */
static const char *fen_read_castling(Board *b, const char *text) {
    bool wk = false, wq = false, bk = false, bq = false;

    if (text == NULL || text[0] == '\0') {
        return "castling field cannot be empty";
    }

    if (strcmp(text, "-") != 0) {
        const char *order = "KQkq";
        const char *next = order;
        for (const char *p = text; *p != '\0'; ++p) {
            const char *found = strchr(next, *p);
            if (found == NULL) {
                return "castling field must be - or letters from KQkq in that order";
            }
            next = found + 1;
            if (*p == 'K') wk = true;
            if (*p == 'Q') wq = true;
            if (*p == 'k') bk = true;
            if (*p == 'q') bq = true;
        }
    }

    /* Verify that castling rights correspond to King on starting square */
    if ((wk || wq) && !piece_at(b, 7, 4, 'K', WHITE)) {
        return "White castling right without the king on e1";
    }
    if ((bk || bq) && !piece_at(b, 0, 4, 'K', BLACK)) {
        return "Black castling right without the king on e8";
    }

    /* Verify that castling rights correspond to Rooks on starting squares */
    if ((wk && !piece_at(b, 7, 7, 'R', WHITE)) || (wq && !piece_at(b, 7, 0, 'R', WHITE)) ||
        (bk && !piece_at(b, 0, 7, 'R', BLACK)) || (bq && !piece_at(b, 0, 0, 'R', BLACK))) {
        return "castling right without the rook on its starting square";
    }

    b->white_king_moved   = !(wk || wq);
    b->black_king_moved   = !(bk || bq);
    b->white_rook_h_moved = !wk;
    b->white_rook_a_moved = !wq;
    b->black_rook_h_moved = !bk;
    b->black_rook_a_moved = !bq;
    return NULL;
}

/*
 * fen_read_en_passant
 * Parses Field 4 of a FEN string: en passant target square ("-" or algebraic coordinate).
 */
static const char *fen_read_en_passant(Board *b, const char *text) {
    int row, col;

    b->ep_row = -1;
    b->ep_col = -1;

    if (strcmp(text, "-") == 0) {
        return NULL;
    }
    if (strlen(text) != 2 || !parse_square(text, &row, &col)) {
        return "en passant field must be - or a square";
    }

    /* White to move means Black just moved a pawn 2 squares forward:
     * skipped square is on Rank 6 (row 2), pawn is on Rank 5 (row 3), square behind is on Rank 7 (row 1).
     * Black to move means White just moved a pawn 2 squares forward:
     * skipped square is on Rank 3 (row 5), pawn is on Rank 4 (row 4), square behind is on Rank 2 (row 6).
     */
    int expected_row = (b->turn == WHITE) ? 2 : 5;
    int pawn_row     = (b->turn == WHITE) ? 3 : 4;
    int start_row    = (b->turn == WHITE) ? 1 : 6;
    Color mover      = opposite(b->turn);

    if (row != expected_row) {
        return "en passant square is on the wrong rank for the side to move";
    }
    if (!piece_at(b, pawn_row, col, 'P', mover) ||
        b->board[row][col].color != EMPTY ||
        b->board[start_row][col].color != EMPTY) {
        return "en passant square does not match a pawn that just moved two squares";
    }

    b->ep_row = row;
    b->ep_col = col;
    return NULL;
}

/*
 * fen_read_number
 * Parses a non-negative integer from text (used for halfmove clock and fullmove number).
 */
static bool fen_read_number(const char *text, int minimum, int *value) {
    long number = 0;

    if (*text == '\0' || strlen(text) > 5) {
        return false;
    }
    for (const char *p = text; *p != '\0'; ++p) {
        if (!isdigit((unsigned char)*p)) {
            return false;
        }
        number = number * 10 + (*p - '0');
    }
    if (number < minimum) {
        return false;
    }
    *value = (int)number;
    return true;
}

/*
 * fen_check_material
 * Validates that piece counts do not exceed what any legal chess game allows.
 * Also checks that no pawns exist on Rank 1 or Rank 8.
 */
static const char *fen_check_material(const Board *b, Color side) {
    int count[128] = {0};
    int total = 0;

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            Piece p = b->board[row][col];
            if (p.color != side) {
                continue;
            }
            ++count[(unsigned char)p.type];
            ++total;
            if (p.type == 'P' && (row == 0 || row == 7)) {
                return "a pawn is on the first or last rank";
            }
        }
    }

    if (count['K'] != 1) {
        return (side == WHITE) ? "White must have exactly one king" : "Black must have exactly one king";
    }

    int promoted = (count['Q'] > 1 ? count['Q'] - 1 : 0) +
                   (count['R'] > 2 ? count['R'] - 2 : 0) +
                   (count['B'] > 2 ? count['B'] - 2 : 0) +
                   (count['N'] > 2 ? count['N'] - 2 : 0);

    if (count['P'] > 8 || total > 16 || promoted > (8 - count['P'])) {
        return (side == WHITE) ? "White has more pieces than a game allows" : "Black has more pieces than a game allows";
    }
    return NULL;
}

/*
 * count_attackers
 * Counts how many pieces of color `by` attack square (row, col).
 */
static int count_attackers(const Board *b, int row, int col, Color by) {
    int attackers = 0;
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            if (b->board[r][c].color == by && piece_attacks(b, r, c, row, col)) {
                ++attackers;
            }
        }
    }
    return attackers;
}

/*
 * load_fen
 * Parses, validates, and loads a chess position from a FEN string into `*b`.
 *
 * If the FEN string is invalid or violates chess rules, returns false and stores
 * the human-readable explanation in `*reason` without modifying `*b`.
 */
static bool load_fen(Board *b, const char *fen, const char **reason) {
    if (fen == NULL) {
        *reason = "FEN text is missing";
        return false;
    }
    char text[FEN_TEXT_SIZE];
    char *fields[6];
    Board next = {0};
    int king_row = 0;
    int king_col = 0;

    if (strlen(fen) >= sizeof(text)) {
        *reason = "FEN text is too long";
        return false;
    }
    strcpy(text, fen);

    int field_count = split_fen_fields(text, fields, 6);
    if (field_count != 4 && field_count != 6) {
        *reason = "a FEN has 6 fields (or 4) separated by single spaces";
        return false;
    }

    /* Initialize all squares to empty */
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            next.board[row][col] = empty_piece();
        }
    }

    /* Field 1: Piece placement */
    *reason = fen_read_placement(&next, fields[0]);
    if (*reason != NULL) {
        return false;
    }

    /* Field 2: Side to move ("w" or "b") */
    if (strcmp(fields[1], "w") != 0 && strcmp(fields[1], "b") != 0) {
        *reason = "side to move must be w or b";
        return false;
    }
    next.turn = (fields[1][0] == 'w') ? WHITE : BLACK;

    /* Validate piece material counts */
    *reason = fen_check_material(&next, WHITE);
    if (*reason == NULL) {
        *reason = fen_check_material(&next, BLACK);
    }
    /* Field 3: Castling rights */
    if (*reason == NULL) {
        *reason = fen_read_castling(&next, fields[2]);
    }
    /* Field 4: En passant square */
    if (*reason == NULL) {
        *reason = fen_read_en_passant(&next, fields[3]);
    }
    if (*reason != NULL) {
        return false;
    }

    /* Fields 5 & 6: Halfmove clock and fullmove number (optional, default 0 and 1) */
    next.halfmove_clock = 0;
    next.fullmove_number = 1;
    if (field_count == 6) {
        if (!fen_read_number(fields[4], 0, &next.halfmove_clock) ||
            !fen_read_number(fields[5], 1, &next.fullmove_number)) {
            *reason = "halfmove clock and move number must be whole numbers (move number at least 1)";
            return false;
        }
    }

    /* In chess, the side that is NOT to move cannot be left in check! */
    if (is_in_check(&next, opposite(next.turn))) {
        *reason = "the side that is not to move is in check";
        return false;
    }

    /* Side to move must have a King */
    if (!find_king(&next, next.turn, &king_row, &king_col)) {
        *reason = "the side to move has no king";
        return false;
    }

    /* A king cannot be checked by more than 2 pieces simultaneously */
    if (count_attackers(&next, king_row, king_col, opposite(next.turn)) > 2) {
        *reason = "the king to move is attacked by more than two pieces";
        return false;
    }

    /* Inherit the existing dynamic history buffer */
    next.history = b->history;
    next.history_capacity = b->history_capacity;
    next.history_size = 0;

    /* Commit position */
    *b = next;
    record_position(b);
    *reason = NULL;
    return true;
}

/*
 * board_to_fen
 * Serializes the current board state into standard FEN notation.
 */
static void board_to_fen(const Board *b, char out[FEN_TEXT_SIZE]) {
    size_t n = 0;

    /* 1. Piece placement */
    for (int row = 0; row < BOARD_SIZE; ++row) {
        int empty_count = 0;
        for (int col = 0; col < BOARD_SIZE; ++col) {
            Piece piece = b->board[row][col];
            if (piece.color == EMPTY) {
                ++empty_count;
                continue;
            }
            if (empty_count > 0) {
                out[n++] = (char)('0' + empty_count);
                empty_count = 0;
            }
            out[n++] = piece_symbol(piece);
        }
        if (empty_count > 0) {
            out[n++] = (char)('0' + empty_count);
        }
        if (row < 7) {
            out[n++] = '/';
        }
    }

    /* 2. Side to move */
    out[n++] = ' ';
    out[n++] = (b->turn == WHITE) ? 'w' : 'b';
    out[n++] = ' ';

    /* 3. Castling rights */
    size_t castling_start = n;
    if (!b->white_king_moved && !b->white_rook_h_moved) {
        out[n++] = 'K';
    }
    if (!b->white_king_moved && !b->white_rook_a_moved) {
        out[n++] = 'Q';
    }
    if (!b->black_king_moved && !b->black_rook_h_moved) {
        out[n++] = 'k';
    }
    if (!b->black_king_moved && !b->black_rook_a_moved) {
        out[n++] = 'q';
    }
    if (n == castling_start) {
        out[n++] = '-';
    }

    /* 4. En passant target square */
    out[n++] = ' ';
    if (in_bounds(b->ep_row, b->ep_col)) {
        out[n++] = (char)('a' + b->ep_col);
        out[n++] = (char)('0' + (8 - b->ep_row));
    } else {
        out[n++] = '-';
    }

    /* 5 & 6. Halfmove clock and fullmove number */
    if (n < FEN_TEXT_SIZE) {
        snprintf(out + n, FEN_TEXT_SIZE - n, " %d %d", b->halfmove_clock, b->fullmove_number);
    } else if (FEN_TEXT_SIZE > 0) {
        out[FEN_TEXT_SIZE - 1] = '\0';
    }
}

/*
 * follow_piece
 * Follows a single piece across a move for piece-tracking reports.
 * Non-static: exported for test suites and calculator stages.
 */
FollowCase follow_piece(const Board *before, Move move, int row, int col,
                        int *after_row, int *after_col, char *after_type);

FollowCase follow_piece(const Board *before, Move move, int row, int col,
                        int *after_row, int *after_col, char *after_type) {
    Piece piece = before->board[row][col];
    Piece mover = before->board[move.sr][move.sc];
    bool captured = false;

    *after_type = piece.type;

    /* If this is the piece that moved */
    if (row == move.sr && col == move.sc) {
        *after_row = move.er;
        *after_col = move.ec;
        if (mover.type == 'P' && (move.er == 0 || move.er == 7)) {
            *after_type = (move.promotion == '\0') ? 'Q' : move.promotion;
            return FOLLOW_PROMOTED;
        }
        return FOLLOW_MOVED;
    }

    /* Other pieces: check if captured or castled rook */
    resolve_piece_after_move(before, move, row, col, after_row, after_col, &captured);
    if (captured) {
        *after_row = -1;
        *after_col = -1;
        return FOLLOW_CAPTURED;
    }
    if (*after_col != col) {
        return FOLLOW_CASTLING_ROOK;
    }
    return FOLLOW_STAYS;
}

/* ============================================================================
 * SECTION 15: STAGE 3A - FACT CALCULATOR REPORT AND PIECE TRACKER
 * ============================================================================
 */

/*
 * text_add
 * Formats text using printf-style arguments and appends it to a TextBuffer.
 * Automatically doubles the TextBuffer's capacity as needed using realloc.
 *
 * NOTE FOR BEGINNERS:
 * In C, functions with variable numbers of arguments (like printf) use stdarg.h.
 * va_list holds the argument list, va_start initializes it, and vsnprintf
 * formats the string safely into a temporary buffer.
 */
static void text_add(TextBuffer *t, const char *format, ...) {
    va_list args;
    char line[512];

    va_start(args, format);
    int n = vsnprintf(line, sizeof(line), format, args);
    va_end(args);

    if (n < 0) {
        return;
    }

    size_t add_len = strlen(line);

    /* Resize buffer if additional text exceeds current capacity */
    if (t->length + add_len + 1 > t->capacity) {
        size_t next_capacity = (t->capacity == 0) ? 1024 : t->capacity;
        while (t->length + add_len + 1 > next_capacity) {
            next_capacity *= 2;
        }
        char *more = (char *)realloc(t->text, next_capacity);
        if (!more) {
            fputs("Out of memory building the calculator report.\n", stderr);
            exit(EXIT_FAILURE);
        }
        t->text = more;
        t->capacity = next_capacity;
    }

    memcpy(t->text + t->length, line, add_len + 1);
    t->length += add_len;
}

/*
 * tracker_init
 * Assigns unique identity numbers (1..32) to all pieces on the board.
 */
static void tracker_init(Tracker *t, const Board *b) {
    int next_id = 1;

    memset(t, 0, sizeof(*t));
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            Piece piece = b->board[row][col];
            if (piece.color == EMPTY || next_id >= CALC_MAX_ID) {
                continue;
            }
            t->grid.id[row][col] = next_id;
            t->color[next_id] = piece.color;
            ++next_id;
        }
    }
}

/*
 * make_names
 * Assigns readable names to pieces (e.g. "P e2", "N g1") based on their starting squares.
 */
static void make_names(const Board *b, const Tracker *t, Names *names) {
    memset(names, 0, sizeof(*names));
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = t->grid.id[row][col];
            if (id > 0 && id < CALC_MAX_ID) {
                char square[3];
                square_text(square_index(row, col), square);
                snprintf(names->name[id], sizeof(names->name[id]),
                         "%c %s", b->board[row][col].type, square);
            }
        }
    }
}

/*
 * take_snapshot
 * Takes a snapshot of all piece mobility and square reach for fact analysis.
 */
static void take_snapshot(const Board *b, const IdGrid *ids, Snapshot *s) {
    memset(s, 0, sizeof(*s));

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = ids->id[row][col];
            if (id <= 0 || id >= CALC_MAX_ID) {
                continue;
            }

            bool destinations[BOARD_SIZE][BOARD_SIZE];
            Color side = b->board[row][col].color;
            legal_destination_map(b, row, col, side, destinations);

            s->present[id] = true;
            s->row[id] = row;
            s->col[id] = col;

            for (int i = 0; i < TOTAL_SQUARES; ++i) {
                if (destinations[i / BOARD_SIZE][i % BOARD_SIZE]) {
                    s->legal[id][i] = true;
                    ++s->legal_count[id];
                    s->reach[side][i] = true;
                }
            }
        }
    }
}

/*
 * ids_after_move
 * Maps where each named piece ends up after move `m`.
 */
static void ids_after_move(const Board *before, Move m, const IdGrid *ids,
                           IdGrid *after, bool captured[CALC_MAX_ID]) {
    memset(after, 0, sizeof(*after));
    memset(captured, 0, sizeof(bool) * CALC_MAX_ID);

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = ids->id[row][col];
            if (id <= 0 || id >= CALC_MAX_ID) {
                continue;
            }

            int to_row = 0;
            int to_col = 0;
            char type_after = '\0';

            FollowCase outcome = follow_piece(before, m, row, col, &to_row, &to_col, &type_after);
            if (outcome == FOLLOW_CAPTURED) {
                captured[id] = true;
            } else {
                after->id[to_row][to_col] = id;
            }
        }
    }
}

/*
 * zero_move_cause
 * Diagnoses why a piece has 0 legal moves:
 *   "BLOCKED" - Has 0 pseudo-legal moves.
 *   "CHECK"   - Has pseudo-legal moves, but king is in check and cannot escape.
 *   "PIN"     - Has pseudo-legal moves, but piece is pinned to the king.
 */
static const char *zero_move_cause(const Board *b, int row, int col) {
    Board view = *b;
    int pseudo = 0;

    view.turn = b->board[row][col].color;

    for (int er = 0; er < BOARD_SIZE; ++er) {
        for (int ec = 0; ec < BOARD_SIZE; ++ec) {
            Move m = {row, col, er, ec, '\0'};
            if (pseudo_legal(&view, m)) {
                ++pseudo;
            }
        }
    }

    if (pseudo == 0) {
        return "BLOCKED";
    }

    return is_in_check(&view, view.turn) ? "CHECK" : "PIN";
}

/*
 * linked
 * Checks if piece on (pr, pc) protects (if friendly) or attacks (if enemy) piece on (qr, qc).
 * Kings are never listed as protected or attacked.
 */
static bool linked(const Board *b, int pr, int pc, int qr, int qc, bool protect) {
    Piece p = b->board[pr][pc];
    Piece q = b->board[qr][qc];

    if (p.color == EMPTY || q.color == EMPTY || q.type == 'K' || (pr == qr && pc == qc)) {
        return false;
    }

    bool same_color = (p.color == q.color);
    if (same_color != protect) {
        return false;
    }

    return piece_attacks(b, pr, pc, qr, qc);
}

/*
 * report_links
 * Reports protection and attack links that exist in `has` and not in `lacks`.
 */
static void report_links(TextBuffer *out, const Names *names, const char *keyword, Color side, bool protect,
                         const Board *has, const IdGrid *has_id, const Board *lacks, const Snapshot *lacks_snap) {
    for (int pr = 0; pr < BOARD_SIZE; ++pr) {
        for (int pc = 0; pc < BOARD_SIZE; ++pc) {
            int p = has_id->id[pr][pc];
            if (p == 0 || has->board[pr][pc].color != side) {
                continue;
            }

            for (int qr = 0; qr < BOARD_SIZE; ++qr) {
                for (int qc = 0; qc < BOARD_SIZE; ++qc) {
                    int q = has_id->id[qr][qc];
                    if (q == 0 || !linked(has, pr, pc, qr, qc, protect)) {
                        continue;
                    }

                    bool in_other = lacks_snap->present[p] && lacks_snap->present[q] &&
                                    linked(lacks, lacks_snap->row[p], lacks_snap->col[p],
                                           lacks_snap->row[q], lacks_snap->col[q], protect);
                    if (!in_other) {
                        text_add(out, "%s %s %s %s\n", keyword, color_name(side), names->name[p], names->name[q]);
                    }
                }
            }
        }
    }
}

/*
 * move_text
 * Formats a move into standard algebraic text: e2e4 or e7e8q.
 */
static void move_text(Move m, char out[6]) {
    out[0] = (char)('a' + m.sc);
    out[1] = (char)('0' + (8 - m.sr));
    out[2] = (char)('a' + m.ec);
    out[3] = (char)('0' + (8 - m.er));
    out[4] = m.promotion ? (char)tolower((unsigned char)m.promotion) : '\0';
    out[5] = '\0';
}

/*
 * report_mates
 * Reports all immediate checkmate moves (MATE1) available for `side`.
 */
static void report_mates(TextBuffer *out, const Board *b, Color side) {
    Board view = *b;
    MoveList moves;
    bool any = false;

    view.turn = side;
    moves = generate_moves(&view);

    for (size_t i = 0; i < moves.count; ++i) {
        Board next = view;
        make_move(&next, moves.items[i]);
        MoveList replies = generate_moves(&next);
        bool mate = (replies.count == 0 && is_in_check(&next, next.turn));
        free(replies.items);

        if (mate) {
            char text[6];
            move_text(moves.items[i], text);
            if (!any) {
                text_add(out, "MATE1 %s", color_name(side));
                any = true;
            }
            text_add(out, " %s", text);
        }
    }
    free(moves.items);

    if (any) {
        text_add(out, "\n");
    }
}

/*
 * report_header
 * Prints header lines of CALC report: MOVED, CASTLE, CAPTURED, PROMOTED.
 */
static void report_header(TextBuffer *out, const Board *b, const Tracker *t, Move m,
                          const bool captured[CALC_MAX_ID]) {
    Piece mover = b->board[m.sr][m.sc];
    char text[6], from[3], to[3];

    move_text(m, text);
    text_add(out, "CALC BEGIN %s\n", text);
    square_text(square_index(m.sr, m.sc), from);
    square_text(square_index(m.er, m.ec), to);
    text_add(out, "MOVED %s %c %s %s\n", color_name(mover.color), mover.type, from, to);

    /* Castling notification */
    if (mover.type == 'K' && abs(m.ec - m.sc) == 2) {
        char rook_from[3], rook_to[3];
        square_text(square_index(m.sr, m.ec > m.sc ? 7 : 0), rook_from);
        square_text(square_index(m.sr, m.ec > m.sc ? 5 : 3), rook_to);
        text_add(out, "CASTLE %s %s %s\n", color_name(mover.color), rook_from, rook_to);
    }

    /* Captured pieces */
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = t->grid.id[row][col];
            if (id != 0 && captured[id]) {
                char square[3];
                square_text(square_index(row, col), square);
                text_add(out, "CAPTURED %s %c %s\n",
                         color_name(t->color[id]), b->board[row][col].type, square);
            }
        }
    }

    /* Pawn promotion */
    if (mover.type == 'P' && (m.er == 0 || m.er == 7)) {
        text_add(out, "PROMOTED %s %s %s %c\n", color_name(mover.color), from, to,
                 m.promotion ? m.promotion : 'Q');
    }
}

/*
 * report_zero
 * Reports pieces with zero legal moves (before, after, or both).
 */
static void report_zero(TextBuffer *out, const Board *b, const Board *a, const Tracker *t,
                        const Snapshot *s0, const Snapshot *s1, Color side) {
    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = t->grid.id[row][col];
            if (id == 0 || t->color[id] != side || !s1->present[id]) {
                continue;
            }

            bool before = (s0->legal_count[id] == 0);
            bool after  = (s1->legal_count[id] == 0);

            if (!before && !after) {
                continue;
            }

            char name[8];
            char square[3];
            square_text(square_index(row, col), square);
            snprintf(name, sizeof(name), "%c %s", b->board[row][col].type, square);

            const char *cause;
            if (after) {
                cause = zero_move_cause(a, s1->row[id], s1->col[id]);
            } else {
                cause = zero_move_cause(b, row, col);
            }

            const char *when;
            if (before && after) {
                when = "both";
            } else if (after) {
                when = "after";
            } else {
                when = "before";
            }

            text_add(out, "ZERO %s %s %s %s\n", color_name(side), name, cause, when);
        }
    }
}

/*
 * report_pairs
 * Reports destination changes for pieces: LOST, GAINED, or RESTORED.
 */
static void report_pairs(TextBuffer *out, const Tracker *t, const Names *names, const Snapshot *s0,
                         const Snapshot *s1, Color side, const char *keyword, int *count) {
    *count = 0;

    for (int row = 0; row < BOARD_SIZE; ++row) {
        for (int col = 0; col < BOARD_SIZE; ++col) {
            int id = t->grid.id[row][col];
            if (id == 0 || t->color[id] != side || !s1->present[id]) {
                continue;
            }

            bool any = false;
            for (int i = 0; i < TOTAL_SQUARES; ++i) {
                bool lost_square = (s0->legal[id][i] && !s1->legal[id][i]);
                bool new_square  = (!s0->legal[id][i] && s1->legal[id][i]);

                bool wanted = false;
                if (keyword[0] == 'L' && lost_square) {
                    wanted = true;
                } else if (keyword[0] == 'G' && new_square && !t->lost[id][i]) {
                    wanted = true;
                } else if (keyword[0] == 'R' && new_square && t->lost[id][i]) {
                    wanted = true;
                }

                if (!wanted) {
                    continue;
                }

                char square[3];
                square_text(i, square);
                if (!any) {
                    text_add(out, "%s %s %s", keyword, color_name(side), names->name[id]);
                    any = true;
                }
                text_add(out, " %s", square);
                ++*count;
            }

            if (any) {
                text_add(out, "\n");
            }
        }
    }
}

/*
 * report_team_squares
 * Reports squares that became DENIED or OPENED for a team's total reach.
 */
static int report_team_squares(TextBuffer *out, const Board *b, const Tracker *t, const Snapshot *s0,
                               const Snapshot *s1, const bool captured[CALC_MAX_ID], Color side, bool denied) {
    int count = 0;

    for (int i = 0; i < TOTAL_SQUARES; ++i) {
        bool change = false;
        if (denied) {
            change = (s0->reach[side][i] && !s1->reach[side][i]);
        } else {
            change = (!s0->reach[side][i] && s1->reach[side][i]);
        }

        if (!change) {
            continue;
        }

        bool only_captured = denied;
        for (int row = 0; row < BOARD_SIZE && only_captured; ++row) {
            for (int col = 0; col < BOARD_SIZE; ++col) {
                int id = t->grid.id[row][col];
                if (id != 0 && b->board[row][col].color == side && s0->legal[id][i] && !captured[id]) {
                    only_captured = false;
                    break;
                }
            }
        }

        char square[3];
        square_text(i, square);
        text_add(out, "%s %s %s%s\n", denied ? "DENIED" : "OPENED", color_name(side), square,
                 only_captured ? " by-capture" : "");
        ++count;
    }
    return count;
}

/*
 * count_zero_after
 * Counts pieces of `side` with 0 legal moves in snapshot s1.
 */
static int count_zero_after(const Tracker *t, const Snapshot *s1, Color side) {
    int zero = 0;
    for (int id = 1; id < CALC_MAX_ID; ++id) {
        if (s1->present[id] && t->color[id] == side && s1->legal_count[id] == 0) {
            ++zero;
        }
    }
    return zero;
}

/*
 * calc_report
 * Generates the complete Stage 3A Calculator report for move `m`.
 */
static void calc_report(const Board *b, const Tracker *t, Move m, TextBuffer *out) {
    Board after = *b;
    IdGrid after_id;
    bool captured[CALC_MAX_ID];
    Snapshot s0, s1;
    int lost[3], gained[3], restored[3], denied[3], opened[3];
    static const Color sides[2] = {WHITE, BLACK};
    Names names;

    make_names(b, t, &names);
    make_move(&after, m);
    ids_after_move(b, m, &t->grid, &after_id, captured);
    take_snapshot(b, &t->grid, &s0);
    take_snapshot(&after, &after_id, &s1);

    report_header(out, b, t, m, captured);

    for (int i = 0; i < 2; ++i) {
        report_zero(out, b, &after, t, &s0, &s1, sides[i]);
    }
    for (int i = 0; i < 2; ++i) {
        report_pairs(out, t, &names, &s0, &s1, sides[i], "LOST", &lost[sides[i]]);
    }
    for (int i = 0; i < 2; ++i) {
        report_pairs(out, t, &names, &s0, &s1, sides[i], "GAINED", &gained[sides[i]]);
    }
    for (int i = 0; i < 2; ++i) {
        report_pairs(out, t, &names, &s0, &s1, sides[i], "RESTORED", &restored[sides[i]]);
    }
    for (int i = 0; i < 2; ++i) {
        denied[sides[i]] = report_team_squares(out, b, t, &s0, &s1, captured, sides[i], true);
    }
    for (int i = 0; i < 2; ++i) {
        opened[sides[i]] = report_team_squares(out, b, t, &s0, &s1, captured, sides[i], false);
    }
    for (int i = 0; i < 2; ++i) {
        report_links(out, &names, "PROTECT+", sides[i], true, &after, &after_id, b, &s0);
    }
    for (int i = 0; i < 2; ++i) {
        report_links(out, &names, "PROTECT-", sides[i], true, b, &t->grid, &after, &s1);
    }
    for (int i = 0; i < 2; ++i) {
        report_links(out, &names, "ATTACK+", sides[i], false, &after, &after_id, b, &s0);
    }
    for (int i = 0; i < 2; ++i) {
        report_links(out, &names, "ATTACK-", sides[i], false, b, &t->grid, &after, &s1);
    }
    for (int i = 0; i < 2; ++i) {
        if (is_in_check(&after, sides[i])) {
            text_add(out, "CHECK %s\n", color_name(sides[i]));
        }
    }

    /* Version 9: If move ended game, omit MATE1 lines */
    MoveList answers = generate_moves(&after);
    bool is_game_over = (answers.count == 0);
    free(answers.items);

    for (int i = 0; !is_game_over && i < 2; ++i) {
        report_mates(out, &after, sides[i]);
    }

    for (int i = 0; i < 2; ++i) {
        Color s = sides[i];
        text_add(out, "COUNT %s U1 %d U2 %d U3 %d GAINED %d RESTORED %d OPENED %d\n", color_name(s),
                 count_zero_after(t, &s1, s), lost[s], denied[s], gained[s], restored[s], opened[s]);
    }
    text_add(out, "CALC END\n");
}

/*
 * tracker_commit
 * Commits move `m` into tracker, updating lost destinations for subsequent moves.
 */
static void tracker_commit(Tracker *t, const Board *b, Move m) {
    Board after = *b;
    IdGrid after_id;
    bool captured[CALC_MAX_ID];
    Snapshot s0, s1;

    make_move(&after, m);
    ids_after_move(b, m, &t->grid, &after_id, captured);
    take_snapshot(b, &t->grid, &s0);
    take_snapshot(&after, &after_id, &s1);

    for (int id = 1; id < CALC_MAX_ID; ++id) {
        if (captured[id]) {
            memset(t->lost[id], 0, sizeof(t->lost[id]));
            continue;
        }
        if (!s1.present[id]) {
            continue;
        }
        for (int i = 0; i < TOTAL_SQUARES; ++i) {
            if (s0.legal[id][i] && !s1.legal[id][i]) {
                t->lost[id][i] = true;
            } else if (!s0.legal[id][i] && s1.legal[id][i]) {
                t->lost[id][i] = false;
            }
        }
    }
    t->grid = after_id;
}

/* ============================================================================
 * SECTION 16: STAGE 3B - OPPONENT REPLY ANALYSIS
 * ============================================================================
 */

/*
 * calc_counts
 * Computes the COUNT line metrics for move `m`.
 */
static void calc_counts(const Board *b, const Tracker *t, Move m, SideCounts counts[3]) {
    Board after = *b;
    IdGrid after_id;
    bool captured[CALC_MAX_ID];
    Snapshot s0, s1;

    make_move(&after, m);
    ids_after_move(b, m, &t->grid, &after_id, captured);
    take_snapshot(b, &t->grid, &s0);
    take_snapshot(&after, &after_id, &s1);

    memset(counts, 0, sizeof(SideCounts) * 3);

    for (int id = 1; id < CALC_MAX_ID; ++id) {
        if (!s1.present[id]) {
            continue;
        }
        SideCounts *c = &counts[t->color[id]];
        if (s1.legal_count[id] == 0) {
            ++c->zero_after;
        }
        for (int i = 0; i < TOTAL_SQUARES; ++i) {
            if (s0.legal[id][i] && !s1.legal[id][i]) {
                ++c->lost;
            } else if (!s0.legal[id][i] && s1.legal[id][i]) {
                if (t->lost[id][i]) {
                    ++c->restored;
                } else {
                    ++c->gained;
                }
            }
        }
    }

    for (int side = WHITE; side <= BLACK; ++side) {
        for (int i = 0; i < TOTAL_SQUARES; ++i) {
            if (s0.reach[side][i] && !s1.reach[side][i]) {
                ++counts[side].denied;
            } else if (!s0.reach[side][i] && s1.reach[side][i]) {
                ++counts[side].opened;
            }
        }
    }
}

/*
 * count_mate_in_one
 * Counts how many moves give immediate checkmate for `side`.
 */
static int count_mate_in_one(const Board *b, Color side) {
    Board view = *b;
    MoveList moves;
    int mates = 0;

    view.turn = side;
    moves = generate_moves(&view);

    for (size_t i = 0; i < moves.count; ++i) {
        Board next = view;
        make_move(&next, moves.items[i]);
        MoveList replies = generate_moves(&next);
        if (replies.count == 0 && is_in_check(&next, next.turn)) {
            ++mates;
        }
        free(replies.items);
    }
    free(moves.items);
    return mates;
}

/*
 * counts_text
 * Formats SideCounts into text string for REPLIES lines.
 */
static void counts_text(TextBuffer *out, const SideCounts counts[3]) {
    for (int side = WHITE; side <= BLACK; ++side) {
        const SideCounts *c = &counts[side];
        text_add(out, " %s U1 %d U2 %d U3 %d GAINED %d RESTORED %d OPENED %d", color_name((Color)side),
                 c->zero_after, c->lost, c->denied, c->gained, c->restored, c->opened);
    }
}

/*
 * position_after
 * Helper to produce board and tracker state after playing move `m`.
 */
static void position_after(const Board *b, const Tracker *t, Move m, Board *after, Tracker *after_tracker) {
    *after = *b;
    *after_tracker = *t;
    tracker_commit(after_tracker, b, m);
    make_move(after, m);
}

/*
 * replies_report
 * Generates Stage 3B replies report for move `m`.
 */
static void replies_report(const Board *b, const Tracker *t, Move m, TextBuffer *out) {
    Board after;
    Tracker tracker_after;
    char text[6];
    int stops = 0, leaves = 0, no_threat = 0, allows = 0;

    position_after(b, t, m, &after, &tracker_after);
    Color mover = b->board[m.sr][m.sc].color;
    move_text(m, text);
    text_add(out, "REPLIES BEGIN %s\n", text);

    MoveList replies = generate_moves(&after);
    bool threat = false;

    if (replies.count == 0) {
        text_add(out, "NO REPLIES %s\n", is_in_check(&after, after.turn) ? "checkmate" : "stalemate");
    } else {
        TextBuffer threats = {NULL, 0, 0};
        report_mates(&threats, &after, mover);
        threat = (threats.length > 0);
        if (threat) {
            text_add(out, "THREAT%s", threats.text + strlen("MATE1"));
        } else {
            text_add(out, "THREAT %s none\n", color_name(mover));
        }
        free(threats.text);
    }

    if (replies.count > 1) {
        qsort(replies.items, replies.count, sizeof(Move), compare_moves);
    }

    for (size_t i = 0; i < replies.count; ++i) {
        Board after_reply = after;
        SideCounts counts[3];
        make_move(&after_reply, replies.items[i]);
        bool still = (count_mate_in_one(&after_reply, mover) > 0);
        const char *label;

        if (threat && still) {
            label = "LEAVES";
            ++leaves;
        } else if (threat) {
            label = "STOPS";
            ++stops;
        } else if (still) {
            label = "ALLOWS";
            ++allows;
        } else {
            label = "NO-THREAT";
            ++no_threat;
        }

        calc_counts(&after, &tracker_after, replies.items[i], counts);
        move_text(replies.items[i], text);
        text_add(out, "REPLY %s %s", text, label);
        counts_text(out, counts);
        text_add(out, "\n");
    }

    text_add(out, "SUMMARY REPLIES %d STOPS %d LEAVES %d NO-THREAT %d ALLOWS %d\n",
             (int)replies.count, stops, leaves, no_threat, allows);
    text_add(out, "REPLIES END\n");
    free(replies.items);
}

/*
 * reply_detail
 * Generates full CALC report for a single specific reply `r` to move `m`.
 */
static bool reply_detail(const Board *b, const Tracker *t, Move m, Move r, TextBuffer *out) {
    Board after;
    Tracker tracker_after;

    position_after(b, t, m, &after, &tracker_after);
    if (!legal_move(&after, r)) {
        return false;
    }
    calc_report(&after, &tracker_after, r, out);
    return true;
}

/*
 * parse_move_text
 * Parses move text like "e2e4" or "e7e8q" into a Move struct.
 */
static bool parse_move_text(const char *text, Move *m) {
    size_t length = strlen(text);
    int sr, sc, er, ec;

    if ((length != 4 && length != 5) || !parse_square(text, &sr, &sc) || !parse_square(text + 2, &er, &ec)) {
        return false;
    }

    m->sr = sr;
    m->sc = sc;
    m->er = er;
    m->ec = ec;
    m->promotion = '\0';

    if (length == 5) {
        char p = (char)toupper((unsigned char)text[4]);
        if (strchr("QRBN", p) == NULL) {
            return false;
        }
        m->promotion = p;
    }
    return true;
}

/* ============================================================================
 * SECTION 17: STAGE 3C - GAME TREE SEARCH (LOOP AND TRACE)
 * ============================================================================
 */

/*
 * zero_move_pieces
 * Counts pieces belonging to side to move that have 0 legal moves.
 */
static int zero_move_pieces(const Board *b, const MoveList *moves) {
    bool moves_from[TOTAL_SQUARES] = {false};
    int zero = 0;

    for (size_t i = 0; i < moves->count; ++i) {
        moves_from[moves->items[i].sr * BOARD_SIZE + moves->items[i].sc] = true;
    }

    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            if (b->board[r][c].color == b->turn && !moves_from[r * BOARD_SIZE + c]) {
                ++zero;
            }
        }
    }
    return zero;
}

/*
 * loop_walk
 * Recursive depth-first tree traversal exploring all positions up to `depth` plies.
 */
static void loop_walk(LoopState *s, const Board *b, int ply) {
    MoveList moves = sorted_moves(b);
    ++s->positions[ply];

    if (s->zero_k > 0 && zero_move_pieces(b, &moves) >= s->zero_k) {
        ++s->zero[ply];
    }

    if (moves.count == 0) {
        if (is_in_check(b, b->turn)) {
            char text[6];
            ++s->mated[ply][b->turn];
            ++s->first_mated[s->first_index][b->turn];
            if (b->turn != s->mover && ply >= 3) {
                s->reply_reaches_mate = true;
            }
            text_add(s->out, "MATE %d", ply);
            for (int i = 0; i < ply; ++i) {
                move_text(s->line[i], text);
                text_add(s->out, " %s", text);
            }
            text_add(s->out, " MATED %s\n", color_name(b->turn));
        } else {
            ++s->stalemates[ply];
        }
    } else if (ply < s->depth) {
        for (size_t i = 0; i < moves.count; ++i) {
            Board next = *b;
            make_move(&next, moves.items[i]);
            s->line[ply] = moves.items[i];
            if (ply == 1) {
                s->reply_reaches_mate = false;
            }
            loop_walk(s, &next, ply + 1);
            if (ply == 1 && s->reply_reaches_mate) {
                ++s->replies_with_mate[s->first_index];
            }
        }
    }
    free(moves.items);
}

/*
 * mate_forced
 * Minimax search returning true if side to move can force checkmate within `n` plies.
 */
static bool mate_forced(const Board *b, int n) {
    if (n < 1) {
        return false;
    }

    bool forced = false;
    MoveList moves = generate_moves(b);

    for (size_t i = 0; i < moves.count && !forced; ++i) {
        Board next = *b;
        make_move(&next, moves.items[i]);
        MoveList replies = generate_moves(&next);

        if (replies.count == 0) {
            forced = is_in_check(&next, next.turn);
        } else if (n >= 3) {
            bool all = true;
            for (size_t j = 0; j < replies.count && all; ++j) {
                Board after = next;
                make_move(&after, replies.items[j]);
                all = mate_forced(&after, n - 2);
            }
            forced = all;
        }
        free(replies.items);
    }
    free(moves.items);
    return forced;
}

/*
 * first_move_forces
 * Evaluates whether first move (already played into `after`) forces checkmate within `n` plies.
 */
static bool first_move_forces(const Board *after, int n) {
    MoveList replies = generate_moves(after);
    bool forced;

    if (replies.count == 0) {
        forced = is_in_check(after, after->turn);
    } else {
        forced = (n >= 3);
        for (size_t j = 0; j < replies.count && forced; ++j) {
            Board next = *after;
            make_move(&next, replies.items[j]);
            forced = mate_forced(&next, n - 2);
        }
    }
    free(replies.items);
    return forced;
}

/*
 * loop_report
 * Builds Stage 3C tree search report for depth 1..LOOP_MAX_DEPTH.
 */
static void loop_report(const Board *b, int depth, int zero_k, TextBuffer *out) {
    static LoopState s;
    MoveList first = sorted_moves(b);
    bool any_forced = false, any_possible = false;
    char text[6];

    memset(&s, 0, sizeof(s));
    s.depth = depth;
    s.zero_k = zero_k;
    s.mover = b->turn;
    s.out = out;

    text_add(out, "LOOP BEGIN %s DEPTH %d", color_name(b->turn), depth);
    if (zero_k > 0) {
        text_add(out, " ZERO %d", zero_k);
    }
    text_add(out, "\n");

    if (first.count == 0) {
        text_add(out, "NO MOVES %s\n", is_in_check(b, b->turn) ? "checkmate" : "stalemate");
        text_add(out, "LOOP END\n");
        free(first.items);
        return;
    }

    /* 1. Explore all sequences */
    for (size_t i = 0; i < first.count; ++i) {
        Board next = *b;
        make_move(&next, first.items[i]);
        s.first_index = (int)i;
        s.line[0] = first.items[i];
        loop_walk(&s, &next, 1);
    }

    /* 2. Print totals per ply */
    for (int p = 1; p <= depth; ++p) {
        text_add(out, "PLY %d POSITIONS %ld MATED White %ld Black %ld STALEMATES %ld", p, s.positions[p],
                 s.mated[p][WHITE], s.mated[p][BLACK], s.stalemates[p]);
        if (zero_k > 0) {
            text_add(out, " ZERO %ld", s.zero[p]);
        }
        text_add(out, "\n");
    }

    /* 3. Evaluate each candidate first move */
    for (size_t i = 0; i < first.count; ++i) {
        Board next = *b;
        make_move(&next, first.items[i]);
        MoveList replies = generate_moves(&next);
        move_text(first.items[i], text);
        text_add(out, "FIRST %s ", text);

        if (first_move_forces(&next, depth)) {
            text_add(out, "FORCED");
            any_forced = true;
        } else if (s.replies_with_mate[i] > 0) {
            text_add(out, "POSSIBLE %d OF %d", s.replies_with_mate[i], (int)replies.count);
            any_possible = true;
        } else {
            text_add(out, "NOT-FOUND");
        }
        text_add(out, " MATED White %ld Black %ld\n", s.first_mated[i][WHITE], s.first_mated[i][BLACK]);
        free(replies.items);
    }

    text_add(out, "RESULT %s %s\n", color_name(b->turn),
             any_forced ? "FORCED" : any_possible ? "POSSIBLE" : "NOT-FOUND");
    if (!any_forced) {
        text_add(out, "LIMIT %d\n", depth);
    }
    text_add(out, "LOOP END\n");
    free(first.items);
}

/*
 * parse_loop_args
 * Parses arguments for "loop N" or "loop N K".
 */
static bool parse_loop_args(const char *text, int *depth, int *zero_k) {
    if (text == NULL || depth == NULL || zero_k == NULL) {
        return false;
    }
    int n = 0, k = 0, used = 0;

    if (sscanf(text, "%d%n", &n, &used) != 1) {
        return false;
    }
    text += used;

    while (*text == ' ') {
        ++text;
    }
    if (*text != '\0') {
        if (sscanf(text, "%d%n", &k, &used) != 1 || text[used] != '\0' || k < 1 || k > 16) {
            return false;
        }
    }

    if (n < 1 || n > LOOP_MAX_DEPTH) {
        return false;
    }
    *depth = n;
    *zero_k = k;
    return true;
}

/*
 * trace_report
 * Replays a move sequence "trace e2e4 e7e5 ...", printing CALC reports for each move.
 */
static bool trace_report(const Board *b, const Tracker *t, const char *moves_text, TextBuffer *out, int *bad_ply) {
    if (moves_text == NULL) {
        return false;
    }
    static Tracker tracker;
    Board board = *b;
    Move moves[LOOP_MAX_FIRST];
    int count = 0;
    char word[16];
    const char *p = moves_text;

    *bad_ply = 0;
    tracker = *t;

    while (*p != '\0') {
        int length = 0;
        while (*p == ' ') {
            ++p;
        }
        if (*p == '\0') {
            break;
        }
        while (p[length] != '\0' && p[length] != ' ') {
            ++length;
        }
        if (count == LOOP_MAX_FIRST || length >= (int)sizeof(word)) {
            *bad_ply = count + 1;
            return false;
        }
        memcpy(word, p, (size_t)length);
        word[length] = '\0';
        p += length;

        if (!parse_move_text(word, &moves[count]) || !legal_move(&board, moves[count])) {
            *bad_ply = count + 1;
            return false;
        }
        make_move(&board, moves[count]);
        ++count;
    }

    if (count == 0) {
        *bad_ply = 1;
        return false;
    }

    board = *b;
    text_add(out, "TRACE BEGIN %d\n", count);
    for (int i = 0; i < count; ++i) {
        char text[6];
        move_text(moves[i], text);
        text_add(out, "TRACE PLY %d %s\n", i + 1, text);
        calc_report(&board, &tracker, moves[i], out);
        tracker_commit(&tracker, &board, moves[i]);
        make_move(&board, moves[i]);
    }
    text_add(out, "TRACE END\n");
    return true;
}
/* ============================================================================
 * SECTION 18: STAGE 3D - GOALS, PASS MODE, ROUTES, SUPPORT, AND SECOND GOAL
 * ============================================================================
 */

/*
 * text_raw
 * Appends raw text of given length to TextBuffer in safe chunks.
 */
static void text_raw(TextBuffer *t, const char *text, size_t length) {
    char piece[256];
    while (length > 0) {
        size_t n = (length < sizeof(piece) - 1) ? length : (sizeof(piece) - 1);
        memcpy(piece, text, n);
        piece[n] = '\0';
        text_add(t, "%s", piece);
        text += n;
        length -= n;
    }
}

/*
 * goal_squares
 * Resolves goal squares into array of 0..63 indices.
 * If g->king is true, targets all valid squares adjacent to the enemy king.
 */
static int goal_squares(const Goal *g, const Board *b, Color side, int squares[GOAL_MAX_SQUARES]) {
    int count = 0;
    if (!g->king) {
        for (int i = 0; i < g->count; ++i) {
            squares[count++] = g->square[i];
        }
        return count;
    }

    int kr, kc;
    Color enemy = (side == WHITE) ? BLACK : WHITE;
    if (!find_king(b, enemy, &kr, &kc)) {
        return 0;
    }

    for (int r = kr - 1; r <= kr + 1; ++r) {
        for (int c = kc - 1; c <= kc + 1; ++c) {
            if (in_bounds(r, c) && (r != kr || c != kc)) {
                squares[count++] = r * BOARD_SIZE + c;
            }
        }
    }
    return count;
}

/*
 * goal_text
 * Formats goal description: "king" or list of squares like "f7 g7".
 */
static void goal_text(const Goal *g, TextBuffer *out) {
    char sq[3];
    if (g->king) {
        text_add(out, "king");
    } else {
        for (int i = 0; i < g->count; ++i) {
            square_text(g->square[i], sq);
            text_add(out, "%s%s", (i > 0) ? " " : "", sq);
        }
    }
}

/*
 * pieces_on_square
 * Counts friendly pieces attacking/defending square sq (excluding any piece on sq itself).
 */
static int pieces_on_square(const Board *b, int sq, Color side) {
    int count = 0;
    int target_row = sq / BOARD_SIZE;
    int target_col = sq % BOARD_SIZE;

    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            int current_sq = r * BOARD_SIZE + c;
            if (current_sq != sq && b->board[r][c].color == side) {
                if (piece_attacks(b, r, c, target_row, target_col)) {
                    ++count;
                }
            }
        }
    }
    return count;
}

/*
 * goal_holds
 * Checks if goal condition holds:
 *   COND_REACH: A piece of `side` stands on square `sq`.
 *   COND_PROTECTED: A piece of `side` stands on `sq` AND another piece of `side` protects it.
 */
static bool goal_holds(const Board *b, Color side, int sq, GoalCondition cond) {
    int r = sq / BOARD_SIZE;
    int c = sq % BOARD_SIZE;

    if (b->board[r][c].color != side) {
        return false;
    }
    if (cond == COND_REACH) {
        return true;
    }
    return pieces_on_square(b, sq, side) > 0;
}

/*
 * pass_moves
 * PASS mode: legal moves for `side` evaluated as if it were its turn.
 */
static MoveList pass_moves(const Board *b, Color side) {
    Board view = *b;
    view.turn = side;
    return sorted_moves(&view);
}

/*
 * pass_play
 * Plays move `m` for `side` in PASS mode (the opponent passes).
 */
static void pass_play(Board *b, Move m, Color side) {
    b->turn = side;
    make_move(b, m);
    b->turn = side;
    b->ep_row = -1;
    b->ep_col = -1;
}

/*
 * piece_distance
 * Shortest number of moves (0..max) for the piece on (r, c) alone to reach square `sq`.
 * Returns -1 if more than max.
 */
static int piece_distance(const Board *b, int r, int c, Color side, int sq, int max) {
    if (r * BOARD_SIZE + c == sq) {
        return 0;
    }
    if (max <= 0) {
        return -1;
    }

    int best = -1;
    MoveList moves = pass_moves(b, side);

    for (size_t i = 0; i < moves.count; ++i) {
        Move m = moves.items[i];
        if (m.sr != r || m.sc != c) {
            continue;
        }
        if (m.er * BOARD_SIZE + m.ec == sq) {
            best = 1;
            break;
        }
    }

    for (size_t i = 0; best != 1 && i < moves.count; ++i) {
        Move m = moves.items[i];
        if (m.sr != r || m.sc != c) {
            continue;
        }
        Board next = *b;
        pass_play(&next, m, side);
        int remaining_max = (best == -1) ? (max - 1) : (best - 2);
        int d = piece_distance(&next, m.er, m.ec, side, sq, remaining_max);
        if (d >= 0 && (best == -1 || d + 1 < best)) {
            best = d + 1;
        }
    }
    free(moves.items);
    return best;
}

/*
 * side_within
 * Returns true if any team pieces can satisfy goal condition on `sq` within `depth` moves.
 */
static bool side_within(const Board *b, Color side, int sq, GoalCondition cond, int depth) {
    if (goal_holds(b, side, sq, cond)) {
        return true;
    }
    if (depth <= 0) {
        return false;
    }

    bool found = false;
    MoveList moves = pass_moves(b, side);

    for (size_t i = 0; i < moves.count && !found; ++i) {
        Board next = *b;
        pass_play(&next, moves.items[i], side);
        found = side_within(&next, side, sq, cond, depth - 1);
    }
    free(moves.items);
    return found;
}

/*
 * side_distance
 * Shortest number of moves (0..max) for any team pieces to satisfy goal on `sq`.
 */
static int side_distance(const Board *b, Color side, int sq, GoalCondition cond, int max) {
    for (int d = 0; d <= max; ++d) {
        if (side_within(b, side, sq, cond, d)) {
            return d;
        }
    }
    return -1;
}

/* Global flag for Stage 3E: "risk on" adds AT-RISK to ROUTE lines */
static bool goal_show_risk = false;

/* Forward declaration of piece_value */
static int piece_value(char type);

/*
 * route_line
 * Formats a ROUTE line and appends it to report buffer.
 */
static void route_line(RouteState *s, const Board *end, const char *kind, int length) {
    char text[6];

    if (s->route_count == GOAL_MAX_ROUTES) {
        ++s->extra;
        return;
    }

    RouteVector *v = &s->routes[s->route_count++];
    Color enemy = (s->side == WHITE) ? BLACK : WHITE;

    v->own = length;
    v->length = length;
    memcpy(v->path, s->path, sizeof(v->path));
    v->protectors = pieces_on_square(end, s->sq, s->side);
    v->attackers  = pieces_on_square(end, s->sq, enemy);
    v->line_start = s->out->length;

    text_add(s->out, "ROUTE %s", kind);
    for (int i = 0; i < length; ++i) {
        move_text(s->path[i], text);
        text_add(s->out, " %s", text);
    }
    text_add(s->out, " OWN %d PROTECTORS %d ATTACKERS %d", v->own, v->protectors, v->attackers);

    if (goal_show_risk) {
        int r = s->sq / BOARD_SIZE;
        int c = s->sq % BOARD_SIZE;
        int value = (v->attackers > 0) ? piece_value(end->board[r][c].type) : 0;
        text_add(s->out, " AT-RISK %d", value);
    }

    v->line_end = s->out->length;
    text_add(s->out, "\n");
}

/*
 * piece_routes
 * Finds every route of exactly `length` moves for piece at (r, c) ending on `sq`.
 */
static void piece_routes(RouteState *s, const Board *b, int r, int c, int ply, int length, const char *kind) {
    if (ply == length) {
        if (r * BOARD_SIZE + c == s->sq) {
            route_line(s, b, kind, length);
        }
        return;
    }
    if (r * BOARD_SIZE + c == s->sq) {
        return; /* Arrived earlier */
    }

    MoveList moves = pass_moves(b, s->side);
    for (size_t i = 0; i < moves.count; ++i) {
        Move m = moves.items[i];
        if (m.sr != r || m.sc != c) {
            continue;
        }
        Board next = *b;
        pass_play(&next, m, s->side);
        s->path[ply] = m;
        piece_routes(s, &next, m.er, m.ec, ply + 1, length, kind);
    }
    free(moves.items);
}

/*
 * side_routes
 * Finds every sequence of exactly `length` moves satisfying goal condition on `sq`.
 */
static void side_routes(RouteState *s, const Board *b, int ply, int length, GoalCondition cond, const char *kind) {
    bool holds = goal_holds(b, s->side, s->sq, cond);
    if (ply == length) {
        if (holds) {
            route_line(s, b, kind, length);
        }
        return;
    }
    if (holds) {
        return;
    }

    MoveList moves = pass_moves(b, s->side);
    for (size_t i = 0; i < moves.count; ++i) {
        Board next = *b;
        pass_play(&next, moves.items[i], s->side);
        s->path[ply] = moves.items[i];
        side_routes(s, &next, ply + 1, length, cond, kind);
    }
    free(moves.items);
}

/*
 * mark_dominated
 * Marks routes as DOMINATED when another route to the same square is
 * no worse in all dimensions (fewer/equal moves, more/equal protectors, fewer/equal attackers)
 * and strictly better in at least one.
 */
static void mark_dominated(RouteState *s) {
    if (s->route_count == 0) {
        return;
    }

    TextBuffer marked = {NULL, 0, 0};
    size_t copied = s->routes[0].line_start;
    text_raw(&marked, s->out->text, copied);

    for (int i = 0; i < s->route_count; ++i) {
        RouteVector *a = &s->routes[i];
        bool dominated = false;

        for (int j = 0; j < s->route_count && !dominated; ++j) {
            const RouteVector *b = &s->routes[j];
            bool no_worse = (b->own <= a->own &&
                             b->protectors >= a->protectors &&
                             b->attackers <= a->attackers);
            bool better = (b->own < a->own ||
                           b->protectors > a->protectors ||
                           b->attackers < a->attackers);
            dominated = (no_worse && better);
        }

        size_t next = (i + 1 < s->route_count) ? s->routes[i + 1].line_start : s->out->length;
        text_raw(&marked, s->out->text + a->line_start, a->line_end - a->line_start);
        a->dominated = dominated;
        if (dominated) {
            text_add(&marked, " DOMINATED");
        }
        text_raw(&marked, s->out->text + a->line_end, next - a->line_end);
    }

    free(s->out->text);
    *s->out = marked;
}

/*
 * order_label
 * Returns the owner's order label ("IF", "ELSE IF", "ELSE") for a value in `values`:
 *   - The smallest distinct value is "IF".
 *   - The largest distinct value is "ELSE".
 *   - Any value strictly in between is "ELSE IF".
 *   - If all values are equal (only one distinct value), returns "IF".
 *
 * NOTE FOR BEGINNERS:
 * This rewritten version avoids arbitrary fixed-size arrays and directly tests:
 *   1. Does values contain any valid element strictly smaller than `value`?
 *   2. Does values contain any valid element strictly larger than `value`?
 */
static const char *order_label(const int *values, int count, int value) {
    bool has_smaller = false;
    bool has_larger = false;

    for (int i = 0; i < count; ++i) {
        if (values[i] < 0) {
            continue; /* Skip invalid or negative entries */
        }
        if (values[i] < value) {
            has_smaller = true;
        } else if (values[i] > value) {
            has_larger = true;
        }
    }

    if (!has_smaller) {
        return "IF";
    } else if (!has_larger) {
        return "ELSE";
    } else {
        return "ELSE IF";
    }
}

/* Forward declaration of second_goal_report */
static void second_goal_report(const Board *b, const Goal *second, const int *first_square,
                               const RouteVector *routes, int route_count, TextBuffer *out);

/*
 * routes_report_with
 * Generates the complete Stage 3D routes report for goal `g` (and optional second goal).
 */
static void routes_report_with(const Board *b, const Goal *g, const Goal *second, TextBuffer *out) {
    static RouteState s;
    static RouteVector saved[GOAL_MAX_ROUTES];
    int saved_count = 0;
    int first_reach = -1;
    int squares[GOAL_MAX_SQUARES];

    int count = goal_squares(g, b, b->turn, squares);
    Color side = b->turn;
    Color enemy = (side == WHITE) ? BLACK : WHITE;
    int reach[GOAL_MAX_SQUARES];
    int prot[GOAL_MAX_SQUARES];
    char sq[3];

    text_add(out, "ROUTES BEGIN %s GOAL ", color_name(side));
    goal_text(g, out);
    text_add(out, " LIMIT %d PASS\n", g->limit);
    text_add(out, "NOTE PASS is hypothetical: only %s moves, %s passes; not a real sequence of turns\n",
             color_name(side), color_name(enemy));

    for (int k = 0; k < count; ++k) {
        TextBuffer part = {NULL, 0, 0};
        memset(&s, 0, sizeof(s));
        s.out = &part;
        s.side = side;
        s.sq = squares[k];
        square_text(squares[k], sq);

        text_add(&part, "GOAL %s NOW %s %d %s %d\n", sq,
                 color_name(WHITE), pieces_on_square(b, squares[k], WHITE),
                 color_name(BLACK), pieces_on_square(b, squares[k], BLACK));

        /* PIECE routes */
        int distance[64];
        for (int i = 0; i < 64; ++i) {
            distance[i] = -2;
            if (b->board[i / BOARD_SIZE][i % BOARD_SIZE].color != side) {
                continue;
            }
            distance[i] = piece_distance(b, i / BOARD_SIZE, i % BOARD_SIZE, side, squares[k], g->limit);
        }

        for (int i = 0; i < 64; ++i) {
            char at[3];
            if (distance[i] == -2) {
                continue;
            }
            square_text(i, at);
            if (distance[i] >= 0) {
                text_add(&part, "PIECE %c %s CONDITION IF MOVES %d ORDER %s\n",
                         b->board[i / BOARD_SIZE][i % BOARD_SIZE].type, at,
                         distance[i], order_label(distance, 64, distance[i]));
            } else {
                text_add(&part, "PIECE %c %s CONDITION ELSE ORDER NONE\n",
                         b->board[i / BOARD_SIZE][i % BOARD_SIZE].type, at);
            }
        }

        for (int i = 0; i < 64; ++i) {
            if (distance[i] >= 1) {
                char kind[16], at[3];
                square_text(i, at);
                snprintf(kind, sizeof(kind), "PIECE %c %s",
                         b->board[i / BOARD_SIZE][i % BOARD_SIZE].type, at);
                piece_routes(&s, b, i / BOARD_SIZE, i % BOARD_SIZE, 0, distance[i], kind);
            }
        }

        /* SIDE routes */
        reach[k] = side_distance(b, side, squares[k], COND_REACH, g->limit);
        prot[k]  = side_distance(b, side, squares[k], COND_PROTECTED, g->limit);

        if (reach[k] >= 0) {
            text_add(&part, "SIDE REACH CONDITION IF MOVES %d\n", reach[k]);
        } else {
            text_add(&part, "SIDE REACH CONDITION ELSE\n");
        }

        if (prot[k] >= 0) {
            text_add(&part, "SIDE PROTECTED CONDITION IF MOVES %d\n", prot[k]);
            if (prot[k] >= 1) {
                side_routes(&s, b, 0, prot[k], COND_PROTECTED, "SIDE PROTECTED");
            }
        } else {
            text_add(&part, "SIDE PROTECTED CONDITION ELSE\n");
        }

        if (s.route_count > 0) {
            mark_dominated(&s);
        }

        if (reach[k] >= 0 && first_reach < 0) {
            first_reach = squares[k];
            saved_count = s.route_count;
            memcpy(saved, s.routes, sizeof(RouteVector) * (size_t)s.route_count);
        }

        if (s.extra > 0) {
            text_add(&part, "MORE ROUTES %d not listed\n", s.extra);
        }

        text_raw(out, part.text, part.length);
        free(part.text);
    }

    if (count == 0) {
        text_add(out, "NO SQUARES\n");
    }

    for (int k = 0; k < count; ++k) {
        square_text(squares[k], sq);
        text_add(out, "SQUARE %s REACH CONDITION %s PROTECTED CONDITION %s\n", sq,
                 (reach[k] >= 0) ? "IF" : "ELSE",
                 (prot[k] >= 0) ? "IF" : "ELSE");
    }

    /* FIRST-IF order lines */
    const char *condition_names[2] = {"REACH", "PROTECTED"};
    for (int c = 0; c < 2; ++c) {
        int first_index = -1;
        for (int k = 0; k < count && first_index < 0; ++k) {
            int dist = (c == 0) ? reach[k] : prot[k];
            if (dist >= 0) {
                first_index = k;
            }
        }
        if (first_index >= 0) {
            square_text(squares[first_index], sq);
            text_add(out, "FIRST-IF %s %s\n", condition_names[c], sq);
        } else {
            text_add(out, "FIRST-IF %s none (ELSE)\n", condition_names[c]);
        }
    }

    if (second != NULL && second->active) {
        second_goal_report(b, second, (first_reach >= 0) ? &first_reach : NULL,
                           saved, saved_count, out);
    }

    text_add(out, "ROUTES END\n");
}

/*
 * routes_report
 * Non-static wrapper exported for test suites.
 */
void routes_report(const Board *b, const Goal *g, TextBuffer *out);
void routes_report(const Board *b, const Goal *g, TextBuffer *out) {
    routes_report_with(b, g, NULL, out);
}

/*
 * mark_text
 * Formats PIECE and SIDE condition marks for goal squares.
 */
static void mark_text(const Board *after, const Goal *g, const int *squares, int count,
                      int r, int c, int used, TextBuffer *out) {
    Color side = after->turn;
    char sq[3];
    int left = g->limit - used;
    bool done = false;

    for (int k = 0; k < count && !done && left >= 0; ++k) {
        int d = piece_distance(after, r, c, side, squares[k], left);
        if (d >= 0) {
            square_text(squares[k], sq);
            text_add(out, " PIECE CONDITION IF %s MOVES %d", sq, used + d);
            done = true;
        }
    }
    if (!done) {
        text_add(out, " PIECE CONDITION ELSE");
    }

    done = false;
    for (int k = 0; k < count && !done && left >= 0; ++k) {
        int d = side_distance(after, side, squares[k], COND_REACH, left);
        if (d >= 0) {
            square_text(squares[k], sq);
            text_add(out, " SIDE CONDITION IF %s MOVES %d", sq, used + d);
            done = true;
        }
    }
    if (!done) {
        text_add(out, " SIDE CONDITION ELSE");
    }
    text_add(out, "\n");
}

/*
 * goal_marks_selection
 * Appends goal marks for each destination of selected piece on (r, c).
 */
static void goal_marks_selection(const Board *b, const Goal *g, int r, int c, TextBuffer *out) {
    int squares[GOAL_MAX_SQUARES];
    int count = goal_squares(g, b, b->turn, squares);
    char at[3], text[6];

    square_text(r * BOARD_SIZE + c, at);
    text_add(out, "GOAL MARKS %c %s GOAL ", b->board[r][c].type, at);
    goal_text(g, out);
    text_add(out, " LIMIT %d PASS\n", g->limit);

    MoveList moves = sorted_moves(b);
    for (size_t i = 0; i < moves.count; ++i) {
        Move m = moves.items[i];
        if (m.sr != r || m.sc != c) {
            continue;
        }
        Board after = *b;
        Color side = b->turn;
        pass_play(&after, m, side);
        move_text(m, text);
        text_add(out, "MARK %s", text);
        mark_text(&after, g, squares, count, m.er, m.ec, 1, out);
    }
    free(moves.items);
    text_add(out, "GOAL MARKS END\n");
}

/*
 * goal_marks_after
 * Appends goal marks after previewing move `m`.
 */
static void goal_marks_after(const Board *b, const Goal *g, Move m, TextBuffer *out) {
    int squares[GOAL_MAX_SQUARES];
    Color side = b->turn;
    Board after = *b;
    char text[6], at[3];

    pass_play(&after, m, side);
    int count = goal_squares(g, &after, side, squares);
    move_text(m, text);
    text_add(out, "GOAL MARKS AFTER %s GOAL ", text);
    goal_text(g, out);
    text_add(out, " LIMIT %d PASS\n", g->limit);

    for (int k = 0; k < count; ++k) {
        if (goal_holds(&after, side, squares[k], COND_REACH)) {
            square_text(squares[k], at);
            text_add(out, "REACHED %s 1\n", at);
        }
    }

    MoveList moves = pass_moves(&after, side);
    for (size_t i = 0; i < moves.count; ++i) {
        Move n = moves.items[i];
        Board next = after;
        pass_play(&next, n, side);
        square_text(n.sr * BOARD_SIZE + n.sc, at);
        move_text(n, text);
        text_add(out, "MARK %c %s %s", after.board[n.sr][n.sc].type, at, text);
        mark_text(&next, g, squares, count, n.er, n.ec, 2, out);
    }
    free(moves.items);
    text_add(out, "GOAL MARKS END\n");
}

/*
 * parse_goal
 * Parses "f7 2", "f7 g7 h7 3", or "king 2".
 */
static bool parse_goal(const char *text, Goal *g) {
    if (text == NULL || g == NULL) {
        return false;
    }
    Goal read;
    char word[16];
    int used = 0;

    memset(&read, 0, sizeof(read));
    read.limit = -1;

    while (sscanf(text, "%15s%n", word, &used) == 1) {
        text += used;
        int r, c, n;
        char extra;

        if (read.limit != -1) {
            return false;
        }

        if (!strcmp(word, "king") && read.count == 0 && !read.king) {
            read.king = true;
        } else if (strlen(word) == 2 && parse_square(word, &r, &c) && !read.king) {
            if (read.count == GOAL_MAX_SQUARES) {
                return false;
            }
            int sq = r * BOARD_SIZE + c;
            for (int i = 0; i < read.count; ++i) {
                if (read.square[i] == sq) {
                    return false;
                }
            }
            read.square[read.count++] = sq;
        } else if (sscanf(word, "%d%c", &n, &extra) == 1 && n >= 1 && n <= GOAL_MAX_LIMIT &&
                   (read.count > 0 || read.king)) {
            read.limit = n;
        } else {
            return false;
        }
    }

    if (read.limit == -1) {
        return false;
    }

    read.active = true;
    *g = read;
    return true;
}

/*
 * move_distance
 * Computes Chebyshev distance (King distance) between start and destination squares:
 * max(|delta_row|, |delta_col|).
 */
static int move_distance(Move m) {
    int delta_row = abs(m.er - m.sr);
    int delta_col = abs(m.ec - m.sc);
    if (delta_row > delta_col) {
        return delta_row;
    } else {
        return delta_col;
    }
}

/*
 * distance_lines
 * Prints distance order lines for piece on (r, c).
 */
static void distance_lines(const Board *b, int r, int c, const char *label, TextBuffer *out) {
    Board view = *b;
    int distances[256];
    Move moves[256];
    int count = 0;
    char text[6];

    view.turn = b->board[r][c].color;
    MoveList all = sorted_moves(&view);

    for (size_t i = 0; i < all.count && count < 256; ++i) {
        if (all.items[i].sr == r && all.items[i].sc == c) {
            moves[count] = all.items[i];
            distances[count] = move_distance(all.items[i]);
            ++count;
        }
    }
    free(all.items);

    if (count == 0) {
        text_add(out, "NO-MOVES%s\n", label + 4);
        return;
    }

    for (int d = 1; d <= 7; ++d) {
        for (int i = 0; i < count; ++i) {
            if (distances[i] != d) {
                continue;
            }
            move_text(moves[i], text);
            text_add(out, "%s %s DISTANCE %d ORDER %s", label, text, d, order_label(distances, count, d));
            char type = b->board[r][c].type;
            if (type == 'N') {
                text_add(out, " JUMP");
            } else if (type == 'K' && d == 2) {
                bool king_side = (moves[i].ec > moves[i].sc);
                char rook_from[3], rook_to[3];
                square_text(r * BOARD_SIZE + (king_side ? 7 : 0), rook_from);
                square_text(r * BOARD_SIZE + (king_side ? 5 : 3), rook_to);
                text_add(out, " CASTLE %s%s", rook_from, rook_to);
            }
            text_add(out, "\n");
        }
    }
}

/*
 * distance_selection
 * Prints distance order for selected piece on (r, c).
 */
static void distance_selection(const Board *b, int r, int c, TextBuffer *out) {
    char at[3];
    square_text(r * BOARD_SIZE + c, at);
    text_add(out, "DISTANCE ORDER %c %s\n", b->board[r][c].type, at);
    distance_lines(b, r, c, "MOVE", out);
    text_add(out, "DISTANCE ORDER END\n");
}

/*
 * distance_after
 * Prints distance order for all pieces in AFTER position.
 */
static void distance_after(const Board *b, Move m, TextBuffer *out) {
    Board after = *b;
    char text[6];
    make_move(&after, m);
    move_text(m, text);
    text_add(out, "DISTANCE ORDER AFTER %s\n", text);

    for (int side = WHITE; side <= BLACK; ++side) {
        for (int i = 0; i < TOTAL_SQUARES; ++i) {
            if (after.board[i / BOARD_SIZE][i % BOARD_SIZE].color != (Color)side) {
                continue;
            }
            char at[3], label[24];
            square_text(i, at);
            snprintf(label, sizeof(label), "MOVE %s %c %s",
                     color_name((Color)side), after.board[i / BOARD_SIZE][i % BOARD_SIZE].type, at);
            distance_lines(&after, i / BOARD_SIZE, i % BOARD_SIZE, label, out);
        }
    }
    text_add(out, "DISTANCE ORDER END\n");
}

/*
 * goal_forced_real
 * Real goal search: returns true if `side` can force reaching goal `sq` within `n` plies.
 */
static bool goal_forced_real(const Board *b, Color side, int sq, GoalCondition cond, int n) {
    if (n < 1) {
        return false;
    }

    bool forced = false;
    MoveList moves = generate_moves(b);

    for (size_t i = 0; i < moves.count && !forced; ++i) {
        Board next = *b;
        make_move(&next, moves.items[i]);
        if (goal_holds(&next, side, sq, cond)) {
            forced = true;
            break;
        }
        if (n < 3) {
            continue;
        }

        MoveList replies = generate_moves(&next);
        bool all = (replies.count > 0);
        for (size_t j = 0; j < replies.count && all; ++j) {
            Board after = next;
            make_move(&after, replies.items[j]);
            all = goal_forced_real(&after, side, sq, cond, n - 2);
        }
        free(replies.items);
        forced = all;
    }
    free(moves.items);
    return forced;
}

/*
 * goal_possible_real
 * Real goal search: returns true if reaching goal `sq` is possible in any branch within `n` plies.
 */
static bool goal_possible_real(const Board *b, Color side, int sq, GoalCondition cond, int n) {
    if (n < 1) {
        return false;
    }

    bool possible = false;
    MoveList moves = generate_moves(b);

    for (size_t i = 0; i < moves.count && !possible; ++i) {
        Board next = *b;
        make_move(&next, moves.items[i]);
        if (goal_holds(&next, side, sq, cond)) {
            possible = true;
            break;
        }
        if (n < 3) {
            continue;
        }

        MoveList replies = generate_moves(&next);
        for (size_t j = 0; j < replies.count && !possible; ++j) {
            Board after = next;
            make_move(&after, replies.items[j]);
            possible = goal_possible_real(&after, side, sq, cond, n - 2);
        }
        free(replies.items);
    }
    free(moves.items);
    return possible;
}

static const char *real_text(RealResult r) {
    if (r == REAL_FORCED) {
        return "CONDITION IF FORCED";
    } else if (r == REAL_POSSIBLE) {
        return "CONDITION IF POSSIBLE";
    } else {
        return "CONDITION ELSE";
    }
}

/*
 * real_first_lines
 * Evaluates each candidate first move for real goal reachability.
 */
static RealResult real_first_lines(const Board *b, int sq, GoalCondition cond, int depth, TextBuffer *out) {
    Color side = b->turn;
    RealResult best = REAL_ELSE;
    char text[6];
    MoveList first = sorted_moves(b);

    for (size_t i = 0; i < first.count; ++i) {
        Board next = *b;
        make_move(&next, first.items[i]);
        move_text(first.items[i], text);
        text_add(out, "FIRST %s ", text);

        if (goal_holds(&next, side, sq, cond)) {
            text_add(out, "CONDITION IF FORCED MOVES 1\n");
            best = REAL_FORCED;
            continue;
        }

        MoveList replies = generate_moves(&next);
        bool forced = (depth >= 3 && replies.count > 0);
        int k = 0;

        for (size_t j = 0; j < replies.count && depth >= 3; ++j) {
            Board after = next;
            make_move(&after, replies.items[j]);
            bool can = goal_possible_real(&after, side, sq, cond, depth - 2);
            if (can) {
                ++k;
            }
            if (forced && (!can || !goal_forced_real(&after, side, sq, cond, depth - 2))) {
                forced = false;
            }
        }

        if (forced) {
            text_add(out, "CONDITION IF FORCED\n");
            best = REAL_FORCED;
        } else if (k > 0) {
            text_add(out, "CONDITION IF POSSIBLE %d OF %d\n", k, (int)replies.count);
            if (best == REAL_ELSE) {
                best = REAL_POSSIBLE;
            }
        } else {
            text_add(out, "CONDITION ELSE\n");
        }
        free(replies.items);
    }
    free(first.items);
    return best;
}

/*
 * routes_real_report
 * Generates Stage 3D real goal report ("routes real N").
 */
static void routes_real_report(const Board *b, const Goal *g, int depth, TextBuffer *out) {
    int squares[GOAL_MAX_SQUARES];
    int count = goal_squares(g, b, b->turn, squares);
    Color side = b->turn;
    Color enemy = (side == WHITE) ? BLACK : WHITE;
    RealResult result[GOAL_MAX_SQUARES][2];
    const char *names[2] = {"REACH", "PROTECTED"};
    bool all_forced = true;
    char sq[3];

    text_add(out, "ROUTES BEGIN %s GOAL ", color_name(side));
    goal_text(g, out);
    text_add(out, " DEPTH %d REAL\n", depth);
    text_add(out, "NOTE REAL: %s answers with every legal move; FORCED = reached whatever %s does\n",
             color_name(enemy), color_name(enemy));

    MoveList moves = generate_moves(b);
    bool none = (moves.count == 0);
    free(moves.items);

    if (none) {
        text_add(out, "NO MOVES %s\n", is_in_check(b, side) ? "checkmate" : "stalemate");
        text_add(out, "ROUTES END\n");
        return;
    }

    for (int k = 0; k < count; ++k) {
        square_text(squares[k], sq);
        for (int c = 0; c < 2; ++c) {
            text_add(out, "GOAL %s %s\n", sq, names[c]);
            result[k][c] = real_first_lines(b, squares[k], (c == 0) ? COND_REACH : COND_PROTECTED, depth, out);
            text_add(out, "RESULT %s %s %s\n", sq, names[c], real_text(result[k][c]));
            if (result[k][c] != REAL_FORCED) {
                all_forced = false;
            }
        }
    }

    if (count == 0) {
        text_add(out, "NO SQUARES\n");
    }

    for (int k = 0; k < count; ++k) {
        square_text(squares[k], sq);
        text_add(out, "SQUARE %s REACH %s PROTECTED %s\n", sq,
                 real_text(result[k][0]), real_text(result[k][1]));
    }

    for (int c = 0; c < 2; ++c) {
        int first_idx = -1;
        for (int k = 0; k < count && first_idx < 0; ++k) {
            if (result[k][c] != REAL_ELSE) {
                first_idx = k;
            }
        }
        if (first_idx >= 0) {
            square_text(squares[first_idx], sq);
            text_add(out, "FIRST-IF %s %s %s\n", names[c], sq,
                     (result[first_idx][c] == REAL_FORCED) ? "FORCED" : "POSSIBLE");
        } else {
            text_add(out, "FIRST-IF %s none (ELSE)\n", names[c]);
        }
    }

    if (!all_forced || count == 0) {
        text_add(out, "LIMIT %d\n", depth);
    }
    text_add(out, "ROUTES END\n");
}

/*
 * parse_routes_real
 * Parses "real N" after "routes ".
 */
static bool parse_routes_real(const char *text, int *depth) {
    if (text == NULL || depth == NULL) {
        return false;
    }
    int n = 0, used = 0;
    if (strncmp(text, "real ", 5) != 0 || sscanf(text + 5, "%d%n", &n, &used) != 1 ||
        text[5 + used] != '\0' || n < 1 || n > LOOP_MAX_DEPTH) {
        return false;
    }
    *depth = n;
    return true;
}

/*
 * support_report
 * Generates Stage 3D SUPPORT report after previewing move `m`.
 */
static void support_report(const Board *b, Move m, TextBuffer *out) {
    Color side = b->turn;
    Board after = *b;
    char text[6], at[3], from[3];
    int follows = 0;

    pass_play(&after, m, side);
    int sq = m.er * BOARD_SIZE + m.ec;
    char type = after.board[m.er][m.ec].type;

    square_text(sq, at);
    move_text(m, text);
    text_add(out, "SUPPORT BEGIN %s PASS\n", text);
    text_add(out, "NOTE PASS is hypothetical: %s moves again, %s passes\n",
             color_name(side), color_name((side == WHITE) ? BLACK : WHITE));
    text_add(out, "SUPPORT NOW %c %s PROTECTORS %d\n", type, at, pieces_on_square(&after, sq, side));

    MoveList moves = pass_moves(&after, side);
    for (size_t i = 0; i < moves.count; ++i) {
        Move f = moves.items[i];
        if (f.sr == m.er && f.sc == m.ec) {
            continue; /* Must be another piece */
        }
        Board next = after;
        pass_play(&next, f, side);
        if (next.board[m.er][m.ec].color != side) {
            continue;
        }

        bool before = piece_attacks(&after, f.sr, f.sc, m.er, m.ec);
        bool now    = piece_attacks(&next, f.er, f.ec, m.er, m.ec);

        if (now && !before) {
            move_text(f, text);
            square_text(f.sr * BOARD_SIZE + f.sc, from);
            text_add(out, "FOLLOW %s %c %s PROTECTS %c %s PROTECTORS %d\n",
                     text, after.board[f.sr][f.sc].type, from, type,
                     at, pieces_on_square(&next, sq, side));
            ++follows;
        }
    }
    free(moves.items);
    text_add(out, "SUMMARY FOLLOWS %d\n", follows);
    text_add(out, "SUPPORT END\n");
}

/*
 * second_from
 * Evaluates second goal from a specific starting position.
 */
static void second_from(const Board *from, const Goal *second, const char *label, TextBuffer *out) {
    int squares[GOAL_MAX_SQUARES];
    int count = goal_squares(second, from, from->turn, squares);
    char sq[3];

    for (int k = 0; k < count; ++k) {
        int reach = side_distance(from, from->turn, squares[k], COND_REACH, second->limit);
        int prot  = side_distance(from, from->turn, squares[k], COND_PROTECTED, second->limit);
        square_text(squares[k], sq);

        text_add(out, "FROM %s SQUARE %s REACH ", label, sq);
        if (reach >= 0) {
            text_add(out, "CONDITION IF MOVES %d", reach);
        } else {
            text_add(out, "CONDITION ELSE");
        }

        text_add(out, " PROTECTED ");
        if (prot >= 0) {
            text_add(out, "CONDITION IF MOVES %d\n", prot);
        } else {
            text_add(out, "CONDITION ELSE\n");
        }
    }
}

/*
 * second_goal_report
 * Generates report evaluating a second goal.
 */
static void second_goal_report(const Board *b, const Goal *second, const int *first_square,
                               const RouteVector *routes, int route_count, TextBuffer *out) {
    char sq[3], text[6];

    text_add(out, "SECOND GOAL ");
    goal_text(second, out);
    text_add(out, " LIMIT %d PASS AFTER ", second->limit);

    if (first_square != NULL) {
        square_text(*first_square, sq);
        text_add(out, "%s\n", sq);
    } else {
        text_add(out, "none (ELSE)\n");
    }

    second_from(b, second, "START", out);

    for (int i = 0; first_square != NULL && i < route_count; ++i) {
        bool repeated = false;
        for (int j = 0; j < i && !repeated; ++j) {
            repeated = (!routes[j].dominated && routes[j].length == routes[i].length);
            for (int p = 0; repeated && p < routes[i].length; ++p) {
                const Move *x = &routes[j].path[p];
                const Move *y = &routes[i].path[p];
                repeated = (x->sr == y->sr && x->sc == y->sc &&
                            x->er == y->er && x->ec == y->ec &&
                            x->promotion == y->promotion);
            }
        }
        if (routes[i].dominated || repeated) {
            continue;
        }

        Board end = *b;
        TextBuffer label = {NULL, 0, 0};
        for (int p = 0; p < routes[i].length; ++p) {
            pass_play(&end, routes[i].path[p], b->turn);
            move_text(routes[i].path[p], text);
            text_add(&label, "%s%s", (p > 0) ? " " : "", text);
        }
        second_from(&end, second, label.text, out);
        free(label.text);
    }
    text_add(out, "SECOND END\n");
}

/* ============================================================================
 * SECTION 19: STAGE 3E - CAPTURE SEQUENCES, PIECE VALUES, AND EXCHANGES
 * ============================================================================
 */

/*
 * piece_value
 * Returns standard conventional chess piece values:
 *   Pawn = 1, Knight = 3, Bishop = 3, Rook = 5, Queen = 9.
 */
static int piece_value(char type) {
    switch (type) {
        case 'P': return 1;
        case 'N': return 3;
        case 'B': return 3;
        case 'R': return 5;
        case 'Q': return 9;
        default:  return 0;
    }
}

/*
 * captured_type
 * Returns the piece type ('P', 'N', etc.) captured by move `m`, or 0 if non-capturing.
 * Accounts for en passant captures.
 */
static char captured_type(const Board *b, Move m) {
    Piece target = b->board[m.er][m.ec];
    if (target.color != EMPTY && target.color != b->board[m.sr][m.sc].color) {
        return target.type;
    }
    if (b->board[m.sr][m.sc].type == 'P' && m.sc != m.ec && target.color == EMPTY) {
        return 'P'; /* En passant capture */
    }
    return 0;
}

/*
 * captures_on
 * Returns all legal captures landing on square `sq` for current player.
 */
static MoveList captures_on(const Board *b, int sq) {
    MoveList all = sorted_moves(b);
    MoveList caps = {NULL, 0, 0};

    for (size_t i = 0; i < all.count; ++i) {
        if (all.items[i].er * BOARD_SIZE + all.items[i].ec == sq && captured_type(b, all.items[i])) {
            append_move(&caps, all.items[i]);
        }
    }
    free(all.items);
    return caps;
}

/*
 * exchange_line
 * Formats one capture sequence in Stage 3E exchange report.
 */
static void exchange_line(ExchangeState *x, int length, bool cut) {
    char text[6];
    int took[3] = {0, 0, 0};

    text_add(x->out, "SEQUENCE");
    for (int i = 0; i < length; ++i) {
        move_text(x->line[i], text);
        text_add(x->out, " %s", text);
    }

    for (int side = WHITE; side <= BLACK; ++side) {
        text_add(x->out, " %s-TOOK", (side == WHITE) ? "WHITE" : "BLACK");
        bool any = false;
        for (int i = 0; i < length; ++i) {
            if (x->by[i] == (Color)side) {
                text_add(x->out, " %c", x->taken[i]);
                took[side] += piece_value(x->taken[i]);
                any = true;
            }
        }
        if (!any) {
            text_add(x->out, " -");
        }
    }

    text_add(x->out, " MATERIAL White %d Black %d%s\n",
             took[WHITE], took[BLACK], cut ? " LIMIT" : "");
    ++x->sequences;
}

/*
 * exchange_walk
 * Explores all sequences of alternating captures on one square up to `limit`.
 */
static void exchange_walk(ExchangeState *x, const Board *b, int length) {
    MoveList caps = captures_on(b, x->sq);
    bool cut = (length == x->limit && caps.count > 0);

    if (length > 0) {
        exchange_line(x, length, cut);
    }
    if (cut) {
        x->cut = true;
    }

    for (size_t i = 0; length < x->limit && i < caps.count; ++i) {
        Board next = *b;
        x->line[length] = caps.items[i];
        x->taken[length] = captured_type(b, caps.items[i]);
        x->by[length] = b->turn;
        make_move(&next, caps.items[i]);
        exchange_walk(x, &next, length + 1);
    }
    free(caps.items);
}

/*
 * exchange_value
 * Minimax evaluation of material exchange on square `sq`.
 */
static void exchange_value(const Board *b, Color mover, int sq, int m, int left,
                           bool *forced, bool *possible, bool *bounded) {
    MoveList caps = (left > 0) ? captures_on(b, sq) : (MoveList){NULL, 0, 0};

    if (left == 0) {
        MoveList more = captures_on(b, sq);
        if (more.count > 0) {
            *bounded = true;
        }
        free(more.items);
    }

    bool stop_ok = (m >= 0);
    bool any_forced = false;
    bool all_forced = true;
    bool any_possible = stop_ok;

    for (size_t i = 0; i < caps.count; ++i) {
        Board next = *b;
        int v = piece_value(captured_type(b, caps.items[i]));
        int child = (b->turn == mover) ? (m + v) : (m - v);
        bool f = false, p = false;

        make_move(&next, caps.items[i]);
        exchange_value(&next, mover, sq, child, left - 1, &f, &p, bounded);

        any_forced = any_forced || f;
        all_forced = all_forced && f;
        any_possible = any_possible || p;
    }

    if (b->turn == mover) {
        *forced = stop_ok || any_forced;
    } else {
        *forced = stop_ok && all_forced;
    }
    *possible = any_possible;
    free(caps.items);
}

static const char *material_text(MaterialResult r) {
    if (r == MATERIAL_FORCED) {
        return "MATERIAL FORCED NONNEGATIVE";
    } else if (r == MATERIAL_POSSIBLE) {
        return "MATERIAL POSSIBLE NONNEGATIVE";
    } else {
        return "MATERIAL ELSE";
    }
}

/*
 * first_capture_class
 * Classifies the material outcome of a first capture.
 */
static MaterialResult first_capture_class(const Board *b, Move c, int limit, bool *bounded) {
    Board next = *b;
    bool forced = false, possible = false;
    int v = piece_value(captured_type(b, c));

    make_move(&next, c);
    *bounded = false;
    exchange_value(&next, b->turn, c.er * BOARD_SIZE + c.ec, v, limit - 1, &forced, &possible, bounded);

    if (forced) {
        return MATERIAL_FORCED;
    } else if (possible) {
        return MATERIAL_POSSIBLE;
    } else {
        return MATERIAL_ELSE;
    }
}

/*
 * exchange_report
 * Generates Stage 3E exchange report for square `sq` with capture limit `limit`.
 */
static void exchange_report(const Board *b, int sq, int limit, TextBuffer *out) {
    static ExchangeState x;
    char at[3], text[6];

    memset(&x, 0, sizeof(x));
    x.mover = b->turn;
    x.sq = sq;
    x.limit = limit;
    x.out = out;

    square_text(sq, at);
    text_add(out, "EXCHANGE BEGIN %s %s LIMIT %d\n", color_name(b->turn), at, limit);
    text_add(out, "NOTE values P 1, N 3, B 3, R 5, Q 9 are logged only, not a score; a nonnegative material result is not proof that a move is good\n");

    MoveList first = captures_on(b, sq);
    if (first.count == 0) {
        text_add(out, "NO CAPTURES\n");
        text_add(out, "EXCHANGE END\n");
        free(first.items);
        return;
    }

    exchange_walk(&x, b, 0);

    int values[256];
    size_t count = (first.count < 256) ? first.count : 256;
    for (size_t i = 0; i < count; ++i) {
        values[i] = piece_value(captured_type(b, first.items[i]));
    }

    for (size_t i = 0; i < count; ++i) {
        bool bounded = false;
        MaterialResult r = first_capture_class(b, first.items[i], limit, &bounded);
        move_text(first.items[i], text);
        /* "TAKES" names the piece the first capture takes (Version 14 wording). */
        text_add(out, "FIRST %s TAKES %c VALUE %d %s ORDER %s%s\n", text,
                 captured_type(b, first.items[i]), values[i],
                 material_text(r), order_label(values, (int)count, values[i]),
                 bounded ? " BOUNDED" : "");
    }

    text_add(out, "SUMMARY SEQUENCES %d\n", x.sequences);

    /* The LIMIT line appears only when some capture line was cut short by the
     * limit, exactly as in Version 14 (the golden transcripts depend on it). */
    if (x.cut) {
        text_add(out, "LIMIT %d\n", limit);
    }
    text_add(out, "EXCHANGE END\n");
    free(first.items);
}

/*
 * parse_exchange
 * Parses "exchange <square> N".
 */
static bool parse_exchange(const char *text, int *sq, int *limit) {
    if (text == NULL || sq == NULL || limit == NULL) {
        return false;
    }
    char word[16];
    int n = 0, used = 0, r = 0, c = 0;

    if (sscanf(text, "%15s%n", word, &used) != 1 || strlen(word) != 2 || !parse_square(word, &r, &c)) {
        return false;
    }
    text += used;

    if (sscanf(text, "%d%n", &n, &used) != 1 || text[used] != '\0' || n < 1 || n > EXCHANGE_MAX) {
        return false;
    }

    *sq = r * BOARD_SIZE + c;
    *limit = n;
    return true;
}

/*
 * order_report
 * Generates Stage 3E combined move ordering report (ideas 7 & 8).
 */
static void order_report(const Board *b, int limit, TextBuffer *out) {
    static OrderEntry e[256];
    int count = 0;
    char text[6];

    MoveList all = sorted_moves(b);
    for (size_t i = 0; i < all.count && count < 256; ++i) {
        OrderEntry *o = &e[count++];
        o->move = all.items[i];
        o->taken = captured_type(b, all.items[i]);
        o->value = piece_value(o->taken);
        o->squares = move_distance(all.items[i]);
        o->bounded = false;
        o->material = o->taken ? first_capture_class(b, all.items[i], limit, &o->bounded) : MATERIAL_ELSE;
    }
    free(all.items);

    text_add(out, "ORDER BEGIN %s EXCHANGE LIMIT %d\n", color_name(b->turn), limit);
    text_add(out, "NOTE an order of listed facts (ideas 7 and 8), rebuilt in every position; not a choice of move\n");

    if (count == 0) {
        text_add(out, "NO MOVES %s\n", is_in_check(b, b->turn) ? "checkmate" : "stalemate");
        text_add(out, "ORDER END\n");
        return;
    }

    bool group1 = false;
    for (int i = 0; i < count; ++i) {
        if (e[i].taken && e[i].material != MATERIAL_ELSE) {
            group1 = true;
        }
    }
    text_add(out, "HEADS %s\n", group1 ? "CAPTURE" : "DISTANCE");

    /* Group 1: FORCED, then POSSIBLE */
    for (int cls = MATERIAL_FORCED; cls >= MATERIAL_POSSIBLE; --cls) {
        int values[256], n = 0;
        for (int i = 0; i < count; ++i) {
            if (e[i].taken && (int)e[i].material == cls) {
                values[n++] = 9 - e[i].value;
            }
        }
        for (int v = 9; v >= 1; --v) {
            for (int d = 1; d <= 7; ++d) {
                for (int i = 0; i < count; ++i) {
                    if (!e[i].taken || (int)e[i].material != cls || e[i].value != v || e[i].squares != d) {
                        continue;
                    }
                    move_text(e[i].move, text);
                    text_add(out, "GROUP 1 CAPTURE %s TAKES %c VALUE %d SQUARES %d %s ORDER %s%s\n",
                             text, e[i].taken, e[i].value, e[i].squares,
                             material_text(e[i].material), order_label(values, n, 9 - v),
                             e[i].bounded ? " BOUNDED" : "");
                }
            }
        }
    }

    /* Group 2: Everything else by distance travelled */
    int distances[256], n = 0;
    for (int i = 0; i < count; ++i) {
        if (!(e[i].taken && e[i].material != MATERIAL_ELSE)) {
            distances[n++] = e[i].squares;
        }
    }

    for (int d = 1; d <= 7; ++d) {
        for (int i = 0; i < count; ++i) {
            if ((e[i].taken && e[i].material != MATERIAL_ELSE) || e[i].squares != d) {
                continue;
            }
            move_text(e[i].move, text);
            text_add(out, "GROUP 2 DISTANCE %s SQUARES %d ORDER %s", text, d, order_label(distances, n, d));
            if (e[i].taken) {
                text_add(out, " TAKES %c VALUE %d %s%s", e[i].taken, e[i].value,
                         material_text(e[i].material), e[i].bounded ? " BOUNDED" : "");
            }
            text_add(out, "\n");
        }
    }
    text_add(out, "ORDER END\n");
}

/* ============================================================================
 * SECTION 20: STAGE 3F - MULTI-MOVE COMPARISON REPORT
 * ============================================================================
 */

/*
 * line_after
 * Finds the line in `text` starting with `prefix` and copies the remainder into `out`.
 */
static bool line_after(const char *text, const char *prefix, char *out, size_t size) {
    if (text == NULL || prefix == NULL || out == NULL || size == 0) {
        return false;
    }
    size_t n = strlen(prefix);
    for (const char *p = text; p != NULL && *p != '\0';) {
        const char *end = strchr(p, '\n');
        size_t len = end ? (size_t)(end - p) : strlen(p);
        if (len >= n && strncmp(p, prefix, n) == 0) {
            size_t rest = len - n;
            if (rest >= size) {
                rest = size - 1;
            }
            memcpy(out, p + n, rest);
            out[rest] = '\0';
            return true;
        }
        p = end ? end + 1 : NULL;
    }
    return false;
}

/*
 * count_lines
 * Counts lines in `text` starting with `prefix`.
 */
static int count_lines(const char *text, const char *prefix) {
    size_t n = strlen(prefix);
    int count = 0;
    for (const char *p = text; p != NULL && *p != '\0';) {
        if (strncmp(p, prefix, n) == 0) {
            ++count;
        }
        const char *end = strchr(p, '\n');
        p = end ? end + 1 : NULL;
    }
    return count;
}

/*
 * chain_level
 * Calculates level index of `value` in sorted distinct chain.
 */
static int chain_level(const int *values, int count, int value, bool up) {
    if (values == NULL || count <= 0) {
        return 0;
    }
    int level = 0;
    bool seen[64] = {false};

    for (int i = 0; i < count; ++i) {
        int v = values[i];
        if (v < 0 || v >= 64 || seen[v]) {
            continue;
        }
        seen[v] = true;
        if (up ? (v < value) : (v > value)) {
            ++level;
        }
    }
    return level;
}

/*
 * level_of
 * Maps condition status string to numeric rank: FORCED = 2, POSSIBLE = 1, other = 0.
 */
static int level_of(const char *status) {
    if (strstr(status, "FORCED") != NULL) {
        return 2;
    }
    if (strstr(status, "POSSIBLE") != NULL) {
        return 1;
    }
    return 0;
}

/*
 * collect
 * Collects all analytical facts for a candidate move from other stages.
 */
static void collect(Candidate *c, const Board *b, const Tracker *t, int depth, const Goal *g,
                    const char *loop_text, const char *real_text_all, const char *order_text,
                    const int *squares, int count_squares, const int *all_values, int n_values,
                    const int *all_distances, int n_distances) {
    TextBuffer r = {NULL, 0, 0};
    TextBuffer rep_view = {NULL, 0, 0};
    char prefix[64], buf[240];

    calc_report(b, t, c->move, &r);
    if (!line_after(r.text, "COUNT White ", c->r_white, sizeof(c->r_white))) {
        strcpy(c->r_white, "-");
    }
    if (!line_after(r.text, "COUNT Black ", c->r_black, sizeof(c->r_black))) {
        strcpy(c->r_black, "-");
    }
    strcpy(c->check, line_after(r.text, "CHECK ", buf, sizeof(buf)) ? buf : "none");
    if (!line_after(r.text, "MATE1 White ", c->mate1_white, sizeof(c->mate1_white))) {
        strcpy(c->mate1_white, "none");
    }
    if (!line_after(r.text, "MATE1 Black ", c->mate1_black, sizeof(c->mate1_black))) {
        strcpy(c->mate1_black, "none");
    }
    c->links[0] = count_lines(r.text, "PROTECT+ ");
    c->links[1] = count_lines(r.text, "PROTECT- ");
    c->links[2] = count_lines(r.text, "ATTACK+ ");
    c->links[3] = count_lines(r.text, "ATTACK- ");
    free(r.text);

    replies_report(b, t, c->move, &rep_view);
    if (line_after(rep_view.text, "NO REPLIES ", buf, sizeof(buf))) {
        snprintf(c->threat, sizeof(c->threat), "GAME-OVER %s", buf);
        strcpy(c->replies, "-");
    } else {
        if (!line_after(rep_view.text, "THREAT ", c->threat, sizeof(c->threat))) {
            strcpy(c->threat, "-");
        }
        if (!line_after(rep_view.text, "SUMMARY REPLIES ", c->replies, sizeof(c->replies))) {
            strcpy(c->replies, "-");
        }
    }
    free(rep_view.text);

    snprintf(prefix, sizeof(prefix), "FIRST %s ", c->text);
    c->loop_level = -1;
    strcpy(c->loop_status, "-");
    strcpy(c->loop_mated, "-");

    if (line_after(loop_text, prefix, buf, sizeof(buf))) {
        char *mated = strstr(buf, " MATED ");
        if (mated != NULL) {
            snprintf(c->loop_mated, sizeof(c->loop_mated), "%s", mated + 1);
            *mated = '\0';
        }
        snprintf(c->loop_status, sizeof(c->loop_status), "%s", buf);
        c->loop_level = level_of(buf);
    }

    for (int k = 0; k < count_squares; ++k) {
        for (int cond = 0; cond < 2; ++cond) {
            char head[32], sq[3];
            square_text(squares[k], sq);
            snprintf(head, sizeof(head), "GOAL %s %s\n", sq, (cond == 0) ? "REACH" : "PROTECTED");
            strcpy(c->goal_text[k][cond], "-");
            c->goal_level[k][cond] = -1;

            const char *part = real_text_all ? strstr(real_text_all, head) : NULL;
            const char *stop = part ? strstr(part, "RESULT ") : NULL;
            if (part != NULL && stop != NULL) {
                const char *found = strstr(part, prefix);
                if (found != NULL && found < stop) {
                    const char *end = strchr(found, '\n');
                    if (end == NULL || end > stop) {
                        end = stop;
                    }
                    if (end > found + strlen(prefix)) {
                        size_t len = (size_t)(end - (found + strlen(prefix)));
                        if (len >= sizeof(c->goal_text[k][cond])) {
                            len = sizeof(c->goal_text[k][cond]) - 1;
                        }
                        memcpy(c->goal_text[k][cond], found + strlen(prefix), len);
                        c->goal_text[k][cond][len] = '\0';
                        c->goal_level[k][cond] = level_of(c->goal_text[k][cond]);
                    }
                }
            }
        }
    }
    (void)g;

    c->taken = captured_type(b, c->move);
    c->value = piece_value(c->taken);
    c->squares = move_distance(c->move);
    c->squares_rank = chain_level(all_distances, n_distances, c->squares, true);
    c->squares_label = order_label(all_distances, n_distances, c->squares);

    if (c->taken) {
        int neg[256];
        for (int i = 0; i < n_values; ++i) {
            neg[i] = 9 - all_values[i];
        }
        c->value_rank = chain_level(all_values, n_values, c->value, false);
        c->value_label = order_label(neg, n_values, 9 - c->value);
        c->material = first_capture_class(b, c->move, depth, &c->bounded);
        c->material_known = true;
    } else {
        c->value_rank = -1;
        c->value_label = "none";
        c->material_known = false;
        c->bounded = false;
    }
    square_text(c->move.er * BOARD_SIZE + c->move.ec, c->stop);

    /* GROUP: Line in combined order (ideas 7 & 8) */
    c->group = 0;
    c->group_class = 0;
    c->group_label = "-";

    for (const char *p = order_text; p != NULL && *p != '\0';) {
        char word[8];
        int grp = 0;
        if (sscanf(p, "GROUP %d %*s %5s", &grp, word) == 2 && strcmp(word, c->text) == 0) {
            const char *end = strchr(p, '\n');
            size_t len = end ? (size_t)(end - p) : strlen(p);
            char line[200];
            if (len >= sizeof(line)) {
                len = sizeof(line) - 1;
            }
            memcpy(line, p, len);
            line[len] = '\0';
            c->group = grp;
            c->group_class = strstr(line, "MATERIAL FORCED") ? 2 : strstr(line, "MATERIAL POSSIBLE") ? 1 : 0;
            char *ord = strstr(line, " ORDER ");
            c->group_label = (ord == NULL) ? "-" :
                             (strncmp(ord + 7, "ELSE IF", 7) == 0) ? "ELSE IF" :
                             (strncmp(ord + 7, "ELSE", 4) == 0)    ? "ELSE" : "IF";
            break;
        }
        const char *end = strchr(p, '\n');
        p = end ? end + 1 : NULL;
    }
}

static const char *material_word(const Candidate *c) {
    if (!c->material_known) {
        return "-";
    }
    if (c->material == MATERIAL_FORCED) {
        return "FORCED NONNEGATIVE";
    } else if (c->material == MATERIAL_POSSIBLE) {
        return "POSSIBLE NONNEGATIVE";
    } else {
        return "ELSE";
    }
}

static void raw_line(TextBuffer *out, const Candidate *a, const Candidate *b, const char *fact,
                     const char *va, const char *vb) {
    text_add(out, "COMPARE %s %s %s %s | %s %s\n",
             a->text, b->text, fact, va, vb, strcmp(va, vb) == 0 ? "SAME" : "DIFFERENT");
}

static int strength_line(TextBuffer *out, const Candidate *a, const Candidate *b, const char *fact,
                         const char *va, const char *vb, int la, int lb) {
    text_add(out, "COMPARE %s %s %s %s | %s ", a->text, b->text, fact, va, vb);
    if (la < 0 || lb < 0) {
        text_add(out, "NOT-COMPARABLE\n");
        return 2;
    }
    if (la == lb) {
        text_add(out, "TIE\n");
        return 0;
    }
    text_add(out, "STRONGER-CONDITION %s\n", (la > lb) ? a->text : b->text);
    return (la > lb) ? 1 : -1;
}

static int order_line(TextBuffer *out, const Candidate *a, const Candidate *b, const char *fact,
                      const char *va, const char *vb, int ra, int rb) {
    text_add(out, "COMPARE %s %s %s %s | %s ", a->text, b->text, fact, va, vb);
    if (ra < 0 || rb < 0) {
        text_add(out, "NOT-COMPARABLE\n");
        return 2;
    }
    if (ra == rb) {
        text_add(out, "SAME-ORDER-LEVEL\n");
        return 0;
    }
    text_add(out, "EARLIER-IN-ORDER %s\n", (ra < rb) ? a->text : b->text);
    return (ra < rb) ? 1 : -1;
}

/*
 * compare_report
 * Generates Stage 3F comparison report for 2 to 6 candidate moves.
 */
static void compare_report(const Board *b, const Tracker *t, const Goal *g, int depth,
                           const Move *moves, int count, TextBuffer *out) {
    TextBuffer loop_text = {NULL, 0, 0};
    TextBuffer real_all  = {NULL, 0, 0};
    TextBuffer order_text = {NULL, 0, 0};

    Candidate cand[COMPARE_MAX];
    int squares[GOAL_MAX_SQUARES];
    int count_squares = (g != NULL && g->active) ? goal_squares(g, b, b->turn, squares) : 0;
    char va[128], vb[128];

        loop_report(b, depth, 0, &loop_text);
    order_report(b, depth, &order_text);
    if (g != NULL && g->active) {
        routes_real_report(b, g, depth, &real_all);
    }

    MoveList all = sorted_moves(b);
    int all_distances[256], all_values[256];
    int n_distances = (all.count < 256) ? (int)all.count : 256;
    int n_values = 0;

    for (size_t i = 0; i < (size_t)n_distances; ++i) {
        all_distances[i] = move_distance(all.items[i]);
        char tk = captured_type(b, all.items[i]);
        if (tk && n_values < 256) {
            all_values[n_values++] = piece_value(tk);
        }
    }
    free(all.items);

    text_add(out, "COMPARE BEGIN %s DEPTH %d CANDIDATES", color_name(b->turn), depth);
    for (int i = 0; i < count; ++i) {
        memset(&cand[i], 0, sizeof(cand[i]));
        cand[i].move = moves[i];
        move_text(moves[i], cand[i].text);
        text_add(out, " %s", cand[i].text);
    }
    text_add(out, "\n");
    text_add(out, "NOTE measurements only: no weights, no move is chosen or played; STRONGER-CONDITION compares the strength of one stated condition, not the quality of a move\n");
    text_add(out, "NOTE the same side to move, one depth (%d) and one goal for every candidate, so every condition is measured under the same terms\n", depth);
    if (count_squares > 0) {
        text_add(out, "GOAL ");
        goal_text(g, out);
        text_add(out, " REAL DEPTH %d\n", depth);
    }

    for (int i = 0; i < count; ++i) {
        Candidate *c = &cand[i];
        collect(c, b, t, depth, g, loop_text.text, real_all.text, order_text.text,
                squares, count_squares, all_values, n_values, all_distances, n_distances);

        text_add(out, "CANDIDATE %s\n", c->text);
        text_add(out, "FACT R-COUNT White %s\n", c->r_white);
        text_add(out, "FACT R-COUNT Black %s\n", c->r_black);
        text_add(out, "FACT CHECK %s\n", c->check);
        text_add(out, "FACT MATE1 White %s\n", c->mate1_white);
        text_add(out, "FACT MATE1 Black %s\n", c->mate1_black);
        text_add(out, "FACT LINKS PROTECT+ %d PROTECT- %d ATTACK+ %d ATTACK- %d\n", c->links[0], c->links[1], c->links[2], c->links[3]);
        text_add(out, "FACT THREAT %s\n", c->threat);
        text_add(out, "FACT REPLIES %s\n", c->replies);
        text_add(out, "FACT LOOP %s %s LIMIT %d\n", c->loop_status, c->loop_mated, depth);

        for (int k = 0; k < count_squares; ++k) {
            char sq[3];
            square_text(squares[k], sq);
            text_add(out, "FACT GOAL %s REACH %s\n", sq, c->goal_text[k][0]);
            text_add(out, "FACT GOAL %s PROTECTED %s\n", sq, c->goal_text[k][1]);
        }

        if (c->taken) {
            text_add(out, "FACT CAPTURE %c VALUE %d\n", c->taken, c->value);
        } else {
            text_add(out, "FACT CAPTURE none\n");
        }

        text_add(out, "FACT MATERIAL %s%s\n", material_word(c), c->bounded ? " BOUNDED" : "");
        text_add(out, "FACT VALUE-ORDER %s\n", c->value_label);
        text_add(out, "FACT SQUARES-ORDER %d %s\n", c->squares, c->squares_label);
        text_add(out, "FACT GROUP %d %s%s %s\n", c->group,
                 (c->group == 1) ? "CAPTURE" : "DISTANCE",
                 (c->group != 1) ? "" : (c->group_class == 2) ? " FORCED" : " POSSIBLE",
                 c->group_label);

        text_add(out, "VIEW LOOP-1 SQUARES %d ORDER %s STOP %s %s\n",
                 c->squares, c->squares_label, c->stop, c->taken ? "CAPTURE" : "EMPTY");

        if (c->taken) {
            text_add(out, "VIEW LOOP-2 VALUE %d ORDER %s MATERIAL %s%s\n",
                     c->value, c->value_label, material_word(c), c->bounded ? " BOUNDED" : "");
        } else {
            text_add(out, "VIEW LOOP-2 VALUE none ORDER none MATERIAL -\n");
        }
        text_add(out, "NEURON-STATE UNDEFINED\n");
    }

    for (int i = 0; i < count; ++i) {
        for (int j = i + 1; j < count; ++j) {
            const Candidate *a = &cand[i], *c = &cand[j];
            int ahead_a = 0, ahead_b = 0, ties = 0;

            text_add(out, "PAIR %s %s\n", a->text, c->text);
            raw_line(out, a, c, "R-COUNT-White", a->r_white, c->r_white);
            raw_line(out, a, c, "R-COUNT-Black", a->r_black, c->r_black);
            raw_line(out, a, c, "CHECK", a->check, c->check);
            raw_line(out, a, c, "MATE1-White", a->mate1_white, c->mate1_white);
            raw_line(out, a, c, "MATE1-Black", a->mate1_black, c->mate1_black);

            snprintf(va, sizeof(va), "%d %d %d %d", a->links[0], a->links[1], a->links[2], a->links[3]);
            snprintf(vb, sizeof(vb), "%d %d %d %d", c->links[0], c->links[1], c->links[2], c->links[3]);
            raw_line(out, a, c, "LINKS", va, vb);
            raw_line(out, a, c, "THREAT", a->threat, c->threat);
            raw_line(out, a, c, "REPLIES", a->replies, c->replies);
            raw_line(out, a, c, "LOOP-MATED", a->loop_mated, c->loop_mated);

            int r = strength_line(out, a, c, "LOOP", a->loop_status, c->loop_status, a->loop_level, c->loop_level);
            if (r == 1) ++ahead_a;
            else if (r == -1) ++ahead_b;
            else if (r == 0) ++ties;

            for (int k = 0; k < count_squares; ++k) {
                for (int cond = 0; cond < 2; ++cond) {
                    char fact[32], sq[3];
                    square_text(squares[k], sq);
                    snprintf(fact, sizeof(fact), "GOAL-%s-%s", sq, (cond == 0) ? "REACH" : "PROTECTED");
                    r = strength_line(out, a, c, fact, a->goal_text[k][cond], c->goal_text[k][cond],
                                      a->goal_level[k][cond], c->goal_level[k][cond]);
                    if (r == 1) ++ahead_a;
                    else if (r == -1) ++ahead_b;
                    else if (r == 0) ++ties;
                }
            }

            r = strength_line(out, a, c, "MATERIAL", material_word(a), material_word(c),
                              a->material_known ? (int)a->material : -1,
                              c->material_known ? (int)c->material : -1);
            if (r == 1) ++ahead_a;
            else if (r == -1) ++ahead_b;
            else if (r == 0) ++ties;

            snprintf(va, sizeof(va), "%c %d", a->taken ? a->taken : '-', a->value);
            snprintf(vb, sizeof(vb), "%c %d", c->taken ? c->taken : '-', c->value);
            raw_line(out, a, c, "CAPTURE", a->taken ? va : "none", c->taken ? vb : "none");

            int v_order = order_line(out, a, c, "VALUE-ORDER", a->value_label, c->value_label,
                                     a->value_rank, c->value_rank);
            snprintf(va, sizeof(va), "%d %s", a->squares, a->squares_label);
            snprintf(vb, sizeof(vb), "%d %s", c->squares, c->squares_label);
            int s_order = order_line(out, a, c, "SQUARES-ORDER", va, vb, a->squares_rank, c->squares_rank);

            snprintf(va, sizeof(va), "%d %s", a->group, a->group_label);
            snprintf(vb, sizeof(vb), "%d %s", c->group, c->group_label);

            int ga = (a->group == 1) ? ((2 - a->group_class) * 3) : 6;
            int gb = (c->group == 1) ? ((2 - c->group_class) * 3) : 6;
            ga += (!strcmp(a->group_label, "IF") ? 0 : !strcmp(a->group_label, "ELSE IF") ? 1 : 2);
            gb += (!strcmp(c->group_label, "IF") ? 0 : !strcmp(c->group_label, "ELSE IF") ? 1 : 2);
            order_line(out, a, c, "GROUP", va, vb, a->group ? ga : -1, c->group ? gb : -1);

            const char *word = "NO-DIRECTED-COMPARISON";
            if (ahead_a > 0 && ahead_b > 0) {
                word = "MIXED";
            } else if (ahead_a > 0 || ahead_b > 0) {
                word = "ALL-AHEAD";
            } else if (ties > 0) {
                word = "ALL-TIE";
            }

            text_add(out, "AGREEMENT %s %s %s", a->text, c->text, word);
            if (!strcmp(word, "ALL-AHEAD")) {
                text_add(out, " %s", (ahead_a > 0) ? a->text : c->text);
            }
            text_add(out, "\n");

            int l1 = s_order;
            int l2 = v_order;
            if (l2 == 0) {
                if (a->material_known && c->material_known) {
                    if (a->material > c->material) {
                        l2 = 1;
                    } else if (a->material < c->material) {
                        l2 = -1;
                    } else {
                        l2 = 0;
                    }
                } else {
                    l2 = 2;
                }
            }

            text_add(out, "VIEWS %s %s LOOP-1 %s LOOP-2 %s ", a->text, c->text,
                     (l1 == 1) ? a->text : (l1 == -1) ? c->text : (l1 == 0) ? "SAME-LEVEL" : "NOT-COMPARABLE",
                     (l2 == 1) ? a->text : (l2 == -1) ? c->text : (l2 == 0) ? "SAME-LEVEL" : "NOT-COMPARABLE");
            text_add(out, "%s\n", (l1 == 2 || l2 == 2) ? "NOT-COMPARABLE" : (l1 == l2) ? "SAME-VIEW" : "DIFFERENT-VIEW");
        }
    }

    text_add(out, "COMPARE END\n");
    free(loop_text.text);
    free(real_all.text);
    free(order_text.text);
}

/*
 * parse_compare
 * Parses "compare N m1 m2 ...".
 */
static bool parse_compare(const Board *b, const char *text, int *depth, Move *moves, int *count) {
    if (b == NULL || text == NULL || depth == NULL || moves == NULL || count == NULL) {
        return false;
    }
    char word[16];
    int used = 0, n = 0;

    if (sscanf(text, "%d%n", &n, &used) != 1 || n < 1 || n > 5) {
        return false;
    }
    text += used;

    *count = 0;
    while (sscanf(text, "%15s%n", word, &used) == 1) {
        Move m;
        text += used;

        if (*count == COMPARE_MAX || !parse_move_text(word, &m) || !legal_move(b, m)) {
            return false;
        }

        for (int i = 0; i < *count; ++i) {
            if (moves[i].sr == m.sr && moves[i].sc == m.sc &&
                moves[i].er == m.er && moves[i].ec == m.ec &&
                moves[i].promotion == m.promotion) {
                return false; /* Duplicate move */
            }
        }
        moves[(*count)++] = m;
    }

    if (*count < 2) {
        return false;
    }
    *depth = n;
    return true;
}

/* ============================================================================
 * SECTION 21: MAIN PROGRAM AND INTERACTIVE COMMAND LOOP
 * ============================================================================
 */

/*
 * clear_selection
 * Helper function that resets user selection and preview state variables.
 */
static void clear_selection(int *row, int *col, bool *preview_shown,
                            bool *promotion_choice_pending) {
    *row = -1;
    *col = -1;
    *preview_shown = false;
    *promotion_choice_pending = false;
}

/*
 * main
 * Entry point of the chess program. Runs the interactive game loop.
 */
/*
 * enable_console_colours (Version 16)
 * The board is drawn with ANSI colour codes such as "\033[48;5;180m".
 * Linux, macOS and CLion's own terminal understand them. A Windows console
 * window shows them as colours only after the program asks for it, by
 * switching on "virtual terminal processing" for its output. Without this
 * the codes appear as text, for example "<-[48;5;180m".
 * If the output is not a console (for example a file, as in the transcript
 * tests), GetConsoleMode fails and nothing is changed.
 * On other systems this function does nothing.
 */
static void enable_console_colours(void) {
#ifdef _WIN32
#ifndef ENABLE_VIRTUAL_TERMINAL_PROCESSING
#define ENABLE_VIRTUAL_TERMINAL_PROCESSING 0x0004 /* older headers lack it */
#endif
    HANDLE output = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD mode = 0;

    if (output != INVALID_HANDLE_VALUE && GetConsoleMode(output, &mode)) {
        SetConsoleMode(output, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
    }
#endif
}

int main(void) {
    Board game = {0};
    char input[INPUT_BUFFER_SIZE];
    int selected_row = -1;
    int selected_col = -1;
    bool preview_shown = false;
    Move preview_move = {0, 0, 0, 0, '\0'};
    bool promotion_choice_pending = false;
    Move pending_promotion_move = {0, 0, 0, 0, '\0'};
    bool distance_view = false;
    Tracker tracker;
    Goal goal = {false, false, 0, {0}, 0};
    Goal second_goal = {false, false, 0, {0}, 0};

#ifdef _WIN32
    /*
     * Windows only, and only in a real console window (Version 14's three
     * lines, put back in Version 16): set the console to UTF-8. The check
     * _isatty(0) matters: when the input comes from a file (the transcript
     * tests), the cmd.exe started by system() would use up that input
     * before the game could read it. The colours are switched on below,
     * by enable_console_colours().
     */
    if (_isatty(0)) {
        (void)system("chcp 65001 > nul");
    }
#endif

    /* Done after chcp, so that nothing started by system() can undo it. */
    enable_console_colours();

    puts("=== Simple 2-Player Chess ===");
    reset_board(&game);
    tracker_init(&tracker, &game);

    for (;;) {
        bool stalemate = false;
        const char *draw_reason = NULL;

        /* Verify that both kings are still on the board */
        if (!has_king(&game, WHITE) || !has_king(&game, BLACK)) {
            puts("Invalid position: both kings must be on the board.");
            break;
        }

        /* Render the board to the console */
        display(&game, selected_row, selected_col);

        /* Check for game over (Checkmate, Stalemate, or Draw) */
        if (game_over(&game, &stalemate, &draw_reason)) {
            if (stalemate) {
                puts("Game Over! Stalemate.");
            } else if (draw_reason) {
                printf("Game Over! Draw by %s.\n", draw_reason);
            } else {
                const char *winner = (game.turn == WHITE) ? "Black" : "White";
                printf("Checkmate! %s wins!\n", winner);
            }
            break;
        }

        /* Notify player if their king is currently in check */
        if (is_in_check(&game, game.turn)) {
            printf(CYAN "Your king is in check!\n" RESET);
        }

        /* Print user guidance instructions */
        puts("STEP 2: Select, preview, then explicitly finalize a chess move.");
        if (promotion_choice_pending) {
            puts("PROMOTION:");
            puts("Q = Queen");
            puts("R = Rook");
            puts("B = Bishop");
            puts("N = Knight");
            puts("Type NEW to cancel and select another piece.");
            puts("Type your choice, then press Enter.");
        } else if (!in_bounds(selected_row, selected_col)) {
            puts("Characters 1-2: enter a piece square (e.g. d2), then Enter.");
        } else if (!preview_shown) {
            puts("Characters 3-4: enter a destination (e.g. d4), then Enter.");
            puts("The BEFORE and AFTER lists will appear. NO MOVE is made yet.");
            puts("Press N then Enter to choose a DIFFERENT piece.");
        } else {
            printf("PREVIEW READY: %c%d -> %c%d (NOT played).\n",
                   'a' + preview_move.sc, 8 - preview_move.sr,
                   'a' + preview_move.ec, 8 - preview_move.er);
            puts("F = Finalize move | P = Preview another destination | N = New piece");
            puts("Type one command, then press Enter.");
        }

        if (!preview_shown) {
            puts("Every move requires a preview followed by F + Enter.");
            puts("Other commands: restart, quit, claim, resign");
        }

        print_selection_near_prompt(&game, selected_row, selected_col);

        /* Print contextual prompt */
        if (promotion_choice_pending) {
            printf("%s - choose promotion (Q/R/B/N): ", color_name(game.turn));
        } else if (preview_shown) {
            printf("%s - Enter command (F/P/N): ", color_name(game.turn));
        } else if (in_bounds(selected_row, selected_col)) {
            printf("%s - enter destination (characters 3-4): ", color_name(game.turn));
        } else {
            printf("%s - enter START square (characters 1-2): ", color_name(game.turn));
        }
        fflush(stdout);

        /* Read user input line */
        InputResult input_result = read_input_line(input, sizeof(input));
        if (input_result == INPUT_READ_EOF) {
            break;
        }
        if (input_result == INPUT_READ_TOO_LONG) {
            continue;
        }

        Command command = parse_command(input);

        /* Command: Cancel piece selection (new / n) */
        if (command == COMMAND_NEW ||
            (command == COMMAND_SHORT_NEW && !promotion_choice_pending)) {
            clear_selection(&selected_row, &selected_col, &preview_shown,
                            &promotion_choice_pending);
            puts("NEW SELECTION: now enter characters 1-2 for a different piece.");
            continue;
        }

        /* Command: Stage 3S FEN Print / Load */
        if (strcmp(input, "fen") == 0) {
            char fen_text[FEN_TEXT_SIZE];
            board_to_fen(&game, fen_text);
            printf("FEN: %s\n", fen_text);
            continue;
        }
        if (strncmp(input, "fen ", 4) == 0) {
            const char *reason = NULL;
            if (load_fen(&game, input + 4, &reason)) {
                clear_selection(&selected_row, &selected_col, &preview_shown,
                                &promotion_choice_pending);
                tracker_init(&tracker, &game);
                puts("FEN loaded: practice position set up.");
            } else {
                printf(RED "FEN rejected: %s. The position is unchanged." RESET "\n", reason);
            }
            continue;
        }

        /* Command: Promotion Choice */
        if (promotion_choice_pending && strlen(input) == 1) {
            char choice = (char)toupper((unsigned char)input[0]);
            if (strchr("QRBN", choice) != NULL) {
                pending_promotion_move.promotion = choice;
                show_step2_after(&game, pending_promotion_move);
                if (goal.active) {
                    TextBuffer marks = {NULL, 0, 0};
                    goal_marks_after(&game, &goal, pending_promotion_move, &marks);
                    if (marks.text != NULL) {
                        fputs(marks.text, stdout);
                        free(marks.text);
                    }
                }
                if (distance_view) {
                    TextBuffer view = {NULL, 0, 0};
                    distance_after(&game, pending_promotion_move, &view);
                    if (view.text != NULL) {
                        fputs(view.text, stdout);
                        free(view.text);
                    }
                }
                preview_move = pending_promotion_move;
                preview_shown = true;
                promotion_choice_pending = false;
                continue;
            }
        }
        if (promotion_choice_pending && !is_game_command(command)) {
            puts(RED "Choose Q, R, B or N; or type NEW to cancel." RESET);
            continue;
        }

        /* Command: Stage 3A Calculator Report ('R') */
        if (!strcmp(input, "r") || !strcmp(input, "R")) {
            if (!preview_shown) {
                puts(RED "No preview to report. Select a piece and preview a destination, then type R." RESET);
            } else {
                TextBuffer report = {NULL, 0, 0};
                calc_report(&game, &tracker, preview_move, &report);
                if (report.text != NULL) {
                    fputs(report.text, stdout);
                    free(report.text);
                }
            }
            continue;
        }

        /* Command: Stage 3B Replies Report */
        if (!strcmp(input, "replies") || !strncmp(input, "replies ", 8)) {
            TextBuffer view = {NULL, 0, 0};
            Move reply;
            if (!preview_shown) {
                puts(RED "No preview to answer. Select a piece and preview a destination, then type replies." RESET);
            } else if (input[7] == '\0') {
                replies_report(&game, &tracker, preview_move, &view);
            } else if (!parse_move_text(input + 8, &reply) ||
                       !reply_detail(&game, &tracker, preview_move, reply, &view)) {
                puts(RED "Not a legal reply. Type replies to list them, or replies e7e5 for one." RESET);
            }
            if (view.text != NULL) {
                fputs(view.text, stdout);
                free(view.text);
            }
            continue;
        }

        /* Command: Stage 3C Game Tree Loop */
        if (!strcmp(input, "loop") || !strncmp(input, "loop ", 5)) {
            int depth = 0, zero_k = 0;
            if (input[4] == '\0' || !parse_loop_args(input + 5, &depth, &zero_k)) {
                puts(RED "Type loop and a depth from 1 to 6, for example loop 3 (or loop 3 6 to also count pieces that can't move)." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                if (depth >= 5) {
                    printf("Searching %d plies. This can take minutes (5 plies: about half a minute to a few minutes; 6: much longer).\n", depth);
                    fflush(stdout);
                }
                loop_report(&game, depth, zero_k, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3D Goals */
        if (!strcmp(input, "goal") || !strncmp(input, "goal ", 5)) {
            TextBuffer view = {NULL, 0, 0};
            if (input[4] == '\0') {
                if (goal.active) {
                    text_add(&view, "GOAL ACTIVE ");
                    goal_text(&goal, &view);
                    text_add(&view, " LIMIT %d PASS\n", goal.limit);
                } else {
                    text_add(&view, "No goal is active. Type goal f7 2 (squares, then a limit of own moves 1 to 4).\n");
                }
            } else if (!strcmp(input + 5, "off")) {
                goal.active = false;
                text_add(&view, "Goal cleared.\n");
            } else if (parse_goal(input + 5, &goal)) {
                text_add(&view, "GOAL ACTIVE ");
                goal_text(&goal, &view);
                text_add(&view, " LIMIT %d PASS\n", goal.limit);
            } else {
                puts(RED "Type goal, squares and a limit from 1 to 4, for example goal f7 2, goal f7 g7 h7 3 or goal king 2; goal off clears it." RESET);
            }
            if (view.text != NULL) {
                fputs(view.text, stdout);
                free(view.text);
            }
            continue;
        }

        /* Command: Stage 3D Distance View Toggle */
        if (!strcmp(input, "distance") || !strcmp(input, "distance on") || !strcmp(input, "distance off")) {
            if (input[8] == ' ') {
                distance_view = (input[10] == 'n');
            }
            printf("DISTANCE ORDER %s\n", distance_view ? "ON" : "OFF");
            continue;
        }

        /* Command: Stage 3D Second Goal */
        if (!strcmp(input, "goal2") || !strncmp(input, "goal2 ", 6)) {
            if (input[5] == '\0') {
                if (second_goal.active) {
                    TextBuffer view = {NULL, 0, 0};
                    text_add(&view, "SECOND GOAL ACTIVE ");
                    goal_text(&second_goal, &view);
                    text_add(&view, " LIMIT %d PASS\n", second_goal.limit);
                    if (view.text != NULL) {
                        fputs(view.text, stdout);
                        free(view.text);
                    }
                } else {
                    puts("No second goal is active. Type goal2 d5 2 (squares, then a limit of own moves 1 to 4).");
                }
            } else if (!strcmp(input + 6, "off")) {
                second_goal.active = false;
                puts("Second goal cleared.");
            } else if (parse_goal(input + 6, &second_goal)) {
                TextBuffer view = {NULL, 0, 0};
                text_add(&view, "SECOND GOAL ACTIVE ");
                goal_text(&second_goal, &view);
                text_add(&view, " LIMIT %d PASS\n", second_goal.limit);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            } else {
                puts(RED "Type goal2, squares and a limit from 1 to 4, for example goal2 d5 2; goal2 off clears it." RESET);
            }
            continue;
        }

        /* Command: Stage 3D Real Routes */
        if (!strncmp(input, "routes ", 7)) {
            int depth = 0;
            if (!goal.active) {
                puts(RED "No goal is active. Type goal f7 2 first, then routes." RESET);
            } else if (!parse_routes_real(input + 7, &depth)) {
                puts(RED "Type routes (PASS), or routes real and a depth from 1 to 6, for example routes real 3." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                if (depth >= 5) {
                    printf("Searching %d plies. This can take minutes.\n", depth);
                    fflush(stdout);
                }
                routes_real_report(&game, &goal, depth, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3E Exchange Analysis */
        if (!strcmp(input, "exchange") || !strncmp(input, "exchange ", 9)) {
            int sq = 0, limit = 0;
            if (input[8] == '\0' || !parse_exchange(input + 9, &sq, &limit)) {
                puts(RED "Type exchange, a square and a limit of captures from 1 to 8, for example exchange e5 4." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                exchange_report(&game, sq, limit, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3E Order Report */
        if (!strcmp(input, "order") || !strncmp(input, "order ", 6)) {
            int limit = 0, used = 0;
            if (input[5] == '\0' || sscanf(input + 6, "%d%n", &limit, &used) != 1 ||
                input[6 + used] != '\0' || limit < 1 || limit > EXCHANGE_MAX) {
                puts(RED "Type order and an exchange limit from 1 to 8, for example order 4." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                order_report(&game, limit, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3F Multi-Move Comparison */
        if (!strcmp(input, "compare") || !strncmp(input, "compare ", 8)) {
            Move moves[COMPARE_MAX];
            int depth = 0, count = 0;
            if (input[7] == '\0' || !parse_compare(&game, input + 8, &depth, moves, &count)) {
                puts(RED "Type compare, a depth from 1 to 5, then 2 to 6 different legal moves, for example compare 3 d1h5 d1f3 g1f3." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                if (depth >= 5) {
                    printf("Searching %d plies. This can take minutes.\n", depth);
                    fflush(stdout);
                }
                compare_report(&game, &tracker, &goal, depth, moves, count, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3E Risk On/Off */
        if (!strcmp(input, "risk") || !strcmp(input, "risk on") || !strcmp(input, "risk off")) {
            if (input[4] == ' ') {
                goal_show_risk = (input[6] == 'n');
            }
            printf("AT-RISK %s\n", goal_show_risk ? "ON" : "OFF");
            continue;
        }

        /* Command: Stage 3D Support Report */
        if (!strcmp(input, "support")) {
            if (!preview_shown) {
                puts(RED "No preview to support. Select a piece and preview a destination, then type support." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                support_report(&game, preview_move, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3D PASS Routes */
        if (!strcmp(input, "routes")) {
            if (!goal.active) {
                puts(RED "No goal is active. Type goal f7 2 first, then routes." RESET);
            } else {
                TextBuffer view = {NULL, 0, 0};
                routes_report_with(&game, &goal, &second_goal, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }
            continue;
        }

        /* Command: Stage 3C Trace Sequence */
        if (!strcmp(input, "trace") || !strncmp(input, "trace ", 6)) {
            TextBuffer view = {NULL, 0, 0};
            int bad_ply = 0;
            if (!trace_report(&game, &tracker, input[5] == '\0' ? "" : input + 6, &view, &bad_ply)) {
                printf(RED "Not a legal sequence (move %d). Type trace and moves, for example trace e2e4 e7e5." RESET "\n",
                       bad_ply);
            }
            if (view.text != NULL) {
                fputs(view.text, stdout);
                free(view.text);
            }
            continue;
        }

        /* Command: Finalize Previewed Move ('F') */
        if (command == COMMAND_FINALIZE) {
            if (!preview_shown || !in_bounds(selected_row, selected_col)) {
                puts(RED "No preview to finalize. Select a piece and preview a destination first." RESET);
                continue;
            }
            if (!legal_move(&game, preview_move)) {
                puts(RED "Preview is no longer legal. Start a new selection." RESET);
                preview_shown = false;
                continue;
            }

            printf("FINALIZED: %c%d -> %c%d\n",
                   'a' + preview_move.sc, 8 - preview_move.sr,
                   'a' + preview_move.ec, 8 - preview_move.er);

            tracker_commit(&tracker, &game, preview_move);
            make_move(&game, preview_move);
            record_position(&game);
            clear_selection(&selected_row, &selected_col, &preview_shown,
                            &promotion_choice_pending);
            continue;
        }

        /* Command: Discard Preview ('P') */
        if (command == COMMAND_PREVIEW) {
            if (!in_bounds(selected_row, selected_col)) {
                puts(RED "Select a piece first." RESET);
            } else {
                preview_shown = false;
                puts("Preview cleared. Enter another destination for the selected piece.");
            }
            continue;
        }

        /* If preview is already shown, require F, P, or N before entering another square */
        if (preview_shown && strlen(input) == 2) {
            puts(RED "Preview already shown. Press F, P or N, then Enter." RESET);
            continue;
        }

        /* Square entry: exactly 2 characters (e.g. "e2" or "e4") */
        if (strlen(input) == 2) {
            int row, col;
            if (!parse_square(input, &row, &col)) {
                puts(RED "Enter a square such as d2." RESET);
                continue;
            }

            /* Case 1: No piece currently selected -> Select START square */
            if (!in_bounds(selected_row, selected_col)) {
                if (game.board[row][col].color != game.turn) {
                    puts(RED "Choose a square containing your own piece." RESET);
                    continue;
                }
                selected_row = row;
                selected_col = col;
                preview_shown = false;
                print_selection_near_prompt(&game, row, col);
                puts("Piece selected. BEFORE/AFTER lists will appear together after the destination.");

                if (goal.active) {
                    TextBuffer marks = {NULL, 0, 0};
                    goal_marks_selection(&game, &goal, row, col, &marks);
                    if (marks.text != NULL) {
                        fputs(marks.text, stdout);
                        free(marks.text);
                    }
                }
                if (distance_view) {
                    TextBuffer view = {NULL, 0, 0};
                    distance_selection(&game, row, col, &view);
                    if (view.text != NULL) {
                        fputs(view.text, stdout);
                        free(view.text);
                    }
                }
                continue;
            }

            /* Case 2: Piece already selected -> Preview DESTINATION square */
            Move chosen = {selected_row, selected_col, row, col, '\0'};
            if (!legal_move(&game, chosen)) {
                puts(RED "Not a legal destination. Press N then Enter to select a different piece." RESET);
                continue;
            }

            /* Check for pawn promotion: prompt for choice before showing preview */
            if (game.board[selected_row][selected_col].type == 'P' &&
                (row == 0 || row == 7)) {
                pending_promotion_move = chosen;
                promotion_choice_pending = true;
                puts("PROMOTION: choose Q (Queen), R (Rook), B (Bishop), or N (Knight).");
                puts("Type NEW to cancel and choose a different starting piece.");
                continue;
            }

            /* Show Step 2 comparative preview */
            show_step2_after(&game, chosen);

            if (goal.active) {
                TextBuffer marks = {NULL, 0, 0};
                goal_marks_after(&game, &goal, chosen, &marks);
                if (marks.text != NULL) {
                    fputs(marks.text, stdout);
                    free(marks.text);
                }
            }
            if (distance_view) {
                TextBuffer view = {NULL, 0, 0};
                distance_after(&game, chosen, &view);
                if (view.text != NULL) {
                    fputs(view.text, stdout);
                    free(view.text);
                }
            }

            preview_move = chosen;
            preview_shown = true;
            continue;
        }

        /* Command: Quit */
        if (command == COMMAND_QUIT) {
            break;
        }

        /* Command: Restart */
        if (command == COMMAND_RESTART) {
            reset_board(&game);
            tracker_init(&tracker, &game);
            clear_selection(&selected_row, &selected_col, &preview_shown,
                            &promotion_choice_pending);
            puts("Game restarted.");
            continue;
        }

        /* Command: Resign */
        if (command == COMMAND_RESIGN) {
            Color winner = opposite(game.turn);
            printf("%s resigns. %s wins.\n",
                   color_name(game.turn),
                   color_name(winner));
            break;
        }

        /* Command: Claim Draw */
        if (command == COMMAND_CLAIM) {
            if (claimable_draw(&game, (Move){0, 0, 0, 0, '\0'},
                               false, &draw_reason)) {
                printf("Game Over! Draw claimed by %s.\n", draw_reason);
                break;
            }
            puts(RED "No draw claim is currently available." RESET);
            continue;
        }

        /* Direct moves disabled message */
        if (strlen(input) == 4 || strlen(input) == 5 ||
            !strncmp(input, "offer ", 6) ||
            !strncmp(input, "claim ", 6)) {
            puts(RED "Direct moves are disabled. Enter the START square, then the"
                     " destination, review BEFORE/AFTER, and press F + Enter." RESET);
            continue;
        }

        puts(RED "Unknown command. Enter a square, or use F, P, N, restart, quit, claim or resign." RESET);
    }

    /* Clean up allocated history buffer before exiting */
    free(game.history);
    return 0;
}
