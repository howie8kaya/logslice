"""CLI integration for the timeline feature."""
from __future__ import annotations

import argparse
import json
from typing import List

from logslice.parser import LogEntry
from logslice.timeline import VALID_BUCKETS, build_timeline


def add_timeline_args(parser: argparse.ArgumentParser) -> None:
    """Register --timeline flag and related options onto *parser*."""
    parser.add_argument(
        "--timeline",
        action="store_true",
        default=False,
        help="Print activity timeline bucketed by time.",
    )
    parser.add_argument(
        "--timeline-bucket",
        choices=list(VALID_BUCKETS),
        default="minute",
        metavar="BUCKET",
        help="Bucket size for timeline (second/minute/hour/day). Default: minute.",
    )
    parser.add_argument(
        "--timeline-fill",
        action="store_true",
        default=False,
        help="Fill gaps between buckets with zero-count entries.",
    )
    parser.add_argument(
        "--timeline-json",
        action="store_true",
        default=False,
        help="Output timeline as JSON instead of plain text.",
    )


def handle_timeline(args: argparse.Namespace, entries: List[LogEntry]) -> int:
    """Run timeline command; returns exit code."""
    buckets = build_timeline(
        entries,
        bucket=args.timeline_bucket,
        fill_gaps=args.timeline_fill,
    )

    if not buckets:
        print("No timestamped entries found for timeline.")
        return 0

    if args.timeline_json:
        print(json.dumps([b.as_dict() for b in buckets], indent=2))
        return 0

    # Plain text bar chart
    max_count = max(b.count for b in buckets) or 1
    bar_width = 40
    for b in buckets:
        bar_len = int(b.count / max_count * bar_width)
        bar = "#" * bar_len
        ts = b.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts}  {bar:<{bar_width}}  {b.count}")
    return 0
