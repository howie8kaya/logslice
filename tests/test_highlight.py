"""Tests for the highlight module."""

import pytest

from logslice.highlight import (
    apply_highlight,
    colorize,
    highlight_level,
    highlight_pattern,
)


def test_colorize_known_color():
    result = colorize("hello", "red")
    assert "hello" in result
    assert "\033[" in result


def test_colorize_unknown_color_returns_plain():
    result = colorize("hello", "ultraviolet")
    assert result == "hello"


def test_highlight_pattern_wraps_match():
    result = highlight_pattern("foo bar foo", "foo")
    # both occurrences should be wrapped
    assert result.count("foo") == 2
    assert "\033[" in result


def test_highlight_pattern_case_insensitive():
    result = highlight_pattern("ERROR error Error", "error")
    assert "\033[" in result


def test_highlight_pattern_invalid_regex_returns_original():
    text = "some log line"
    result = highlight_pattern(text, "[invalid")
    assert result == text


def test_highlight_pattern_empty_pattern_returns_original():
    text = "some log line"
    result = highlight_pattern(text, "")
    assert result == text


def test_highlight_level_error():
    result = highlight_level("some error line", "ERROR")
    assert "\033[31m" in result  # red


def test_highlight_level_warning():
    result = highlight_level("a warning", "WARNING")
    assert "\033[33m" in result  # yellow


def test_highlight_level_info():
    result = highlight_level("info msg", "INFO")
    assert "\033[32m" in result  # green


def test_highlight_level_unknown_returns_plain():
    text = "trace level msg"
    result = highlight_level(text, "TRACE")
    assert result == text


def test_highlight_level_none_returns_plain():
    text = "no level"
    result = highlight_level(text, None)
    assert result == text


def test_apply_highlight_combines_both():
    text = "2024-01-01 ERROR something failed"
    result = apply_highlight(text, "ERROR", "failed")
    assert "\033[" in result
    assert "failed" in result


def test_apply_highlight_no_pattern():
    text = "2024-01-01 INFO startup"
    result = apply_highlight(text, "INFO", None)
    assert "\033[" in result
    assert "startup" in result
