"""Command-line entry point: argument parsing, then launch the TUI."""

from __future__ import annotations

import argparse
import sys

from . import __app_name__, __version__
from .app.app import MissionControlApp
from .app.datahub import DataHub
from .config import resolve_nasa_api_key
from .errors import InvalidLocationError
from .settings import load_settings, save_settings

MIN_PYTHON = (3, 9)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mission-control",
        description=f"{__app_name__} \u2014 a live space operations dashboard, in your terminal.",
        epilog=(
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --location 24.86,67.00 --label \"Karachi\"\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--location", metavar="LAT,LON", help="observer location, e.g. 24.86,67.00")
    parser.add_argument("--label", metavar="NAME", default="", help="a friendly name for that location")
    parser.add_argument("--nasa-api-key", metavar="KEY",
                        help="NASA API key (default: DEMO_KEY, or $NASA_API_KEY)")
    parser.add_argument("--version", action="version", version=f"{__app_name__} {__version__}")
    return parser


def _parse_location(text: str) -> tuple[float, float]:
    try:
        lat_str, lon_str = text.split(",", 1)
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
    except ValueError as exc:
        raise InvalidLocationError(f"'{text}' is not a valid 'lat,lon' pair.") from exc
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise InvalidLocationError("Latitude must be -90..90 and longitude -180..180.")
    return lat, lon


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(p) for p in MIN_PYTHON)
        current = ".".join(str(p) for p in sys.version_info[:3])
        sys.stderr.write(f"[ERROR] {__app_name__} requires Python {required}+ (found {current}).\n")
        return 2

    args = build_parser().parse_args(argv)
    settings = load_settings()

    if args.location:
        try:
            lat, lon = _parse_location(args.location)
        except InvalidLocationError as exc:
            sys.stderr.write(f"[ERROR] {exc.message}\n")
            return 1
        settings.latitude, settings.longitude = lat, lon
        settings.location_label = args.label or f"{lat:.2f}, {lon:.2f}"
        save_settings(settings)

    hub = DataHub(
        nasa_api_key=resolve_nasa_api_key(args.nasa_api_key),
        latitude=settings.latitude, longitude=settings.longitude,
        location_label=settings.location_label,
    )
    app = MissionControlApp(hub)
    app.run()
    return 0
