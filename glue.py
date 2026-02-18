#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that concatenates files and standard input to standard output."""

import argparse
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import TextProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    END_MARKER: Final[str] = ansi.Colors.BRIGHT_BLUE
    NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    TAB_MARKER: Final[str] = ansi.Colors.BRIGHT_CYAN


class Whitespace:
    """Namespace for whitespace replacement constants."""
    END_MARKER: Final[str] = "$"
    TAB_MARKER: Final[str] = ">···"


class Glue(TextProgram):
    """
    A program that concatenates files and standard input to standard output.

    :ivar line_number: Line number to be printed with output lines.
    """

    def __init__(self) -> None:
        """Initialize a new ``Glue`` instance."""
        super().__init__(name="glue", version="1.4.2")

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
        parser.add_argument("--number-width", default=6, help="pad line numbers to width N (default: 6; N >= 1)",
                            metavar="N", type=int)
        blank_group.add_argument("-s", "--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("-E", "--show-ends", action="store_true",
                            help=f"display '{Whitespace.END_MARKER}' at end of each line")
        parser.add_argument("-T", "--show-tabs", action="store_true",
                            help=f"display tab characters as '{Whitespace.TAB_MARKER}'")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for numbers and whitespace (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_lines(file_info.text_stream)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files(sys.stdin)
            else:
                self.print_lines(sys.stdin)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_lines(self, lines: Iterable[str]) -> None:
        """Print lines to standard output, applying numbering, whitespace rendering, and blank-line handling."""
        blank_line_count = 0
        number_lines = self.args.number or self.args.number_nonblank

        for line in io.normalize_input_lines(lines):
            print_number = number_lines

            if not line:  # Blank line?
                blank_line_count += 1

                if self.should_suppress_blank_line(blank_line_count):
                    continue

                if self.args.number_nonblank:
                    print_number = False
            else:
                blank_line_count = 0

            line = self.render_whitespace(line)

            if print_number:
                self.line_number += 1
                line = self.render_number(line)

            print(line)

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
        rendered = line

        if self.args.show_tabs:
            if self.print_color:
                rendered = rendered.replace("\t", f"{Colors.TAB_MARKER}{Whitespace.TAB_MARKER}{ansi.RESET}")
            else:
                rendered = rendered.replace("\t", Whitespace.TAB_MARKER)

        if self.args.show_ends:
            if self.print_color:
                rendered = f"{rendered}{Colors.END_MARKER}{Whitespace.END_MARKER}{ansi.RESET}"
            else:
                rendered = f"{rendered}{Whitespace.END_MARKER}"

        return rendered

    def should_suppress_blank_line(self, blank_line_count: int) -> bool:
        """Return whether a blank line should be suppressed."""
        if self.args.no_blank:
            return True

        if self.args.squeeze_blank and blank_line_count > 1:
            return True

        return False

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.number_width < 1:
            self.print_error_and_exit("--number-width must be >= 1")


if __name__ == "__main__":
    Glue().run()
