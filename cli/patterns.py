"""
Module for pattern-related functions.
"""

import re
from collections.abc import Iterable

from .colors import RESET
from .types import CompiledPatterns, ErrorReporter, PatternIterable


def color_patterns_in_text(text: str, patterns: Iterable[re.Pattern[str]], *, color: str) -> str:
    """
    Colors all patterns in the text.

    :param text: Text to color.
    :param patterns: Patterns to find.
    :param color: Color to use.
    :return: The text with all patterns colored.
    """
    slices = []

    # Get the slices for each match.
    for group in patterns:
        for match in group.finditer(text):
            slices.append((match.start(), match.end()))

    # Merge the overlapping slices.
    merged_slices = []

    for start, end in sorted(slices):
        if merged_slices and start <= merged_slices[-1][1]:
            merged_slices[-1] = (merged_slices[-1][0], max(merged_slices[-1][1], end))
        else:
            merged_slices.append((start, end))

    # Color the slices.
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


def combine_patterns(patterns: PatternIterable, *, ignore_case: bool) -> re.Pattern[str]:
    """
    Combines all patterns into a single compiled OR-pattern.

    :param patterns: List of compiled pattern groups.
    :param ignore_case: Whether to ignore case.
    :return: A single compiled regular expression matching any pattern.
    """
    flags = re.IGNORECASE if ignore_case else re.NOFLAG
    sources = [group.pattern for group in patterns]

    return re.compile("|".join(sources), flags=flags)


def compile_patterns(patterns: Iterable[str], *, ignore_case: bool, on_error: ErrorReporter) -> CompiledPatterns:
    """
    Compiles patterns into OR-groups implementing AND-of-OR matching.

    :param patterns: Patterns to compile.
    :param ignore_case: Whether to ignore case.
    :param on_error: Callback invoked with an error message for pattern-related errors.
    :return: A list of compiled regular expression patterns implementing AND-of-OR matching.
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


def text_has_patterns(text: str, patterns: PatternIterable) -> bool:
    """
    Returns whether the text matches all patterns.

    :param text: Text to search.
    :param patterns: Patterns to match.
    :return: True or False.
    """
    for group in patterns:
        if not group.search(text):
            return False

    return True
