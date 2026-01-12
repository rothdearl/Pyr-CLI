#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: seek.py
Author: Roth Earl
Version: 1.3.2
Description: A program to search for files in a directory hierarchy.
License: GNU GPLv3
"""

import argparse
import os
import pathlib
import re
import sys
import time
from typing import Final, final

from cli import CLIProgram, ConsoleColors, PatternFinder


@final
class Colors:
    """
    Class for managing colors.
    """
    MATCH: Final[str] = ConsoleColors.BRIGHT_RED


@final
class Seek(CLIProgram):
    """
    A program to search for files in a directory hierarchy.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="seek", version="1.3.2", error_exit_code=2)

        self.at_least_one_match: bool = False
        self.name_patterns: list[list[re.Pattern]] = []
        self.path_patterns: list[list[re.Pattern]] = []

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="search for files in a directory hierarchy",
                                         epilog="default starting point is the current directory", prog=self.NAME)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("dirs", help="directory starting points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-d", "--depth", help="descend at most N levels of directories below the starting points",
                            metavar="N+", type=int)
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching patterns")
        parser.add_argument("-I", "--invert-match", action="store_true",
                            help="print files that do not match the specified criteria")
        parser.add_argument("-n", "--name", action="extend", help="print files whose names match PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-p", "--path", action="extend", help="print files whose paths match PATTERN",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("--abs", action="store_true", help="print absolute file paths")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display matched strings in color")
        parser.add_argument("--dot", action="store_true", help="include dot (.) files in output")
        parser.add_argument("--empty", choices=("y", "n"), help="print only empty files")
        modified_group.add_argument("--m-days", help="print files modified less than or more than n days ago",
                                    metavar="±n", type=int)
        modified_group.add_argument("--m-hours", help="print files modified less than or more than n hours ago",
                                    metavar="±n", type=int)
        modified_group.add_argument("--m-mins", help="print files modified less than or more than n minutes ago",
                                    metavar="±n", type=int)
        parser.add_argument("--quotes", action="store_true", help="print file paths enclosed in double quotes")
        parser.add_argument("--type", choices=("d", "f"), help="print only directories (d) or regular files (f)")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def check_for_errors(self) -> None:
        """
        Raises a SystemExit if there are any errors.
        :return: None
        :raises SystemExit: Request to exit from the interpreter if there are any errors.
        """
        super().check_for_errors()

        if not self.at_least_one_match:
            raise SystemExit(1)

    def file_matches_filters(self, file: pathlib.Path) -> bool:
        """
        Returns whether the file matches any of the filters.
        :param file: The file.
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
            self.print_file_error(f"{file}: permission denied")

        return matches_filters

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        # Pre-compile patterns.
        if self.args.name:  # --name
            self.name_patterns = PatternFinder.compile_patterns(self, self.args.name, ignore_case=self.args.ignore_case)

        if self.args.path:  # --path
            self.path_patterns = PatternFinder.compile_patterns(self, self.args.path, ignore_case=self.args.ignore_case)

        if CLIProgram.input_is_redirected():
            for directory in sys.stdin:
                self.print_files(directory.rstrip("\n"))

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
        :param file: The file.
        :return: None
        """
        file_name = file.name if file.name else os.curdir  # The dot file does not have a file name.
        file_path = str(file.parent) if len(file.parts) > 1 else ""  # Do not use the dot file in the path.

        if not file.name and not self.args.dot:  # Skip the dot file if not --dot.
            return

        if self.args.depth and self.args.depth < len(file.parts):  # --depth
            return

        if not PatternFinder.text_has_patterns(file_name, self.name_patterns) != self.args.invert_match:
            return

        if not PatternFinder.text_has_patterns(file_path, self.path_patterns) != self.args.invert_match:
            return

        if not self.file_matches_filters(file):  # --type, --empty, --m-days, --m-hours, or --m-mins
            return

        self.at_least_one_match = True

        # If --quiet, exit on first match for performance.
        if self.args.quiet:
            raise SystemExit(0)

        if self.print_color and not self.args.invert_match:  # --invert-match
            file_name = PatternFinder.color_patterns_in_text(file_name, self.name_patterns,
                                                             color=Colors.MATCH) if self.name_patterns else file_name
            file_path = PatternFinder.color_patterns_in_text(file_path, self.path_patterns,
                                                             color=Colors.MATCH) if self.path_patterns else file_path

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

    def print_files(self, directory: str) -> None:
        """
        Prints all the files in the directory hierarchy.
        :param directory: The directory to walk.
        :return: None
        """
        if os.path.exists(directory):
            directory_hierarchy = pathlib.Path(directory)

            self.print_file(directory_hierarchy)

            try:
                for file in directory_hierarchy.rglob("*"):
                    self.print_file(file)
            except PermissionError as error:
                self.print_file_error(f"{error.filename}: permission denied")
        else:
            self.print_file_error(f"{directory if directory else "\"\""}: no such file or directory")


if __name__ == "__main__":
    Seek().run()
