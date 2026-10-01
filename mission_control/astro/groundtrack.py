"""Great-circle extrapolation for smooth ISS animation between API polls.

The live API is only refreshed every few seconds (to stay well within its
generous but non-infinite rate limit), but the ISS moves fast (~7.66 km/s).
Between refreshes, this extrapolates its position forward along a great
circle at its last known heading and speed, computed from two real fixes -
so the on-screen marker moves smoothly and stays accurate, rather than
jumping every few seconds or drifting from a guess.
"""

from __future__ import annotations

import math
from datetime import datetime

EARTH_RADIUS_KM = 6371.0


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial great-circle bearing from point 1 to point 2, degrees from North."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    return math.degrees(math.atan2(y, x)) % 360.0


def destination(lat: float, lon: float, bearing: float, distance_km: float) -> tuple[float, float]:
    """Point reached travelling ``distance_km`` along ``bearing`` from (lat, lon)."""
    phi1, lam1, theta = math.radians(lat), math.radians(lon), math.radians(bearing)
    delta = distance_km / EARTH_RADIUS_KM
    phi2 = math.asin(math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta))
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    lat2 = math.degrees(phi2)
    lon2 = (math.degrees(lam2) + 540.0) % 360.0 - 180.0
    return lat2, lon2


class GroundTrackExtrapolator:
    """Tracks the last two real fixes and extrapolates smooth intermediate
    positions for animation between them."""

    def __init__(self) -> None:
        self._prev: tuple[datetime, float, float] | None = None
        self._heading: float | None = None

    def update(self, when: datetime, lat: float, lon: float) -> None:
        if self._prev is not None:
            _, plat, plon = self._prev
            if (plat, plon) != (lat, lon):
                self._heading = bearing_deg(plat, plon, lat, lon)
        self._prev = (when, lat, lon)

    def position_at(self, when: datetime, velocity_kmh: float) -> tuple[float, float]:
        """Extrapolated (lat, lon) at ``when``, using the last known heading."""
        if self._prev is None:
            return 0.0, 0.0
        fix_time, lat, lon = self._prev
        if self._heading is None:
            return lat, lon
        elapsed_h = (when - fix_time).total_seconds() / 3600.0
        return destination(lat, lon, self._heading, velocity_kmh * elapsed_h)

    @property
    def heading(self) -> float | None:
        return self._heading
