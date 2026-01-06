#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: track.py
Author: Roth Earl
Version: 1.3.0
Description: A program to print the last part of files.
License: GNU GPLv3
"""

import argparse
import os
import sys
import time
from threading import Thread
from typing import Final, TextIO, final

from cli import CLIProgram, ConsoleColors, FileReader


@final
class Colors:
    """
    Class for managing colors.
    """
    COLON: Final[str] = ConsoleColors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ConsoleColors.BRIGHT_MAGENTA
    FOLLOWING: Final[str] = f"{ConsoleColors.DIM}{ConsoleColors.WHITE}"
    LINE_NUMBER: Final[str] = ConsoleColors.BRIGHT_GREEN


@final
class Track(CLIProgram):
    """
    A program to print the last part of files.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance.
        """
        super().__init__(name="track", version="1.3.0")

    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the last part of FILES",
                                         epilog="with no FILES, read standard input", prog=self.NAME)

        parser.add_argument("files", help="files to print", metavar="FILES", nargs="*")
        parser.add_argument("-f", "--follow", action="store_true", help="output appended data as the file grows")
        parser.add_argument("-H", "--no-file-header", action="store_true",
                            help="suppress the prefixing of file names on output")
        parser.add_argument("-n", "--lines", help="print the last or all but the first n lines", metavar="±n", type=int)
        parser.add_argument("-N", "--line-number", action="store_true", help="print line number with output lines")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="display the file headers in color")
        parser.add_argument("--iso", action="store_true", help="use iso-8859-1 instead of utf-8 when reading files")
        parser.add_argument("--pipe", action="store_true", help="read input from standard output")
        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {self.VERSION}")

        return parser

    def follow_file(self, file_name: str, print_file_name: bool, polling_interval: float = .5) -> None:
        """
        Follows a file for new lines.
        :param file_name: The file name.
        :param print_file_name: Whether to print the file name with each update.
        :param polling_interval: The duration between each check.
        :return: None
        """
        try:
            # Get the initial file content.
            with open(file_name, "r", encoding=self.encoding) as file:
                previous_content = file.read()

            # Follow file until Ctrl-C.
            while True:
                # Re-open the file with each iteration.
                with open(file_name, "r", encoding=self.encoding) as file:
                    next_content = file.read()

                    # Check for changes.
                    if previous_content != next_content:
                        print_index = 0

                        if next_content.startswith(previous_content):
                            print_index = len(previous_content)
                        elif len(next_content) < len(previous_content):
                            print(f"data deleted in: {file_name}")
                        else:
                            print(f"data modified in: {file_name}")

                        if print_file_name:
                            self.print_file_header(file_name)

                        CLIProgram.print_line(next_content[print_index:])
                        previous_content = next_content

                time.sleep(polling_interval)
        except FileNotFoundError:
            self.log_file_error(f"{file_name} has been deleted")
        except (OSError, UnicodeDecodeError):
            self.log_file_error(f"{file_name} is no longer accessible")

    def follow_files(self, files: list[str]) -> list[Thread]:
        """
        Follows the files for new lines.
        :param files: The files.
        :return: A list of threads that are following files.
        """
        print_file_name = len(files) > 1
        threads = []

        for file in files:
            thread = Thread(target=self.follow_file, args=(file, print_file_name))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        return threads

    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """
        files_printed = []

        # Ensure --line-number is only True if --follow=False.
        self.args.line_number = self.args.line_number and not self.args.follow

        # Set --no-file-header to True if there are no files and --pipe=False.
        if not self.args.files and not self.args.pipe:
            self.args.no_file_header = True

        if CLIProgram.input_is_redirected():
            if self.args.pipe:  # --pipe
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
            for thread in self.follow_files(files_printed):
                thread.join()

    def print_file_header(self, file: str) -> None:
        """
        Prints the file name, or (standard input) if empty, with a colon.
        :param file: The file.
        :return: None
        """
        if not self.args.no_file_header:  # --no-file-header
            file_name = os.path.relpath(file) if file else "(standard input)"
            following = f" (following)" if self.args.follow and file else ""

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{Colors.FOLLOWING}{following}{ConsoleColors.RESET}"
            else:
                file_name = f"{file_name}:{following}"

            print(file_name)

    def print_lines(self, lines: list[str]) -> None:
        """
        Prints the lines.
        :param lines: The lines.
        :return: None
        """
        line_number = 0
        lines_to_print = 10 if not self.args.lines else self.args.lines  # --lines
        skip_to_line = len(lines) - lines_to_print

        # Print all but the first 'n' lines.
        if lines_to_print < 0:
            skip_to_line = abs(lines_to_print)

        for line in lines:
            line_number += 1

            if line_number > skip_to_line:
                if self.args.line_number:  # --line-number
                    width = 7

                    if self.print_color:
                        line = f"{Colors.LINE_NUMBER}{line_number:>{width}}{Colors.COLON}:{ConsoleColors.RESET}{line}"
                    else:
                        line = f"{line_number:>{width}}:{line}"

                CLIProgram.print_line(line)

    def print_lines_from_files(self, files: TextIO | list[str]) -> list[str]:
        """
        Prints lines from files.
        :param files: The files.
        :return: A list of the files printed.
        """
        files_printed = []

        for _, file, text in FileReader.read_files(self, files, self.encoding):
            try:
                self.print_file_header(file=file)
                self.print_lines(text.readlines())
                files_printed.append(file)
            except UnicodeDecodeError:
                self.log_file_error(f"{file}: unable to read with {self.encoding}")

        return files_printed

    def print_lines_from_input(self) -> None:
        """
        Prints lines from standard input until EOF is entered.
        :return: None
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


if __name__ == "__main__":
    CLIProgram.run(Track())
