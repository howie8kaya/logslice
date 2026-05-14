"""Tests for logslice.formatter module."""

import json
import csv
import io
import pytest
from logslice.parser import LogEntry
from logslice.formatter import format_entries, FORMAT_PLAIN, FORMAT_JSON, FORMAT_CSV


def make_entries():
    return [
        LogEntry(line_number=1, raw="INFO  Server started\n", matched_groups={"level": "INFO"}),
        LogEntry(line_number=3, raw="ERROR Failed\n", matched_groups={"level": "ERROR"}),
    ]


def test_plain_format_contains_line_numbers():
    output = format_entries(make_entries(), FORMAT_PLAIN)
    assert "[1]" in output
    assert "[3]" in output


def test_plain_format_contains_raw_text():
    output = format_entries(make_entries(), FORMAT_PLAIN)
    assert "INFO  Server started" in output
    assert "ERROR Failed" in output


def test_json_format_is_valid_json():
    output = format_entries(make_entries(), FORMAT_JSON)
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 2


def test_json_format_has_expected_keys():
    output = format_entries(make_entries(), FORMAT_JSON)
    data = json.loads(output)
    for item in data:
        assert "line_number" in item
        assert "raw" in item
        assert "matched_groups" in item


def test_json_format_preserves_matched_groups():
    """Ensure matched_groups values are correctly serialized in JSON output."""
    output = format_entries(make_entries(), FORMAT_JSON)
    data = json.loads(output)
    assert data[0]["matched_groups"] == {"level": "INFO"}
    assert data[1]["matched_groups"] == {"level": "ERROR"}


def test_csv_format_has_header():
    output = format_entries(make_entries(), FORMAT_CSV)
    reader = csv.DictReader(io.StringIO(output))
    assert reader.fieldnames == ["line_number", "raw", "matched_groups"]


def test_csv_format_row_count():
    output = format_entries(make_entries(), FORMAT_CSV)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 2


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        format_entries(make_entries(), "xml")


def test_empty_entries_plain():
    output = format_entries([], FORMAT_PLAIN)
    assert output == ""


def test_empty_entries_json():
    output = format_entries([], FORMAT_JSON)
    assert json.loads(output) == []


def test_empty_entries_csv():
    """Empty entries should still produce a CSV header with no data rows."""
    output = format_entries([], FORMAT_CSV)
    reader = csv.DictReader(io.StringIO(output))
    assert reader.fieldnames == ["line_number", "raw", "matched_groups"]
    assert list(reader) == []
