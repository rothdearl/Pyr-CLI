#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that prints files to standard output."""

import argparse
import sys
from collections.abc import Sequence
from typing import Final, override

from cli import TextProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    END_MARKER: Final[str] = ansi.Colors.BRIGHT_BLUE
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    SPACE_MARKER: Final[str] = ansi.Colors.BRIGHT_CYAN
    TAB_MARKER: Final[str] = ansi.Colors.BRIGHT_CYAN


class Whitespace:
    """Namespace for whitespace replacement constants."""
    END_MARKER: Final[str] = "$"
    SPACE_MARKER: Final[str] = "·"
    TAB_MARKER: Final[str] = ">···"
    TRAILING_SPACE_MARKER: Final[str] = "~"


class Show(TextProgram):
    """A program that prints files to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Show`` instance."""
        super().__init__(name="show", version="1.4.2")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="read standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-s", "--start", default=1, help="start at line N (N < 0 counts from end; N != 0)",
                            metavar="N", type=int)
        parser.add_argument("-l", "--max-lines", default=sys.maxsize, help="print first N lines (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-n", "--line-numbers", action="store_true", help="number lines")
        parser.add_argument("--ends", action="store_true",
                            help=f"display '{Whitespace.END_MARKER}' at end of each line")
        parser.add_argument("--spaces", action="store_true",
                            help=f"display spaces as '{Whitespace.SPACE_MARKER}' and trailing spaces as '{Whitespace.TRAILING_SPACE_MARKER}'")
        parser.add_argument("--tabs", action="store_true", help=f"display tab characters as '{Whitespace.TAB_MARKER}'")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, line numbers, and whitespace (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.print_lines(file_info.text_stream.readlines())

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the rendered file header for ``file_name``."""
        print(self.render_file_header(file_name, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON))

    def print_lines(self, lines: Sequence[str]) -> None:
        """Print lines to standard output, applying numbering and whitespace rendering."""
        line_start = self.args.start if self.args.start > 0 else len(lines) + self.args.start + 1
        line_end = min(len(lines), line_start + self.args.max_lines - 1)
        padding = len(str(line_end))

        for line_number, line in enumerate(io.normalize_input_lines(lines), start=1):
            if line_start <= line_number <= line_end:
                rendered = line

                if self.args.spaces:
                    rendered = self.render_spaces(rendered)

                if self.args.tabs:
                    rendered = self.render_tabs(rendered)

                if self.args.ends:
                    rendered = self.render_ends(rendered)

                if self.args.line_numbers:
                    rendered = self.render_line_number(rendered, line_number, padding)

                print(rendered)

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        self.print_lines(sys.stdin.readlines())

    def render_ends(self, line: str) -> str:
        """Append a visible end-of-line marker to the line."""
        if self.print_color:
            return f"{line}{Colors.END_MARKER}{Whitespace.END_MARKER}{ansi.RESET}"

        return f"{line}{Whitespace.END_MARKER}"

    def render_line_number(self, line: str, line_number: int, padding: int) -> str:
        """Prefix the line with a line number, right-aligned to the specified padding."""
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:>{padding}}{ansi.RESET} {line}"

        return f"{line_number:>{padding}} {line}"

    def render_spaces(self, line: str) -> str:
        """Replace spaces and trailing spaces with visible markers."""
        rendered = line
        trailing_count = len(rendered) - len(rendered.rstrip(" "))  # Count trailing spaces.

        # Truncate trailing spaces.
        rendered = rendered[:-trailing_count] if trailing_count else rendered

        if self.print_color:
            rendered = rendered.replace(" ", f"{Colors.SPACE_MARKER}{Whitespace.SPACE_MARKER}{ansi.RESET}")
            rendered = rendered + Colors.SPACE_MARKER + (Whitespace.TRAILING_SPACE_MARKER * trailing_count) + ansi.RESET
        else:
            rendered = rendered.replace(" ", Whitespace.SPACE_MARKER)
            rendered = rendered + (Whitespace.TRAILING_SPACE_MARKER * trailing_count)

        return rendered

    def render_tabs(self, line: str) -> str:
        """Replace tabs with visible markers."""
        if self.print_color:
            return line.replace("\t", f"{Colors.TAB_MARKER}{Whitespace.TAB_MARKER}{ansi.RESET}")

        return line.replace("\t", Whitespace.TAB_MARKER)

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.max_lines < 1:
            self.print_error_and_exit("--max-lines must be >= 1")

        if self.args.start == 0:
            self.print_error_and_exit("--start cannot be 0")


if __name__ == "__main__":
    Show().run()
