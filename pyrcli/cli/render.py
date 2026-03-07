"""Utilities for styling text with ANSI escape sequences."""

import re
from collections.abc import Collection
from typing import Final

from .ansi import RESET, TextAttributes


def _collect_merged_match_ranges(text: str, *, patterns: Collection[re.Pattern[str]]) -> list[tuple[int, int]]:
    """Return merged, non-overlapping match ranges for all patterns in ``text``."""
    ranges = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            ranges.append((match.start(), match.end()))

    # Merge overlapping ranges to prevent nested ANSI codes from corrupting the output.
    merged = []

    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


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
    # Avoid allocation and iteration for the empty case.
    if not patterns:
        return text

    styled_text = []
    prev_end = 0

    for start, end in _collect_merged_match_ranges(text, patterns=patterns):
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
