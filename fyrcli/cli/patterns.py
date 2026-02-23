"""Provides utilities for compiling and matching regular expression patterns in text."""

import re
from collections.abc import Iterable
from typing import Final

from .types import CompiledPatterns, ErrorReporter


def compile_combined_patterns(compiled_patterns: Iterable[re.Pattern[str]], *, ignore_case: bool) -> re.Pattern[str]:
    """
    Combine patterns into a single compiled OR-pattern.

    :param compiled_patterns: Patterns to combine.
    :param ignore_case: Whether to ignore case.
    :return: Compiled regular expression matching any pattern.
    """
    flags = re.IGNORECASE if ignore_case else re.NOFLAG
    sources = [f"(?:{pattern.pattern})" for pattern in compiled_patterns]

    return re.compile("|".join(sources), flags=flags)


def compile_patterns(patterns: Iterable[str], *, ignore_case: bool, on_error: ErrorReporter) -> CompiledPatterns:
    """
    Compile a sequence of regular expression patterns suitable for AND-style matching (e.g., ``matches_all_patterns``).

    :param patterns: Patterns to compile.
    :param ignore_case: Whether to ignore case.
    :param on_error: Callback invoked with an error message for pattern-related errors.
    :return: List of compiled regular expression patterns.
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


def matches_all_patterns(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    """Return whether the text matches every pattern."""
    return all(group.search(text) for group in patterns)


__all__: Final[tuple[str, ...]] = (
    "compile_combined_patterns",
    "compile_patterns",
    "matches_all_patterns",
)
