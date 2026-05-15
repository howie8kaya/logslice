"""Tests for logslice.cli_rank."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from io import StringIO
from typing import Optional
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.cli_rank import add_rank_args, handle_rank


def make_entry(
    raw: str,
    level: Optional[str] = None,
    line_number: int = 1,
) -> LogEntry:
    return LogEntry(raw=raw, line_number=line_number, timestamp=None, level=level, groups={})


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_rank_args(p)
    return p


@pytest.fixture()
def defaults(parser) -> argparse.Namespace:
    return parser.parse_args([])


def test_add_rank_args_registers_rank(parser):
    args = parser.parse_args(["--rank"])
    assert args.rank is True


def test_rank_default_is_false(defaults):
    assert defaults.rank is False


def test_rank_by_default_is_count(defaults):
    assert defaults.rank_by == "count"


def test_rank_top_default_is_10(defaults):
    assert defaults.rank_top == 10


def test_rank_format_default_is_plain(defaults):
    assert defaults.rank_format == "plain"


def test_handle_rank_skips_when_flag_false(defaults, capsys):
    entries = [make_entry("hello")]
    code = handle_rank(defaults, entries)
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_handle_rank_plain_output(parser, capsys):
    args = parser.parse_args(["--rank", "--rank-by", "count", "--rank-top", "5"])
    entries = [
        make_entry("disk full", level="ERROR", line_number=i) for i in range(3)
    ]
    code = handle_rank(args, entries)
    assert code == 0
    out = capsys.readouterr().out
    assert "disk full" in out
    assert "3" in out


def test_handle_rank_json_output(parser, capsys):
    args = parser.parse_args(["--rank", "--rank-format", "json"])
    entries = [make_entry("timeout", level="WARN", line_number=1)]
    code = handle_rank(args, entries)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["count"] == 1


def test_handle_rank_empty_entries(parser, capsys):
    args = parser.parse_args(["--rank"])
    code = handle_rank(args, [])
    assert code == 0
    assert "No entries" in capsys.readouterr().out
