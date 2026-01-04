#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: concat.py
Author: Roth Earl
Version: 1.3.0
Description: A program to concatenate files to standard output.
License: GNU GPLv3
"""

import argparse
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    EOL: Final[str] = ConsoleColors.BRIGHT_BLUE
    NUMBER: Final[str] = ConsoleColors.BRIGHT_GREEN
    WHITESPACE: Final[str] = ConsoleColors.BRIGHT_CYAN


@final
class Main(CLIProgram):
    """
    A program to concatenate files to standard output.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="concat", version="1.3.0")

        self.number: int = 0
        self.repeated_blank_lines: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="concatenate FILES to standard output",
                                         epilog="with no FILES, read standard input", prog=self.NAME)
        blank = parser.add_mutually_exclusive_group()
        number = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="files to concatenate", metavar="FILES", nargs="*")
        number.add_argument("-b", "--number-nonblank", action="store_true", help="number nonblank output lines")
        number.add_argument("-n", "--number", action="store_true", help="number all output lines")
        blank.add_argument("-B", "--no-blank", action="store_true", help="suppress blank lines")
        blank.add_argument("-s", "--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        parser.add_argument("-E", "--show-ends", action="store_true",
                            help=f"display {Whitespace.EOL} at end of each line")
        parser.add_argument("-g", "--group", action="store_true", help="separate files with an empty line")
        parser.add_argument("-S", "--spaces", action="store_true", help=f"display spaces as {Whitespace.SPACE}")
        parser.add_argument("-T", "--tabs", action="store_true", help=f"display tab characters as {Whitespace.TAB}")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display the spaces, tabs, end of line and numbers in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--pipe", action="store_true", help="read input from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
                self.print_lines_from_files(sys.stdin.readlines())
            else:
                self.print_lines(sys.stdin)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_lines(self, lines: TextIO | list[str]) -> None:
        """
        Prints the lines.
        :param lines: The lines.
        :return: None
        """
        print_number = False

        for line in lines:
            self.number += 1

            if self.args.number or self.args.number_nonblank:  # --number or --number-nonblank
                print_number = True

            if not line or line == "\n":
                self.repeated_blank_lines += 1

                if self.args.number_nonblank:  # --number-nonblank
                    self.number -= 1
                    print_number = False

                if self.args.no_blank and self.repeated_blank_lines:  # --no-blank
                    continue

                if self.args.squeeze_blank and self.repeated_blank_lines > 1:  # --squeeze-blank
                    continue
            else:
                self.repeated_blank_lines = 0

            if self.args.spaces:  # --spaces
                if self.print_color:
                    line = line.replace(" ", f"{Colors.WHITESPACE}{Whitespace.SPACE}{ConsoleColors.RESET}")
                else:
                    line = line.replace(" ", Whitespace.SPACE)

            if self.args.tabs:  # --tabs
                if self.print_color:
                    line = line.replace("\t", f"{Colors.WHITESPACE}{Whitespace.TAB}{ConsoleColors.RESET}")
                else:
                    line = line.replace("\t", Whitespace.TAB)

            if self.args.show_ends:  # --show-ends
                end_index = -1 if line.endswith("\n") else len(line)
                newline = "\n" if end_index == -1 else ""

                if self.print_color:
                    line = f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{ConsoleColors.RESET}{newline}"
                else:
                    line = f"{line[:end_index]}{Whitespace.EOL}{newline}"

            if print_number:
                width = 7

                if self.print_color:
                    line = f"{Colors.NUMBER}{self.number:>{width}}{ConsoleColors.RESET} {line}"
                else:
                    line = f"{self.number:>{width}} {line}"

            CLIProgram.print_line(line)

    def print_lines_from_files(self, files: list[str]) -> None:
        """
        Prints lines from files.
        :param files: The files.
        :return: None
        """
        last_file_index = len(files) - 1

        for index, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.print_lines(text)

                if self.args.group and index < last_file_index:  # --group
                    print()
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Prints lines from standard input until EOF is entered.
        :return: None
        """
        eof = False

        while not eof:
            try:
                self.print_lines([input()])
            except EOFError:
                eof = True


@final
class Whitespace:
    """
    Class for managing whitespace constants.
    """
    EOL: Final[str] = "$"
    SPACE: Final[str] = "~"
    TAB: Final[str] = ">···"


if __name__ == "__main__":
    CLIProgram.run(Main())
