"""Cross-file log correlation: match entries across two log streams by time proximity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional, Tuple

from logslice.parser import LogEntry


@dataclass
class CorrelatedPair:
    left: LogEntry
    right: LogEntry
    delta_seconds: float

    def as_dict(self) -> dict:
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "delta_seconds": round(self.delta_seconds, 3),
        }


@dataclass
class CorrelationResult:
    pairs: List[CorrelatedPair] = field(default_factory=list)
    unmatched_left: List[LogEntry] = field(default_factory=list)
    unmatched_right: List[LogEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "pairs": [p.as_dict() for p in self.pairs],
            "unmatched_left": [e.to_dict() for e in self.unmatched_left],
            "unmatched_right": [e.to_dict() for e in self.unmatched_right],
        }


def correlate_entries(
    left: List[LogEntry],
    right: List[LogEntry],
    window_seconds: float = 1.0,
    match_level: bool = False,
) -> CorrelationResult:
    """Pair entries from two streams that fall within *window_seconds* of each other.

    Uses a greedy nearest-neighbour approach: each right entry is consumed at most once.
    Entries without timestamps are placed in the appropriate unmatched list.
    """
    window = timedelta(seconds=window_seconds)

    timestamped_left = [e for e in left if e.timestamp is not None]
    timestamped_right = [e for e in right if e.timestamp is not None]

    no_ts_left = [e for e in left if e.timestamp is None]
    no_ts_right = [e for e in right if e.timestamp is None]

    used_right: set[int] = set()
    pairs: List[CorrelatedPair] = []

    for le in sorted(timestamped_left, key=lambda e: e.timestamp):
        best_idx: Optional[int] = None
        best_delta: Optional[timedelta] = None

        for idx, re in enumerate(timestamped_right):
            if idx in used_right:
                continue
            if match_level and le.level != re.level:
                continue
            delta = abs(le.timestamp - re.timestamp)
            if delta <= window:
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best_idx = idx

        if best_idx is not None:
            used_right.add(best_idx)
            pairs.append(
                CorrelatedPair(
                    left=le,
                    right=timestamped_right[best_idx],
                    delta_seconds=best_delta.total_seconds(),
                )
            )
        else:
            no_ts_left.append(le)

    unmatched_right = [
        re for idx, re in enumerate(timestamped_right) if idx not in used_right
    ] + no_ts_right

    return CorrelationResult(
        pairs=pairs,
        unmatched_left=no_ts_left,
        unmatched_right=unmatched_right,
    )
