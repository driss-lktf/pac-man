"""Tests for maze loading, layout and connectivity."""

from __future__ import annotations

from collections import deque

import pytest

import pacman.maze as maze_module
from pacman.constants import DIRECTIONS, SUPER_PACGUM
from pacman.maze import Maze


def _reachable(maze: Maze) -> set[tuple[int, int]]:
    """Return every cell reachable from the player's spawn."""
    seen = {maze.player_start}
    queue: deque[tuple[int, int]] = deque([maze.player_start])
    while queue:
        x, y = queue.popleft()
        for direction in DIRECTIONS:
            if maze.can_move(x, y, direction):
                nxt = (x + direction[0], y + direction[1])
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return seen


def test_seed_is_deterministic() -> None:
    first = Maze(19, 19, seed=42)
    second = Maze(19, 19, seed=42)
    assert first.grid == second.grid


def test_player_starts_on_a_corridor() -> None:
    maze = Maze(21, 21, seed=42)
    assert not maze.is_wall(*maze.player_start)


def test_four_ghost_corners() -> None:
    maze = Maze(21, 21, seed=42)
    assert len(maze.ghost_starts) == 4
    for cell in maze.ghost_starts:
        assert not maze.is_wall(*cell)


def test_super_pacgums_in_corners() -> None:
    maze = Maze(21, 21, seed=42)
    supers = [c for c, k in maze.pellets.items() if k == SUPER_PACGUM]
    assert len(supers) == 4


def test_all_pellets_are_reachable() -> None:
    for size in (15, 21, 31, 41):
        maze = Maze(size, size, seed=42)
        reachable = _reachable(maze)
        assert all(cell in reachable for cell in maze.pellets)


def test_can_move_is_symmetric() -> None:
    maze = Maze(19, 19, seed=42)
    opp = {0: 1, 1: 0, 2: 3, 3: 2}
    for y in range(maze.height):
        for x in range(maze.width):
            for i, direction in enumerate(DIRECTIONS):
                nx, ny = x + direction[0], y + direction[1]
                if not (0 <= nx < maze.width and 0 <= ny < maze.height):
                    continue
                back = DIRECTIONS[opp[i]]
                assert maze.can_move(x, y, direction) == \
                    maze.can_move(nx, ny, back)


def test_pacgum_limit_caps_the_number_of_pacgums() -> None:
    maze = Maze(21, 21, seed=42, pacgum_limit=42)
    pacgums = [c for c, k in maze.pellets.items() if k != SUPER_PACGUM]
    assert len(pacgums) == 42
    assert maze.pacgum_total == 46  # 42 pacgums + the 4 super-pacgums


def test_pacgum_limit_above_capacity_fills_every_corridor() -> None:
    full = Maze(19, 19, seed=42)
    capped = Maze(19, 19, seed=42, pacgum_limit=100000)
    assert capped.pacgum_total == full.pacgum_total


def test_player_start_never_holds_a_pellet() -> None:
    maze = Maze(19, 19, seed=42)
    assert maze.player_start not in maze.pellets or \
        maze.pellets[maze.player_start] == SUPER_PACGUM


def test_generator_failure_is_reported_as_runtime_error(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken external generator must surface as a clean RuntimeError."""
    class Boom:
        def __init__(self, **kwargs: object) -> None:
            raise ValueError("generator exploded")

    monkeypatch.setattr(maze_module, "MazeGenerator", Boom)
    with pytest.raises(RuntimeError):
        Maze(19, 19, seed=42)


def test_generator_returning_an_empty_grid_is_rejected(
        monkeypatch: pytest.MonkeyPatch) -> None:
    class Empty:
        def __init__(self, **kwargs: object) -> None:
            self.maze: list[list[int]] = []

    monkeypatch.setattr(maze_module, "MazeGenerator", Empty)
    with pytest.raises(RuntimeError):
        Maze(19, 19, seed=42)


def test_eat_removes_pellet() -> None:
    maze = Maze(19, 19, seed=42)
    cell = next(iter(maze.pellets))
    before = maze.remaining
    assert maze.eat(cell) is not None
    assert maze.remaining == before - 1
    assert maze.eat(cell) is None
