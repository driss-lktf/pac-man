"""MLX-equivalent drawing layer.

The subject requires a graphical library *similar to MLX*: every function we
rely on must have an equivalent in MLX.  MLX (MiniLibX / MLX42) offers a
deliberately tiny surface:

===========================  ==========================================
MLX function                 :class:`Canvas` / :class:`Window` method
===========================  ==========================================
``mlx_new_image``            :func:`Canvas.new_image`
``mlx_put_pixel``            :meth:`Canvas.put_pixel`
``mlx_image_to_window``      :meth:`Canvas.put_image`
``mlx_put_string``           :meth:`Canvas.put_string`
``mlx_new_window``           :class:`Window`
``mlx_loop`` / ``mlx_hook``  :meth:`Window.poll_events` + the app loop
``mlx_close_window``         :meth:`Window.close`
===========================  ==========================================

Everything else in this module (lines, rectangles, discs, polygons) is
rasterised **by us** on top of ``put_pixel`` and horizontal pixel runs, which
is exactly what one writes by hand on an MLX image buffer.  Horizontal runs
are committed with a single memory write instead of one call per pixel — the
same optimisation an MLX program does by writing directly into the image
buffer returned by ``mlx_get_data_addr``.

No pygame drawing, sprite, transform, mixer or alpha-blending helper is used
anywhere in the project, so no function without an MLX counterpart is relied
upon.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pygame

Color = Tuple[int, int, int]
Point = Tuple[float, float]


class Canvas:
    """A drawable image buffer exposing MLX-level primitives only.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
    """

    def __init__(self, width: int, height: int,
                 surface: Optional[Any] = None) -> None:
        """Create an image buffer (``mlx_new_image``).

        Args:
            width: Buffer width in pixels.
            height: Buffer height in pixels.
            surface: Existing pixel buffer to wrap (used for the window
                buffer); a new one is allocated when omitted.
        """
        self.width = width
        self.height = height
        self._buffer: Any = (surface if surface is not None
                             else pygame.Surface((width, height)))
        self._fonts: Dict[int, Any] = {}

    @classmethod
    def new_image(cls, width: int, height: int) -> "Canvas":
        """Allocate a new off-screen image (``mlx_new_image``)."""
        return cls(width, height)

    @property
    def buffer(self) -> Any:
        """The underlying pixel buffer."""
        return self._buffer

    # ------------------------------------------------------------------
    # Raw pixel access -- the only primitives MLX really gives you
    # ------------------------------------------------------------------
    def put_pixel(self, x: int, y: int, color: Color) -> None:
        """Write a single pixel (``mlx_put_pixel``); out-of-bounds is a no-op.

        Args:
            x: Pixel column.
            y: Pixel row.
            color: RGB colour to write.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self._buffer.set_at((x, y), color)

    def pixel_run(self, x: int, y: int, length: int, color: Color) -> None:
        """Write ``length`` consecutive pixels starting at ``(x, y)``.

        This is the horizontal run an MLX program writes straight into the
        image buffer; it is equivalent to calling :meth:`put_pixel` once per
        pixel, only faster.

        Args:
            x: First pixel column.
            y: Pixel row.
            length: Number of pixels to write.
            color: RGB colour to write.
        """
        if length <= 0 or not (0 <= y < self.height):
            return
        left = max(0, x)
        right = min(self.width, x + length)
        if right > left:
            self._buffer.fill(color, (left, y, right - left, 1))

    def clear(self, color: Color) -> None:
        """Reset every pixel of the image to ``color``."""
        self._buffer.fill(color)

    # ------------------------------------------------------------------
    # Rasterised shapes, all built on the two primitives above
    # ------------------------------------------------------------------
    def fill_rect(self, x: int, y: int, width: int, height: int,
                  color: Color) -> None:
        """Fill an axis-aligned rectangle, one pixel run per row."""
        for row in range(y, y + height):
            self.pixel_run(x, row, width, color)

    def rect(self, x: int, y: int, width: int, height: int,
             color: Color, thickness: int = 1) -> None:
        """Draw the outline of an axis-aligned rectangle."""
        if width <= 0 or height <= 0:
            return
        thickness = max(1, min(thickness, width, height))
        self.fill_rect(x, y, width, thickness, color)
        self.fill_rect(x, y + height - thickness, width, thickness, color)
        self.fill_rect(x, y, thickness, height, color)
        self.fill_rect(x + width - thickness, y, thickness, height, color)

    def rounded_rect(self, x: int, y: int, width: int, height: int,
                     radius: int, color: Color) -> None:
        """Fill a rectangle whose four corners are rounded.

        Args:
            x: Left edge.
            y: Top edge.
            width: Rectangle width.
            height: Rectangle height.
            radius: Corner radius in pixels.
            color: Fill colour.
        """
        radius = max(0, min(radius, width // 2, height // 2))
        for row in range(height):
            inset = 0
            if row < radius:
                delta = radius - row - 1
            elif row >= height - radius:
                delta = row - (height - radius)
            else:
                delta = -1
            if delta >= 0:
                inset = radius - int(math.sqrt(
                    max(0.0, radius * radius - delta * delta)))
            self.pixel_run(x + inset, y + row, width - 2 * inset, color)

    def hline(self, x: int, y: int, length: int, color: Color,
              thickness: int = 1) -> None:
        """Draw a horizontal segment ``thickness`` pixels thick."""
        self.fill_rect(x, y - thickness // 2, length, thickness, color)

    def vline(self, x: int, y: int, length: int, color: Color,
              thickness: int = 1) -> None:
        """Draw a vertical segment ``thickness`` pixels thick."""
        self.fill_rect(x - thickness // 2, y, thickness, length, color)

    def line(self, start: Point, end: Point, color: Color,
             thickness: int = 1) -> None:
        """Draw an arbitrary segment with Bresenham's algorithm.

        Axis-aligned segments are delegated to :meth:`hline` / :meth:`vline`
        so they stay a handful of pixel runs.
        """
        x0, y0 = int(start[0]), int(start[1])
        x1, y1 = int(end[0]), int(end[1])
        if y0 == y1:
            self.hline(min(x0, x1), y0, abs(x1 - x0) + 1, color, thickness)
            return
        if x0 == x1:
            self.vline(x0, min(y0, y1), abs(y1 - y0) + 1, color, thickness)
            return
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        step_x = 1 if x0 < x1 else -1
        step_y = 1 if y0 < y1 else -1
        error = dx + dy
        half = thickness // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                return
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x0 += step_x
            if doubled <= dx:
                error += dx
                y0 += step_y

    def disc(self, cx: int, cy: int, radius: int, color: Color) -> None:
        """Fill a circle, scanline by scanline."""
        if radius <= 0:
            return
        for dy in range(-radius, radius + 1):
            half = int(math.sqrt(max(0.0, radius * radius - dy * dy)))
            self.pixel_run(cx - half, cy + dy, 2 * half + 1, color)

    def ellipse(self, cx: int, cy: int, rx: int, ry: int,
                color: Color) -> None:
        """Fill an axis-aligned ellipse, scanline by scanline."""
        if rx <= 0 or ry <= 0:
            return
        for dy in range(-ry, ry + 1):
            ratio = 1.0 - (dy * dy) / float(ry * ry)
            if ratio < 0.0:
                continue
            half = int(rx * math.sqrt(ratio))
            self.pixel_run(cx - half, cy + dy, 2 * half + 1, color)

    def polygon(self, points: Sequence[Point], color: Color) -> None:
        """Fill a polygon using the even-odd scanline rule.

        Args:
            points: The polygon vertices, in order.
            color: Fill colour.
        """
        count = len(points)
        if count < 3:
            return
        top = max(0, int(min(p[1] for p in points)))
        bottom = min(self.height - 1, int(max(p[1] for p in points)))
        for row in range(top, bottom + 1):
            center = row + 0.5
            crossings: List[float] = []
            for i in range(count):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % count]
                if (y0 <= center) == (y1 <= center):
                    continue
                crossings.append(x0 + (center - y0) * (x1 - x0) / (y1 - y0))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                left = int(math.floor(crossings[i]))
                right = int(math.ceil(crossings[i + 1]))
                self.pixel_run(left, row, right - left, color)

    # ------------------------------------------------------------------
    # Images and text
    # ------------------------------------------------------------------
    def put_image(self, image: "Canvas", x: int, y: int) -> None:
        """Copy another image into this one (``mlx_image_to_window``)."""
        self._buffer.blit(image.buffer, (x, y))

    def _font(self, size: int) -> Any:
        """Return a cached font of the requested pixel height."""
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def string_width(self, text: str, size: int) -> int:
        """Return the pixel width ``text`` would occupy at ``size``."""
        return int(self._font(size).size(text)[0])

    def put_string(self, text: str, x: int, y: int, color: Color,
                   size: int) -> None:
        """Draw text with its top-left corner at ``(x, y)``.

        Equivalent to ``mlx_put_string``; the glyph size is a parameter here
        because the font is ours rather than the library's built-in one.
        """
        self._buffer.blit(self._font(size).render(text, True, color), (x, y))

    def put_string_centered(self, text: str, cx: int, cy: int, color: Color,
                            size: int) -> None:
        """Draw text centred on ``(cx, cy)``."""
        font = self._font(size)
        width, height = font.size(text)
        self._buffer.blit(font.render(text, True, color),
                          (cx - width // 2, cy - height // 2))

    def put_string_right(self, text: str, right: int, cy: int, color: Color,
                         size: int) -> None:
        """Draw text right-aligned on ``right`` and vertically centred."""
        font = self._font(size)
        width, height = font.size(text)
        self._buffer.blit(font.render(text, True, color),
                          (right - width, cy - height // 2))


class Window:
    """An on-screen window and its event queue (``mlx_new_window``)."""

    def __init__(self, width: int, height: int, title: str) -> None:
        """Open the window and prepare its drawable buffer.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.
        """
        pygame.init()
        pygame.display.set_caption(title)
        surface = pygame.display.set_mode((width, height))
        self.canvas = Canvas(width, height, surface)
        self._clock: Any = pygame.time.Clock()

    def poll_events(self) -> List[Any]:
        """Return the pending events (``mlx_hook`` / ``mlx_key_hook``)."""
        events: List[Any] = list(pygame.event.get())
        return events

    def tick(self, fps: int) -> float:
        """Cap the frame rate and return the elapsed seconds."""
        return float(self._clock.tick(fps)) / 1000.0

    def flush(self) -> None:
        """Present the buffer on screen (end of an ``mlx_loop`` iteration)."""
        pygame.display.flip()

    @staticmethod
    def close() -> None:
        """Destroy the window and release the display (``mlx_terminate``)."""
        pygame.quit()
