"""Sun and Moon: positions, phase, and rise/set/twilight events.

The Sun comes from Earth's Keplerian elements (with precession to the date);
the Moon uses the principal terms of Meeus' lunar theory, good to roughly
0.1-0.2 degrees - plenty for phase, rise/set and "where to look" purposes.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Callable

from .kepler import PRECESSION_DEG_PER_CENTURY, heliocentric
from .timeutil import centuries, from_julian_date, gmst_deg, julian_date

SYNODIC_MONTH = 29.530588853
AU_KM = 149_597_870.7


def obliquity_deg(jd: float) -> float:
    return 23.439291 - 0.0130042 * centuries(jd)


def ecliptic_to_equatorial(lon_deg: float, lat_deg: float, jd: float) -> tuple[float, float]:
    """Ecliptic (of date) longitude/latitude -> right ascension/declination, degrees."""
    eps = math.radians(obliquity_deg(jd))
    lam, beta = math.radians(lon_deg), math.radians(lat_deg)
    ra = math.atan2(math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps), math.cos(lam))
    dec = math.asin(math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam))
    return math.degrees(ra) % 360.0, math.degrees(dec)


def equatorial_to_horizontal(ra: float, dec: float, lat: float, lon: float, jd: float) -> tuple[float, float]:
    """RA/Dec (degrees) -> (altitude, azimuth from North through East), degrees."""
    hour_angle = math.radians((gmst_deg(jd) + lon - ra) % 360.0)
    phi, delta = math.radians(lat), math.radians(dec)
    sin_alt = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(hour_angle)
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    az = math.degrees(math.atan2(
        math.sin(hour_angle), math.cos(hour_angle) * math.sin(phi) - math.tan(delta) * math.cos(phi)
    )) + 180.0
    return alt, az % 360.0


# --------------------------------------------------------------------------- #
# Sun
# --------------------------------------------------------------------------- #


def sun_ecliptic_longitude(jd: float) -> float:
    """Apparent-ish geocentric ecliptic longitude of the Sun, of date, degrees."""
    ex, ey, _ = heliocentric("Earth", jd)
    lon = math.degrees(math.atan2(-ey, -ex))
    return (lon + PRECESSION_DEG_PER_CENTURY * centuries(jd)) % 360.0


def sun_equatorial(jd: float) -> tuple[float, float, float]:
    """(RA deg, Dec deg, distance AU) of the Sun."""
    ex, ey, ez = heliocentric("Earth", jd)
    dist = math.sqrt(ex * ex + ey * ey + ez * ez)
    lon = sun_ecliptic_longitude(jd)
    lat = math.degrees(math.asin(-ez / dist))
    ra, dec = ecliptic_to_equatorial(lon, lat, jd)
    return ra, dec, dist


def sun_altitude(lat: float, lon: float, when: datetime) -> float:
    jd = julian_date(when)
    ra, dec, _ = sun_equatorial(jd)
    return equatorial_to_horizontal(ra, dec, lat, lon, jd)[0]


def sun_altaz(lat: float, lon: float, when: datetime) -> tuple[float, float]:
    jd = julian_date(when)
    ra, dec, _ = sun_equatorial(jd)
    return equatorial_to_horizontal(ra, dec, lat, lon, jd)


# --------------------------------------------------------------------------- #
# Moon (Meeus, Astronomical Algorithms ch. 47, principal terms)
# --------------------------------------------------------------------------- #

# (D, M, M', F, sum_l [1e-6 deg], sum_r [1e-3 km])
_MOON_LON_DIST = [
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111),
    (2, 0, 0, 0, 658314, -2955968), (0, 0, 2, 0, 213618, -569925),
    (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138),
    (2, 0, 1, 0, 53322, -170733), (2, -1, 0, 0, 45758, -204586),
    (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321),
    (0, 0, 1, 2, -12528, 0), (0, 0, 1, -2, 10980, 79661),
    (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
]
# (D, M, M', F, sum_b [1e-6 deg])
_MOON_LAT = [
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693),
    (2, 0, 0, -1, 173237), (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271),
    (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198), (2, 0, 1, -1, 9266),
    (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324), (2, 0, 1, 1, 4200),
]


def moon_ecliptic(jd: float) -> tuple[float, float, float]:
    """(longitude deg, latitude deg, distance km) of the Moon, of date."""
    t = centuries(jd)
    lp = 218.3164477 + 481267.88123421 * t - 0.0015786 * t * t
    d = math.radians(297.8501921 + 445267.1114034 * t - 0.0018819 * t * t)
    m = math.radians(357.5291092 + 35999.0502909 * t - 0.0001536 * t * t)
    mp = math.radians(134.9633964 + 477198.8675055 * t + 0.0087414 * t * t)
    f = math.radians(93.2720950 + 483202.0175233 * t - 0.0036539 * t * t)
    e = 1.0 - 0.002516 * t - 0.0000074 * t * t

    sum_l = sum_r = sum_b = 0.0
    for cd, cm, cmp_, cf, sl, sr in _MOON_LON_DIST:
        arg = cd * d + cm * m + cmp_ * mp + cf * f
        factor = e ** abs(cm)
        sum_l += sl * factor * math.sin(arg)
        sum_r += sr * factor * math.cos(arg)
    for cd, cm, cmp_, cf, sb in _MOON_LAT:
        arg = cd * d + cm * m + cmp_ * mp + cf * f
        sum_b += sb * (e ** abs(cm)) * math.sin(arg)

    return (lp + sum_l / 1e6) % 360.0, sum_b / 1e6, 385000.56 + sum_r / 1000.0


def moon_equatorial(jd: float) -> tuple[float, float, float]:
    lon, lat, dist = moon_ecliptic(jd)
    ra, dec = ecliptic_to_equatorial(lon, lat, jd)
    return ra, dec, dist


def moon_altaz(lat: float, lon: float, when: datetime) -> tuple[float, float]:
    """Topocentric altitude/azimuth (includes the Moon's large parallax)."""
    jd = julian_date(when)
    ra, dec, dist = moon_equatorial(jd)
    alt, az = equatorial_to_horizontal(ra, dec, lat, lon, jd)
    parallax = math.degrees(math.asin(6378.14 / dist))
    return alt - parallax * math.cos(math.radians(alt)), az


def moon_elongation(jd: float) -> float:
    """Moon - Sun ecliptic longitude, 0..360 (0 = new, 180 = full)."""
    return (moon_ecliptic(jd)[0] - sun_ecliptic_longitude(jd)) % 360.0


def moon_illumination(jd: float) -> float:
    """Illuminated fraction of the lunar disc, 0..1."""
    lon, lat, _ = moon_ecliptic(jd)
    elong = math.radians((lon - sun_ecliptic_longitude(jd)) % 360.0)
    return (1.0 - math.cos(math.radians(lat)) * math.cos(elong)) / 2.0


def phase_name(elong: float) -> str:
    e = elong % 360.0
    if e < 6 or e >= 354:
        return "New Moon"
    if e < 84:
        return "Waxing Crescent"
    if e < 96:
        return "First Quarter"
    if e < 174:
        return "Waxing Gibbous"
    if e < 186:
        return "Full Moon"
    if e < 264:
        return "Waning Gibbous"
    if e < 276:
        return "Last Quarter"
    return "Waning Crescent"


def next_phase(after: datetime, target_elongation: float) -> datetime:
    """Time (UTC) of the next moment the Moon reaches ``target_elongation``
    (0 = new, 90 = first quarter, 180 = full, 270 = last quarter)."""
    jd0 = julian_date(after)

    def diff(jd: float) -> float:
        return ((moon_elongation(jd) - target_elongation + 180.0) % 360.0) - 180.0

    step = 0.125  # 3 hours
    lo, prev = jd0, diff(jd0)
    for _ in range(int(SYNODIC_MONTH / step) + 20):
        hi = lo + step
        cur = diff(hi)
        if prev < 0 <= cur and abs(cur - prev) < 90:
            for _ in range(30):  # bisection
                mid = (lo + hi) / 2.0
                if diff(mid) < 0:
                    lo = mid
                else:
                    hi = mid
            return from_julian_date((lo + hi) / 2.0)
        lo, prev = hi, cur
    return after + timedelta(days=SYNODIC_MONTH / 2)


# --------------------------------------------------------------------------- #
# Rise / set / twilight scanning
# --------------------------------------------------------------------------- #


def find_crossings(
    altitude_fn: Callable[[datetime], float], start: datetime, hours: float,
    threshold: float, step_minutes: float = 10.0,
) -> list[tuple[str, datetime]]:
    """Find every ('rise'|'set', time) where altitude crosses ``threshold``."""
    events: list[tuple[str, datetime]] = []
    step = timedelta(minutes=step_minutes)
    t_prev, a_prev = start, altitude_fn(start) - threshold
    steps = int(hours * 60 / step_minutes)
    for _ in range(steps):
        t_cur = t_prev + step
        a_cur = altitude_fn(t_cur) - threshold
        if (a_prev < 0) != (a_cur < 0):
            lo, hi, a_lo = t_prev, t_cur, a_prev
            for _ in range(8):  # bisection down to ~2 seconds
                mid = lo + (hi - lo) / 2
                a_mid = altitude_fn(mid) - threshold
                if (a_mid < 0) == (a_lo < 0):
                    lo, a_lo = mid, a_mid
                else:
                    hi = mid
            events.append(("rise" if a_cur >= 0 else "set", lo + (hi - lo) / 2))
        t_prev, a_prev = t_cur, a_cur
    return events


SUN_HORIZON = -0.833
CIVIL_TWILIGHT = -6.0
NAUTICAL_TWILIGHT = -12.0
ASTRONOMICAL_TWILIGHT = -18.0


def sun_events(lat: float, lon: float, day_start: datetime) -> dict[str, datetime | None]:
    """Sunrise, sunset and twilight times within 24 h of ``day_start``."""
    fn = lambda t: sun_altitude(lat, lon, t)  # noqa: E731
    out: dict[str, datetime | None] = {
        "sunrise": None, "sunset": None, "dawn": None, "dusk": None,
        "astro_dawn": None, "astro_dusk": None,
    }
    for kind, when in find_crossings(fn, day_start, 24, SUN_HORIZON, 10):
        key = "sunrise" if kind == "rise" else "sunset"
        out[key] = out[key] or when
    for kind, when in find_crossings(fn, day_start, 24, CIVIL_TWILIGHT, 10):
        key = "dawn" if kind == "rise" else "dusk"
        out[key] = out[key] or when
    for kind, when in find_crossings(fn, day_start, 24, ASTRONOMICAL_TWILIGHT, 10):
        key = "astro_dawn" if kind == "rise" else "astro_dusk"
        out[key] = out[key] or when
    return out


def moon_events(lat: float, lon: float, day_start: datetime) -> dict[str, datetime | None]:
    fn = lambda t: moon_altaz(lat, lon, t)[0]  # noqa: E731
    out: dict[str, datetime | None] = {"moonrise": None, "moonset": None}
    for kind, when in find_crossings(fn, day_start, 25, SUN_HORIZON, 10):
        key = "moonrise" if kind == "rise" else "moonset"
        out[key] = out[key] or when
    return out
