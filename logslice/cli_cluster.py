"""CLI integration for the log clustering feature."""
from __future__ import annotations

import argparse
import json
from typing import List

from logslice.parser import LogEntry
from logslice.cluster import cluster_entries


def add_cluster_args(parser: argparse.ArgumentParser) -> None:
    """Register clustering arguments on *parser*."""
    parser.add_argument(
        "--cluster",
        action="store_true",
        default=False,
        help="Cluster similar log lines by message pattern.",
    )
    parser.add_argument(
        "--cluster-min",
        type=int,
        default=1,
        metavar="N",
        dest="cluster_min",
        help="Only show clusters with at least N entries (default: 1).",
    )
    parser.add_argument(
        "--cluster-ignore-level",
        action="store_true",
        default=False,
        dest="cluster_ignore_level",
        help="Do not include log level in cluster signature.",
    )
    parser.add_argument(
        "--cluster-format",
        choices=["text", "json"],
        default="text",
        dest="cluster_format",
        help="Output format for cluster results (default: text).",
    )


def handle_cluster(args: argparse.Namespace, entries: List[LogEntry]) -> int:
    """Run clustering and print results.  Returns exit code."""
    if not getattr(args, "cluster", False):
        return 0

    clusters = cluster_entries(
        entries,
        min_count=args.cluster_min,
        use_level=not args.cluster_ignore_level,
    )

    if not clusters:
        print("No clusters found.")
        return 0

    if args.cluster_format == "json":
        print(json.dumps([c.as_dict() for c in clusters], indent=2))
    else:
        for c in clusters:
            print(f"[{c.count:>6}x]  {c.pattern}")
            print(f"         sample: {c.entries[0].raw[:120]}")
            print()

    return 0
