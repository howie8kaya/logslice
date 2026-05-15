"""Tests for logslice.window sliding window aggregation."""
from datetime import datetime, timedelta

import pytest

from logslice.parser import LogEntry
from logslice.window import WindowBucket, sliding_window, _level_counts


def make_entry(offset_seconds: int, level: str = "INFO", msg: str = "test") -> LogEntry:
    ts = datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)
    return LogEntry(line_number=offset_seconds + 1, raw=msg, timestamp=ts, level=level, message=msg)


# --- _level_counts ---

def test_level_counts_empty():
    assert _level_counts([]) == {}


def test_level_counts_mixed():
    entries = [make_entry(0, "ERROR"), make_entry(1, "info"), make_entry(2, "ERROR")]
    counts = _level_counts(entries)
    assert counts["ERROR"] == 2
    assert counts["INFO"] == 1


def test_level_counts_unknown_level():
    e = LogEntry(line_number=1, raw="x", timestamp=None, level=None, message="x")
    assert _level_counts([e]) == {"UNKNOWN": 1}


# --- sliding_window ---

def test_empty_entries_returns_empty():
    assert sliding_window([]) == []


def test_no_timestamps_returns_empty():
    e = LogEntry(line_number=1, raw="x", timestamp=None, level="INFO", message="x")
    assert sliding_window([e]) == []


def test_single_entry_one_bucket():
    entries = [make_entry(0)]
    buckets = sliding_window(entries, window_seconds=60)
    assert len(buckets) == 1
    assert buckets[0].count == 1


def test_tumbling_windows_no_overlap():
    # entries at 0s, 30s, 60s, 90s with 60s tumbling window
    entries = [make_entry(0), make_entry(30), make_entry(60), make_entry(90)]
    buckets = sliding_window(entries, window_seconds=60, step_seconds=60)
    assert len(buckets) == 2
    assert buckets[0].count == 2  # 0s and 30s
    assert buckets[1].count == 2  # 60s and 90s


def test_sliding_window_overlapping():
    # entries at 0s, 30s, 60s; window=60s, step=30s
    entries = [make_entry(0), make_entry(30), make_entry(60)]
    buckets = sliding_window(entries, window_seconds=60, step_seconds=30)
    # window 1: [0, 60) -> 0s, 30s
    # window 2: [30, 90) -> 30s, 60s
    assert len(buckets) == 2
    assert buckets[0].count == 2
    assert buckets[1].count == 2


def test_bucket_end_is_exclusive():
    # entry exactly at window end should NOT be in that bucket
    entries = [make_entry(0), make_entry(60)]
    buckets = sliding_window(entries, window_seconds=60, step_seconds=60)
    assert buckets[0].count == 1
    assert buckets[1].count == 1


def test_as_dict_keys():
    entries = [make_entry(0, "ERROR")]
    bucket = sliding_window(entries, window_seconds=60)[0]
    d = bucket.as_dict()
    assert "start" in d
    assert "end" in d
    assert "count" in d
    assert "levels" in d
    assert d["levels"]["ERROR"] == 1


def test_default_step_equals_window():
    entries = [make_entry(i * 10) for i in range(12)]  # 0..110s
    tumbling = sliding_window(entries, window_seconds=60)
    explicit = sliding_window(entries, window_seconds=60, step_seconds=60)
    assert len(tumbling) == len(explicit)
    for a, b in zip(tumbling, explicit):
        assert a.count == b.count
