"""Annotation module: attach labels/tags to log entries based on regex rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class AnnotationRule:
    """A single rule that maps a regex pattern to a label."""

    label: str
    pattern: str
    ignore_case: bool = False

    def __post_init__(self) -> None:
        flags = re.IGNORECASE if self.ignore_case else 0
        self._compiled = re.compile(self.pattern, flags)

    def matches(self, text: str) -> bool:
        return bool(self._compiled.search(text))


def _compile_rules(rules: List[Dict]) -> List[AnnotationRule]:
    """Build AnnotationRule objects from plain dicts."""
    result = []
    for r in rules:
        result.append(
            AnnotationRule(
                label=r["label"],
                pattern=r["pattern"],
                ignore_case=r.get("ignore_case", False),
            )
        )
    return result


def annotate_entries(
    entries: List[LogEntry],
    rules: List[Dict],
    *,
    multi: bool = True,
) -> List[LogEntry]:
    """Return entries with an 'annotations' key added to their extras.

    Args:
        entries: Parsed log entries.
        rules:   List of dicts with keys: label, pattern, ignore_case (opt).
        multi:   If False, stop after the first matching rule per entry.
    """
    compiled = _compile_rules(rules)
    annotated: List[LogEntry] = []

    for entry in entries:
        labels: List[str] = []
        for rule in compiled:
            if rule.matches(entry.raw):
                labels.append(rule.label)
                if not multi:
                    break
        new_extras = dict(entry.extras or {})
        new_extras["annotations"] = labels
        annotated.append(
            LogEntry(
                line_number=entry.line_number,
                raw=entry.raw,
                timestamp=entry.timestamp,
                level=entry.level,
                message=entry.message,
                extras=new_extras,
            )
        )

    return annotated
