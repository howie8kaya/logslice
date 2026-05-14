"""Tests for logslice.diff."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.diff import diff_entries, format_diff, DiffResult


def make_entry(raw: str, line_no: int = 1) -> LogEntry:
    return LogEntry(
        line_number=line_no,
        raw=raw,
        timestamp=None,
        level=None,
        message=raw.strip(),
        extra={},
    )


# ---------------------------------------------------------------------------
# diff_entries
# ---------------------------------------------------------------------------

def test_identical_lists_produce_no_diff():
    entries = [make_entry("foo bar"), make_entry("baz qux")]
    result = diff_entries(entries, entries)
    assert result.added == []
    assert result.removed == []
    assert len(result.common) == 2


def test_added_lines_detected():
    baseline = [make_entry("line one")]
    current = [make_entry("line one"), make_entry("line two")]
    result = diff_entries(baseline, current)
    assert len(result.added) == 1
    assert result.added[0].raw == "line two"
    assert result.removed == []


def test_removed_lines_detected():
    baseline = [make_entry("line one"), make_entry("line two")]
    current = [make_entry("line one")]
    result = diff_entries(baseline, current)
    assert len(result.removed) == 1
    assert result.removed[0].raw == "line two"
    assert result.added == []


def test_empty_baseline_all_added():
    current = [make_entry("new line")]
    result = diff_entries([], current)
    assert len(result.added) == 1
    assert result.removed == []
    assert result.common == []


def test_empty_current_all_removed():
    baseline = [make_entry("old line")]
    result = diff_entries(baseline, [])
    assert len(result.removed) == 1
    assert result.added == []


def test_ignore_case_matches_differently_cased_lines():
    baseline = [make_entry("ERROR: disk full")]
    current = [make_entry("error: disk full")]
    result = diff_entries(baseline, current, ignore_case=True)
    assert result.added == []
    assert result.removed == []
    assert len(result.common) == 1


def test_case_sensitive_by_default_treats_as_different():
    baseline = [make_entry("ERROR: disk full")]
    current = [make_entry("error: disk full")]
    result = diff_entries(baseline, current, ignore_case=False)
    assert len(result.added) == 1
    assert len(result.removed) == 1


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_has_expected_keys():
    result = DiffResult(
        added=[make_entry("a")],
        removed=[make_entry("b")],
        common=[make_entry("c")],
    )
    d = result.as_dict()
    assert "added" in d
    assert "removed" in d
    assert d["added_count"] == 1
    assert d["removed_count"] == 1
    assert d["common_count"] == 1


# ---------------------------------------------------------------------------
# format_diff
# ---------------------------------------------------------------------------

def test_format_diff_removed_prefix():
    result = DiffResult(removed=[make_entry("gone")], added=[], common=[])
    lines = format_diff(result, color=False)
    assert any(l.startswith("- ") for l in lines)


def test_format_diff_added_prefix():
    result = DiffResult(added=[make_entry("new")], removed=[], common=[])
    lines = format_diff(result, color=False)
    assert any(l.startswith("+ ") for l in lines)


def test_format_diff_color_contains_ansi():
    result = DiffResult(added=[make_entry("new")], removed=[make_entry("old")], common=[])
    lines = format_diff(result, color=True)
    combined = "".join(lines)
    assert "\033[" in combined
