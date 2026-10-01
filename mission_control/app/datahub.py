"""Central cache/fetch hub: one background-friendly place that owns every
live data source, each on its own refresh cadence, each independently
resilient to failure."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Generic, TypeVar

from ..config import (
    APOD_REFRESH_SECONDS,
    EPIC_REFRESH_SECONDS,
    ISS_REFRESH_SECONDS,
    LAUNCHES_REFRESH_SECONDS,
    NEO_REFRESH_SECONDS,
    SPACE_WEATHER_REFRESH_SECONDS,
    WEATHER_REFRESH_SECONDS,
)
from ..errors import DataUnavailableError, MissionControlError
from ..sources import iss, launches, local_weather, neo, photos, space_weather

T = TypeVar("T")


@dataclass
class Slot(Generic[T]):
    """One cached value, fetched on a background thread on its own cadence."""

    fetch: Callable[[], T]
    refresh_seconds: float
    value: T | None = None
    error: MissionControlError | None = None
    updated_at: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _inflight: bool = False

    def maybe_refresh(self, now: float) -> None:
        if self._inflight or (now - self.updated_at) < self.refresh_seconds:
            return
        with self._lock:
            if self._inflight:
                return
            self._inflight = True
        threading.Thread(target=self._do_fetch, daemon=True).start()

    def _do_fetch(self) -> None:
        try:
            value = self.fetch()
            with self._lock:
                self.value, self.error = value, None
        except MissionControlError as exc:
            with self._lock:
                self.error = exc
        except Exception as exc:  # noqa: BLE001 - never let one source kill the app
            with self._lock:
                self.error = DataUnavailableError(str(exc))
        finally:
            with self._lock:
                self.updated_at = time.monotonic()
                self._inflight = False


class DataHub:
    """Owns every live-data :class:`Slot` used by the dashboard."""

    def __init__(self, nasa_api_key: str, latitude: float, longitude: float, location_label: str) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.location_label = location_label

        self.iss: Slot = Slot(iss.get_iss_position, ISS_REFRESH_SECONDS)
        self.launches: Slot = Slot(lambda: launches.get_upcoming_launches(8), LAUNCHES_REFRESH_SECONDS)
        self.neo: Slot = Slot(lambda: neo.get_close_approaches(nasa_api_key), NEO_REFRESH_SECONDS)
        self.space_weather: Slot = Slot(space_weather.get_space_weather, SPACE_WEATHER_REFRESH_SECONDS)
        self.apod: Slot = Slot(lambda: photos.get_apod(nasa_api_key), APOD_REFRESH_SECONDS)
        self.epic: Slot = Slot(lambda: photos.get_latest_earth_image(nasa_api_key), EPIC_REFRESH_SECONDS)
        self.weather: Slot = Slot(
            lambda: local_weather.get_local_weather(latitude, longitude, location_label),
            WEATHER_REFRESH_SECONDS,
        )
        self._epic_image_bytes: bytes | None = None
        self._epic_image_url: str | None = None

    def tick(self) -> None:
        now = time.monotonic()
        for slot in (self.iss, self.launches, self.neo, self.space_weather,
                    self.apod, self.epic, self.weather):
            slot.maybe_refresh(now)

    def get_epic_image_bytes(self) -> bytes | None:
        """Download the actual EPIC image once its URL is known (not just
        its metadata), cached until a newer image appears."""
        epic = self.epic.value
        if epic is None:
            return None
        if self._epic_image_url == epic.image_url and self._epic_image_bytes is not None:
            return self._epic_image_bytes
        try:
            import requests
            response = requests.get(epic.image_url, timeout=(5, 20))
            if response.status_code == 200:
                self._epic_image_bytes = response.content
                self._epic_image_url = epic.image_url
                return self._epic_image_bytes
        except Exception:  # noqa: BLE001
            pass
        return None
