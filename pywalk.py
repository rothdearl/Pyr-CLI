#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: pywalk.py
Author: Roth Earl
Version: 1.2.2
Description: A program to print files in a directory hierarchy.
License: GNU GPLv3
"""

import argparse
import os
import pathlib
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
class PyWalk(CLIProgram):
    """
    A program to print files in a directory hierarchy.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="pywalk", version="1.2.2", error_exit_code=2)

        self.at_least_one_match: bool = False

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print files in a directory hierarchy",
                                         epilog="default starting-point is the current directory", prog=self.NAME)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("dirs", help="directory starting-points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-d", "--depth", help="descend at most N+ levels of directories below the starting-points",
                            metavar="N+", type=int)
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case in patterns and input data")
        parser.add_argument("-I", "--invert-match", action="store_true", help="print non-matching files")
        parser.add_argument("-n", "--name", action="extend", help="print files that match PATTERN", metavar="PATTERN",
                            nargs=1)
        parser.add_argument("-p", "--path", action="extend", help="print paths that match PATTERN", metavar="PATTERN",
                            nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display the matched strings in color")
        parser.add_argument("--cwd", action="store_true", help="print the current working directory")
        parser.add_argument("--dot", action="store_true", help="print the dot (.) file")
        parser.add_argument("--empty", choices=("y", "n"), help="print files that are empty")
        modified_group.add_argument("--m-days", help="print files modified < than or > than n days", metavar="±n",
                                    type=int)
        modified_group.add_argument("--m-hours", help="print files modified < than or > than n hours", metavar="±n",
                                    type=int)
        modified_group.add_argument("--m-mins", help="print files modified < than or > than n minutes", metavar="±n",
                                    type=int)
        parser.add_argument("--quote", action="store_true", help="print files in quotation marks")
        parser.add_argument("--type", choices=("d", "f"), help="print files by type")
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

    def color_patterns_in_path(self, text: str, patterns: list[str]) -> str:
        """
        Colors all patterns in the path.
        :param text: The text to color.
        :param patterns: The patterns.
        :return: The path with all the patterns colored.
        """
        if patterns:
            text = PatternFinder.color_patterns_in_text(text, patterns, ignore_case=self.args.ignore_case,
                                                        color=Colors.MATCH)

        return text

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
                    matches_filters = difference < (last_modified * -1)
                else:
                    matches_filters = difference > last_modified
        except PermissionError:
            matches_filters = False
            self.log_file_error(f"{file}: permission denied")

        return matches_filters

    def file_has_patterns(self, file: str, patterns: list[str]) -> bool:
        """
        Returns whether the file has the patterns.
        :param file: The file.
        :param patterns: The patterns.
        :return: True or False.
        """
        return not patterns or PatternFinder.text_has_patterns(self, file, patterns,
                                                               ignore_case=self.args.ignore_case) != self.args.invert_match

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        if CLIProgram.input_is_redirected():
            for directory in sys.stdin:
                self.print_files(directory.rstrip("\n"))

            if self.args.dirs:  # Process any additional directories.
                for directory in self.args.dirs:
                    self.print_files(directory)
        else:
            dirs = [os.curdir] if not self.args.dirs else self.args.dirs

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

        if self.args.depth and self.args.depth < len(file.parents):  # --depth
            return

        if not self.file_has_patterns(file_name, self.args.name):  # --name
            return

        if not self.file_has_patterns(file_path, self.args.path):  # --path
            return

        if not self.file_matches_filters(file):  # --type, --empty, --m-days, --m-hours, or --m-mins
            return

        self.at_least_one_match = True

        # If --quiet, exit on first match for performance.
        if self.args.quiet:
            raise SystemExit(0)

        if self.print_color and not self.args.invert_match:  # --invert-match
            file_name = self.color_patterns_in_path(file_name, self.args.name)
            file_path = self.color_patterns_in_path(file_path, self.args.path)

        if self.args.cwd:  # --cwd
            if file.name:  # Do not join the current working directory with the dot file.
                path = os.path.join(pathlib.Path.cwd(), file_path, file_name)
            else:
                path = os.path.join(pathlib.Path.cwd(), file_path)
        elif self.args.dot and file.name:  # Do not join the current directory with the dot file.
            path = os.path.join(os.curdir, file_path, file_name)
        else:
            path = os.path.join(file_path, file_name)

        if self.args.quote:  # --quote
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
                self.log_file_error(f"{error.filename}: permission denied")
        else:
            self.log_file_error(f"{directory if directory else "\"\""}: no such file or directory")


if __name__ == "__main__":
    CLIProgram.run(PyWalk())
