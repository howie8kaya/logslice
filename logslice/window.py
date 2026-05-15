"""Sliding window aggregation over log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class WindowBucket:
    start: datetime
    end: datetime
    entries: List[LogEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    def as_dict(self) -> dict:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "count": self.count,
            "levels": _level_counts(self.entries),
        }


def _level_counts(entries: List[LogEntry]) -> dict:
    counts: dict = {}
    for e in entries:
        lvl = (e.level or "UNKNOWN").upper()
        counts[lvl] = counts.get(lvl, 0) + 1
    return counts


def sliding_window(
    entries: List[LogEntry],
    window_seconds: int = 60,
    step_seconds: Optional[int] = None,
) -> List[WindowBucket]:
    """Aggregate entries into overlapping sliding windows.

    Args:
        entries: Log entries to aggregate (must have timestamps).
        window_seconds: Width of each window in seconds.
        step_seconds: Step between window starts. Defaults to window_seconds
                      (tumbling/non-overlapping windows).

    Returns:
        List of WindowBucket objects ordered by start time.
    """
    if step_seconds is None:
        step_seconds = window_seconds

    timed = [e for e in entries if e.timestamp is not None]
    if not timed:
        return []

    timed_sorted = sorted(timed, key=lambda e: e.timestamp)  # type: ignore[arg-type]
    first_ts: datetime = timed_sorted[0].timestamp  # type: ignore[assignment]
    last_ts: datetime = timed_sorted[-1].timestamp  # type: ignore[assignment]

    window_delta = timedelta(seconds=window_seconds)
    step_delta = timedelta(seconds=step_seconds)

    buckets: List[WindowBucket] = []
    current_start = first_ts

    while current_start <= last_ts:
        current_end = current_start + window_delta
        bucket = WindowBucket(start=current_start, end=current_end)
        for e in timed_sorted:
            ts: datetime = e.timestamp  # type: ignore[assignment]
            if current_start <= ts < current_end:
                bucket.entries.append(e)
        buckets.append(bucket)
        current_start += step_delta

    return buckets
