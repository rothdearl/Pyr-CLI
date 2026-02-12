#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that prints files to standard output."""

import argparse
import os
import sys
from collections.abc import Collection, Iterable
from typing import Final, override

from cli import CLIProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    EOL: Final[str] = ansi.Colors.BRIGHT_BLUE
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    SPACE: Final[str] = ansi.Colors.BRIGHT_CYAN
    TAB: Final[str] = ansi.Colors.BRIGHT_CYAN


class Whitespace:
    """
    Namespace for whitespace replacement constants.

    :cvar EOL: Replacement for the EOL.
    :cvar SPACE: Replacement for a space.
    :cvar TAB: Replacement for a tab.
    :cvar TRAILING_SPACE: Replacement for a trailing space.
    """
    EOL: Final[str] = "$"
    SPACE: Final[str] = "·"
    TAB: Final[str] = ">···"
    TRAILING_SPACE: Final[str] = "~"


class Show(CLIProgram):
    """A program that prints files to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Show`` instance."""
        super().__init__(name="show", version="1.3.15")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="read standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-l", "--max-lines", default=sys.maxsize, help="print first N lines (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-n", "--line-numbers", action="store_true", help="number lines")
        parser.add_argument("-s", "--start", default=1, help="start at line N (N < 0 counts from end; N != 0)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, line numbers, and whitespace (default: on)")
        parser.add_argument("--ends", action="store_true", help=f"display '{Whitespace.EOL}' at end of each line")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--spaces", action="store_true",
                            help=f"display spaces as '{Whitespace.SPACE}' and trailing spaces as '{Whitespace.TRAILING_SPACE}'")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--tabs", action="store_true", help=f"display tab characters as '{Whitespace.TAB}'")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        if self.args.max_lines < 1:  # --max-lines
            self.print_error_and_exit("--max-lines must be >= 1")

        if self.args.start == 0:  # --start
            self.print_error_and_exit("--start cannot = 0")

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
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
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def print_lines(self, lines: Collection[str]) -> None:
        """Print lines to standard output according to command-line arguments."""
        line_start = len(lines) + self.args.start + 1 if self.args.start < 0 else self.args.start
        line_end = line_start + self.args.max_lines - 1
        line_min = min(self.args.max_lines, len(lines)) if self.args.max_lines else len(lines)
        padding = len(str(line_min))

        for line_number, line in enumerate(io.normalize_input_lines(lines), start=1):
            if line_start <= line_number <= line_end:
                if self.args.spaces:  # --spaces
                    line = self.render_spaces(line)

                if self.args.tabs:  # --tabs
                    line = self.render_tabs(line)

                if self.args.ends:  # --ends
                    line = self.render_ends(line)

                if self.args.line_numbers:  # --line-numbers
                    line = self.render_line_number(line, line_number, padding)

                print(line)

    def print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read and print lines from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.print_lines(file_info.text_stream.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        self.print_lines(sys.stdin.readlines())

    def render_ends(self, line: str) -> str:
        """Append a visible end-of-line marker to the line."""
        end_index = len(line)

        if self.print_color:
            return f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{ansi.RESET}"

        return f"{line[:end_index]}{Whitespace.EOL}"

    def render_line_number(self, line: str, line_number: int, padding: int) -> str:
        """Prefix the line with a line number, right-aligned to the specified padding."""
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}{ansi.RESET} {line}"

        return f"{line_number:>{padding}} {line}"

    def render_spaces(self, line: str) -> str:
        """Replace spaces and trailing spaces with visible markers."""
        trailing_count = len(line) - len(line.rstrip(" "))  # Count trailing spaces.

        # Truncate trailing spaces.
        line = line[:-trailing_count] if trailing_count else line

        if self.print_color:
            line = line.replace(" ", f"{Colors.SPACE}{Whitespace.SPACE}{ansi.RESET}")
            line = line + Colors.SPACE + (Whitespace.TRAILING_SPACE * trailing_count) + ansi.RESET
        else:
            line = line.replace(" ", Whitespace.SPACE)
            line = line + (Whitespace.TRAILING_SPACE * trailing_count)

        return line

    def render_tabs(self, line: str) -> str:
        """Replace tabs with visible markers."""
        if self.print_color:
            return line.replace("\t", f"{Colors.TAB}{Whitespace.TAB}{ansi.RESET}")

        return line.replace("\t", Whitespace.TAB)


if __name__ == "__main__":
    Show().run()
