"""Geocentric planet positions and rise/set, built on the Keplerian elements."""

from __future__ import annotations

import math
from datetime import datetime

from .kepler import PLANETS, heliocentric, orbital_period_years
from .sun_moon import ecliptic_to_equatorial, equatorial_to_horizontal
from .timeutil import julian_date

VISIBLE_PLANETS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]


def geocentric_equatorial(name: str, jd: float) -> tuple[float, float, float]:
    """(RA deg, Dec deg, distance AU from Earth) for any planet, geocentric."""
    ex, ey, ez = heliocentric("Earth", jd)
    px, py, pz = heliocentric(name, jd)
    x, y, z = px - ex, py - ey, pz - ez
    dist = math.sqrt(x * x + y * y + z * z)
    ecl_lon = math.degrees(math.atan2(y, x)) % 360.0
    ecl_lat = math.degrees(math.asin(z / dist))
    ra, dec = ecliptic_to_equatorial(ecl_lon, ecl_lat, jd)
    return ra, dec, dist


def planet_altaz(name: str, lat: float, lon: float, when: datetime) -> tuple[float, float]:
    jd = julian_date(when)
    ra, dec, _ = geocentric_equatorial(name, jd)
    return equatorial_to_horizontal(ra, dec, lat, lon, jd)


def planet_distance_au(name: str, when: datetime) -> float:
    _, _, dist = geocentric_equatorial(name, julian_date(when))
    return dist


def elongation_from_sun(name: str, when: datetime) -> float:
    """Apparent separation between a planet and the Sun, as seen from Earth (degrees)."""
    from .sun_moon import sun_equatorial

    jd = julian_date(when)
    ra_p, dec_p, _ = geocentric_equatorial(name, jd)
    ra_s, dec_s, _ = sun_equatorial(jd)
    ra_p, dec_p, ra_s, dec_s = map(math.radians, (ra_p, dec_p, ra_s, dec_s))
    cos_sep = (math.sin(dec_p) * math.sin(dec_s)
               + math.cos(dec_p) * math.cos(dec_s) * math.cos(ra_p - ra_s))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_sep))))
