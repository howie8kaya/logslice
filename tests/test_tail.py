"""Tests for logslice.tail — file-follow functionality."""

import os
import tempfile
import time
import threading
import pytest

from logslice.parser import LogParser
from logslice.tail import tail_file, _count_lines


LOG_LINE = "2024-01-15 10:00:00 INFO hello world\n"
LOG_LINE2 = "2024-01-15 10:00:01 ERROR something broke\n"


@pytest.fixture()
def tmp_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("")  # start empty
    return str(p)


def _append_after(path: str, text: str, delay: float = 0.1) -> None:
    """Append *text* to *path* after *delay* seconds (runs in a thread)."""
    def _write():
        time.sleep(delay)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    t = threading.Thread(target=_write, daemon=True)
    t.start()


def test_count_lines_empty(tmp_log):
    assert _count_lines(tmp_log) == 0


def test_count_lines_non_empty(tmp_log):
    with open(tmp_log, "w") as fh:
        fh.write(LOG_LINE * 3)
    assert _count_lines(tmp_log) == 3


def test_tail_yields_new_entry(tmp_log):
    parser = LogParser()
    _append_after(tmp_log, LOG_LINE, delay=0.1)
    entries = list(tail_file(tmp_log, parser=parser, poll_interval=0.05, max_lines=1))
    assert len(entries) == 1
    assert entries[0].raw == LOG_LINE.rstrip("\n")


def test_tail_yields_multiple_entries(tmp_log):
    parser = LogParser()
    def _write_two():
        time.sleep(0.1)
        with open(tmp_log, "a") as fh:
            fh.write(LOG_LINE)
            fh.write(LOG_LINE2)
    t = threading.Thread(target=_write_two, daemon=True)
    t.start()
    entries = list(tail_file(tmp_log, parser=parser, poll_interval=0.05, max_lines=2))
    assert len(entries) == 2


def test_tail_with_pattern_filter(tmp_log):
    parser = LogParser(pattern=r"ERROR")
    def _write():
        time.sleep(0.1)
        with open(tmp_log, "a") as fh:
            fh.write(LOG_LINE)   # INFO — filtered out
            fh.write(LOG_LINE2)  # ERROR — kept
    t = threading.Thread(target=_write, daemon=True)
    t.start()
    entries = list(tail_file(tmp_log, parser=parser, poll_interval=0.05, max_lines=1))
    assert len(entries) == 1
    assert "ERROR" in entries[0].raw


def test_tail_line_numbers_increment(tmp_log):
    # pre-populate two lines so line numbering starts at 3
    with open(tmp_log, "w") as fh:
        fh.write(LOG_LINE * 2)
    parser = LogParser()
    _append_after(tmp_log, LOG_LINE, delay=0.1)
    entries = list(tail_file(tmp_log, parser=parser, poll_interval=0.05, max_lines=1))
    assert entries[0].line_number == 3
