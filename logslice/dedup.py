"""Deduplication utilities for log entries."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import List, Optional

from logslice.parser import LogEntry


def _normalize(text: str, ignore_numbers: bool = True) -> str:
    """Return a normalized version of *text* used as a dedup key."""
    if ignore_numbers:
        text = re.sub(r"\b\d+\b", "<N>", text)
    return text.strip().lower()


def dedup_entries(
    entries: List[LogEntry],
    *,
    ignore_numbers: bool = True,
    keep: str = "first",
) -> List[LogEntry]:
    """Remove duplicate log entries based on normalised raw text.

    Args:
        entries: Sequence of :class:`LogEntry` objects to deduplicate.
        ignore_numbers: When *True* numeric tokens are replaced before
            comparing, so ``timeout after 3s`` and ``timeout after 7s``
            are treated as the same message.
        keep: Either ``"first"`` (default) or ``"last"`` — which
            occurrence to retain when duplicates are found.

    Returns:
        A new list with duplicates removed, preserving original order of
        the kept entries.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    seen: dict[str, int] = {}  # key -> index in *result*
    result: List[Optional[LogEntry]] = []

    for entry in entries:
        key = _normalize(entry.raw, ignore_numbers=ignore_numbers)
        if key in seen:
            if keep == "last":
                result[seen[key]] = None  # mark old slot as removed
                seen[key] = len(result)
                result.append(entry)
        else:
            seen[key] = len(result)
            result.append(entry)

    return [e for e in result if e is not None]


def count_duplicates(
    entries: List[LogEntry],
    *,
    ignore_numbers: bool = True,
) -> dict[str, int]:
    """Return a mapping of normalised message -> occurrence count."""
    counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        key = _normalize(entry.raw, ignore_numbers=ignore_numbers)
        counts[key] += 1
    return dict(counts)
