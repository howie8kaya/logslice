"""Random sampling of log entries with optional seed for reproducibility."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class SampleResult:
    total: int
    sampled: int
    entries: List[LogEntry]

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "sampled": self.sampled,
            "entries": [e.to_dict() for e in self.entries],
        }


def sample_entries(
    entries: List[LogEntry],
    n: Optional[int] = None,
    fraction: Optional[float] = None,
    seed: Optional[int] = None,
) -> SampleResult:
    """Return a random sample of log entries.

    Exactly one of *n* or *fraction* must be provided.
    If *seed* is given the selection is deterministic.
    """
    if n is None and fraction is None:
        raise ValueError("Provide either n or fraction.")
    if n is not None and fraction is not None:
        raise ValueError("Provide either n or fraction, not both.")

    total = len(entries)

    if fraction is not None:
        if not (0.0 < fraction <= 1.0):
            raise ValueError("fraction must be in the range (0, 1].")
        n = max(1, round(total * fraction))

    n = min(n, total)  # type: ignore[arg-type]

    rng = random.Random(seed)
    sampled = rng.sample(entries, n) if total > 0 else []

    return SampleResult(total=total, sampled=len(sampled), entries=sampled)
