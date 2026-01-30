#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: peek.py
Author: Roth Earl
Version: 1.3.7
Description: A program to print the first part of files.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections import deque
from collections.abc import Iterable
from enum import StrEnum
from typing import TextIO, final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.BRIGHT_CYAN
    FILE_NAME = ansi.BRIGHT_MAGENTA


@final
class Peek(CLIProgram):
    """
    A program to print the first part of files.
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Peek`` instance.
        """
        super().__init__(name="peek", version="1.3.7")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the first part of FILES",
                                         epilog="if no FILES are specified, read standard input", prog=self.name)

        parser.add_argument("files", help="one or more input files", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true", help="do not prepend file names to output")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the first N lines (N >= 1), or all but the last N if negative (default: 10)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
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
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_lines(self, lines: Iterable[str] | TextIO) -> None:
        """
        Print the lines.

        :param lines: Lines to print.
        """
        # If --lines is positive or zero: print the first N lines.
        if self.args.lines >= 0:
            for index, line in enumerate(lines):
                if index >= self.args.lines:
                    break

                io.print_normalized_line(line)

            return

        # --lines is negative: print all but last |N| lines
        buffer = deque(maxlen=-self.args.lines)

        for line in lines:
            if len(buffer) == buffer.maxlen:
                io.print_normalized_line(buffer.popleft())

            buffer.append(line)

    def print_lines_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Print lines from the files.

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
        Print lines from standard input until EOF is entered.
        """
        self.print_lines(sys.stdin.read().splitlines())

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        pass


if __name__ == "__main__":
    Peek().run()
