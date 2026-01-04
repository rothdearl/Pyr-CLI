#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: distinct.py
Author: Roth Earl
Version: 1.3.0
Description: A program to filter matching lines in files.
License: GNU GPLv3
"""

import argparse
import os
import re
import sys
from typing import Final, TextIO, final

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = ConsoleColors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ConsoleColors.BRIGHT_MAGENTA
    GROUP_COUNT: Final[str] = ConsoleColors.BRIGHT_GREEN


@final
class Main(CLIProgram):
    """
    A program to filter matching lines in files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="distinct", version="1.3.0")

        self.FIELD_PATTERN: Final[str] = r"\s+|\W+"
        self.max_chars: int = 0
        self.skip_chars: int = 0
        self.skip_fields: int = 0

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="filter matching lines in FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)
        print_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="files to filter", metavar="FILES", nargs="*")
        parser.add_argument("-a", "--adjacent", action="store_true", help="only filter matching adjacent lines")
        parser.add_argument("-b", "--skip-blank", action="store_true", help="avoid comparing blank lines")
        parser.add_argument("-c", "--count", action="store_true", help="prefix lines by the number of occurrences")
        print_group.add_argument("-d", "--repeated", action="store_true",
                                 help="only print duplicate lines, one for each group")
        print_group.add_argument("-D", "--duplicate", action="store_true", help="print all duplicate lines")
        print_group.add_argument("-g", "--group", action="store_true",
                                 help="show all items, separating groups with an empty line")
        print_group.add_argument("-u", "--unique", action="store_true", help="only print unique lines")
        parser.add_argument("-f", "--skip-fields", help="avoid comparing the first N fields", metavar="N", type=int)
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the file name header on output")
        parser.add_argument("-i", "--ignore-case", action="store_true",
                            help="ignore differences in case when comparing")
        parser.add_argument("-m", "--max-chars", help="compare no more than N+ characters", metavar="N+", type=int)
        parser.add_argument("-s", "--skip-chars", help="avoid comparing the first N characters", metavar="N", type=int)
        parser.add_argument("-w", "--skip-whitespace", action="store_true",
                            help="avoid comparing leading and trailing whitespace")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="display the counts and file headers in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--pipe", action="store_true", help="read input from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def filter_matching_lines(self, lines: TextIO | list[str], *, origin_file) -> None:
        """
        Filters lines that match.
        :param lines: The lines.
        :param origin_file: The file where the lines originated from.
        :return: None
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
                    width = 7

                    # Only print the group count for the first line.
                    if line_index == 0:
                        if self.print_color:
                            group_count_str = f"{Colors.GROUP_COUNT}{group_count:>{width},}{Colors.COLON}:{ConsoleColors.RESET}"
                        else:
                            group_count_str = f"{group_count:>{width},}:"
                    else:
                        space = " "
                        group_count_str = f"{space:>{width}} "

                if self.args.duplicate or self.args.repeated:  # --duplicate or --repeated
                    can_print = group_count > 1
                elif self.args.unique:  # --unique
                    can_print = group_count == 1

                if can_print:
                    if not file_header_printed:
                        self.print_file_header(origin_file)
                        file_header_printed = True

                    CLIProgram.print_line(f"{group_count_str}{line}")

                    if not (self.args.duplicate or self.args.group):  # --duplicate or --group
                        break

            if self.args.group and group_index < last_group_index:  # --group
                print()

    def filter_matching_lines_from_files(self, files: TextIO | list[str]) -> None:
        """
        Filters lines that match from files.
        :param files: The files.
        :return: None
        """
        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.filter_matching_lines(text, origin_file=file)
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

    def filter_matching_lines_from_input(self) -> None:
        """
        Filters lines that match from standard input until EOF is entered.
        :return: None
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(input())
            except EOFError:
                eof = True

        self.filter_matching_lines(lines, origin_file="")

    def get_character_compare_sequence(self, line: str) -> str:
        """
        Returns the character sequence from the line to use for comparing.
        :param line: The line.
        :return: The character sequence to use for comparing.
        """
        if self.args.skip_whitespace:  # --skip-whitespace
            line = line.strip()

        if self.args.skip_fields:  # --skip-fields
            line = "".join(re.split(self.FIELD_PATTERN, line)[self.skip_fields:])

        if self.args.max_chars or self.args.skip_chars:  # --max_chars or --skip_chars
            start_index = self.skip_chars
            end_index = start_index + self.max_chars if self.args.max_chars else len(line)

            line = line[start_index:end_index]

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def group_adjacent_matching_lines(self, lines: TextIO | list[str]) -> list[list[str]]:
        """
        Groups adjacent lines that match.
        :param lines: The lines.
        :return: A list of lines where the first element is the group and the remaining elements are the matching lines.
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

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        self.set_match_info_values()

        # Set --no-file-header to True if there are no files and --pipe=False.
        if not self.args.files and not self.args.pipe:
            self.args.no_file_header = True

        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
                self.filter_matching_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.filter_matching_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.filter_matching_lines_from_files(self.args.files)
        elif self.args.files:
            self.filter_matching_lines_from_files(self.args.files)
        else:
            self.filter_matching_lines_from_input()

    def group_all_matching_lines(self, lines: TextIO | list[str]) -> dict[str, list[str]]:
        """
        Groups all lines that match.
        :param lines: The lines.
        :return: A mapping of lines where the key is the group and the values are the matching lines.
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

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.
        :param file: The file.
        :return: None
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ConsoleColors.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def set_match_info_values(self) -> None:
        """
        Sets the values to use for matching lines.
        :return: None
        """
        self.max_chars = 1 if not self.args.max_chars else self.args.max_chars  # --max-chars
        self.skip_chars = 0 if not self.args.skip_chars else self.args.skip_chars  # --skip-chars
        self.skip_fields = 0 if not self.args.skip_fields else self.args.skip_fields  # --skip-fields

        # Validate the match values.
        if self.skip_fields < 0:
            self.log_error(f"skip fields ({self.skip_fields}) cannot be less than 0", raise_system_exit=True)

        if self.skip_chars < 0:
            self.log_error(f"skip characters ({self.skip_chars}) cannot be less than 0", raise_system_exit=True)

        if self.max_chars < 1:
            self.log_error(f"max characters ({self.max_chars}) cannot be less than 1", raise_system_exit=True)


if __name__ == "__main__":
    CLIProgram.run(Main())
