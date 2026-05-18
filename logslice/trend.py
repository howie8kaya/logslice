"""Trend analysis: compute rate-of-change across time buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class TrendPoint:
    bucket: str
    count: int
    delta: Optional[int]       # change vs previous bucket (None for first)
    delta_pct: Optional[float] # percentage change vs previous bucket

    def as_dict(self) -> dict:
        return {
            "bucket": self.bucket,
            "count": self.count,
            "delta": self.delta,
            "delta_pct": round(self.delta_pct, 2) if self.delta_pct is not None else None,
        }


@dataclass
class TrendReport:
    resolution: str
    level_filter: Optional[str]
    points: List[TrendPoint] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "resolution": self.resolution,
            "level_filter": self.level_filter,
            "points": [p.as_dict() for p in self.points],
        }


def _floor_ts(ts: datetime, resolution: str) -> str:
    if resolution == "minute":
        return ts.strftime("%Y-%m-%dT%H:%M")
    if resolution == "hour":
        return ts.strftime("%Y-%m-%dT%H")
    if resolution == "day":
        return ts.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown resolution: {resolution!r}")


def compute_trend(
    entries: List[LogEntry],
    resolution: str = "minute",
    level: Optional[str] = None,
) -> TrendReport:
    """Bucket entries by time resolution and compute deltas between buckets."""
    buckets: dict[str, int] = {}
    for entry in entries:
        if entry.timestamp is None:
            continue
        if level and (entry.level or "").upper() != level.upper():
            continue
        key = _floor_ts(entry.timestamp, resolution)
        buckets[key] = buckets.get(key, 0) + 1

    sorted_keys = sorted(buckets)
    points: List[TrendPoint] = []
    prev: Optional[int] = None
    for key in sorted_keys:
        count = buckets[key]
        if prev is None:
            delta, delta_pct = None, None
        else:
            delta = count - prev
            delta_pct = (delta / prev * 100.0) if prev != 0 else None
        points.append(TrendPoint(bucket=key, count=count, delta=delta, delta_pct=delta_pct))
        prev = count

    return TrendReport(resolution=resolution, level_filter=level, points=points)
