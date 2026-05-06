"""CLI helpers for the --export flag added to the main logslice command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.export import export_entries, SUPPORTED_FORMATS
from logslice.parser import LogEntry


def add_export_args(parser: argparse.ArgumentParser) -> None:
    """Attach export-related arguments to an existing ArgumentParser."""
    grp = parser.add_argument_group("export")
    grp.add_argument(
        "--export",
        metavar="FILE",
        help="Write filtered results to FILE instead of stdout.",
    )
    grp.add_argument(
        "--export-format",
        choices=SUPPORTED_FORMATS,
        default=None,
        metavar="FMT",
        help=(
            "Output format for --export (json, csv, txt). "
            "Defaults to the file extension."
        ),
    )


def handle_export(
    args: argparse.Namespace,
    entries: List[LogEntry],
) -> bool:
    """If --export was requested, write *entries* and return True.

    Returns False when no export was requested so the caller can fall
    back to normal stdout output.
    """
    if not args.export:
        return False

    try:
        fmt = export_entries(entries, args.export, fmt=args.export_format)
        print(
            f"Exported {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} "
            f"to '{args.export}' ({fmt}).",
            file=sys.stderr,
        )
    except ValueError as exc:
        print(f"logslice export error: {exc}", file=sys.stderr)
        sys.exit(1)

    return True
