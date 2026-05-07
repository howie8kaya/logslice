"""Tail support: follow a log file and yield new entries as they appear."""

import time
import os
from typing import Iterator, Optional
from logslice.parser import LogParser, LogEntry


def tail_file(
    path: str,
    parser: LogParser,
    poll_interval: float = 0.25,
    max_lines: Optional[int] = None,
) -> Iterator[LogEntry]:
    """Follow *path* and yield parsed LogEntry objects as new lines arrive.

    Reads the file from the current end, then polls for new content.
    Stops after *max_lines* entries if given (useful for tests).
    """
    count = 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        # seek to end so we only see new lines
        fh.seek(0, os.SEEK_END)
        line_no = _count_lines(path)

        while True:
            line = fh.readline()
            if not line:
                time.sleep(poll_interval)
                continue

            line_no += 1
            stripped = line.rstrip("\n")
            entry = parser._parse_line(stripped, line_no)  # noqa: SLF001
            if entry is not None:
                yield entry
                count += 1
                if max_lines is not None and count >= max_lines:
                    return


def _count_lines(path: str) -> int:
    """Return the number of lines currently in *path*."""
    count = 0
    with open(path, "rb") as fh:
        for _ in fh:
            count += 1
    return count
