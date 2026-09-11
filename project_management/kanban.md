# Timeline & Kanban

## Timeline (planned vs actual)

| Phase | Planned | Actual | Notes |
|-------|---------|--------|-------|
| Subject analysis & architecture | Day 1 | Day 1 | Module split decided up front |
| Config loader (JSON + comments) | Day 1 | Day 1 | Defaults & clamping included |
| Maze adapter over `mazegenerator` | Day 2 | Day 2 | Wall-bit encoding understood |
| Entities & smooth movement | Day 2–3 | Day 2–3 | Tile interpolation model |
| Ghost AI | Day 3 | Day 3 | 4 personalities |
| Game rules (score/lives/timer) | Day 3–4 | Day 4 | Centralized in `Game` |
| Rendering & HUD | Day 4 | Day 4 | Drawn with primitives, no assets |
| Menus / screens / name entry | Day 4–5 | Day 5 | State machine in `App` |
| Highscore persistence | Day 5 | Day 5 | JSON, robust to errors |
| Cheat mode | Day 5 | Day 5 | F1–F5 |
| Tests, lint, README, packaging | Day 6 | Day 6 | flake8 + mypy clean, pytest green |
| Subject v1.5 update (MLX rule) + generator 2.1.0 | — | Day 7 | Unplanned rework, see below |

## Change log — subject v1.4 → v1.5 (Day 7)

The subject was updated to v1.5 while the mandatory scope was already
complete. Diffing both PDFs showed a single functional change: a graphical
library is now considered *similar to MLX* only if **every function used has
an MLX equivalent**. At the same time, a new revision (2.1.0) of the assigned
A-Maze-ing package was delivered.

Actions taken:

- Audited every graphical call in the project. `pygame.draw.*`, alpha
  surfaces and `Surface.blit`-based overlays had no MLX counterpart.
- Introduced `pacman/canvas.py`, an MLX-equivalent layer (window, images,
  `put_pixel`, image-to-window, string drawing, event polling). Every shape is
  now rasterised by us on top of those primitives.
- Rewrote `pacman/render.py` and the drawing paths of `pacman/app.py` against
  that layer; the pause overlay became an opaque panel (MiniLibX has no alpha).
- Kept 60 FPS by caching the static level in an off-screen image, the way an
  MLX program builds an image once and calls `mlx_image_to_window` per frame.
- Upgraded the vendored A-Maze-ing package from 2.0.2 to 2.1.0 **as-is**, and
  shipped its wheel for re-installation during the peer review. No adapter
  change was needed — the interface is unchanged; 2.1.0 additionally braids
  the maze when `perfect=False`, which removes dead-ends.
- Hardened the configuration for the defense update: the singular `level`
  key is accepted alongside `levels`, and the suggested `pacgum` key now caps
  the number of pacgums placed per level.

## Blocking points & conflicts

- **None blocking.** The only friction was the v1.5 MLX rule landing after the
  renderer was finished. It was resolved by isolating the graphical library
  behind a single module rather than patching call sites — which also means a
  future rule change touches one file.

## Kanban board (final state)

### Backlog
- _(empty — mandatory scope complete)_

### In progress
- _(empty)_

### Done
- [x] Argument & error handling (no traceback)
- [x] JSON-with-comments configuration + validation/clamping
- [x] External maze generation integration (`perfect=False`, fixed first seed)
- [x] Pacgums in corridors, super-pacgums + ghosts in the 4 corners
- [x] Player in the middle, 4-direction movement (arrows / WASD)
- [x] Lives, respawn, game over
- [x] Ghost AI: chase / flee when edible / return when eaten
- [x] Scoring (pacgum / super-pacgum / ghost), non-decreasing
- [x] Per-level timer with timeout handling
- [x] ≥ 10 levels, score & lives carried over, victory screen
- [x] Pause / resume
- [x] Main menu, highscores view, instructions, end screens
- [x] Persistent top-10 highscore with name entry
- [x] Cheat mode (invincibility, freeze, skip, lives, speed)
- [x] Makefile (install/run/debug/lint/lint-strict/clean)
- [x] Unit tests, flake8 & mypy clean
- [x] README with all required sections
- [x] Packaging script for Itch.io
