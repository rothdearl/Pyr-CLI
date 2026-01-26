#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: slice.py
Author: Roth Earl
Version: 1.3.5
Description: A program to slice lines in files into shell-style fields.
License: GNU GPLv3
"""

import argparse
import os
import shlex
import sys
from collections.abc import Iterable
from enum import StrEnum
from typing import TextIO, final

from cli import CLIProgram, colors, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = colors.BRIGHT_CYAN
    COUNT = colors.BRIGHT_GREEN
    COUNT_TOTAL = colors.BRIGHT_YELLOW
    FILE_NAME = colors.BRIGHT_MAGENTA


@final
class Slice(CLIProgram):
    """
    A program to slice lines in files into shell-style fields.

    :ivar list[int] fields_to_print: Fields to print.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="slice", version="1.3.5")

        self.fields_to_print: list[int] = []

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="slice lines in FILES into shell-style fields",
                                         epilog="with no FILES, read standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-s", "--separator", help="use SEP to separate output fields (default: tab)", metavar="SEP")
        parser.add_argument("-u", "--unique", action="store_true",
                            help="print each field only once, in ascending order")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="colorize counts and file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--literal-quotes", action="store_true",
                            help="treat quotes as ordinary characters (disable shell-style quote parsing)")
        parser.add_argument("--print", action="extend",
                            help="print only the specified fields (1-based indices; duplicates allowed)", metavar="N",
                            nargs='+', type=int)
        parser.add_argument("--quotes", choices=("d", "s"),
                            help="wrap fields in double (d) or single (s) quotes (default: none)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def main(self) -> None:
        """
        Runs the primary function of the program.
        """
        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_sliced_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.print_sliced_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.print_sliced_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_sliced_lines_from_files(self.args.files)
        else:
            self.print_sliced_lines_from_input()

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.

        :param file: File header to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            filename = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                filename = f"{Colors.FILE_NAME}{filename}{Colors.COLON}:{colors.RESET}"
            else:
                filename = f"{filename}:"

            print(filename)

    def print_sliced_lines(self, lines: Iterable[str] | TextIO) -> None:
        """
        Prints the sliced the lines.

        :param lines: Lines to slice.
        """
        quote = "\"" if self.args.quotes == "d" else "'" if self.args.quotes == "s" else ""  # --quotes
        separator = self.args.separator if self.args.separator is not None else "\t"  # --separator

        for line in lines:
            fields = self.slice_line(line)

            # Do not print blank lines when there are no fields to print.
            if not fields:
                continue

            print(separator.join(f"{quote}{field}{quote}" for field in fields))

    def print_sliced_lines_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Slices lines into fields from files.

        :param files: Files to slice lines from.
        """
        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.filename)
                self.print_sliced_lines(file_info.text)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def print_sliced_lines_from_input(self) -> None:
        """
        Slices lines into fields from standard input until EOF is entered.
        """
        self.print_sliced_lines(sys.stdin.read().splitlines())

    def slice_line(self, line: str) -> list[str]:
        """
        Slices the line into fields.

        :param line: Line to slice.
        :return: A list of fields.
        """
        lexer = shlex.shlex(line, posix=True, punctuation_chars=False)

        # Configure the lexer.
        lexer.whitespace_split = True  # Treat whitespace as the token separator.

        if self.args.literal_quotes:  # --literal-quotes
            lexer.quotes = ""  # Disables quotes.

        # Parse the fields.
        try:
            fields = list(lexer)
        except ValueError:
            # Likely a "No closing quotation" error; strip the line and add it as a single field.
            fields = [line.lstrip().rstrip()]

        # If --print, collect just the specified fields.
        if self.fields_to_print:
            max_fields = len(fields)

            fields = [fields[i] for i in self.fields_to_print if i < max_fields]

        return fields

    def validate_parsed_arguments(self) -> None:
        """
        Validates the parsed command-line arguments.
        """
        self.fields_to_print = self.args.print or []  # --print

        # Validate --print values.
        for field in self.fields_to_print:
            if field < 1:
                self.print_error_and_exit("'print' must contain fields >= 1")

        if self.args.unique:  # --unique
            self.fields_to_print = sorted(set(self.fields_to_print))

        # Convert one-based input to zero-based.
        self.fields_to_print = [i - 1 for i in self.fields_to_print]


if __name__ == "__main__":
    CLIProgram.run(Slice())
