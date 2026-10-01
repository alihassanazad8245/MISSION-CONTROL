"""Core astronomy and rendering sanity checks (real math, no network)."""

from __future__ import annotations

from datetime import datetime, timezone

from mission_control.astro.kepler import heliocentric_longitude
from mission_control.astro.sun_moon import moon_elongation, moon_illumination, phase_name, sun_altitude
from mission_control.astro.timeutil import julian_date, to_pkt
from mission_control.mapping_compat import format_duration
from mission_control.render.moonphase import render_moon
from mission_control.render.orbits import render_orbits
from mission_control.render.worldmap import is_land, render_map


def test_julian_date_known_epoch() -> None:
    # J2000.0 epoch is exactly JD 2451545.0.
    assert abs(julian_date(datetime(2000, 1, 1, 12, tzinfo=timezone.utc)) - 2451545.0) < 1e-6


def test_to_pkt_is_utc_plus_five() -> None:
    utc = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    pkt = to_pkt(utc)
    assert pkt.hour == 15


def test_sun_altitude_is_higher_at_noon_than_midnight() -> None:
    day = datetime(2026, 6, 21, tzinfo=timezone.utc)
    noon = sun_altitude(33.68, 73.05, day.replace(hour=7))   # ~noon in PKT (UTC+5)
    midnight = sun_altitude(33.68, 73.05, day.replace(hour=19))
    assert noon > midnight


def test_moon_phase_name_covers_full_range() -> None:
    names = {phase_name(e) for e in range(0, 360, 15)}
    assert "New Moon" in names
    assert "Full Moon" in names
    assert "First Quarter" in names
    assert "Last Quarter" in names


def test_moon_illumination_is_bounded() -> None:
    jd = julian_date(datetime.now(timezone.utc))
    illum = moon_illumination(jd)
    assert 0.0 <= illum <= 1.0


def test_heliocentric_longitude_is_an_angle() -> None:
    jd = julian_date(datetime.now(timezone.utc))
    for planet in ("Mercury", "Venus", "Earth", "Mars", "Jupiter"):
        lon = heliocentric_longitude(planet, jd)
        assert 0.0 <= lon < 360.0


def test_format_duration_days_hours_minutes() -> None:
    assert format_duration(90061) == "1d 1h 1m"
    assert format_duration(3661) == "1h 1m 1s"
    assert format_duration(45) == "0m 45s"


def test_is_land_recognises_known_points() -> None:
    assert is_land(33.68, 73.05)    # Islamabad
    assert not is_land(0, -140)     # mid-Pacific Ocean


def test_render_map_places_marker() -> None:
    lines = render_map(40, 16, markers={"X": (33.68, 73.05)})
    assert any("X" in line for line in lines)
    assert len(lines) == 16


def test_render_moon_produces_output() -> None:
    art = render_moon(0.5, True, 10)
    assert art.plain.count("\n") == 10


def test_render_orbits_places_the_sun() -> None:
    diagram = render_orbits(datetime.now(timezone.utc), 88, 32)
    assert "\u2600" in diagram.plain
