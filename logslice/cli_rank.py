"""CLI integration for the rank feature."""
from __future__ import annotations

import argparse
import json
from typing import List

from logslice.parser import LogEntry
from logslice.rank import rank_entries


def add_rank_args(parser: argparse.ArgumentParser) -> None:
    """Register --rank and related flags onto *parser*."""
    parser.add_argument(
        "--rank",
        action="store_true",
        default=False,
        help="Rank log entries by frequency or severity weight.",
    )
    parser.add_argument(
        "--rank-by",
        choices=["count", "weight"],
        default="count",
        dest="rank_by",
        help="Ranking strategy: 'count' (default) or 'weight'.",
    )
    parser.add_argument(
        "--rank-top",
        type=int,
        default=10,
        dest="rank_top",
        metavar="N",
        help="Number of top entries to display (default: 10).",
    )
    parser.add_argument(
        "--rank-format",
        choices=["plain", "json"],
        default="plain",
        dest="rank_format",
        help="Output format for ranked results.",
    )


def handle_rank(args: argparse.Namespace, entries: List[LogEntry]) -> int:
    """Execute ranking and print results. Returns exit code."""
    if not getattr(args, "rank", False):
        return 0

    results = rank_entries(entries, top_n=args.rank_top, by=args.rank_by)

    if not results:
        print("No entries to rank.")
        return 0

    if args.rank_format == "json":
        print(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        col_w = 6
        print(f"{'Rank':<{col_w}} {'Count':>6}  {'Level':<10}  Message")
        print("-" * 72)
        for i, r in enumerate(results, start=1):
            level_str = r.level or "-"
            msg = r.raw[:50] + "..." if len(r.raw) > 50 else r.raw
            print(f"{i:<{col_w}} {r.count:>6}  {level_str:<10}  {msg}")

    return 0
