"""Integration tests for CLI --start / --end / --level flags."""

import json
import textwrap
import tempfile
import os
import pytest

from logslice.cli import run


LOG_CONTENT = textwrap.dedent("""\
    DEBUG 2024-06-01T08:00:00 boot
    INFO 2024-06-01T09:00:00 ready
    WARNING 2024-06-01T10:00:00 slow response
    ERROR 2024-06-01T11:00:00 connection failed
    CRITICAL 2024-06-01T12:00:00 system crash
""")

PATTERN = r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL) (?P<timestamp>\S+) (?P<message>.+)"


@pytest.fixture()
def log_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write(LOG_CONTENT)
        name = f.name
    yield name
    os.unlink(name)


def test_cli_level_filter(log_file, capsys):
    run([log_file, "-p", PATTERN, "--level", "ERROR", "-f", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    levels = [d["groups"]["level"] for d in data]
    assert set(levels) == {"ERROR", "CRITICAL"}


def test_cli_start_filter(log_file, capsys):
    run([log_file, "-p", PATTERN, "--start", "2024-06-01T10:00:00", "-f", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 3
    assert data[0]["groups"]["level"] == "WARNING"


def test_cli_end_filter(log_file, capsys):
    run([log_file, "-p", PATTERN, "--end", "2024-06-01T09:00:00", "-f", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2


def test_cli_combined_filters(log_file, capsys):
    run([
        log_file, "-p", PATTERN,
        "--start", "2024-06-01T09:00:00",
        "--end",   "2024-06-01T11:00:00",
        "--level", "WARNING",
        "-f", "json",
    ])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    levels = [d["groups"]["level"] for d in data]
    assert "WARNING" in levels
    assert "ERROR" in levels


def test_cli_invalid_datetime_exits(log_file):
    with pytest.raises(SystemExit) as exc_info:
        run([log_file, "--start", "not-a-date"])
    assert exc_info.value.code == 1


def test_cli_invalid_level_exits(log_file):
    with pytest.raises((SystemExit, ValueError)):
        run([log_file, "-p", PATTERN, "--level", "TRACE"])
