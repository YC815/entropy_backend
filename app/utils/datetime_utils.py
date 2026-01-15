"""Datetime helpers for deadline normalization.

All inputs are normalized relative to the configured timezone (default: Asia/Taipei)
then stored in UTC with minute precision and without seconds/micros.
"""
from __future__ import annotations

from datetime import datetime, date, time, timezone
import pytz

from app.core.config import settings


DEFAULT_TIME = time(hour=23, minute=59)


def _ensure_timezone(dt: datetime, tz_name: str):
    tz = pytz.timezone(tz_name)
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt.astimezone(tz)


def normalize_deadline_input(value):
    """
    Normalize incoming deadline values to UTC with minute precision.

    Rules:
    - None -> None
    - Date-only -> 23:59 in settings.TZ
    - Naive datetime -> interpret as settings.TZ
    - Aware datetime -> convert from its tz to settings.TZ first
    - Seconds/micros are dropped
    """
    if value is None:
        return None

    tz_name = settings.TZ or "Asia/Taipei"

    # Parse strings and date objects
    if isinstance(value, str):
        normalized_str = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized_str)
        except ValueError as e:
            raise ValueError(f"Invalid deadline format: {value}") from e
        if isinstance(parsed, datetime):
            value = parsed
        elif isinstance(parsed, date):  # type: ignore[unreachable]
            value = datetime.combine(parsed, DEFAULT_TIME)
        else:
            raise ValueError("Unsupported deadline value")

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, DEFAULT_TIME)

    if not isinstance(value, datetime):
        raise ValueError("Unsupported deadline type")

    localized = _ensure_timezone(value, tz_name)
    trimmed = localized.replace(second=0, microsecond=0)
    return trimmed.astimezone(timezone.utc)


def serialize_deadline(dt: datetime | None):
    if dt is None:
        return None
    # Always emit UTC ISO string
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
