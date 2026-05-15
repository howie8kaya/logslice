"""CLI integration for the heatmap feature."""
from __future__ import annotations

import argparse
import json
from typing import List

from logslice.heatmap import build_heatmap, DAYS, HOURS
from logslice.parser import LogEntry


def add_heatmap_args(parser: argparse.ArgumentParser) -> None:
    """Register --heatmap and --heatmap-format flags."""
    parser.add_argument(
        "--heatmap",
        action="store_true",
        default=False,
        help="Print a day-of-week x hour-of-day activity heatmap.",
    )
    parser.add_argument(
        "--heatmap-format",
        choices=["table", "json"],
        default="table",
        help="Output format for heatmap (default: table).",
    )


def _render_table(heatmap) -> str:
    grid = heatmap.grid()
    header = "     " + "".join(f"{h:>4}" for h in HOURS)
    lines = [header]
    for day in DAYS:
        row = f"{day:<5}" + "".join(f"{grid[day][h]:>4}" for h in HOURS)
        lines.append(row)
    if heatmap.skipped:
        lines.append(f"(skipped {heatmap.skipped} entries without timestamp)")
    return "\n".join(lines)


def handle_heatmap(args: argparse.Namespace, entries: List[LogEntry]) -> int:
    """Run heatmap and print results. Returns exit code."""
    if not getattr(args, "heatmap", False):
        return 0

    heatmap = build_heatmap(entries)
    fmt = getattr(args, "heatmap_format", "table")

    if fmt == "json":
        print(json.dumps(heatmap.as_dict(), indent=2))
    else:
        print(_render_table(heatmap))

    return 0
