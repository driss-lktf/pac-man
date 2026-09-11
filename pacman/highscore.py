"""Persistent highscore system.

Highscores are stored as a JSON list of ``{"name": str, "score": int}``
entries, sorted by descending score and capped to the top ten.  All file
operations are defensive: a missing or corrupted file simply yields an
empty highscore table instead of crashing the game.
"""

from __future__ import annotations

import json
import string
from typing import List, Tuple

MAX_ENTRIES: int = 10
MAX_NAME_LENGTH: int = 10

# The subject allows alphanumeric characters and spaces only. ``str.isalnum``
# is Unicode-aware and would also accept accented letters, so the allowed set
# is spelled out explicitly to stay strictly ASCII.
NAME_CHARS: frozenset[str] = frozenset(
    string.ascii_letters + string.digits + " ")


def is_name_char(char: str) -> bool:
    """Return whether ``char`` may appear in a player name."""
    return char in NAME_CHARS


def sanitize_name(name: str) -> str:
    """Return a valid player name.

    Names are limited to ASCII alphanumeric characters and spaces, trimmed
    and capped at :data:`MAX_NAME_LENGTH` characters.  An empty result falls
    back to ``"PLAYER"``.

    Args:
        name: The raw name entered by the player.

    Returns:
        A sanitized, non-empty player name.
    """
    cleaned = "".join(c for c in name if is_name_char(c))
    cleaned = cleaned.strip()[:MAX_NAME_LENGTH].strip()
    return cleaned if cleaned else "PLAYER"


class HighScores:
    """Manage the persistent top-ten highscore table."""

    def __init__(self, filename: str) -> None:
        """Create the manager and load existing scores from disk.

        Args:
            filename: Path of the JSON file used for persistence.
        """
        self._filename = filename
        self._entries: List[Tuple[str, int]] = []
        self.load()

    @property
    def entries(self) -> List[Tuple[str, int]]:
        """The current highscores as ``(name, score)`` tuples."""
        return list(self._entries)

    def load(self) -> None:
        """Load highscores from disk, tolerating any file error."""
        self._entries = []
        try:
            with open(self._filename, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            score = item.get("score")
            if not isinstance(name, str):
                continue
            if isinstance(score, bool) or not isinstance(score, int):
                continue
            if score < 0:
                continue
            self._entries.append((sanitize_name(name), score))
        self._sort_and_trim()

    def save(self) -> None:
        """Persist highscores to disk, tolerating any file error."""
        payload = [
            {"name": name, "score": score}
            for name, score in self._entries
        ]
        try:
            with open(self._filename, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except OSError as error:
            print(f"[highscore] warning: cannot save scores: {error}")

    def qualifies(self, score: int) -> bool:
        """Return whether ``score`` would enter the top ten."""
        if score < 0:
            return False
        if len(self._entries) < MAX_ENTRIES:
            return True
        return score > self._entries[-1][1]

    def add(self, name: str, score: int) -> None:
        """Add a score, keep the top ten and persist the table.

        Args:
            name: The player name (it will be sanitized).
            score: A non-negative score (negatives are coerced to zero).
        """
        safe_score = max(0, int(score))
        self._entries.append((sanitize_name(name), safe_score))
        self._sort_and_trim()
        self.save()

    def _sort_and_trim(self) -> None:
        """Sort by descending score and keep the top entries only."""
        self._entries.sort(key=lambda entry: entry[1], reverse=True)
        self._entries = self._entries[:MAX_ENTRIES]
