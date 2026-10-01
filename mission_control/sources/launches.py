"""Upcoming launches via Launch Library 2 (free, no key, ~15 req/hour anon)."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import LAUNCHES_URL
from ..models import Launch
from .base import get_json


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def get_upcoming_launches(limit: int = 8) -> list[Launch]:
    data = get_json(LAUNCHES_URL, params={"limit": limit})
    launches: list[Launch] = []
    for item in data.get("results", []):
        try:
            provider = (item.get("launch_service_provider") or {}).get("name", "Unknown")
            rocket_cfg = (item.get("rocket") or {}).get("configuration") or {}
            pad = item.get("pad") or {}
            location = (pad.get("location") or {}).get("name", "Unknown")
            launches.append(Launch(
                name=item.get("name", "Unnamed launch"), net=_parse_dt(item["net"]),
                status=(item.get("status") or {}).get("name", "Unknown"), provider=provider,
                rocket=rocket_cfg.get("full_name") or rocket_cfg.get("name", "Unknown rocket"),
                pad=pad.get("name", "Unknown pad"), location=location,
            ))
        except (KeyError, ValueError):
            continue
    return launches
