"""UTC time helpers for current naive datetime columns."""
from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return a naive UTC datetime compatible with existing DB columns."""
    return datetime.now(UTC).replace(tzinfo=None)
