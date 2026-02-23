"""Provides utilities for parsing, splitting, and normalizing text."""

import csv
import re
import shlex
from collections.abc import Iterable, Iterator
from typing import Final

from .types import ErrorReporter


def decode_python_escape_sequences(line: str) -> str:
    """Decode Python-style backslash escape sequences in ``line`` (may raise ``UnicodeDecodeError``)."""
    return line.encode("utf-8").decode("unicode_escape")


def iter_nonempty_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield normalized, non-empty lines."""
    for file_name in iter_normalized_lines(lines):
        if file_name:
            yield file_name


def iter_normalized_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield lines with one trailing newline removed, if present."""
    for line in lines:
        yield strip_trailing_newline(line)


def split_csv(text: str, *, separator: str = " ", on_error: ErrorReporter) -> list[str]:
    """Split text into fields using CSV parsing when possible, falling back to ``str.split``."""
    try:
        decoded_separator = decode_python_escape_sequences(separator)

        if not decoded_separator:
            raise ValueError()

        # CSV requires a single non-quote, non-newline delimiter after escape decoding.
        if len(decoded_separator) == 1 and decoded_separator not in ('"', "\n", "\r"):
            return next(csv.reader([text], delimiter=decoded_separator))
    except (UnicodeDecodeError, ValueError, csv.Error):
        on_error(f"invalid separator: {separator!r}")
        return text.split()

    return text.split(separator)


def split_regex(text: str, *, pattern: str, ignore_case: bool = False, on_error: ErrorReporter) -> list[str]:
    """Split text into fields using a regular expression pattern, falling back to ``str.split`` on invalid patterns."""
    flags = re.IGNORECASE if ignore_case else re.NOFLAG

    try:
        return re.split(pattern=pattern, string=text, flags=flags)
    except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
        on_error(f"invalid pattern: {pattern!r}")

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


def strip_trailing_newline(line: str) -> str:
    """Remove one trailing newline, if present."""
    return line.removesuffix("\n")


__all__: Final[tuple[str, ...]] = (
    "decode_python_escape_sequences",
    "iter_nonempty_lines",
    "iter_normalized_lines",
    "split_csv",
    "split_regex",
    "split_shell_style",
    "strip_trailing_newline",
)
