"""Tests for logslice.timeline."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.timeline import TimelineBucket, _floor_timestamp, build_timeline


def make_entry(ts: str | None, level: str = "INFO", msg: str = "hello") -> LogEntry:
    dt = datetime.fromisoformat(ts) if ts else None
    return LogEntry(line_number=1, raw=msg, timestamp=dt, level=level, message=msg)


# --- _floor_timestamp ---

def test_floor_second():
    dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
    assert _floor_timestamp(dt, "second") == datetime(2024, 1, 15, 12, 30, 45)


def test_floor_minute():
    dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
    assert _floor_timestamp(dt, "minute") == datetime(2024, 1, 15, 12, 30)


def test_floor_hour():
    dt = datetime(2024, 1, 15, 12, 30, 45)
    assert _floor_timestamp(dt, "hour") == datetime(2024, 1, 15, 12, 0)


def test_floor_day():
    dt = datetime(2024, 1, 15, 12, 30, 45)
    assert _floor_timestamp(dt, "day") == datetime(2024, 1, 15)


def test_floor_invalid_raises():
    with pytest.raises(ValueError, match="Invalid bucket"):
        _floor_timestamp(datetime.now(), "week")


# --- build_timeline ---

def test_empty_entries_returns_empty():
    assert build_timeline([]) == []


def test_no_timestamps_returns_empty():
    entries = [make_entry(None), make_entry(None)]
    assert build_timeline(entries) == []


def test_single_bucket():
    entries = [
        make_entry("2024-01-15T10:01:30"),
        make_entry("2024-01-15T10:01:55"),
    ]
    result = build_timeline(entries, bucket="minute")
    assert len(result) == 1
    assert result[0].count == 2
    assert result[0].timestamp == datetime(2024, 1, 15, 10, 1)


def test_multiple_buckets_sorted():
    entries = [
        make_entry("2024-01-15T10:03:00"),
        make_entry("2024-01-15T10:01:00"),
        make_entry("2024-01-15T10:02:00"),
    ]
    result = build_timeline(entries, bucket="minute")
    assert len(result) == 3
    assert result[0].timestamp < result[1].timestamp < result[2].timestamp


def test_level_counts_aggregated():
    entries = [
        make_entry("2024-01-15T10:01:00", level="ERROR"),
        make_entry("2024-01-15T10:01:30", level="INFO"),
        make_entry("2024-01-15T10:01:45", level="ERROR"),
    ]
    result = build_timeline(entries, bucket="minute")
    assert result[0].levels["ERROR"] == 2
    assert result[0].levels["INFO"] == 1


def test_fill_gaps_adds_zero_buckets():
    entries = [
        make_entry("2024-01-15T10:01:00"),
        make_entry("2024-01-15T10:03:00"),
    ]
    result = build_timeline(entries, bucket="minute", fill_gaps=True)
    assert len(result) == 3
    assert result[1].count == 0
    assert result[1].timestamp == datetime(2024, 1, 15, 10, 2)


def test_invalid_bucket_raises():
    with pytest.raises(ValueError):
        build_timeline([], bucket="week")


def test_as_dict_shape():
    b = TimelineBucket(timestamp=datetime(2024, 1, 1, 12, 0), count=5, levels={"INFO": 5})
    d = b.as_dict()
    assert d["count"] == 5
    assert d["levels"] == {"INFO": 5}
    assert "timestamp" in d
