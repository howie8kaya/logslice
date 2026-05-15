"""Threshold alerting: flag entries when a level exceeds a count within a time window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class ThresholdAlert:
    level: str
    count: int
    window_start: datetime
    window_end: datetime
    entries: List[LogEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "count": self.count,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "lines": [e.line_number for e in self.entries],
        }


def check_threshold(
    entries: List[LogEntry],
    level: str,
    max_count: int,
    window_seconds: int = 60,
) -> List[ThresholdAlert]:
    """Slide a time window over timestamped entries and return alerts where
    *level* appears more than *max_count* times within *window_seconds*."""

    level_upper = level.upper()
    candidates = [
        e for e in entries
        if e.timestamp is not None and (e.level or "").upper() == level_upper
    ]

    if not candidates:
        return []

    candidates.sort(key=lambda e: e.timestamp)  # type: ignore[arg-type]
    window = timedelta(seconds=window_seconds)
    alerts: List[ThresholdAlert] = []
    seen_starts: set = set()

    for i, anchor in enumerate(candidates):
        win_end = anchor.timestamp + window  # type: ignore[operator]
        bucket = [e for e in candidates[i:] if e.timestamp <= win_end]  # type: ignore[operator]
        if len(bucket) > max_count:
            key = anchor.timestamp
            if key not in seen_starts:
                seen_starts.add(key)
                alerts.append(
                    ThresholdAlert(
                        level=level_upper,
                        count=len(bucket),
                        window_start=anchor.timestamp,  # type: ignore[arg-type]
                        window_end=win_end,
                        entries=bucket,
                    )
                )

    return alerts
