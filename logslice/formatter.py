"""Output formatters for parsed log entries."""

import json
import csv
import io
from typing import Iterable
from logslice.parser import LogEntry


FORMAT_PLAIN = "plain"
FORMAT_JSON = "json"
FORMAT_CSV = "csv"

SUPPORTED_FORMATS = (FORMAT_PLAIN, FORMAT_JSON, FORMAT_CSV)


def format_entries(entries: Iterable[LogEntry], fmt: str) -> str:
    """Format a collection of log entries into the specified output format."""
    if fmt == FORMAT_PLAIN:
        return _format_plain(entries)
    elif fmt == FORMAT_JSON:
        return _format_json(entries)
    elif fmt == FORMAT_CSV:
        return _format_csv(entries)
    else:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")


def _format_plain(entries: Iterable[LogEntry]) -> str:
    lines = []
    for entry in entries:
        lines.append(f"[{entry.line_number}] {entry.raw.strip()}")
    return "\n".join(lines)


def _format_json(entries: Iterable[LogEntry]) -> str:
    data = [entry.to_dict() for entry in entries]
    return json.dumps(data, indent=2)


def _format_csv(entries: Iterable[LogEntry]) -> str:
    output = io.StringIO()
    fieldnames = ["line_number", "raw", "matched_groups"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in entries:
        row = entry.to_dict()
        row["matched_groups"] = json.dumps(row["matched_groups"])
        writer.writerow(row)
    return output.getvalue().strip()
