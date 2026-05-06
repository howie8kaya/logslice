"""Output formatters for log entries."""

import csv
import io
import json
from typing import List, Optional

from logslice.highlight import apply_highlight
from logslice.parser import LogEntry


def format_entries(
    entries: List[LogEntry],
    fmt: str = "plain",
    highlight: bool = False,
    pattern: Optional[str] = None,
) -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == "json":
        return _format_json(entries)
    if fmt == "csv":
        return _format_csv(entries)
    return _format_plain(entries, highlight=highlight, pattern=pattern)


def _format_plain(
    entries: List[LogEntry],
    highlight: bool = False,
    pattern: Optional[str] = None,
) -> str:
    lines = []
    for entry in entries:
        raw = entry.raw.rstrip()
        if highlight:
            raw = apply_highlight(raw, entry.level, pattern)
        lines.append(f"[{entry.line_number}] {raw}")
    return "\n".join(lines)


def _format_json(entries: List[LogEntry]) -> str:
    return json.dumps([entry.to_dict() for entry in entries], indent=2, default=str)


def _format_csv(entries: List[LogEntry]) -> str:
    buf = io.StringIO()
    fieldnames = ["line_number", "timestamp", "level", "message", "raw"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        row = entry.to_dict()
        row["raw"] = entry.raw.rstrip()
        writer.writerow(row)
    return buf.getvalue().rstrip()
