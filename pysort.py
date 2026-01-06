#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: pysort.py
Author: Roth Earl
Version: 1.2.1
Description: A program to sort and print files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import random
import re
import sys
from typing import Final, TextIO, final

from dateutil.parser import ParserError, parse

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = ConsoleColors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ConsoleColors.BRIGHT_MAGENTA


@final
class PySort(CLIProgram):
    """
    A program to sort and print files to standard output.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="pysort", version="1.2.1")

        self.DATE_PATTERN: Final[str] = r"[\f\r\n\t\v]"  # All whitespace except spaces.
        self.DEFAULT_PATTERN: Final[str] = r"\s+"  # All whitespace.
        self.WORD_PATTERN: Final[str] = r"\s+|\W+"  # All whitespace and non-words.
        self.pattern: str | None = None
        self.skip_fields: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="sort FILES to standard output",
                                         epilog="with no FILES, read standard input", prog=self.NAME)
        sort_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="files to sort", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--no-blank", action="store_true", help="suppress blank lines")
        sort_group.add_argument("-d", "--dictionary-sort", action="store_true", help="compare lines lexicographically")
        sort_group.add_argument("-D", "--date-sort", action="store_true", help="compare dates from newest to oldest")
        sort_group.add_argument("-n", "--natural-sort", action="store_true",
                                help="compare words alphabetically and numbers numerically")
        sort_group.add_argument("-R", "--random-sort", action="store_true", help="randomize the result of comparisons")
        parser.add_argument("-f", "--skip-fields", help="avoid comparing the first N fields", metavar="N", type=int)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-p", "--pattern", help="split lines into fields using PATTERN", nargs=1)
        parser.add_argument("-r", "--reverse", action="store_true", help="reverse the result of comparisons")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display the file names in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--pipe", action="store_true", help="read FILES from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def get_date_sort_key(self, line: str) -> str:
        """
        Returns the date sort key.
        :param line: The line.
        :return: The date sort key.
        """
        fields = self.split_line(line, self.DATE_PATTERN if self.pattern is None else self.pattern)

        try:
            if fields:
                date = str(parse(fields[0]))
            else:
                date = line
        except ParserError:
            date = line

        return date

    def get_default_sort_key(self, line: str) -> list[str]:
        """
        Returns the default sort key.
        :param line: The line.
        :return: The default sort key.
        """
        return self.split_line(line, self.DEFAULT_PATTERN if self.pattern is None else self.pattern)

    def get_dictionary_sort_key(self, line: str) -> list[str]:
        """
        Returns the dictionary sort key.
        :param line: The line.
        :return: The dictionary sort key.
        """
        return self.split_line(line, self.WORD_PATTERN if self.pattern is None else self.pattern)

    def get_natural_sort_key(self, line: str) -> list[str]:
        """
        Returns the natural sort key.
        :param line: The line.
        :return: The natural sort key.
        """
        digits = []
        pattern = self.DEFAULT_PATTERN if self.pattern is None else self.pattern

        for field in self.split_line(line, pattern, strip_number_separators=True):
            # Zero-pad integers so they sort numerically.
            if field.isdigit():
                field = f"{field:0>20}"

            digits.append(field)

        return digits

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.
        :param file: The file.
        :return: None
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ConsoleColors.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_field_info_values()

        # Set --ignore-case to True if --dictionary-sort=True or --natural-sort=True.
        if self.args.dictionary_sort or self.args.natural_sort:
            self.args.ignore_case = True

        # Set --no-file-header to True if there are no files and --pipe=False.
        if not self.args.files and not self.args.pipe:
            self.args.no_file_header = True

        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
                self.sort_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.sort_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.sort_lines_from_files(self.args.files)
        elif self.args.files:
            self.sort_lines_from_files(self.args.files)
        else:
            self.sort_lines_from_input()

    def set_field_info_values(self) -> None:
        """
        Sets the values to use for sorting lines.
        :return: None
        """
        self.pattern = None if not self.args.pattern else self.args.pattern[0]  # --pattern
        self.skip_fields = 0 if not self.args.skip_fields else self.args.skip_fields  # --skip-fields

        # Validate the field values.
        if self.skip_fields < 0:
            self.log_error(f"skip fields ({self.skip_fields}) cannot be less than 0", raise_system_exit=True)

    def sort_lines(self, lines: list[str]) -> None:
        """
        Sorts the lines.
        :param lines: The lines.
        :return: None
        """
        if self.args.date_sort:  # --date-sort
            lines.sort(key=self.get_date_sort_key, reverse=self.args.reverse)
        elif self.args.dictionary_sort:  # --dictionary-sort
            lines.sort(key=self.get_dictionary_sort_key, reverse=self.args.reverse)
        elif self.args.natural_sort:  # --natural-sort
            lines.sort(key=self.get_natural_sort_key, reverse=self.args.reverse)
        elif self.args.random_sort:  # --random-sort
            random.shuffle(lines)
        else:
            lines.sort(key=self.get_default_sort_key, reverse=self.args.reverse)

        # Print lines.
        for line in lines:
            if self.args.no_blank and not line.rstrip():  # --no-blank
                continue

            CLIProgram.print_line(line)

    def sort_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Sorts lines from files.
        :param files: The files.
        :return: None
        """
        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.print_file_header(file)
                self.sort_lines(text.readlines())
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

    def sort_lines_from_input(self) -> None:
        """
        Sorts lines from standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(input())
            except EOFError:
                eof = True

        self.sort_lines(lines)

    def split_line(self, line: str, field_pattern: str, *, strip_number_separators: bool = False) -> list[str]:
        """
        Splits the line into a list of fields.
        :param line: The line.
        :param field_pattern: The pattern for getting fields.
        :param strip_number_separators: Whether to strip number separators (commas and decimals) before splitting.
        :return: A list of fields.
        """
        fields = []

        # Strip leading and trailing whitespace.
        line = line.strip()

        # Strip commas and decimals.
        if strip_number_separators:
            line = line.replace(",", "").replace(".", "")

        try:
            for index, field in enumerate(re.split(field_pattern, line)):
                if field and index >= self.skip_fields:
                    fields.append(field.casefold() if self.args.ignore_case else field)  # --ignore-case
        except re.error:
            self.log_error(f"invalid regex pattern: {field_pattern}", raise_system_exit=True)

        return fields


if __name__ == "__main__":
    CLIProgram.run(PySort())
