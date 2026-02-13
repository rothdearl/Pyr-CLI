#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that replaces matching text in files."""

import argparse
import os
import re
import sys
from collections.abc import Iterable, Iterator
from typing import Final, override

from cli import CLIProgram, ansi, io, patterns, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Subs(CLIProgram):
    """
    A program that replaces matching text in files.

    :ivar pattern: Compiled pattern to match.
    """

    def __init__(self) -> None:
        """Initialize a new ``Subs`` instance."""
        super().__init__(name="subs", version="1.3.15")

        self.pattern: re.Pattern[str] | None = None

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="replace matching text in FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-e", "--find", action="extend", help="match PATTERN (repeat --find to match any pattern)",
                            metavar="PATTERN", nargs=1, required=True)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching")
        parser.add_argument("-r", "--replace", help="replace matches with literal STRING", metavar="STRING",
                            required=True)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--in-place", action="store_true",
                            help="write changes back to FILES instead of standard output")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--max-replacements", default=sys.maxsize, help="limit replacements to N per line (N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        if self.args.max_replacements < 1:  # --max-replacements
            self.print_error_and_exit("--max-replacements must be >= 1")

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def compile_patterns(self) -> None:
        """Compile search patterns and combine them into a single OR-pattern."""
        if compiled := patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                 on_error=self.print_error_and_exit):
            self.pattern = patterns.compile_combined_patterns(compiled, ignore_case=self.args.ignore_case)

    def iterate_replaced_lines(self, lines: Iterable[str]) -> Iterator[str]:
        """Yield lines with pattern matches replaced."""
        for line in io.normalize_input_lines(lines):
            if self.pattern:
                yield self.pattern.sub(self.args.replace, line, count=self.args.max_replacements)
            else:
                yield line

    @override
    def main(self) -> None:
        """Run the program."""
        self.compile_patterns()

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.process_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_replaced_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_files(self.args.files)
        elif self.args.files:
            self.process_files(self.args.files)
        else:
            self.print_replaced_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def print_replaced_lines(self, lines: Iterable[str]) -> None:
        """Print replaced lines."""
        for line in self.iterate_replaced_lines(lines):
            print(line)

    def print_replaced_lines_from_input(self) -> None:
        """Read, replace, and print lines from standard input until EOF."""
        self.print_replaced_lines(sys.stdin)

    def process_files(self, files: Iterable[str]) -> None:
        """Process files by replacing matches and printing results or writing changes in place."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            if self.args.in_place:  # --in-place
                io.write_text_to_file(file_info.file_name,
                                      self.iterate_replaced_lines(file_info.text_stream.readlines()), self.encoding,
                                      on_error=self.print_error)
            else:
                try:
                    self.print_file_header(file_info.file_name)
                    self.print_replaced_lines(file_info.text_stream.readlines())
                except UnicodeDecodeError:
                    self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")


if __name__ == "__main__":
    Subs().run()
