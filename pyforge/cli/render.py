"""Rendering utilities for presentation-formatted text."""

import re
from collections.abc import Collection

from .ansi import RESET, TextAttributes


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


def reverse_video(text: str) -> str:
    """Return the text wrapped in reverse-video ANSI escape codes."""
    return f"{TextAttributes.REVERSE}{text}{RESET}"


__all__: list[str] = [
    "color_pattern_matches",
    "reverse_video",
]
