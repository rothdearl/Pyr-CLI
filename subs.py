#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: subs.py
Author: Roth Earl
Version: 1.3.5
Description: A program to replace text in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from collections.abc import Iterable
from enum import StrEnum
from typing import TextIO, final

from cli import CLIProgram, colors, io, patterns, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = colors.BRIGHT_CYAN
    FILE_NAME = colors.BRIGHT_MAGENTA


@final
class Subs(CLIProgram):
    """
    A program to replace text in files.

    :ivar re.Pattern[str] pattern: Compiled pattern to match.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="subs", version="1.3.5")

        self.pattern: re.Pattern[str] | None = None

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds and returns an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="replace text in FILES",
                                         epilog="with no FILES, read standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-f", "--find", action="extend", help="replace text matching PATTERN", metavar="PATTERN",
                            nargs=1, required=True)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching patterns")
        parser.add_argument("-r", "--replace", help="replace matches with literal STRING", metavar="STRING",
                            required=True)
        parser.add_argument("--color", choices=("on", "off"), default="on", help="colorize file headers (default: on)")
        parser.add_argument("--in-place", action="store_true",
                            help="write changes back to FILES instead of standard output")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--max-replacements", default=sys.maxsize,
                            help="limit replacements to N per line (default: unlimited; N >= 1)", metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def iterate_replaced_lines(self, lines: Iterable[str]) -> Iterable[str]:
        """
        Yield lines with pattern matches replaced.

        :param lines: Input lines.
        :return: An iterator yielding transformed lines.
        """
        for line in lines:
            line = line.rstrip("\n")  # Remove trailing newlines so $ matches only once per line.

            if self.pattern:
                line = self.pattern.sub(self.args.replace, line, count=self.args.max_replacements)

            yield line

    def main(self) -> None:
        """
        Runs the primary function of the program.
        """
        # Pre-compile --find patterns.
        if compiled := patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                 on_error=self.print_error_and_exit):
            self.pattern = patterns.combine_patterns(compiled, ignore_case=self.args.ignore_case)

        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.process_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.print_replaced_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_files(self.args.files)
        elif self.args.files:
            self.process_files(self.args.files)
        else:
            self.print_replaced_lines_from_input()

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.

        :param file: File header to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            filename = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                filename = f"{Colors.FILE_NAME}{filename}{Colors.COLON}:{colors.RESET}"
            else:
                filename = f"{filename}:"

            print(filename)

    def print_replaced_lines(self, lines: Iterable[str]) -> None:
        """
        Prints the replaced matches in the lines.

        :param lines: Lines to replace.
        """
        for line in self.iterate_replaced_lines(lines):
            io.print_line(line)

    def print_replaced_lines_from_input(self) -> None:
        """
        Prints the replaced matches in the lines from standard input until EOF is entered.
        """
        self.print_replaced_lines(sys.stdin.read().splitlines())

    def process_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Process files by replacing matches and printing results or writing changes in place.

        :param files: Files to process.
        """
        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            if self.args.in_place:  # --in-place
                io.write_text_to_file(file_info.filename, self.iterate_replaced_lines(file_info.text.readlines()),
                                      self.encoding, on_error=self.print_error)
            else:
                try:
                    self.print_file_header(file=file_info.filename)
                    self.print_replaced_lines(file_info.text.readlines())
                except UnicodeDecodeError:
                    self.print_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def validate_parsed_arguments(self) -> None:
        """
        Validates the parsed command-line arguments.
        """
        if self.args.max_replacements < 1:  # --max-replacements
            self.print_error_and_exit("'max-replacements' must be >= 1")


if __name__ == "__main__":
    Subs().run()
