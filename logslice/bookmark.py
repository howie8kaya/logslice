"""Bookmark support: save and restore parse positions in log files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


DEFAULT_BOOKMARK_DIR = os.path.expanduser("~/.logslice/bookmarks")


@dataclass
class Bookmark:
    filepath: str
    line_number: int
    byte_offset: int
    label: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


def _bookmark_path(name: str, directory: str = DEFAULT_BOOKMARK_DIR) -> str:
    os.makedirs(directory, exist_ok=True)
    safe_name = name.replace(os.sep, "_").replace(" ", "_")
    return os.path.join(directory, f"{safe_name}.json")


def save_bookmark(bookmark: Bookmark, name: str, directory: str = DEFAULT_BOOKMARK_DIR) -> str:
    """Persist a bookmark to disk. Returns the path written."""
    path = _bookmark_path(name, directory)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(bookmark.as_dict(), fh, indent=2)
    return path


def load_bookmark(name: str, directory: str = DEFAULT_BOOKMARK_DIR) -> Optional[Bookmark]:
    """Load a bookmark by name. Returns None if not found."""
    path = _bookmark_path(name, directory)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Bookmark(**data)


def delete_bookmark(name: str, directory: str = DEFAULT_BOOKMARK_DIR) -> bool:
    """Remove a bookmark. Returns True if deleted, False if not found."""
    path = _bookmark_path(name, directory)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def list_bookmarks(directory: str = DEFAULT_BOOKMARK_DIR) -> list[str]:
    """Return all bookmark names stored in the directory."""
    if not os.path.isdir(directory):
        return []
    return [
        fname[:-5]
        for fname in os.listdir(directory)
        if fname.endswith(".json")
    ]
