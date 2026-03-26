"""Shared helpers for person-like schemas."""
from typing import Optional


def split_full_name(full_name: str) -> tuple[Optional[str], Optional[str]]:
    """Split a full name into first/last parts."""
    parts = [part for part in full_name.strip().split() if part]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])
