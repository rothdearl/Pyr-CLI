"""Provides utilities for parsing, splitting, and normalizing text."""

import csv
import re
import shlex

from .types import ErrorReporter


def split_csv(text: str, *, separator: str = " ", on_error: ErrorReporter) -> list[str]:
    """Split text into fields using CSV parsing when possible, falling back to ``str.split``."""
    # Decode escape sequences in the field separator.
    try:
        separator = separator.encode().decode("unicode_escape")

        if not separator:
            raise ValueError()

        if len(separator) == 1 and separator not in ('"', "\n", "\r"):
            return next(csv.reader([text], delimiter=separator))
    except (UnicodeDecodeError, ValueError, csv.Error):
        visible_name = repr(separator) if separator else "(empty)"
        on_error(f"invalid separator: {visible_name}")
        return text.split()

    return text.split(separator)


def split_regex(text: str, *, pattern: str, ignore_case: bool = False, on_error: ErrorReporter) -> list[str]:
    """Split text into fields using a regular expression pattern, falling back to ``str.split`` on invalid patterns."""
    flags = re.IGNORECASE if ignore_case else re.NOFLAG

    try:
        return re.split(pattern=pattern, string=text, flags=flags)
    except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
        on_error(f"invalid pattern: {pattern}")

    return text.split()


def split_shell_style(text: str, *, literal_quotes: bool = False) -> list[str]:
    """Split text into fields using shell-style parsing."""
    lexer = shlex.shlex(text, posix=True, punctuation_chars=False)

    # Configure the lexer.
    lexer.whitespace_split = True  # Treat whitespace as the token separator.

    if literal_quotes:
        lexer.quotes = ""  # Treat quotes as ordinary characters.

    # Parse the fields.
    try:
        return list(lexer)
    except ValueError:
        # e.g., unmatched quotes: fall back to a single field.
        return [text]


__all__ = [
    "split_csv",
    "split_regex",
    "split_shell_style",
]
