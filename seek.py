#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: seek.py
Author: Roth Earl
Version: 1.3.5
Description: A program to search for files in a directory hierarchy.
License: GNU GPLv3
"""

import argparse
import os
import pathlib
import sys
import time
from enum import StrEnum
from typing import final

from cli import CLIProgram, CompiledPatterns, colors, patterns, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    MATCH = colors.BRIGHT_RED


@final
class Seek(CLIProgram):
    """
    A program to search for files in a directory hierarchy.

    :ivar bool found_match: Whether a match was found.
    :ivar CompiledPatterns name_patterns: Compiled name patterns to match.
    :ivar CompiledPatterns path_patterns: Compiled path patterns to match.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="seek", version="1.3.5", error_exit_code=2)

        self.found_match: bool = False
        self.name_patterns: CompiledPatterns = []
        self.path_patterns: CompiledPatterns = []

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="search for files in a directory hierarchy",
                                         epilog="default starting point is the current directory", prog=self.name)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("dirs", help="directory starting points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching patterns")
        parser.add_argument("-n", "--name", action="extend", help="print files whose names match PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-p", "--path", action="extend", help="print files whose paths match PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("-v", "--invert-match", action="store_true",
                            help="print files that do not match the specified criteria")
        parser.add_argument("--abs", action="store_true", help="print absolute file paths")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="colorize matches (default: on)")
        parser.add_argument("--dot", action="store_true", help="include dot (.) files in output")
        parser.add_argument("--empty", choices=("y", "n"), help="print only empty files")
        modified_group.add_argument("--m-days", help="print files modified less than or more than N days ago",
                                    metavar="N", type=int)
        modified_group.add_argument("--m-hours", help="print files modified less than or more than N hours ago",
                                    metavar="N", type=int)
        modified_group.add_argument("--m-mins", help="print files modified less than or more than N minutes ago",
                                    metavar="N", type=int)
        parser.add_argument("--max-depth", default=sys.maxsize,
                            help="descend at most N levels below the starting points (N >= 1)", metavar="N", type=int)
        parser.add_argument("--quotes", action="store_true", help="print file paths enclosed in double quotes")
        parser.add_argument("--type", choices=("d", "f"), help="print only directories (d) or regular files (f)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def check_for_errors(self) -> None:
        """
        Raises a SystemExit if there are any errors.

        :raises SystemExit: Request to exit from the interpreter if there are any errors.
        """
        super().check_for_errors()

        if not self.found_match:
            raise SystemExit(1)

    def file_matches_filters(self, file: pathlib.Path) -> bool:
        """
        Returns whether the file matches any of the filters.

        :param file: File to check.
        :return: True or False.
        """
        matches_filters = True

        try:
            if self.args.type:  # --type
                is_dir = file.is_dir()

                if self.args.type == "d":
                    matches_filters = is_dir
                else:
                    matches_filters = not is_dir

            if matches_filters and self.args.empty:  # --empty
                if file.is_dir():
                    matches_filters = not os.listdir(file)
                else:
                    matches_filters = not file.lstat().st_size

                if self.args.empty == "n":
                    matches_filters = not matches_filters

            # --m-days, --m-hours, or --m-mins
            if matches_filters and any((self.args.m_days, self.args.m_hours, self.args.m_mins)):
                if self.args.m_days:
                    last_modified = self.args.m_days * 86400  # Convert seconds to days.
                elif self.args.m_hours:
                    last_modified = self.args.m_hours * 3600  # Convert seconds to hours.
                else:
                    last_modified = self.args.m_mins * 60  # Convert seconds to minutes.

                difference = time.time() - file.lstat().st_mtime

                if last_modified < 0:
                    matches_filters = difference < abs(last_modified)
                else:
                    matches_filters = difference > last_modified
        except PermissionError:
            matches_filters = False
            self.print_error(f"{file}: permission denied")

        return matches_filters

    def main(self) -> None:
        """
        Runs the primary function of the program.
        """
        # Pre-compile patterns.
        if self.args.name:  # --name
            self.name_patterns = patterns.compile_patterns(self.args.name, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

        if self.args.path:  # --path
            self.path_patterns = patterns.compile_patterns(self.args.path, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

        if terminal.input_is_redirected():
            for directory in sys.stdin:
                self.print_files(directory.rstrip())

            if self.args.dirs:  # Process any additional directories.
                for directory in self.args.dirs:
                    self.print_files(directory)
        else:
            dirs = self.args.dirs if self.args.dirs else [os.curdir]

            for directory in dirs:
                self.print_files(directory)

    def print_file(self, file: pathlib.Path) -> None:
        """
        Prints the file.

        :param file: File to print.
        """
        filename = file.name or os.curdir  # The dot file does not have a file name.
        file_path = str(file.parent) if len(file.parts) > 1 else ""  # Do not use the dot file in the path.

        if not file.name and not self.args.dot:  # Skip the dot file if not --dot.
            return

        if self.args.max_depth < len(file.parts):  # --max-depth
            return

        if not patterns.text_has_patterns(filename, self.name_patterns) != self.args.invert_match:
            return

        if not patterns.text_has_patterns(file_path, self.path_patterns) != self.args.invert_match:
            return

        if not self.file_matches_filters(file):  # --type, --empty, --m-days, --m-hours, or --m-mins
            return

        self.found_match = True

        # If --quiet, exit on first match for performance.
        if self.args.quiet:
            raise SystemExit(0)

        if self.print_color and not self.args.invert_match:  # --invert-match
            filename = patterns.color_patterns_in_text(filename, self.name_patterns,
                                                       color=Colors.MATCH) if self.name_patterns else filename
            file_path = patterns.color_patterns_in_text(file_path, self.path_patterns,
                                                        color=Colors.MATCH) if self.path_patterns else file_path

        if self.args.abs:  # --abs
            if file.name:  # Do not join the current working directory with the dot file.
                path = os.path.join(pathlib.Path.cwd(), file_path, filename)
            else:
                path = os.path.join(pathlib.Path.cwd(), file_path)
        elif self.args.dot and file.name:  # Do not join the current directory with the dot file.
            path = os.path.join(os.curdir, file_path, filename)
        else:
            path = os.path.join(file_path, filename)

        if self.args.quotes:  # --quotes
            path = f"\"{path}\""

        print(path)

    def print_files(self, directory: str) -> None:
        """
        Prints all the files in the directory hierarchy.

        :param directory: Directory to traverse.
        """
        if os.path.exists(directory):
            directory_hierarchy = pathlib.Path(directory)

            self.print_file(directory_hierarchy)

            try:
                for file in directory_hierarchy.rglob("*"):
                    self.print_file(file)
            except PermissionError as error:
                self.print_error(f"{error.filename}: permission denied")
        else:
            directory = directory or '""'
            self.print_error(f"{directory}: no such file or directory")

    def validate_parsed_arguments(self) -> None:
        """
        Validates the parsed command-line arguments.
        """
        if self.args.max_depth < 1:  # --max-depth
            self.print_error_and_exit("'max-depth' must be >= 1")


if __name__ == "__main__":
    Seek().run()
