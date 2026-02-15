#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that prints the last part of files, optionally following new lines."""

import argparse
import os
import sys
import time
from collections.abc import Iterable, Sequence
from threading import Thread
from typing import Final, override

from cli import CLIProgram, ansi, io, terminal


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Track(CLIProgram):
    """A program that prints the last part of files, optionally following new lines."""

    def __init__(self) -> None:
        """Initialize a new ``Track`` instance."""
        super().__init__(name="track", version="1.3.16")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="print the last part of FILES, optionally following new lines",
                                         epilog="read standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read input from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the last N lines, or all but the first N if N < 0 (default: 10)", metavar="N",
                            type=int)
        parser.add_argument("-f", "--follow", action="store_true", help="output appended lines as the file grows")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def follow_file(self, file_name: str, print_file_name_on_update) -> None:
        """Follow the file for new lines."""
        polling_interval: float = .5

        try:
            # Get the initial file content.
            with open(file_name, mode="rt", encoding=self.encoding) as f:
                previous_content = f.read()

            # Follow file until Ctrl-C.
            while True:
                # Re-open the file with each iteration.
                with open(file_name, mode="rt", encoding=self.encoding) as f:
                    next_content = f.read()

                    # Check for changes.
                    if previous_content != next_content:
                        print_index = 0

                        if next_content.startswith(previous_content):
                            print_index = len(previous_content)
                        elif len(next_content) < len(previous_content):
                            print(f"data deleted in: {file_name}")
                        else:
                            print(f"data modified in: {file_name}")

                        if print_file_name_on_update:
                            self.print_file_header(file_name)

                        print(next_content[print_index:])
                        previous_content = next_content

                time.sleep(polling_interval)
        except FileNotFoundError:
            self.print_error(f"{file_name} has been deleted")
        except (UnicodeDecodeError, OSError):
            self.print_error(f"{file_name} is no longer accessible")

    @override
    def main(self) -> None:
        """Run the program."""
        printed_files = []

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                printed_files.extend(self.print_lines_from_files(sys.stdin))
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                printed_files.extend(self.print_lines_from_files(self.args.files))
        elif self.args.files:
            printed_files.extend(self.print_lines_from_files(self.args.files))
        else:
            self.print_lines_from_input()

        if self.args.follow and printed_files:  # --follow
            # Start threads and wait for them to terminate.
            for thread in self.start_following_threads(printed_files, print_file_name_on_update=len(printed_files) > 1):
                thread.join()

    def print_file_header(self, file_name: str) -> None:
        """Print the file name (or "(standard input)" if empty), followed by a colon, unless ``args.no_file_name`` is set."""
        if not self.args.no_file_name:  # --no-file-name
            file_header = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_header = f"{Colors.FILE_NAME}{file_header}{Colors.COLON}:{ansi.RESET}"
            else:
                file_header = f"{file_header}:"

            print(file_header)

    def print_lines(self, lines: Sequence[str]) -> None:
        """Print lines to standard output."""
        max_lines = self.args.lines  # --lines
        skip_to_line = len(lines) - max_lines

        # Print all but the first 'N' lines.
        if max_lines < 0:
            skip_to_line = abs(max_lines)

        for index, line in enumerate(io.normalize_input_lines(lines), start=1):
            if index > skip_to_line:
                print(line)

    def print_lines_from_files(self, files: Iterable[str]) -> list[str]:
        """Read and print lines from each file, returning the names of files successfully printed."""
        printed_files = []

        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.print_lines(file_info.text_stream.readlines())
                printed_files.append(file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

        return printed_files

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        while True:
            self.print_lines(sys.stdin.readlines())

            if not self.args.follow:  # --follow on standard input is an infinite loop until Ctrl-C.
                return

    def start_following_threads(self, files: Iterable[str], *, print_file_name_on_update: bool) -> list[Thread]:
        """Start a thread for each file and return the started ``Thread`` objects."""
        threads = []

        for file_name in files:
            thread = Thread(target=self.follow_file, args=(file_name, print_file_name_on_update),
                            name=f"following-{file_name}")
            thread.start()
            threads.append(thread)

        return threads


if __name__ == "__main__":
    Track().run()
