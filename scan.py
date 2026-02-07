#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: scan.py
Author: Roth Earl
Version: 1.3.12
Description: A program that prints lines that match patterns in files.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, Patterns, ansi, io, patterns, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    MATCH: Final[str] = ansi.Colors.BRIGHT_RED


class Scan(CLIProgram):
    """
    A program that prints lines that match patterns in files.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_match: Whether a match was found in a file.
    :ivar line_number: Line number for tracking where matches were found.
    :ivar patterns: Compiled patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize a new ``Scan`` instance."""
        super().__init__(name="scan", version="1.3.12", error_exit_code=2)

        self.found_match: bool = False
        self.line_number: int = 0
        self.patterns: Patterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print lines that match patterns in FILES",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)
        count_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        count_group.add_argument("-c", "--count", action="store_true",
                                 help="print the count of matching lines per input file")
        count_group.add_argument("-C", "--count-nonzero", action="store_true",
                                 help="print the count only for files with at least one match")
        parser.add_argument("-f", "--find", action="extend", help="print lines that match PATTERN", metavar="PATTERN",
                            nargs=1)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="do not prefix output with file names")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case distinctions")
        parser.add_argument("-n", "--line-number", action="store_true", help="show line number for each matching line")
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print lines that do not match")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, matches, and line numbers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_for_errors(self) -> None:
        """Raise ``SystemExit(Scan.NO_MATCHES_EXIT_CODE)`` if a match was not found."""
        super().check_for_errors()

        if not self.found_match:
            raise SystemExit(Scan.NO_MATCHES_EXIT_CODE)

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        # Exit early if no --find patterns are provided.
        if not self.args.find:
            sys.exit(Scan.NO_MATCHES_EXIT_CODE)

    def is_printing_counts(self) -> bool:
        """Return whether ``--count`` or ``--count-nonzero`` is set."""
        return self.args.count or self.args.count_nonzero  # --count or --count-nonzero

    @override
    def main(self) -> None:
        """Run the program."""
        # Pre-compile --find patterns.
        if self.args.find:
            self.patterns = patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                      on_error=self.print_error_and_exit)

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_matches_from_files(sys.stdin)
            elif standard_input := sys.stdin.readlines():
                self.args.no_file_name = self.args.no_file_name or not self.args.files  # No file header if no files.
                self.print_matches(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.print_matches_from_files(self.args.files)
        elif self.args.files:
            self.print_matches_from_files(self.args.files)
        else:
            self.args.no_file_name = True  # No file header if no files.
            self.print_matches_from_input()

    def print_matches(self, lines: Iterable[str], *, origin_file: str, reset_line_number=True) -> None:
        """
        Print matches found in lines.

        :param lines: Iterable of lines to search.
        :param origin_file: File where the lines originated from.
        :param reset_line_number: Whether to reset the internal line number (default: ``True``).
        """
        matches = []

        if reset_line_number:
            self.line_number = 0

        # Find matches.
        for line in lines:
            self.line_number += 1

            if patterns.matches_all_patterns(line, self.patterns) != self.args.invert_match:  # --invert-match
                self.found_match = True

                # If --quiet, exit on first match for performance.
                if self.args.quiet:
                    raise SystemExit(0)

                if self.print_color and not self.args.invert_match:  # --invert-match
                    line = patterns.color_pattern_matches(line, self.patterns, color=Colors.MATCH)

                matches.append((self.line_number, line))

        # Print matches.
        file_name = ""

        if self.args.count_nonzero and not matches:  # --count-nonzero
            return

        if not self.args.no_file_name:  # --no-file-name
            file_name = os.path.relpath(origin_file) if origin_file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

        if self.is_printing_counts():
            print(f"{file_name}{len(matches)}")
        elif matches:
            padding = len(str(matches[-1][0])) if reset_line_number else 0

            if file_name:
                print(file_name)

            for line_number, line in matches:
                if self.args.line_number:  # --line-number
                    if self.print_color:
                        print(f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}:{ansi.RESET}", end="")
                    else:
                        print(f"{line_number:>{padding}}:", end="")

                io.print_line_with_newline(line)

    def print_matches_from_files(self, files: Iterable[str]) -> None:
        """Read lines from each file and print matches."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_matches(file_info.text, origin_file=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_matches_from_input(self) -> None:
        """Read lines from standard input until EOF and print matches."""
        eof = False
        lines = []

        while not eof:
            try:
                line = input()

                # If printing counts, wait until EOF before finding matches.
                if self.is_printing_counts():
                    lines.append(line)
                else:
                    self.print_matches([line], origin_file="", reset_line_number=False)
            except EOFError:
                eof = True

        if self.is_printing_counts():
            self.print_matches(lines, origin_file="")


if __name__ == "__main__":
    Scan().run()
