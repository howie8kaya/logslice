"""Tests for logslice.grep and logslice.cli_grep."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pytest

from logslice.grep import GrepResult, grep_entries, summarize_grep
from logslice.parser import LogEntry
from logslice.cli_grep import add_grep_args, handle_grep


def make_entry(raw: str, lineno: int = 1) -> LogEntry:
    return LogEntry(line_number=lineno, raw=raw, timestamp=None, level=None, message=raw, extra={})


ENTRIES = [
    make_entry("ERROR connection refused", 1),
    make_entry("INFO server started", 2),
    make_entry("WARNING disk usage high", 3),
    make_entry("ERROR timeout exceeded", 4),
    make_entry("DEBUG heartbeat ok", 5),
]


# --- grep_entries ---

def test_no_patterns_returns_all():
    results = grep_entries(ENTRIES, [])
    assert len(results) == len(ENTRIES)


def test_single_pattern_match():
    results = grep_entries(ENTRIES, ["ERROR"])
    assert len(results) == 2
    assert all("ERROR" in r.entry.raw for r in results)


def test_ignore_case():
    results = grep_entries(ENTRIES, ["error"], ignore_case=True)
    assert len(results) == 2


def test_or_logic_multiple_patterns():
    results = grep_entries(ENTRIES, ["ERROR", "INFO"])
    assert len(results) == 3


def test_and_logic_require_all():
    results = grep_entries(ENTRIES, ["ERROR", "timeout"], require_all=True)
    assert len(results) == 1
    assert "timeout" in results[0].entry.raw


def test_invert_match():
    results = grep_entries(ENTRIES, ["ERROR"], invert=True)
    assert len(results) == 3
    assert all("ERROR" not in r.entry.raw for r in results)


def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid regex"):
        grep_entries(ENTRIES, ["[invalid"])


def test_grep_result_as_dict():
    r = GrepResult(entry=ENTRIES[0], matched_patterns=["ERROR"], match_count=1)
    d = r.as_dict()
    assert d["matched_patterns"] == ["ERROR"]
    assert d["match_count"] == 1
    assert "raw" in d


# --- summarize_grep ---

def test_summarize_counts_patterns():
    results = grep_entries(ENTRIES, ["ERROR"])
    counts = summarize_grep(results)
    assert counts.get("ERROR") == 2


def test_summarize_empty_results():
    assert summarize_grep([]) == {}


# --- CLI ---

@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    add_grep_args(p)
    return p


def test_add_grep_args_registers_patterns(parser):
    args = parser.parse_args(["ERROR", "somefile.log"])
    assert args.patterns == ["ERROR"]


def test_add_grep_args_defaults(parser):
    args = parser.parse_args(["ERROR", "somefile.log"])
    assert args.ignore_case is False
    assert args.require_all is False
    assert args.invert is False
    assert args.summary is False


def test_handle_grep_missing_file(tmp_path, capsys):
    p = argparse.ArgumentParser()
    add_grep_args(p)
    args = p.parse_args(["ERROR", str(tmp_path / "nope.log")])
    code = handle_grep(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_handle_grep_output(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text("ERROR something bad\nINFO all good\nERROR again\n")
    p = argparse.ArgumentParser()
    add_grep_args(p)
    args = p.parse_args(["ERROR", str(log)])
    code = handle_grep(args)
    assert code == 0
    out = capsys.readouterr().out
    assert out.count("ERROR") == 2


def test_handle_grep_summary_output(tmp_path, capsys):
    log = tmp_path / "app.log"
    log.write_text("ERROR something\nINFO ok\n")
    p = argparse.ArgumentParser()
    add_grep_args(p)
    args = p.parse_args(["--summary", "ERROR", str(log)])
    code = handle_grep(args)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data.get("ERROR") == 1


def test_handle_grep_no_match_returns_1(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("INFO all good\n")
    p = argparse.ArgumentParser()
    add_grep_args(p)
    args = p.parse_args(["ERROR", str(log)])
    code = handle_grep(args)
    assert code == 1
