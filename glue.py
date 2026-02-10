#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: glue.py
Author: Roth Earl
Version: 1.3.14
Description: A program that concatenates files and standard input to standard output.
License: GNU GPLv3
"""

import argparse
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    EOL: Final[str] = ansi.Colors.BRIGHT_BLUE
    NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    TAB: Final[str] = ansi.Colors.BRIGHT_CYAN


class Whitespace:
    """
    Namespace for whitespace replacement constants.

    :cvar EOL: Replacement for the EOL.
    :cvar TAB: Replacement for a tab.
    """
    EOL: Final[str] = "$"
    TAB: Final[str] = ">···"


class Glue(CLIProgram):
    """
    A program that concatenates files and standard input to standard output.

    :ivar line_number: Line number to be printed with output lines.
    """

    def __init__(self) -> None:
        """Initialize a new ``Glue`` instance."""
        super().__init__(name="glue", version="1.3.14")

        self.line_number: int = 0

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="concatenate FILES to standard output",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        blank_group = parser.add_mutually_exclusive_group()
        number_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        number_group.add_argument("-b", "--number-nonblank", action="store_true", help="number nonblank lines")
        number_group.add_argument("-n", "--number", action="store_true", help="number lines")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        blank_group.add_argument("-s", "--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        parser.add_argument("-E", "--show-ends", action="store_true",
                            help=f"display '{Whitespace.EOL}' at end of each line")
        parser.add_argument("-T", "--show-tabs", action="store_true",
                            help=f"display tab characters as '{Whitespace.TAB}'")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for numbers and whitespace (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--number-width", default=6, help="pad line numbers to width N (default: 6; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        if self.args.number_width < 1:  # --number-width
            self.print_error_and_exit("--number-width must be >= 1")

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_lines_from_files(sys.stdin)
            else:
                self.print_lines(sys.stdin)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_lines(self, lines: Iterable[str]) -> None:
        """Print lines to standard output applying numbering and whitespace rendering and blank-line suppression."""
        blank_line_count = 0
        number_lines = self.args.number or self.args.number_nonblank  # --number or --number-nonblank

        for line in io.normalize_input_lines(lines):
            print_number = number_lines

            if not line:  # Blank line?
                blank_line_count += 1

                if self.should_suppress_blank_line(blank_line_count):
                    continue

                if self.args.number_nonblank:  # --number-nonblank
                    print_number = False
            else:
                blank_line_count = 0

            line = self.render_whitespace(line)

            if print_number:
                self.line_number += 1
                line = self.render_number(line)

            print(line)

    def print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read and print lines from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_lines(file_info.text)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        self.print_lines(sys.stdin)

    def render_number(self, line: str) -> str:
        """Prefix a formatted line number to the line."""
        if self.print_color:
            return f"{Colors.NUMBER}{self.line_number:>{self.args.number_width}}{ansi.RESET} {line}"

        return f"{self.line_number:>{self.args.number_width}} {line}"

    def render_whitespace(self, line: str) -> str:
        """Render visible representations of tabs and end-of-line markers."""
        if self.args.show_tabs:  # --show-tabs
            if self.print_color:
                line = line.replace("\t", f"{Colors.TAB}{Whitespace.TAB}{ansi.RESET}")
            else:
                line = line.replace("\t", Whitespace.TAB)

        if self.args.show_ends:  # --show-ends
            if self.print_color:
                line = f"{line}{Colors.EOL}{Whitespace.EOL}{ansi.RESET}"
            else:
                line = f"{line}{Whitespace.EOL}"

        return line

    def should_suppress_blank_line(self, blank_line_count: int) -> bool:
        """Determine whether a blank line should be suppressed based on blank-line handling options."""
        if self.args.no_blank:  # --no-blank
            return True

        if self.args.squeeze_blank and blank_line_count > 1:  # --squeeze-blank
            return True

        return False


if __name__ == "__main__":
    Glue().run()
