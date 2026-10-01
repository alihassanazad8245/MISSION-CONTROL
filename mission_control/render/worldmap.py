"""A real coastline world map, rendered with Unicode Braille characters.

Braille cells pack a 2x4 dot grid per character, giving roughly 4x the
resolution of plain block characters in the same terminal space. The land
mask comes from actual Natural Earth 1:110m coastline data (see
``landdata.py``), not a hand-drawn approximation.
"""

from __future__ import annotations

import zlib
import base64
from functools import lru_cache

from . import landdata

# Dot bit positions within a Braille cell, indexed [col][row] (2 wide, 4 tall).
_DOT_BITS = [[0x01, 0x02, 0x04, 0x40], [0x08, 0x10, 0x20, 0x80]]
BRAILLE_BASE = 0x2800


@lru_cache(maxsize=1)
def _land_bits() -> bytes:
    return zlib.decompress(base64.b64decode(landdata.DATA))


def is_land(lat: float, lon: float) -> bool:
    """Look up the land/sea mask at a given latitude/longitude."""
    w, h = landdata.WIDTH, landdata.HEIGHT
    x = int((lon + 180.0) / 360.0 * w) % w
    y = min(h - 1, max(0, int((90.0 - lat) / 180.0 * h)))
    row_bytes = w // 8
    byte_index = y * row_bytes + x // 8
    bit = 7 - (x % 8)
    return bool(_land_bits()[byte_index] & (1 << bit))


def render_map(
    cols: int, rows: int,
    markers: dict[str, tuple[float, float]] | None = None,
    trail: list[tuple[float, float]] | None = None,
) -> list[str]:
    """Render the world map at ``cols`` x ``rows`` *character* cells (each
    cell covers a 2x4 dot block, so effective resolution is doubled/quadrupled).

    ``markers`` is ``{single_char_or_word: (lat, lon)}`` - each is placed as
    a plain character overlay (not a Braille dot) so it stands out.
    ``trail`` is a list of (lat, lon) plotted as individual Braille dots,
    e.g. a satellite's recent ground track.
    """
    grid = [[0] * cols for _ in range(rows)]
    dot_w, dot_h = cols * 2, rows * 4

    for py in range(dot_h):
        lat = 90.0 - (py + 0.5) / dot_h * 180.0
        for px in range(dot_w):
            lon = (px + 0.5) / dot_w * 360.0 - 180.0
            if is_land(lat, lon):
                cell_col, cell_row = px // 2, py // 4
                sub_col, sub_row = px % 2, py % 4
                grid[cell_row][cell_col] |= _DOT_BITS[sub_col][sub_row]

    if trail:
        for lat, lon in trail:
            px = int((lon + 180.0) / 360.0 * dot_w) % dot_w
            py = min(dot_h - 1, max(0, int((90.0 - lat) / 180.0 * dot_h)))
            cell_col, cell_row = px // 2, py // 4
            sub_col, sub_row = px % 2, py % 4
            grid[cell_row][cell_col] |= _DOT_BITS[sub_col][sub_row]

    lines = ["".join(chr(BRAILLE_BASE + v) for v in row) for row in grid]

    if markers:
        for label, (lat, lon) in markers.items():
            col = int((lon + 180.0) / 360.0 * cols) % cols
            row = min(rows - 1, max(0, int((90.0 - lat) / 180.0 * rows)))
            line = lines[row]
            glyph = label[0]
            lines[row] = line[:col] + glyph + line[col + 1:]

    return lines
