"""Maze loading and level layout.

This module is the *adapter* around the assigned ``mazegenerator``
package: it consumes the package's public interface as-is (the ``maze``
grid plus ``maze_entry`` / ``maze_exit``) and turns it into everything the
game needs -- walkable cells, pacgum placement, player and ghost spawns.
"""

from __future__ import annotations

import sys
from collections import deque
from typing import Dict, List, Optional, Tuple

from mazegenerator import MazeGenerator

from .constants import (
    DIRECTIONS,
    PACGUM,
    SUPER_PACGUM,
    WALL_ALL,
)

Cell = Tuple[int, int]


class Maze:
    """A single playable level built from a generated maze.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        grid: The raw wall-encoded grid from the generator.
        pellets: Mapping of cell -> pellet type (pacgum/super-pacgum).
        player_start: The cell where the player spawns.
        ghost_starts: One spawn cell per ghost (the four corners).
        pacgum_total: Number of pellets to eat to clear the level.
    """

    def __init__(self, width: int, height: int, seed: int,
                 pacgum_limit: int = 0) -> None:
        """Generate a maze and lay out its contents.

        Args:
            width: Desired maze width in cells.
            height: Desired maze height in cells.
            seed: Generator seed (0 means fully random).
            pacgum_limit: Maximum number of pacgums to place; ``0`` fills
                every corridor cell.

        Raises:
            RuntimeError: If the external generator fails.
        """
        self.width = width
        self.height = height
        self.pacgum_limit = max(0, pacgum_limit)
        self.grid: List[List[int]] = self._build_grid(width, height, seed)
        self.pellets: Dict[Cell, int] = {}
        self.player_start: Cell = (width // 2, height // 2)
        self.ghost_starts: List[Cell] = []
        self.pacgum_total: int = 0
        self._layout()

    @staticmethod
    def _build_grid(width: int, height: int, seed: int) -> List[List[int]]:
        """Call the external generator defensively and return its grid."""
        # The generator carves the maze recursively; raise the recursion
        # limit so large mazes never trigger a RecursionError.
        previous_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(previous_limit, width * height * 4 + 1000))
        try:
            generator = MazeGenerator(
                size=(width, height), perfect=False, seed=seed)
            raw = generator.maze
            grid: List[List[int]] = [[int(v) for v in row] for row in raw]
        except Exception as error:
            raise RuntimeError(f"maze generator failed: {error}")
        finally:
            sys.setrecursionlimit(previous_limit)
        if not grid or not grid[0]:
            raise RuntimeError("maze generator returned an empty grid")
        return grid

    def is_wall(self, x: int, y: int) -> bool:
        """Return whether the cell is a solid block or out of bounds."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        return self.grid[y][x] == WALL_ALL

    def can_move(self, x: int, y: int, direction: Tuple[int, int, int, int]
                 ) -> bool:
        """Return whether moving from ``(x, y)`` in ``direction`` is legal.

        A passage exists only when both adjacent cells agree it is open,
        which guarantees symmetric, two-way corridors.

        Args:
            x: Source cell x.
            y: Source cell y.
            direction: A direction tuple from :data:`constants.DIRECTIONS`.

        Returns:
            ``True`` if the move is allowed.
        """
        dx, dy, my_wall, their_wall = direction
        nx, ny = x + dx, y + dy
        if self.is_wall(nx, ny) or self.is_wall(x, y):
            return False
        if self.grid[y][x] & my_wall:
            return False
        if self.grid[ny][nx] & their_wall:
            return False
        return True

    def _nearest_walkable(self, target: Cell) -> Cell:
        """Breadth-first search for the closest non-wall cell to ``target``."""
        tx, ty = target
        tx = max(0, min(self.width - 1, tx))
        ty = max(0, min(self.height - 1, ty))
        if not self.is_wall(tx, ty):
            return (tx, ty)
        seen = {(tx, ty)}
        queue: deque[Cell] = deque([(tx, ty)])
        while queue:
            x, y = queue.popleft()
            for dx, dy, _, _ in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if (nx, ny) in seen:
                    continue
                if not self.is_wall(nx, ny):
                    return (nx, ny)
                seen.add((nx, ny))
                queue.append((nx, ny))
        return (tx, ty)

    def _corners(self) -> List[Cell]:
        """Return the four walkable corner cells of the maze."""
        raw = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        ]
        corners: List[Cell] = []
        for corner in raw:
            walkable = self._nearest_walkable(corner)
            if walkable not in corners:
                corners.append(walkable)
        return corners

    def _layout(self) -> None:
        """Place the player, the ghosts, the pacgums and super-pacgums."""
        self.player_start = self._nearest_walkable(
            (self.width // 2, self.height // 2))
        corners = self._corners()
        self.ghost_starts = list(corners)
        reserved = set(corners)
        reserved.add(self.player_start)

        candidates: List[Cell] = []
        for y in range(self.height):
            for x in range(self.width):
                if self.is_wall(x, y):
                    continue
                cell = (x, y)
                if cell in corners:
                    self.pellets[cell] = SUPER_PACGUM
                elif cell not in reserved:
                    candidates.append(cell)
        for cell in self._select_pacgums(candidates):
            self.pellets[cell] = PACGUM
        self.pacgum_total = len(self.pellets)

    def _select_pacgums(self, candidates: List[Cell]) -> List[Cell]:
        """Return the corridor cells that receive a pacgum.

        Without a configured limit every corridor is filled; otherwise the
        requested number of pacgums is spread evenly over the maze so the
        level stays playable whatever the value.

        Args:
            candidates: Every corridor cell eligible for a pacgum.

        Returns:
            The subset of ``candidates`` to fill.
        """
        wanted = self.pacgum_limit
        if wanted <= 0 or wanted >= len(candidates):
            return candidates
        step = len(candidates) / float(wanted)
        return [candidates[min(len(candidates) - 1, int(i * step))]
                for i in range(wanted)]

    def eat(self, cell: Cell) -> Optional[int]:
        """Consume the pellet at ``cell`` and return its type, if any."""
        return self.pellets.pop(cell, None)

    @property
    def remaining(self) -> int:
        """Number of pellets still on the board."""
        return len(self.pellets)
