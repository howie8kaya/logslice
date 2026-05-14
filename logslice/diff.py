"""Log diff: compare two sets of log entries and report additions/removals."""

from dataclasses import dataclass, field
from typing import List, Tuple
from logslice.parser import LogEntry


@dataclass
class DiffResult:
    added: List[LogEntry] = field(default_factory=list)
    removed: List[LogEntry] = field(default_factory=list)
    common: List[LogEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "added": [e.to_dict() for e in self.added],
            "removed": [e.to_dict() for e in self.removed],
            "common_count": len(self.common),
            "added_count": len(self.added),
            "removed_count": len(self.removed),
        }


def _entry_key(entry: LogEntry) -> str:
    """Produce a normalised key for comparison (raw text, stripped)."""
    return entry.raw.strip()


def diff_entries(
    baseline: List[LogEntry],
    current: List[LogEntry],
    ignore_case: bool = False,
) -> DiffResult:
    """Compare two lists of LogEntry objects.

    Returns a DiffResult describing lines only in *baseline* (removed),
    only in *current* (added), and lines present in both (common).
    Order-independent: comparison is based on unique raw-text keys.
    """

    def key(e: LogEntry) -> str:
        k = _entry_key(e)
        return k.lower() if ignore_case else k

    baseline_keys = {key(e): e for e in baseline}
    current_keys = {key(e): e for e in current}

    common_keys = baseline_keys.keys() & current_keys.keys()
    removed_keys = baseline_keys.keys() - current_keys.keys()
    added_keys = current_keys.keys() - baseline_keys.keys()

    return DiffResult(
        added=[current_keys[k] for k in sorted(added_keys)],
        removed=[baseline_keys[k] for k in sorted(removed_keys)],
        common=[baseline_keys[k] for k in sorted(common_keys)],
    )


def format_diff(result: DiffResult, color: bool = False) -> List[str]:
    """Return a human-readable list of diff lines (unified-style prefixes)."""
    lines: List[str] = []

    for entry in result.removed:
        prefix = "\033[31m- \033[0m" if color else "- "
        lines.append(f"{prefix}{entry.raw.rstrip()}")

    for entry in result.added:
        prefix = "\033[32m+ \033[0m" if color else "+ "
        lines.append(f"{prefix}{entry.raw.rstrip()}")

    return lines
