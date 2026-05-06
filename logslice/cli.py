"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.parser import LogParser
from logslice.formatter import format_entries
from logslice.filter import apply_filters


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file parser, filter, and formatter.",
    )
    p.add_argument("file", help="Path to log file")
    p.add_argument("-p", "--pattern", default=None, help="Regex pattern to match lines")
    p.add_argument("-f", "--format", dest="fmt", choices=["plain", "json", "csv"],
                   default="plain", help="Output format")
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="Case-insensitive pattern matching")
    p.add_argument("--start", default=None,
                   help="Filter entries at or after this ISO timestamp (requires 'timestamp' named group)")
    p.add_argument("--end", default=None,
                   help="Filter entries at or before this ISO timestamp (requires 'timestamp' named group)")
    p.add_argument("--level", default=None,
                   help="Minimum log level to include: DEBUG|INFO|WARNING|ERROR|CRITICAL")
    return p


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        print(f"logslice: invalid datetime '{value}', expected ISO format.", file=sys.stderr)
        sys.exit(1)


def run(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_parser = LogParser(pattern=args.pattern, ignore_case=args.ignore_case)
    try:
        entries = log_parser.parse_file(args.file)
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    start = _parse_dt(args.start)
    end   = _parse_dt(args.end)

    entries = apply_filters(entries, start=start, end=end, min_level=args.level)

    output = format_entries(entries, fmt=args.fmt)
    print(output)


if __name__ == "__main__":
    run()
