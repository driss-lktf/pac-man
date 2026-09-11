"""Shared constants for the Pac-Man game.

This module gathers the wall-encoding bits used by the assigned
``mazegenerator`` package, the movement directions and the colour
palette used by the renderer.
"""

from __future__ import annotations

from typing import Tuple

# --- Wall encoding (as produced by the MazeGenerator package) ----------
# Each maze cell is an int whose 4 low bits describe its walls.
WALL_N: int = 1   # north wall (blocks movement to the cell above)
WALL_E: int = 2   # east wall  (blocks movement to the cell on the right)
WALL_S: int = 4   # south wall (blocks movement to the cell below)
WALL_W: int = 8   # west wall  (blocks movement to the cell on the left)
WALL_ALL: int = 15  # a solid block: the '42' pattern inserted by the lib

# --- Directions --------------------------------------------------------
# (dx, dy, wall-bit-of-this-cell, wall-bit-of-the-neighbour)
Direction = Tuple[int, int, int, int]
UP: Direction = (0, -1, WALL_N, WALL_S)
DOWN: Direction = (0, 1, WALL_S, WALL_N)
LEFT: Direction = (-1, 0, WALL_W, WALL_E)
RIGHT: Direction = (1, 0, WALL_E, WALL_W)
DIRECTIONS: list[Direction] = [UP, DOWN, LEFT, RIGHT]

# --- Cell content (pellet layer) --------------------------------------
EMPTY: int = 0
PACGUM: int = 1
SUPER_PACGUM: int = 2

# --- Colours (R, G, B) -------------------------------------------------
BLACK: Tuple[int, int, int] = (0, 0, 0)
WHITE: Tuple[int, int, int] = (255, 255, 255)
GREY: Tuple[int, int, int] = (140, 140, 150)
DARK_GREY: Tuple[int, int, int] = (40, 40, 48)
YELLOW: Tuple[int, int, int] = (255, 221, 0)
GOLD: Tuple[int, int, int] = (255, 184, 51)
WALL_BLUE: Tuple[int, int, int] = (33, 33, 222)
WALL_FILL: Tuple[int, int, int] = (62, 84, 222)
PELLET: Tuple[int, int, int] = (255, 235, 190)
RED: Tuple[int, int, int] = (222, 0, 0)
PINK: Tuple[int, int, int] = (255, 153, 204)
CYAN: Tuple[int, int, int] = (0, 222, 222)
ORANGE: Tuple[int, int, int] = (255, 153, 51)
EDIBLE_BLUE: Tuple[int, int, int] = (40, 40, 222)
EYE_WHITE: Tuple[int, int, int] = (240, 240, 255)
GREEN: Tuple[int, int, int] = (0, 222, 102)

GHOST_COLORS: list[Tuple[int, int, int]] = [RED, PINK, CYAN, ORANGE]

# Window / layout
FPS: int = 60
PLAY_AREA: int = 720       # target size (px) of the maze drawing area
HUD_HEIGHT: int = 56       # height (px) of the bottom HUD bar
SIDE_MARGIN: int = 24      # outer margin around the maze (px)
