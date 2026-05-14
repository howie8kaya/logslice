"""Tests for logslice.cluster."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.cluster import _signature, cluster_entries, Cluster


def make_entry(
    raw: str,
    level: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(raw=raw, level=level, timestamp=timestamp, line_number=1, extra={})


# ---------------------------------------------------------------------------
# _signature
# ---------------------------------------------------------------------------

def test_signature_replaces_integers():
    assert _signature("connected 42 clients") == "connected <VAR> clients"


def test_signature_replaces_ip_addresses():
    sig = _signature("request from 192.168.1.10 failed")
    assert "<VAR>" in sig
    assert "192.168.1.10" not in sig


def test_signature_replaces_hex_tokens():
    sig = _signature("token=deadbeef1234abcd expired")
    assert "deadbeef1234abcd" not in sig


def test_signature_keeps_plain_words():
    assert _signature("server started") == "server started"


# ---------------------------------------------------------------------------
# cluster_entries
# ---------------------------------------------------------------------------

def test_empty_entries_returns_empty_list():
    assert cluster_entries([]) == []


def test_single_entry_forms_one_cluster():
    entries = [make_entry("user 1 logged in", level="info")]
    clusters = cluster_entries(entries)
    assert len(clusters) == 1
    assert clusters[0].count == 1


def test_similar_entries_grouped_together():
    entries = [
        make_entry("user 1 logged in", level="info"),
        make_entry("user 2 logged in", level="info"),
        make_entry("user 99 logged in", level="info"),
    ]
    clusters = cluster_entries(entries)
    assert len(clusters) == 1
    assert clusters[0].count == 3


def test_different_messages_form_separate_clusters():
    entries = [
        make_entry("disk full on /dev/sda1"),
        make_entry("connection timeout after 30s"),
    ]
    clusters = cluster_entries(entries)
    assert len(clusters) == 2


def test_min_count_filters_small_clusters():
    entries = [
        make_entry("user 1 logged in"),
        make_entry("user 2 logged in"),
        make_entry("rare event occurred"),
    ]
    clusters = cluster_entries(entries, min_count=2)
    assert all(c.count >= 2 for c in clusters)


def test_sorted_by_count_descending():
    entries = [
        make_entry("rare event"),
        make_entry("common event 1"),
        make_entry("common event 2"),
        make_entry("common event 3"),
    ]
    clusters = cluster_entries(entries)
    counts = [c.count for c in clusters]
    assert counts == sorted(counts, reverse=True)


def test_level_included_in_key_by_default():
    entries = [
        make_entry("disk full", level="error"),
        make_entry("disk full", level="warn"),
    ]
    clusters = cluster_entries(entries, use_level=True)
    assert len(clusters) == 2


def test_level_ignored_when_disabled():
    entries = [
        make_entry("disk full", level="error"),
        make_entry("disk full", level="warn"),
    ]
    clusters = cluster_entries(entries, use_level=False)
    assert len(clusters) == 1
    assert clusters[0].count == 2


def test_as_dict_has_expected_keys():
    entries = [make_entry("server started")]
    c = cluster_entries(entries)[0]
    d = c.as_dict()
    assert "pattern" in d
    assert "count" in d
    assert "sample" in d
