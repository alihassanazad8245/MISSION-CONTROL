"""Small reusable Textual widgets: anything that renders a Rich object and
needs periodic repainting."""

from __future__ import annotations

from typing import Callable

from rich.console import RenderableType
from textual.reactive import reactive
from textual.widgets import Static


class LiveRenderable(Static):
    """A Static widget that repaints from a zero-arg callable on demand."""

    def __init__(self, renderer: Callable[[], RenderableType], **kwargs) -> None:
        super().__init__(**kwargs)
        self._renderer = renderer

    def refresh_content(self) -> None:
        try:
            self.update(self._renderer())
        except Exception as exc:  # noqa: BLE001 - never let a render bug crash the app
            self.update(f"[red]Render error: {exc}[/red]")
