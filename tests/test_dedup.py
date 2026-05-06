"""Tests for logslice.dedup."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.dedup import _normalize, count_duplicates, dedup_entries
from logslice.parser import LogEntry


def make_entry(
    raw: str,
    lineno: int = 1,
    level: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(lineno=lineno, raw=raw, level=level, timestamp=timestamp, groups={})


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

def test_normalize_strips_whitespace():
    assert _normalize("  hello  ") == "hello"


def test_normalize_lowercases():
    assert _normalize("ERROR Occurred") == "error occurred"


def test_normalize_replaces_numbers_when_enabled():
    assert _normalize("retry 3 times") == "retry <n> times"


def test_normalize_keeps_numbers_when_disabled():
    assert _normalize("retry 3 times", ignore_numbers=False) == "retry 3 times"


# ---------------------------------------------------------------------------
# dedup_entries — keep='first'
# ---------------------------------------------------------------------------

def test_dedup_removes_exact_duplicates():
    entries = [
        make_entry("connection refused", lineno=1),
        make_entry("connection refused", lineno=2),
        make_entry("connection refused", lineno=3),
    ]
    result = dedup_entries(entries)
    assert len(result) == 1
    assert result[0].lineno == 1


def test_dedup_keep_last():
    entries = [
        make_entry("disk full", lineno=1),
        make_entry("disk full", lineno=5),
    ]
    result = dedup_entries(entries, keep="last")
    assert len(result) == 1
    assert result[0].lineno == 5


def test_dedup_treats_numeric_variants_as_same():
    entries = [
        make_entry("timeout after 3s", lineno=1),
        make_entry("timeout after 10s", lineno=2),
    ]
    result = dedup_entries(entries, ignore_numbers=True)
    assert len(result) == 1


def test_dedup_numeric_variants_kept_when_disabled():
    entries = [
        make_entry("timeout after 3s", lineno=1),
        make_entry("timeout after 10s", lineno=2),
    ]
    result = dedup_entries(entries, ignore_numbers=False)
    assert len(result) == 2


def test_dedup_preserves_unique_entries():
    entries = [
        make_entry("alpha", lineno=1),
        make_entry("beta", lineno=2),
        make_entry("gamma", lineno=3),
    ]
    result = dedup_entries(entries)
    assert len(result) == 3


def test_dedup_invalid_keep_raises():
    with pytest.raises(ValueError):
        dedup_entries([], keep="middle")


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

def test_count_duplicates_basic():
    entries = [
        make_entry("disk full", lineno=1),
        make_entry("disk full", lineno=2),
        make_entry("oom killed", lineno=3),
    ]
    counts = count_duplicates(entries)
    assert counts["disk full"] == 2
    assert counts["oom killed"] == 1
