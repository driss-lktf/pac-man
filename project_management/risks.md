# Risk Analysis

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| 1 | Config updated at defense with invalid/missing values | High | High | Every key validated, clamped to safe defaults, unknown keys ignored, no traceback. Covered by tests. |
| 2 | Assigned `mazegenerator` re-installed / different version | Medium | High | We consume the public interface as-is via a thin adapter (`maze.py`); no dependency on internals. |
| 3 | Maze generator fails or returns an empty grid | Low | High | Generation wrapped in try/except → clean `RuntimeError` surfaced as a friendly message. |
| 4 | Deep recursion on large mazes (`RecursionError`) | Medium | Medium | Recursion limit raised before generation, restored after. Tested up to 41×41. |
| 5 | Unreachable pacgums make a level unbeatable | Medium | High | Symmetric two-way passage check; connectivity verified by tests on several sizes. |
| 6 | Crash during review (unhandled exception) | Medium | High | Top-level guard in `pac-man.py` catches everything and prints a clean message. |
| 7 | Corrupted highscore file | Low | Medium | Load/save tolerate any file error and fall back to an empty table. |
| 8 | Reviewer cannot test all features quickly | Medium | Medium | Cheat mode (F1–F5) exposes invincibility, freeze, level skip, extra lives, speed. |
| 9 | flake8 / mypy failures at review | Low | Medium | `make lint` run continuously; CI-like gate before each commit. |
| 10 | Packaging build differs from local run | Low | Medium | `pacman.spec` bundles `config.json` and the maze package; documented steps. |
| 11 | Graphical library judged not "similar to MLX" (subject v1.5) | Medium | High | All rendering goes through `pacman/canvas.py`, which exposes only MLX-equivalent operations (`put_pixel`, images, image-to-window, strings, hooks); shapes are rasterised by us. Mapping table documented in the README. |
| 12 | Subject or assigned package updated again mid-project | Medium | Medium | Graphical library isolated in one module, generator behind one adapter — both swappable without touching game logic. |
| 13 | Per-pixel drawing too slow in Python | Medium | Medium | Static level cached in an off-screen image, horizontal spans written in one go; measured > 700 FPS on the largest maze. |
