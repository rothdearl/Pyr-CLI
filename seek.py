#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that searches for files in a directory hierarchy."""

import argparse
import os
import pathlib
import sys
import time
from collections.abc import Iterable
from typing import Final, override

from cli import CLIProgram, CompiledPatterns, ansi, io, patterns, terminal


class Colors:
    """Namespace for terminal color constants."""
    MATCH: Final[str] = ansi.Colors.BRIGHT_RED


class Seek(CLIProgram):
    """
    A program that searches for files in a directory hierarchy.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_any_match: Whether any match was found.
    :ivar name_patterns: Compiled name patterns to match.
    :ivar path_patterns: Compiled path patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize a new ``Seek`` instance."""
        super().__init__(name="seek", version="1.3.15", error_exit_code=2)

        self.found_any_match: bool = False
        self.name_patterns: CompiledPatterns = []
        self.path_patterns: CompiledPatterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="search for files in a directory hierarchy",
                                         epilog="use the current directory as the default starting point",
                                         prog=self.name)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("directories", help="search starting points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching")
        parser.add_argument("-n", "--name", action="extend",
                            help="print files whose names match PATTERN (repeat -n to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-p", "--path", action="extend",
                            help="print files whose paths match PATTERN (repeat -p to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress file error messages")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print files that do not match")
        parser.add_argument("--abs", action="store_true", help="print absolute paths")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="use color for matches (default: on)")
        parser.add_argument("--dot-prefix", action="store_true",
                            help="prefix relative paths with './' (print '.' for current directory)")
        parser.add_argument("--empty-only", action="store_true", help="print only empty files")
        modified_group.add_argument("--mtime-days",
                                    help="print files modified within N days or more than N days ago (use N or -N)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-hours",
                                    help="print files modified within N hours or more than N hours ago (use N or -N)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-mins",
                                    help="print files modified within N minutes or more than N minutes ago (use N or -N)",
                                    metavar="N", type=int)
        parser.add_argument("--max-depth", default=sys.maxsize,
                            help="descend at most N levels below the starting points (N >= 1)", metavar="N", type=int)
        parser.add_argument("--quotes", action="store_true", help="print file paths in double quotes")
        parser.add_argument("--type", choices=("d", "f"), help="print only directories (d) or regular files (f)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_for_errors(self) -> None:
        """Raise ``SystemExit(NO_MATCHES_EXIT_CODE)`` if a match was not found."""
        super().check_for_errors()

        if not self.found_any_match:
            raise SystemExit(Seek.NO_MATCHES_EXIT_CODE)

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        if self.args.max_depth < 1:  # --max-depth
            self.print_error_and_exit("--max-depth must be >= 1")

    def compile_patterns(self) -> None:
        """Compile search patterns."""
        if self.args.name:  # --name
            self.name_patterns = patterns.compile_patterns(self.args.name, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

        if self.args.path:  # --path
            self.path_patterns = patterns.compile_patterns(self.args.path, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

    def file_matches_filters(self, file: pathlib.Path) -> bool:
        """Return whether the file matches all enabled filters."""
        matches_all_filters = True

        try:
            if self.args.type:  # --type
                is_dir = file.is_dir()

                if self.args.type == "d":
                    matches_all_filters = is_dir
                else:
                    matches_all_filters = not is_dir

            if matches_all_filters and self.args.empty_only:  # --empty-only
                if file.is_dir():
                    matches_all_filters = not os.listdir(file)
                else:
                    matches_all_filters = not file.lstat().st_size

            # --mtime-days, --mtime-hours, or --mtime-mins
            if matches_all_filters and any((self.args.mtime_days, self.args.mtime_hours, self.args.mtime_mins)):
                if self.args.mtime_days:
                    last_modified = self.args.mtime_days * 86400  # Convert days to seconds.
                elif self.args.mtime_hours:
                    last_modified = self.args.mtime_hours * 3600  # Convert hours to seconds.
                else:
                    last_modified = self.args.mtime_mins * 60  # Convert minutes to seconds.

                difference = time.time() - file.lstat().st_mtime

                if last_modified < 0:
                    matches_all_filters = difference < abs(last_modified)
                else:
                    matches_all_filters = difference > last_modified
        except PermissionError:
            matches_all_filters = False
            self.print_error(f"{file}: permission denied")

        return matches_all_filters

    def file_matches_patterns(self, file_name: str, file_path: str) -> bool:
        """Return whether the ``file_name`` and ``file_path`` match all provided pattern groups."""
        if not patterns.matches_all_patterns(file_name, self.name_patterns):  # --name
            return False

        if not patterns.matches_all_patterns(file_path, self.path_patterns):  # --path
            return False

        return True

    @override
    def main(self) -> None:
        """Run the program."""
        self.compile_patterns()

        if terminal.stdin_is_redirected():
            self.print_files(sys.stdin)

            if self.args.directories:  # Process any additional directories.
                self.print_files(self.args.directories)
        else:
            self.print_files(self.args.directories or [os.curdir])

    def print_file(self, file: pathlib.Path) -> None:
        """Print the file if it matches the specified search criteria."""
        file_name = file.name or os.curdir  # The dot file has no name component.
        file_path = str(file.parent) if len(file.parts) > 1 else ""  # Do not use the dot file in the path.

        if not file.name and not self.args.dot_prefix:  # Skip the root directory if not --dot-prefix.
            return

        if self.args.max_depth < len(file.parts):  # --max-depth
            return

        # Check if the file matches the search criteria and whether to invert the result.
        matches = self.file_matches_patterns(file_name, file_path) and self.file_matches_filters(file)

        if matches == self.args.invert_match:  # --invert-match
            return

        self.found_any_match = True

        # Exit early if --quiet.
        if self.args.quiet:
            raise SystemExit(0)

        if self.print_color and not self.args.invert_match:  # --invert-match
            file_name = patterns.color_pattern_matches(file_name, self.name_patterns, color=Colors.MATCH)
            file_path = patterns.color_pattern_matches(file_path, self.path_patterns, color=Colors.MATCH)

        if self.args.abs:  # --abs
            if file.name:  # Do not join the current working directory with the dot file.
                path = os.path.join(pathlib.Path.cwd(), file_path, file_name)
            else:
                path = os.path.join(pathlib.Path.cwd(), file_path)
        elif self.args.dot_prefix and file.name:  # Do not join the current directory with the dot file.
            path = os.path.join(os.curdir, file_path, file_name)
        else:
            path = os.path.join(file_path, file_name)

        if self.args.quotes:  # --quotes
            path = f"\"{path}\""

        print(path)

    def print_files(self, directories: Iterable[str]) -> None:
        """Print files that match the specified search criteria in a directory hierarchy."""
        for directory in io.normalize_input_lines(directories):
            if os.path.exists(directory):
                directory_hierarchy = pathlib.Path(directory)

                self.print_file(directory_hierarchy)

                try:
                    for path in directory_hierarchy.rglob("*"):
                        self.print_file(path)
                except PermissionError as error:
                    self.print_error(f"{error.filename}: permission denied")
            else:
                visible_name = directory or '""'  # Use a visible placeholder for empty file names in messages.
                self.print_error(f"{visible_name}: no such file or directory")


if __name__ == "__main__":
    Seek().run()
