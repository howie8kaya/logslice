"""CLI integration for the trend analysis feature."""
from __future__ import annotations

import argparse
import json
from typing import List

from logslice.parser import LogEntry
from logslice.trend import compute_trend

_VALID_RESOLUTIONS = ("minute", "hour", "day")


def add_trend_args(parser: argparse.ArgumentParser) -> None:
    """Register --trend and related options on *parser*."""
    parser.add_argument(
        "--trend",
        action="store_true",
        default=False,
        help="Show rate-of-change trend across time buckets.",
    )
    parser.add_argument(
        "--trend-resolution",
        choices=_VALID_RESOLUTIONS,
        default="minute",
        metavar="RES",
        help="Bucket size for trend analysis: minute, hour, day (default: minute).",
    )
    parser.add_argument(
        "--trend-level",
        default=None,
        metavar="LEVEL",
        help="Restrict trend analysis to a specific log level.",
    )
    parser.add_argument(
        "--trend-json",
        action="store_true",
        default=False,
        help="Output trend report as JSON.",
    )


def handle_trend(args: argparse.Namespace, entries: List[LogEntry]) -> int:
    """Run trend analysis and print results; returns exit code."""
    if not getattr(args, "trend", False):
        return 0

    report = compute_trend(
        entries,
        resolution=args.trend_resolution,
        level=args.trend_level,
    )

    if args.trend_json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    if not report.points:
        print("[trend] No timestamped entries found.")
        return 0

    print(f"[trend] resolution={report.resolution}  level={report.level_filter or 'ALL'}")
    print(f"  {'Bucket':<20} {'Count':>6}  {'Delta':>7}  {'Delta%':>8}")
    print("  " + "-" * 48)
    for pt in report.points:
        delta_str = f"{pt.delta:+d}" if pt.delta is not None else "  --"
        pct_str = f"{pt.delta_pct:+.1f}%" if pt.delta_pct is not None else "  --"
        print(f"  {pt.bucket:<20} {pt.count:>6}  {delta_str:>7}  {pct_str:>8}")

    return 0
