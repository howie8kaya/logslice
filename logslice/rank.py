"""Rank log entries by frequency of occurrence or error weight."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class RankedEntry:
    raw: str
    count: int
    level: Optional[str]
    example: LogEntry

    def as_dict(self) -> dict:
        return {
            "raw": self.raw,
            "count": self.count,
            "level": self.level,
            "example_line": self.example.line_number,
        }


_LEVEL_WEIGHT: dict[str, int] = {
    "critical": 5,
    "fatal": 5,
    "error": 4,
    "warning": 3,
    "warn": 3,
    "info": 2,
    "debug": 1,
}


def _message_key(entry: LogEntry) -> str:
    """Return a normalised key for grouping similar messages."""
    text = entry.raw.strip()
    # strip leading timestamp-like prefix (digits, colons, dashes, spaces)
    import re
    text = re.sub(r'^[\d\-T:.Z\s]+', '', text).strip()
    return text


def rank_entries(
    entries: List[LogEntry],
    top_n: int = 10,
    by: str = "count",
) -> List[RankedEntry]:
    """Rank entries by frequency ('count') or weighted severity ('weight').

    Args:
        entries: Parsed log entries to rank.
        top_n: Maximum number of results to return.
        by: Ranking strategy — 'count' or 'weight'.

    Returns:
        List of RankedEntry sorted descending by the chosen metric.
    """
    if by not in ("count", "weight"):
        raise ValueError(f"Unknown ranking strategy: {by!r}. Use 'count' or 'weight'.")

    groups: dict[str, list[LogEntry]] = {}
    for entry in entries:
        key = _message_key(entry)
        groups.setdefault(key, []).append(entry)

    ranked: list[RankedEntry] = []
    for key, group in groups.items():
        example = group[0]
        count = len(group)
        level = (example.level or "").lower()
        ranked.append(RankedEntry(raw=key, count=count, level=example.level, example=example))

    if by == "weight":
        ranked.sort(
            key=lambda r: _LEVEL_WEIGHT.get((r.level or "").lower(), 0) * r.count,
            reverse=True,
        )
    else:
        ranked.sort(key=lambda r: r.count, reverse=True)

    return ranked[:top_n]
