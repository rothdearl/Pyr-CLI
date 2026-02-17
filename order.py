#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that sorts files and prints them to standard output."""

import argparse
import datetime
import os
import random
import re
import sys
from typing import Final, override

from dateutil.parser import ParserError, parse

from cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Order(TextProgram):
    """
    A program that sorts files and prints them to standard output.

    :cvar CURRENCY_SANITIZE_REGEX: Matches one or more consecutive characters that are not digits, commas, or periods.
    :cvar DIGIT_TOKEN_REGEX: Matches (and captures) one or more decimal digits.
    :cvar NON_WORD_OR_WHITESPACE_REGEX: Matches one or more consecutive characters that are not Unicode word characters or whitespace.
    """

    CURRENCY_SANITIZE_REGEX: Final[str] = r"[^0-9,.]+"
    DIGIT_TOKEN_REGEX: Final[str] = r"(\d+)"
    NON_WORD_OR_WHITESPACE_REGEX: Final[str] = r"[^\w\s]+"

    def __init__(self) -> None:
        """Initialize a new ``Order`` instance."""
        super().__init__(name="order", version="1.4.0")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="sort and print FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        sort_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        sort_group.add_argument("-c", "--currency-sort", action="store_true", help="sort lines by currency value")
        sort_group.add_argument("-d", "--dictionary-order", action="store_true", help="sort lines in dictionary order")
        sort_group.add_argument("-D", "--date-sort", action="store_true", help="sort lines by date")
        sort_group.add_argument("-n", "--natural-sort", action="store_true",
                                help="sort lines in natural order (numbers numeric)")
        sort_group.add_argument("-R", "--random-sort", action="store_true", help="sort lines in random order")
        parser.add_argument("--decimal-comma", action="store_true",
                            help="interpret comma as the decimal separator (use with --currency-sort or --natural-sort)")
        parser.add_argument("-b", "--ignore-leading-blanks", action="store_true", help="ignore leading whitespace")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when comparing")
        parser.add_argument("-f", "--skip-fields", help="skip the first N non-empty fields when comparing (N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--field-separator",
                            help="split lines into fields using SEP (default: <space>; use with --skip-fields)",
                            metavar="SEP")
        parser.add_argument("-r", "--reverse", action="store_true", help="reverse the order of the sort")
        parser.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        # --field-separator is only meaningful with --skip-fields.
        if self.args.field_separator is not None and self.args.skip_fields is None:
            self.print_error_and_exit("--field-separator is only used with --skip-fields")

        # --decimal-comma is only meaningful with --currency-sort or --natural-sort.
        if self.args.decimal_comma and not any((self.args.currency_sort, self.args.natural_sort)):
            self.print_error_and_exit("--decimal-comma is only used with --currency-sort or --natural-sort")

    def generate_currency_sort_key(self, line: str) -> list[tuple[int, float | str]]:
        """
        Return a sort key that orders currency-like values numerically when possible.

        :param line: Line to derive key from.
        :return: A list of tuples containing ``(0, number)`` when text parses as a number, otherwise ``(1, text)``.
        """
        segments = []

        for field in self.get_sort_fields(line, filter_empty_fields=True):
            negative = "-" in field or "(" in field and ")" in field  # Negative if field contains "-" or "(" and ")".

            # Remove non-numeric characters.
            number = self.normalize_number(re.sub(pattern=Order.CURRENCY_SANITIZE_REGEX, repl="", string=field))

            try:
                segments.append((0, float(number) * (-1 if negative else 1)))  # Convert to float and apply sign.
            except ValueError:
                segments.append((1, field))

        return segments

    def generate_date_sort_key(self, line: str) -> list[tuple[int, datetime.datetime | str]]:
        """
        Return a sort key that orders date-like values chronologically when possible.

        :param line: Line to derive key from.
        :return: A list of tuples containing ``(0, date)`` when text parses as a date, otherwise ``(1, text)``.
        """
        segments = []

        for field in self.get_sort_fields(line, filter_empty_fields=True):
            try:
                segments.append((0, parse(field)))
            except ParserError:
                segments.append((1, field))

        return segments

    def generate_default_sort_key(self, line: str) -> list[str]:
        """Return a sort key that orders lines lexicographically."""
        return self.get_sort_fields(line)

    def generate_dictionary_sort_key(self, line: str) -> list[str]:
        """Return a sort key that implements case-insensitive dictionary order while ignoring punctuation."""
        sort_fields = []

        for field in self.get_sort_fields(line):
            # Remove everything except Unicode word characters and whitespace.
            sort_fields.append(re.sub(pattern=Order.NON_WORD_OR_WHITESPACE_REGEX, repl="", string=field))

        return sort_fields

    def generate_natural_sort_key(self, line: str) -> list[tuple[int, float | str]]:
        """
        Return a sort key that orders text lexicographically and numbers numerically when possible.

        :param line: Line to derive key from.
        :return: A list of tuples containing ``(0, number)`` when text parses as a number, otherwise ``(1, text)``.
        """
        segments = []

        for field in self.get_sort_fields(line, filter_empty_fields=True):
            try:
                segments.append((0, float(self.normalize_number(field))))
            except ValueError:
                # Split field into chunks and check for digits.
                for chunk in re.split(pattern=Order.DIGIT_TOKEN_REGEX, string=field):
                    if not chunk:  # Skip empty chunks.
                        continue

                    if chunk.isdigit():
                        segments.append((0, int(chunk)))
                    else:
                        segments.append((1, chunk))

        return segments

    def get_sort_fields(self, line: str, filter_empty_fields: bool = False) -> list[str]:
        """Return normalized sort fields after optional empty-field filtering and applying ``--skip-fields``."""
        normalized = self.normalize_line(line)
        separator = self.args.field_separator or " "
        skip = self.args.skip_fields

        # Split line into fields, optionally filter empty fields, and apply --skip-fields.
        fields = text.split_csv(normalized, separator=separator, on_error=self.print_error_and_exit)

        # When skipping fields, discard empty tokens first so skip counts apply to "real" fields.
        if filter_empty_fields or skip:
            fields = [field for field in fields if field]

        if skip:
            fields = fields[skip:]

        return fields

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.sort_and_print_lines(file_info.text_stream.readlines())

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.sort_and_print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.sort_and_print_lines_from_input()

    def normalize_line(self, line: str) -> str:
        """Return the line with trailing whitespace removed and optional leading-blank and case normalization applied."""
        normalized = line.rstrip()  # Remove trailing whitespace.

        if self.args.ignore_leading_blanks:
            normalized = normalized.lstrip()

        if self.args.ignore_case:
            normalized = normalized.casefold()

        return normalized

    def normalize_number(self, number: str) -> str:
        """Return the number with a period "." as the decimal separator and no thousands separators."""
        if self.args.decimal_comma:
            # Remove thousands separator, then replace commas with decimals.
            return number.replace(".", "").replace(",", ".")

        # Remove thousands separator.
        return number.replace(",", "")

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --ignore-case to True if --dictionary-order=True or --natural-sort=True.
        if self.args.dictionary_order or self.args.natural_sort:
            self.args.ignore_case = True

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def sort_and_print_lines(self, lines: list[str]) -> None:
        """Sort lines in place and print them to standard output according to command-line arguments."""
        if self.args.random_sort:
            random.shuffle(lines)
        else:
            key_function = (
                self.generate_currency_sort_key if self.args.currency_sort else
                self.generate_date_sort_key if self.args.date_sort else
                self.generate_dictionary_sort_key if self.args.dictionary_order else
                self.generate_natural_sort_key if self.args.natural_sort else
                self.generate_default_sort_key
            )
            reverse = self.args.reverse

            lines.sort(key=key_function, reverse=reverse)

        # Print lines.
        for line in io.normalize_input_lines(lines):
            if self.args.no_blank and not line.rstrip():
                continue

            print(line)

    def sort_and_print_lines_from_input(self) -> None:
        """Read, sort, and print lines from standard input until EOF."""
        self.sort_and_print_lines(sys.stdin.readlines())

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.skip_fields is not None and self.args.skip_fields < 1:
            self.print_error_and_exit("--skip-fields must be >= 1")


if __name__ == "__main__":
    Order().run()
