"""CLI integration for the redact feature."""

import argparse
from typing import List

from logslice.redact import redact_entries
from logslice.parser import LogEntry


def add_redact_args(parser: argparse.ArgumentParser) -> None:
    """Register redaction-related CLI arguments onto an existing parser."""
    parser.add_argument(
        '--redact',
        action='store_true',
        default=False,
        help='Enable built-in redaction of passwords, tokens, emails, and card numbers.',
    )
    parser.add_argument(
        '--redact-pattern',
        dest='redact_patterns',
        metavar='PATTERN',
        action='append',
        default=[],
        help='Additional regex pattern to redact (can be specified multiple times).',
    )
    parser.add_argument(
        '--no-builtin-redact',
        dest='no_builtin_redact',
        action='store_true',
        default=False,
        help='Disable built-in redaction patterns (only custom patterns apply).',
    )


def handle_redact(
    args: argparse.Namespace,
    entries: List[LogEntry],
) -> List[LogEntry]:
    """Apply redaction to entries based on parsed CLI args.

    Returns the (possibly redacted) list of entries.
    """
    should_redact = args.redact or bool(args.redact_patterns)
    if not should_redact:
        return entries

    use_builtins = not args.no_builtin_redact
    extra = args.redact_patterns or []

    return redact_entries(
        entries,
        extra_patterns=extra if extra else None,
        use_builtins=use_builtins,
    )
