"""Tests for logslice.filter module."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.filter import filter_by_time_range, filter_by_level, apply_filters


def make_entry(line_no: int, raw: str, groups: dict) -> LogEntry:
    e = LogEntry(line_number=line_no, raw=raw, groups=groups)
    return e


ENTRIES = [
    make_entry(1, "DEBUG 2024-01-01T08:00:00 boot",  {"level": "DEBUG",   "timestamp": "2024-01-01T08:00:00"}),
    make_entry(2, "INFO  2024-01-01T09:00:00 start", {"level": "INFO",    "timestamp": "2024-01-01T09:00:00"}),
    make_entry(3, "WARNING 2024-01-01T10:00:00 slow",{"level": "WARNING", "timestamp": "2024-01-01T10:00:00"}),
    make_entry(4, "ERROR 2024-01-01T11:00:00 fail",  {"level": "ERROR",   "timestamp": "2024-01-01T11:00:00"}),
    make_entry(5, "CRITICAL 2024-01-01T12:00:00 die",{"level": "CRITICAL","timestamp": "2024-01-01T12:00:00"}),
]


def test_filter_by_time_range_start_only():
    start = datetime.fromisoformat("2024-01-01T10:00:00")
    result = filter_by_time_range(ENTRIES, start=start)
    assert len(result) == 3
    assert result[0].groups["level"] == "WARNING"


def test_filter_by_time_range_end_only():
    end = datetime.fromisoformat("2024-01-01T09:00:00")
    result = filter_by_time_range(ENTRIES, end=end)
    assert len(result) == 2


def test_filter_by_time_range_both():
    start = datetime.fromisoformat("2024-01-01T09:00:00")
    end   = datetime.fromisoformat("2024-01-01T10:00:00")
    result = filter_by_time_range(ENTRIES, start=start, end=end)
    assert len(result) == 2
    levels = [e.groups["level"] for e in result]
    assert levels == ["INFO", "WARNING"]


def test_filter_by_time_range_no_timestamp_passes_through():
    entry = make_entry(99, "no ts", {})
    result = filter_by_time_range([entry], start=datetime.fromisoformat("2099-01-01T00:00:00"))
    assert len(result) == 1


def test_filter_by_level_warning_and_above():
    result = filter_by_level(ENTRIES, min_level="WARNING")
    assert len(result) == 3
    assert all(e.groups["level"] in ("WARNING", "ERROR", "CRITICAL") for e in result)


def test_filter_by_level_debug_returns_all():
    result = filter_by_level(ENTRIES, min_level="DEBUG")
    assert len(result) == 5


def test_filter_by_level_unknown_level_raises():
    with pytest.raises(ValueError, match="Unknown log level"):
        filter_by_level(ENTRIES, min_level="VERBOSE")


def test_filter_by_level_no_level_field_passes_through():
    entry = make_entry(99, "plain line", {})
    result = filter_by_level([entry], min_level="ERROR")
    assert len(result) == 1


def test_apply_filters_combined():
    start = datetime.fromisoformat("2024-01-01T09:00:00")
    result = apply_filters(ENTRIES, start=start, min_level="ERROR")
    assert len(result) == 2
    assert result[0].groups["level"] == "ERROR"
    assert result[1].groups["level"] == "CRITICAL"


def test_apply_filters_no_args_returns_all():
    result = apply_filters(ENTRIES)
    assert len(result) == len(ENTRIES)
