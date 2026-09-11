"""Application shell: window, main loop and screen state machine.

The :class:`App` wires everything together: it owns the window (through the
MLX-equivalent :mod:`pacman.canvas` layer), the
:class:`~pacman.game.Game` instance and the navigation between the menu,
the gameplay, the pause overlay, the highscores, the instructions and the
end-of-game name entry.
"""

from __future__ import annotations

from typing import Any, List, Optional

import pygame

from .canvas import Window
from .config import Config
from .constants import (
    BLACK,
    DOWN,
    FPS,
    GREY,
    LEFT,
    RIGHT,
    UP,
    WHITE,
    YELLOW,
)
from .game import LOST, WON, Game
from .highscore import (
    MAX_NAME_LENGTH,
    HighScores,
    is_name_char,
    sanitize_name,
)
from .render import WIN_H, WIN_W, Renderer

# Application screens.
MENU: int = 0
PLAY: int = 1
PAUSE: int = 2
HIGHSCORES: int = 3
INSTRUCTIONS: int = 4
END: int = 5

MENU_ITEMS: List[str] = [
    "Start Game", "View Highscores", "Instructions", "Exit"]
PAUSE_ITEMS: List[str] = ["Resume", "Return to Main Menu"]


class App:
    """The Pac-Man application and its top-level state machine."""

    def __init__(self, config: Config) -> None:
        """Initialise pygame, the window and the persistent state.

        Args:
            config: The validated game configuration.
        """
        self.config = config
        self.highscores = HighScores(config.highscore_filename)
        self.window = Window(WIN_W, WIN_H, "Pac-Man - Ghosts! More ghosts!")
        self.canvas = self.window.canvas
        self.renderer = Renderer(self.canvas)
        self.running = True
        self.state = MENU
        self.menu_index = 0
        self.pause_index = 0
        self.anim_time = 0.0
        self.name_buffer = ""
        self.end_won = False
        self.menu_error = ""
        self.game: Optional[Game] = None
        self._key_dirs = {
            pygame.K_UP: UP, pygame.K_w: UP,
            pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
            pygame.K_LEFT: LEFT, pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
        }

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the main loop until the player quits."""
        try:
            while self.running:
                dt = min(self.window.tick(FPS), 0.05)
                self.anim_time += dt
                self._handle_events()
                if self.state == PLAY and self.game is not None:
                    self._update_game(dt)
                self._draw()
                self.window.flush()
        finally:
            self.window.close()

    def _update_game(self, dt: float) -> None:
        """Advance the running game, surviving a maze-generator failure.

        Building the next level goes through the external A-Maze-ing
        package, so a failure there must not take the whole application
        down: the player is sent back to the main menu with a message.
        """
        if self.game is None:
            return
        try:
            self.game.update(dt)
        except RuntimeError as error:
            self._abort_to_menu(str(error))
            return
        self._check_game_end()

    def _abort_to_menu(self, message: str) -> None:
        """Drop the current game and return to the menu with an error."""
        print(f"[game] error: {message}")
        self.menu_error = message
        self.game = None
        self.menu_index = 0
        self.state = MENU

    def _check_game_end(self) -> None:
        """Move to the end screen when the game is won or lost."""
        if self.game is None:
            return
        if self.game.status in (WON, LOST):
            self.end_won = self.game.status == WON
            self.name_buffer = ""
            self.state = END

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _handle_events(self) -> None:
        """Dispatch input events to the handler for the current screen."""
        for event in self.window.poll_events():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type != pygame.KEYDOWN:
                continue
            if self.state == MENU:
                self._on_menu_key(event)
            elif self.state == PLAY:
                self._on_play_key(event)
            elif self.state == PAUSE:
                self._on_pause_key(event)
            elif self.state == END:
                self._on_end_key(event)
            elif self.state in (HIGHSCORES, INSTRUCTIONS):
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = MENU

    def _on_menu_key(self, event: Any) -> None:
        """Handle navigation on the main menu."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(MENU_ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(MENU_ITEMS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._select_menu()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _select_menu(self) -> None:
        """Apply the currently highlighted main-menu choice."""
        choice = MENU_ITEMS[self.menu_index]
        if choice == "Start Game":
            self.menu_error = ""
            try:
                self.game = Game(self.config)
            except RuntimeError as error:
                self._abort_to_menu(str(error))
                return
            self.state = PLAY
        elif choice == "View Highscores":
            self.state = HIGHSCORES
        elif choice == "Instructions":
            self.state = INSTRUCTIONS
        else:
            self.running = False

    def _on_play_key(self, event: Any) -> None:
        """Handle gameplay input, including cheats and pause."""
        if self.game is None:
            return
        if event.key == pygame.K_ESCAPE:
            self.pause_index = 0
            self.state = PAUSE
            return
        if event.key in self._key_dirs:
            self.game.player.request(self._key_dirs[event.key])
            return
        self._handle_cheat_key(event)

    def _handle_cheat_key(self, event: Any) -> None:
        """Trigger cheat actions bound to the function keys."""
        if self.game is None:
            return
        if event.key == pygame.K_F1:
            self.game.cheat_toggle_invincible()
        elif event.key == pygame.K_F2:
            self.game.cheat_toggle_freeze()
        elif event.key == pygame.K_F3:
            self.game.cheat_skip_level()
        elif event.key == pygame.K_F4:
            self.game.cheat_add_life()
        elif event.key == pygame.K_F5:
            self.game.cheat_cycle_speed()

    def _on_pause_key(self, event: Any) -> None:
        """Handle navigation on the pause overlay."""
        if event.key == pygame.K_ESCAPE:
            self.state = PLAY
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.pause_index = (self.pause_index - 1) % len(PAUSE_ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.pause_index = (self.pause_index + 1) % len(PAUSE_ITEMS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.pause_index == 0:
                self.state = PLAY
            else:
                self.game = None
                self.state = MENU

    def _on_end_key(self, event: Any) -> None:
        """Handle name entry on the game-over / victory screen."""
        if event.key == pygame.K_RETURN:
            self.highscores.add(self.name_buffer, self._final_score())
            self.game = None
            self.state = MENU
            self.menu_index = 0
        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        elif len(self.name_buffer) < MAX_NAME_LENGTH:
            char = event.unicode
            if char and is_name_char(char):
                self.name_buffer += char

    def _final_score(self) -> int:
        """Return the final score of the finished game."""
        return self.game.score if self.game is not None else 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self) -> None:
        """Render the current screen."""
        self.canvas.clear(BLACK)
        if self.state == MENU:
            self._draw_menu()
        elif self.state in (PLAY, PAUSE):
            self._draw_game()
            if self.state == PAUSE:
                self._draw_pause()
        elif self.state == HIGHSCORES:
            self._draw_highscores()
        elif self.state == INSTRUCTIONS:
            self._draw_instructions()
        elif self.state == END:
            self._draw_end()

    def _draw_menu(self) -> None:
        """Draw the main menu, options and a highscore preview."""
        self.renderer.text("PAC-MAN", 96, YELLOW, (WIN_W // 2, 120))
        self.renderer.text("Ghosts! More ghosts!", 30, GREY,
                           (WIN_W // 2, 180))
        for i, item in enumerate(MENU_ITEMS):
            color = YELLOW if i == self.menu_index else WHITE
            prefix = "> " if i == self.menu_index else "  "
            self.renderer.text(prefix + item, 40, color,
                               (WIN_W // 2, 260 + i * 50))
        if self.menu_error:
            self.renderer.text(self.menu_error[:60], 24, (222, 60, 60),
                               (WIN_W // 2, 455))
        self.renderer.text("highscores", 30, GREY, (WIN_W // 2, 500))
        top = self.highscores.entries[:5]
        if not top:
            self.renderer.text("- no scores yet -", 26, GREY,
                               (WIN_W // 2, 540))
        for i, (name, score) in enumerate(top):
            self.renderer.text(f"{i + 1}. {name} - {score} pts", 28,
                               WHITE, (WIN_W // 2, 540 + i * 34))
        self.renderer.text("Arrow keys to move, Enter to select", 24,
                           GREY, (WIN_W // 2, WIN_H - 30))

    def _draw_game(self) -> None:
        """Draw the maze, pellets, entities and HUD."""
        if self.game is None:
            return
        layout = Renderer.layout_for(self.game.maze)
        self.renderer.draw_board(self.game.maze, layout)
        self.renderer.draw_super_pacgums(self.game.maze, layout,
                                         self.anim_time)
        edible = self.game.edible_active()
        for ghost in self.game.ghosts:
            self.renderer.draw_ghost(ghost, layout, edible)
        self.renderer.draw_player(self.game, layout, self.anim_time)
        self.renderer.draw_hud(self.game)

    def _draw_pause(self) -> None:
        """Draw the pause panel and its menu on top of the game view."""
        panel_w, panel_h = 460, 300
        left = (WIN_W - panel_w) // 2
        top = (WIN_H - panel_h) // 2 - 20
        self.canvas.fill_rect(left, top, panel_w, panel_h, BLACK)
        self.canvas.rect(left, top, panel_w, panel_h, GREY, 2)
        self.renderer.text("PAUSED", 80, YELLOW, (WIN_W // 2, top + 70))
        for i, item in enumerate(PAUSE_ITEMS):
            color = YELLOW if i == self.pause_index else WHITE
            prefix = "> " if i == self.pause_index else "  "
            self.renderer.text(prefix + item, 40, color,
                               (WIN_W // 2, top + 160 + i * 56))
        self.renderer.text("Esc to resume", 24, GREY,
                           (WIN_W // 2, top + panel_h - 30))

    def _draw_highscores(self) -> None:
        """Draw the full top-ten highscore table."""
        self.renderer.text("HIGHSCORES", 70, YELLOW, (WIN_W // 2, 90))
        entries = self.highscores.entries
        if not entries:
            self.renderer.text("- no scores yet -", 32, GREY,
                               (WIN_W // 2, 240))
        for i, (name, score) in enumerate(entries):
            self.renderer.text(f"{i + 1:>2}. {name:<12} {score} pts", 34,
                               WHITE, (WIN_W // 2, 180 + i * 46))
        self.renderer.text("Esc / Enter to go back", 26, GREY,
                           (WIN_W // 2, WIN_H - 40))

    def _draw_instructions(self) -> None:
        """Draw the controls, rules and cheat-mode reference."""
        self.renderer.text("INSTRUCTIONS", 64, YELLOW, (WIN_W // 2, 70))
        lines = [
            "Move: Arrow keys or W A S D",
            "Eat every pacgum to clear the level.",
            "Super-pacgums (corners) make ghosts edible: eat them!",
            "A ghost touch costs a life. You start with several.",
            "Pause: Esc        Quit from menu: Esc",
            "",
            "Cheat mode (for review):",
            "F1 - Invincibility      F2 - Freeze ghosts",
            "F3 - Skip level         F4 - Add a life",
            "F5 - Cycle player speed",
        ]
        for i, line in enumerate(lines):
            self.renderer.text_left(line, 30, WHITE,
                                    (80, 160 + i * 42))
        self.renderer.text("Esc / Enter to go back", 26, GREY,
                           (WIN_W // 2, WIN_H - 40))

    def _draw_end(self) -> None:
        """Draw the victory / game-over screen with the name prompt."""
        title = "YOU WIN!" if self.end_won else "GAME OVER"
        color = YELLOW if self.end_won else (222, 60, 60)
        self.renderer.text(title, 90, color, (WIN_W // 2, 150))
        if self.end_won:
            self.renderer.text("Congratulations, all levels cleared!",
                               30, WHITE, (WIN_W // 2, 230))
        self.renderer.text(f"Final score: {self._final_score()}", 44,
                           WHITE, (WIN_W // 2, 300))
        rank = self._rank_text()
        if rank:
            self.renderer.text(rank, 28, GREY, (WIN_W // 2, 350))
        self.renderer.text("Enter your name:", 34, WHITE,
                           (WIN_W // 2, 430))
        shown = sanitize_name(self.name_buffer) if self.name_buffer else ""
        caret = "_" if int(self.anim_time * 2) % 2 == 0 else " "
        self.renderer.text(shown + caret, 48, YELLOW, (WIN_W // 2, 480))
        self.renderer.text("Press Enter to save and return to menu", 26,
                           GREY, (WIN_W // 2, WIN_H - 60))

    def _rank_text(self) -> str:
        """Return a short message about the score's highscore standing."""
        if self.highscores.qualifies(self._final_score()):
            return "New highscore!"
        return ""
