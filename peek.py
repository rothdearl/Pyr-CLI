#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: peek.py
Author: Roth Earl
Version: 1.3.4
Description: A program to print the first part of files.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections import deque
from enum import StrEnum
from typing import Iterable, TextIO, final

from cli import CLIProgram, colors, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = colors.BRIGHT_CYAN
    FILE_NAME = colors.BRIGHT_MAGENTA


@final
class Peek(CLIProgram):
    """
    A program to print the first part of files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="peek", version="1.3.4")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds and returns an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the first part of FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the first N lines, or all but the last N if negative (default: 10)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on", help="colorize file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.
        :param file: The file.
        :return: None
        """
        if not self.args.no_file_header:  # --no-file-header
            filename = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                filename = f"{Colors.FILE_NAME}{filename}{Colors.COLON}:{colors.RESET}"
            else:
                filename = f"{filename}:"

            print(filename)

    def print_lines(self, lines: Iterable[str] | TextIO) -> None:
        """
        Prints the lines.
        :param lines: The lines.
        :return: None
        """
        # If --lines is positive or zero: print the first N lines.
        if self.args.lines >= 0:
            for index, line in enumerate(lines):
                if index >= self.args.lines:
                    break

                io.print_line(line)

            return

        # --lines is negative: print all but last |N| lines
        buffer = deque(maxlen=-self.args.lines)

        for line in lines:
            if len(buffer) == buffer.maxlen:
                io.print_line(buffer.popleft())

            buffer.append(line)

    def print_lines_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Prints lines from files.
        :param files: The files.
        :return: None
        """
        for file_info in io.read_files(files, self.encoding, reporter=self):
            try:
                self.print_file_header(file=file_info.filename)
                self.print_lines(file_info.text)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Prints lines from standard input until EOF is entered.
        :return: None
        """
        self.print_lines(sys.stdin.read().splitlines())

    def validate_parsed_arguments(self) -> None:
        """
        Validates the parsed command-line arguments.
        :return: None
        """
        pass


if __name__ == "__main__":
    Peek().run()
