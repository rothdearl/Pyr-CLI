"""Provides utilities for compiling, matching, and coloring regular expression patterns in text."""

import re
from collections.abc import Collection, Iterable

from .ansi import RESET
from .types import CompiledPatterns, ErrorReporter


def color_pattern_matches(text: str, patterns: Collection[re.Pattern[str]], *, color: str) -> str:
    """
    Color all regions of the text that match any of the given patterns.

    :param text: Text to color.
    :param patterns: Patterns to match.
    :param color: Color to use.
    :return: Text with all matched regions wrapped in color codes.
    """
    # Return early if no patterns are provided.
    if not patterns:
        return text

    # Get ranges for each match.
    ranges = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            ranges.append((match.start(), match.end()))

    # Merge overlapping ranges.
    merged_ranges = []

    for start, end in sorted(ranges):
        if merged_ranges and start <= merged_ranges[-1][1]:
            merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], end))
        else:
            merged_ranges.append((start, end))

    # Color ranges.
    colored_text = []
    prev_end = 0

    for start, end in merged_ranges:
        if prev_end < start:
            colored_text.append(text[prev_end:start])

        colored_text.extend([color, text[start:end], RESET])
        prev_end = end

    if prev_end < len(text):
        colored_text.append(text[prev_end:])

    return "".join(colored_text)


def compile_combined_patterns(patterns: Iterable[re.Pattern[str]], *, ignore_case: bool) -> re.Pattern[str]:
    """
    Combine patterns into a single compiled OR-pattern.

    :param patterns: Patterns to combine.
    :param ignore_case: Whether to ignore case.
    :return: Compiled regular expression matching any pattern.
    """
    flags = re.IGNORECASE if ignore_case else re.NOFLAG
    sources = [f"(?:{group.pattern})" for group in patterns]

    return re.compile("|".join(sources), flags=flags)


def compile_patterns(patterns: Iterable[str], *, ignore_case: bool, on_error: ErrorReporter) -> CompiledPatterns:
    """
    Compile patterns into OR groups implementing AND-of-OR matching.

    :param patterns: Patterns to compile.
    :param ignore_case: Whether to ignore case.
    :param on_error: Callback invoked with an error message for pattern-related errors.
    :return: List of compiled regular expression patterns implementing AND-of-OR matching.
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
    """
    Return whether the text matches all pattern groups.

    :param text: Text to search.
    :param patterns: Patterns to match.
    :return: ``True`` if the text matches all pattern groups.
    """
    return all(group.search(text) for group in patterns)


__all__ = [
    "color_pattern_matches",
    "compile_combined_patterns",
    "compile_patterns",
    "matches_all_patterns",
]
