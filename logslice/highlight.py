"""Terminal color highlighting for matched patterns in log output."""

import re
from typing import Optional

# ANSI color codes
RESET = "\033[0m"
COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
}

LEVEL_COLORS = {
    "ERROR": "red",
    "CRITICAL": "red",
    "WARNING": "yellow",
    "WARN": "yellow",
    "INFO": "green",
    "DEBUG": "blue",
}


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    code = COLORS.get(color, "")
    if not code:
        return text
    return f"{code}{text}{RESET}"


def highlight_pattern(text: str, pattern: str, color: str = "cyan") -> str:
    """Highlight all occurrences of pattern in text."""
    if not pattern:
        return text
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return text

    def replace_match(m: re.Match) -> str:
        return colorize(m.group(0), color)

    return compiled.sub(replace_match, text)


def highlight_level(text: str, level: Optional[str]) -> str:
    """Colorize the entire line based on log level."""
    if not level:
        return text
    color = LEVEL_COLORS.get(level.upper())
    if not color:
        return text
    return colorize(text, color)


def apply_highlight(raw: str, level: Optional[str], pattern: Optional[str]) -> str:
    """Apply level-based and pattern-based highlighting to a raw log line."""
    result = highlight_level(raw, level)
    if pattern:
        result = highlight_pattern(result, pattern, color="cyan")
    return result
