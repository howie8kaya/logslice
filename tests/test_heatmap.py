"""Tests for logslice.heatmap."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.heatmap import build_heatmap, DAYS, HOURS, Heatmap
from logslice.parser import LogEntry


def make_entry(ts: Optional[datetime] = None, raw: str = "log line") -> LogEntry:
    return LogEntry(line_number=1, raw=raw, timestamp=ts, level=None, message=raw, extra={})


def _ts(weekday: int, hour: int) -> datetime:
    """weekday: 0=Mon … 6=Sun"""
    # 2024-01-01 is a Monday
    base_day = 0  # Monday
    delta_days = weekday - base_day
    return datetime(2024, 1, 1 + delta_days, hour, 0, 0)


def test_empty_entries_returns_zero_heatmap():
    hm = build_heatmap([])
    assert hm.skipped == 0
    assert all(c.count == 0 for c in hm.cells)


def test_cells_cover_all_days_and_hours():
    hm = build_heatmap([])
    assert len(hm.cells) == len(DAYS) * len(HOURS)


def test_single_entry_increments_correct_cell():
    entry = make_entry(ts=_ts(0, 9))  # Monday 09:00
    hm = build_heatmap([entry])
    grid = hm.grid()
    assert grid["Mon"][9] == 1
    # all other cells zero
    total = sum(c.count for c in hm.cells)
    assert total == 1


def test_multiple_entries_same_slot():
    entries = [make_entry(ts=_ts(2, 14)) for _ in range(5)]  # Wed 14:00
    hm = build_heatmap(entries)
    assert hm.grid()["Wed"][14] == 5


def test_entries_without_timestamp_counted_as_skipped():
    entries = [make_entry(ts=None) for _ in range(3)]
    hm = build_heatmap(entries)
    assert hm.skipped == 3
    assert all(c.count == 0 for c in hm.cells)


def test_mixed_entries_skipped_and_counted():
    entries = [
        make_entry(ts=_ts(4, 23)),  # Fri 23:00
        make_entry(ts=None),
        make_entry(ts=_ts(4, 23)),
    ]
    hm = build_heatmap(entries)
    assert hm.skipped == 1
    assert hm.grid()["Fri"][23] == 2


def test_as_dict_structure():
    hm = build_heatmap([make_entry(ts=_ts(1, 6))])
    d = hm.as_dict()
    assert "cells" in d
    assert "skipped" in d
    assert isinstance(d["cells"], list)
    first = d["cells"][0]
    assert {"day", "hour", "count"} == set(first.keys())


def test_grid_returns_all_days():
    hm = build_heatmap([])
    grid = hm.grid()
    assert set(grid.keys()) == set(DAYS)


def test_saturday_sunday_entries():
    entries = [
        make_entry(ts=_ts(5, 0)),   # Sat 00:00
        make_entry(ts=_ts(6, 23)),  # Sun 23:00
    ]
    hm = build_heatmap(entries)
    assert hm.grid()["Sat"][0] == 1
    assert hm.grid()["Sun"][23] == 1
