"""Summary report generation for log entries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class SummaryReport:
    total: int = 0
    unique_levels: List[str] = field(default_factory=list)
    level_counts: dict = field(default_factory=dict)
    top_patterns: List[tuple] = field(default_factory=list)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    error_rate: float = 0.0

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "unique_levels": self.unique_levels,
            "level_counts": self.level_counts,
            "top_patterns": [
                {"pattern": p, "count": c} for p, c in self.top_patterns
            ],
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "error_rate": round(self.error_rate, 4),
        }


def _extract_message_prefix(raw: str, words: int = 4) -> str:
    """Return first N words of a line as a rough pattern key."""
    tokens = raw.strip().split()
    return " ".join(tokens[:words]) if tokens else raw


def generate_summary(
    entries: List[LogEntry],
    top_n: int = 5,
    prefix_words: int = 4,
) -> SummaryReport:
    """Generate a summary report from a list of log entries."""
    if not entries:
        return SummaryReport()

    level_counter: Counter = Counter()
    pattern_counter: Counter = Counter()
    timestamps = []

    for entry in entries:
        level = (entry.level or "UNKNOWN").upper()
        level_counter[level] += 1
        pattern_counter[_extract_message_prefix(entry.raw, prefix_words)] += 1
        if entry.timestamp is not None:
            timestamps.append(entry.timestamp)

    total = len(entries)
    error_count = sum(
        v for k, v in level_counter.items() if k in ("ERROR", "CRITICAL", "FATAL")
    )

    return SummaryReport(
        total=total,
        unique_levels=sorted(level_counter.keys()),
        level_counts=dict(level_counter),
        top_patterns=pattern_counter.most_common(top_n),
        first_timestamp=str(min(timestamps)) if timestamps else None,
        last_timestamp=str(max(timestamps)) if timestamps else None,
        error_rate=error_count / total if total else 0.0,
    )
