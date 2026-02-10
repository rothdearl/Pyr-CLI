#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: order.py
Author: Roth Earl
Version: 1.3.14
Description: A program that sorts files and prints them to standard output.
License: GNU GPLv3
"""

import argparse
import datetime
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


class FieldPatterns:
    """
    Namespace for field pattern constants.

    :cvar DIGITS: Pattern for splitting fields on digits.
    :cvar NON_ALPHANUMERIC: Pattern for splitting fields on non-alphanumeric characters.
    :cvar NON_SPACE_WHITESPACE: Pattern for splitting fields on non-space whitespace characters.
    :cvar NO_MATCH: Pattern that never matches.
    """
    DIGITS: Final[str] = r"[0-9]+"
    NON_ALPHANUMERIC: Final[str] = r"[^a-zA-Z0-9]"
    NON_SPACE_WHITESPACE: Final[str] = r"[\f\r\n\t\v]"
    NO_MATCH: Final[str] = "(?!.)"
    WORDS: Final[str] = r"\b\w+\b"


class Order(CLIProgram):
    """A program that sorts files and prints them to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Order`` instance."""
        super().__init__(name="order", version="1.3.14")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="sort and print FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        sort_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--ignore-leading-blanks", action="store_true", help="ignore leading whitespace")
        sort_group.add_argument("-c", "--currency-sort", action="store_true", help="sort lines by currency value")
        sort_group.add_argument("-d", "--dictionary-order", action="store_true", help="sort lines in dictionary order")
        sort_group.add_argument("-D", "--date-sort", action="store_true", help="sort lines by date")
        sort_group.add_argument("-n", "--natural-sort", action="store_true",
                                help="sort lines in natural order (numbers numeric)")
        sort_group.add_argument("-R", "--random-sort", action="store_true", help="sort lines in random order")
        parser.add_argument("-f", "--skip-fields", default=0, help="skip the first N fields when comparing (N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when comparing")
        parser.add_argument("-r", "--reverse", action="store_true", help="reverse the order of the sort")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--decimal-sep", choices=("period", "comma"), default="period",
                            help="use period or comma as decimal separator (default: period)")
        parser.add_argument("--field-pattern", help="use PATTERN to split lines into fields (affects --skip-fields)",
                            metavar="PATTERN")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        if self.args.skip_fields < 0:  # --skip-fields
            self.print_error_and_exit("--skip-fields must be >= 0")

    def generate_currency_sort_key(self, line: str) -> tuple[int, float | str]:
        """
        Return a sort key that orders currency-like values numerically when possible.

        :param line: Line to derive key from.
        :return: ``(0, number)`` when the key parses as a number, otherwise ``(1, text)``.
        """
        key = self.make_sort_key(line, default_field_pattern=FieldPatterns.NON_SPACE_WHITESPACE)
        negative = "-" in key or "(" in key and ")" in key  # Negative if key contains "-" or "(" and ")".

        # Remove non-numeric characters and normalize.
        number = self.normalize_number(re.sub(pattern=r"[^0-9,.]", repl="", string=key))

        try:
            return 0, float(number) * (-1 if negative else 1)  # Convert to float and apply sign.
        except ValueError:
            return 1, key

    def generate_date_sort_key(self, line: str) -> tuple[int, datetime.datetime | str]:
        """
        Return a sort key that compares date-like values chronologically when possible.

        :param line: Line to derive key from.
        :return: ``(0, date)`` when the key parses as a date, otherwise ``(1, text)``.
        """
        key = self.make_sort_key(line, default_field_pattern=FieldPatterns.NON_SPACE_WHITESPACE)

        try:
            return 0, parse(key)
        except ParserError:
            return 1, key

    def generate_default_sort_key(self, line: str) -> str:
        """Return a sort key that orders text lexicographically using whitespace-delimited fields."""
        return self.make_sort_key(line, default_field_pattern=FieldPatterns.NO_MATCH)

    def generate_dictionary_sort_key(self, line: str) -> str:
        """Return a sort key that orders text lexicographically using whitespace and non-word characters."""
        return self.make_sort_key(line, default_field_pattern=FieldPatterns.NON_ALPHANUMERIC)

    def generate_natural_sort_key(self, line: str) -> tuple[int, float | str]:
        """
        Return a sort key that orders text lexicographically and numbers numerically.

        :param line: Line to derive key from.
        :return: ``(0, number)`` when the key parses as a number, otherwise ``(1, text)``.
        """
        key = self.make_sort_key(line, default_field_pattern=FieldPatterns.DIGITS)

        try:
            return 0, float(self.normalize_number(key))
        except ValueError:
            return 1, key

    def get_sort_fields(self, line: str, *, default_field_pattern: str) -> list[str]:
        """Return the normalized fields used for sorting after skipping the first ``skip_fields`` fields."""
        field_pattern = self.args.field_pattern or default_field_pattern
        fields = []

        # Normalize line before splitting.
        line = self.normalize_line(line)

        try:
            for index, field in enumerate(re.split(field_pattern, line)):
                if index >= self.args.skip_fields:  # --skip-fields
                    fields.append(field)
        except re.error:  # re.PatternError was introduced in Python 3.13; use re.error for Python < 3.13.
            self.print_error_and_exit(f"invalid regex pattern: {field_pattern}")

        # print(fields)
        return fields

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

    def make_sort_key(self, line: str, *, default_field_pattern: str) -> str:
        """Return a normalized sort key after skipping the first ``skip_fields`` non-empty fields."""
        return " ".join(self.get_sort_fields(line, default_field_pattern=default_field_pattern))

    def normalize_line(self, line: str) -> str:
        """Return the line with trailing whitespace removed and optional leading-blank and case normalization applied."""
        line = line.rstrip()  # Remove trailing whitespace.

        if self.args.ignore_leading_blanks:  # --ignore-leading-blanks
            line = line.lstrip()

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def normalize_number(self, number: str) -> str:
        """Return the number with a period "." as the decimal separator and no thousands separators."""
        if self.args.decimal_sep == "period":  # --decimal-sep
            # Remove thousands separator.
            return number.replace(",", "")

        # Remove thousands separator, then replace commas with decimals.
        return number.replace(".", "").replace(",", ".")

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
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
        """Read, sort, and print lines from each file."""
        for _, file, text in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file)
                self.sort_and_print_lines(text.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file}: unable to read with {self.encoding}")

    def sort_and_print_lines_from_input(self) -> None:
        """Read, sort, and print lines from standard input until EOF."""
        self.sort_and_print_lines(sys.stdin.readlines())


if __name__ == "__main__":
    Order().run()
