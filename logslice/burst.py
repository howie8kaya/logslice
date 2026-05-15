"""Burst detection: identify time windows with abnormally high log volume."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class BurstWindow:
    start: datetime
    end: datetime
    count: int
    entries: List[LogEntry] = field(default_factory=list, repr=False)

    def as_dict(self) -> dict:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "count": self.count,
            "duration_seconds": (self.end - self.start).total_seconds(),
        }


def detect_bursts(
    entries: List[LogEntry],
    window_seconds: int = 60,
    threshold: int = 10,
) -> List[BurstWindow]:
    """Return windows where entry count exceeds *threshold* within *window_seconds*.

    Uses a sliding window over timestamped entries.  Entries without a
    timestamp are silently skipped.
    """
    timestamped = [e for e in entries if e.timestamp is not None]
    if not timestamped:
        return []

    timestamped = sorted(timestamped, key=lambda e: e.timestamp)  # type: ignore[arg-type]
    delta = timedelta(seconds=window_seconds)

    bursts: List[BurstWindow] = []
    left = 0

    for right in range(len(timestamped)):
        right_ts: datetime = timestamped[right].timestamp  # type: ignore[assignment]

        # Advance left pointer so window fits within delta
        while timestamped[left].timestamp < right_ts - delta:  # type: ignore[operator]
            left += 1

        window_entries = timestamped[left : right + 1]
        if len(window_entries) >= threshold:
            start_ts: datetime = window_entries[0].timestamp  # type: ignore[assignment]
            # Avoid emitting overlapping burst windows — only emit when the
            # right edge advances past the last recorded burst end.
            if bursts and right_ts <= bursts[-1].end:
                # Extend existing burst if it grew
                if len(window_entries) > bursts[-1].count:
                    bursts[-1] = BurstWindow(
                        start=start_ts,
                        end=right_ts,
                        count=len(window_entries),
                        entries=list(window_entries),
                    )
            else:
                bursts.append(
                    BurstWindow(
                        start=start_ts,
                        end=right_ts,
                        count=len(window_entries),
                        entries=list(window_entries),
                    )
                )

    return bursts
