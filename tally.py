#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tally.py
Author: Roth Earl
Version: 1.3.7
Description: A program to print line, word, and character counts in files.
License: GNU GPLv3
"""

import argparse
import re
import sys
from collections.abc import Iterable
from enum import IntEnum, StrEnum
from typing import Final, TextIO, TypeAlias, final

from cli import CLIProgram, ansi, io, terminal

# Define type aliases.
Counts: TypeAlias = tuple[int, int, int, int]
Totals: TypeAlias = list[int]


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COUNT = ansi.BRIGHT_CYAN
    COUNT_ORIGIN = ansi.BRIGHT_MAGENTA
    COUNT_TOTAL = ansi.BRIGHT_YELLOW


class CountIndex(IntEnum):
    """
    Count index constants.
    """
    LINES = 0
    WORDS = 1
    CHARACTERS = 2
    MAX_LINE_LENGTH = 3


@final
class Tally(CLIProgram):
    """
    A program to print line, word, and character counts in files.

    :cvar COUNT_FLAGS: Flags for determining if a count will be printed.
    :cvar TOTALS: Total of all counts.
    :cvar WORD_PATTERN: Pattern for splitting lines into words.
    :ivar files_counted: Number of files counted.
    :ivar flag_count: Number of flags provided as arguments.
    """

    COUNT_FLAGS: Final[list[bool]] = [False, False, False, False]
    TOTALS: Final[Totals] = [0, 0, 0, 0]
    WORD_PATTERN: Final[str] = r"\b\w+\b"

    def __init__(self) -> None:
        """
        Initialize a new ``Tally`` instance.
        """
        super().__init__(name="tally", version="1.3.7")

        self.files_counted: int = 0
        self.flag_count: int = 0

    @staticmethod
    def add_counts_to_totals(counts: Counts) -> None:
        """
        Add the counts to the totals.

        :param counts: Count information.
        """
        Tally.TOTALS[CountIndex.LINES] += counts[CountIndex.LINES]
        Tally.TOTALS[CountIndex.WORDS] += counts[CountIndex.WORDS]
        Tally.TOTALS[CountIndex.CHARACTERS] += counts[CountIndex.CHARACTERS]
        Tally.TOTALS[CountIndex.MAX_LINE_LENGTH] = max(Tally.TOTALS[CountIndex.MAX_LINE_LENGTH],
                                                       counts[CountIndex.MAX_LINE_LENGTH])

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="print line, word and character counts in FILES",
                                         epilog="with no FILES, read standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-c", "--chars", action="store_true", help="print the character counts")
        parser.add_argument("-l", "--lines", action="store_true", help="print the line counts")
        parser.add_argument("-L", "--max-line-length", action="store_true", help="print the maximum line length")
        parser.add_argument("-t", "--tab-width", default=8,
                            help="use N spaces for tabs when computing line length (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-w", "--words", action="store_true", help="print the word counts")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="colorize counts and file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print a line with total counts")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def get_counts(self, text: Iterable[str] | TextIO, *, has_newlines: bool) -> Counts:
        """
        Return counts for the lines, words, characters, and the maximum line length in the text.

        :param text: Text to count.
        :param has_newlines: Whether the text has newlines.
        :return: Count information.
        """
        character_count, line_count, max_line_length, words = 0, 0, 0, 0
        display_width_offset = -1 if has_newlines else 0
        line_length_offset = 0 if has_newlines else 1

        for line in text:
            line_length = len(line) + line_length_offset
            max_display_width = len(line) + (line.count("\t") * self.args.tab_width) - display_width_offset

            character_count += line_length
            line_count += 1
            max_line_length = max(max_display_width, max_line_length)
            words += len(re.findall(Tally.WORD_PATTERN, line))

        return line_count, words, character_count, max_line_length

    def main(self) -> None:
        """
        Run the primary function of the program.
        """
        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_counts_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    counts = self.get_counts(standard_input, has_newlines=True)

                    self.files_counted += 1
                    self.add_counts_to_totals(counts)
                    self.print_counts(counts, count_origin="(standard input)" if self.args.files else "")

            if self.args.files:  # Process any additional files.
                self.print_counts_from_files(self.args.files)
        elif self.args.files:
            self.print_counts_from_files(self.args.files)
        else:
            self.print_counts_from_input()

        if self.args.total == "on" or (self.args.total == "auto" and self.files_counted > 1):  # --total
            self.print_counts(Tally.TOTALS, count_origin="total")

    def print_counts(self, counts: Counts | Totals, *, count_origin: str) -> None:
        """
        Print the counts.

        :param counts: Count information.
        :param count_origin: Where the counts originated from.
        """
        count_color = Colors.COUNT_TOTAL if count_origin == "total" else Colors.COUNT
        count_origin_color = Colors.COUNT_TOTAL if count_origin == "total" else Colors.COUNT_ORIGIN

        for index, count in enumerate(counts):
            if Tally.COUNT_FLAGS[index]:
                width = 12 if self.flag_count > 1 or count_origin else 0

                if self.print_color:
                    print(f"{count_color}{count:>{width},}{ansi.RESET}", end="")
                else:
                    print(f"{count:>{width},}", end="")

        if count_origin:
            if self.print_color:
                print(f"\t{count_origin_color}{count_origin}{ansi.RESET}")
            else:
                print(f"\t{count_origin}")
        else:
            print()

    def print_counts_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Print counts from the files.

        :param files: Files to count.
        """
        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            try:
                counts = self.get_counts(file_info.text, has_newlines=True)

                self.files_counted += 1
                self.add_counts_to_totals(counts)
                self.print_counts(counts, count_origin=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_counts_from_input(self) -> None:
        """
        Prints counts from standard input until EOF is entered.
        """
        counts = self.get_counts(sys.stdin.read().splitlines(), has_newlines=False)

        self.add_counts_to_totals(counts)
        self.print_counts(counts, count_origin="")

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        if self.args.tab_width < 1:
            self.print_error_and_exit("'tab-width' must be >= 1")

        # -1 one for the tab character.
        self.args.tab_width -= 1

        # Check which count flags were provided: --lines, --words, --chars, or --max-line-length
        for index, flag in enumerate((self.args.lines, self.args.words, self.args.chars, self.args.max_line_length)):
            if flag:
                Tally.COUNT_FLAGS[index] = True
                self.flag_count += 1

        # If no count flags, default to lines, words and characters.
        if not self.flag_count:
            flags = (CountIndex.LINES, CountIndex.WORDS, CountIndex.CHARACTERS)

            for index in flags:
                Tally.COUNT_FLAGS[index] = True

            self.flag_count = len(flags)


if __name__ == "__main__":
    Tally().run()
