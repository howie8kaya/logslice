"""CLI helpers for the deduplication feature."""

from __future__ import annotations

import argparse
from typing import List

from logslice.dedup import count_duplicates, dedup_entries
from logslice.parser import LogEntry


def add_dedup_args(parser: argparse.ArgumentParser) -> None:
    """Register dedup-related arguments on *parser*."""
    group = parser.add_argument_group("deduplication")
    group.add_argument(
        "--dedup",
        action="store_true",
        default=False,
        help="Remove duplicate log lines before output.",
    )
    group.add_argument(
        "--dedup-keep",
        choices=["first", "last"],
        default="first",
        dest="dedup_keep",
        help="Which occurrence to keep when deduplicating (default: first).",
    )
    group.add_argument(
        "--dedup-keep-numbers",
        action="store_true",
        default=False,
        dest="dedup_keep_numbers",
        help="Treat lines differing only in numeric values as distinct.",
    )
    group.add_argument(
        "--dedup-stats",
        action="store_true",
        default=False,
        dest="dedup_stats",
        help="Print duplicate counts to stderr before output.",
    )


def handle_dedup(
    args: argparse.Namespace,
    entries: List[LogEntry],
) -> List[LogEntry]:
    """Apply deduplication to *entries* according to parsed *args*.

    Returns the (possibly filtered) list of entries.  When ``--dedup`` is
    not set the original list is returned unchanged.
    """
    if not args.dedup:
        return entries

    ignore_numbers = not args.dedup_keep_numbers

    if args.dedup_stats:
        import sys

        counts = count_duplicates(entries, ignore_numbers=ignore_numbers)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        if duplicates:
            print("[dedup] duplicate messages:", file=sys.stderr)
            for msg, cnt in sorted(duplicates.items(), key=lambda x: -x[1]):
                print(f"  ({cnt}x) {msg}", file=sys.stderr)
        else:
            print("[dedup] no duplicates found.", file=sys.stderr)

    return dedup_entries(entries, ignore_numbers=ignore_numbers, keep=args.dedup_keep)
