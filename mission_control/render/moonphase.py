"""ASCII Moon-phase disc, shaded by the real terminator position."""

from __future__ import annotations

import math

from rich.text import Text

_SHADES = " .:-=+*#%@"


def render_moon(illumination: float, waxing: bool, diameter: int = 16) -> Text:
    """A circular disc where the lit fraction (0..1) and direction (waxing =
    terminator bulges toward the right) matches the real Moon right now."""
    radius = diameter / 2.0
    text = Text()
    for row in range(diameter):
        y = row - radius + 0.5
        ny = y / radius
        for col in range(diameter * 2):  # double width, terminal chars are tall
            x = (col - diameter + 0.5) / 2.0
            nx = x / radius
            dist = math.sqrt(nx * nx + ny * ny)
            if dist > 1.0:
                text.append(" ")
                continue
            # Terminator position in the same normalised (-1..1) space as nx/ny.
            # Waxing: illuminated on the right, growing from new (t=+1, nothing
            # lit) to full (t=-1, everything lit). Waning is the mirror image:
            # illuminated on the left, shrinking from full back to new.
            half_width = math.sqrt(max(0.0, 1 - ny * ny))
            if waxing:
                terminator_x = math.cos(illumination * math.pi) * half_width
                lit = nx >= terminator_x
            else:
                terminator_x = -math.cos(illumination * math.pi) * half_width
                lit = nx <= terminator_x
            shade = _SHADES[-1] if lit else _SHADES[1]
            style = "bold white" if lit else "grey35"
            text.append(shade, style=style)
        text.append("\n")
    return text
