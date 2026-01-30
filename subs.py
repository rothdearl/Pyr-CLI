#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: subs.py
Author: Roth Earl
Version: 1.3.7
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

from cli import CLIProgram, ansi, io, patterns, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.BRIGHT_CYAN
    FILE_NAME = ansi.BRIGHT_MAGENTA


@final
class Subs(CLIProgram):
    """
    A program to replace text in files.

    :ivar pattern: Compiled pattern to match.
    """

    def __init__(self) -> None:
        """
        Initialize a new Subs instance.
        """
        super().__init__(name="subs", version="1.3.7")

        self.pattern: re.Pattern[str] | None = None

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="replace text in FILES",
                                         epilog="if no FILES are specified, read standard input", prog=self.name)

        parser.add_argument("files", help="one or more input files", metavar="FILES", nargs="*")
        parser.add_argument("-f", "--find", action="extend", help="replace text matching PATTERN", metavar="PATTERN",
                            nargs=1, required=True)
        parser.add_argument("-H", "--no-file-header", action="store_true", help="do not prepend file names to output")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching patterns")
        parser.add_argument("-r", "--replace", help="replace matches with literal STRING", metavar="STRING",
                            required=True)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file headers (default: on)")
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
        :return: Iterator yielding transformed lines.
        """
        for line in lines:
            line = line.rstrip("\n")  # Remove trailing newlines so $ matches only once per line.

            if self.pattern:
                line = self.pattern.sub(self.args.replace, line, count=self.args.max_replacements)

            yield line

    def main(self) -> None:
        """
        Run the program logic.
        """
        self.precompile_patterns()

        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
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

    def precompile_patterns(self) -> None:
        """
        Pre-compile search patterns.
        """
        if compiled := patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                 on_error=self.print_error_and_exit):
            self.pattern = patterns.compile_combined_patterns(compiled, ignore_case=self.args.ignore_case)

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name, or "(standard input)" if empty, with a colon.

        :param file_name: File name to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_replaced_lines(self, lines: Iterable[str]) -> None:
        """
        Print replaced matches in the lines.

        :param lines: Lines to replace matches in.
        """
        for line in self.iterate_replaced_lines(lines):
            io.print_normalized_line(line)

    def print_replaced_lines_from_input(self) -> None:
        """
        Print replaced matches in lines from standard input until EOF is entered.
        """
        self.print_replaced_lines(sys.stdin.read().splitlines())

    def process_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Process files by replacing matches and printing results or writing changes in place.

        :param files: Files to process.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            if self.args.in_place:  # --in-place
                io.write_text_to_file(file_info.file_name, self.iterate_replaced_lines(file_info.text.readlines()),
                                      self.encoding, on_error=self.print_error)
            else:
                try:
                    self.print_file_header(file_info.file_name)
                    self.print_replaced_lines(file_info.text.readlines())
                except UnicodeDecodeError:
                    self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        if self.args.max_replacements < 1:  # --max-replacements
            self.print_error_and_exit("'max-replacements' must be >= 1")


if __name__ == "__main__":
    Subs().run()
