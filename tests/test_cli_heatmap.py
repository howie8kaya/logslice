"""Tests for logslice.cli_heatmap."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Optional

import pytest

from logslice.cli_heatmap import add_heatmap_args, handle_heatmap
from logslice.parser import LogEntry


def make_entry(ts: Optional[datetime] = None) -> LogEntry:
    return LogEntry(line_number=1, raw="x", timestamp=ts, level=None, message="x", extra={})


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    add_heatmap_args(p)
    return p


@pytest.fixture
def defaults(parser):
    return parser.parse_args([])


def test_add_heatmap_args_registers_flag(parser):
    args = parser.parse_args(["--heatmap"])
    assert args.heatmap is True


def test_heatmap_default_is_false(defaults):
    assert defaults.heatmap is False


def test_heatmap_format_default_is_table(defaults):
    assert defaults.heatmap_format == "table"


def test_heatmap_format_json(parser):
    args = parser.parse_args(["--heatmap", "--heatmap-format", "json"])
    assert args.heatmap_format == "json"


def test_handle_heatmap_skipped_when_flag_false(defaults, capsys):
    entries = [make_entry(ts=datetime(2024, 1, 1, 10))]
    rc = handle_heatmap(defaults, entries)
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_handle_heatmap_table_output(parser, capsys):
    args = parser.parse_args(["--heatmap"])
    entries = [make_entry(ts=datetime(2024, 1, 1, 8))]  # Monday 08:00
    rc = handle_heatmap(args, entries)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Mon" in out
    assert "8" in out


def test_handle_heatmap_json_output(parser, capsys):
    args = parser.parse_args(["--heatmap", "--heatmap-format", "json"])
    entries = [make_entry(ts=datetime(2024, 1, 3, 15))]  # Wed 15:00
    handle_heatmap(args, entries)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "cells" in data
    assert "skipped" in data


def test_handle_heatmap_skipped_shown_in_table(parser, capsys):
    args = parser.parse_args(["--heatmap"])
    entries = [make_entry(ts=None), make_entry(ts=None)]
    handle_heatmap(args, entries)
    out = capsys.readouterr().out
    assert "skipped 2" in out
