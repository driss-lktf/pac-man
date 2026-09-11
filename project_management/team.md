# Team Organization

## Members

| Login | Main focus |
|-------|-----------|
| `dlaktaf` | Architecture, maze integration, game rules, packaging |
| `dsom` | Rendering/UI, ghost AI, highscores, tests |

> Pair-programming was used on the trickiest parts (movement model, ghost AI).

## How decisions were made

- **Architecture:** agreed up front on a strict module split (config / maze /
  entities / game / render / app) so the two of us could work in parallel with
  minimal conflicts.
- **Movement model:** chose tile-to-tile interpolation over free pixel movement
  to keep collisions and corridor alignment simple and bug-free.
- **Configuration schema:** designed around the subject's suggested keys, with
  defaults documented in the README.
- **Highscore storage:** picked a plain JSON file for portability and easy
  review (no external dependency).

## How issues were handled

- Each feature was kept independently runnable; regressions were caught early by
  `make lint` and `make test` before every commit.
- Blocking points (e.g., understanding the maze wall-bit encoding) were resolved
  by writing small throwaway scripts and a connectivity test rather than
  guessing.

## Blocking points & conflicts

- **Wall-bit encoding** of `mazegenerator` was initially unclear → resolved by
  reading the package docstring/METADATA and validating with a connectivity
  test (all pellets reachable).
- **Player spawn / corners possibly on a wall block** (the central "42"
  pattern) → resolved with a nearest-walkable BFS.
- No major conflicts: the module boundaries kept merges clean.
