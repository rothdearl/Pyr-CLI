#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that counts lines, words, and characters in files."""

import argparse
import re
import sys
from collections.abc import Iterable
from typing import Final, NamedTuple, override

from cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COUNT: Final[str] = ansi.Colors.BRIGHT_CYAN
    COUNT_TOTAL: Final[str] = ansi.Colors.BRIGHT_YELLOW
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Counts(NamedTuple):
    """Immutable container for information about counts."""
    lines: int
    words: int
    characters: int
    max_line_length: int


class Tally(TextProgram):
    """
    A program that counts lines, words, and characters in files.

    :cvar WORD_PATTERN: Matches a whole word token.
    :ivar files_counted: Number of files counted.
    :ivar flags: Flags for determining if a count attribute will be printed.
    :ivar totals: Total counts across all files.
    """

    WORD_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b\w+\b")

    def __init__(self) -> None:
        """Initialize a new ``Tally`` instance."""
        super().__init__(name="tally", version="1.4.3")

        self.files_counted: int = 0
        self.flags: list[bool] = [False, False, False, False]  # [lines, words, characters, max_line_length]
        self.totals: Counts = Counts(0, 0, 0, 0)

    def add_counts_to_totals(self, counts: Counts) -> None:
        """Add the counts to the totals."""
        self.totals = Counts(
            self.totals.lines + counts.lines,
            self.totals.words + counts.words,
            self.totals.characters + counts.characters,
            max(self.totals.max_line_length, counts.max_line_length)
        )

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="count lines, words, and characters in FILES",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-l", "--lines", action="store_true", help="print line counts")
        parser.add_argument("-c", "--chars", action="store_true", help="print character counts")
        parser.add_argument("-w", "--words", action="store_true", help="print word counts")
        parser.add_argument("-L", "--max-line-length", action="store_true", help="print maximum line length")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print total counts in an extra line (default: auto)")
        parser.add_argument("-t", "--tab-width", default=8,
                            help="use N spaces per tab when computing line length (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("--count-width", default=8, help="pad counts to width N (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for counts and file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def calculate_counts(self, lines: Iterable[str]) -> Counts:
        """Calculate counts for lines, words, characters, and the maximum displayed line length in the lines."""
        character_count, line_count, max_line_length, words = 0, 0, 0, 0

        for raw_line in lines:
            display_line = text.strip_trailing_newline(raw_line)
            max_display_width = len(display_line.expandtabs(self.args.tab_width))

            character_count += len(raw_line)
            line_count += 1
            max_line_length = max(max_display_width, max_line_length)
            words += len(self.WORD_PATTERN.findall(display_line))

        return Counts(line_count, words, character_count, max_line_length)

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        counts = self.calculate_counts(file_info.text_stream)

        self.files_counted += 1
        self.add_counts_to_totals(counts)
        self.print_counts(counts, origin_file=file_info.file_name)

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        # Check which count flags were provided: --lines, --words, --chars, or --max-line-length
        for index, flag in enumerate((self.args.lines, self.args.words, self.args.chars, self.args.max_line_length)):
            if flag:
                self.flags[index] = True

        # If no count flags, default to lines (0), words (1), and characters (2).
        if not sum(self.flags):
            for index in (0, 1, 2):
                self.flags[index] = True

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            else:
                if standard_input := sys.stdin.readlines():
                    counts = self.calculate_counts(standard_input)

                    self.files_counted += 1
                    self.add_counts_to_totals(counts)
                    self.print_counts(counts, origin_file="(standard input)" if self.args.files else "")

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_counts_from_input()

        if self.args.total == "on" or (self.args.total == "auto" and self.files_counted > 1):
            self.print_counts(self.totals, origin_file="total")

    def print_counts(self, counts: Counts, *, origin_file: str) -> None:
        """Print line, word, and character counts for the given file."""
        count_color = Colors.COUNT_TOTAL if origin_file == "total" else Colors.COUNT
        origin_file_color = Colors.COUNT_TOTAL if origin_file == "total" else Colors.FILE_NAME
        padding = self.args.count_width if origin_file or sum(self.flags) > 1 else 0  # 0 if standard input or one flag.

        for index, count in enumerate(counts):
            if self.flags[index]:
                if self.print_color:
                    print(f"{count_color}{count:>{padding},}{ansi.RESET}", end="")
                else:
                    print(f"{count:>{padding},}", end="")

        if origin_file:
            if self.print_color:
                print(f" {origin_file_color}{origin_file}{ansi.RESET}")
            else:
                print(f" {origin_file}")
        else:
            print()

    def print_counts_from_input(self) -> None:
        """Read, count, and print from standard input until EOF."""
        counts = self.calculate_counts(sys.stdin)

        self.add_counts_to_totals(counts)
        self.print_counts(counts, origin_file="")

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.count_width < 1:
            self.print_error_and_exit("--count-width must be >= 1")

        if self.args.tab_width < 1:
            self.print_error_and_exit("--tab-width must be >= 1")


if __name__ == "__main__":
    Tally().run()
