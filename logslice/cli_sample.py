"""CLI integration for the log-entry sampling feature."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.parser import LogEntry
from logslice.sample import sample_entries
from logslice.formatter import format_entries


def add_sample_args(parser: argparse.ArgumentParser) -> None:
    """Register --sample-n / --sample-frac / --sample-seed arguments."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--sample-n",
        type=int,
        default=None,
        metavar="N",
        help="Draw exactly N random log entries.",
    )
    group.add_argument(
        "--sample-frac",
        type=float,
        default=None,
        metavar="FRAC",
        help="Draw a random fraction of entries (0 < FRAC <= 1).",
    )
    parser.add_argument(
        "--sample-seed",
        type=int,
        default=None,
        metavar="SEED",
        help="Random seed for reproducible sampling.",
    )


def handle_sample(
    args: argparse.Namespace,
    entries: List[LogEntry],
    fmt: str = "plain",
    highlight: bool = False,
) -> int:
    """Run sampling if requested; returns exit code (0 = ok, 1 = error)."""
    n = getattr(args, "sample_n", None)
    frac = getattr(args, "sample_frac", None)
    seed = getattr(args, "sample_seed", None)

    if n is None and frac is None:
        return 0  # sampling not requested

    try:
        result = sample_entries(entries, n=n, fraction=frac, seed=seed)
    except ValueError as exc:
        print(f"sample error: {exc}", file=sys.stderr)
        return 1

    print(format_entries(result.entries, fmt=fmt, highlight=highlight))
    print(
        f"# sampled {result.sampled} of {result.total} entries",
        file=sys.stderr,
    )
    return 0
