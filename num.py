#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: num.py
Author: Roth Earl
Version: 1.3.10
Description: A program to number output lines from files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections.abc import Collection, Iterable
from enum import StrEnum
from typing import final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.Colors16.BRIGHT_CYAN
    FILE_NAME = ansi.Colors16.BRIGHT_MAGENTA
    LINE_NUMBER = ansi.Colors16.BRIGHT_GREEN


@final
class Num(CLIProgram):
    """
    A program to number output lines from files to standard output.
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Num`` instance.
        """
        super().__init__(name="num", version="1.3.10")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="number output lines from FILES to standard output",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)
        blank_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--number-nonblank", action="store_true", help="number nonblank output lines")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="do not prefix output with file names")
        parser.add_argument("-w", "--number-width", default=6, help="pad line numbers to width N (default: 6; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names and line numbers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress all blank lines")
        blank_group.add_argument("--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        parser.add_argument("--number-format", choices=("ln", "rn", "rz"), default="rn",
                            help="format line numbers (ln=left, rn=right, rz=zero-padded; default: rn)")
        parser.add_argument("--number-separator", default="\t",
                            help="separate line numbers and output lines with SEP (default: <tab>)", metavar="SEP")
        parser.add_argument("--starting-number", default=1, help="start numbering at N (default: 1; N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name, or "(standard input)" if empty, with a colon.

        :param file_name: File name to print.
        """
        if not self.args.no_file_name:  # --no-file-name
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_lines(self, lines: Iterable[str]) -> None:
        """
        Print lines using formatting specified by command-line arguments.

        :param lines: Lines to print.
        """
        line_number = self.args.starting_number - 1  # --starting-line-number
        number_format = {"ln": "<", "rn": ">", "rz": "0>"}[self.args.number_format]  # --number-format
        repeated_blank_lines = 0

        for line in lines:
            print_number = True

            if line == "\n":  # Blank line?
                repeated_blank_lines += 1

                if self.args.number_nonblank:  # --number-nonblank
                    print_number = False

                if self.args.no_blank:  # --no-blank
                    continue

                if self.args.squeeze_blank and repeated_blank_lines > 1:  # --squeeze-blank
                    continue
            else:
                repeated_blank_lines = 0

            if print_number:
                line_number += 1

                if self.print_color:
                    line = f"{Colors.LINE_NUMBER}{line_number:{number_format}{self.args.number_width}}{ansi.RESET}{self.args.number_separator}{line}"
                else:
                    line = f"{line_number:{number_format}{self.args.number_width}}{self.args.number_separator}{line}"

            io.print_line_normalized(line)

    def print_lines_from_files(self, files: Collection[str]) -> None:
        """
        Print lines from files using formatting specified by command-line arguments.

        :param files: Files to print lines from.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.print_lines(file_info.text)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Print lines from standard input until EOF using formatting specified by command-line arguments.
        """
        self.print_lines(sys.stdin.read().splitlines())

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        if self.args.number_width < 1:  # --number-width
            self.print_error_and_exit("'number-width' must be >= 1")

        if self.args.starting_number < 0:  # --starting-number
            self.print_error_and_exit("'--starting-number' must be >= 0")


if __name__ == "__main__":
    Num().run()
