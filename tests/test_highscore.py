"""Tests for the persistent highscore system."""

from __future__ import annotations

from pathlib import Path

from pacman.highscore import (
    MAX_ENTRIES,
    HighScores,
    is_name_char,
    sanitize_name,
)


def test_sanitize_name_strips_and_caps() -> None:
    assert sanitize_name("  Bob!! 4_2  ") == "Bob 42"
    assert sanitize_name("abcdefghijklmnop") == "abcdefghij"
    assert sanitize_name("***") == "PLAYER"


def test_sanitize_name_keeps_ascii_alphanumeric_only() -> None:
    """The subject allows alphanumeric characters and spaces only."""
    assert sanitize_name("emoji-name") == "emojiname"
    assert sanitize_name("Zoe") == "Zoe"
    assert sanitize_name("éèê") == "PLAYER"
    assert sanitize_name("Joél 42") == "Jol 42"


def test_is_name_char_matches_the_allowed_set() -> None:
    assert all(is_name_char(c) for c in "Ab9 ")
    assert not any(is_name_char(c) for c in "é-_!\t\n")


def test_add_keeps_top_ten_sorted(tmp_path: Path) -> None:
    store = HighScores(str(tmp_path / "hs.json"))
    for i in range(15):
        store.add(f"P{i}", i * 10)
    scores = [score for _, score in store.entries]
    assert len(scores) == MAX_ENTRIES
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 140


def test_persistence_roundtrip(tmp_path: Path) -> None:
    path = str(tmp_path / "hs.json")
    first = HighScores(path)
    first.add("Alice", 100)
    second = HighScores(path)
    assert ("Alice", 100) in second.entries


def test_corrupted_file_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "hs.json"
    path.write_text("not valid json {{{")
    store = HighScores(str(path))
    assert store.entries == []


def test_qualifies(tmp_path: Path) -> None:
    store = HighScores(str(tmp_path / "hs.json"))
    assert store.qualifies(10) is True
    assert store.qualifies(-1) is False
    for i in range(MAX_ENTRIES):
        store.add("P", 100)
    assert store.qualifies(50) is False
    assert store.qualifies(150) is True


def test_negative_scores_are_coerced(tmp_path: Path) -> None:
    store = HighScores(str(tmp_path / "hs.json"))
    store.add("Neg", -50)
    assert store.entries == [("Neg", 0)]
