#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tally.py
Author: Roth Earl
Version: 1.3.4
Description: A program to print line, word and character counts in files.
License: GNU GPLv3
"""

import argparse
import re
import sys
from enum import IntEnum, StrEnum
from typing import Final, TextIO, TypeAlias, final

from cli import CLIProgram, colors, io, terminal

# Define type aliases.
Stats: TypeAlias = tuple[int, int, int, int]


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    STAT = colors.BRIGHT_CYAN
    STAT_ORIGIN = colors.BRIGHT_MAGENTA
    STAT_TOTAL = colors.BRIGHT_YELLOW


class StatIndex(IntEnum):
    """
    Stat index constants.
    """
    LINES = 0
    WORDS = 1
    CHARACTERS = 2
    MAX_LINE_LENGTH = 3


@final
class Tally(CLIProgram):
    """
    A program to print line, word and character counts in files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="tally", version="1.3.4")

        self.OPTIONS: Final[list[bool]] = [False, False, False, False]
        self.TOTALS: Final[list[int]] = [0, 0, 0, 0]
        self.WORD_PATTERN: Final[str] = r"\b\w+\b"
        self.files_counted: int = 0
        self.options_count: int = 0
        self.tab_width: int = 8

    def add_stats_to_totals(self, stats: Stats) -> None:
        """
        Adds the stats to the totals.
        :param stats: The stats.
        :return: None
        """
        self.TOTALS[StatIndex.LINES] += stats[StatIndex.LINES]
        self.TOTALS[StatIndex.WORDS] += stats[StatIndex.WORDS]
        self.TOTALS[StatIndex.CHARACTERS] += stats[StatIndex.CHARACTERS]
        self.TOTALS[StatIndex.MAX_LINE_LENGTH] = max(self.TOTALS[StatIndex.MAX_LINE_LENGTH],
                                                     stats[StatIndex.MAX_LINE_LENGTH])

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="print line, word and character counts in FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to count", metavar="FILES", nargs="*")
        parser.add_argument("-c", "--chars", action="store_true", help="print the character counts")
        parser.add_argument("-l", "--lines", action="store_true", help="print the line counts")
        parser.add_argument("-L", "--max-line-length", action="store_true", help="print the maximum line length")
        parser.add_argument("-t", "--tab-width",
                            help="use N spaces for tabs when computing line length (default: 8; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-w", "--words", action="store_true", help="print the word counts")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="colorize counts and file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="treat standard input as a list of FILES")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print a line with total counts")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def get_stats(self, text: TextIO | list[str]) -> Stats:
        """
        Returns the counts for the lines, words, characters and the maximum line length in the text.
        :param text: The text.
        :return: The stats.
        """
        character_count, line_count, max_line_length, words = 0, 0, 0, 0

        for line in text:
            line_length = len(line)
            max_display_width = line_length + (line.count("\t") * self.tab_width) - 1  # -1 for the newline.

            character_count += line_length
            line_count += 1
            max_line_length = max(max_display_width, max_line_length)
            words += len(re.findall(self.WORD_PATTERN, line))

        return line_count, words, character_count, max_line_length

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_count_info_values()

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_stats_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    stats = self.get_stats(standard_input)

                    self.files_counted += 1
                    self.add_stats_to_totals(stats)
                    self.print_stats(stats, stat_origin="(standard input)" if self.args.files else "")

            if self.args.files:  # Process any additional files.
                self.print_stats_from_files(self.args.files)
        elif self.args.files:
            self.print_stats_from_files(self.args.files)
        else:
            self.print_stats_from_input()

        if self.args.total == "on" or (self.args.total == "auto" and self.files_counted > 1):  # --total
            self.print_stats(self.TOTALS, stat_origin="total")

    def print_stats(self, stats: Stats | list[int], *, stat_origin: str) -> None:
        """
        Prints the stats.
        :param stats: The stats.
        :param stat_origin: Where the stats originated from.
        :return: None
        """
        stat_color = Colors.STAT_TOTAL if stat_origin == "total" else Colors.STAT
        stat_origin_color = Colors.STAT_TOTAL if stat_origin == "total" else Colors.STAT_ORIGIN

        for index, stat in enumerate(stats):
            if self.OPTIONS[index]:
                width = 12 if self.options_count > 1 or stat_origin else 0

                if self.print_color:
                    print(f"{stat_color}{stat:>{width},}{colors.RESET}", end="")
                else:
                    print(f"{stat:>{width},}", end="")

        if stat_origin:
            if self.print_color:
                print(f"\t{stat_origin_color}{stat_origin}{colors.RESET}")
            else:
                print(f"\t{stat_origin}")
        else:
            print()

    def print_stats_from_files(self, files: TextIO | list[str]) -> None:
        """
        Prints stats from files.
        :param files: The files.
        :return: None
        """
        for file_info in io.read_files(files, self.encoding, logger=self):
            try:
                stats = self.get_stats(file_info.text)

                self.files_counted += 1
                self.add_stats_to_totals(stats)
                self.print_stats(stats, stat_origin=file_info.filename)
            except UnicodeDecodeError:
                self.print_file_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def print_stats_from_input(self) -> None:
        """
        Prints stats from standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(f"{input()}\n")  # Add a newline to the input.
            except EOFError:
                eof = True

        # Print stats.
        stats = self.get_stats(lines)

        self.add_stats_to_totals(stats)
        self.print_stats(stats, stat_origin="")

    def set_count_info_values(self) -> None:
        """
        Sets the values to use for counting.
        :return: None
        """
        self.tab_width = self.args.tab_width if self.args.tab_width is not None else 8  # --tab-width

        if self.tab_width < 1:
            self.print_error(f"'tab-width' must be >= 1", raise_system_exit=True)

        # -1 one for the tab character.
        self.tab_width -= 1

        # Check which stat options were provided: --lines, --words, --chars, or --max-line-length
        for index, option in enumerate((self.args.lines, self.args.words, self.args.chars, self.args.max_line_length)):
            if option:
                self.OPTIONS[index] = True
                self.options_count += 1

        # If no stat options, default to lines, words and characters.
        if not self.options_count:
            self.OPTIONS[StatIndex.LINES] = True
            self.OPTIONS[StatIndex.WORDS] = True
            self.OPTIONS[StatIndex.CHARACTERS] = True
            self.options_count = 3


if __name__ == "__main__":
    Tally().run()
