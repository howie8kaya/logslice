"""Tests for logslice.context and logslice.cli_context."""

import argparse
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.context import extract_with_context, find_matched_indices
from logslice.cli_context import add_context_args, handle_context


def make_entry(line_no: int, text: str = "") -> LogEntry:
    return LogEntry(
        line_number=line_no,
        raw=text or f"line {line_no}",
        timestamp=None,
        level=None,
        message=text or f"line {line_no}",
        extra={},
    )


ENTRIES = [make_entry(i, f"msg {i}") for i in range(10)]


# --- extract_with_context ---

def test_no_matches_returns_empty():
    assert extract_with_context(ENTRIES, []) == []


def test_match_only_no_context():
    result = extract_with_context(ENTRIES, [3], before=0, after=0)
    assert len(result) == 1
    entry, is_match = result[0]
    assert entry.line_number == 3
    assert is_match is True


def test_before_context():
    result = extract_with_context(ENTRIES, [5], before=2, after=0)
    line_numbers = [e.line_number for e, _ in result]
    assert line_numbers == [3, 4, 5]
    flags = [m for _, m in result]
    assert flags == [False, False, True]


def test_after_context():
    result = extract_with_context(ENTRIES, [5], before=0, after=2)
    line_numbers = [e.line_number for e, _ in result]
    assert line_numbers == [5, 6, 7]


def test_context_clamps_at_boundaries():
    result = extract_with_context(ENTRIES, [0], before=5, after=0)
    assert result[0][0].line_number == 0
    assert len(result) == 1


def test_overlapping_contexts_deduplicated():
    result = extract_with_context(ENTRIES, [3, 5], before=2, after=0)
    line_numbers = [e.line_number for e, _ in result]
    assert len(line_numbers) == len(set(line_numbers)), "duplicates found"
    assert 3 in line_numbers and 5 in line_numbers


# --- find_matched_indices ---

def test_find_matched_indices_basic():
    filtered = [ENTRIES[2], ENTRIES[7]]
    indices = find_matched_indices(ENTRIES, filtered)
    assert indices == [2, 7]


def test_find_matched_indices_empty_filtered():
    assert find_matched_indices(ENTRIES, []) == []


# --- CLI helpers ---

def _make_args(**kwargs):
    defaults = {"before": 0, "after": 0, "context": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_context_args_registers_before():
    p = argparse.ArgumentParser()
    add_context_args(p)
    args = p.parse_args(["-B", "3"])
    assert args.before == 3


def test_add_context_args_registers_after():
    p = argparse.ArgumentParser()
    add_context_args(p)
    args = p.parse_args(["-A", "2"])
    assert args.after == 2


def test_add_context_args_registers_context_shorthand():
    p = argparse.ArgumentParser()
    add_context_args(p)
    args = p.parse_args(["-C", "4"])
    assert args.context == 4


def test_handle_context_no_context_returns_all_matched():
    filtered = [ENTRIES[2], ENTRIES[5]]
    result = handle_context(_make_args(), ENTRIES, filtered)
    assert all(is_match for _, is_match in result)
    assert len(result) == 2


def test_handle_context_shorthand_overrides_before_after():
    args = _make_args(before=1, after=1, context=3)
    filtered = [ENTRIES[5]]
    result = handle_context(args, ENTRIES, filtered)
    line_numbers = [e.line_number for e, _ in result]
    assert 2 in line_numbers and 8 in line_numbers
