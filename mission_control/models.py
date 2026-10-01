"""Typed data structures for each dashboard panel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class IssPosition:
    latitude: float
    longitude: float
    altitude_km: float
    velocity_kmh: float
    visibility: str
    timestamp: datetime


@dataclass(slots=True)
class Launch:
    name: str
    net: datetime
    status: str
    provider: str
    rocket: str
    pad: str
    location: str


@dataclass(slots=True)
class CloseApproach:
    name: str
    close_approach_time: datetime
    velocity_kmh: float
    miss_distance_km: float
    miss_distance_lunar: float
    diameter_min_m: float
    diameter_max_m: float
    is_hazardous: bool


@dataclass(slots=True)
class SpaceWeather:
    kp_index: float | None
    kp_time: datetime | None
    radio_blackout_scale: str
    radiation_storm_scale: str
    geomagnetic_storm_scale: str
    aurora_verdict: str


@dataclass(slots=True)
class ApodEntry:
    title: str
    explanation: str
    date: str
    media_type: str
    url: str
    copyright: str = ""


@dataclass(slots=True)
class EarthImage:
    caption: str
    date: str
    image_url: str


@dataclass(slots=True)
class LocalWeather:
    temperature_c: float
    apparent_c: float
    humidity_pct: float
    wind_kmh: float
    wind_dir_deg: float
    weather_code: int
    weather_text: str
    is_day: bool
    sunrise: datetime | None
    sunset: datetime | None
    daily_max_c: float
    daily_min_c: float
    uv_index: float | None
    location_label: str
