"""A top-down animated solar-system diagram.

Every planet is drawn at its real current heliocentric longitude (from
``astro.kepler``) on a ring sized by its true orbital distance (compressed
with a square-root scale so Mercury and Neptune both fit on screen). Real
planetary motion is far too slow to see change second to second, so the
dashboard can advance a *simulated* clock faster than real time - the
physics is exact for whatever moment is being simulated, only the clock
itself is sped up, and that is always labelled on screen.
"""

from __future__ import annotations

import math
from datetime import datetime

from rich.text import Text

from ..astro.kepler import PLANETS, heliocentric_longitude
from ..astro.timeutil import julian_date

PLANET_COLORS = {
    "Mercury": "grey70", "Venus": "wheat1", "Earth": "dodger_blue1", "Mars": "red3",
    "Jupiter": "orange3", "Saturn": "gold3", "Uranus": "cyan", "Neptune": "blue3",
}
PLANET_SYMBOLS = {
    "Mercury": "\u263f", "Venus": "\u2640", "Earth": "\u2295", "Mars": "\u2642",
    "Jupiter": "\u2643", "Saturn": "\u2644", "Uranus": "\u2645", "Neptune": "\u2646",
}
#: Real semi-major axes in AU, for the display ring radii (sqrt-scaled below).
_SEMI_MAJOR_AU = {
    "Mercury": 0.387, "Venus": 0.723, "Earth": 1.0, "Mars": 1.524,
    "Jupiter": 5.203, "Saturn": 9.537, "Uranus": 19.19, "Neptune": 30.07,
}


def render_orbits(when: datetime, width: int, height: int, highlight: str | None = None) -> Text:
    """Render the solar system top-down, Sun at centre, at ``when``.

    Ring spacing is schematic (evenly spaced by orbital rank), not physically
    to scale - true relative distances (Mercury at ~13% of Neptune's orbit)
    would crush the inner planets into the Sun's own character cell at
    terminal resolution. Angles are always the real computed positions.
    """
    jd = julian_date(when)
    cx, cy = width / 2.0, height / 2.0
    max_radius = min(cx, cy) - 1.5
    ring_step = max_radius / len(PLANETS)

    grid: list[list[tuple[str, str] | None]] = [[None for _ in range(width)] for _ in range(height)]

    def put(x: float, y: float, char: str, style: str, priority: int) -> None:
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < width and 0 <= iy < height:
            existing = grid[iy][ix]
            if existing is None or priority >= existing[2]:
                grid[iy][ix] = (char, style, priority)

    def rank_radius(name: str) -> float:
        return ring_step * (PLANETS.index(name) + 1)

    # Orbit rings (faint dots) - drawn first, lowest priority.
    for name in PLANETS:
        radius = rank_radius(name)
        steps = max(24, int(radius * 8))
        for k in range(steps):
            theta = 2 * math.pi * k / steps
            # Terminal cells are roughly twice as tall as wide - squash Y to keep circles round.
            put(cx + radius * math.cos(theta), cy + radius * math.sin(theta) * 0.5, "\u00b7", "grey27", 0)

    put(cx, cy, "\u2600", "bold yellow", 2)  # the Sun - always wins over any planet

    for name in PLANETS:
        lon = heliocentric_longitude(name, jd)
        if name == "Earth":
            lon = (lon + 180.0) % 360.0  # Earth's position as seen from the Sun
        radius = rank_radius(name)
        theta = math.radians(lon)
        x, y = cx + radius * math.cos(theta), cy + radius * math.sin(theta) * 0.5
        style = PLANET_COLORS.get(name, "white")
        if highlight == name:
            style = f"bold {style} on grey15"
        put(x, y, PLANET_SYMBOLS.get(name, "*"), style, 1)

    text = Text()
    for row in grid:
        for cell in row:
            if cell is None:
                text.append(" ")
            else:
                text.append(cell[0], style=cell[1])
        text.append("\n")
    return text
