"""Utilities for styling text with ANSI escape sequences."""

import re
from collections.abc import Collection
from typing import Final

from .ansi import RESET, TextAttributes


def bold(text: str) -> str:
    """Return ``text`` rendered in bold."""
    return style(text, ansi_style=TextAttributes.BOLD)


def dim(text: str) -> str:
    """Return ``text`` rendered in dim."""
    return style(text, ansi_style=TextAttributes.DIM)


def reverse_video(text: str) -> str:
    """Return ``text`` rendered with reversed foreground and background colors."""
    return style(text, ansi_style=TextAttributes.REVERSE)


def style(text: str, *, ansi_style: str) -> str:
    """Return ``text`` rendered with the given ANSI style, reset afterward."""
    return f"{ansi_style}{text}{RESET}"


def style_pattern_matches(text: str, *, patterns: Collection[re.Pattern[str]], ansi_style: str) -> str:
    """Return ``text`` rendered with the given ANSI style, reset afterward."""
    if not patterns:
        return text

    # Collect, merge overlapping, and style match ranges.
    ranges = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            ranges.append((match.start(), match.end()))

    merged_ranges = []

    for start, end in sorted(ranges):
        if merged_ranges and start <= merged_ranges[-1][1]:
            merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], end))
        else:
            merged_ranges.append((start, end))

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
