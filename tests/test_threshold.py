"""Tests for logslice.threshold."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.threshold import ThresholdAlert, check_threshold


def make_entry(
    line_number: int,
    level: str,
    ts: Optional[datetime] = None,
    raw: str = "log line",
) -> LogEntry:
    return LogEntry(
        line_number=line_number,
        raw=raw,
        timestamp=ts,
        level=level,
        message=raw,
        extra={},
    )


BASE = datetime(2024, 1, 1, 12, 0, 0)


def test_no_entries_returns_empty():
    assert check_threshold([], "ERROR", max_count=3) == []


def test_no_matching_level_returns_empty():
    entries = [make_entry(1, "INFO", BASE)]
    assert check_threshold(entries, "ERROR", max_count=1) == []


def test_entries_without_timestamp_ignored():
    entries = [make_entry(i, "ERROR", None) for i in range(10)]
    assert check_threshold(entries, "ERROR", max_count=2) == []


def test_below_threshold_no_alert():
    entries = [
        make_entry(i, "ERROR", BASE + timedelta(seconds=i * 5))
        for i in range(3)
    ]
    # 3 entries in 60s window, max_count=3 means strictly greater than
    result = check_threshold(entries, "ERROR", max_count=3, window_seconds=60)
    assert result == []


def test_above_threshold_triggers_alert():
    entries = [
        make_entry(i, "ERROR", BASE + timedelta(seconds=i * 5))
        for i in range(5)
    ]
    result = check_threshold(entries, "ERROR", max_count=3, window_seconds=60)
    assert len(result) >= 1
    assert all(isinstance(a, ThresholdAlert) for a in result)
    assert result[0].level == "ERROR"
    assert result[0].count > 3


def test_alert_count_reflects_bucket_size():
    entries = [
        make_entry(i, "WARN", BASE + timedelta(seconds=i * 2))
        for i in range(6)
    ]
    result = check_threshold(entries, "WARN", max_count=4, window_seconds=15)
    assert result[0].count >= 5


def test_window_separates_bursts():
    burst1 = [
        make_entry(i, "ERROR", BASE + timedelta(seconds=i))
        for i in range(5)
    ]
    burst2 = [
        make_entry(10 + i, "ERROR", BASE + timedelta(seconds=300 + i))
        for i in range(5)
    ]
    result = check_threshold(burst1 + burst2, "ERROR", max_count=3, window_seconds=10)
    starts = {a.window_start for a in result}
    # Both bursts should be detected independently
    assert len(starts) >= 2


def test_as_dict_keys():
    entries = [
        make_entry(i, "ERROR", BASE + timedelta(seconds=i))
        for i in range(5)
    ]
    result = check_threshold(entries, "ERROR", max_count=3, window_seconds=60)
    assert result
    d = result[0].as_dict()
    assert set(d.keys()) == {"level", "count", "window_start", "window_end", "lines"}
    assert isinstance(d["lines"], list)


def test_case_insensitive_level_matching():
    entries = [
        make_entry(i, "error", BASE + timedelta(seconds=i))
        for i in range(5)
    ]
    result = check_threshold(entries, "ERROR", max_count=3, window_seconds=60)
    assert len(result) >= 1
