#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: order.py
Author: Roth Earl
Version: 1.3.12
Description: A program that sorts files and prints them to standard output.
License: GNU GPLv3
"""

import argparse
import os
import random
import re
import sys
from collections.abc import Iterable
from typing import Final, override

from dateutil.parser import ParserError, parse

from cli import CLIProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Order(CLIProgram):
    """
    A program that sorts files and prints them to standard output.

    :cvar NON_SPACE_WHITESPACE_PATTERN: Pattern for splitting lines on all whitespace characters except spaces.
    :cvar WHITESPACE_PATTERN: Pattern for splitting lines on all whitespace characters.
    :cvar WORD_PATTERN: Pattern for splitting lines on whitespace and non-word characters.
    """

    NON_SPACE_WHITESPACE_PATTERN: Final[str] = r"[\f\r\n\t\v]"
    WHITESPACE_PATTERN: Final[str] = r"\s+"
    WORD_PATTERN: Final[str] = r"\s+|\W+"

    def __init__(self) -> None:
        """Initialize a new ``Order`` instance."""
        super().__init__(name="order", version="1.3.12")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="sort and print FILES to standard output",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)
        sort_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--ignore-leading-blanks", action="store_true", help="ignore leading blanks")
        sort_group.add_argument("-c", "--currency-sort", action="store_true", help="sort lines by currency value")
        sort_group.add_argument("-d", "--dictionary-order", action="store_true",
                                help="sort lines using dictionary order")
        sort_group.add_argument("-D", "--date-sort", action="store_true", help="sort lines by date")
        sort_group.add_argument("-n", "--natural-sort", action="store_true",
                                help="sort alphabetically, treating numbers numerically")
        sort_group.add_argument("-R", "--random-sort", action="store_true", help="sort lines in random order")
        parser.add_argument("-f", "--skip-fields", default=0, help="skip the first N fields when sorting (N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="do not prefix output with file names")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-r", "--reverse", action="store_true", help="reverse the order of the sort")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--field-pattern",
                            help="generate sort keys by splitting lines into fields on regex PATTERN",
                            metavar="PATTERN")
        parser.add_argument("--latin1", action="store_true", help="read FILES using latin-1 (default: utf-8)")
        parser.add_argument("--no-blank", action="store_true", help="suppress all blank lines")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        if self.args.skip_fields < 0:  # --skip-fields
            self.print_error_and_exit("--skip-fields must be >= 0")

    def generate_currency_sort_key(self, line: str) -> list[str]:
        """Return a sort key that orders fields by currency values, handling symbols and accounting-style negatives."""
        return self.split_line(line, Order.NON_SPACE_WHITESPACE_PATTERN)

    def generate_date_sort_key(self, line: str) -> str:
        """Return a sort key that orders fields by the first parseable date."""
        fields = self.split_line(line, Order.NON_SPACE_WHITESPACE_PATTERN)

        try:
            date_key = str(parse(fields[0])) if fields else line
        except ParserError:
            date_key = line

        return date_key

    def generate_default_sort_key(self, line: str) -> list[str]:
        """Return a sort key that orders fields lexicographically."""
        return self.split_line(line, Order.WHITESPACE_PATTERN)

    def generate_dictionary_sort_key(self, line: str) -> list[str]:
        """Return a sort key that orders word-like fields lexicographically."""
        return self.split_line(line, Order.WORD_PATTERN)

    def generate_natural_sort_key(self, line: str) -> list[tuple[int, str | float]]:
        """
        Return a sort key that orders text lexicographically and numbers numerically.

        :param line: Line to derive key from.
        :return: A list of tuples containing the kind (0 = text, 1 = number) and comparison value.
        """
        natural_key = []

        for field in self.split_line(line, Order.WHITESPACE_PATTERN):
            try:
                number = float(field.replace(",", ""))  # Strip commas before parsing.
                natural_key.append((1, number))
            except ValueError:
                natural_key.append((0, field))

        return natural_key

    @override
    def main(self) -> None:
        """Run the program."""
        # Set --ignore-case to True if --dictionary-order=True or --natural-sort=True.
        if self.args.dictionary_order or self.args.natural_sort:
            self.args.ignore_case = True

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.sort_and_print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.sort_and_print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.sort_and_print_lines_from_files(self.args.files)
        elif self.args.files:
            self.sort_and_print_lines_from_files(self.args.files)
        else:
            self.sort_and_print_lines_from_input()

    def normalize_line(self, line: str) -> str:
        """Normalize the line for field splitting according to command-line options."""
        line = line.rstrip()  # Remove trailing whitespace.

        if self.args.ignore_leading_blanks:  # --ignore-leading-blanks
            line = line.lstrip()

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``--no-file-name`` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def sort_and_print_lines(self, lines: list[str]) -> None:
        """Sort lines in place and print them to standard output according to command-line arguments."""
        if self.args.random_sort:  # --random-sort
            random.shuffle(lines)
        else:
            key_function = (
                self.generate_currency_sort_key if self.args.currency_sort else  # --currency-sort
                self.generate_date_sort_key if self.args.date_sort else  # --date-sort
                self.generate_dictionary_sort_key if self.args.dictionary_order else  # --dictionary-order
                self.generate_natural_sort_key if self.args.natural_sort else  # --natural-sort
                self.generate_default_sort_key
            )
            reverse = self.args.reverse  # --reverse

            lines.sort(key=key_function, reverse=reverse)

        # Print lines.
        for line in io.normalize_input_lines(lines):
            if self.args.no_blank and not line.rstrip():  # --no-blank
                continue

            print(line)

    def sort_and_print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read lines from each file and print them."""
        for _, file, text in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file)
                self.sort_and_print_lines(text.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file}: unable to read with {self.encoding}")

    def sort_and_print_lines_from_input(self) -> None:
        """Read lines from standard input until EOF and print them."""
        self.sort_and_print_lines(sys.stdin.readlines())

    def split_line(self, line: str, default_field_pattern: str) -> list[str]:
        """Split the line into fields using a regular expression pattern."""
        field_pattern = self.args.field_pattern or default_field_pattern
        fields = []

        # Normalize the line before splitting.
        line = self.normalize_line(line)

        try:
            for index, field in enumerate(re.split(field_pattern, line)):
                if field and index >= self.args.skip_fields:  # --skip-fields
                    fields.append(field)
        except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
            self.print_error_and_exit(f"invalid regex pattern: {field_pattern}")

        return fields


if __name__ == "__main__":
    Order().run()
