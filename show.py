#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: show.py
Author: Roth Earl
Version: 1.3.5
Description: A program to print files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections.abc import Collection, Iterable
from enum import StrEnum
from typing import TextIO, final

from cli import CLIProgram, colors, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = colors.BRIGHT_CYAN
    EOL = colors.BRIGHT_BLUE
    FILE_NAME = colors.BRIGHT_MAGENTA
    LINE_NUMBER = colors.BRIGHT_GREEN
    SPACE = colors.BRIGHT_CYAN
    TAB = colors.BRIGHT_CYAN


class Whitespace(StrEnum):
    """
    Whitespace replacement constants.
    """
    EOL = "$"
    SPACE = "·"
    TAB = ">···"
    TRAILING_SPACE = "~"


@final
class Show(CLIProgram):
    """
    A program to print files to standard output.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="show", version="1.3.5")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="with no FILES, read standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-n", "--line-numbers", action="store_true", help="print line numbers with output lines")
        parser.add_argument("-p", "--print", default=sys.maxsize, help="print only N lines (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-s", "--start", default=1, help="start at line N, from end if negative (N != 0)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="colorize file names, whitespace, and line numbers (default: on)")
        parser.add_argument("--ends", action="store_true", help=f"display '{Whitespace.EOL}' at end of each line")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--spaces", action="store_true",
                            help=f"display spaces as '{Whitespace.SPACE}' and trailing spaces as '{Whitespace.TRAILING_SPACE}'")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--tabs", action="store_true", help=f"display tab characters as '{Whitespace.TAB}'")
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

        :param file: File header to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            filename = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                filename = f"{Colors.FILE_NAME}{filename}{Colors.COLON}:{colors.RESET}"
            else:
                filename = f"{filename}:"

            print(filename)

    def print_lines(self, lines: Collection[str]) -> None:
        """
        Prints the lines.

        :param lines: Lines to print.
        """
        line_start = len(lines) + self.args.start + 1 if self.args.start < 0 else self.args.start
        line_end = line_start + self.args.print - 1
        line_min = min(self.args.print, len(lines)) if self.args.print else len(lines)
        padding = len(str(line_min))

        for index, line in enumerate(lines, start=1):
            if line_start <= index <= line_end:
                line = self.show_spaces(line) if self.args.spaces else line  # --spaces
                line = self.show_tabs(line) if self.args.tabs else line  # --tabs
                line = self.show_ends(line) if self.args.ends else line  # --ends
                line = self.show_line_number(line, index, padding) if self.args.line_numbers else line  # --line-numbers
                io.print_line(line)

    def print_lines_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Prints lines from files.

        :param files: Files to print lines from.
        """
        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.filename)
                self.print_lines(file_info.text.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Prints lines from standard input until EOF is entered.
        """
        self.print_lines(sys.stdin.read().splitlines())

    def show_ends(self, line: str) -> str:
        """
        Appends the EOL character to the end of the line.

        :param line: Line to append.
        :return: The line.
        """
        end_index = -1 if line.endswith("\n") else len(line)
        newline = "\n" if end_index == -1 else ""

        if self.print_color:
            return f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{colors.RESET}{newline}"

        return f"{line[:end_index]}{Whitespace.EOL}{newline}"

    def show_line_number(self, line: str, line_number: int, padding: int) -> str:
        """
        Prepends the line with the line number.

        :param line: Line to prepend.
        :param line_number: Line number.
        :param padding: Line number padding.
        :return: The line.
        """
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}:{colors.RESET}{line}"

        return f"{line_number:>{padding}}:{line}"

    def show_spaces(self, line: str) -> str:
        """
        Replaces spaces with Whitespace.SPACE or Whitespace.TRAILING_SPACE in the line.

        :param line: Line to replace spaces.
        :return: The line.
        """
        has_newline = line.endswith("\n")
        trailing_count = len(line) - len(line.rstrip())  # Count trailing spaces.

        # Truncate trailing spaces.
        line = line[:-trailing_count] if trailing_count else line

        if has_newline:
            trailing_count -= 1

        if self.print_color:
            line = line.replace(" ", f"{Colors.SPACE}{Whitespace.SPACE}{colors.RESET}")
            line = line + Colors.SPACE + (Whitespace.TRAILING_SPACE * trailing_count) + colors.RESET
        else:
            line = line.replace(" ", Whitespace.SPACE)
            line = line + (Whitespace.TRAILING_SPACE * trailing_count)

        return line + "\n" if has_newline else line

    def show_tabs(self, line: str) -> str:
        """
        Replaces tabs with Whitespace.TAB in the line.

        :param line: Line to replace tabs.
        :return: The line.
        """
        if self.print_color:
            return line.replace("\t", f"{Colors.TAB}{Whitespace.TAB}{colors.RESET}")

        return line.replace("\t", Whitespace.TAB)

    def validate_parsed_arguments(self) -> None:
        """
        Validates the parsed command-line arguments.
        """
        if self.args.print < 1:  # --print
            self.print_error_and_exit("'print' must be >= 1")

        if self.args.start == 0:  # --start
            self.print_error_and_exit("'start' cannot = 0")


if __name__ == "__main__":
    Show().run()
