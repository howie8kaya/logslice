"""CLI helpers for the --tail / -f live-follow feature."""

import argparse
import sys
from logslice.parser import LogParser
from logslice.tail import tail_file
from logslice.formatter import format_entries
from logslice.highlight import apply_highlight


def add_tail_args(parser: argparse.ArgumentParser) -> None:
    """Register tail-related arguments on *parser*."""
    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        default=False,
        help="follow the log file and print new entries as they arrive",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.25,
        metavar="SECONDS",
        help="polling interval in seconds when following (default: 0.25)",
    )


def _format_entry(entry, output_format: str, highlight: bool, pattern, ignore_case: bool) -> str:
    """Format a single log *entry* and optionally apply highlight.

    Returns the formatted string (without a trailing newline).
    """
    lines = format_entries([entry], fmt=output_format, highlight=False)
    if highlight and output_format == "plain":
        lines = apply_highlight(lines, pattern=pattern, ignore_case=ignore_case)
    return lines


def handle_tail(args: argparse.Namespace) -> None:
    """Stream new log entries from *args.file* to stdout.

    Reads *args.file* from its current end and prints each new entry as it
    arrives.  Exits cleanly on KeyboardInterrupt (Ctrl-C).
    """
    pattern = getattr(args, "pattern", None)
    ignore_case = getattr(args, "ignore_case", False)
    highlight = getattr(args, "highlight", False)
    output_format = getattr(args, "format", "plain")

    parser = LogParser(pattern=pattern, ignore_case=ignore_case)

    try:
        for entry in tail_file(
            args.file,
            parser=parser,
            poll_interval=args.poll_interval,
        ):
            lines = _format_entry(entry, output_format, highlight, pattern, ignore_case)
            sys.stdout.write(lines + "\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass  # clean exit on Ctrl-C
