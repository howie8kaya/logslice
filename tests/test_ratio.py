"""Tests for logslice.ratio module."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.ratio import LevelRatio, RatioReport, compute_ratio


def make_entry(level: Optional[str] = None, raw: str = "log line") -> LogEntry:
    return LogEntry(line_number=1, raw=raw, timestamp=None, level=level, message=raw, extra={})


def test_empty_entries_returns_zero_report():
    report = compute_ratio([])
    assert report.total == 0
    assert report.error_ratio == 0.0
    assert report.warn_ratio == 0.0
    assert report.levels == []


def test_total_count():
    entries = [make_entry("INFO")] * 5
    report = compute_ratio(entries)
    assert report.total == 5


def test_single_level_ratio_is_one():
    entries = [make_entry("INFO")] * 4
    report = compute_ratio(entries)
    assert len(report.levels) == 1
    assert report.levels[0].level == "INFO"
    assert report.levels[0].ratio == pytest.approx(1.0)
    assert report.levels[0].percent == pytest.approx(100.0)


def test_error_ratio_counted_correctly():
    entries = [make_entry("ERROR")] * 2 + [make_entry("INFO")] * 8
    report = compute_ratio(entries)
    assert report.error_ratio == pytest.approx(0.2)


def test_critical_included_in_error_ratio():
    entries = [make_entry("CRITICAL")] * 1 + [make_entry("ERROR")] * 1 + [make_entry("INFO")] * 8
    report = compute_ratio(entries)
    assert report.error_ratio == pytest.approx(0.2)


def test_warn_ratio_counted_correctly():
    entries = [make_entry("WARNING")] * 3 + [make_entry("INFO")] * 7
    report = compute_ratio(entries)
    assert report.warn_ratio == pytest.approx(0.3)


def test_warn_alias_included():
    entries = [make_entry("WARN")] * 2 + [make_entry("WARNING")] * 2 + [make_entry("INFO")] * 6
    report = compute_ratio(entries)
    assert report.warn_ratio == pytest.approx(0.4)


def test_unknown_level_grouped_as_unknown():
    entries = [make_entry(None)] * 3 + [make_entry("INFO")] * 7
    report = compute_ratio(entries)
    levels_map = {lr.level: lr for lr in report.levels}
    assert "UNKNOWN" in levels_map
    assert levels_map["UNKNOWN"].count == 3


def test_levels_sorted_by_count_descending():
    entries = [make_entry("DEBUG")] * 1 + [make_entry("INFO")] * 5 + [make_entry("ERROR")] * 3
    report = compute_ratio(entries)
    counts = [lr.count for lr in report.levels]
    assert counts == sorted(counts, reverse=True)


def test_as_dict_has_expected_keys():
    entries = [make_entry("INFO")] * 2 + [make_entry("ERROR")] * 1
    report = compute_ratio(entries)
    d = report.as_dict()
    assert set(d.keys()) == {"total", "error_ratio", "warn_ratio", "levels"}
    assert isinstance(d["levels"], list)
    for lr in d["levels"]:
        assert set(lr.keys()) == {"level", "count", "total", "ratio", "percent"}


def test_level_ratio_percent_matches_ratio():
    lr = LevelRatio(level="INFO", count=1, total=4)
    assert lr.percent == pytest.approx(lr.ratio * 100)


def test_level_ratio_zero_total_safe():
    lr = LevelRatio(level="INFO", count=0, total=0)
    assert lr.ratio == 0.0
    assert lr.percent == 0.0
