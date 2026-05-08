"""Tests for logslice.summary module."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.summary import SummaryReport, generate_summary, _extract_message_prefix


def make_entry(raw, level=None, timestamp=None):
    return LogEntry(
        line_number=1,
        raw=raw,
        level=level,
        timestamp=timestamp,
        extra={},
    )


def test_empty_entries_returns_default_report():
    report = generate_summary([])
    assert report.total == 0
    assert report.level_counts == {}
    assert report.top_patterns == []
    assert report.first_timestamp is None
    assert report.last_timestamp is None
    assert report.error_rate == 0.0


def test_total_count():
    entries = [make_entry(f"line {i}") for i in range(7)]
    report = generate_summary(entries)
    assert report.total == 7


def test_level_counts():
    entries = [
        make_entry("msg", level="INFO"),
        make_entry("msg", level="INFO"),
        make_entry("msg", level="ERROR"),
        make_entry("msg", level="debug"),
    ]
    report = generate_summary(entries)
    assert report.level_counts["INFO"] == 2
    assert report.level_counts["ERROR"] == 1
    assert report.level_counts["DEBUG"] == 1


def test_unique_levels_sorted():
    entries = [
        make_entry("x", level="WARN"),
        make_entry("x", level="INFO"),
        make_entry("x", level="ERROR"),
    ]
    report = generate_summary(entries)
    assert report.unique_levels == ["ERROR", "INFO", "WARN"]


def test_error_rate_calculation():
    entries = [
        make_entry("a", level="ERROR"),
        make_entry("b", level="INFO"),
        make_entry("c", level="INFO"),
        make_entry("d", level="CRITICAL"),
    ]
    report = generate_summary(entries)
    assert report.error_rate == pytest.approx(0.5)


def test_timestamp_range():
    t1 = datetime(2024, 1, 1, 10, 0, 0)
    t2 = datetime(2024, 1, 1, 12, 0, 0)
    t3 = datetime(2024, 1, 1, 11, 0, 0)
    entries = [
        make_entry("a", timestamp=t1),
        make_entry("b", timestamp=t2),
        make_entry("c", timestamp=t3),
    ]
    report = generate_summary(entries)
    assert report.first_timestamp == str(t1)
    assert report.last_timestamp == str(t2)


def test_top_patterns_limited_by_top_n():
    entries = [
        make_entry("alpha beta gamma delta"),
        make_entry("alpha beta gamma delta"),
        make_entry("foo bar baz qux"),
    ]
    report = generate_summary(entries, top_n=1)
    assert len(report.top_patterns) == 1
    assert report.top_patterns[0][0] == "alpha beta gamma delta"


def test_extract_message_prefix_short_line():
    assert _extract_message_prefix("hi", words=4) == "hi"


def test_as_dict_keys():
    report = generate_summary([make_entry("test", level="INFO")])
    d = report.as_dict()
    assert set(d.keys()) == {
        "total", "unique_levels", "level_counts",
        "top_patterns", "first_timestamp", "last_timestamp", "error_rate",
    }


def test_unknown_level_for_entries_without_level():
    entries = [make_entry("no level here", level=None)]
    report = generate_summary(entries)
    assert "UNKNOWN" in report.level_counts
