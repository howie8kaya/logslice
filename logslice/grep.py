"""Multi-pattern grep across log entries with match context and counts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from logslice.parser import LogEntry


@dataclass
class GrepResult:
    entry: LogEntry
    matched_patterns: List[str] = field(default_factory=list)
    match_count: int = 0

    def as_dict(self) -> dict:
        d = self.entry.to_dict()
        d["matched_patterns"] = self.matched_patterns
        d["match_count"] = self.match_count
        return d


def _compile_patterns(
    patterns: List[str], ignore_case: bool = False
) -> List[re.Pattern]:
    flags = re.IGNORECASE if ignore_case else 0
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, flags))
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern '{p}': {exc}") from exc
    return compiled


def grep_entries(
    entries: List[LogEntry],
    patterns: List[str],
    *,
    ignore_case: bool = False,
    require_all: bool = False,
    invert: bool = False,
) -> List[GrepResult]:
    """Filter entries by one or more regex patterns.

    Args:
        entries: Parsed log entries to search.
        patterns: List of regex pattern strings.
        ignore_case: Perform case-insensitive matching.
        require_all: If True, all patterns must match (AND); otherwise any (OR).
        invert: Return entries that do NOT match.

    Returns:
        List of GrepResult objects for matching entries.
    """
    if not patterns:
        return [GrepResult(entry=e) for e in entries]

    compiled = _compile_patterns(patterns, ignore_case=ignore_case)
    results: List[GrepResult] = []

    for entry in entries:
        text = entry.raw
        matched: List[str] = []
        for pat in compiled:
            if pat.search(text):
                matched.append(pat.pattern)

        hit = (len(matched) == len(compiled)) if require_all else bool(matched)
        if invert:
            hit = not hit

        if hit:
            results.append(
                GrepResult(
                    entry=entry,
                    matched_patterns=matched if not invert else [],
                    match_count=len(matched) if not invert else 0,
                )
            )

    return results


def summarize_grep(
    results: List[GrepResult],
) -> Dict[str, int]:
    """Return a count of how many entries each pattern matched."""
    counts: Dict[str, int] = {}
    for r in results:
        for p in r.matched_patterns:
            counts[p] = counts.get(p, 0) + 1
    return counts
