"""Settings persistence: the observer's saved location, as plain JSON.
Defaults to Islamabad, Pakistan if nothing has been saved yet.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .config import SETTINGS_FILE, Settings


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_settings(path: Path | None = None) -> Settings:
    path = path if path is not None else SETTINGS_FILE
    if not path.exists():
        return Settings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    return Settings.from_dict(raw)


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = path if path is not None else SETTINGS_FILE
    _atomic_write(path, json.dumps(settings.to_dict(), indent=2))
