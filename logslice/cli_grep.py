"""CLI integration for the grep feature."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.grep import grep_entries, summarize_grep
from logslice.parser import LogParser


def add_grep_args(parser: argparse.ArgumentParser) -> None:
    """Register grep-related arguments onto *parser*."""
    parser.add_argument(
        "patterns",
        nargs="+",
        metavar="PATTERN",
        help="One or more regex patterns to search for.",
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        default=False,
        help="Case-insensitive matching.",
    )
    parser.add_argument(
        "--all",
        dest="require_all",
        action="store_true",
        default=False,
        help="All patterns must match (AND logic).",
    )
    parser.add_argument(
        "-v",
        "--invert",
        action="store_true",
        default=False,
        help="Return lines that do NOT match.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print per-pattern match counts instead of matched lines.",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        help="Log file to search.",
    )


def handle_grep(args: argparse.Namespace) -> int:
    """Execute grep and write results to stdout. Returns exit code."""
    lp = LogParser()
    try:
        entries = lp.parse_file(args.file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    results = grep_entries(
        entries,
        args.patterns,
        ignore_case=args.ignore_case,
        require_all=args.require_all,
        invert=args.invert,
    )

    if args.summary:
        counts = summarize_grep(results)
        print(json.dumps(counts, indent=2))
        return 0

    for r in results:
        print(r.entry.raw)

    return 0 if results else 1
