#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: order.py
Author: Roth Earl
Version: 1.3.7
Description: A program to sort and print files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import random
import re
import sys
from enum import StrEnum
from typing import TextIO, final

from dateutil.parser import ParserError, parse

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.BRIGHT_CYAN
    FILE_NAME = ansi.BRIGHT_MAGENTA


class FieldPatterns(StrEnum):
    """
    Field separator pattern constants.
    """
    DATES = r"[\f\r\n\t\v]"  # All whitespace except spaces.
    WHITESPACE = r"\s+"  # All whitespace.
    WORDS = r"\s+|\W+"  # All whitespace and non-words.


@final
class Order(CLIProgram):
    """
    A program to sort and print files to standard output.

    :ivar skip_fields: Number of fields to skip at the beginning of each line.
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Order`` instance.
        """
        super().__init__(name="order", version="1.3.7")

        self.skip_fields: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="sort and print FILES to standard output",
                                         epilog="if no FILES are specified, read standard input", prog=self.name)
        sort_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="one or more input files", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--ignore-leading-blanks", action="store_true", help="ignore leading blanks in lines")
        sort_group.add_argument("-d", "--dictionary-sort", action="store_true",
                                help="sort lines using dictionary order")
        sort_group.add_argument("-D", "--date-sort", action="store_true", help="sort lines by date")
        sort_group.add_argument("-k", "--key-pattern", help="generate sort keys by splitting lines on regex PATTERN",
                                metavar="PATTERN")
        sort_group.add_argument("-n", "--natural-sort", action="store_true",
                                help="sort alphabetically, treating numbers numerically")
        sort_group.add_argument("-R", "--random-sort", action="store_true", help="sort lines in random order")
        parser.add_argument("-f", "--skip-fields", help="skip the first N fields when sorting (N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-header", action="store_true", help="do not prepend file names to output")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-r", "--reverse", action="store_true", help="reverse the order of the sort")
        parser.add_argument("-s", "--skip-blank", action="store_true", help="ignore blank lines when comparing")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def generate_date_sort_key(self, line: str) -> str:
        """
        Return a date sort key.

        :param line: Line to generate key from.
        :return: Date sort key.
        """
        fields = self.split_line(line, FieldPatterns.DATES, strip_number_separators=False)

        try:
            date = str(parse(fields[0])) if fields else line
        except ParserError:
            date = line

        return date

    def generate_default_sort_key(self, line: str) -> list[str]:
        """
        Return a default sort key.

        :param line: Line to generate key from.
        :return: Default sort key.
        """
        return self.split_line(line, FieldPatterns.WHITESPACE, strip_number_separators=False)

    def generate_dictionary_sort_key(self, line: str) -> list[str]:
        """
        Return a dictionary sort key.

        :param line: Line to generate key from.
        :return: Dictionary sort key.
        """
        return self.split_line(line, FieldPatterns.WORDS, strip_number_separators=False)

    def generate_key_pattern_sort_key(self, line: str) -> list[str]:
        """
        Return a key pattern sort key.

        :param line: Line to generate key from.
        :return: Key pattern sort key.
        """
        return self.split_line(line, self.args.key_pattern, strip_number_separators=False)

    def generate_natural_sort_key(self, line: str) -> list[str]:
        """
        Return a natural sort key.

        :param line: Line to generate key from.
        :return: Natural sort key.
        """
        digits = []
        pattern = FieldPatterns.WHITESPACE

        for field in self.split_line(line, pattern, strip_number_separators=True):
            # Zero-pad integers so they sort numerically.
            if field.isdigit():
                field = f"{field:0>20}"

            digits.append(field)

        return digits

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name, or "(standard input)" if empty, with a colon.

        :param file_name: File name to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --ignore-case to True if --dictionary-sort=True or --natural-sort=True.
        if self.args.dictionary_sort or self.args.natural_sort:
            self.args.ignore_case = True

        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.sort_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.sort_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.sort_lines_from_files(self.args.files)
        elif self.args.files:
            self.sort_lines_from_files(self.args.files)
        else:
            self.sort_lines_from_input()

    def sort_lines(self, lines: list[str]) -> None:
        """
        Sort the lines.

        :param lines: Lines to sort.
        """
        reverse = self.args.reverse  # --reverse

        if self.args.date_sort:  # --date-sort
            lines.sort(key=self.generate_date_sort_key, reverse=reverse)
        elif self.args.dictionary_sort:  # --dictionary-sort
            lines.sort(key=self.generate_dictionary_sort_key, reverse=reverse)
        elif self.args.key_pattern:  # --key-pattern
            lines.sort(key=self.generate_key_pattern_sort_key, reverse=reverse)
        elif self.args.natural_sort:  # --natural-sort
            lines.sort(key=self.generate_natural_sort_key, reverse=reverse)
        elif self.args.random_sort:  # --random-sort
            random.shuffle(lines)
        else:
            lines.sort(key=self.generate_default_sort_key, reverse=reverse)

        # Print lines.
        for line in lines:
            if self.args.skip_blank and not line.rstrip():  # --skip-blank
                continue

            io.print_normalized_line(line)

    def sort_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Sort lines from files.

        :param files: Files to sort lines from.
        """
        for _, file, text in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file)
                self.sort_lines(text.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file}: unable to read with {self.encoding}")

    def sort_lines_from_input(self) -> None:
        """
        Sort lines from standard input until EOF is entered.
        """
        self.sort_lines(sys.stdin.read().splitlines())

    def split_line(self, line: str, field_pattern: str, *, strip_number_separators: bool) -> list[str]:
        """
        Split the line into a list of fields.

        :param line: Line to split.
        :param field_pattern: Pattern for getting fields.
        :param strip_number_separators: Whether to strip number separators (commas and decimals) before splitting.
        :return: List of fields.
        """
        fields = []

        if self.args.ignore_leading_blanks:  # --ignore-leading-blanks
            line = line.strip()

        if strip_number_separators:
            line = line.replace(",", "").replace(".", "")  # Strip commas and decimals.

        try:
            for index, field in enumerate(re.split(field_pattern, line)):
                if field and index >= self.skip_fields:
                    fields.append(field.casefold() if self.args.ignore_case else field)  # --ignore-case
        except re.error:
            self.print_error_and_exit(f"invalid regex pattern: {field_pattern}")

        return fields

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        self.skip_fields = self.args.skip_fields if self.args.skip_fields is not None else 0  # --skip-fields

        if self.skip_fields < 0:
            self.print_error_and_exit("'skip-fields' must be >= 0")


if __name__ == "__main__":
    CLIProgram.run(Order())
