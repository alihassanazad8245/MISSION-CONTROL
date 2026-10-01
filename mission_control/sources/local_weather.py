"""Local weather via Open-Meteo (free, no key, no signup)."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import OPEN_METEO_URL, WMO_WEATHER_CODES
from ..errors import DataUnavailableError
from ..models import LocalWeather
from .base import get_json


def _parse_iso_naive_as_utc(value: str) -> datetime:
    # Open-Meteo returns local-to-the-requested-timezone naive strings when a
    # timezone is given; we always request "UTC" explicitly so these are UTC.
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def get_local_weather(latitude: float, longitude: float, location_label: str) -> LocalWeather:
    data = get_json(OPEN_METEO_URL, params={
        "latitude": latitude, "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,"
                  "weather_code,wind_speed_10m,wind_direction_10m",
        "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min,uv_index_max",
        "timezone": "UTC",
    })
    try:
        current = data["current"]
        daily = data["daily"]
        code = int(current.get("weather_code", 0))
        sunrise = _parse_iso_naive_as_utc(daily["sunrise"][0]) if daily.get("sunrise") else None
        sunset = _parse_iso_naive_as_utc(daily["sunset"][0]) if daily.get("sunset") else None
        uv = daily.get("uv_index_max", [None])[0]
        return LocalWeather(
            temperature_c=float(current["temperature_2m"]),
            apparent_c=float(current["apparent_temperature"]),
            humidity_pct=float(current["relative_humidity_2m"]),
            wind_kmh=float(current["wind_speed_10m"]),
            wind_dir_deg=float(current["wind_direction_10m"]),
            weather_code=code, weather_text=WMO_WEATHER_CODES.get(code, "Unknown"),
            is_day=bool(current.get("is_day", 1)),
            sunrise=sunrise, sunset=sunset,
            daily_max_c=float(daily["temperature_2m_max"][0]),
            daily_min_c=float(daily["temperature_2m_min"][0]),
            uv_index=float(uv) if uv is not None else None,
            location_label=location_label,
        )
    except (KeyError, ValueError, IndexError, TypeError) as exc:
        raise DataUnavailableError("Unexpected weather response format.") from exc
