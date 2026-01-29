"""
Functions for pattern-related operations.
"""

import re
from collections.abc import Iterable

from .ansi import RESET
from .types import CompiledPatterns, ErrorReporter, PatternGroups


def color_pattern_matches(text: str, patterns: Iterable[re.Pattern[str]], *, color: str) -> str:
    """
    Color all matches of the given patterns in the text.

    :param text: Text to color.
    :param patterns: Compiled regular expression patterns to match.
    :param color: Color to use.
    :return: Text with all matched regions wrapped in color codes.
    """
    slices = []

    # Get slices for each match.
    for pattern in patterns:
        for match in pattern.finditer(text):
            slices.append((match.start(), match.end()))

    # Merge overlapping slices.
    merged_slices = []

    for start, end in sorted(slices):
        if merged_slices and start <= merged_slices[-1][1]:
            merged_slices[-1] = (merged_slices[-1][0], max(merged_slices[-1][1], end))
        else:
            merged_slices.append((start, end))

    # Color slices.
    colored_text = []
    prev_end = 0

    for start, end in merged_slices:
        if prev_end < start:
            colored_text.append(text[prev_end:start])

        colored_text.extend([color, text[start:end], RESET])
        prev_end = end

    if prev_end < len(text):
        colored_text.append(text[prev_end:])

    return "".join(colored_text)


def compile_combined_patterns(patterns: PatternGroups, *, ignore_case: bool) -> re.Pattern[str]:
    """
    Combine patterns into a single compiled OR-pattern.

    :param patterns: Iterable of compiled patterns.
    :param ignore_case: Whether to ignore case.
    :return: Compiled regular expression matching any pattern.
    """
    flags = re.IGNORECASE if ignore_case else re.NOFLAG
    sources = [group.pattern for group in patterns]

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
            on_error(f"invalid pattern: {pattern}")

    return compiled


def matches_all_patterns(text: str, patterns: PatternGroups) -> bool:
    """
    Return whether the text matches every pattern group.

    :param text: Text to search.
    :param patterns: Patterns to match.
    :return: ``True`` if the text matches all pattern groups.
    """
    for group in patterns:
        if not group.search(text):
            return False

    return True


__all__ = [
    "color_pattern_matches",
    "compile_combined_patterns",
    "compile_patterns",
    "matches_all_patterns"
]
