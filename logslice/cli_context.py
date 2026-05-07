"""CLI argument support for context lines (--before / --after)."""

import argparse
from typing import List, Tuple

from logslice.parser import LogEntry
from logslice.context import extract_with_context, find_matched_indices


def add_context_args(parser: argparse.ArgumentParser) -> None:
    """Register -B / -A / -C context line arguments on *parser*."""
    group = parser.add_argument_group("context")
    group.add_argument(
        "-B",
        "--before",
        type=int,
        default=0,
        metavar="N",
        help="Show N lines of context before each match (default: 0)",
    )
    group.add_argument(
        "-A",
        "--after",
        type=int,
        default=0,
        metavar="N",
        help="Show N lines of context after each match (default: 0)",
    )
    group.add_argument(
        "-C",
        "--context",
        type=int,
        default=None,
        metavar="N",
        help="Show N lines of context before AND after each match",
    )


def handle_context(
    args: argparse.Namespace,
    all_entries: List[LogEntry],
    filtered_entries: List[LogEntry],
) -> List[Tuple[LogEntry, bool]]:
    """Apply context expansion based on parsed CLI args.

    Returns list of (entry, is_match) tuples ready for display.
    """
    before = args.before
    after = args.after

    if getattr(args, "context", None) is not None:
        before = args.context
        after = args.context

    if before == 0 and after == 0:
        return [(e, True) for e in filtered_entries]

    matched_indices = find_matched_indices(all_entries, filtered_entries)
    return extract_with_context(all_entries, matched_indices, before=before, after=after)
