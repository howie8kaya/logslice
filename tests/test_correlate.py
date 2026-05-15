"""Tests for logslice.correlate."""

from datetime import datetime, timezone
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.correlate import correlate_entries, CorrelatedPair


def make_entry(
    raw: str,
    ts: Optional[datetime] = None,
    level: str = "INFO",
    line: int = 1,
) -> LogEntry:
    return LogEntry(raw=raw, timestamp=ts, level=level, line_number=line, extra={})


def ts(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# basic pairing
# ---------------------------------------------------------------------------

def test_identical_timestamps_pair():
    left = [make_entry("L1", ts(10, 0, 0))]
    right = [make_entry("R1", ts(10, 0, 0))]
    result = correlate_entries(left, right, window_seconds=1.0)
    assert len(result.pairs) == 1
    assert result.pairs[0].delta_seconds == 0.0
    assert result.unmatched_left == []
    assert result.unmatched_right == []


def test_within_window_pairs():
    left = [make_entry("L1", ts(10, 0, 0))]
    right = [make_entry("R1", ts(10, 0, 0, 0))]  # same second
    result = correlate_entries(left, right, window_seconds=2.0)
    assert len(result.pairs) == 1


def test_outside_window_no_pair():
    left = [make_entry("L1", ts(10, 0, 0))]
    right = [make_entry("R1", ts(10, 0, 5))]
    result = correlate_entries(left, right, window_seconds=1.0)
    assert len(result.pairs) == 0
    assert len(result.unmatched_left) == 1
    assert len(result.unmatched_right) == 1


def test_each_right_entry_used_at_most_once():
    left = [
        make_entry("L1", ts(10, 0, 0)),
        make_entry("L2", ts(10, 0, 0)),
    ]
    right = [make_entry("R1", ts(10, 0, 0))]
    result = correlate_entries(left, right, window_seconds=1.0)
    assert len(result.pairs) == 1
    assert len(result.unmatched_left) == 1


def test_no_timestamp_entries_go_to_unmatched():
    left = [make_entry("L1", None)]
    right = [make_entry("R1", None)]
    result = correlate_entries(left, right)
    assert result.pairs == []
    assert len(result.unmatched_left) == 1
    assert len(result.unmatched_right) == 1


def test_match_level_filters_mismatched_levels():
    left = [make_entry("L1", ts(10, 0, 0), level="ERROR")]
    right = [make_entry("R1", ts(10, 0, 0), level="INFO")]
    result = correlate_entries(left, right, window_seconds=5.0, match_level=True)
    assert len(result.pairs) == 0


def test_match_level_allows_same_level():
    left = [make_entry("L1", ts(10, 0, 0), level="ERROR")]
    right = [make_entry("R1", ts(10, 0, 0), level="ERROR")]
    result = correlate_entries(left, right, window_seconds=5.0, match_level=True)
    assert len(result.pairs) == 1


def test_nearest_neighbour_chosen():
    left = [make_entry("L1", ts(10, 0, 5))]
    right = [
        make_entry("R1", ts(10, 0, 4)),  # delta 1s
        make_entry("R2", ts(10, 0, 3)),  # delta 2s
    ]
    result = correlate_entries(left, right, window_seconds=5.0)
    assert len(result.pairs) == 1
    assert result.pairs[0].right.raw == "R1"


def test_as_dict_structure():
    le = make_entry("L1", ts(10, 0, 0))
    re = make_entry("R1", ts(10, 0, 0))
    result = correlate_entries([le], [re])
    d = result.as_dict()
    assert "pairs" in d
    assert "unmatched_left" in d
    assert "unmatched_right" in d
    assert "delta_seconds" in d["pairs"][0]


def test_empty_inputs_return_empty_result():
    result = correlate_entries([], [])
    assert result.pairs == []
    assert result.unmatched_left == []
    assert result.unmatched_right == []
