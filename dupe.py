#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: dupe.py
Author: Roth Earl
Version: 1.3.10
Description: A program to filter duplicate or unique lines in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from collections.abc import Iterable
from enum import StrEnum
from typing import Final, final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.Colors16.BRIGHT_CYAN
    FILE_NAME = ansi.Colors16.BRIGHT_MAGENTA
    GROUP_COUNT = ansi.Colors16.BRIGHT_GREEN


@final
class Dupe(CLIProgram):
    """
    A program to filter duplicate or unique lines in files.

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
        super().__init__(name="dupe", version="1.3.10")

        self.max_chars: int = 0
        self.skip_chars: int = 0
        self.skip_fields: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="filter duplicate or unique lines in FILES",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)
        print_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-a", "--adjacent", action="store_true", help="compare only adjacent lines")
        parser.add_argument("-c", "--count", action="store_true", help="prefix lines with the number of occurrences")
        print_group.add_argument("-d", "--repeated", action="store_true",
                                 help="print only duplicate lines, one per group")
        print_group.add_argument("-D", "--all-repeated", action="store_true", help="print all duplicate lines")
        print_group.add_argument("-g", "--group", action="store_true",
                                 help="show all lines, separating groups with an empty line")
        print_group.add_argument("-u", "--unique", action="store_true", help="only print unique lines")
        parser.add_argument("-f", "--skip-fields", help="skip the first N fields when comparing (N >= 0)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="do not prefix output with file names")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-m", "--max-chars", help="compare no more than N characters (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-s", "--skip-chars", help="skip the first N characters when comparing (N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("-w", "--skip-whitespace", action="store_true",
                            help="skip leading and trailing whitespace when comparing")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names and counts (default: on)")
        parser.add_argument("--count-width", default=4, help="pad occurrence counts to width N (default: 4; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--no-blank", action="store_true", help="suppress all blank lines")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def can_group_key(self, key: str) -> bool:
        """
        Return whether the key can be grouped.

        :param key: The key to check.
        :return: ``True`` if the key is non-empty, or if blank keys are allowed.
        """
        return not self.args.no_blank or key.strip()  # --no-blank

    def get_compare_key(self, line: str) -> str:
        """
        Return a normalized comparison key derived from the line, applying rules according to command-line options.

        :param line: Line to process.
        :return: Normalized comparison key.
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

    def group_adjacent_matching_lines(self, lines: Iterable[str]) -> list[list[str]]:
        """
        Group adjacent lines whose comparison keys match.

        :param lines: Lines to group.
        :return: List of string groups, where the first element is the group and the remaining elements are matches.
        """
        group_index = 0
        group_list = []
        previous_line = None

        for line in lines:
            next_line = self.get_compare_key(line)

            if not self.can_group_key(next_line):
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

    def group_lines_by_key(self, lines: Iterable[str]) -> dict[str, list[str]]:
        """
        Group all lines globally by their comparison keys.

        :param lines: Lines to group.
        :return: Mapping of string groups, where the key is the group and the value is a list of matches.
        """
        group_map = {}

        for line in lines:
            key = self.get_compare_key(line)

            if not self.can_group_key(key):
                continue

            if key in group_map:
                group_map[key].append(line)
            else:
                group_map[key] = [line]

        return group_map

    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_grouped_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_grouped_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.print_grouped_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_grouped_lines_from_files(self.args.files)
        else:
            self.print_grouped_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name, or "(standard input)" if empty, with a colon.

        :param file_name: File name to print.
        """
        if not self.args.no_file_name:  # --no-file-name
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_grouped_lines(self, lines: Iterable[str], *, origin_file) -> None:
        """
        Print lines using rules specified by command-line arguments.

        :param lines: Lines to print.
        :param origin_file: File where the lines originated from.
        """
        file_header_printed = False

        # Group matches.
        if self.args.adjacent:  # --adjacent
            groups = self.group_adjacent_matching_lines(lines)
        else:
            groups = self.group_lines_by_key(lines).values()

        # Print groups.
        last_group_index = len(groups) - 1

        for group_index, group in enumerate(groups):
            group_count = len(group)

            for line_index, line in enumerate(group):
                can_print = True
                group_count_str = ""

                if self.args.count:  # --count
                    # Only print the group count for the first line.
                    if line_index == 0:
                        if self.print_color:
                            group_count_str = f"{Colors.GROUP_COUNT}{group_count:>{self.args.count_width},}{Colors.COLON}:{ansi.RESET}"
                        else:
                            group_count_str = f"{group_count:>{self.args.count_width},}:"
                    else:
                        space = " "
                        group_count_str = f"{space:>{self.args.number_width}} "

                if self.args.all_repeated or self.args.repeated:  # --all-repeated or --repeated
                    can_print = group_count > 1
                elif self.args.unique:  # --unique
                    can_print = group_count == 1

                if can_print:
                    if not file_header_printed:
                        self.print_file_header(origin_file)
                        file_header_printed = True

                    io.print_line_normalized(f"{group_count_str}{line}")

                    if not (self.args.all_repeated or self.args.group):  # --all-repeated or --group
                        break

            if self.args.group and group_index < last_group_index:  # --group
                print()

    def print_grouped_lines_from_files(self, files: Iterable[str]) -> None:
        """
        Print lines from files using rules specified by command-line arguments.

        :param files: Files to print lines from.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_grouped_lines(file_info.text, origin_file=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_grouped_lines_from_input(self) -> None:
        """
        Print lines from standard input until EOF using rules specified by command-line arguments.
        """
        self.print_grouped_lines(sys.stdin.read().splitlines(), origin_file="")

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        self.max_chars = self.args.max_chars if self.args.max_chars is not None else 1  # --max-chars
        self.skip_chars = self.args.skip_chars if self.args.skip_chars is not None else 0  # --skip-chars
        self.skip_fields = self.args.skip_fields if self.args.skip_fields is not None else 0  # --skip-fields

        if self.args.count_width < 1:  # --count-width
            self.print_error_and_exit("'count-width' must be >= 1")

        if self.max_chars < 1:
            self.print_error_and_exit("'max-chars' must be >= 1")

        if self.skip_chars < 0:
            self.print_error_and_exit("'skip-chars' must be >= 0")

        if self.skip_fields < 0:
            self.print_error_and_exit("'skip-fields' must be >= 0")


if __name__ == "__main__":
    Dupe().run()
