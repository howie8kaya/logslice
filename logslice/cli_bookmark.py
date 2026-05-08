"""CLI integration for bookmark commands."""

from __future__ import annotations

import argparse
from typing import Any

from logslice.bookmark import (
    Bookmark,
    save_bookmark,
    load_bookmark,
    delete_bookmark,
    list_bookmarks,
)


def add_bookmark_args(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="bookmark_cmd", help="bookmark sub-commands")

    save_p = sub.add_parser("save", help="save a bookmark")
    save_p.add_argument("name", help="bookmark name")
    save_p.add_argument("filepath", help="log file path")
    save_p.add_argument("--line", type=int, default=0, help="line number")
    save_p.add_argument("--offset", type=int, default=0, help="byte offset")
    save_p.add_argument("--label", default=None, help="optional label")

    load_p = sub.add_parser("load", help="show a bookmark")
    load_p.add_argument("name", help="bookmark name")

    del_p = sub.add_parser("delete", help="delete a bookmark")
    del_p.add_argument("name", help="bookmark name")

    sub.add_parser("list", help="list all bookmarks")


def handle_bookmark(args: Any) -> int:
    cmd = getattr(args, "bookmark_cmd", None)

    if cmd == "save":
        bm = Bookmark(
            filepath=args.filepath,
            line_number=args.line,
            byte_offset=args.offset,
            label=args.label,
        )
        path = save_bookmark(bm, args.name)
        print(f"Bookmark '{args.name}' saved to {path}")
        return 0

    if cmd == "load":
        bm = load_bookmark(args.name)
        if bm is None:
            print(f"No bookmark named '{args.name}'")
            return 1
        print(f"file:   {bm.filepath}")
        print(f"line:   {bm.line_number}")
        print(f"offset: {bm.byte_offset}")
        if bm.label:
            print(f"label:  {bm.label}")
        return 0

    if cmd == "delete":
        removed = delete_bookmark(args.name)
        if removed:
            print(f"Bookmark '{args.name}' deleted.")
            return 0
        print(f"Bookmark '{args.name}' not found.")
        return 1

    if cmd == "list":
        names = list_bookmarks()
        if not names:
            print("No bookmarks saved.")
        else:
            for name in sorted(names):
                print(name)
        return 0

    print("No bookmark sub-command given. Use save/load/delete/list.")
    return 1
