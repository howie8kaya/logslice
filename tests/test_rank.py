"""Tests for logslice.rank."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.rank import RankedEntry, rank_entries, _message_key


def make_entry(
    raw: str,
    level: Optional[str] = None,
    line_number: int = 1,
    timestamp: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(
        raw=raw,
        line_number=line_number,
        timestamp=timestamp,
        level=level,
        groups={},
    )


def test_empty_entries_returns_empty():
    assert rank_entries([]) == []


def test_single_entry_ranked_once():
    entries = [make_entry("connection refused", level="ERROR")]
    result = rank_entries(entries)
    assert len(result) == 1
    assert result[0].count == 1


def test_duplicate_messages_grouped():
    entries = [
        make_entry("disk full", level="ERROR", line_number=1),
        make_entry("disk full", level="ERROR", line_number=2),
        make_entry("disk full", level="ERROR", line_number=3),
    ]
    result = rank_entries(entries)
    assert len(result) == 1
    assert result[0].count == 3


def test_top_n_limits_results():
    entries = [make_entry(f"msg {i}", line_number=i) for i in range(20)]
    result = rank_entries(entries, top_n=5)
    assert len(result) == 5


def test_rank_by_count_descending():
    entries = (
        [make_entry("alpha", line_number=i) for i in range(5)]
        + [make_entry("beta", line_number=i + 100) for i in range(2)]
    )
    result = rank_entries(entries, by="count")
    assert result[0].raw == "alpha"
    assert result[0].count == 5
    assert result[1].count == 2


def test_rank_by_weight_prefers_critical():
    entries = (
        [make_entry("info msg", level="INFO", line_number=i) for i in range(10)]
        + [make_entry("fatal boom", level="CRITICAL", line_number=i + 100) for i in range(2)]
    )
    result = rank_entries(entries, by="weight")
    # critical * 2 = 10, info * 10 = 20 — count wins for info but weight flips it
    # critical weight=5 * 2=10, info weight=2 * 10=20 → info still on top by score
    assert result[0].level == "INFO"  # 20 > 10


def test_rank_by_weight_critical_beats_low_count_info():
    entries = (
        [make_entry("minor note", level="INFO", line_number=i) for i in range(1)]
        + [make_entry("fatal boom", level="CRITICAL", line_number=i + 100) for i in range(1)]
    )
    result = rank_entries(entries, by="weight")
    assert result[0].level == "CRITICAL"


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown ranking strategy"):
        rank_entries([make_entry("x")], by="bogus")


def test_ranked_entry_as_dict():
    entry = make_entry("test message", level="WARN", line_number=7)
    r = RankedEntry(raw="test message", count=3, level="WARN", example=entry)
    d = r.as_dict()
    assert d["count"] == 3
    assert d["level"] == "WARN"
    assert d["example_line"] == 7
    assert "raw" in d


def test_message_key_strips_timestamp_prefix():
    entry = make_entry("2024-01-01T12:00:00 ERROR disk full")
    key = _message_key(entry)
    assert not key.startswith("2024")
    assert "disk full" in key
