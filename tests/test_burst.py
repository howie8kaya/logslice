"""Tests for logslice.burst — burst detection module."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from logslice.burst import BurstWindow, detect_bursts
from logslice.parser import LogEntry


def make_entry(ts: Optional[datetime] = None, msg: str = "log line") -> LogEntry:
    return LogEntry(line_number=1, raw=msg, timestamp=ts, level=None, message=msg, groups={})


def ts(offset_seconds: int) -> datetime:
    base = datetime(2024, 1, 1, 12, 0, 0)
    return base + timedelta(seconds=offset_seconds)


# ---------------------------------------------------------------------------
# detect_bursts
# ---------------------------------------------------------------------------

def test_empty_entries_returns_empty():
    assert detect_bursts([]) == []


def test_no_timestamps_returns_empty():
    entries = [make_entry(ts=None) for _ in range(20)]
    assert detect_bursts(entries, window_seconds=60, threshold=5) == []


def test_below_threshold_no_burst():
    entries = [make_entry(ts=ts(i * 10)) for i in range(5)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert result == []


def test_exactly_at_threshold_triggers_burst():
    entries = [make_entry(ts=ts(i)) for i in range(10)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert len(result) >= 1


def test_burst_count_matches_window_entries():
    entries = [make_entry(ts=ts(i)) for i in range(15)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert result[0].count >= 10


def test_burst_window_start_before_end():
    entries = [make_entry(ts=ts(i)) for i in range(12)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert result[0].start <= result[0].end


def test_no_burst_when_spread_out():
    # 10 entries spread over 200 seconds — no 60-second window has >= 10
    entries = [make_entry(ts=ts(i * 20)) for i in range(10)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert result == []


def test_burst_entries_are_populated():
    entries = [make_entry(ts=ts(i)) for i in range(12)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    assert len(result[0].entries) >= 10


def test_as_dict_keys():
    bw = BurstWindow(
        start=ts(0),
        end=ts(30),
        count=15,
        entries=[],
    )
    d = bw.as_dict()
    assert set(d.keys()) == {"start", "end", "count", "duration_seconds"}


def test_as_dict_duration():
    bw = BurstWindow(start=ts(0), end=ts(45), count=5, entries=[])
    assert bw.as_dict()["duration_seconds"] == 45.0


def test_mixed_timestamped_and_none():
    entries = [make_entry(ts=ts(i)) for i in range(10)]
    entries += [make_entry(ts=None) for _ in range(5)]
    result = detect_bursts(entries, window_seconds=60, threshold=10)
    # Should process only timestamped entries without crashing
    assert isinstance(result, list)
