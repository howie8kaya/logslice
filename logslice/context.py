"""Context lines support: capture N lines before/after each matching entry."""

from typing import List, Tuple
from logslice.parser import LogEntry


def extract_with_context(
    entries: List[LogEntry],
    matched_indices: List[int],
    before: int = 0,
    after: int = 0,
) -> List[Tuple[LogEntry, bool]]:
    """Return entries with context lines around matched indices.

    Returns a list of (entry, is_match) tuples. Duplicate entries are
    deduplicated while preserving order.

    Args:
        entries: The full list of parsed log entries.
        matched_indices: Indices (into ``entries``) that satisfied the filter.
        before: Number of lines to include before each match.
        after: Number of lines to include after each match.

    Returns:
        Ordered list of ``(entry, is_match)`` tuples with no duplicates.
    """
    if not matched_indices:
        return []

    seen: set = set()
    result: List[Tuple[LogEntry, bool]] = []
    matched_set = set(matched_indices)
    n = len(entries)

    for idx in matched_indices:
        start = max(0, idx - before)
        end = min(n - 1, idx + after)
        for i in range(start, end + 1):
            if i not in seen:
                seen.add(i)
                result.append((entries[i], i in matched_set))

    return result


def find_matched_indices(
    entries: List[LogEntry], filtered: List[LogEntry]
) -> List[int]:
    """Map filtered entries back to their indices in the original list.

    Uses object identity (``id()``) for O(1) lookup, so ``filtered`` must
    contain the exact same objects as the corresponding elements in ``entries``.

    Args:
        entries: The full list of parsed log entries.
        filtered: A subset of ``entries`` that passed a filter.

    Returns:
        List of indices in ``entries`` corresponding to each item in
        ``filtered``, in the same order.
    """
    # Build index by id for O(1) lookup
    id_to_index = {id(e): i for i, e in enumerate(entries)}
    indices = []
    for entry in filtered:
        idx = id_to_index.get(id(entry))
        if idx is not None:
            indices.append(idx)
    return indices
