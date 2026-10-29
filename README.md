# chess-python

A two-player chess program in Python, converted from [chess-c99](https://github.com/IWatchSheep/chess-c99) version 16, plus a five-move memory window.

The program reports what a move changes. Choosing a move is left to [AI-Vision-3D](https://github.com/IWatchSheep/AI-Vision-3D), which ranks strategies and targets from these reports.

`chess.txt` is the original C99 source, kept for comparison. The C repository is archived.

## Run

No packages to install. From this folder:

```sh
python3 main.py
```

Widen the console to about 140 columns for the before/after report.

Run the tests with:

```sh
python3 -m unittest test_engine.py test_main.py
```

## How to move

1. Type the square of one of your pieces, for example `e2`.
2. Type a destination, for example `e4`. Nothing is played yet. The report shows every other piece’s squares before and after, and what it gained, lost, and kept.
3. Type `F` to play that preview. `P` tries another destination for the same piece. `N` picks a different piece.

A typed move such as `e2e4` is refused. Promotion asks for `Q`, `R`, `B`, or `N`.

Other game commands: `restart`, `quit`, `claim`, `resign`, `fen`, `fen <FEN>`, `help`.

## Five-move memory

Type `memory` after any preview or played move.

The window holds the latest 4 played moves and the preview waiting for `F`. Each entry stores the move, the side, the FEN before, the FEN after, squares gained, squares lost, how many destinations stayed the same, and the squares whose piece changed. The last line compares the oldest before-position with the latest after-position.

`F` stores the preview and drops the oldest played move once five have been played. `P` and `N` drop the preview only. `restart`, and a FEN that loads, clear the window. A rejected FEN leaves it in place.

This window is separate from the draw-rule history. A pawn move or a capture clears that draw history. `memory` keeps its own record.

## Fact reports

After a preview:

| Command | What it prints |
|---|---|
| `R` | Facts for every piece: moves lost, gained, and restored; protection; attacks; check; mate-in-one threats |
| `replies` | Every legal answer, labeled `STOPS`, `LEAVES`, `NO-THREAT`, or `ALLOWS` |
| `replies e7e5` | The full report for one answer |
| `loop 3` | Every line up to 3 plies, and whether a mate is forced or only possible |
| `trace e2e4 e7e5` | The `R` report along one line |
| `goal f7 2` | Marks moves that can reach the square within the limit |
| `routes` | Shortest routes, with protection on arrival |
| `routes real 3` | The same goal with the other side answering |
| `support` | Moves that would protect the previewed piece |
| `exchange e5 4` | Capture orders on one square |
| `order 4` | Captures first, then the other moves by distance |
| `compare 3 d1h5 d1f3 g1f3` | Candidate moves compared fact by fact |
| `distance on` | Order moves by the squares they travel |
| `risk on` | Show a piece arriving on an attacked goal square |

`help` lists these. `help goal` prints one topic.

## Layout

| Path | Role |
|---|---|
| `main.py` | The game loop |
| `chess_engine/movegen.py`, `board.py` | Rules, FEN, castling, en passant, repetition |
| `chess_engine/ui.py` | The board and the before/after preview |
| `chess_engine/move_memory.py` | The five-move window |
| `chess_engine/study/` | Fact reports: `calc`, `replies`, `search`, `goals`, `exchange` |
| `test_engine.py`, `test_main.py` | Rules, reports, and the memory window |
