"""Time helpers: Julian dates, sidereal time, and Pakistan Standard Time."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

#: Pakistan Standard Time (UTC+5, no daylight saving since 2009).
PKT = timezone(timedelta(hours=5), "PKT")

J2000 = 2451545.0


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_pkt(dt: datetime) -> datetime:
    """Convert any aware datetime to Pakistan Standard Time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PKT)


def julian_date(dt: datetime) -> float:
    """Julian Date (UT) for an aware datetime."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def from_julian_date(jd: float) -> datetime:
    """Inverse of :func:`julian_date` (returns an aware UTC datetime)."""
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=jd - J2000)


def centuries(jd: float) -> float:
    return (jd - J2000) / 36525.0


def gmst_deg(jd: float) -> float:
    """Greenwich mean sidereal time in degrees."""
    t = centuries(jd)
    g = (280.46061837 + 360.98564736629 * (jd - J2000)
         + 0.000387933 * t * t - t ** 3 / 38710000.0)
    return g % 360.0
