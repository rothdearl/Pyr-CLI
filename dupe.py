#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that filters duplicate or unique lines from files."""

import argparse
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
    """A program that filters duplicate or unique lines from files."""

    def __init__(self) -> None:
        """Initialize a new ``Dupe`` instance."""
        super().__init__(name="dupe", version="1.3.15")

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
        parser.add_argument("-f", "--skip-fields", help="skip the first N non-empty fields when comparing (N >= 1)",
                            metavar="N", type=int)
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
                            help="split lines into fields using SEP (default: <space>; affects --skip-fields)",
                            metavar="SEP")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--no-blank", action="store_true", help="suppress blank lines")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def can_group_key(self, key: str) -> bool:
        """Return whether the key is non-empty, or if blank keys are allowed."""
        return not self.args.no_blank or key.strip()  # --no-blank

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        if self.args.count_width < 1:  # --count-width
            self.print_error_and_exit("--count-width must be >= 1")

        if self.args.max_chars is not None and self.args.max_chars < 1:  # --max-chars
            self.print_error_and_exit("--max-chars must be >= 1")

        if self.args.skip_chars is not None and self.args.skip_chars < 0:  # --skip-chars
            self.print_error_and_exit("--skip-chars must be >= 0")

        if self.args.skip_fields is not None and self.args.skip_fields < 1:  # --skip-fields
            self.print_error_and_exit("--skip-fields must be >= 1")

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def get_compare_key(self, line: str) -> str:
        """Return a normalized comparison key derived from the line, applying rules according to command-line options."""
        if self.args.skip_whitespace:  # --skip-whitespace
            line = line.strip()

        if self.args.skip_fields:  # --skip-fields
            fields = [field for field in line.split(self.args.field_separator) if field]  # Collect non-empty fields.

            line = self.args.field_separator.join(fields[self.args.skip_fields:])

        if self.args.max_chars or self.args.skip_chars:  # --max_chars or --skip_chars
            start_index = self.args.skip_chars or 0
            end_index = start_index + self.args.max_chars if self.args.max_chars else len(line)

            line = line[start_index:end_index]

        if self.args.ignore_case:  # --ignore-case
            line = line.casefold()

        return line

    def group_adjacent_matching_lines(self, lines: Iterable[str]) -> list[list[str]]:
        """Return a list of groups, where the first element is the group and the remaining elements are matches."""
        group_index = 0
        group_list = []
        previous_line = None

        for line in io.normalize_input_lines(lines):
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

    def group_and_print_lines(self, lines: Iterable[str], *, origin_file: str) -> None:
        """Group and print lines to standard output according to command-line arguments."""
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

                    if not (self.args.all_repeated or self.args.group):  # --all-repeated or --group
                        break

            if self.args.group and group_index < last_group_index:  # --group
                print()

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
        """Return a mapping of string groups, where the key is the group and the value is a list of matches."""
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
