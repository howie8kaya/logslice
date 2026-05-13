"""Tests for logslice.redact and logslice.cli_redact."""

import argparse
import pytest

from logslice.parser import LogEntry
from logslice.redact import redact_text, redact_entries, _compile_rules
from logslice.cli_redact import add_redact_args, handle_redact


def make_entry(raw: str, message: str = '', line: int = 1) -> LogEntry:
    return LogEntry(line_number=line, raw=raw, timestamp=None, level=None, message=message, extra={})


# --- redact_text ---

def test_redact_text_password():
    rules = _compile_rules()
    result = redact_text('login password=supersecret here', rules)
    assert 'supersecret' not in result
    assert 'REDACTED' in result


def test_redact_text_email():
    rules = _compile_rules()
    result = redact_text('contact user@example.com for help', rules)
    assert 'user@example.com' not in result


def test_redact_text_card_number():
    rules = _compile_rules()
    result = redact_text('card: 4111 1111 1111 1111 charged', rules)
    assert '4111' not in result


def test_redact_text_token():
    rules = _compile_rules()
    result = redact_text('api_key=abc123xyz', rules)
    assert 'abc123xyz' not in result


def test_redact_text_no_match_unchanged():
    rules = _compile_rules()
    original = 'everything is fine here'
    assert redact_text(original, rules) == original


def test_redact_text_custom_pattern():
    rules = _compile_rules(extra_patterns=[r'INTERNAL-\d+'], use_builtins=False)
    result = redact_text('ticket INTERNAL-9981 created', rules)
    assert 'INTERNAL-9981' not in result
    assert 'REDACTED' in result


def test_compile_rules_invalid_pattern_skipped():
    rules = _compile_rules(extra_patterns=['[invalid('], use_builtins=False)
    assert rules == []


# --- redact_entries ---

def test_redact_entries_modifies_raw_and_message():
    e = make_entry(raw='password=hunter2', message='password=hunter2')
    result = redact_entries([e])
    assert 'hunter2' not in result[0].raw
    assert 'hunter2' not in result[0].message


def test_redact_entries_preserves_metadata():
    e = make_entry(raw='hello world', line=42)
    result = redact_entries([e])
    assert result[0].line_number == 42
    assert result[0].timestamp is None


def test_redact_entries_no_builtins_only_custom():
    e = make_entry(raw='password=secret CUSTOM-001')
    result = redact_entries([e], extra_patterns=[r'CUSTOM-\d+'], use_builtins=False)
    assert 'CUSTOM-001' not in result[0].raw
    assert 'secret' in result[0].raw  # builtin not applied


def test_redact_entries_empty_list():
    assert redact_entries([]) == []


# --- CLI integration ---

@pytest.fixture
def parser():
    p = argparse.ArgumentParser()
    add_redact_args(p)
    return p


def test_add_redact_args_registers_redact(parser):
    args = parser.parse_args([])
    assert hasattr(args, 'redact')
    assert args.redact is False


def test_add_redact_args_pattern_list(parser):
    args = parser.parse_args(['--redact-pattern', 'FOO-\\d+'])
    assert 'FOO-\\d+' in args.redact_patterns


def test_handle_redact_no_flag_returns_same(parser):
    entries = [make_entry('password=secret')]
    args = parser.parse_args([])
    result = handle_redact(args, entries)
    assert result is entries


def test_handle_redact_flag_applies_redaction(parser):
    entries = [make_entry('password=secret')]
    args = parser.parse_args(['--redact'])
    result = handle_redact(args, entries)
    assert 'secret' not in result[0].raw


def test_handle_redact_custom_pattern_triggers(parser):
    entries = [make_entry('ref=MYTOKEN-777')]
    args = parser.parse_args(['--redact-pattern', r'MYTOKEN-\d+'])
    result = handle_redact(args, entries)
    assert 'MYTOKEN-777' not in result[0].raw
