"""Tests for logslice.parser module."""

import pytest
from logslice.parser import LogParser, LogEntry


SAMPLE_LINES = [
    "2024-01-01 INFO  Server started\n",
    "2024-01-01 ERROR Failed to connect\n",
    "2024-01-01 DEBUG Checking health\n",
    "2024-01-01 ERROR Timeout reached\n",
]


def test_parse_all_lines_no_pattern():
    parser = LogParser()
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert len(entries) == 4
    assert all(isinstance(e, LogEntry) for e in entries)


def test_parse_with_pattern_filters():
    parser = LogParser(pattern="ERROR")
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert len(entries) == 2
    assert all("ERROR" in e.raw for e in entries)


def test_line_numbers_are_correct():
    parser = LogParser()
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert [e.line_number for e in entries] == [1, 2, 3, 4]


def test_named_groups_captured():
    parser = LogParser(pattern=r"(?P<level>ERROR|INFO|DEBUG)")
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert entries[0].matched_groups["level"] == "INFO"
    assert entries[1].matched_groups["level"] == "ERROR"


def test_ignore_case():
    parser = LogParser(pattern="error", ignore_case=True)
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert len(entries) == 2


def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        LogParser(pattern="[unclosed")


def test_no_matches_returns_empty():
    parser = LogParser(pattern="CRITICAL")
    entries = list(parser.parse_lines(SAMPLE_LINES))
    assert entries == []


def test_to_dict_structure():
    parser = LogParser(pattern=r"(?P<level>\w+)")
    entries = list(parser.parse_lines(["INFO hello\n"]))
    d = entries[0].to_dict()
    assert "line_number" in d
    assert "raw" in d
    assert "matched_groups" in d
