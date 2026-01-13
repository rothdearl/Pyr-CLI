#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: show.py
Author: Roth Earl
Version: 1.3.3
Description: A program to print files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, colors, io, terminal


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = colors.BRIGHT_CYAN
    EOL: Final[str] = colors.BRIGHT_BLUE
    FILE_NAME: Final[str] = colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = colors.BRIGHT_GREEN
    WHITESPACE: Final[str] = colors.BRIGHT_CYAN


@final
class Show(CLIProgram):
    """
    A program to print files to standard output.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="show", version="1.3.3")

        self.line_start: int = 0
        self.lines: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to print", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-l", "--lines", help="print only N lines", metavar="N+", type=int)
        parser.add_argument("-n", "--line-number", action="store_true", help="print line number with output lines")
        parser.add_argument("-s", "--line-start", help="print at line n from the head or tail", metavar="±n", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display file names, whitespace and line numbers in color")
        parser.add_argument("--ends", action="store_true", help=f"display {Whitespace.EOL} at end of each line")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 instead of utf-8")
        parser.add_argument("--spaces", action="store_true", help=f"display spaces as {Whitespace.SPACE}")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input as arguments")
        parser.add_argument("--tabs", action="store_true", help=f"display tab characters as {Whitespace.TAB}")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_line_info_values()

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
            file_name = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{colors.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_lines(self, lines: list[str]) -> None:
        """
        Prints the lines.
        :param lines: The lines.
        :return: None
        """
        line_number = 0
        line_start = len(lines) + self.line_start + 1 if self.line_start < 0 else self.line_start
        line_end = line_start + self.lines - 1

        for line in lines:
            line_number += 1

            if line_start <= line_number <= line_end:
                if self.args.spaces:  # --spaces
                    if self.print_color:
                        line = line.replace(" ", f"{Colors.WHITESPACE}{Whitespace.SPACE}{colors.RESET}")
                    else:
                        line = line.replace(" ", Whitespace.SPACE)

                if self.args.tabs:  # --tabs
                    if self.print_color:
                        line = line.replace("\t", f"{Colors.WHITESPACE}{Whitespace.TAB}{colors.RESET}")
                    else:
                        line = line.replace("\t", Whitespace.TAB)

                if self.args.ends:  # --ends
                    end_index = -1 if line.endswith("\n") else len(line)
                    newline = "\n" if end_index == -1 else ""

                    if self.print_color:
                        line = f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{colors.RESET}{newline}"
                    else:
                        line = f"{line[:end_index]}{Whitespace.EOL}{newline}"

                if self.args.line_number:  # --line-number
                    width = 7

                    if self.print_color:
                        line = f"{Colors.LINE_NUMBER}{line_number:>{width}}{Colors.COLON}:{colors.RESET}{line}"
                    else:
                        line = f"{line_number:>{width}}:{line}"

                io.print_line(line)

    def print_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Prints lines from files.
        :param files: The files.
        :return: None
        """
        for _, file, text in io.read_files(self, files, self.encoding):
            try:
                self.print_file_header(file)
                self.print_lines(text.readlines())
            except UnicodeDecodeError:
                self.print_file_error(f"{file}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Prints lines from standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(input())
            except EOFError:
                eof = True

        self.print_lines(lines)

    def set_line_info_values(self) -> None:
        """
        Sets the values to use for printing lines.
        :return: None
        """
        self.line_start = self.args.line_start if self.args.line_start else 1  # --line-start
        self.lines = self.args.lines if self.args.lines else sys.maxsize  # --lines

        # Validate the line values.
        if self.line_start == 0:
            self.print_error(f"line start ({self.line_start}) cannot be 0", raise_system_exit=True)

        if self.lines < 1:
            self.print_error(f"lines ({self.lines}) cannot be less than 1", raise_system_exit=True)


@final
class Whitespace:
    """
    Class for managing whitespace constants.
    """
    EOL: Final[str] = "$"
    SPACE: Final[str] = "~"
    TAB: Final[str] = ">···"


if __name__ == "__main__":
    Show().run()
