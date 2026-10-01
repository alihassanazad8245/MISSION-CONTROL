"""Central configuration: paths, endpoints, defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

USER_AGENT = "mission-control/2.0"
REQUEST_TIMEOUT: tuple[float, float] = (5.0, 15.0)

ISS_POSITION_URL = "https://api.wheretheiss.at/v1/satellites/25544"
LAUNCHES_URL = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
NASA_NEO_FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
NASA_EPIC_URL = "https://api.nasa.gov/EPIC/api/natural/images"
NASA_EPIC_ARCHIVE = "https://epic.gsfc.nasa.gov/archive/natural"
NOAA_KP_INDEX_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
NOAA_SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_NASA_API_KEY = "DEMO_KEY"

# --- Default location: Pakistan (Islamabad) -------------------------------
DEFAULT_LATITUDE = 33.6844
DEFAULT_LONGITUDE = 73.0479
DEFAULT_LOCATION_LABEL = "Islamabad, Pakistan"
DEFAULT_TIMEZONE = "Asia/Karachi"  # UTC+5, no DST

ISS_REFRESH_SECONDS = 4
LAUNCHES_REFRESH_SECONDS = 600
NEO_REFRESH_SECONDS = 900
WEATHER_REFRESH_SECONDS = 300
SPACE_WEATHER_REFRESH_SECONDS = 300
APOD_REFRESH_SECONDS = 3600
EPIC_REFRESH_SECONDS = 3600
ASTRO_REFRESH_SECONDS = 30

DASHBOARD_TICK_SECONDS = 1.0

WMO_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def resolve_nasa_api_key(explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    return os.environ.get("NASA_API_KEY", "").strip() or DEFAULT_NASA_API_KEY


@dataclass(slots=True)
class Settings:
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    location_label: str = DEFAULT_LOCATION_LABEL

    def to_dict(self) -> dict:
        return {"latitude": self.latitude, "longitude": self.longitude,
                "location_label": self.location_label}

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(
            latitude=data.get("latitude", DEFAULT_LATITUDE),
            longitude=data.get("longitude", DEFAULT_LONGITUDE),
            location_label=data.get("location_label", DEFAULT_LOCATION_LABEL),
        )
