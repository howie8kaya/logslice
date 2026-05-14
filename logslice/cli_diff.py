"""CLI integration for the log diff feature."""

import argparse
import sys
from typing import List

from logslice.parser import LogParser
from logslice.diff import diff_entries, format_diff


def add_diff_args(parser: argparse.ArgumentParser) -> None:
    """Register --diff, --diff-baseline, and related flags on *parser*."""
    parser.add_argument(
        "--diff",
        action="store_true",
        default=False,
        help="Enable diff mode: compare baseline file against the main log file.",
    )
    parser.add_argument(
        "--diff-baseline",
        metavar="FILE",
        default=None,
        help="Path to the baseline log file used as the reference in diff mode.",
    )
    parser.add_argument(
        "--diff-ignore-case",
        action="store_true",
        default=False,
        help="Ignore case when comparing log lines.",
    )
    parser.add_argument(
        "--diff-color",
        action="store_true",
        default=False,
        help="Colorise diff output (red = removed, green = added).",
    )


def handle_diff(args: argparse.Namespace) -> int:
    """Run diff mode.  Returns an exit code (0 = no diff, 1 = diff found, 2 = error)."""
    if not args.diff:
        return 0

    if not args.diff_baseline:
        print("error: --diff requires --diff-baseline", file=sys.stderr)
        return 2

    baseline_parser = LogParser()
    current_parser = LogParser()

    try:
        baseline_entries = baseline_parser.parse_file(args.diff_baseline)
        current_entries = current_parser.parse_file(args.file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = diff_entries(
        baseline_entries,
        current_entries,
        ignore_case=args.diff_ignore_case,
    )

    lines = format_diff(result, color=args.diff_color)
    for line in lines:
        print(line)

    summary = (
        f"--- removed: {result.removed_count if hasattr(result, 'removed_count') else len(result.removed)}, "
        f"+++ added: {len(result.added)}, "
        f"common: {len(result.common)}"
    )
    print(summary)

    return 1 if (result.added or result.removed) else 0
