#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: glue.py
Author: Roth Earl
Version: 1.3.10
Description: A program to concatenate files and standard input to standard output.
License: GNU GPLv3
"""

import argparse
import sys
from collections.abc import Collection, Iterable
from enum import StrEnum
from typing import final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    EOL = ansi.Colors16.BRIGHT_BLUE
    NUMBER = ansi.Colors16.BRIGHT_GREEN
    TABS = ansi.Colors16.BRIGHT_CYAN


class Whitespace(StrEnum):
    """
    Whitespace replacement constants.
    """
    EOL = "$"
    TAB = ">···"


@final
class Glue(CLIProgram):
    """
    A program to concatenate files and standard input to standard output.

    :ivar line_number: Line number to be printed with output lines.
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Glue`` instance.
        """
        super().__init__(name="glue", version="1.3.10")

        self.line_number: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="concatenate FILES and standard input to standard output",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)
        blank_group = parser.add_mutually_exclusive_group()
        number_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        number_group.add_argument("-b", "--number-nonblank", action="store_true", help="number nonblank output lines")
        number_group.add_argument("-n", "--number", action="store_true", help="number output lines")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress all blank lines")
        blank_group.add_argument("-s", "--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        parser.add_argument("-E", "--show-ends", action="store_true",
                            help=f"display '{Whitespace.EOL}' at end of each line")
        parser.add_argument("-T", "--show-tabs", action="store_true",
                            help=f"display tab characters as '{Whitespace.TAB}'")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for numbers and whitespace (default: on)")
        parser.add_argument("--group", action="store_true", help="separate FILES with a blank line")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--number-width", default=6, help="pad line numbers to width N (default: 6; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def main(self) -> None:
        """
        Run the program logic.
        """
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_lines_from_files(sys.stdin.readlines())
            else:
                self.print_lines(sys.stdin)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_lines(self, lines: Iterable[str]) -> None:
        """
        Print lines using formatting specified by command-line arguments.

        :param lines: Lines to print.
        """
        print_number = False
        repeated_blank_lines = 0

        for line in lines:
            if self.args.number or self.args.number_nonblank:  # --number or --number-nonblank
                print_number = True

            if line == "\n":  # Blank line?
                repeated_blank_lines += 1

                if self.args.number_nonblank:  # --number-nonblank
                    print_number = False

                if self.args.no_blank and repeated_blank_lines:  # --no-blank
                    continue

                if self.args.squeeze_blank and repeated_blank_lines > 1:  # --squeeze-blank
                    continue
            else:
                repeated_blank_lines = 0

            if self.args.show_tabs:  # --show-tabs
                if self.print_color:
                    line = line.replace("\t", f"{Colors.TABS}{Whitespace.TAB}{ansi.RESET}")
                else:
                    line = line.replace("\t", Whitespace.TAB)

            if self.args.show_ends:  # --show-ends
                end_index = -1 if line.endswith("\n") else len(line)
                newline = "\n" if end_index == -1 else ""

                if self.print_color:
                    line = f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{ansi.RESET}{newline}"
                else:
                    line = f"{line[:end_index]}{Whitespace.EOL}{newline}"

            if print_number:
                self.line_number += 1

                if self.print_color:
                    line = f"{Colors.NUMBER}{self.line_number:>{self.args.number_width}}{ansi.RESET} {line}"
                else:
                    line = f"{self.line_number:>{self.args.number_width}} {line}"

            io.print_line_normalized(line)

    def print_lines_from_files(self, files: Collection[str]) -> None:
        """
        Print lines from files using formatting specified by command-line arguments.

        :param files: Files to print lines from.
        """
        last_file_index = len(files) - 1

        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_lines(file_info.text)

                if self.args.group and file_info.file_index < last_file_index:  # --group
                    print()
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Print lines from standard input until EOF using formatting specified by command-line arguments.
        """
        eof = False

        while not eof:
            try:
                self.print_lines([input()])
            except EOFError:
                eof = True

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        if self.args.number_width < 1:  # --number-width
            self.print_error_and_exit("'number-width' must be >= 1")


if __name__ == "__main__":
    Glue().run()
