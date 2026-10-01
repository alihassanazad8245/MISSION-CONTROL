#!/usr/bin/env python3
"""Mission Control - entry point.

    python main.py          launch the live dashboard
    python main.py --help   all options
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def run() -> int:
    try:
        from mission_control.cli import main
    except ImportError as exc:
        package = getattr(exc, "name", None) or "a required package"
        sys.stderr.write(
            f"\n[ERROR] Mission Control could not start: '{package}' is not installed.\n\n"
            "Install the dependencies first:\n\n    pip install -r requirements.txt\n\n"
        )
        return 2
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
