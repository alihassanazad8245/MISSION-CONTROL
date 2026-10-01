"""Exception types used across the dashboard."""

from __future__ import annotations


class MissionControlError(Exception):
    """Base class for all expected, user-facing errors."""

    def __init__(self, message: str, hints: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.message = message
        self.hints = hints


class DataUnavailableError(MissionControlError):
    """Raised when a data source can't be reached or returns bad data.

    Every panel catches this on its own - one source being down never takes
    the rest of the dashboard with it.
    """


class InvalidLocationError(MissionControlError):
    """Raised when a latitude/longitude pair is invalid."""
