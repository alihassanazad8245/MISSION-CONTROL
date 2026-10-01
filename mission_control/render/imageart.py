"""Render a downloaded image as full-colour terminal art.

Uses the "upper half block" trick (▀): each character cell shows two
vertical source pixels at once - the block's foreground colour is the top
pixel, its background colour is the bottom pixel - roughly doubling
vertical resolution versus one pixel per character. Works in any truecolor
terminal, no image protocol (Sixel/Kitty/iTerm2) required.
"""

from __future__ import annotations

import io

from rich.text import Text


def render_image_bytes(data: bytes, width: int, height: int) -> Text:
    """Render raw image bytes as a Rich :class:`Text` of coloured half-blocks.

    ``height`` is in *character rows*; each row encodes 2 source pixel rows,
    so the image is resampled to ``(width, height * 2)`` pixels first.
    """
    from PIL import Image

    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB").resize((width, height * 2))
        pixels = img.load()

        text = Text()
        for row in range(height):
            for col in range(width):
                top = pixels[col, row * 2]
                bottom = pixels[col, row * 2 + 1]
                text.append("\u2580", style=f"rgb({top[0]},{top[1]},{top[2]}) on rgb({bottom[0]},{bottom[1]},{bottom[2]})")
            if row != height - 1:
                text.append("\n")
        return text
