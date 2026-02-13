#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that prints lines matching patterns in files."""

import argparse
import os
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, CompiledPatterns, ansi, io, patterns, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    MATCH: Final[str] = ansi.Colors.BRIGHT_RED


class Scan(CLIProgram):
    """
    A program that prints lines matching patterns in files.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_any_match: Whether any match was found.
    :ivar patterns: Compiled patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize a new ``Scan`` instance."""
        super().__init__(name="scan", version="1.3.15", error_exit_code=2)

        self.found_any_match: bool = False
        self.patterns: CompiledPatterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print lines matching patterns in FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        count_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        count_group.add_argument("-c", "--count", action="store_true", help="print count of matching lines per file")
        count_group.add_argument("-C", "--count-nonzero", action="store_true",
                                 help="print count of matching lines for files with a match")
        parser.add_argument("-e", "--find", action="extend",
                            help="print lines that match PATTERN (repeat --find to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching")
        parser.add_argument("-n", "--line-number", action="store_true", help="show line number for each matching line")
        parser.add_argument("-q", "--quiet", "--silent", action="store_true",
                            help="suppress normal output (matches, counts, and file names)")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress file error messages")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print lines that do not match")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, matches, and line numbers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_for_errors(self) -> None:
        """Raise ``SystemExit(NO_MATCHES_EXIT_CODE)`` if a match was not found."""
        super().check_for_errors()

        if not self.found_any_match:
            raise SystemExit(Scan.NO_MATCHES_EXIT_CODE)

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def compile_patterns(self) -> None:
        """Compile search patterns."""
        if self.args.find:
            self.patterns = patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                      on_error=self.print_error_and_exit)

    def is_printing_counts(self) -> bool:
        """Return whether ``args.count`` or ``args.count_nonzero`` is set."""
        return self.args.count or self.args.count_nonzero  # --count or --count-nonzero

    @override
    def main(self) -> None:
        """Run the program."""
        self.compile_patterns()

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_matches_from_files(sys.stdin)
            elif standard_input := sys.stdin.readlines():
                self.print_matches(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.print_matches_from_files(self.args.files)
        elif self.args.files:
            self.print_matches_from_files(self.args.files)
        else:
            self.args.no_file_name = True  # No file header if no files.
            self.print_matches_from_input()

    def print_matches(self, lines: Iterable[str], *, origin_file: str) -> None:
        """Search lines and print matches or counts according to command-line options."""
        # Return early if no --find patterns are provided.
        if not self.args.find:
            return

        matches = []

        # Find matches.
        for line_number, line in enumerate(io.normalize_input_lines(lines), start=1):
            if patterns.matches_all_patterns(line, self.patterns) != self.args.invert_match:  # --invert-match
                self.found_any_match = True

                # Exit early if --quiet.
                if self.args.quiet:
                    raise SystemExit(0)

                if self.print_color and not self.args.invert_match:  # --invert-match
                    line = patterns.color_pattern_matches(line, self.patterns, color=Colors.MATCH)

                matches.append((line_number, line))

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
            padding = len(str(matches[-1][0]))  # Use the line number from the last match to determine pad width.

            if file_name:
                print(file_name)

            for line_number, line in matches:
                if self.args.line_number:  # --line-number
                    if self.print_color:
                        print(f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}:{ansi.RESET}", end="")
                    else:
                        print(f"{line_number:>{padding}}:", end="")

                print(line)

    def print_matches_from_files(self, files: Iterable[str]) -> None:
        """Read and print matches from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_matches(file_info.text_stream, origin_file=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_matches_from_input(self) -> None:
        """Read and print matches from standard input until EOF."""
        if self.is_printing_counts():
            self.print_matches(sys.stdin.readlines(), origin_file="")
        else:
            self.print_matches(sys.stdin, origin_file="")


if __name__ == "__main__":
    Scan().run()
