#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that numbers lines from files and prints them to standard output."""

import argparse
import os
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import TextProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN


class Num(TextProgram):
    """
    A program that numbers lines from files and prints them to standard output.

    :cvar FORMAT_PREFIXES: Mapping of short format keys to format-spec prefixes used when formatting line numbers.
    """

    FORMAT_PREFIXES: Final[dict[str, str]] = {
        "ln": "<",  # Left-aligned
        "rn": ">",  # Right-aligned
        "rz": "0>",  # Zero-padded, right-aligned
    }

    def __init__(self) -> None:
        """Initialize a new ``Num`` instance."""
        super().__init__(name="num", version="1.4.1")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="number lines in FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        blank_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-b", "--number-nonblank", action="store_true", help="number nonblank lines")
        parser.add_argument("--number-start", default=1, help="start numbering at N (default: 1; N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("-w", "--number-width", default=6, help="pad line numbers to width N (default: 6; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--number-format", choices=("ln", "rn", "rz"), default="rn",
                            help="format line numbers (ln=left, rn=right, rz=zero-padded; default: rn)")
        parser.add_argument("--number-separator", default="\t",
                            help="separate line numbers and output lines with SEP (default: <tab>)", metavar="SEP")
        blank_group.add_argument("-s", "--squeeze-blank", action="store_true", help="suppress repeated blank lines")
        blank_group.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names and line numbers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.number_lines(file_info.text_stream)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.number_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.number_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def number_lines(self, lines: Iterable[str]) -> None:
        """Number and print lines to standard output according to command-line arguments."""
        blank_line_count = 0
        format_prefix = Num.FORMAT_PREFIXES[self.args.number_format]
        line_number = self.args.number_start - 1

        for line in io.normalize_input_lines(lines):
            print_number = True

            if not line:  # Blank line?
                blank_line_count += 1

                if self.should_suppress_blank_line(blank_line_count):
                    continue

                if self.args.number_nonblank:
                    print_number = False
            else:
                blank_line_count = 0

            if print_number:
                line_number += 1
                line = self.render_line_number(line, line_number, format_prefix=format_prefix)

            print(line)

    def number_lines_from_input(self) -> None:
        """Read, number, and print lines from standard input until EOF."""
        self.number_lines(sys.stdin)

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def render_line_number(self, line: str, line_number: int, *, format_prefix: str) -> str:
        """Prefix a formatted line number to the line."""
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:{format_prefix}{self.args.number_width}}{ansi.RESET}{self.args.number_separator}{line}"

        return f"{line_number:{format_prefix}{self.args.number_width}}{self.args.number_separator}{line}"

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
        if self.args.number_start < 0:
            self.print_error_and_exit("--number-start must be >= 0")

        if self.args.number_width < 1:
            self.print_error_and_exit("--number-width must be >= 1")

        # Decode escape sequences in --number-separator.
        try:
            self.args.number_separator = self.args.number_separator.encode().decode("unicode_escape")
        except UnicodeDecodeError:
            self.print_error_and_exit("--number-separator contains an invalid escape sequence")


if __name__ == "__main__":
    Num().run()
