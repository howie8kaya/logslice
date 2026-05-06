"""Compute summary statistics over a collection of LogEntry objects."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class LogStats:
    total: int = 0
    by_level: Dict[str, int] = field(default_factory=dict)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    top_patterns: List[tuple] = field(default_factory=list)  # [(word, count), ...]

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "by_level": self.by_level,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "top_patterns": [
                {"word": w, "count": c} for w, c in self.top_patterns
            ],
        }


def compute_stats(entries: List[LogEntry], top_n: int = 5) -> LogStats:
    """Return a LogStats summary for *entries*."""
    if not entries:
        return LogStats()

    stats = LogStats(total=len(entries))

    # Level distribution
    level_counter: Counter = Counter()
    for entry in entries:
        lvl = (entry.level or "UNKNOWN").upper()
        level_counter[lvl] += 1
    stats.by_level = dict(level_counter.most_common())

    # Timestamp range — use only entries that have a timestamp
    timestamps = [
        entry.timestamp for entry in entries if entry.timestamp is not None
    ]
    if timestamps:
        stats.first_timestamp = min(timestamps)
        stats.last_timestamp = max(timestamps)

    # Top words across all raw lines (simple tokenisation)
    word_counter: Counter = Counter()
    for entry in entries:
        for word in entry.raw.split():
            clean = word.strip("[]():,;.").lower()
            if len(clean) > 3:
                word_counter[clean] += 1
    stats.top_patterns = word_counter.most_common(top_n)

    return stats
