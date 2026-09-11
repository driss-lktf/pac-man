"""Game entities: the player and the ghosts.

Entities move smoothly from cell to cell.  Each entity stores its current
cell plus an interpolation ``progress`` towards the next cell, which keeps
movement aligned with the corridors while still looking fluid on screen.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .constants import DIRECTIONS, Direction
from .maze import Cell, Maze

# Ghost states.
NORMAL: int = 0
EDIBLE: int = 1
EATEN: int = 2


def _opposite(direction: Optional[Direction]) -> Optional[Direction]:
    """Return the direction facing the opposite way, if any."""
    if direction is None:
        return None
    dx, dy, _, _ = direction
    for candidate in DIRECTIONS:
        if candidate[0] == -dx and candidate[1] == -dy:
            return candidate
    return None


class Entity:
    """Base class handling smooth cell-to-cell motion."""

    def __init__(self, tile: Cell, speed: float) -> None:
        """Initialise the entity at ``tile`` with ``speed`` cells/second."""
        self.start_tile: Cell = tile
        self.tile: Cell = tile
        self.speed: float = speed
        self.direction: Optional[Direction] = None
        self.next_tile: Optional[Cell] = None
        self.progress: float = 0.0

    def reset(self) -> None:
        """Snap the entity back to its spawn cell and stop it."""
        self.tile = self.start_tile
        self.direction = None
        self.next_tile = None
        self.progress = 0.0

    def pixel_pos(self, cell_px: float,
                  origin: Tuple[float, float]) -> Tuple[float, float]:
        """Return the on-screen centre of the entity in pixels.

        Args:
            cell_px: Side length of one cell, in pixels.
            origin: Top-left pixel position of the maze drawing area.
        """
        ox, oy = origin
        cx = ox + self.tile[0] * cell_px + cell_px / 2
        cy = oy + self.tile[1] * cell_px + cell_px / 2
        if self.next_tile is not None:
            nx = ox + self.next_tile[0] * cell_px + cell_px / 2
            ny = oy + self.next_tile[1] * cell_px + cell_px / 2
            cx += (nx - cx) * self.progress
            cy += (ny - cy) * self.progress
        return cx, cy

    def fpos(self) -> Tuple[float, float]:
        """Return the entity position in fractional cell coordinates."""
        x, y = float(self.tile[0]), float(self.tile[1])
        if self.next_tile is not None:
            x += (self.next_tile[0] - x) * self.progress
            y += (self.next_tile[1] - y) * self.progress
        return x, y

    def _pick_next(self, maze: Maze) -> None:
        """Choose the next cell to move to (overridden by subclasses)."""
        self.next_tile = None

    def advance(self, dt: float, maze: Maze) -> None:
        """Advance motion by ``dt`` seconds along the corridors."""
        if self.next_tile is None:
            self._pick_next(maze)
            if self.next_tile is None:
                return
        self.progress += self.speed * dt
        while self.progress >= 1.0:
            self.progress -= 1.0
            if self.next_tile is not None:
                self.tile = self.next_tile
            self.next_tile = None
            self._pick_next(maze)
            if self.next_tile is None:
                self.progress = 0.0
                break


class Player(Entity):
    """The player-controlled Pac-Man."""

    def __init__(self, tile: Cell, speed: float) -> None:
        """Create the player at ``tile`` with the given speed."""
        super().__init__(tile, speed)
        self.desired: Optional[Direction] = None

    def reset(self) -> None:
        """Reset the player and clear any buffered input."""
        super().reset()
        self.desired = None

    def request(self, direction: Direction) -> None:
        """Buffer a turn request to be applied at the next cell."""
        self.desired = direction

    def _pick_next(self, maze: Maze) -> None:
        """Apply the buffered turn, else keep going straight, else stop."""
        x, y = self.tile
        for direction in (self.desired, self.direction):
            if direction is None:
                continue
            if maze.can_move(x, y, direction):
                self.direction = direction
                self.next_tile = (x + direction[0], y + direction[1])
                return
        self.next_tile = None


class Ghost(Entity):
    """An autonomous ghost with a simple personality-based AI."""

    def __init__(self, tile: Cell, speed: float, personality: int,
                 color: Tuple[int, int, int]) -> None:
        """Create a ghost.

        Args:
            tile: Spawn (corner) cell.
            speed: Base speed in cells per second.
            personality: 0=chaser, 1=ambusher, 2=erratic, 3=shy.
            color: RGB colour used by the renderer.
        """
        super().__init__(tile, speed)
        self.personality = personality
        self.color = color
        self.base_speed = speed
        self.state: int = NORMAL
        self.respawn_timer: float = 0.0
        self.frozen: bool = False

    def reset(self) -> None:
        """Reset the ghost to its corner and to its normal state."""
        super().reset()
        self.state = NORMAL
        self.respawn_timer = 0.0

    def make_edible(self) -> None:
        """Turn the ghost edible (ignored if it is currently eaten)."""
        if self.state != EATEN:
            self.state = EDIBLE
            self.speed = self.base_speed * 0.6

    def make_normal(self) -> None:
        """Return the ghost to its normal, chasing state."""
        if self.state == EDIBLE:
            self.state = NORMAL
            self.speed = self.base_speed

    def get_eaten(self, respawn_time: float) -> None:
        """Send the ghost home as 'eyes' for ``respawn_time`` seconds."""
        self.state = EATEN
        self.respawn_timer = respawn_time
        self.tile = self.start_tile
        self.next_tile = None
        self.progress = 0.0
        self.speed = self.base_speed

    # Player state cached every frame so that ``_decide`` (called from
    # within ``advance``) stays cheap and needs no extra arguments.
    _player_tile: Cell = (0, 0)
    _player_dir: Optional[Direction] = None
    _blinky_tile: Cell = (0, 0)

    def set_ai_target(self, player: "Player", blinky_tile: Cell) -> None:
        """Cache the player's state for the next motion step."""
        self._player_tile = player.tile
        self._player_dir = player.direction
        self._blinky_tile = blinky_tile

    def _chase_target(self) -> Cell:
        """Compute the cell this ghost is heading towards while chasing."""
        px, py = self._player_tile
        if self.personality == 0:
            return (px, py)
        if self.personality == 1:
            if self._player_dir is not None:
                dx, dy, _, _ = self._player_dir
                return (px + 4 * dx, py + 4 * dy)
            return (px, py)
        if self.personality == 2:
            bx, by = self._blinky_tile
            return (2 * px - bx, 2 * py - by)
        # Shy ghost: chase when far, retreat to its corner when close.
        if abs(px - self.tile[0]) + abs(py - self.tile[1]) > 6:
            return (px, py)
        return self.start_tile

    def update(self, dt: float, maze: Maze, player: "Player",
               blinky_tile: Cell) -> None:
        """Update the ghost AI and motion for one frame."""
        if self.state == EATEN:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.state = NORMAL
                self.speed = self.base_speed
            return
        if self.frozen:
            return
        self.advance(dt, maze)

    def _pick_next(self, maze: Maze) -> None:
        """Pick the next cell using the cached AI decision."""
        choice = self._decide(maze)
        if choice is None:
            self.next_tile = None
            return
        self.direction = choice
        x, y = self.tile
        self.next_tile = (x + choice[0], y + choice[1])

    def _decide(self, maze: Maze) -> Optional[Direction]:
        """Choose a legal direction towards (or away from) the target."""
        x, y = self.tile
        options: List[Direction] = [
            d for d in DIRECTIONS if maze.can_move(x, y, d)
        ]
        if not options:
            return None
        reverse = _opposite(self.direction)
        forward = [d for d in options if d != reverse]
        if forward:
            options = forward
        # While edible, flee: maximize distance to the player. Otherwise
        # chase: minimize distance to the personality target.
        flee = self.state == EDIBLE
        target = self._player_tile if flee else self._chase_target()
        best: Optional[Direction] = None
        best_score = -1e18
        for direction in options:
            nx, ny = x + direction[0], y + direction[1]
            dist = float((nx - target[0]) ** 2 + (ny - target[1]) ** 2)
            score = dist if flee else -dist
            score += random.uniform(0.0, 0.4)
            if score > best_score:
                best_score = score
                best = direction
        return best
