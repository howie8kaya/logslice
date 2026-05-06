"""Core log file parser with regex support."""

import re
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class LogEntry:
    line_number: int
    raw: str
    matched_groups: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "raw": self.raw.strip(),
            "matched_groups": self.matched_groups,
        }


class LogParser:
    def __init__(self, pattern: Optional[str] = None, ignore_case: bool = False):
        self.pattern = pattern
        self.ignore_case = ignore_case
        self._regex: Optional[re.Pattern] = None

        if pattern:
            flags = re.IGNORECASE if ignore_case else 0
            try:
                self._regex = re.compile(pattern, flags)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}")

    def parse_file(self, filepath: str) -> Iterator[LogEntry]:
        """Parse a log file and yield matching LogEntry objects."""
        with open(filepath, "r", errors="replace") as f:
            for line_number, line in enumerate(f, start=1):
                entry = self._process_line(line_number, line)
                if entry is not None:
                    yield entry

    def parse_lines(self, lines: list[str]) -> Iterator[LogEntry]:
        """Parse an iterable of lines and yield matching LogEntry objects."""
        for line_number, line in enumerate(lines, start=1):
            entry = self._process_line(line_number, line)
            if entry is not None:
                yield entry

    def _process_line(self, line_number: int, line: str) -> Optional[LogEntry]:
        if self._regex is None:
            return LogEntry(line_number=line_number, raw=line)

        match = self._regex.search(line)
        if match:
            groups = match.groupdict() if match.groupdict() else {str(i): v for i, v in enumerate(match.groups(), 1)}
            return LogEntry(line_number=line_number, raw=line, matched_groups=groups)
        return None
