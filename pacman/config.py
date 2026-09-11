"""Configuration loading and validation.

The configuration file is JSON extended with comments: lines (or trailing
parts of lines) starting with ``#`` or ``//`` are ignored, and ``/* ... */``
blocks are also supported.

Every value is validated and clamped to a safe default when it is missing
or invalid, so the game never crashes because of a faulty configuration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, List, Tuple

# Hard safety bounds for maze dimensions (cells).
MIN_DIM: int = 15
MAX_DIM: int = 41
# The game must always offer at least this many levels.
MIN_LEVELS: int = 10


def strip_json_comments(text: str) -> str:
    """Remove ``#``, ``//`` and ``/* */`` comments from a JSON string.

    Comment markers located inside JSON string literals are preserved.

    Args:
        text: The raw file content.

    Returns:
        The same content with all comments removed.
    """
    out: List[str] = []
    i = 0
    n = len(text)
    in_string = False
    escape = False
    while i < n:
        char = text[i]
        if in_string:
            out.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue
        if char == "#" or (char == "/" and i + 1 < n and text[i + 1] == "/"):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if char == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(char)
        i += 1
    return "".join(out)


@dataclass
class Config:
    """Validated game configuration.

    Attributes:
        highscore_filename: Path of the JSON file storing highscores.
        lives: Number of lives the player starts with.
        seed: Seed used to generate the very first level.
        level_max_time: Time limit per level, in seconds.
        points_per_pacgum: Score gained when eating a pacgum.
        points_per_super_pacgum: Score gained when eating a super-pacgum.
        points_per_ghost: Score gained when eating an edible ghost.
        edible_duration: Duration ghosts stay edible, in seconds.
        ghost_respawn_time: Delay before an eaten ghost comes back.
        player_speed: Player speed, in cells per second.
        ghost_speed: Ghost speed, in cells per second.
        pacgum: Number of pacgums per level (0 fills every corridor).
        levels: List of (width, height) maze sizes, one per level.
    """

    highscore_filename: str = "highscores.json"
    lives: int = 3
    seed: int = 42
    level_max_time: int = 90
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    edible_duration: float = 7.0
    ghost_respawn_time: float = 5.0
    player_speed: float = 6.0
    ghost_speed: float = 5.0
    pacgum: int = 0
    levels: List[Tuple[int, int]] = field(default_factory=list)


def _warn(message: str) -> None:
    """Print a clear configuration warning (no traceback)."""
    print(f"[config] warning: {message}")


def _as_int(data: dict[str, Any], key: str, default: int,
            low: int, high: int) -> int:
    """Read ``key`` as an int clamped to ``[low, high]`` with a default."""
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _warn(f"'{key}' must be a number, using default {default}")
        return default
    result = int(value)
    if result < low or result > high:
        result = max(low, min(high, result))
        _warn(f"'{key}' out of range, clamped to {result}")
    return result


def _as_float(data: dict[str, Any], key: str, default: float,
              low: float, high: float) -> float:
    """Read ``key`` as a float clamped to ``[low, high]`` with a default."""
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _warn(f"'{key}' must be a number, using default {default}")
        return default
    result = float(value)
    if result < low or result > high:
        result = max(low, min(high, result))
        _warn(f"'{key}' out of range, clamped to {result}")
    return result


def _as_str(data: dict[str, Any], key: str, default: str) -> str:
    """Read ``key`` as a non-empty string with a default."""
    if key not in data:
        return default
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        _warn(f"'{key}' must be a non-empty string, using default")
        return default
    return value


def _default_levels() -> List[Tuple[int, int]]:
    """Build the default list of increasing maze sizes (>= MIN_LEVELS)."""
    levels: List[Tuple[int, int]] = []
    size = 19
    for _ in range(MIN_LEVELS):
        size = min(size, MAX_DIM)
        levels.append((size, size))
        size += 2
    return levels


def _parse_levels(data: dict[str, Any]) -> List[Tuple[int, int]]:
    """Parse and validate the levels array, padding to MIN_LEVELS.

    Both ``levels`` and the singular ``level`` spelling suggested by the
    subject are accepted, so an unexpected key name never costs a level.
    """
    raw = data.get("levels", data.get("level"))
    levels: List[Tuple[int, int]] = []
    if isinstance(raw, list):
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                _warn(f"level #{index} is not an object, ignored")
                continue
            width = _as_int(item, "width", 21, MIN_DIM, MAX_DIM)
            height = _as_int(item, "height", 21, MIN_DIM, MAX_DIM)
            levels.append((width, height))
    elif raw is not None:
        _warn("'levels' must be a list, using defaults")
    if not levels:
        return _default_levels()
    if len(levels) < MIN_LEVELS:
        _warn(f"only {len(levels)} level(s) given, padding to {MIN_LEVELS}")
        defaults = _default_levels()
        levels.extend(defaults[len(levels):])
    return levels


def load_config(path: str) -> Config:
    """Load and validate a configuration file.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        A fully validated :class:`Config` instance.

    Raises:
        ValueError: If the file cannot be read or parsed as JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw_text = handle.read()
    except OSError as error:
        raise ValueError(f"cannot read config file '{path}': {error}")
    except UnicodeDecodeError:
        raise ValueError(f"'{path}' is not a text file, so not a JSON file")

    try:
        data = json.loads(strip_json_comments(raw_text))
    except json.JSONDecodeError as error:
        raise ValueError(f"'{path}' is not a JSON file: {error}")

    if not isinstance(data, dict):
        raise ValueError(f"'{path}' must contain a JSON object")

    config = Config(
        highscore_filename=_as_str(
            data, "highscore_filename", "highscores.json"),
        lives=_as_int(data, "lives", 3, 1, 99),
        seed=_as_int(data, "seed", 42, 0, 2_000_000_000),
        level_max_time=_as_int(data, "level_max_time", 90, 10, 3600),
        points_per_pacgum=_as_int(data, "points_per_pacgum", 10, 0, 100000),
        points_per_super_pacgum=_as_int(
            data, "points_per_super_pacgum", 50, 0, 100000),
        points_per_ghost=_as_int(
            data, "points_per_ghost", 200, 0, 100000),
        edible_duration=_as_float(data, "edible_duration", 7.0, 1.0, 60.0),
        ghost_respawn_time=_as_float(
            data, "ghost_respawn_time", 5.0, 1.0, 60.0),
        player_speed=_as_float(data, "player_speed", 6.0, 1.0, 20.0),
        ghost_speed=_as_float(data, "ghost_speed", 5.0, 1.0, 20.0),
        pacgum=_as_int(data, "pacgum", 0, 0, 100000),
        levels=_parse_levels(data),
    )
    return config
