"""Tests for logslice.cli_cluster."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from io import StringIO
from typing import Optional
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.cli_cluster import add_cluster_args, handle_cluster


def make_entry(raw: str, level: Optional[str] = None) -> LogEntry:
    return LogEntry(raw=raw, level=level, timestamp=None, line_number=1, extra={})


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_cluster_args(p)
    return p


def defaults(parser: argparse.ArgumentParser) -> argparse.Namespace:
    return parser.parse_args([])


def test_add_cluster_args_registers_cluster(parser):
    ns = defaults(parser)
    assert hasattr(ns, "cluster")


def test_cluster_default_is_false(parser):
    ns = defaults(parser)
    assert ns.cluster is False


def test_cluster_min_default(parser):
    ns = defaults(parser)
    assert ns.cluster_min == 1


def test_cluster_ignore_level_default(parser):
    ns = defaults(parser)
    assert ns.cluster_ignore_level is False


def test_cluster_format_default(parser):
    ns = defaults(parser)
    assert ns.cluster_format == "text"


def test_handle_cluster_disabled_returns_zero(parser):
    ns = defaults(parser)
    entries = [make_entry("hello world")]
    assert handle_cluster(ns, entries) == 0


def test_handle_cluster_no_results_prints_message(parser, capsys):
    ns = parser.parse_args(["--cluster", "--cluster-min", "999"])
    entries = [make_entry("hello world")]
    rc = handle_cluster(ns, entries)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No clusters" in out


def test_handle_cluster_text_output(parser, capsys):
    ns = parser.parse_args(["--cluster"])
    entries = [
        make_entry("user 1 logged in"),
        make_entry("user 2 logged in"),
    ]
    handle_cluster(ns, entries)
    out = capsys.readouterr().out
    assert "2x" in out or "2" in out


def test_handle_cluster_json_output(parser, capsys):
    ns = parser.parse_args(["--cluster", "--cluster-format", "json"])
    entries = [make_entry("user 1 logged in"), make_entry("user 2 logged in")]
    handle_cluster(ns, entries)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["count"] == 2
