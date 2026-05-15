"""Heatmap: count log entries by hour-of-day and day-of-week."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from logslice.parser import LogEntry

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = list(range(24))


@dataclass
class HeatmapCell:
    day: str
    hour: int
    count: int

    def as_dict(self) -> Dict:
        return {"day": self.day, "hour": self.hour, "count": self.count}


@dataclass
class Heatmap:
    """day -> hour -> count matrix."""
    cells: List[HeatmapCell] = field(default_factory=list)
    skipped: int = 0

    def as_dict(self) -> Dict:
        return {
            "cells": [c.as_dict() for c in self.cells],
            "skipped": self.skipped,
        }

    def grid(self) -> Dict[str, Dict[int, int]]:
        """Return nested dict[day][hour] = count for easy lookup."""
        result: Dict[str, Dict[int, int]] = {d: {h: 0 for h in HOURS} for d in DAYS}
        for cell in self.cells:
            result[cell.day][cell.hour] = cell.count
        return result


def build_heatmap(entries: List[LogEntry]) -> Heatmap:
    """Aggregate entries into a day-of-week x hour-of-day heatmap."""
    counts: Dict[str, Dict[int, int]] = {d: {h: 0 for h in HOURS} for d in DAYS}
    skipped = 0

    for entry in entries:
        if entry.timestamp is None:
            skipped += 1
            continue
        day = DAYS[entry.timestamp.weekday()]
        hour = entry.timestamp.hour
        counts[day][hour] += 1

    cells = [
        HeatmapCell(day=day, hour=hour, count=counts[day][hour])
        for day in DAYS
        for hour in HOURS
    ]
    return Heatmap(cells=cells, skipped=skipped)
