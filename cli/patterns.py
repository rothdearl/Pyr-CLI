"""
Module for pattern related functions.
"""

import re
from typing import Iterator

from cli import CLIProgram, colors


def _split_pattern_on_pipe(pattern: str) -> Iterator[str]:
    """
    Splits the pattern on the pipe character if it is not escaped by a backslash character.
    :param pattern: The pattern to split.
    :return: A list of patterns.
    """
    prev_ch = None
    token_start = 0

    for index, ch in enumerate(pattern):
        if ch == "|" and prev_ch != "\\":
            if token := pattern[token_start:index]:
                yield token

            token_start = index + 1

        prev_ch = ch

    if token := pattern[token_start:]:
        yield token


def color_patterns_in_text(text: str, patterns: list[re.Pattern], *, color: str) -> str:
    """
    Colors all patterns in the text.
    :param text: The text to color.
    :param patterns: The patterns to color.
    :param color: The color.
    :return: The text with all patterns colored.
    """
    indices = []

    # Get the indices for each match.
    for group in patterns:
        for match in group.finditer(text):
            indices.append((match.start(), match.end()))

    # Merge the overlapping indices.
    merged_indices = []

    for start, end in sorted(indices):
        if merged_indices and start <= merged_indices[-1][1]:
            merged_indices[-1] = (merged_indices[-1][0], max(merged_indices[-1][1], end))
        else:
            merged_indices.append((start, end))

    # Color the indices.
    colored_text = []
    prev_end = 0

    for start, end in merged_indices:
        if prev_end < start:
            colored_text.append(text[prev_end:start])

        colored_text.extend([color, text[start:end], colors.RESET])
        prev_end = end

    if prev_end < len(text):
        colored_text.append(text[prev_end:])

    return "".join(colored_text)


def compile_patterns(program: CLIProgram, patterns: list[str], *, ignore_case: bool) -> list[re.Pattern]:
    """
    Compiles patterns into OR-groups implementing AND-of-OR matching.
    :param program: The program finding patterns.
    :param patterns: The patterns to compile.
    :param ignore_case: Whether to ignore case.
    :return: A list of OR-groups of compiled regular expression patterns.
    """
    compiled = []
    flags = re.IGNORECASE if ignore_case else re.NOFLAG

    for pattern in patterns:
        group = [sub_group for sub_group in _split_pattern_on_pipe(pattern)]

        if not group:  # Skip empty groups.
            continue

        try:
            compiled.append(re.compile("|".join(group), flags=flags))
        except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
            program.print_error(f"invalid pattern: {pattern}", raise_system_exit=True)

    return compiled


def text_has_patterns(text: str, patterns: list[re.Pattern]) -> bool:
    """
    Returns whether the text matches all patterns.
    :param text: The text.
    :param patterns: The patterns to match.
    :return: True or False.
    """
    for group in patterns:
        if not group.search(text):
            return False

    return True
