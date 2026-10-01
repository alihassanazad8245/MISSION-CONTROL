"""Near-Earth object close approaches via NASA NeoWs."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import NASA_NEO_FEED_URL
from ..models import CloseApproach
from .base import get_json


def get_close_approaches(nasa_api_key: str, date: datetime | None = None) -> list[CloseApproach]:
    target = (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    data = get_json(NASA_NEO_FEED_URL, params={
        "start_date": target, "end_date": target, "api_key": nasa_api_key,
    })
    approaches: list[CloseApproach] = []
    for day_items in data.get("near_earth_objects", {}).values():
        for item in day_items:
            try:
                diameter = item.get("estimated_diameter", {}).get("meters", {})
                approach_data = (item.get("close_approach_data") or [{}])[0]
                velocity = approach_data.get("relative_velocity", {})
                miss = approach_data.get("miss_distance", {})
                # "close_approach_date_full" uses a non-ISO format
                # (e.g. "2026-Sep-27 09:26") - stick to the reliable ISO date.
                approach_date = approach_data.get("close_approach_date", target)
                approaches.append(CloseApproach(
                    name=item.get("name", "Unknown object"),
                    close_approach_time=datetime.fromisoformat(approach_date + "T00:00:00+00:00"),
                    velocity_kmh=float(velocity.get("kilometers_per_hour", 0)),
                    miss_distance_km=float(miss.get("kilometers", 0)),
                    miss_distance_lunar=float(miss.get("lunar", 0)),
                    diameter_min_m=float(diameter.get("estimated_diameter_min", 0)),
                    diameter_max_m=float(diameter.get("estimated_diameter_max", 0)),
                    is_hazardous=bool(item.get("is_potentially_hazardous_asteroid")),
                ))
            except (KeyError, ValueError, IndexError):
                continue
    approaches.sort(key=lambda a: a.miss_distance_km)
    return approaches
