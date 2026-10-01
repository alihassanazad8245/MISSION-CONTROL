"""Shared HTTP GET helper for every data source."""

from __future__ import annotations

from typing import Any

import requests

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..errors import DataUnavailableError

_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return _session


def close_session() -> None:
    global _session
    if _session is not None:
        _session.close()
        _session = None


def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """GET a URL and return its parsed JSON, mapping every failure mode to
    :class:`DataUnavailableError` so callers never see a raw requests
    exception."""
    session = _get_session()
    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise DataUnavailableError(f"Timed out reaching {url}") from exc
    except requests.exceptions.ConnectionError as exc:
        raise DataUnavailableError(f"Could not connect to {url}") from exc
    except requests.exceptions.RequestException as exc:  # pragma: no cover
        raise DataUnavailableError(f"Request failed: {exc}") from exc

    if response.status_code == 429:
        raise DataUnavailableError("Rate limited - try again in a few minutes.",
                                   hints=("This source has a low free-tier request limit",))
    if response.status_code >= 400:
        raise DataUnavailableError(f"Server returned {response.status_code} for {url}")

    try:
        return response.json()
    except ValueError as exc:
        raise DataUnavailableError(f"Malformed response from {url}") from exc
