#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: subs.py
Author: Roth Earl
Version: 1.0.0
Description: A program to replace text in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from enum import StrEnum
from typing import Iterator, TextIO, final

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
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="subs", version="1.0.0")

        self.max_replacements: int = 0
        self.pattern: re.Pattern[str] | None = None

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds and returns an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="replace text in FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to process", metavar="FILES", nargs="*")
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
        parser.add_argument("--max-replacements", help="limit replacements to N per line (default: unlimited; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--stdin-files", action="store_true", help="treat standard input as a list of FILES")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def iterate_replaced_lines(self, lines: list[str]) -> Iterator[str]:
        """
        Yield lines with pattern matches replaced.
        :param lines: Input lines.
        :return: An iterator yielding transformed lines.
        """
        for line in lines:
            line = line.rstrip("\n")  # Remove trailing newlines so $ matches only once per line.

            if self.pattern:
                line = self.pattern.sub(self.args.replace, line, count=self.max_replacements)

            yield line

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_max_replacements()

        # Pre-compile --find patterns.
        if compiled := patterns.compile_patterns(self, self.args.find, ignore_case=self.args.ignore_case):
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
        :param file: The file.
        :return: None
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{colors.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_replaced_lines(self, lines: list[str]) -> None:
        """
        Prints the replaced matches in the lines.
        :param lines: The lines.
        :return: None
        """
        for line in self.iterate_replaced_lines(lines):
            io.print_line(line)

    def print_replaced_lines_from_input(self) -> None:
        """
        Prints the replaced matches in the lines from standard input until EOF is entered.
        :return: None
        """
        self.print_replaced_lines(sys.stdin.read().splitlines())

    def process_files(self, files: TextIO | list[str]) -> None:
        """
        Process files by replacing matches and printing results or writing changes in place.
        :param files: The files to process.
        :return: None
        """
        for file_info in io.read_files(files, self.encoding, logger=self):
            if self.args.in_place:  # --in-place
                io.write_text_to_file(file_info.filename, self.iterate_replaced_lines(file_info.text.readlines()),
                                      self.encoding, logger=self)
            else:
                try:
                    self.print_file_header(file=file_info.filename)
                    self.print_replaced_lines(file_info.text.readlines())
                except UnicodeDecodeError:
                    self.print_file_error(f"{file_info.filename}: unable to read with {self.encoding}")

    def set_max_replacements(self) -> None:
        """
        Sets the maximum replacements.
        :return: None
        """
        if self.args.max_replacements is not None:  # --max-replacements
            if self.args.max_replacements < 1:
                self.print_error(f"'max-replacements' must be >= 1", raise_system_exit=True)

            self.max_replacements = self.args.max_replacements


if __name__ == "__main__":
    Subs().run()
