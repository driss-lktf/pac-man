"""Core game logic for a single play session.

The :class:`Game` owns the current level, the player, the ghosts and all
the rules: scoring, lives, the per-level timer, the power-pellet (edible)
mechanic and the cheat menu used during peer review.
"""

from __future__ import annotations

from typing import List, Tuple

from .config import Config
from .constants import GHOST_COLORS, SUPER_PACGUM
from .entities import EATEN, EDIBLE, NORMAL, Ghost, Player
from .maze import Maze

# Game status values.
PLAYING: int = 0
WON: int = 1
LOST: int = 2

COLLISION_DISTANCE: float = 0.5


class Game:
    """Holds and updates the whole state of one play session."""

    def __init__(self, config: Config) -> None:
        """Start a new game from level 0 using ``config``."""
        self.config = config
        self.score: int = 0
        self.lives: int = config.lives
        self.level_index: int = 0
        self.status: int = PLAYING
        self.edible_timer: float = 0.0
        self.time_left: float = float(config.level_max_time)
        self.player_speed_mult: float = 1.0
        # Cheat flags.
        self.cheat_invincible: bool = False
        self.cheat_ghost_freeze: bool = False
        self.flash_message: str = ""
        self.flash_timer: float = 0.0
        self.maze: Maze
        self.player: Player
        self.ghosts: List[Ghost] = []
        self._load_level(self.level_index)

    @property
    def level_count(self) -> int:
        """Total number of levels in this game."""
        return len(self.config.levels)

    def _level_seed(self, index: int) -> int:
        """First level uses the fixed seed, the rest are random."""
        return self.config.seed if index == 0 else 0

    def _load_level(self, index: int) -> None:
        """Build the maze and (re)spawn every entity for ``index``."""
        width, height = self.config.levels[index]
        self.maze = Maze(width, height, self._level_seed(index),
                         self.config.pacgum)
        self.time_left = float(self.config.level_max_time)
        self.edible_timer = 0.0
        self.player = Player(
            self.maze.player_start,
            self.config.player_speed * self.player_speed_mult,
        )
        self.ghosts = []
        for i, corner in enumerate(self.maze.ghost_starts):
            ghost = Ghost(
                corner,
                self.config.ghost_speed,
                personality=i % 4,
                color=GHOST_COLORS[i % len(GHOST_COLORS)],
            )
            ghost.frozen = self.cheat_ghost_freeze
            self.ghosts.append(ghost)

    def _reset_positions(self) -> None:
        """Send the player and ghosts back to their spawn cells."""
        self.player.reset()
        self.player.speed = self.config.player_speed * self.player_speed_mult
        self.edible_timer = 0.0
        for ghost in self.ghosts:
            ghost.reset()
            ghost.frozen = self.cheat_ghost_freeze

    def _flash(self, message: str, duration: float = 1.5) -> None:
        """Show a short on-screen status message."""
        self.flash_message = message
        self.flash_timer = duration

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Advance the whole game by ``dt`` seconds."""
        if self.status != PLAYING:
            return
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

        self._update_timer(dt)
        if self.status != PLAYING:
            return

        self.player.advance(dt, self.maze)
        self._eat_pellets()

        blinky_tile = self.ghosts[0].tile if self.ghosts else (0, 0)
        for ghost in self.ghosts:
            ghost.set_ai_target(self.player, blinky_tile)
            ghost.update(dt, self.maze, self.player, blinky_tile)

        self._update_edible(dt)
        self._handle_collisions()
        self._check_level_clear()

    def _update_timer(self, dt: float) -> None:
        """Count the level timer down; a timeout costs one life."""
        self.time_left -= dt
        if self.time_left <= 0.0:
            self._flash("Time up!")
            self._lose_life()
            self.time_left = float(self.config.level_max_time)

    def _eat_pellets(self) -> None:
        """Eat the pellet under the player, if any, and score it."""
        kind = self.maze.eat(self.player.tile)
        if kind is None:
            return
        if kind == SUPER_PACGUM:
            self.score += self.config.points_per_super_pacgum
            self.edible_timer = self.config.edible_duration
            for ghost in self.ghosts:
                ghost.make_edible()
        else:
            self.score += self.config.points_per_pacgum

    def _update_edible(self, dt: float) -> None:
        """Tick the power-pellet timer and end the edible window."""
        if self.edible_timer <= 0.0:
            return
        self.edible_timer -= dt
        if self.edible_timer <= 0.0:
            self.edible_timer = 0.0
            for ghost in self.ghosts:
                ghost.make_normal()

    def _handle_collisions(self) -> None:
        """Resolve every player/ghost overlap for this frame."""
        px, py = self.player.fpos()
        for ghost in self.ghosts:
            if ghost.state == EATEN:
                continue
            gx, gy = ghost.fpos()
            if (px - gx) ** 2 + (py - gy) ** 2 > COLLISION_DISTANCE ** 2:
                continue
            if ghost.state == EDIBLE:
                self.score += self.config.points_per_ghost
                ghost.get_eaten(self.config.ghost_respawn_time)
            elif not self.cheat_invincible:
                self._lose_life()
                return

    def _lose_life(self) -> None:
        """Remove one life and either respawn or end the game."""
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.status = LOST
            return
        self._reset_positions()

    def _check_level_clear(self) -> None:
        """Move to the next level (or win) once the board is empty."""
        if self.maze.remaining > 0:
            return
        if self.level_index + 1 >= self.level_count:
            self.status = WON
            return
        self.level_index += 1
        self._flash(f"Level {self.level_index + 1}!")
        self._load_level(self.level_index)

    # ------------------------------------------------------------------
    # Cheat menu (for peer review)
    # ------------------------------------------------------------------
    def cheat_toggle_invincible(self) -> None:
        """Toggle invincibility (ghosts can no longer kill the player)."""
        self.cheat_invincible = not self.cheat_invincible
        state = "ON" if self.cheat_invincible else "OFF"
        self._flash(f"Invincible: {state}")

    def cheat_toggle_freeze(self) -> None:
        """Toggle ghost freeze (ghosts stop moving)."""
        self.cheat_ghost_freeze = not self.cheat_ghost_freeze
        for ghost in self.ghosts:
            ghost.frozen = self.cheat_ghost_freeze
        state = "ON" if self.cheat_ghost_freeze else "OFF"
        self._flash(f"Ghost freeze: {state}")

    def cheat_skip_level(self) -> None:
        """Immediately clear the current level."""
        self.maze.pellets.clear()
        self._flash("Level skipped")
        self._check_level_clear()

    def cheat_add_life(self) -> None:
        """Grant one extra life."""
        self.lives += 1
        self._flash(f"Lives: {self.lives}")

    def cheat_cycle_speed(self) -> None:
        """Cycle the player speed multiplier between 1x, 1.5x and 2x."""
        steps = [1.0, 1.5, 2.0]
        index = (steps.index(self.player_speed_mult) + 1) % len(steps) \
            if self.player_speed_mult in steps else 0
        self.player_speed_mult = steps[index]
        self.player.speed = self.config.player_speed * self.player_speed_mult
        self._flash(f"Speed: x{self.player_speed_mult:g}")

    def active_cheats(self) -> List[str]:
        """Return short labels for every currently active cheat."""
        labels: List[str] = []
        if self.cheat_invincible:
            labels.append("INVINCIBLE")
        if self.cheat_ghost_freeze:
            labels.append("FREEZE")
        if self.player_speed_mult != 1.0:
            labels.append(f"SPEED x{self.player_speed_mult:g}")
        return labels

    def edible_active(self) -> bool:
        """Return whether ghosts are currently edible."""
        return self.edible_timer > 0.0

    def ghost_status(self) -> List[Tuple[int, float]]:
        """Return ``(state, edible_ratio)`` for each ghost (for the HUD)."""
        out: List[Tuple[int, float]] = []
        duration = max(self.config.edible_duration, 0.001)
        ratio = self.edible_timer / duration
        for ghost in self.ghosts:
            out.append((ghost.state, ratio if ghost.state == EDIBLE else 0.0))
        return out

    @staticmethod
    def state_names() -> Tuple[int, int, int]:
        """Expose ghost state constants (NORMAL, EDIBLE, EATEN)."""
        return NORMAL, EDIBLE, EATEN
