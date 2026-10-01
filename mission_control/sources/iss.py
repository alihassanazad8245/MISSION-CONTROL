"""ISS position via wheretheiss.at (free, no key, generous rate limit)."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import ISS_POSITION_URL
from ..errors import DataUnavailableError
from ..models import IssPosition
from .base import get_json


def get_iss_position() -> IssPosition:
    data = get_json(ISS_POSITION_URL)
    try:
        return IssPosition(
            latitude=float(data["latitude"]), longitude=float(data["longitude"]),
            altitude_km=float(data["altitude"]), velocity_kmh=float(data["velocity"]),
            visibility=data.get("visibility", "unknown"),
            timestamp=datetime.fromtimestamp(data["timestamp"], tz=timezone.utc),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DataUnavailableError("Unexpected ISS position response format.") from exc
