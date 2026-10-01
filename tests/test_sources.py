"""Source-module tests against realistic mocked API payloads."""

from __future__ import annotations

from unittest.mock import patch

from mission_control.sources import iss, launches, local_weather, neo, photos, space_weather


def test_get_iss_position() -> None:
    with patch("mission_control.sources.iss.get_json", return_value={
        "latitude": 10.0, "longitude": 20.0, "altitude": 420.0, "velocity": 27600.0,
        "visibility": "daylight", "timestamp": 1700000000,
    }):
        pos = iss.get_iss_position()
        assert pos.latitude == 10.0
        assert pos.velocity_kmh == 27600.0


def test_get_upcoming_launches() -> None:
    payload = {"results": [{
        "name": "Test Launch", "net": "2026-10-01T10:00:00Z", "status": {"name": "Go"},
        "launch_service_provider": {"name": "SpaceX"},
        "rocket": {"configuration": {"full_name": "Falcon 9"}},
        "pad": {"name": "SLC-40", "location": {"name": "Cape Canaveral"}},
    }]}
    with patch("mission_control.sources.launches.get_json", return_value=payload):
        result = launches.get_upcoming_launches()
        assert result[0].provider == "SpaceX"


def test_get_close_approaches_handles_non_iso_full_date() -> None:
    payload = {"near_earth_objects": {"2026-09-28": [{
        "name": "Rock", "estimated_diameter": {"meters": {"estimated_diameter_min": 1, "estimated_diameter_max": 2}},
        "is_potentially_hazardous_asteroid": False,
        "close_approach_data": [{"close_approach_date": "2026-09-28",
                                 "close_approach_date_full": "2026-Sep-28 09:26",
                                 "relative_velocity": {"kilometers_per_hour": "1000"},
                                 "miss_distance": {"kilometers": "100", "lunar": "0.1"}}],
    }]}}
    with patch("mission_control.sources.neo.get_json", return_value=payload):
        result = neo.get_close_approaches("DEMO_KEY")
        assert result[0].name == "Rock"


def test_get_space_weather_degrades_on_partial_failure() -> None:
    from mission_control.errors import DataUnavailableError
    with patch("mission_control.sources.space_weather.get_json",
              side_effect=[DataUnavailableError("down"), {"0": {"G": {"Scale": "2"}}}]):
        weather = space_weather.get_space_weather()
        assert weather.kp_index is None
        assert weather.geomagnetic_storm_scale == "G2"


def test_get_apod() -> None:
    payload = {"title": "Nebula", "explanation": "x", "date": "2026-09-28",
              "media_type": "image", "url": "x.jpg"}
    with patch("mission_control.sources.photos.get_json", return_value=payload):
        apod = photos.get_apod("DEMO_KEY")
        assert apod.title == "Nebula"


def test_get_local_weather() -> None:
    payload = {
        "current": {"temperature_2m": 30.0, "relative_humidity_2m": 40, "apparent_temperature": 31.0,
                    "is_day": 1, "weather_code": 1, "wind_speed_10m": 10.0, "wind_direction_10m": 180},
        "daily": {"sunrise": ["2026-09-28T01:15"], "sunset": ["2026-09-28T13:05"],
                 "temperature_2m_max": [35.0], "temperature_2m_min": [20.0], "uv_index_max": [7.0]},
    }
    with patch("mission_control.sources.local_weather.get_json", return_value=payload):
        weather = local_weather.get_local_weather(33.68, 73.05, "Islamabad, Pakistan")
        assert weather.temperature_c == 30.0
        assert weather.location_label == "Islamabad, Pakistan"
