"""Tests for configuration parsing, comments and clamping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pacman.config import MIN_LEVELS, load_config, strip_json_comments


def test_strip_hash_and_slash_comments() -> None:
    text = '{\n# hash\n"a": 1, // slash\n"b": 2 /* block */\n}'
    assert json.loads(strip_json_comments(text)) == {"a": 1, "b": 2}


def test_comment_markers_inside_strings_are_kept() -> None:
    text = '{"name": "a # b // c"}'
    assert json.loads(strip_json_comments(text)) == {"name": "a # b // c"}


def test_load_defaults_when_empty(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text("{}")
    config = load_config(str(path))
    assert config.lives == 3
    assert config.seed == 42
    assert len(config.levels) >= MIN_LEVELS


def test_invalid_values_are_clamped(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"lives": -1, "player_speed": 999, "seed": "x"}')
    config = load_config(str(path))
    assert config.lives == 1
    assert config.player_speed == 20.0
    assert config.seed == 42


def test_levels_are_padded_to_minimum(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"levels": [{"width": 21, "height": 21}]}')
    config = load_config(str(path))
    assert len(config.levels) == MIN_LEVELS


def test_singular_level_key_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"level": [{"width": 25, "height": 25}]}')
    config = load_config(str(path))
    assert config.levels[0] == (25, 25)
    assert len(config.levels) == MIN_LEVELS


def test_pacgum_count_is_read_and_clamped(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"pacgum": 42}')
    assert load_config(str(path)).pacgum == 42
    path.write_text('{"pacgum": -5}')
    assert load_config(str(path)).pacgum == 0
    path.write_text("{}")
    assert load_config(str(path)).pacgum == 0


def test_unknown_keys_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"nope": 1, "lives": 5}')
    assert load_config(str(path)).lives == 5


def test_missing_file_raises_value_error() -> None:
    with pytest.raises(ValueError):
        load_config("/does/not/exist.json")


def test_non_object_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text("[1, 2, 3]")
    with pytest.raises(ValueError):
        load_config(str(path))


def test_any_filename_is_accepted_when_content_is_json(
        tmp_path: Path) -> None:
    """The subject only requires a JSON file, whatever its name."""
    path = tmp_path / "defense_config"
    path.write_text('{"lives": 5}')
    assert load_config(str(path)).lives == 5


def test_non_json_content_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text("this is definitely not json")
    with pytest.raises(ValueError):
        load_config(str(path))


def test_binary_file_is_rejected_with_a_clear_message(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\xff\xfe")
    with pytest.raises(ValueError, match="not a text file"):
        load_config(str(path))
