#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: peek.py
Author: Roth Earl
Version: 1.3.0
Description: A program to print the first part of files.
License: GNU GPLv3
"""

import argparse
import os
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = ConsoleColors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ConsoleColors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ConsoleColors.BRIGHT_GREEN


@final
class Peek(CLIProgram):
    """
    A program to print the first part of files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="peek", version="1.3.0")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds and returns an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the first part of FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to print", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-n", "--lines", help="print the first or all but the last n lines", metavar="±n", type=int)
        parser.add_argument("-N", "--line-number", action="store_true", help="print line number with output lines")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display the file headers in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--pipe", action="store_true", help="read input from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        # Set --no-file-header to True if there are no files and --pipe=False.
        if not self.args.files and not self.args.pipe:
            self.args.no_file_header = True

        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
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
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ConsoleColors.RESET}"
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
        lines_to_print = 10 if not self.args.lines else self.args.lines  # --lines

        # Print all but the last 'n' lines.
        if lines_to_print < 0:
            lines_to_print = len(lines) + lines_to_print

        for line in lines:
            line_number += 1

            if line_number <= lines_to_print:
                if self.args.line_number:  # --line-number
                    width = 7

                    if self.print_color:
                        line = f"{Colors.LINE_NUMBER}{line_number:>{width}}{Colors.COLON}:{ConsoleColors.RESET}{line}"
                    else:
                        line = f"{line_number:>{width}}:{line}"

                CLIProgram.print_line(line)
            else:
                break

    def print_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Prints lines from files.
        :param files: The files.
        :return: None
        """
        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.print_file_header(file=file)
                self.print_lines(text.readlines())
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

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


if __name__ == "__main__":
    CLIProgram.run(Peek())
