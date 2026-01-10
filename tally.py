#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tally.py
Author: Roth Earl
Version: 1.3.2
Description: A program to print line, word and character counts in files.
License: GNU GPLv3
"""

import argparse
import re
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, CLIProgramRunner, ConsoleColors, FileReader

# Define type aliases.
Stats = tuple[int, int, int, int]


@final
class Colors:
    """
    Class for managing colors.
    """
    STAT: Final[str] = ConsoleColors.BRIGHT_CYAN
    STAT_ORIGIN: Final[str] = ConsoleColors.BRIGHT_MAGENTA
    STAT_TOTAL: Final[str] = ConsoleColors.BRIGHT_YELLOW


@final
class Indexes:
    """
    Class for managing stat indexes.
    """
    LINES: Final[int] = 0
    WORDS: Final[int] = 1
    CHARACTERS: Final[int] = 2
    MAX_LINE_LENGTH: Final[int] = 3


@final
class Tally(CLIProgram):
    """
    A program to print line, word and character counts in files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="tally", version="1.3.2")

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
        self.TOTALS[Indexes.LINES] += stats[Indexes.LINES]
        self.TOTALS[Indexes.WORDS] += stats[Indexes.WORDS]
        self.TOTALS[Indexes.CHARACTERS] += stats[Indexes.CHARACTERS]
        self.TOTALS[Indexes.MAX_LINE_LENGTH] = max(self.TOTALS[Indexes.MAX_LINE_LENGTH], stats[Indexes.MAX_LINE_LENGTH])

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
        parser.add_argument("-t", "--tab-width", help="count tabs as N spaces instead of 8 for line length",
                            metavar="N+", type=int)
        parser.add_argument("-w", "--words", action="store_true", help="print the word counts")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display counts and file names in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input as arguments")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print a line with total counts")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def get_stats(self, text: TextIO | list[str]) -> Stats:
        """
        Returns the counts for the lines, words, characters and the maximum line length in the text.
        :param text: The text.
        :return: The stats.
        """
        character_count = 0
        line_count = 0
        max_line_length = 0
        words = 0

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

        if CLIProgram.input_is_redirected():
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
                    print(f"{stat_color}{stat:>{width},}{ConsoleColors.RESET}", end="")
                else:
                    print(f"{stat:>{width},}", end="")

        if stat_origin:
            if self.print_color:
                print(f"\t{stat_origin_color}{stat_origin}{ConsoleColors.RESET}")
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
        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                stats = self.get_stats(text)

                self.files_counted += 1
                self.add_stats_to_totals(stats)
                self.print_stats(stats, stat_origin=file)
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

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
        if self.args.tab_width:  # --tab-width
            self.tab_width = self.args.tab_width

        if self.tab_width < 1:
            self.log_error(f"tab width ({self.tab_width}) cannot be less than 1", raise_system_exit=True)

        # -1 one for the tab character.
        self.tab_width -= 1

        # Check which stat options were provided: --lines, --words, --chars, or --max-line-length
        for index, option in enumerate((self.args.lines, self.args.words, self.args.chars, self.args.max_line_length)):
            if option:
                self.OPTIONS[index] = True
                self.options_count += 1

        # If no stat options, default to lines, words and characters.
        if not self.options_count:
            self.OPTIONS[Indexes.LINES] = True
            self.OPTIONS[Indexes.WORDS] = True
            self.OPTIONS[Indexes.CHARACTERS] = True
            self.options_count = 3


if __name__ == "__main__":
    CLIProgramRunner.run(Tally())
