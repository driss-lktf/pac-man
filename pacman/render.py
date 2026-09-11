"""Drawing of the in-game view and the HUD.

Every pixel is produced through :mod:`pacman.canvas`, our MLX-equivalent
layer: only ``put_pixel``-level primitives, image copies and string drawing
are used, so no graphical function without an MLX counterpart is relied upon.

The static part of a level (walls plus the pacgums still on the board) is
rasterised once into an off-screen image and copied to the window every
frame -- the classic MLX "build an image, then ``mlx_image_to_window``"
workflow.  Only the animated elements (Pac-Man, ghosts, pulsing
super-pacgums, HUD) are redrawn each frame.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional, Set, Tuple

from .canvas import Canvas
from .constants import (
    BLACK,
    EDIBLE_BLUE,
    EYE_WHITE,
    GREY,
    HUD_HEIGHT,
    PELLET,
    PLAY_AREA,
    SIDE_MARGIN,
    SUPER_PACGUM,
    WALL_ALL,
    WALL_BLUE,
    WALL_E,
    WALL_FILL,
    WALL_N,
    WALL_S,
    WALL_W,
    WHITE,
    YELLOW,
)
from .game import Game
from .maze import Cell, Maze

WIN_W: int = PLAY_AREA + 2 * SIDE_MARGIN
WIN_H: int = PLAY_AREA + 2 * SIDE_MARGIN + HUD_HEIGHT

Layout = Tuple[float, Tuple[float, float]]


class Renderer:
    """Draws the maze, the entities and the heads-up display."""

    def __init__(self, canvas: Canvas) -> None:
        """Store the window image and prepare the level-image cache."""
        self.canvas = canvas
        self._board: Optional[Canvas] = None
        self._board_key: Tuple[int, int] = (0, 0)
        self._painted: Set[Cell] = set()

    # ------------------------------------------------------------------
    # Text helpers (``mlx_put_string``)
    # ------------------------------------------------------------------
    def text(self, value: str, size: int,
             color: Tuple[int, int, int], center: Tuple[int, int]) -> None:
        """Draw centred text at ``center``."""
        self.canvas.put_string_centered(value, center[0], center[1],
                                        color, size)

    def text_left(self, value: str, size: int,
                  color: Tuple[int, int, int],
                  topleft: Tuple[int, int]) -> None:
        """Draw left-aligned text at ``topleft``."""
        self.canvas.put_string(value, topleft[0], topleft[1], color, size)

    @staticmethod
    def layout_for(maze: Maze) -> Layout:
        """Compute the cell size and origin centring ``maze`` in the view."""
        cell = PLAY_AREA / max(maze.width, maze.height)
        maze_w = maze.width * cell
        maze_h = maze.height * cell
        origin = (
            SIDE_MARGIN + (PLAY_AREA - maze_w) / 2.0,
            SIDE_MARGIN + (PLAY_AREA - maze_h) / 2.0,
        )
        return cell, origin

    # ------------------------------------------------------------------
    # Level image: walls + remaining pacgums
    # ------------------------------------------------------------------
    def draw_board(self, maze: Maze, layout: Layout) -> None:
        """Copy the level image to the window, refreshing it if needed."""
        cell, _ = layout
        key = (id(maze), int(cell * 100))
        if self._board is None or key != self._board_key:
            self._board_key = key
            self._board = Canvas.new_image(WIN_W, WIN_H)
            self._board.clear(BLACK)
            self._draw_walls(self._board, maze, layout)
            self._painted = set()
            for cellpos, kind in maze.pellets.items():
                if kind != SUPER_PACGUM:
                    self._paint_pacgum(self._board, cellpos, layout)
                    self._painted.add(cellpos)
        else:
            eaten = self._painted.difference(maze.pellets)
            for cellpos in eaten:
                self._erase_cell(self._board, cellpos, layout)
            self._painted -= eaten
        self.canvas.put_image(self._board, 0, 0)

    def _draw_walls(self, image: Canvas, maze: Maze, layout: Layout) -> None:
        """Rasterise every wall of ``maze`` into ``image``."""
        cell, (ox, oy) = layout
        thickness = max(2, int(cell // 9))
        for y in range(maze.height):
            for x in range(maze.width):
                code = maze.grid[y][x]
                px = int(ox + x * cell)
                py = int(oy + y * cell)
                size = max(1, int(cell) - 1)
                if code == WALL_ALL:
                    image.rounded_rect(px + 1, py + 1, size, size, 4,
                                       WALL_BLUE)
                    image.rounded_rect(px + 3, py + 3, size - 4, size - 4, 3,
                                       WALL_FILL)
                    continue
                self._draw_cell_walls(image, code, px, py, cell, thickness)

    @staticmethod
    def _draw_cell_walls(image: Canvas, code: int, px: int, py: int,
                         cell: float, thickness: int) -> None:
        """Draw the wall segments present on a single corridor cell."""
        length = int(cell) + 1
        bottom = int(py + cell)
        right = int(px + cell)
        if code & WALL_N:
            image.hline(px, py, length, WALL_BLUE, thickness)
        if code & WALL_S:
            image.hline(px, bottom, length, WALL_BLUE, thickness)
        if code & WALL_W:
            image.vline(px, py, length, WALL_BLUE, thickness)
        if code & WALL_E:
            image.vline(right, py, length, WALL_BLUE, thickness)

    @staticmethod
    def _cell_center(cellpos: Cell, layout: Layout) -> Tuple[int, int]:
        """Return the pixel centre of a maze cell."""
        cell, (ox, oy) = layout
        return (int(ox + cellpos[0] * cell + cell / 2),
                int(oy + cellpos[1] * cell + cell / 2))

    @staticmethod
    def _pacgum_radius(layout: Layout) -> int:
        """Return the pacgum radius in pixels for this layout."""
        cell, _ = layout
        return max(2, int(cell * 0.09))

    @staticmethod
    def _paint_pacgum(image: Canvas, cellpos: Cell, layout: Layout) -> None:
        """Draw one small pacgum on the level image."""
        cx, cy = Renderer._cell_center(cellpos, layout)
        image.disc(cx, cy, Renderer._pacgum_radius(layout), PELLET)

    @staticmethod
    def _erase_cell(image: Canvas, cellpos: Cell, layout: Layout) -> None:
        """Clear the centre of a cell after its pacgum has been eaten."""
        cx, cy = Renderer._cell_center(cellpos, layout)
        half = Renderer._pacgum_radius(layout) + 1
        image.fill_rect(cx - half, cy - half, 2 * half + 1, 2 * half + 1,
                        BLACK)

    def draw_super_pacgums(self, maze: Maze, layout: Layout,
                           clock: float) -> None:
        """Draw the pulsing super-pacgums (they are animated every frame)."""
        cell, _ = layout
        pulse = 0.5 + 0.5 * math.sin(clock * 6.0)
        radius = int(cell * (0.18 + 0.06 * pulse))
        for cellpos, kind in maze.pellets.items():
            if kind != SUPER_PACGUM:
                continue
            cx, cy = self._cell_center(cellpos, layout)
            self.canvas.disc(cx, cy, radius, WHITE)

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------
    def draw_player(self, game: Game, layout: Layout, clock: float) -> None:
        """Draw Pac-Man with an animated mouth facing his direction."""
        cell, origin = layout
        cx, cy = game.player.pixel_pos(cell, origin)
        radius = cell * 0.42
        angle = math.radians(45.0) * (0.5 + 0.5 * abs(math.sin(clock * 8.0)))
        facing = 0.0
        if game.player.direction is not None:
            dx, dy, _, _ = game.player.direction
            facing = math.atan2(dy, dx)
        points: List[Tuple[float, float]] = [(cx, cy)]
        start = facing + angle
        end = facing - angle + 2 * math.pi
        steps = 24
        for i in range(steps + 1):
            theta = start + (end - start) * i / steps
            points.append((cx + math.cos(theta) * radius,
                           cy + math.sin(theta) * radius))
        self.canvas.polygon(points, YELLOW)

    def draw_ghost(self, ghost: Any, layout: Layout, edible: bool) -> None:
        """Draw a ghost in its normal, edible or eaten appearance."""
        _normal, edible_state, eaten = Game.state_names()
        cell, origin = layout
        fx, fy = ghost.pixel_pos(cell, origin)
        cx, cy = int(fx), int(fy)
        radius = int(cell * 0.42)
        if ghost.state == eaten:
            self._draw_eyes(cx, cy, radius, ghost.direction)
            return
        color = EDIBLE_BLUE if ghost.state == edible_state else ghost.color
        self.canvas.ellipse(cx, cy, radius, radius, color)
        self.canvas.fill_rect(cx - radius, cy, 2 * radius + 1, radius, color)
        self._draw_skirt(cx, cy, radius, color)
        if ghost.state == edible_state:
            self._draw_scared_face(cx, cy, radius)
        else:
            self._draw_eyes(cx, cy, radius, ghost.direction)

    def _draw_skirt(self, cx: int, cy: int, radius: int,
                    color: Tuple[int, int, int]) -> None:
        """Draw the three rounded bumps at the bottom of a ghost."""
        bump = max(1, (2 * radius) // 6)
        for i in (-1, 0, 1):
            self.canvas.ellipse(cx + i * 2 * bump, cy + radius, bump, bump,
                                color)

    def _draw_eyes(self, cx: int, cy: int, radius: int,
                   direction: Any) -> None:
        """Draw two eyes whose pupils look towards ``direction``."""
        look_x, look_y = 0, 0
        if direction is not None:
            look_x = int(direction[0] * radius * 0.18)
            look_y = int(direction[1] * radius * 0.18)
        for sign in (-1, 1):
            ex = cx + int(sign * radius * 0.35)
            ey = cy - int(radius * 0.15)
            self.canvas.disc(ex, ey, max(1, int(radius * 0.26)), EYE_WHITE)
            self.canvas.disc(ex + look_x, ey + look_y,
                             max(1, int(radius * 0.13)), BLACK)

    def _draw_scared_face(self, cx: int, cy: int, radius: int) -> None:
        """Draw the simple face shown while a ghost is edible."""
        for sign in (-1, 1):
            ex = cx + int(sign * radius * 0.32)
            ey = cy - int(radius * 0.1)
            self.canvas.disc(ex, ey, max(2, int(radius * 0.1)), WHITE)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------
    def draw_hud(self, game: Game) -> None:
        """Draw the bottom HUD bar: score, lives, level, time, cheats."""
        top = WIN_H - HUD_HEIGHT
        self.canvas.fill_rect(0, top, WIN_W, HUD_HEIGHT, BLACK)
        self.canvas.hline(0, top, WIN_W, GREY, 1)
        mid = WIN_H - HUD_HEIGHT // 2
        self.text_left(f"Score: {game.score}", 26, WHITE,
                       (SIDE_MARGIN, mid - 10))
        self.text(f"Lives: {game.lives}", 26, YELLOW, (WIN_W // 2 - 90, mid))
        self.text(f"Level: {game.level_index + 1}/{game.level_count}",
                  26, WHITE, (WIN_W // 2 + 60, mid))
        seconds = max(0, int(math.ceil(game.time_left)))
        color = (222, 60, 60) if seconds <= 10 else WHITE
        self.canvas.put_string_right(f"Time: {seconds}",
                                     WIN_W - SIDE_MARGIN, mid, color, 26)
        cheats = game.active_cheats()
        if cheats:
            self.text_left(" ".join(cheats), 20, (255, 120, 120),
                           (SIDE_MARGIN, mid + 8))
        if game.flash_timer > 0.0 and game.flash_message:
            self.text(game.flash_message, 40, YELLOW,
                      (WIN_W // 2, SIDE_MARGIN + 18))
