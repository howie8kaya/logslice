"""Redaction module for masking sensitive patterns in log entries."""

import re
from typing import List, Optional, Tuple
from logslice.parser import LogEntry

# Built-in common sensitive patterns
BUILTIN_PATTERNS: List[Tuple[str, str]] = [
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+', r'\1=***REDACTED***'),
    (r'(?i)(token|api[_-]?key|secret)\s*[=:]\s*\S+', r'\1=***REDACTED***'),
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '***@***.***'),
]


def _compile_rules(
    extra_patterns: Optional[List[str]] = None,
    use_builtins: bool = True,
) -> List[Tuple[re.Pattern, str]]:
    """Compile redaction rules into (pattern, replacement) pairs."""
    rules: List[Tuple[re.Pattern, str]] = []

    if use_builtins:
        for pat, repl in BUILTIN_PATTERNS:
            rules.append((re.compile(pat), repl))

    if extra_patterns:
        for pat in extra_patterns:
            try:
                rules.append((re.compile(pat), '***REDACTED***'))
            except re.error:
                pass  # skip invalid patterns

    return rules


def redact_text(
    text: str,
    rules: List[Tuple[re.Pattern, str]],
) -> str:
    """Apply all redaction rules to a single text string."""
    for pattern, replacement in rules:
        text = pattern.sub(replacement, text)
    return text


def redact_entries(
    entries: List[LogEntry],
    extra_patterns: Optional[List[str]] = None,
    use_builtins: bool = True,
) -> List[LogEntry]:
    """Return new LogEntry list with sensitive data redacted from raw text."""
    rules = _compile_rules(extra_patterns, use_builtins)
    redacted: List[LogEntry] = []

    for entry in entries:
        new_raw = redact_text(entry.raw, rules)
        new_message = redact_text(entry.message, rules) if entry.message else entry.message
        redacted.append(LogEntry(
            line_number=entry.line_number,
            raw=new_raw,
            timestamp=entry.timestamp,
            level=entry.level,
            message=new_message,
            extra=entry.extra,
        ))

    return redacted
