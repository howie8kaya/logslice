"""Tests for logslice.annotate."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.annotate import AnnotationRule, annotate_entries


def make_entry(raw: str, level: str = "INFO", line_number: int = 1) -> LogEntry:
    return LogEntry(
        line_number=line_number,
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
        extras={},
    )


RULES = [
    {"label": "error", "pattern": r"error", "ignore_case": True},
    {"label": "timeout", "pattern": r"timeout"},
    {"label": "db", "pattern": r"database|db", "ignore_case": True},
]


def test_annotation_rule_matches():
    rule = AnnotationRule(label="error", pattern=r"error", ignore_case=True)
    assert rule.matches("ERROR: something went wrong")
    assert not rule.matches("all good")


def test_annotation_rule_case_sensitive():
    rule = AnnotationRule(label="error", pattern=r"error", ignore_case=False)
    assert not rule.matches("ERROR: something")
    assert rule.matches("error: something")


def test_no_rules_returns_empty_annotations():
    entries = [make_entry("hello world")]
    result = annotate_entries(entries, [])
    assert result[0].extras["annotations"] == []


def test_single_matching_rule():
    entries = [make_entry("Connection timeout reached")]
    result = annotate_entries(entries, RULES)
    assert "timeout" in result[0].extras["annotations"]


def test_multiple_labels_multi_true():
    entries = [make_entry("ERROR connecting to database")]
    result = annotate_entries(entries, RULES, multi=True)
    labels = result[0].extras["annotations"]
    assert "error" in labels
    assert "db" in labels


def test_multi_false_stops_at_first_match():
    entries = [make_entry("ERROR connecting to database")]
    result = annotate_entries(entries, RULES, multi=False)
    labels = result[0].extras["annotations"]
    assert len(labels) == 1
    assert labels[0] == "error"


def test_no_match_gives_empty_list():
    entries = [make_entry("everything is fine")]
    result = annotate_entries(entries, RULES)
    assert result[0].extras["annotations"] == []


def test_original_extras_preserved():
    entry = make_entry("db error")
    entry.extras["source"] = "app.log"
    result = annotate_entries([entry], RULES)
    assert result[0].extras["source"] == "app.log"
    assert "annotations" in result[0].extras


def test_entry_fields_unchanged():
    entry = make_entry("timeout occurred", level="WARN", line_number=42)
    result = annotate_entries([entry], RULES)
    r = result[0]
    assert r.line_number == 42
    assert r.level == "WARN"
    assert r.raw == "timeout occurred"


def test_multiple_entries_annotated_independently():
    entries = [
        make_entry("db connection failed", line_number=1),
        make_entry("request timeout", line_number=2),
        make_entry("all systems normal", line_number=3),
    ]
    result = annotate_entries(entries, RULES)
    assert "db" in result[0].extras["annotations"]
    assert "timeout" in result[1].extras["annotations"]
    assert result[2].extras["annotations"] == []
