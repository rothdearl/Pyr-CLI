"""Provides utilities for compiling and matching regular expression patterns in text."""

import re
from collections.abc import Iterable
from typing import Final

from .types import CompiledPatterns, ErrorReporter


def compile_combined_patterns(compiled_patterns: Iterable[re.Pattern[str]], *, ignore_case: bool) -> re.Pattern[str]:
    """
    Return a compiled pattern that matches any of the provided patterns.

    - Wraps each pattern as a non-capturing group before combining.
    - Case-insensitive when ``ignore_case`` is ``True``.
    """
    flags = re.IGNORECASE if ignore_case else re.NOFLAG
    sources = [f"(?:{pattern.pattern})" for pattern in compiled_patterns]

    return re.compile("|".join(sources), flags=flags)


def compile_patterns(patterns: Iterable[str], *, ignore_case: bool, on_error: ErrorReporter) -> CompiledPatterns:
    """
    Return compiled regular expression patterns suitable for AND-style matching.

    - Skips empty patterns.
    - Case-insensitive when ``ignore_case`` is ``True``.
    - Invokes ``on_error(message)`` for invalid patterns and continues.
    - Returns only successfully compiled patterns.
    """
    compiled = []
    flags = re.IGNORECASE if ignore_case else re.NOFLAG

    for pattern in patterns:
        if not pattern:  # Skip empty patterns.
            continue

        try:
            compiled.append(re.compile(pattern, flags=flags))
        except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
            on_error(f"invalid pattern: {pattern!r}")

    return compiled


def matches_all_patterns(text: str, *, compiled_patterns: Iterable[re.Pattern[str]]) -> bool:
    """Return ``True`` if the text matches every pattern."""
    return all(group.search(text) for group in compiled_patterns)


__all__: Final[tuple[str, ...]] = (
    "compile_combined_patterns",
    "compile_patterns",
    "matches_all_patterns",
)
