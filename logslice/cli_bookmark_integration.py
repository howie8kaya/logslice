"""Standalone entry-point wiring bookmark commands into a top-level CLI."""

from __future__ import annotations

import argparse
import sys

from logslice.cli_bookmark import add_bookmark_args, handle_bookmark


def build_bookmark_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-bookmark",
        description="Manage logslice bookmarks (save/load/delete/list)",
    )
    add_bookmark_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_bookmark_cli()
    args = parser.parse_args(argv)
    return handle_bookmark(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
