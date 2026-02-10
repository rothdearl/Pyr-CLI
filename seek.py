#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: seek.py
Author: Roth Earl
Version: 1.3.14
Description: A program that searches for files in a directory hierarchy.
License: GNU GPLv3
"""

import argparse
import os
import pathlib
import sys
import time
from typing import Final, override

from cli import CLIProgram, Patterns, ansi, patterns, terminal


class Colors:
    """Namespace for terminal color constants."""
    MATCH: Final[str] = ansi.Colors.BRIGHT_RED


class Seek(CLIProgram):
    """
    A program that searches for files in a directory hierarchy.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_match: Whether a match was found.
    :ivar name_patterns: Compiled name patterns to match.
    :ivar path_patterns: Compiled path patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize a new ``Seek`` instance."""
        super().__init__(name="seek", version="1.3.14", error_exit_code=2)

        self.found_match: bool = False
        self.name_patterns: Patterns = []
        self.path_patterns: Patterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="search for files in a directory hierarchy",
                                         epilog="use the current directory as the default starting point",
                                         prog=self.name)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("directories", help="search starting points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when comparing")
        parser.add_argument("-n", "--name", action="extend", help="print files with names matching PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-p", "--path", action="extend", help="print files with paths matching PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress file error messages")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print files that do not match")
        parser.add_argument("--abs", action="store_true", help="print absolute paths")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="use color for matches (default: on)")
        parser.add_argument("--dot", action="store_true", help="include dot (.) files in output")
        parser.add_argument("--empty-only", action="store_true", help="print only empty files")
        modified_group.add_argument("--mtime-days",
                                    help="print files modified less than or more than N days ago (use +N or -N)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-hours",
                                    help="print files modified less than or more than N hours ago (use +N or -N)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-mins",
                                    help="print files modified less than or more than N minutes ago (use +N or -N)",
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

        if not self.found_match:
            SystemExit(Seek.NO_MATCHES_EXIT_CODE)

    @override
    def check_parsed_arguments(self) -> None:
        """Validate parsed command-line arguments."""
        if self.args.max_depth < 1:  # --max-depth
            self.print_error_and_exit("--max-depth must be >= 1")

    def file_matches_filters(self, file: pathlib.Path) -> bool:
        """Check whether the file matches any of the filters."""
        matches_filters = True

        try:
            if self.args.type:  # --type
                is_dir = file.is_dir()

                if self.args.type == "d":
                    matches_filters = is_dir
                else:
                    matches_filters = not is_dir

            if matches_filters and self.args.empty_only:  # --empty-only
                if file.is_dir():
                    matches_filters = not os.listdir(file)
                else:
                    matches_filters = not file.lstat().st_size

            # --mtime-days, --mtime-hours, or --mtime-mins
            if matches_filters and any((self.args.mtime_days, self.args.mtime_hours, self.args.mtime_mins)):
                if self.args.mtime_days:
                    last_modified = self.args.mtime_days * 86400  # Convert seconds to days.
                elif self.args.mtime_hours:
                    last_modified = self.args.mtime_hours * 3600  # Convert seconds to hours.
                else:
                    last_modified = self.args.mtime_mins * 60  # Convert seconds to minutes.

                difference = time.time() - file.lstat().st_mtime

                if last_modified < 0:
                    matches_filters = difference < abs(last_modified)
                else:
                    matches_filters = difference > last_modified
        except PermissionError:
            matches_filters = False
            self.print_error(f"{file}: permission denied")

        return matches_filters

    def file_matches_patterns(self, file_name: str, file_path: str) -> bool:
        """Return whether the file name and file path match their patterns."""
        if not patterns.matches_all_patterns(file_name, self.name_patterns):  # --name
            return False

        if not patterns.matches_all_patterns(file_path, self.path_patterns):  # --path
            return False

        return True

    @override
    def main(self) -> None:
        """Run the program."""
        self.precompile_patterns()

        if terminal.stdin_is_redirected():
            self.print_files(sys.stdin)

            if self.args.directories:  # Process any additional directories.
                self.print_files(self.args.directories)
        else:
            self.print_files(self.args.directories or [os.curdir])

    def precompile_patterns(self) -> None:
        """Pre-compile search patterns."""
        if self.args.name:  # --name
            self.name_patterns = patterns.compile_patterns(self.args.name, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

        if self.args.path:  # --path
            self.path_patterns = patterns.compile_patterns(self.args.path, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

    def print_file(self, file: pathlib.Path) -> None:
        """Print the file if it matches the specified search criteria."""
        file_name = file.name or os.curdir  # The dot file does not have a file name.
        file_path = str(file.parent) if len(file.parts) > 1 else ""  # Do not use the dot file in the path.

        if not file.name and not self.args.dot:  # Skip the dot file if not --dot.
            return

        if self.args.max_depth < len(file.parts):  # --max-depth
            return

        # Check if the file matches the search criteria and whether to invert the result:
        matches = self.file_matches_patterns(file_name, file_path) and self.file_matches_filters(file)

        if matches == self.args.invert_match:  # --invert-match
            return

        self.found_match = True

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
        elif self.args.dot and file.name:  # Do not join the current directory with the dot file.
            path = os.path.join(os.curdir, file_path, file_name)
        else:
            path = os.path.join(file_path, file_name)

        if self.args.quotes:  # --quotes
            path = f"\"{path}\""

        print(path)

    def print_files(self, directory_root: str) -> None:
        """Print files that match the specified search criteria in a directory hierarchy."""
        for directory in directory_root:
            if os.path.exists(directory):
                directory_hierarchy = pathlib.Path(directory)

                self.print_file(directory_hierarchy)

                try:
                    for file_name in directory_hierarchy.rglob("*"):
                        self.print_file(file_name)
                except PermissionError as error:
                    self.print_error(f"{error.filename}: permission denied")
            else:
                visible_name = directory or '""'  # Use a visible placeholder for empty file names in messages.
                self.print_error(f"{visible_name}: no such file or directory")


if __name__ == "__main__":
    Seek().run()
