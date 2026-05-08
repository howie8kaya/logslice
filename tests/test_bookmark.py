"""Tests for logslice.bookmark."""

import os
import pytest

from logslice.bookmark import (
    Bookmark,
    save_bookmark,
    load_bookmark,
    delete_bookmark,
    list_bookmarks,
)


@pytest.fixture
def bm_dir(tmp_path):
    return str(tmp_path / "bookmarks")


def make_bookmark(**kwargs):
    defaults = dict(filepath="/var/log/app.log", line_number=42, byte_offset=1024, label=None)
    defaults.update(kwargs)
    return Bookmark(**defaults)


def test_save_creates_file(bm_dir):
    bm = make_bookmark()
    path = save_bookmark(bm, "test", directory=bm_dir)
    assert os.path.exists(path)


def test_save_and_load_roundtrip(bm_dir):
    bm = make_bookmark(label="checkpoint")
    save_bookmark(bm, "mymark", directory=bm_dir)
    loaded = load_bookmark("mymark", directory=bm_dir)
    assert loaded is not None
    assert loaded.filepath == bm.filepath
    assert loaded.line_number == bm.line_number
    assert loaded.byte_offset == bm.byte_offset
    assert loaded.label == "checkpoint"


def test_load_missing_returns_none(bm_dir):
    result = load_bookmark("nonexistent", directory=bm_dir)
    assert result is None


def test_delete_existing_returns_true(bm_dir):
    bm = make_bookmark()
    save_bookmark(bm, "todelete", directory=bm_dir)
    result = delete_bookmark("todelete", directory=bm_dir)
    assert result is True


def test_delete_missing_returns_false(bm_dir):
    result = delete_bookmark("ghost", directory=bm_dir)
    assert result is False


def test_delete_removes_file(bm_dir):
    bm = make_bookmark()
    path = save_bookmark(bm, "gone", directory=bm_dir)
    delete_bookmark("gone", directory=bm_dir)
    assert not os.path.exists(path)


def test_list_bookmarks_empty(bm_dir):
    assert list_bookmarks(directory=bm_dir) == []


def test_list_bookmarks_returns_names(bm_dir):
    bm = make_bookmark()
    save_bookmark(bm, "alpha", directory=bm_dir)
    save_bookmark(bm, "beta", directory=bm_dir)
    names = list_bookmarks(directory=bm_dir)
    assert set(names) == {"alpha", "beta"}


def test_bookmark_as_dict(bm_dir):
    bm = make_bookmark(label="x")
    d = bm.as_dict()
    assert d["filepath"] == bm.filepath
    assert d["line_number"] == bm.line_number
    assert d["byte_offset"] == bm.byte_offset
    assert d["label"] == "x"
