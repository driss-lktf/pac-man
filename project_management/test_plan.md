# Acceptance Test Plan

Legend: ✅ pass.  Automated tests live in `tests/` (`make test`).

## Configuration & errors

| Test | Expected | Status |
|------|----------|--------|
| No argument / too many arguments | Usage message, exit 1, no traceback | ✅ |
| Config file with any name (no `.json` suffix) | Accepted if its content is JSON | ✅ (unit) |
| Non-JSON content | Clear error, exit 1 | ✅ (unit) |
| Missing file | Clear error, exit 1 | ✅ |
| Invalid JSON | Clear error, exit 1 | ✅ |
| JSON not an object | Clear error, exit 1 | ✅ |
| `#`, `//`, `/* */` comments | Parsed and ignored | ✅ (unit) |
| Comment markers inside strings | Preserved | ✅ (unit) |
| Out-of-range / wrong-type values | Clamped to defaults, warning logged | ✅ (unit) |
| Fewer than 10 levels | Padded to 10 | ✅ (unit) |
| Singular `level` key instead of `levels` | Accepted | ✅ (unit) |
| Unknown keys | Ignored, no warning-driven failure | ✅ (unit) |
| `pacgum` count (e.g. 42) | That many pacgums per level | ✅ (unit) |
| `pacgum` negative / absent | Falls back to 0 = fill every corridor | ✅ (unit) |

## Maze & layout

| Test | Expected | Status |
|------|----------|--------|
| First level uses fixed seed | Deterministic maze | ✅ (unit) |
| Player spawns in the middle on a corridor | Walkable cell | ✅ (unit) |
| 4 ghosts + 4 super-pacgums in corners | Present | ✅ (unit) |
| All pacgums reachable | Level always clearable | ✅ (unit) |
| Passages are symmetric | Two-way corridors | ✅ (unit) |
| Generator raises / returns an empty grid | Clean `RuntimeError`, back to the main menu with a message | ✅ (unit) |

## Gameplay

| Test | Expected | Status |
|------|----------|--------|
| Move with arrows / WASD | Player moves in corridors only | ✅ |
| Eat pacgum / super-pacgum | Score increases; ghosts become edible | ✅ |
| Eat edible ghost | Score += ghost points; ghost returns home | ✅ |
| Touch normal ghost | Lose a life, respawn in the middle | ✅ |
| Lose all lives | Game over screen | ✅ |
| Clear all pacgums | Advance to next level | ✅ |
| Complete last level | Victory screen | ✅ |
| Level timer reaches 0 | Lose a life / restart positions | ✅ |
| Pause / resume (Esc) | Game freezes & resumes | ✅ |

## UI & highscores

| Test | Expected | Status |
|------|----------|--------|
| Main menu navigation | Start / Highscores / Instructions / Exit | ✅ |
| HUD | Score, lives, level, time visible | ✅ |
| Enter name at end (win or lose) | Sanitized, ≤ 10 chars | ✅ |
| Top-10 persistence | Saved & reloaded across runs | ✅ (unit) |
| Corrupted highscore file | Ignored gracefully | ✅ (unit) |

## Cheat mode

| Key | Effect | Status |
|-----|--------|--------|
| F1 | Invincibility on/off | ✅ |
| F2 | Freeze ghosts on/off | ✅ |
| F3 | Skip current level | ✅ |
| F4 | Add a life | ✅ |
| F5 | Cycle player speed | ✅ |

## Graphical layer (MLX equivalence, subject v1.5)

| Test | Expected | Status |
|------|----------|--------|
| Only MLX-equivalent calls used | No `pygame.draw.*`, no alpha, no sprites outside `canvas.py` | ✅ (grep audit) |
| `put_pixel` writes exactly one pixel | Neighbours untouched | ✅ (unit) |
| `put_pixel` out of bounds | Ignored, no crash | ✅ (unit) |
| Pixel run clipped to the image | No overflow | ✅ (unit) |
| Rect / rounded rect / disc / ellipse / polygon | Correct fill and bounds | ✅ (unit) |
| Line endpoints | Both drawn (Bresenham) | ✅ (unit) |
| Image copy (`mlx_image_to_window`) | Pasted at the right offset | ✅ (unit) |
| String drawing | Pixels produced, width measurable | ✅ (unit) |
| Frame rate, largest maze (41×41) | ≥ 60 FPS | ✅ (~950 FPS measured headless) |
| Eaten pacgum erased from the cached level image | No ghost pixels left | ✅ (visual) |

## Quality gates

| Gate | Status |
|------|--------|
| `flake8 .` | ✅ clean |
| `mypy` (mandatory flags) | ✅ no issues |
| `mypy --strict` (`make lint-strict`) | ✅ no issues |
| `pytest` | ✅ 37 passed |
