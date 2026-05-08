"""Tests for logslice.cli_bookmark."""

import argparse
import pytest

from logslice.cli_bookmark import add_bookmark_args, handle_bookmark
from logslice.bookmark import save_bookmark, Bookmark


@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    add_bookmark_args(p)
    return p


@pytest.fixture
def bm_dir(tmp_path, monkeypatch):
    d = str(tmp_path / "bmarks")
    monkeypatch.setattr("logslice.bookmark.DEFAULT_BOOKMARK_DIR", d)
    monkeypatch.setattr("logslice.cli_bookmark.save_bookmark",
                        lambda bm, name: save_bookmark(bm, name, directory=d))
    monkeypatch.setattr("logslice.cli_bookmark.load_bookmark",
                        lambda name: __import__("logslice.bookmark", fromlist=["load_bookmark"]).load_bookmark(name, directory=d))
    monkeypatch.setattr("logslice.cli_bookmark.delete_bookmark",
                        lambda name: __import__("logslice.bookmark", fromlist=["delete_bookmark"]).delete_bookmark(name, directory=d))
    monkeypatch.setattr("logslice.cli_bookmark.list_bookmarks",
                        lambda: __import__("logslice.bookmark", fromlist=["list_bookmarks"]).list_bookmarks(directory=d))
    return d


def test_add_bookmark_args_registers_subcommands(parser):
    # just check parsing doesn't explode
    args = parser.parse_args(["list"])
    assert args.bookmark_cmd == "list"


def test_handle_no_cmd_returns_1(capsys):
    args = argparse.Namespace(bookmark_cmd=None)
    rc = handle_bookmark(args)
    assert rc == 1


def test_handle_list_empty(bm_dir, capsys):
    args = argparse.Namespace(bookmark_cmd="list")
    rc = handle_bookmark(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No bookmarks" in out


def test_handle_load_missing(bm_dir, capsys):
    args = argparse.Namespace(bookmark_cmd="load", name="nope")
    rc = handle_bookmark(args)
    assert rc == 1


def test_handle_delete_missing(bm_dir, capsys):
    args = argparse.Namespace(bookmark_cmd="delete", name="ghost")
    rc = handle_bookmark(args)
    assert rc == 1


def test_handle_save_prints_path(bm_dir, capsys):
    args = argparse.Namespace(
        bookmark_cmd="save",
        name="mymark",
        filepath="/tmp/app.log",
        line=10,
        offset=512,
        label="start",
    )
    rc = handle_bookmark(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "mymark" in out
