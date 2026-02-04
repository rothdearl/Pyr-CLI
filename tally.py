#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tally.py
Author: Roth Earl
Version: 1.3.10
Description: A program to count lines, words, and characters in files.
License: GNU GPLv3
"""

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Final, TypeAlias, final, override

from cli import CLIProgram, ansi, io, terminal

# Define type aliases.
Counts: TypeAlias = tuple[int, int, int, int]  # Indexed by CountIndex.


@dataclass(frozen=True, slots=True)
class Colors:
    """
    Namespace for terminal color constants.

    :cvar COUNT: Color used for a count.
    :cvar COUNT_TOTAL: Color used for a count total.
    :cvar FILE_NAME: Color used for a file name.
    """
    COUNT: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_CYAN
    COUNT_TOTAL: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_YELLOW
    FILE_NAME: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_MAGENTA


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
    A program to count lines, words, and characters in files.

    :cvar COUNT_FLAGS: Flags for determining if a count will be printed.
    :cvar TOTALS: Total counts across all files.
    :cvar WORD_PATTERN: Pattern for splitting lines into words.
    :ivar files_counted: Number of files counted.
    :ivar flag_count: Number of flags provided as arguments.
    """

    COUNT_FLAGS: Final[list[bool]] = [False, False, False, False]  # Indexed by CountIndex.
    TOTALS: Final[list[int]] = [0, 0, 0, 0]  # Indexed by CountIndex.
    WORD_PATTERN: Final[str] = r"\b\w+\b"

    def __init__(self) -> None:
        """
        Initialize a new ``Tally`` instance.
        """
        super().__init__(name="tally", version="1.3.10")

        self.files_counted: int = 0
        self.flag_count: int = 0

    @staticmethod
    def add_counts_to_totals(counts: Counts) -> None:
        """
        Add the counts to the totals.

        :param counts: Count information.
        """
        for index in CountIndex:
            if index is CountIndex.MAX_LINE_LENGTH:
                Tally.TOTALS[index] = max(Tally.TOTALS[index], counts[index])
            else:
                Tally.TOTALS[index] += counts[index]

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="count lines, words, and characters in FILES",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-c", "--chars", action="store_true", help="print the character counts")
        parser.add_argument("-l", "--lines", action="store_true", help="print the line counts")
        parser.add_argument("-L", "--max-line-length", action="store_true",
                            help="print the maximum line length in characters")
        parser.add_argument("-t", "--tab-width", default=8,
                            help="use N spaces for tabs when computing line length (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-w", "--words", action="store_true", help="print the word counts")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for counts and file names (default: on)")
        parser.add_argument("--count-width", default=8, help="pad counts to width N (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print a line with total counts across all FILES")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def calculate_counts(self, text: Iterable[str]) -> Counts:
        """
        Calculate the counts for the lines, words, characters, and the maximum line length in the text.

        :param text: Text to count.
        :return: Count information.
        """
        character_count, line_count, max_line_length, words = 0, 0, 0, 0
        display_width_offset = -1  # Account for the newline.

        for line in text:
            line_length = len(line)
            max_display_width = len(line) + (line.count("\t") * self.args.tab_width) - display_width_offset

            character_count += line_length
            line_count += 1
            max_line_length = max(max_display_width, max_line_length)
            words += len(re.findall(Tally.WORD_PATTERN, line))

        return line_count, words, character_count, max_line_length

    @override
    def check_parsed_arguments(self) -> None:
        """
        Validate parsed command-line arguments.
        """
        if self.args.count_width < 1:  # --count-width
            self.print_error_and_exit("'count-width' must be >= 1")

        if self.args.tab_width < 1:  # --tab-width
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

    @override
    def main(self) -> None:
        """
        Run the program logic.
        """
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_counts_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    counts = self.calculate_counts(standard_input)

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

    def print_counts(self, counts: Iterable, *, count_origin: str) -> None:
        """
        Print counts.

        :param counts: Count information.
        :param count_origin: Where the counts originated from.
        """
        count_color = Colors.COUNT_TOTAL if count_origin == "total" else Colors.COUNT
        count_origin_color = Colors.COUNT_TOTAL if count_origin == "total" else Colors.FILE_NAME

        for index, count in enumerate(counts):
            if Tally.COUNT_FLAGS[index]:
                padding = self.args.count_width if self.flag_count > 1 or count_origin else 0

                if self.print_color:
                    print(f"{count_color}{count:>{padding},}{ansi.RESET}", end="")
                else:
                    print(f"{count:>{padding},}", end="")

        if count_origin:
            if self.print_color:
                print(f" {count_origin_color}{count_origin}{ansi.RESET}")
            else:
                print(f" {count_origin}")
        else:
            print()

    def print_counts_from_files(self, files: Iterable[str]) -> None:
        """
        Read lines from each file, then count and print.

        :param files: Iterable of files to read.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                counts = self.calculate_counts(file_info.text)

                self.files_counted += 1
                self.add_counts_to_totals(counts)
                self.print_counts(counts, count_origin=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_counts_from_input(self) -> None:
        """
        Read lines from standard input until EOF, then count and print.
        """
        counts = self.calculate_counts(sys.stdin)

        self.add_counts_to_totals(counts)
        self.print_counts(counts, count_origin="")


if __name__ == "__main__":
    Tally().run()
