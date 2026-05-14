"""Pivot log entries by a field (e.g. level, source) and count occurrences per time bucket."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class PivotTable:
    bucket_size: str  # 'minute', 'hour', 'day'
    pivot_field: str  # 'level' or any extra key
    buckets: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "bucket_size": self.bucket_size,
            "pivot_field": self.pivot_field,
            "buckets": self.buckets,
        }


def _truncate(ts: datetime, bucket_size: str) -> str:
    """Return a string key for the time bucket containing *ts*."""
    if bucket_size == "minute":
        return ts.strftime("%Y-%m-%d %H:%M")
    if bucket_size == "hour":
        return ts.strftime("%Y-%m-%d %H")
    if bucket_size == "day":
        return ts.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown bucket_size: {bucket_size!r}")


def _get_pivot_value(entry: LogEntry, pivot_field: str) -> str:
    """Extract the pivot value from a LogEntry."""
    if pivot_field == "level":
        return entry.level or "UNKNOWN"
    return str(entry.extra.get(pivot_field, "UNKNOWN"))


def pivot_entries(
    entries: List[LogEntry],
    pivot_field: str = "level",
    bucket_size: str = "hour",
) -> PivotTable:
    """Build a PivotTable from *entries*.

    Entries without a timestamp are placed in the ``"(no timestamp)"`` bucket.
    """
    table = PivotTable(bucket_size=bucket_size, pivot_field=pivot_field)
    buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for entry in entries:
        bucket_key = (
            _truncate(entry.timestamp, bucket_size)
            if entry.timestamp
            else "(no timestamp)"
        )
        pivot_value = _get_pivot_value(entry, pivot_field)
        buckets[bucket_key][pivot_value] += 1

    # Convert inner defaultdicts to plain dicts for clean serialisation
    table.buckets = {k: dict(v) for k, v in sorted(buckets.items())}
    return table
