"""Tests for highlight integration in formatter."""

from datetime import datetime

import pytest

from logslice.formatter import format_entries
from logslice.parser import LogEntry


def make_entry(line_number=1, level="INFO", raw="INFO startup complete"):
    return LogEntry(
        line_number=line_number,
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
        groups={},
    )


def test_plain_no_highlight_no_ansi():
    entries = [make_entry()]
    result = format_entries(entries, fmt="plain", highlight=False)
    assert "\033[" not in result


def test_plain_highlight_adds_ansi():
    entries = [make_entry(level="ERROR", raw="ERROR something broke")]
    result = format_entries(entries, fmt="plain", highlight=True)
    assert "\033[" in result


def test_plain_highlight_with_pattern():
    entries = [make_entry(raw="INFO connection timeout occurred")]
    result = format_entries(entries, fmt="plain", highlight=True, pattern="timeout")
    assert "timeout" in result
    assert "\033[" in result


def test_json_format_ignores_highlight_flag():
    """JSON output should never contain ANSI codes."""
    entries = [make_entry(level="ERROR", raw="ERROR boom")]
    result = format_entries(entries, fmt="json", highlight=True)
    assert "\033[" not in result


def test_csv_format_ignores_highlight_flag():
    """CSV output should never contain ANSI codes."""
    entries = [make_entry(level="WARNING", raw="WARNING disk low")]
    result = format_entries(entries, fmt="csv", highlight=True)
    assert "\033[" not in result


def test_multiple_entries_highlight():
    entries = [
        make_entry(line_number=1, level="INFO", raw="INFO all good"),
        make_entry(line_number=2, level="ERROR", raw="ERROR all bad"),
    ]
    result = format_entries(entries, fmt="plain", highlight=True)
    assert "[1]" in result
    assert "[2]" in result
    assert "\033[" in result
