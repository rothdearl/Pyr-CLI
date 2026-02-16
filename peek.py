#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that prints the first part of files."""

import argparse
import os
import sys
from collections import deque
from collections.abc import Iterable
from typing import Final, override

from cli import TextProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Peek(TextProgram):
    """A program that prints the first part of files."""

    def __init__(self) -> None:
        """Initialize a new ``Peek`` instance."""
        super().__init__(name="peek", version="1.3.18")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the first part of FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the first N lines, or all but the last N if N < 0 (default: 10)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
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

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def print_lines(self, lines: Iterable[str]) -> None:
        """Print lines to standard output."""
        # If --lines is positive or zero: print the first N lines.
        if self.args.lines >= 0:
            for index, line in enumerate(io.normalize_input_lines(lines)):
                if index >= self.args.lines:
                    break

                print(line)

            return

        # --lines is negative: print all but the last |N| lines.
        buffer = deque(maxlen=-self.args.lines)

        for line in io.normalize_input_lines(lines):
            if len(buffer) == buffer.maxlen:
                print(buffer.popleft())

            buffer.append(line)

    def print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read and print lines from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.print_lines(file_info.text_stream)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input (negative ``args.lines`` is treated as ``|N|``)."""
        self.args.lines = abs(self.args.lines)  # Normalize --lines before reading from standard input.
        self.print_lines(sys.stdin)


if __name__ == "__main__":
    Peek().run()
