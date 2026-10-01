"""Space weather via NOAA SWPC (free, no key)."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import NOAA_KP_INDEX_URL, NOAA_SCALES_URL
from ..errors import DataUnavailableError
from ..models import SpaceWeather
from .base import get_json


def _aurora_verdict(kp: float | None) -> str:
    if kp is None:
        return "Unknown - Kp index unavailable"
    if kp >= 7:
        return "High - aurora may be visible at mid-latitudes"
    if kp >= 5:
        return "Elevated - aurora possible at higher latitudes"
    if kp >= 3:
        return "Low - aurora unlikely outside polar regions"
    return "Quiet - no significant aurora activity expected"


def get_space_weather() -> SpaceWeather:
    kp_index, kp_time = None, None
    try:
        kp_data = get_json(NOAA_KP_INDEX_URL)
        if isinstance(kp_data, list) and kp_data:
            latest = kp_data[-1]
            kp_index = float(latest.get("kp", latest.get("estimated_kp", 0)) or 0)
            time_str = latest.get("time_tag")
            if time_str:
                parsed = datetime.fromisoformat(time_str.replace(" ", "T"))
                kp_time = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (DataUnavailableError, KeyError, ValueError, TypeError, IndexError):
        pass

    scales = {"R": "0", "S": "0", "G": "0"}
    try:
        scale_data = get_json(NOAA_SCALES_URL)
        latest_key = next(iter(scale_data)) if isinstance(scale_data, dict) else None
        if latest_key:
            today = scale_data[latest_key]
            for code in ("R", "S", "G"):
                value = (today.get(code) or {}).get("Scale") if isinstance(today.get(code), dict) else None
                scales[code] = value or "0"
    except (DataUnavailableError, KeyError, TypeError, StopIteration):
        pass

    return SpaceWeather(
        kp_index=kp_index, kp_time=kp_time,
        radio_blackout_scale=f"R{scales['R']}", radiation_storm_scale=f"S{scales['S']}",
        geomagnetic_storm_scale=f"G{scales['G']}", aurora_verdict=_aurora_verdict(kp_index),
    )
