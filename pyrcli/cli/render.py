"""Rendering utilities for presentation-formatted text."""

import re
from collections.abc import Iterable
from typing import Final

from .ansi import RESET, TextAttributes


def bold(text: str) -> str:
    """Return the text wrapped in bold ANSI SGR escape codes."""
    return style(text, ansi_style=TextAttributes.BOLD)


def dim(text: str) -> str:
    """Return the text wrapped in dim ANSI SGR escape codes."""
    return style(text, ansi_style=TextAttributes.DIM)


def reverse_video(text: str) -> str:
    """Return the text wrapped in reverse-video ANSI SGR escape codes."""
    return style(text, ansi_style=TextAttributes.REVERSE)


def style(text: str, *, ansi_style: str) -> str:
    """Return the text wrapped in ANSI SGR escape codes."""
    return f"{ansi_style}{text}{RESET}"


def style_pattern_matches(text: str, *, patterns: Iterable[re.Pattern[str]], ansi_style: str) -> str:
    """Return the text with all pattern matches wrapped in ANSI SGR escape codes."""
    if not patterns:  # Return early if no patterns are provided.
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

    # Style ranges.
    styled_text = []
    prev_end = 0

    for start, end in merged_ranges:
        if prev_end < start:
            styled_text.append(text[prev_end:start])

        styled_text.extend([ansi_style, text[start:end], RESET])
        prev_end = end

    if prev_end < len(text):
        styled_text.append(text[prev_end:])

    return "".join(styled_text)


__all__: Final[tuple[str, ...]] = (
    "bold",
    "dim",
    "reverse_video",
    "style",
    "style_pattern_matches",
)
