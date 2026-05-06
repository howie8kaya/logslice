"""Integration tests for the --export CLI flag."""

import json
import csv
import pytest

from unittest.mock import patch, MagicMock
from logslice.cli_export import add_export_args, handle_export
from logslice.parser import LogEntry
from datetime import datetime
import argparse


def make_entry(n, raw, level="INFO"):
    e = LogEntry(line_number=n, raw=raw)
    e.level = level
    e.message = raw
    e.timestamp = datetime(2024, 3, 1, 12, n, 0)
    return e


@pytest.fixture()
def entries():
    return [
        make_entry(1, "INFO boot"),
        make_entry(2, "ERROR crash", "ERROR"),
    ]


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    add_export_args(p)
    return p


def test_add_export_args_registers_export(parser):
    args = parser.parse_args(["--export", "out.json"])
    assert args.export == "out.json"


def test_add_export_args_registers_format(parser):
    args = parser.parse_args(["--export", "out.txt", "--export-format", "csv"])
    assert args.export_format == "csv"


def test_handle_export_returns_false_when_no_export(entries):
    args = argparse.Namespace(export=None, export_format=None)
    result = handle_export(args, entries)
    assert result is False


def test_handle_export_returns_true_and_writes_file(tmp_path, entries):
    out = tmp_path / "result.json"
    args = argparse.Namespace(export=str(out), export_format=None)
    result = handle_export(args, entries)
    assert result is True
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data) == 2


def test_handle_export_csv(tmp_path, entries):
    out = tmp_path / "result.csv"
    args = argparse.Namespace(export=str(out), export_format=None)
    handle_export(args, entries)
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 2


def test_handle_export_explicit_format(tmp_path, entries):
    out = tmp_path / "result.txt"
    args = argparse.Namespace(export=str(out), export_format="json")
    handle_export(args, entries)
    data = json.loads(out.read_text())
    assert isinstance(data, list)


def test_handle_export_bad_format_exits(tmp_path, entries, capsys):
    out = tmp_path / "result.txt"
    args = argparse.Namespace(export=str(out), export_format="xml")
    with pytest.raises(SystemExit):
        handle_export(args, entries)
    captured = capsys.readouterr()
    assert "Unsupported export format" in captured.err


def test_handle_export_prints_summary(tmp_path, entries, capsys):
    out = tmp_path / "result.json"
    args = argparse.Namespace(export=str(out), export_format=None)
    handle_export(args, entries)
    captured = capsys.readouterr()
    assert "Exported 2 entries" in captured.err
