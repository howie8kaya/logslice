"""Tests for logslice.export module."""

import csv
import json
import os
import pytest

from datetime import datetime
from logslice.parser import LogEntry
from logslice.export import export_entries, SUPPORTED_FORMATS


def make_entry(line_number=1, raw="INFO hello", level="INFO", message="hello", ts=None):
    e = LogEntry(line_number=line_number, raw=raw)
    e.level = level
    e.message = message
    e.timestamp = ts or datetime(2024, 1, 15, 10, 0, 0)
    return e


@pytest.fixture()
def entries():
    return [
        make_entry(1, "INFO startup complete", "INFO", "startup complete"),
        make_entry(2, "ERROR disk full", "ERROR", "disk full"),
        make_entry(3, "DEBUG checking queue", "DEBUG", "checking queue"),
    ]


def test_export_json_creates_file(tmp_path, entries):
    out = tmp_path / "out.json"
    fmt = export_entries(entries, str(out))
    assert fmt == "json"
    assert out.exists()


def test_export_json_content(tmp_path, entries):
    out = tmp_path / "out.json"
    export_entries(entries, str(out))
    data = json.loads(out.read_text())
    assert len(data) == 3
    assert data[0]["level"] == "INFO"
    assert data[1]["level"] == "ERROR"


def test_export_csv_creates_file(tmp_path, entries):
    out = tmp_path / "out.csv"
    fmt = export_entries(entries, str(out))
    assert fmt == "csv"
    assert out.exists()


def test_export_csv_content(tmp_path, entries):
    out = tmp_path / "out.csv"
    export_entries(entries, str(out))
    rows = list(csv.DictReader(out.open(newline="", encoding="utf-8")))
    assert len(rows) == 3
    assert rows[0]["level"] == "INFO"
    assert rows[1]["message"] == "disk full"


def test_export_txt_creates_file(tmp_path, entries):
    out = tmp_path / "out.txt"
    fmt = export_entries(entries, str(out))
    assert fmt == "txt"
    lines = out.read_text().splitlines()
    assert lines[0] == "INFO startup complete"


def test_format_inferred_from_extension(tmp_path, entries):
    out = tmp_path / "report.csv"
    fmt = export_entries(entries, str(out))
    assert fmt == "csv"


def test_explicit_format_overrides_extension(tmp_path, entries):
    out = tmp_path / "report.csv"
    fmt = export_entries(entries, str(out), fmt="json")
    assert fmt == "json"
    data = json.loads(out.read_text())
    assert isinstance(data, list)


def test_unsupported_format_raises(tmp_path, entries):
    out = tmp_path / "out.xml"
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_entries(entries, str(out), fmt="xml")


def test_export_empty_entries(tmp_path):
    out = tmp_path / "empty.json"
    export_entries([], str(out))
    data = json.loads(out.read_text())
    assert data == []


def test_nested_output_dir_created(tmp_path, entries):
    out = tmp_path / "a" / "b" / "out.txt"
    export_entries(entries, str(out))
    assert out.exists()
