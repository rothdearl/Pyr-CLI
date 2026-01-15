#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: scan.py
Author: Roth Earl
Version: 1.3.3
Description: A program to print lines that match patterns in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, colors, io, patterns, terminal


@final
class Colors:
    """
    Class for managing color constants.
    """
    COLON: Final[str] = colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = colors.BRIGHT_GREEN
    MATCH: Final[str] = colors.BRIGHT_RED


@final
class Scan(CLIProgram):
    """
    A program to print lines that match patterns in files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="scan", version="1.3.3", error_exit_code=2)

        self.line_number: int = 0
        self.found_match: bool = False
        self.patterns: list[list[re.Pattern]] = []

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print lines that match patterns in FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to search", metavar="FILES", nargs="*")
        parser.add_argument("-c", "--count", action="store_true",
                            help="print only the count of matching lines per input file")
        parser.add_argument("-f", "--find", action="extend", help="print lines that match PATTERN", metavar="PATTERN",
                            nargs=1, required=True)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching patterns")
        parser.add_argument("-I", "--invert-match", action="store_true", help="print lines that do not match")
        parser.add_argument("-n", "--line-number", action="store_true", help="print line number with output lines")
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display matched strings, file names and line numbers in color (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input as arguments")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def check_for_errors(self) -> None:
        """
        Raises a SystemExit if there are any errors.
        :return: None
        :raises SystemExit: Request to exit from the interpreter if there are any errors.
        """
        super().check_for_errors()

        if not self.found_match:
            raise SystemExit(1)

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        # Pre-compile --find patterns.
        self.patterns = patterns.compile_patterns(self, self.args.find, ignore_case=self.args.ignore_case)

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_matches_in_files(sys.stdin)
            elif standard_input := sys.stdin.readlines():
                self.args.no_file_header = self.args.no_file_header or not self.args.files  # No file header if no files
                self.print_matches_in_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.print_matches_in_files(self.args.files)
        elif self.args.files:
            self.print_matches_in_files(self.args.files)
        else:
            self.args.no_file_header = True  # No file header if no files
            self.print_matches_in_input()

    def print_matches_in_files(self, files: TextIO | list[str]) -> None:
        """
        Prints matches found in files.
        :param files: The files.
        :return: None
        """
        for _, file, text in io.read_files(self, files, self.encoding):
            try:
                self.print_matches_in_lines(text, origin_file=file)
            except UnicodeDecodeError:
                self.print_file_error(f"{file}: unable to read with {self.encoding}")

    def print_matches_in_input(self) -> None:
        """
        Prints matches found in standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                line = input()

                # If --count, wait until EOF before finding matches.
                if self.args.count:
                    lines.append(line)
                else:
                    self.print_matches_in_lines([line], origin_file="", reset_line_number=False)
            except EOFError:
                eof = True

        if self.args.count:  # --count
            self.print_matches_in_lines(lines, origin_file="")

    def print_matches_in_lines(self, lines: TextIO | list[str], *, origin_file: str, reset_line_number=True) -> None:
        """
        Prints matches found in lines.
        :param lines: The lines.
        :param origin_file: The file where the lines originated from.
        :param reset_line_number: Whether to reset the line number; default is True.
        :return: None
        """
        matches = []

        if reset_line_number:
            self.line_number = 0

        # Find matches.
        for line in lines:
            self.line_number += 1

            if patterns.text_has_patterns(line, self.patterns) != self.args.invert_match:  # --invert-match
                self.found_match = True

                # If --quiet, exit on first match for performance.
                if self.args.quiet:
                    raise SystemExit(0)

                if self.print_color and not self.args.invert_match:  # --invert-match
                    line = patterns.color_patterns_in_text(line, self.patterns,
                                                           color=Colors.MATCH) if self.patterns else line

                if self.args.line_number:  # --line-number
                    if self.print_color:
                        line = f"{Colors.LINE_NUMBER}{self.line_number:>}{Colors.COLON}:{colors.RESET}{line}"
                    else:
                        line = f"{self.line_number:>}:{line}"

                matches.append(line)

        # Print matches.
        file_name = ""

        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(origin_file) if origin_file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{colors.RESET}"
            else:
                file_name = f"{file_name}:"

        if self.args.count:  # --count
            print(f"{file_name}{len(matches)}")
        elif matches:
            if file_name:
                print(file_name)

            for line in matches:
                io.print_line(line)


if __name__ == "__main__":
    Scan().run()
