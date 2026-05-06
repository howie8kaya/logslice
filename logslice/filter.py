"""Filter utilities for log entries based on time range and severity level."""

from datetime import datetime
from typing import List, Optional
from logslice.parser import LogEntry

LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def filter_by_time_range(
    entries: List[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    time_field: str = "timestamp",
) -> List[LogEntry]:
    """Filter entries whose named group `time_field` falls within [start, end]."""
    result = []
    for entry in entries:
        raw_ts = entry.groups.get(time_field)
        if raw_ts is None:
            result.append(entry)
            continue
        try:
            ts = datetime.fromisoformat(raw_ts)
        except ValueError:
            result.append(entry)
            continue
        if start and ts < start:
            continue
        if end and ts > end:
            continue
        result.append(entry)
    return result


def filter_by_level(
    entries: List[LogEntry],
    min_level: Optional[str] = None,
    level_field: str = "level",
) -> List[LogEntry]:
    """Keep entries whose log level is >= min_level (case-insensitive)."""
    if min_level is None:
        return entries

    min_upper = min_level.upper()
    if min_upper not in LEVEL_ORDER:
        raise ValueError(f"Unknown log level: {min_level!r}. Choose from {LEVEL_ORDER}")

    min_idx = LEVEL_ORDER.index(min_upper)
    result = []
    for entry in entries:
        lvl = entry.groups.get(level_field, "").upper()
        if lvl not in LEVEL_ORDER:
            result.append(entry)
            continue
        if LEVEL_ORDER.index(lvl) >= min_idx:
            result.append(entry)
    return result


def apply_filters(
    entries: List[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_level: Optional[str] = None,
    time_field: str = "timestamp",
    level_field: str = "level",
) -> List[LogEntry]:
    """Convenience wrapper that applies time and level filters in sequence."""
    entries = filter_by_time_range(entries, start=start, end=end, time_field=time_field)
    entries = filter_by_level(entries, min_level=min_level, level_field=level_field)
    return entries
