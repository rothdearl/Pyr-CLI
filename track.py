#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: track.py
Author: Roth Earl
Version: 1.3.7
Description: A program to print the last part of files, optionally following new lines.
License: GNU GPLv3
"""

import argparse
import os
import sys
import time
from collections.abc import Collection, Iterable
from enum import StrEnum
from threading import Thread
from typing import TextIO, final

from cli import CLIProgram, ansi, io, terminal


class Colors(StrEnum):
    """
    Terminal color constants.
    """
    COLON = ansi.BRIGHT_CYAN
    FILE_NAME = ansi.BRIGHT_MAGENTA
    FOLLOWING = f"{ansi.DIM}{ansi.WHITE}"


@final
class Track(CLIProgram):
    """
    A program to print the last part of files, optionally following new lines
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Track`` instance.
        """
        super().__init__(name="track", version="1.3.7")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="print the last part of FILES, optionally following new lines",
                                         epilog="if no FILES are specified, read standard input", prog=self.name)

        parser.add_argument("files", help="one or more input files", metavar="FILES", nargs="*")
        parser.add_argument("-f", "--follow", action="store_true", help="output appended lines as the file grows")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="do not prefix output lines with file names")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the last N lines (N >= 1), or all but the first N if negative (default: 10)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on", help="colorize file headers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def follow_file(self, file: str, print_file_name: bool, polling_interval: float = .5) -> None:
        """
        Follow the file for new lines.

        :param file: File to follow.
        :param print_file_name: Whether to print the file name with each update.
        :param polling_interval: Duration between each check.
        """
        try:
            # Get the initial file content.
            with open(file, "rt", encoding=self.encoding) as f:
                previous_content = f.read()

            # Follow file until Ctrl-C.
            while True:
                # Re-open the file with each iteration.
                with open(file, "rt", encoding=self.encoding) as f:
                    next_content = f.read()

                    # Check for changes.
                    if previous_content != next_content:
                        print_index = 0

                        if next_content.startswith(previous_content):
                            print_index = len(previous_content)
                        elif len(next_content) < len(previous_content):
                            print(f"data deleted in: {file}")
                        else:
                            print(f"data modified in: {file}")

                        if print_file_name:
                            self.print_file_header(file)

                        io.print_normalized_line(next_content[print_index:])
                        previous_content = next_content

                time.sleep(polling_interval)
        except FileNotFoundError:
            self.print_error(f"{file} has been deleted")
        except (OSError, UnicodeDecodeError):
            self.print_error(f"{file} is no longer accessible")

    def main(self) -> None:
        """
        Run the program logic.
        """
        files_printed = []

        # Set --no-file-header to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_header = True

        if terminal.input_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                files_printed.extend(self.print_lines_from_files(sys.stdin))
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                files_printed.extend(self.print_lines_from_files(self.args.files))
        elif self.args.files:
            files_printed.extend(self.print_lines_from_files(self.args.files))
        else:
            self.print_lines_from_input()

        if self.args.follow and files_printed:  # --follow
            for thread in self.start_following_threads(files_printed, print_file_name=len(files_printed) > 1):
                thread.join()

    def print_file_header(self, file: str) -> None:
        """
        Print the file name, or (standard input) if empty, with a colon.

        :param file: File header to print.
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"
            following = " (following)" if self.args.follow and file else ""

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{Colors.FOLLOWING}{following}{ansi.RESET}"
            else:
                file_name = f"{file_name}:{following}"

            print(file_name)

    def print_lines(self, lines: Collection[str]) -> None:
        """
        Print the lines.

        :param lines: Lines to print.
        """
        max_lines = self.args.lines  # --lines
        skip_to_line = len(lines) - max_lines

        # Print all but the first 'N' lines.
        if max_lines < 0:
            skip_to_line = abs(max_lines)

        for index, line in enumerate(lines, start=1):
            if index > skip_to_line:
                io.print_normalized_line(line)

    def print_lines_from_files(self, files: Iterable[str] | TextIO) -> list[str]:
        """
        Print lines from the files.

        :param files: Files to print lines from.
        :return: List of the files printed.
        """
        files_printed = []

        for file_info in io.read_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file=file_info.file_name)
                self.print_lines(file_info.text.readlines())
                files_printed.append(file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

        return files_printed

    def print_lines_from_input(self) -> None:
        """
        Print lines from standard input until EOF is entered.
        """
        eof = False
        lines = []

        while not eof:
            try:
                lines.append(input())
            except EOFError:
                self.print_lines(lines)
                lines.clear()

                # --follow on standard input is an infinite loop until Ctrl-C.
                if not self.args.follow:
                    eof = True

    def start_following_threads(self, files: Collection[str], *, print_file_name: bool) -> list[Thread]:
        """
        Start a thread for each file and return the started ``Thread`` objects.

        :param files: Files to follow.
        :param print_file_name: Whether to print the file name with each update.
        :return: List of started threads that are following files.
        """
        threads = []

        for file_name in files:
            thread = Thread(target=self.follow_file, args=(file_name, print_file_name), name=f"following-{file_name}")
            thread.daemon = True
            thread.start()
            threads.append(thread)

        return threads

    def validate_parsed_arguments(self) -> None:
        """
        Validate the parsed command-line arguments.
        """
        pass


if __name__ == "__main__":
    Track().run()
