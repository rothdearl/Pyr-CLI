#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that filters duplicate or unique lines from files."""

import argparse
import sys
from collections.abc import Iterable
from typing import Final, override

from cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    GROUP_COUNT: Final[str] = ansi.Colors.BRIGHT_GREEN


class Dupe(TextProgram):
    """A program that filters duplicate or unique lines from files."""

    def __init__(self) -> None:
        """Initialize a new ``Dupe`` instance."""
        super().__init__(name="dupe", version="1.4.2")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="find and filter duplicate lines in FILES",
                                         epilog="read standard input when no FILES are specified", prog=self.name)
        print_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        print_group.add_argument("-d", "--repeated", action="store_true", help="print one duplicate line per group")
        print_group.add_argument("-D", "--all-repeated", action="store_true",
                                 help="print all duplicate lines per group")
        print_group.add_argument("-g", "--group", action="store_true",
                                 help="print all lines, grouping identical lines and separating groups with an empty line")
        print_group.add_argument("-u", "--unique", action="store_true", help="print unique lines only")
        parser.add_argument("-c", "--count", action="store_true", help="prefix lines with the number of occurrences")
        parser.add_argument("--count-width", default=4, help="pad occurrence counts to width N (default: 4; N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-a", "--adjacent", action="store_true",
                            help="compare adjacent lines only (do not search entire file)")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when comparing")
        parser.add_argument("--ignore-blank", action="store_true", help="ignore blank lines")
        parser.add_argument("-f", "--skip-fields", help="skip the first N non-empty fields when comparing (N >= 1)",
                            metavar="N", type=int)
        parser.add_argument("--field-separator",
                            help="split lines into fields using SEP (default: <space>; use with --skip-fields)",
                            metavar="SEP")
        parser.add_argument("-s", "--skip-chars", help="skip the first N characters when comparing (N >= 0)",
                            metavar="N", type=int)
        parser.add_argument("-m", "--max-chars", help="compare at most N characters (N >= 1)", metavar="N", type=int)
        parser.add_argument("-w", "--skip-whitespace", action="store_true",
                            help="ignore leading and trailing whitespace when comparing")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names and counts (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def can_group_key(self, key: str) -> bool:
        """Return whether the key should participate in grouping (optionally ignoring blank keys)."""
        return not self.args.ignore_blank or key.strip()

    @override
    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        # --field-separator is only meaningful with --skip-fields.
        if self.args.field_separator is not None and self.args.skip_fields is None:
            self.print_error_and_exit("--field-separator is only used with --skip-fields")

    def get_compare_key(self, line: str) -> str:
        """Return a normalized comparison key derived from the line, applying rules according to command-line options."""
        compare_key = line

        if self.args.skip_whitespace:
            compare_key = compare_key.strip()

        if self.args.skip_fields:
            separator = self.args.field_separator or " "

            compare_key = text.split_csv(compare_key, separator=separator, on_error=self.print_error_and_exit)
            compare_key = separator.join(compare_key[self.args.skip_fields:])

        if self.args.max_chars or self.args.skip_chars:
            start_index = self.args.skip_chars or 0
            end_index = start_index + self.args.max_chars if self.args.max_chars else len(line)

            compare_key = compare_key[start_index:end_index]

        if self.args.ignore_case:
            compare_key = compare_key.casefold()

        return compare_key

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
        if self.args.adjacent:
            groups = self.group_adjacent_matching_lines(lines)
        else:
            groups = self.group_lines_by_key(lines).values()

        # Print groups.
        printed_group_count = 0

        for group in groups:
            group_count = len(group)

            if self.args.group and printed_group_count:
                print()

            for line_index, line in enumerate(group):
                can_print = True
                group_count_str = ""

                if self.args.count:
                    # Only print the group count for the first line.
                    if line_index == 0:
                        if self.print_color:
                            group_count_str = f"{Colors.GROUP_COUNT}{group_count:>{self.args.count_width},}{Colors.COLON}:{ansi.RESET}"
                        else:
                            group_count_str = f"{group_count:>{self.args.count_width},}:"
                    else:
                        empty_space = " "  # Ensure lines align.

                        group_count_str = f"{empty_space:>{self.args.count_width}} "

                if self.args.all_repeated or self.args.repeated:
                    can_print = group_count > 1
                elif self.args.unique:
                    can_print = group_count == 1

                if can_print:
                    if not file_header_printed:
                        self.print_file_header(origin_file)
                        file_header_printed = True

                    print(f"{group_count_str}{line}")
                    printed_group_count += 1

                    if not (self.args.all_repeated or self.args.group):
                        break

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
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.group_and_print_lines(file_info.text_stream, origin_file=file_info.file_name)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            else:
                if standard_input := sys.stdin.readlines():
                    self.group_and_print_lines(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.group_and_print_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the rendered file header for ``file_name``."""
        if self.should_print_file_header():
            print(self.render_file_header(file_name, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON))

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.count_width < 1:
            self.print_error_and_exit("--count-width must be >= 1")

        if self.args.max_chars is not None and self.args.max_chars < 1:
            self.print_error_and_exit("--max-chars must be >= 1")

        if self.args.skip_chars is not None and self.args.skip_chars < 0:
            self.print_error_and_exit("--skip-chars must be >= 0")

        if self.args.skip_fields is not None and self.args.skip_fields < 1:
            self.print_error_and_exit("--skip-fields must be >= 1")


if __name__ == "__main__":
    Dupe().run()
