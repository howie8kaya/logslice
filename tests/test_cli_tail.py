"""Tests for logslice.cli_tail — argument registration and handle_tail."""

import argparse
import threading
import time
import sys
from io import StringIO

import pytest

from logslice.cli_tail import add_tail_args, handle_tail


LOG_LINE = "2024-01-15 10:00:00 INFO hello world\n"


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--pattern", default=None)
    p.add_argument("--ignore-case", action="store_true", default=False)
    p.add_argument("--highlight", action="store_true", default=False)
    p.add_argument("--format", default="plain")
    add_tail_args(p)
    return p


def test_add_tail_args_registers_follow(parser):
    args = parser.parse_args(["app.log"])
    assert hasattr(args, "follow")
    assert args.follow is False


def test_add_tail_args_follow_flag(parser):
    args = parser.parse_args(["app.log", "-f"])
    assert args.follow is True


def test_add_tail_args_poll_interval_default(parser):
    args = parser.parse_args(["app.log"])
    assert args.poll_interval == pytest.approx(0.25)


def test_add_tail_args_poll_interval_custom(parser):
    args = parser.parse_args(["app.log", "--poll-interval", "0.5"])
    assert args.poll_interval == pytest.approx(0.5)


def test_handle_tail_outputs_entry(tmp_path, parser, capsys):
    log = tmp_path / "app.log"
    log.write_text("")

    def _write():
        time.sleep(0.1)
        with open(str(log), "a") as fh:
            fh.write(LOG_LINE)

    t = threading.Thread(target=_write, daemon=True)
    t.start()

    # patch tail_file to stop after 1 entry
    import logslice.cli_tail as ct
    original = ct.tail_file

    def _limited(path, parser, poll_interval):
        from logslice.tail import tail_file as _tf
        yield from _tf(path, parser=parser, poll_interval=poll_interval, max_lines=1)

    ct.tail_file = _limited
    try:
        args = parser.parse_args([str(log), "--poll-interval", "0.05"])
        handle_tail(args)
    finally:
        ct.tail_file = original

    captured = capsys.readouterr()
    assert "hello world" in captured.out
