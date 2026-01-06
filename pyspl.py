#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: pyspl.py
Author: Roth Earl
Version: 1.2.1
Description: A program to split lines into fields.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = ConsoleColors.BRIGHT_CYAN
    COUNT: Final[str] = ConsoleColors.BRIGHT_GREEN
    COUNT_TOTAL: Final[str] = ConsoleColors.BRIGHT_YELLOW
    FILE_NAME: Final[str] = ConsoleColors.BRIGHT_MAGENTA


@final
class PySplit(CLIProgram):
    """
    A program to split lines into fields.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="pyspl", version="1.2.1")

        self.DEFAULT_PATTERN: Final[str] = r"\s+"  # All whitespace.
        self.field_index_end: int = 0
        self.field_index_start: int = 0
        self.pattern: str = ""
        self.quote: str = ""
        self.separator: str = ""

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="split lines in FILES into fields",
                                         epilog="with no FILES, read standard input", prog=self.NAME)
        quote_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="files to split", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("-c", "--count", action="store_true", help="prefix output with field count")
        quote_group.add_argument("-D", "--double-quote", action="store_true", help="print double quotes around fields")
        quote_group.add_argument("-S", "--single-quote", action="store_true", help="print single quotes around fields")
        parser.add_argument("-f", "--field-start", help="print at field N+", metavar="N+", type=int)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-n", "--fields", help="print only N+ fields", metavar="N+", type=int)
        parser.add_argument("-p", "--pattern", help="split lines into fields using PATTERN", nargs=1)
        parser.add_argument("-s", "--separator", help="separate each field with α", metavar="α", nargs=1)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display the counts and file headers in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--total", choices=("auto", "on", "off"), default="auto",
                            help="print a line with total count")
        parser.add_argument("--pipe", action="store_true", help="read FILES from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_field_info_values()

        # Set --no-file-header to True if there are no files and --pipe=False.
        if not self.args.files and not self.args.pipe:
            self.args.no_file_header = True

        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
                self.split_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.split_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.split_lines_from_files(self.args.files)
        elif self.args.files:
            self.split_lines_from_files(self.args.files)
        else:
            self.split_lines_from_input()

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

    def set_field_info_values(self) -> None:
        """
        Sets the values to use for separating lines.
        :return: None
        """
        field_start = 1 if not self.args.field_start else self.args.field_start  # --field-start
        fields = sys.maxsize if not self.args.fields else self.args.fields  # --fields

        # Validate the field values.
        if field_start < 1:
            self.log_error(f"field start ({field_start}) cannot be less than 1", raise_system_exit=True)

        if fields < 1:
            self.log_error(f"fields ({fields}) cannot be less than 1", raise_system_exit=True)

        # Store the field values.
        self.field_index_end = field_start - 1 + fields
        self.field_index_start = field_start - 1
        self.pattern = self.DEFAULT_PATTERN if not self.args.pattern else self.args.pattern[0]  # --pattern
        self.quote = "\"" if self.args.double_quote else "'" if self.args.single_quote else ""  # --double-quote or --single-quote
        self.separator = "\t" if not self.args.separator else self.args.separator[0]  # --separator

    def split_line(self, line: str, field_pattern: str) -> list[str]:
        """
        Splits the line into a list of fields.
        :param line: The line.
        :param field_pattern: The pattern for splitting fields.
        :return: A list of fields.
        """
        fields = []

        # Strip leading and trailing whitespace.
        line = line.strip()

        # Split line into fields.
        try:
            for field in re.split(field_pattern, line):
                if field:
                    fields.append(field)
        except re.error:
            self.log_error(f"invalid regex pattern: {field_pattern}", raise_system_exit=True)

        return fields[self.field_index_start:self.field_index_end]

    def split_lines(self, lines: TextIO | list[str]) -> None:
        """
        Splits the lines into fields.
        :param lines: The lines.
        :return: None
        """
        count_total = 0

        for line in lines:
            fields = self.split_line(line, self.pattern)

            if self.args.no_blank and not fields:  # --no-blank
                continue

            # Get the counts.
            count = len(fields)
            count_total += count

            if self.args.count:  # --count
                count_width = 5

                if self.print_color:
                    count_str = f"{Colors.COUNT}{count:>{count_width}}{Colors.COLON}:{ConsoleColors.RESET}"
                else:
                    count_str = f"{count:>{count_width}}:"

                print(count_str, end="")

            for index, field in enumerate(fields):
                print_end = self.separator if index < len(fields) - 1 else ""

                print(f"{self.quote}{field}{self.quote}", end=print_end)

            print()

        if self.args.total == "on" or (self.args.total == "auto" and self.args.count):  # --total
            count_width = 5 if self.args.count else 0  # --count

            if self.print_color:
                count_str = f"{Colors.COUNT_TOTAL}{count_total:>{count_width}}{Colors.COLON}:{ConsoleColors.RESET}total"
            else:
                count_str = f"{count_total:>{count_width}}:total"

            print(count_str)

    def split_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Splits lines into fields from files.
        :param files: The files.
        :return: None
        """
        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.print_file_header(file)
                self.split_lines(text)
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

    def split_lines_from_input(self) -> None:
        """
        Splits lines into fields from standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(input())
            except EOFError:
                eof = True

        self.split_lines(lines)


if __name__ == "__main__":
    CLIProgram.run(PySplit())
