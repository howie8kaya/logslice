"""Tests for logslice.sample and logslice.cli_sample."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.sample import sample_entries, SampleResult
from logslice.cli_sample import add_sample_args, handle_sample


def make_entry(i: int) -> LogEntry:
    return LogEntry(
        line_number=i,
        raw=f"INFO line {i}",
        timestamp=datetime(2024, 1, 1, 0, i % 60),
        level="INFO",
        message=f"line {i}",
        extra={},
    )


ENTRIES: List[LogEntry] = [make_entry(i) for i in range(1, 21)]  # 20 entries


def test_sample_n_returns_correct_count():
    result = sample_entries(ENTRIES, n=5)
    assert isinstance(result, SampleResult)
    assert result.sampled == 5
    assert len(result.entries) == 5
    assert result.total == 20


def test_sample_fraction_returns_correct_count():
    result = sample_entries(ENTRIES, fraction=0.5)
    assert result.sampled == 10
    assert len(result.entries) == 10


def test_sample_seed_is_deterministic():
    r1 = sample_entries(ENTRIES, n=7, seed=42)
    r2 = sample_entries(ENTRIES, n=7, seed=42)
    assert [e.line_number for e in r1.entries] == [e.line_number for e in r2.entries]


def test_sample_different_seeds_differ():
    r1 = sample_entries(ENTRIES, n=10, seed=1)
    r2 = sample_entries(ENTRIES, n=10, seed=99)
    # With 20 entries and 10 drawn it's astronomically unlikely they match
    assert [e.line_number for e in r1.entries] != [e.line_number for e in r2.entries]


def test_sample_n_larger_than_total_clamps():
    result = sample_entries(ENTRIES, n=100)
    assert result.sampled == 20


def test_sample_empty_entries():
    result = sample_entries([], n=5)
    assert result.total == 0
    assert result.sampled == 0
    assert result.entries == []


def test_sample_fraction_invalid_raises():
    with pytest.raises(ValueError, match="fraction"):
        sample_entries(ENTRIES, fraction=1.5)


def test_sample_no_args_raises():
    with pytest.raises(ValueError):
        sample_entries(ENTRIES)


def test_sample_both_args_raises():
    with pytest.raises(ValueError):
        sample_entries(ENTRIES, n=3, fraction=0.5)


def test_as_dict_keys():
    result = sample_entries(ENTRIES, n=3, seed=0)
    d = result.as_dict()
    assert set(d.keys()) == {"total", "sampled", "entries"}
    assert len(d["entries"]) == 3


# --- CLI tests ---


def _make_ns(**kwargs) -> argparse.Namespace:
    defaults = {"sample_n": None, "sample_frac": None, "sample_seed": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_sample_args_registers_n():
    p = argparse.ArgumentParser()
    add_sample_args(p)
    ns = p.parse_args(["--sample-n", "4"])
    assert ns.sample_n == 4


def test_add_sample_args_registers_frac():
    p = argparse.ArgumentParser()
    add_sample_args(p)
    ns = p.parse_args(["--sample-frac", "0.25"])
    assert ns.sample_frac == pytest.approx(0.25)


def test_add_sample_args_mutually_exclusive():
    p = argparse.ArgumentParser()
    add_sample_args(p)
    with pytest.raises(SystemExit):
        p.parse_args(["--sample-n", "3", "--sample-frac", "0.1"])


def test_handle_sample_no_sampling_returns_zero():
    ns = _make_ns()
    assert handle_sample(ns, ENTRIES) == 0


def test_handle_sample_runs_and_returns_zero(capsys):
    ns = _make_ns(sample_n=5, sample_seed=7)
    code = handle_sample(ns, ENTRIES)
    assert code == 0
    captured = capsys.readouterr()
    assert "sampled 5 of 20" in captured.err


def test_handle_sample_bad_fraction_returns_one(capsys):
    ns = _make_ns(sample_frac=2.0)
    code = handle_sample(ns, ENTRIES)
    assert code == 1
    assert "sample error" in capsys.readouterr().err
