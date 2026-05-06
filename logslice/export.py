"""Export log entries to various file formats."""

import csv
import json
import os
from typing import List, Optional

from logslice.parser import LogEntry


SUPPORTED_FORMATS = ("json", "csv", "txt")


def export_entries(
    entries: List[LogEntry],
    output_path: str,
    fmt: Optional[str] = None,
) -> str:
    """Write entries to *output_path* in the requested format.

    If *fmt* is None the format is inferred from the file extension.
    Returns the resolved format string used.
    """
    if fmt is None:
        _, ext = os.path.splitext(output_path)
        fmt = ext.lstrip(".").lower() or "txt"

    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported export format '{fmt}'. Choose from: {SUPPORTED_FORMATS}"
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if fmt == "json":
        _export_json(entries, output_path)
    elif fmt == "csv":
        _export_csv(entries, output_path)
    else:
        _export_txt(entries, output_path)

    return fmt


def _export_json(entries: List[LogEntry], path: str) -> None:
    data = [e.to_dict() for e in entries]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


def _export_csv(entries: List[LogEntry], path: str) -> None:
    fieldnames = ["line_number", "timestamp", "level", "message", "raw"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for e in entries:
            row = e.to_dict()
            row.setdefault("timestamp", "")
            row.setdefault("level", "")
            row.setdefault("message", "")
            writer.writerow(row)


def _export_txt(entries: List[LogEntry], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(e.raw + "\n")
