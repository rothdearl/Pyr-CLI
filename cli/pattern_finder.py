import re
from abc import ABC
from typing import Iterator, final

from cli import CLIProgram, ConsoleColors


@final
class PatternFinder(ABC):
    """
    Utility class for programs to find patterns.
    """

    @staticmethod
    def __split_pattern_on_pipe(pattern: str) -> Iterator[str]:
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

    @staticmethod
    def color_patterns_in_text(text: str, patterns: list[str], *, ignore_case: bool, color: str) -> str:
        """
        Colors all patterns in the text.
        :param text: The text.
        :param patterns: The patterns.
        :param ignore_case: Whether to ignore case.
        :param color: The color.
        :return: The text with all the patterns colored.
        """
        flags = re.IGNORECASE if ignore_case else 0
        indices = []

        # Get the indices for each match.
        for pattern in patterns:
            for sub_pattern in PatternFinder.__split_pattern_on_pipe(pattern):
                for match in re.finditer(sub_pattern, text, flags=flags):
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

            colored_text.extend([color, text[start:end], ConsoleColors.RESET])
            prev_end = end

        if prev_end < len(text):
            colored_text.append(text[prev_end:])

        return "".join(colored_text)

    @staticmethod
    def text_has_all_patterns(program: CLIProgram, text: str, patterns: list[str], *, ignore_case: bool) -> bool:
        """
        Returns whether the text has all the patterns.
        :param program: The program finding patterns.
        :param text: The text.
        :param patterns: The patterns.
        :param ignore_case: Whether to ignore case.
        :return: True or False.
        """
        flags = re.IGNORECASE if ignore_case else 0

        for pattern in patterns:
            matched = False

            for sub_pattern in PatternFinder.__split_pattern_on_pipe(pattern):
                try:
                    if re.search(sub_pattern, text, flags=flags):
                        matched = True
                        break
                except re.PatternError:
                    program.log_error(f"invalid pattern: {sub_pattern}", raise_system_exit=True)

            if not matched:
                return False

        return True
