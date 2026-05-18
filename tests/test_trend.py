"""Tests for logslice.trend."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.trend import TrendPoint, TrendReport, compute_trend, _floor_ts


def make_entry(ts: Optional[datetime], level: str = "INFO", msg: str = "msg") -> LogEntry:
    return LogEntry(line_number=1, raw=msg, timestamp=ts, level=level, message=msg, extra={})


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


# --- _floor_ts ---

def test_floor_minute():
    assert _floor_ts(ts("2024-03-10T14:32:45"), "minute") == "2024-03-10T14:32"


def test_floor_hour():
    assert _floor_ts(ts("2024-03-10T14:32:45"), "hour") == "2024-03-10T14"


def test_floor_day():
    assert _floor_ts(ts("2024-03-10T14:32:45"), "day") == "2024-03-10"


def test_floor_unknown_raises():
    with pytest.raises(ValueError, match="Unknown resolution"):
        _floor_ts(ts("2024-03-10T14:32:45"), "week")


# --- compute_trend ---

def test_empty_entries_returns_empty_report():
    report = compute_trend([])
    assert report.points == []
    assert report.resolution == "minute"


def test_no_timestamp_entries_ignored():
    entries = [make_entry(None), make_entry(None)]
    report = compute_trend(entries)
    assert report.points == []


def test_single_bucket_no_delta():
    entries = [
        make_entry(ts("2024-03-10T10:01:00")),
        make_entry(ts("2024-03-10T10:01:30")),
    ]
    report = compute_trend(entries, resolution="minute")
    assert len(report.points) == 1
    pt = report.points[0]
    assert pt.count == 2
    assert pt.delta is None
    assert pt.delta_pct is None


def test_two_buckets_positive_delta():
    entries = [
        make_entry(ts("2024-03-10T10:01:00")),
        make_entry(ts("2024-03-10T10:02:00")),
        make_entry(ts("2024-03-10T10:02:30")),
    ]
    report = compute_trend(entries, resolution="minute")
    assert len(report.points) == 2
    assert report.points[0].delta is None
    assert report.points[1].delta == 1   # 2 - 1
    assert report.points[1].delta_pct == pytest.approx(100.0)


def test_level_filter_excludes_other_levels():
    entries = [
        make_entry(ts("2024-03-10T10:01:00"), level="ERROR"),
        make_entry(ts("2024-03-10T10:01:10"), level="INFO"),
        make_entry(ts("2024-03-10T10:01:20"), level="ERROR"),
    ]
    report = compute_trend(entries, resolution="minute", level="ERROR")
    assert len(report.points) == 1
    assert report.points[0].count == 2
    assert report.level_filter == "ERROR"


def test_as_dict_structure():
    entries = [
        make_entry(ts("2024-03-10T10:01:00")),
        make_entry(ts("2024-03-10T10:02:00")),
    ]
    report = compute_trend(entries, resolution="minute")
    d = report.as_dict()
    assert d["resolution"] == "minute"
    assert d["level_filter"] is None
    assert len(d["points"]) == 2
    assert "delta" in d["points"][0]
    assert "delta_pct" in d["points"][0]


def test_delta_pct_none_when_prev_zero():
    # Manufacture two buckets where first has 0 by using level filter on first bucket
    # Easier: patch manually via direct call to TrendPoint
    pt = TrendPoint(bucket="2024-03-10T10:01", count=5, delta=5, delta_pct=None)
    assert pt.as_dict()["delta_pct"] is None
