"""Formatting and estimate helpers for printer state."""

from __future__ import annotations


def duration_hms(seconds: float | int | None) -> str | None:
    if seconds is None or seconds < 0:
        return None
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def remaining_seconds(elapsed_seconds: float | int | None, progress: float | int | None) -> float | None:
    if elapsed_seconds is None or progress is None or not 0 < progress < 1:
        return None
    return max(0.0, float(elapsed_seconds) * (1 - float(progress)) / float(progress))
