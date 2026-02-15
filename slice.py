#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that splits lines in files into fields."""

import argparse
import os
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Slice(CLIProgram):
    """
    A program that splits lines in files into fields.

    :ivar fields_to_print: Fields to print.
    """

    def __init__(self) -> None:
        """Initialize a new ``Slice`` instance."""
        super().__init__(name="slice", version="1.3.16")

        self.fields_to_print: list[int] = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="split lines in FILES into fields",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        mode_modifiers = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-m", "--mode", choices=("csv", "regex", "shell"), default="csv",
                            help="set field parsing mode (default: csv)")
        mode_modifiers.add_argument("--field-pattern", help="split fields using PATTERN (use with --mode regex)",
                                    metavar="PATTERN")
        mode_modifiers.add_argument("--field-separator", default=" ",
                                    help="split fields using SEP (default: <space>; use with --mode csv)",
                                    metavar="SEP")
        mode_modifiers.add_argument("--literal-quotes", action="store_true",
                                    help="treat quotes as ordinary characters (use with --mode shell)")
        parser.add_argument("-s", "--separator", default="\t", help="separate output fields with SEP (default: <tab>)",
                            metavar="SEP")
        parser.add_argument("-u", "--unique", action="store_true",
                            help="normalize field selection to unique field numbers in ascending order (overrides --fields)")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--fields", action="extend",
                            help="print only the specified fields (numbered from 1; order preserved; duplicates allowed)",
                            metavar="N", nargs="+", type=int)
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--quotes", choices=("d", "s"), help="wrap fields in double (d) or single (s) quotes")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        self.fields_to_print = self.args.fields or []  # --fields

        # Validate --fields values.
        for field in self.fields_to_print:
            if field < 1:
                self.print_error_and_exit("--fields must contain fields >= 1")

        if self.args.unique:  # --unique
            self.fields_to_print = sorted(set(self.fields_to_print))

        # Convert one-based input to zero-based.
        self.fields_to_print = [i - 1 for i in self.fields_to_print]

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.split_and_print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.split_and_print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.split_and_print_lines_from_files(self.args.files)
        elif self.args.files:
            self.split_and_print_lines_from_files(self.args.files)
        else:
            self.split_and_print_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def split_and_print_lines(self, lines: Iterable[str]) -> None:
        """Split lines into fields and print."""
        quote = '"' if self.args.quotes == "d" else "'" if self.args.quotes == "s" else ""  # --quotes
        separator = self.args.separator  # --separator

        for line in lines:
            fields = self.split_line(line)

            # Do not print blank lines when there are no fields to print.
            if not fields:
                continue

            print(separator.join(f"{quote}{field}{quote}" for field in fields))

    def split_and_print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read, split, and print lines from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.split_and_print_lines(file_info.text_stream)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def split_and_print_lines_from_input(self) -> None:
        """Read, split, and print lines from standard input until EOF."""
        self.split_and_print_lines(sys.stdin)

    def split_line(self, line: str) -> list[str]:
        """Split the line into fields."""
        fields = text.split_shell_style(line, literal_quotes=self.args.literal_quotes)  # --literal-quotes

        # If --print, return just the specified fields.
        if self.fields_to_print:
            return [fields[index] for index in self.fields_to_print if index < len(fields)]

        return fields


if __name__ == "__main__":
    Slice().run()
