"""Tests for logslice.stats module."""
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.stats import LogStats, compute_stats


def make_entry(
    raw: str,
    level: str | None = None,
    timestamp: str | None = None,
    line_no: int = 1,
) -> LogEntry:
    entry = LogEntry(line_no=line_no, raw=raw)
    entry.level = level
    entry.timestamp = timestamp
    return entry


def test_empty_entries_returns_zero_stats():
    stats = compute_stats([])
    assert stats.total == 0
    assert stats.by_level == {}
    assert stats.first_timestamp is None
    assert stats.last_timestamp is None


def test_total_count():
    entries = [make_entry("line", line_no=i) for i in range(7)]
    stats = compute_stats(entries)
    assert stats.total == 7


def test_by_level_counts():
    entries = [
        make_entry("err msg", level="ERROR"),
        make_entry("err msg2", level="error"),  # case normalised
        make_entry("warn msg", level="WARN"),
        make_entry("info msg", level=None),
    ]
    stats = compute_stats(entries)
    assert stats.by_level["ERROR"] == 2
    assert stats.by_level["WARN"] == 1
    assert stats.by_level["UNKNOWN"] == 1


def test_timestamp_range():
    entries = [
        make_entry("a", timestamp="2024-01-01T10:00:00"),
        make_entry("b", timestamp="2024-01-03T08:00:00"),
        make_entry("c", timestamp="2024-01-02T12:00:00"),
    ]
    stats = compute_stats(entries)
    assert stats.first_timestamp == "2024-01-01T10:00:00"
    assert stats.last_timestamp == "2024-01-03T08:00:00"


def test_timestamp_range_with_none_entries():
    entries = [
        make_entry("a", timestamp=None),
        make_entry("b", timestamp="2024-06-15T09:00:00"),
    ]
    stats = compute_stats(entries)
    assert stats.first_timestamp == "2024-06-15T09:00:00"
    assert stats.last_timestamp == "2024-06-15T09:00:00"


def test_top_patterns_returns_at_most_n():
    raw = "error connecting to database server failed"
    entries = [make_entry(raw, line_no=i) for i in range(10)]
    stats = compute_stats(entries, top_n=3)
    assert len(stats.top_patterns) <= 3


def test_top_patterns_most_frequent_first():
    entries = [
        make_entry("alpha beta gamma"),
        make_entry("alpha beta"),
        make_entry("alpha"),
    ]
    stats = compute_stats(entries, top_n=5)
    words = [w for w, _ in stats.top_patterns]
    assert words[0] == "alpha"


def test_as_dict_keys():
    entries = [make_entry("some log line", level="INFO")]
    stats = compute_stats(entries)
    d = stats.as_dict()
    assert set(d.keys()) == {
        "total", "by_level", "first_timestamp", "last_timestamp", "top_patterns"
    }
    assert isinstance(d["top_patterns"], list)
