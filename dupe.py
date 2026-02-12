#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that filters duplicate or unique lines from files."""

import argparse
import csv
import os
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    GROUP_COUNT: Final[str] = ansi.Colors.BRIGHT_GREEN


class Dupe(CLIProgram):
    """
    A program that filters duplicate or unique lines from files.

    :ivar use_csv_for_skip_fields: Whether to use CSV when skipping fields.
    """

    def __init__(self) -> None:
        """Initialize a new ``Dupe`` instance."""
        super().__init__(name="dupe", version="1.3.15")

        self.use_csv_for_skip_fields: bool = False

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="find and filter duplicate lines in FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        print_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-a", "--adjacent", action="store_true",
                            help="compare adjacent lines only (do not search entire file)")
        parser.add_argument("-c", "--count", action="store_true", help="prefix lines with the number of occurrences")
        print_group.add_argument("-d", "--repeated", action="store_true", help="print one duplicate line per group")
        print_group.add_argument("-D", "--all-repeated", action="store_true",
                                 help="print all duplicate lines per group")
        print_group.add_argument("-g", "--group", action="store_true",
                                 help="show all lines, separating each group with an empty line")
        print_group.add_argument("-u", "--unique", action="store_true", help="print unique lines only")
        parser.add_argument("-f", "--skip-fields",
                            help="skip the first N fields when comparing (empty fields count; N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when comparing")
        parser.add_argument("-m", "--max-chars", help="compare at most N characters (N >= 1)", metavar="N", type=int)
        parser.add_argument("-s", "--skip-chars", help="skip the first N characters when comparing (N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("-w", "--skip-whitespace", action="store_true",
                            help="ignore leading and trailing whitespace when comparing")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names and counts (default: on)")
        parser.add_argument("--count-width", default=4, help="pad occurrence counts to width N (default: 4; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--field-separator", default=" ",
                            help="split lines into fields using SEP (default: <space>; used with --skip-fields)",
                            metavar="SEP")
        parser.add_argument("--ignore-blank", action="store_true", help="ignore blank lines")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def can_group_key(self, key: str) -> bool:
        """Return whether the key should participate in grouping (optionally ignoring blank keys)."""
        return not self.args.ignore_blank or key.strip()  # --ignore-blank

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        if self.args.count_width < 1:  # --count-width
            self.print_error_and_exit("--count-width must be >= 1")

        if self.args.max_chars is not None and self.args.max_chars < 1:  # --max-chars
            self.print_error_and_exit("--max-chars must be >= 1")

        if self.args.skip_chars is not None and self.args.skip_chars < 0:  # --skip-chars
            self.print_error_and_exit("--skip-chars must be >= 0")

        if self.args.skip_fields is not None and self.args.skip_fields < 1:  # --skip-fields
            self.print_error_and_exit("--skip-fields must be >= 1")

        # Decode escape sequences in --field-separator and determine whether to skip fields using CSV.
        try:
            self.args.field_separator = self.args.field_separator.encode().decode("unicode_escape")
        except UnicodeDecodeError:
            self.print_error_and_exit("--field-separator contains an invalid escape sequence")

        self.use_csv_for_skip_fields = len(self.args.field_separator) == 1 and self.args.field_separator != '"'

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def get_compare_key(self, line: str) -> str:
        """Return a normalized comparison key derived from the line, applying rules according to command-line options."""
        if self.args.skip_whitespace:  # --skip-whitespace
            line = line.strip()

        if self.args.skip_fields:  # --skip-fields
            if self.use_csv_for_skip_fields:
                fields = next(csv.reader([line], delimiter=self.args.field_separator))
            else:
                fields = line.split(self.args.field_separator)

            line = self.args.field_separator.join(fields[self.args.skip_fields:])

        if self.args.max_chars or self.args.skip_chars:  # --max-chars or --skip-chars
            start_index = self.args.skip_chars or 0
            end_index = start_index + self.args.max_chars if self.args.max_chars else len(line)

            line = line[start_index:end_index]

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def group_adjacent_matching_lines(self, lines: Iterable[str]) -> list[list[str]]:
        """Return groups of adjacent lines that share the same comparison key, preserving input order."""
        groups = []
        previous_key = None

        for line in io.normalize_input_lines(lines):
            next_key = self.get_compare_key(line)

            if not self.can_group_key(next_key):
                continue

            if next_key != previous_key:
                groups.append([])

            groups[-1].append(line)  # Always append to the last group.
            previous_key = next_key

        return groups

    def group_and_print_lines(self, lines: Iterable[str], *, origin_file: str) -> None:
        """Group and print lines to standard output according to command-line arguments."""
        file_header_printed = False

        # Group matches.
        if self.args.adjacent:  # --adjacent
            groups = self.group_adjacent_matching_lines(lines)
        else:
            groups = self.group_lines_by_key(lines).values()

        # Print groups.
        printed_group_count = 0

        for group in groups:
            group_count = len(group)

            if self.args.group and printed_group_count:  # --group
                print()

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
                        empty_space = " "  # Ensure lines align.

                        group_count_str = f"{empty_space:>{self.args.count_width}} "

                if self.args.all_repeated or self.args.repeated:  # --all-repeated or --repeated
                    can_print = group_count > 1
                elif self.args.unique:  # --unique
                    can_print = group_count == 1

                if can_print:
                    if not file_header_printed:
                        self.print_file_header(origin_file)
                        file_header_printed = True

                    print(f"{group_count_str}{line}")
                    printed_group_count += 1

                    if not (self.args.all_repeated or self.args.group):  # --all-repeated or --group
                        break

    def group_and_print_lines_from_files(self, files: Iterable[str]) -> None:
        """Read and print lines from each file."""
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.group_and_print_lines(file_info.text_stream, origin_file=file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def group_and_print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        self.group_and_print_lines(sys.stdin, origin_file="")

    def group_lines_by_key(self, lines: Iterable[str]) -> dict[str, list[str]]:
        """Return a mapping from comparison key to the lines that match that key."""
        group_map = {}

        for line in io.normalize_input_lines(lines):
            key = self.get_compare_key(line)

            if not self.can_group_key(key):
                continue

            if key in group_map:
                group_map[key].append(line)
            else:
                group_map[key] = [line]

        return group_map

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.group_and_print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.group_and_print_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.group_and_print_lines_from_files(self.args.files)
        elif self.args.files:
            self.group_and_print_lines_from_files(self.args.files)
        else:
            self.group_and_print_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)


if __name__ == "__main__":
    Dupe().run()
