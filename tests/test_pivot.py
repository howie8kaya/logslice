"""Tests for logslice.pivot."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.pivot import PivotTable, _truncate, pivot_entries


def make_entry(
    raw: str = "log line",
    level: str = "INFO",
    timestamp: datetime | None = None,
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(
        line_number=1,
        raw=raw,
        timestamp=timestamp,
        level=level,
        message=raw,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# _truncate
# ---------------------------------------------------------------------------

def test_truncate_minute():
    ts = datetime(2024, 3, 15, 9, 47, 22)
    assert _truncate(ts, "minute") == "2024-03-15 09:47"


def test_truncate_hour():
    ts = datetime(2024, 3, 15, 9, 47, 22)
    assert _truncate(ts, "hour") == "2024-03-15 09"


def test_truncate_day():
    ts = datetime(2024, 3, 15, 9, 47, 22)
    assert _truncate(ts, "day") == "2024-03-15"


def test_truncate_unknown_raises():
    with pytest.raises(ValueError, match="Unknown bucket_size"):
        _truncate(datetime.now(), "week")


# ---------------------------------------------------------------------------
# pivot_entries
# ---------------------------------------------------------------------------

def test_empty_entries_returns_empty_buckets():
    table = pivot_entries([])
    assert isinstance(table, PivotTable)
    assert table.buckets == {}


def test_single_entry_creates_bucket():
    ts = datetime(2024, 1, 1, 12, 0, 0)
    entries = [make_entry(level="ERROR", timestamp=ts)]
    table = pivot_entries(entries, pivot_field="level", bucket_size="hour")
    assert "2024-01-01 12" in table.buckets
    assert table.buckets["2024-01-01 12"]["ERROR"] == 1


def test_multiple_entries_same_bucket():
    ts = datetime(2024, 1, 1, 12, 5, 0)
    entries = [
        make_entry(level="INFO", timestamp=ts),
        make_entry(level="INFO", timestamp=ts),
        make_entry(level="WARN", timestamp=ts),
    ]
    table = pivot_entries(entries, bucket_size="hour")
    bucket = table.buckets["2024-01-01 12"]
    assert bucket["INFO"] == 2
    assert bucket["WARN"] == 1


def test_entries_spread_across_buckets():
    entries = [
        make_entry(level="DEBUG", timestamp=datetime(2024, 1, 1, 10, 0)),
        make_entry(level="DEBUG", timestamp=datetime(2024, 1, 1, 11, 0)),
    ]
    table = pivot_entries(entries, bucket_size="hour")
    assert len(table.buckets) == 2


def test_no_timestamp_goes_to_special_bucket():
    entries = [make_entry(level="INFO", timestamp=None)]
    table = pivot_entries(entries)
    assert "(no timestamp)" in table.buckets
    assert table.buckets["(no timestamp)"]["INFO"] == 1


def test_pivot_on_extra_field():
    entries = [
        make_entry(timestamp=datetime(2024, 6, 1, 8), extra={"service": "api"}),
        make_entry(timestamp=datetime(2024, 6, 1, 8), extra={"service": "worker"}),
        make_entry(timestamp=datetime(2024, 6, 1, 8), extra={"service": "api"}),
    ]
    table = pivot_entries(entries, pivot_field="service", bucket_size="day")
    bucket = table.buckets["2024-06-01"]
    assert bucket["api"] == 2
    assert bucket["worker"] == 1


def test_as_dict_contains_expected_keys():
    table = pivot_entries([], pivot_field="level", bucket_size="minute")
    d = table.as_dict()
    assert d["bucket_size"] == "minute"
    assert d["pivot_field"] == "level"
    assert isinstance(d["buckets"], dict)


def test_buckets_are_sorted_chronologically():
    entries = [
        make_entry(level="INFO", timestamp=datetime(2024, 1, 1, 14)),
        make_entry(level="INFO", timestamp=datetime(2024, 1, 1, 9)),
    ]
    table = pivot_entries(entries, bucket_size="hour")
    keys = list(table.buckets.keys())
    assert keys == sorted(keys)
