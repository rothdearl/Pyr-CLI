#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: pywalk.py
Author: Roth Earl
Version: 1.2.0
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
        super().__init__(name="pywalk", version="1.2.0", error_exit_code=2)

        self.at_least_one_match: bool = False

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print files in a directory hierarchy",
                                         epilog="default directory is the current directory", prog=self.NAME)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("dirs", help="directory starting-points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case in patterns and input data")
        parser.add_argument("-I", "--invert-match", action="store_true", help="print non-matching files")
        parser.add_argument("-n", "--name", action="extend", help="print files that match PATTERN", metavar="PATTERN",
                            nargs=1)
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress all normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress error messages about files")
        parser.add_argument("--abs", action="store_true", help="print absolute file paths")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display the matched strings in color")
        parser.add_argument("--empty", choices=("y", "n"), help="print files that are empty")
        modified_group.add_argument("--m-days", help="print files modified < than or > than n days", metavar="±n",
                                    nargs=1, type=int)
        modified_group.add_argument("--m-hours", help="print files modified < than or > than n hours", metavar="±n",
                                    nargs=1, type=int)
        modified_group.add_argument("--m-mins", help="print files modified < than or > than n minutes", metavar="±n",
                                    nargs=1, type=int)
        parser.add_argument("--quote", action="store_true", help="print paths in quotation marks")
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
                    last_modified = self.args.m_days[0] * 86400  # Convert seconds to days.
                elif self.args.m_hours:
                    last_modified = self.args.m_hours[0] * 3600  # Convert seconds to hours.
                else:
                    last_modified = self.args.m_mins[0] * 60  # Convert seconds to minutes.

                difference = time.time() - file.lstat().st_mtime

                if last_modified < 0:
                    matches_filters = difference < (last_modified * -1)
                else:
                    matches_filters = difference > last_modified
        except PermissionError:
            self.log_file_error(f"{file}: permission denied")

        return matches_filters

    def file_name_matches_patterns(self, file_name: str) -> bool:
        """
        Returns whether the file name matches any of the patterns.
        :param file_name: The file name.
        :return: True or False.
        """
        if not self.args.name:  # --name
            return True

        return PatternFinder.text_has_all_patterns(self, file_name, self.args.name,
                                                   ignore_case=self.args.ignore_case) != self.args.invert_match  # --invert-match

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
            dirs = os.curdir if not self.args.dirs else self.args.dirs

            for directory in dirs:
                self.print_files(directory)

    def print_file(self, file: pathlib.Path) -> None:
        """
        Prints the file.
        :param file: The file.
        :return: None
        """
        if self.file_matches_filters(file):
            file_name = file.name if file.name else os.path.curdir  # The dot file does not have a file name.

            if self.file_name_matches_patterns(file_name):
                self.at_least_one_match = True

                # If --quiet, exit on first match for performance.
                if self.args.quiet:
                    raise SystemExit(0)

                path = str(file.absolute() if self.args.abs else file)  # --abs

                if self.args.quote:  # --quote
                    path = f"\"{path}\""

                if self.print_color and self.args.name and not self.args.invert_match:  # --name and not --invert-match
                    highlight = PatternFinder.color_patterns_in_text(self.args.name, file_name,
                                                                     ignore_case=self.args.ignore_case,
                                                                     color=Colors.MATCH)

                    # Ensure only the file name gets highlighted and nothing else in the path.
                    path = highlight.join(path.rsplit(file_name, maxsplit=1))

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
