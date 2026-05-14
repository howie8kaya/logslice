"""Tests for logslice.cli_dedup."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional

import pytest

from logslice.cli_dedup import add_dedup_args, handle_dedup
from logslice.parser import LogEntry


def make_entry(
    raw: str,
    lineno: int = 1,
    level: Optional[str] = None,
) -> LogEntry:
    return LogEntry(lineno=lineno, raw=raw, level=level, timestamp=None, groups={})


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_dedup_args(p)
    return p


def defaults(parser: argparse.ArgumentParser) -> argparse.Namespace:
    return parser.parse_args([])


# ---------------------------------------------------------------------------
# add_dedup_args
# ---------------------------------------------------------------------------

def test_add_dedup_args_registers_dedup(parser):
    ns = defaults(parser)
    assert hasattr(ns, "dedup")
    assert ns.dedup is False


def test_add_dedup_args_keep_default(parser):
    ns = defaults(parser)
    assert ns.dedup_keep == "first"


def test_add_dedup_args_keep_last(parser):
    ns = parser.parse_args(["--dedup-keep", "last"])
    assert ns.dedup_keep == "last"


def test_add_dedup_args_keep_numbers_default(parser):
    ns = defaults(parser)
    assert ns.dedup_keep_numbers is False


def test_add_dedup_args_stats_default(parser):
    ns = defaults(parser)
    assert ns.dedup_stats is False


# ---------------------------------------------------------------------------
# handle_dedup
# ---------------------------------------------------------------------------

def test_handle_dedup_noop_when_flag_not_set(parser):
    entries = [
        make_entry("msg", lineno=1),
        make_entry("msg", lineno=2),
    ]
    ns = defaults(parser)  # --dedup not set
    result = handle_dedup(ns, entries)
    assert result is entries  # same object, untouched


def test_handle_dedup_removes_duplicates(parser):
    entries = [
        make_entry("error occurred", lineno=1),
        make_entry("error occurred", lineno=2),
        make_entry("all good", lineno=3),
    ]
    ns = parser.parse_args(["--dedup"])
    result = handle_dedup(ns, entries)
    assert len(result) == 2
    assert result[0].lineno == 1
    assert result[1].lineno == 3


def test_handle_dedup_keep_last(parser):
    entries = [
        make_entry("disk full", lineno=1),
        make_entry("disk full", lineno=9),
    ]
    ns = parser.parse_args(["--dedup", "--dedup-keep", "last"])
    result = handle_dedup(ns, entries)
    assert len(result) == 1
    assert result[0].lineno == 9


def test_handle_dedup_empty_input(parser):
    """Dedup on an empty list should return an empty list without errors."""
    ns = parser.parse_args(["--dedup"])
    result = handle_dedup(ns, [])
    assert result == []


def test_handle_dedup_no_duplicates_unchanged(parser):
    """When all entries are unique, dedup should preserve all of them."""
    entries = [
        make_entry("alpha", lineno=1),
        make_entry("beta", lineno=2),
        make_entry("gamma", lineno=3),
    ]
    ns = parser.parse_args(["--dedup"])
    result = handle_dedup(ns, entries)
    assert len(result) == 3
    assert [e.lineno for e in result] == [1, 2, 3]


def test_handle_dedup_stats_prints_to_stderr(parser, capsys):
    entries = [
        make_entry("boom", lineno=1),
        make_entry("boom", lineno=2),
    ]
    ns = parser.parse_args(["--dedup", "--dedup-stats"])
    handle_dedup(ns, entries)
    captured = capsys.readouterr()
    assert "dedup" in captured.err
    assert "boom" in captured.err
