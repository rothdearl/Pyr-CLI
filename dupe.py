#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: dupe.py
Author: Roth Earl
Version: 1.3.7
Description: A program to filter matching lines in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from collections.abc import Iterable
from enum import StrEnum
from typing import Final, TextIO, final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.BRIGHT_CYAN
    FILE_NAME = ansi.BRIGHT_MAGENTA
    GROUP_COUNT = ansi.BRIGHT_GREEN


@final
class Dupe(CLIProgram):
    """
    A program to filter matching lines in files.

    :cvar FIELD_PATTERN: Pattern for splitting lines into fields.
    :ivar max_chars: Maximum number of characters to compare.
    :ivar skip_chars: Number of characters to skip at the beginning of each line.
    :ivar skip_fields: Number of fields to skip at the beginning of each line.
    """

    FIELD_PATTERN: Final[str] = r"\s+|\W+"

    def __init__(self) -> None:
        """
        Initialize a new ``Dupe`` instance.
        """
        super().__init__(name="dupe", version="1.3.7")

        self.max_chars: int = 0
        self.skip_chars: int = 0
        self.skip_fields: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="filter matching lines in FILES",
                                         epilog="with no FILES, read standard input", prog=self.name)
        print_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-a", "--adjacent", action="store_true", help="only filter matching adjacent lines")
        parser.add_argument("-b", "--skip-blank", action="store_true", help="avoid comparing blank lines")
        parser.add_argument("-c", "--count", action="store_true", help="prefix lines by the number of occurrences")
        print_group.add_argument("-d", "--repeated", action="store_true",
                                 help="only print duplicate lines, one for each group")
        print_group.add_argument("-D", "--duplicate", action="store_true", help="print all duplicate lines")
        print_group.add_argument("-g", "--group", action="store_true",
                                 help="show all items, separating groups with an empty line")
        print_group.add_argument("-u", "--unique", action="store_true", help="only print unique lines")
        parser.add_argument("-f", "--skip-fields", help="avoid comparing the first N fields (N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-m", "--max-chars", help="compare no more than N characters (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-s", "--skip-chars", help="avoid comparing the first N characters (N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("-w", "--skip-whitespace", action="store_true",
                            help="avoid comparing leading and trailing whitespace")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="colorize counts and file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def get_character_compare_sequence(self, line: str) -> str:
        """
        Return a character sequence derived from the line for comparison.

        :param line: Line to process.
        :return: Character sequence for comparison.
        """
        if self.args.skip_whitespace:  # --skip-whitespace
            line = line.strip()

        if self.args.skip_fields:  # --skip-fields
            line = "".join(re.split(Dupe.FIELD_PATTERN, line)[self.skip_fields:])

        if self.args.max_chars or self.args.skip_chars:  # --max_chars or --skip_chars
            start_index = self.skip_chars
            end_index = start_index + self.max_chars if self.args.max_chars else len(line)

            line = line[start_index:end_index]

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def group_adjacent_matching_lines(self, lines: Iterable[str] | TextIO) -> list[list[str]]:
        """
        Group adjacent lines that match.

        :param lines: Lines to group.
        :return: Lists of lines where the first element is the group and subsequent elements are matching lines.
        """
        group_index = 0
        group_list = []
        previous_line = None

        for line in lines:
            next_line = self.get_character_compare_sequence(line)

            if self.args.skip_blank and (not next_line or next_line == "\n"):  # --skip-blank
                continue

            if previous_line is None:
                group_list.append([line])
            elif next_line == previous_line:
                group_list[group_index].append(line)
            else:
                group_index += 1
                group_list.append([line])

            previous_line = next_line

        return group_list

    def group_all_matching_lines(self, lines: Iterable[str] | TextIO) -> dict[str, list[str]]:
        """
        Group all lines that match.

        :param lines: Lines to group.
        :return: Mapping of lines where the key is the group and the values are matching lines.
        """
        group_map = {}

        for line in lines:
            key = self.get_character_compare_sequence(line)

            if self.args.skip_blank and (not key or key == "\n"):  # --skip-blank
                continue

            if self.args.ignore_case and key in (k.casefold() for k in group_map.keys()):  # --ignore-case
                group_map[key].append(line)
            elif key in group_map:
                group_map[key].append(line)
            else:
                group_map[key] = [line]

        return group_map

    def main(self) -> None:
        """
        Run the primary function of the program.
        """
        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_matching_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_matching_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.print_matching_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_matching_lines_from_files(self.args.files)
        else:
            self.print_matching_lines_from_input()

    def print_file_header(self, file: str) -> None:
        """
        Print the file name, or (standard input) if empty, with a colon.

        :param file: File header to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_matching_lines(self, lines: Iterable[str] | TextIO, *, origin_file) -> None:
        """
        Print lines that match.

        :param lines: Lines to print.
        :param origin_file: File where the lines originated from.
        """
        file_header_printed = False

        # Group matches.
        if self.args.adjacent:
            groups = self.group_adjacent_matching_lines(lines)
        else:
            groups = self.group_all_matching_lines(lines).values()

        # Print groups.
        last_group_index = len(groups) - 1

        for group_index, group in enumerate(groups):
            group_count = len(group)

            for line_index, line in enumerate(group):
                can_print = True
                group_count_str = ""

                if self.args.count:  # --count
                    padding = 7

                    # Only print the group count for the first line.
                    if line_index == 0:
                        if self.print_color:
                            group_count_str = f"{Colors.GROUP_COUNT}{group_count:>{padding},}{Colors.COLON}:{ansi.RESET}"
                        else:
                            group_count_str = f"{group_count:>{padding},}:"
                    else:
                        space = " "
                        group_count_str = f"{space:>{padding}} "

                if self.args.duplicate or self.args.repeated:  # --duplicate or --repeated
                    can_print = group_count > 1
                elif self.args.unique:  # --unique
                    can_print = group_count == 1

                if can_print:
                    if not file_header_printed:
                        self.print_file_header(origin_file)
                        file_header_printed = True

                    io.print_normalized_line(f"{group_count_str}{line}")

                    if not (self.args.duplicate or self.args.group):  # --duplicate or --group
                        break

            if self.args.group and group_index < last_group_index:  # --group
                print()

    def print_matching_lines_from_files(self, files: Iterable[str] | TextIO) -> None:
        """
        Print lines that match from the files.

        :param files: Files to search.
        """
        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_matching_lines(file_info.text, origin_file=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_matching_lines_from_input(self) -> None:
        """
        Print lines that match from standard input until EOF is entered.
        """
        self.print_matching_lines(sys.stdin.read().splitlines(), origin_file="")

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        self.max_chars = self.args.max_chars if self.args.max_chars is not None else 1  # --max-chars
        self.skip_chars = self.args.skip_chars if self.args.skip_chars is not None else 0  # --skip-chars
        self.skip_fields = self.args.skip_fields if self.args.skip_fields is not None else 0  # --skip-fields

        # Validate match values.
        if self.skip_fields < 0:
            self.print_error_and_exit("'skip-fields' must be >= 0")

        if self.skip_chars < 0:
            self.print_error_and_exit("'skip-chars' must be >= 0")

        if self.max_chars < 1:
            self.print_error_and_exit("'max-chars' must be >= 1")


if __name__ == "__main__":
    Dupe().run()
