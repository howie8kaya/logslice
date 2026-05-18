"""Tests for logslice.cli_trend."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from io import StringIO
from typing import Optional
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.cli_trend import add_trend_args, handle_trend


def make_entry(ts_str: Optional[str], level: str = "INFO", msg: str = "x") -> LogEntry:
    ts = datetime.fromisoformat(ts_str) if ts_str else None
    return LogEntry(line_number=1, raw=msg, timestamp=ts, level=level, message=msg, extra={})


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_trend_args(p)
    return p


@pytest.fixture()
def defaults(parser) -> argparse.Namespace:
    return parser.parse_args([])


def test_add_trend_args_registers_flag(parser):
    ns = parser.parse_args(["--trend"])
    assert ns.trend is True


def test_trend_default_is_false(defaults):
    assert defaults.trend is False


def test_trend_resolution_default(defaults):
    assert defaults.trend_resolution == "minute"


def test_trend_resolution_choices(parser):
    for choice in ("minute", "hour", "day"):
        ns = parser.parse_args(["--trend", "--trend-resolution", choice])
        assert ns.trend_resolution == choice


def test_trend_level_default_is_none(defaults):
    assert defaults.trend_level is None


def test_handle_trend_skips_when_flag_false(defaults, capsys):
    entries = [make_entry("2024-03-10T10:01:00")]
    rc = handle_trend(defaults, entries)
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_handle_trend_plain_output(parser, capsys):
    ns = parser.parse_args(["--trend", "--trend-resolution", "hour"])
    entries = [
        make_entry("2024-03-10T10:01:00"),
        make_entry("2024-03-10T11:01:00"),
        make_entry("2024-03-10T11:02:00"),
    ]
    rc = handle_trend(ns, entries)
    assert rc == 0
    out = capsys.readouterr().out
    assert "resolution=hour" in out
    assert "2024-03-10T10" in out
    assert "2024-03-10T11" in out


def test_handle_trend_json_output(parser, capsys):
    ns = parser.parse_args(["--trend", "--trend-json"])
    entries = [make_entry("2024-03-10T10:01:00"), make_entry("2024-03-10T10:02:00")]
    rc = handle_trend(ns, entries)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "points" in data
    assert data["resolution"] == "minute"


def test_handle_trend_no_entries_message(parser, capsys):
    ns = parser.parse_args(["--trend"])
    rc = handle_trend(ns, [])
    assert rc == 0
    assert "No timestamped" in capsys.readouterr().out
