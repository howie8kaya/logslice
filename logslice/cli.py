"""Command-line interface for logslice."""

import argparse
import sys
from logslice.parser import LogParser
from logslice.formatter import format_entries, SUPPORTED_FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file parser and filter utility with regex support.",
    )
    parser.add_argument("file", nargs="?", help="Log file to parse (stdin if omitted)")
    parser.add_argument("-p", "--pattern", help="Regex pattern to filter lines")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive matching")
    parser.add_argument(
        "-f", "--format",
        choices=SUPPORTED_FORMATS,
        default="plain",
        help="Output format (default: plain)",
    )
    return parser


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        log_parser = LogParser(pattern=args.pattern, ignore_case=args.ignore_case)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.file:
            entries = list(log_parser.parse_file(args.file))
        else:
            lines = sys.stdin.readlines()
            entries = list(log_parser.parse_lines(lines))
    except FileNotFoundError:
        print(f"Error: file '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        output = format_entries(entries, args.format)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if output:
        print(output)


if __name__ == "__main__":
    run()
