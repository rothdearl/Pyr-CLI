"""
Module for command-line programs to find patterns.
"""

import re
from typing import Iterator

from cli import CLIProgram, colors


def _split_pattern_on_pipe(pattern: str) -> Iterator[str]:
    """
    Splits the pattern on the pipe character if it is not escaped by a backslash character.
    :param pattern: The pattern.
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


def color_patterns_in_text(text: str, patterns: list[list[re.Pattern]], *, color: str) -> str:
    """
    Colors all patterns in the text.
    :param text: The text to color.
    :param patterns: The patterns.
    :param color: The color.
    :return: The text with all the patterns colored.
    """
    indices = []

    # Get the indices for each match.
    for pattern in patterns:
        for sub_pattern in pattern:
            for match in sub_pattern.finditer(text):
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


def compile_patterns(program: CLIProgram, patterns: list[str], *, ignore_case: bool) -> list[list[re.Pattern]]:
    """
    Returns a list of OR-groups of compiled regular expression patterns implementing AND-of-OR logic.
    :param program: The program finding patterns.
    :param patterns: The patterns.
    :param ignore_case: Whether to ignore case.
    :return: A list of compiled patterns.
    """
    compiled = []
    flags = re.IGNORECASE if ignore_case else 0

    for pattern in patterns:
        group = []

        for sub_pattern in _split_pattern_on_pipe(pattern):
            try:
                group.append(re.compile(sub_pattern, flags=flags))
            except re.PatternError:
                program.print_error(f"invalid pattern: {sub_pattern}", raise_system_exit=True)

        compiled.append(group)

    return compiled


def text_has_patterns(text: str, patterns: list[list[re.Pattern]]) -> bool:
    """
    Returns whether the text matches all pattern groups (AND), where each group requires at least one sub-pattern (OR).
    :param text: The text.
    :param patterns: The patterns.
    :return: True or False.
    """
    for pattern in patterns:
        for sub_pattern in pattern:
            if sub_pattern.search(text):
                break
        else:
            return False

    return True
