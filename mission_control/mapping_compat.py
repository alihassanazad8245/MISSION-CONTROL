"""Small formatting helpers (kept separate from render/ since it has no UI deps)."""

from __future__ import annotations


def format_duration(seconds: float) -> str:
    """Render a countdown/count-up duration as ``Xd Xh Xm`` or ``Xh Xm Xs``."""
    seconds = int(seconds)
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days > 0:
        return f"{sign}{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{sign}{hours}h {minutes}m {secs}s"
    return f"{sign}{minutes}m {secs}s"
