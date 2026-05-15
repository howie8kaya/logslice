"""Compute error/warning ratios and level proportions across log entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class LevelRatio:
    level: str
    count: int
    total: int

    @property
    def ratio(self) -> float:
        return self.count / self.total if self.total else 0.0

    @property
    def percent(self) -> float:
        return self.ratio * 100.0

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "count": self.count,
            "total": self.total,
            "ratio": round(self.ratio, 6),
            "percent": round(self.percent, 2),
        }


@dataclass
class RatioReport:
    total: int
    levels: List[LevelRatio] = field(default_factory=list)
    error_ratio: float = 0.0
    warn_ratio: float = 0.0

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "error_ratio": round(self.error_ratio, 6),
            "warn_ratio": round(self.warn_ratio, 6),
            "levels": [lr.as_dict() for lr in self.levels],
        }


def compute_ratio(entries: List[LogEntry]) -> RatioReport:
    """Compute per-level ratios for a list of log entries."""
    total = len(entries)
    if total == 0:
        return RatioReport(total=0)

    counts: Dict[str, int] = {}
    for entry in entries:
        lvl = (entry.level or "UNKNOWN").upper()
        counts[lvl] = counts.get(lvl, 0) + 1

    levels = [
        LevelRatio(level=lvl, count=cnt, total=total)
        for lvl, cnt in sorted(counts.items(), key=lambda x: -x[1])
    ]

    error_count = sum(cnt for lvl, cnt in counts.items() if lvl in ("ERROR", "CRITICAL", "FATAL"))
    warn_count = counts.get("WARNING", 0) + counts.get("WARN", 0)

    return RatioReport(
        total=total,
        levels=levels,
        error_ratio=error_count / total,
        warn_ratio=warn_count / total,
    )
