"""Unit tests for the MLX-equivalent drawing layer."""

from __future__ import annotations

import os
from typing import Tuple

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from pacman.canvas import Canvas  # noqa: E402

BLACK: Tuple[int, int, int] = (0, 0, 0)
RED: Tuple[int, int, int] = (255, 0, 0)


def _canvas(width: int = 32, height: int = 32) -> Canvas:
    """Return a cleared off-screen image."""
    pygame.init()
    image = Canvas.new_image(width, height)
    image.clear(BLACK)
    return image


def _at(image: Canvas, x: int, y: int) -> Tuple[int, int, int]:
    """Return the RGB colour of one pixel."""
    red, green, blue = tuple(image.buffer.get_at((x, y)))[:3]
    return (red, green, blue)


def test_put_pixel_writes_one_pixel() -> None:
    image = _canvas()
    image.put_pixel(4, 5, RED)
    assert _at(image, 4, 5) == RED
    assert _at(image, 5, 5) == BLACK


def test_put_pixel_out_of_bounds_is_ignored() -> None:
    image = _canvas()
    image.put_pixel(-1, 0, RED)
    image.put_pixel(0, 999, RED)
    assert _at(image, 0, 0) == BLACK


def test_pixel_run_is_clipped_to_the_image() -> None:
    image = _canvas(8, 8)
    image.pixel_run(-3, 2, 100, RED)
    assert _at(image, 0, 2) == RED
    assert _at(image, 7, 2) == RED
    assert _at(image, 0, 3) == BLACK


def test_fill_rect_covers_its_area_only() -> None:
    image = _canvas()
    image.fill_rect(2, 3, 4, 5, RED)
    assert _at(image, 2, 3) == RED
    assert _at(image, 5, 7) == RED
    assert _at(image, 6, 7) == BLACK
    assert _at(image, 2, 8) == BLACK


def test_rect_draws_an_outline_and_not_a_fill() -> None:
    image = _canvas()
    image.rect(1, 1, 10, 10, RED, 1)
    assert _at(image, 1, 1) == RED
    assert _at(image, 10, 10) == RED
    assert _at(image, 5, 5) == BLACK


def test_disc_is_filled_and_bounded_by_its_radius() -> None:
    image = _canvas()
    image.disc(16, 16, 5, RED)
    assert _at(image, 16, 16) == RED
    assert _at(image, 16, 21) == RED
    assert _at(image, 16, 23) == BLACK


def test_ellipse_respects_both_radii() -> None:
    image = _canvas()
    image.ellipse(16, 16, 8, 3, RED)
    assert _at(image, 23, 16) == RED
    assert _at(image, 16, 19) == RED
    assert _at(image, 16, 22) == BLACK


def test_line_draws_both_endpoints() -> None:
    image = _canvas()
    image.line((2, 2), (20, 12), RED, 1)
    assert _at(image, 2, 2) == RED
    assert _at(image, 20, 12) == RED


def test_polygon_fills_its_interior() -> None:
    image = _canvas()
    image.polygon([(4, 4), (24, 4), (24, 24), (4, 24)], RED)
    assert _at(image, 14, 14) == RED
    assert _at(image, 2, 2) == BLACK


def test_put_image_copies_another_image() -> None:
    source = _canvas(8, 8)
    source.clear(RED)
    target = _canvas()
    target.put_image(source, 4, 4)
    assert _at(target, 4, 4) == RED
    assert _at(target, 11, 11) == RED
    assert _at(target, 12, 12) == BLACK


def test_put_string_draws_something() -> None:
    image = _canvas(200, 60)
    image.put_string("42", 10, 10, RED, 40)
    painted = any(
        _at(image, x, y) != BLACK
        for y in range(60) for x in range(200)
    )
    assert painted
    assert image.string_width("42", 40) > 0
