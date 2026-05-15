"""Tests for logslice.cli_timeline."""
from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest

from logslice.cli_timeline import add_timeline_args, handle_timeline
from logslice.parser import LogEntry


def make_entry(ts: str | None, level: str = "INFO") -> LogEntry:
    dt = datetime.fromisoformat(ts) if ts else None
    return LogEntry(line_number=1, raw="msg", timestamp=dt, level=level, message="msg")


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    add_timeline_args(p)
    return p


@pytest.fixture()
def defaults(parser):
    return parser.parse_args([])


def test_add_timeline_args_registers_flag(parser):
    args = parser.parse_args(["--timeline"])
    assert args.timeline is True


def test_timeline_default_is_false(defaults):
    assert defaults.timeline is False


def test_timeline_bucket_default(defaults):
    assert defaults.timeline_bucket == "minute"


def test_timeline_fill_default(defaults):
    assert defaults.timeline_fill is False


def test_timeline_json_default(defaults):
    assert defaults.timeline_json is False


def test_handle_timeline_no_timestamps(parser, capsys):
    args = parser.parse_args([])
    entries = [make_entry(None), make_entry(None)]
    rc = handle_timeline(args, entries)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No timestamped" in captured.out


def test_handle_timeline_plain_output(parser, capsys):
    args = parser.parse_args(["--timeline-bucket", "hour"])
    entries = [
        make_entry("2024-03-01T09:15:00"),
        make_entry("2024-03-01T09:45:00"),
        make_entry("2024-03-01T10:05:00"),
    ]
    rc = handle_timeline(args, entries)
    assert rc == 0
    out = capsys.readouterr().out
    assert "2024-03-01 09:00:00" in out
    assert "2024-03-01 10:00:00" in out


def test_handle_timeline_json_output(parser, capsys):
    args = parser.parse_args(["--timeline-json"])
    entries = [make_entry("2024-03-01T09:00:00"), make_entry("2024-03-01T09:00:30")]
    rc = handle_timeline(args, entries)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["count"] == 2


def test_handle_timeline_fill_gaps(parser, capsys):
    args = parser.parse_args(["--timeline-bucket", "minute", "--timeline-fill", "--timeline-json"])
    entries = [
        make_entry("2024-03-01T09:00:00"),
        make_entry("2024-03-01T09:02:00"),
    ]
    rc = handle_timeline(args, entries)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 3
    assert data[1]["count"] == 0
