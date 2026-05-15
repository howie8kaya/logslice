"""Timeline bucketing: group log entries into time buckets and count activity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.parser import LogEntry


VALID_BUCKETS = ("second", "minute", "hour", "day")


@dataclass
class TimelineBucket:
    timestamp: datetime
    count: int
    levels: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "count": self.count,
            "levels": dict(self.levels),
        }


def _floor_timestamp(dt: datetime, bucket: str) -> datetime:
    if bucket == "second":
        return dt.replace(microsecond=0)
    if bucket == "minute":
        return dt.replace(second=0, microsecond=0)
    if bucket == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if bucket == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Invalid bucket size '{bucket}'. Choose from: {VALID_BUCKETS}")


def build_timeline(
    entries: List[LogEntry],
    bucket: str = "minute",
    fill_gaps: bool = False,
) -> List[TimelineBucket]:
    """Group entries by time bucket and return sorted timeline buckets."""
    if bucket not in VALID_BUCKETS:
        raise ValueError(f"Invalid bucket size '{bucket}'. Choose from: {VALID_BUCKETS}")

    buckets: Dict[datetime, TimelineBucket] = {}

    for entry in entries:
        if entry.timestamp is None:
            continue
        key = _floor_timestamp(entry.timestamp, bucket)
        if key not in buckets:
            buckets[key] = TimelineBucket(timestamp=key, count=0)
        buckets[key].count += 1
        if entry.level:
            lvl = entry.level.upper()
            buckets[key].levels[lvl] = buckets[key].levels.get(lvl, 0) + 1

    if not buckets:
        return []

    sorted_keys = sorted(buckets)
    if not fill_gaps or len(sorted_keys) < 2:
        return [buckets[k] for k in sorted_keys]

    # Fill missing intervals with zero-count buckets
    deltas = {"second": timedelta(seconds=1), "minute": timedelta(minutes=1),
              "hour": timedelta(hours=1), "day": timedelta(days=1)}
    step = deltas[bucket]
    result: List[TimelineBucket] = []
    current = sorted_keys[0]
    end = sorted_keys[-1]
    while current <= end:
        result.append(buckets.get(current, TimelineBucket(timestamp=current, count=0)))
        current += step
    return result
