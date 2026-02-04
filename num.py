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
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, Final, final, override

from cli import CLIProgram, ansi, io, terminal


@dataclass(frozen=True, slots=True)
class Colors:
    """
    Namespace for terminal color constants.

    :cvar COLON: Color used for the colon following a file name.
    :cvar FILE_NAME: Color used for a file name.
    :cvar LINE_NUMBER: Color used for line numbers and number separators.
    """
    COLON: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_CYAN
    FILE_NAME: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_MAGENTA
    LINE_NUMBER: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_GREEN


@final
class Num(CLIProgram):
    """
    A program to number output lines from files to standard output.

    :cvar FORMAT_PREFIXES: Mapping of short format keys to format-spec prefixes used when formatting line numbers.
    :ivar format_prefix: Format-spec prefix used when formatting line numbers.
    """

    FORMAT_PREFIXES: Final[dict[str, str]] = {
        "ln": "<",  # Left-aligned
        "rn": ">",  # Right-aligned
        "rz": "0>",  # Zero-padded, right-aligned
    }

    def __init__(self) -> None:
        """
        Initialize a new ``Num`` instance.
        """
        super().__init__(name="num", version="1.3.10")

        self.format_prefix: str = ""

    @override
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
                            help="use color for file names, line numbers, and number separators (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress all blank lines")
        blank_group.add_argument("--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        parser.add_argument("--number-format", choices=("ln", "rn", "rz"), default="rn",
                            help="format line numbers (ln=left, rn=right, rz=zero-padded; default: rn)")
        parser.add_argument("--number-separator", default="\t",
                            help="separate line numbers and output lines with SEP (default: <tab>)", metavar="SEP")
        parser.add_argument("--number-start", default=1, help="start numbering at N (default: 1; N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """
        Validate parsed command-line arguments.
        """
        self.format_prefix = Num.FORMAT_PREFIXES[self.args.number_format]  # --number-format

        if self.args.number_start < 0:  # --number-start
            self.print_error_and_exit("'--number-start' must be >= 0")

        if self.args.number_width < 1:  # --number-width
            self.print_error_and_exit("'number-width' must be >= 1")

    @override
    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.number_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.number_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.number_lines_from_files(self.args.files)
        elif self.args.files:
            self.number_lines_from_files(self.args.files)
        else:
            self.number_lines_from_input()

    def number_lines(self, lines: Iterable[str]) -> None:
        """
        Number and print lines to standard output according to command-line arguments.

        :param lines: Iterable of lines to print.
        """
        blank_line_count = 0
        line_number = self.args.number_start - 1  # --number-start

        for line in lines:
            print_number = True

            if line == "\n":  # Blank line?
                blank_line_count += 1

                if self.should_skip_line(blank_line_count):
                    continue

                if self.args.number_nonblank:  # --number-nonblank
                    print_number = False
            else:
                blank_line_count = 0

            if print_number:
                line_number += 1
                line = self.render_line_number(line, line_number)

            io.print_line_normalized(line)

    def number_lines_from_files(self, files: Iterable[str]) -> None:
        """
        Read lines from each file, then number and print them.

        :param files: Iterable of files to read.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.number_lines(file_info.text)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def number_lines_from_input(self) -> None:
        """
        Read lines from standard input until EOF, then number and print them.
        """
        self.number_lines(sys.stdin)

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name or "(standard input)" if empty, followed by a colon, unless ``--no-file-name`` is set.

        :param file_name: File name to print.
        """
        if not self.args.no_file_name:  # --no-file-name
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def render_line_number(self, line: str, line_number: int) -> str:
        """
        Prefix a formatted line number to the line.

        :param line: Line to format.
        :param line_number: Current line number.
        :return: The line prefixed with a line number.
        """
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:{self.format_prefix}{self.args.number_width}}{self.args.number_separator}{ansi.RESET}{line}"

        return f"{line_number:{self.format_prefix}{self.args.number_width}}{self.args.number_separator}{line}"

    def should_skip_line(self, blank_line_count: int) -> bool:
        """
        Determine whether the current line should be suppressed based on blank-line handling options.

        :param blank_line_count: Number of consecutive blank lines encountered so far, including the current line.
        :return: Return ``True`` if the current blank line should be skipped.
        """
        if self.args.no_blank and blank_line_count:  # --no-blank
            return True

        if self.args.squeeze_blank and blank_line_count > 1:  # --squeeze-blank
            return True

        return False


if __name__ == "__main__":
    Num().run()
