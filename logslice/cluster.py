"""Cluster similar log entries by message pattern similarity."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from logslice.parser import LogEntry


_TOKEN_RE = re.compile(r"\b(?:\d+\.\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}|[0-9a-fA-F]{8,}|\d+)\b")


@dataclass
class Cluster:
    pattern: str
    entries: List[LogEntry] = field(default_factory=list)
    count: int = 0

    def as_dict(self) -> Dict:
        return {
            "pattern": self.pattern,
            "count": self.count,
            "sample": self.entries[0].raw if self.entries else "",
        }


def _signature(text: str) -> str:
    """Replace variable tokens with a placeholder to form a stable signature."""
    return _TOKEN_RE.sub("<VAR>", text).strip()


def cluster_entries(
    entries: List[LogEntry],
    min_count: int = 1,
    use_level: bool = True,
) -> List[Cluster]:
    """Group entries by message signature.

    Args:
        entries: Parsed log entries to cluster.
        min_count: Only return clusters with at least this many entries.
        use_level: Include the log level in the signature key when True.

    Returns:
        List of Cluster objects sorted by count descending.
    """
    buckets: Dict[str, Cluster] = defaultdict(lambda: Cluster(pattern=""))

    for entry in entries:
        sig = _signature(entry.raw)
        if use_level and entry.level:
            key = f"[{entry.level.upper()}] {sig}"
        else:
            key = sig

        if buckets[key].pattern == "":
            buckets[key].pattern = key
        buckets[key].entries.append(entry)
        buckets[key].count += 1

    result = [c for c in buckets.values() if c.count >= min_count]
    result.sort(key=lambda c: c.count, reverse=True)
    return result
