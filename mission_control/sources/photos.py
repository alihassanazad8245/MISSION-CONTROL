"""Astronomy Picture of the Day, and today's full-disc Earth photo (EPIC)."""

from __future__ import annotations

from ..config import NASA_APOD_URL, NASA_EPIC_ARCHIVE, NASA_EPIC_URL
from ..errors import DataUnavailableError
from ..models import ApodEntry, EarthImage
from .base import get_json


def get_apod(nasa_api_key: str) -> ApodEntry:
    data = get_json(NASA_APOD_URL, params={"api_key": nasa_api_key})
    try:
        return ApodEntry(
            title=data.get("title", "Untitled"), explanation=data.get("explanation", ""),
            date=data.get("date", ""), media_type=data.get("media_type", "image"),
            url=data.get("url", ""), copyright=(data.get("copyright") or "").strip(),
        )
    except (KeyError, TypeError) as exc:
        raise DataUnavailableError("Unexpected APOD response format.") from exc


def get_latest_earth_image(nasa_api_key: str) -> EarthImage:
    """The most recent full-disc natural-colour photo of Earth from DSCOVR/EPIC."""
    data = get_json(NASA_EPIC_URL, params={"api_key": nasa_api_key})
    if not isinstance(data, list) or not data:
        raise DataUnavailableError("No EPIC Earth images are available right now.")
    latest = data[-1]
    try:
        image_name = latest["image"]
        date_full = latest["date"]  # "YYYY-MM-DD HH:MM:SS"
        y, m, d = date_full.split(" ")[0].split("-")
        url = f"{NASA_EPIC_ARCHIVE}/{y}/{m}/{d}/png/{image_name}.png"
        return EarthImage(caption=latest.get("caption", "Earth, seen from DSCOVR"),
                          date=date_full, image_url=url)
    except (KeyError, ValueError, IndexError) as exc:
        raise DataUnavailableError("Unexpected EPIC response format.") from exc
