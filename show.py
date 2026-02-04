#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: show.py
Author: Roth Earl
Version: 1.3.10
Description: A program to print files to standard output.
License: GNU GPLv3
"""

import argparse
import os
import sys
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from typing import ClassVar, Final, final, override

from cli import CLIProgram, ansi, io, terminal


@dataclass(frozen=True, slots=True)
class Colors:
    """
    Namespace for terminal color constants.

    :cvar COLON: Color used for the colon following a file name.
    :cvar EOL: Color used for the EOL replacement.
    :cvar FILE_NAME: Color used for a file name.
    :cvar LINE_NUMBER: Color used for line numbers.
    :cvar SPACE: Color used for the space replacement.
    :cvar TAB: Color used for the tab replacement.
    """
    COLON: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_CYAN
    EOL: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_BLUE
    FILE_NAME: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_MAGENTA
    LINE_NUMBER: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_GREEN
    SPACE: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_CYAN
    TAB: ClassVar[Final[str]] = ansi.Colors16.BRIGHT_CYAN


@dataclass(frozen=True, slots=True)
class Whitespace:
    """
    Namespace for whitespace replacement constants.

    :cvar EOL: Replacement for the EOL.
    :cvar SPACE: Replacement for a space.
    :cvar TAB: Replacement for a tab.
    :cvar TRAILING_SPACE: Replacement for a trailing space.
    """
    EOL: ClassVar[Final[str]] = "$"
    SPACE: ClassVar[Final[str]] = "·"
    TAB: ClassVar[Final[str]] = ">···"
    TRAILING_SPACE: ClassVar[Final[str]] = "~"


@final
class Show(CLIProgram):
    """
    A program to print files to standard output.
    """

    def __init__(self) -> None:
        """
        Initialize a new ``Show`` instance.
        """
        super().__init__(name="show", version="1.3.10")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Build and return an argument parser.

        :return: An argument parser.
        """
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="if no FILES are specified, read from standard input", prog=self.name)

        parser.add_argument("files", help="input files", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="do not prefix output with file names")
        parser.add_argument("-n", "--line-numbers", action="store_true", help="number output lines")
        parser.add_argument("-p", "--print", default=sys.maxsize, help="print only N lines (N >= 1)", metavar="N",
                            type=int)
        parser.add_argument("-s", "--start", default=1, help="start at line N, from end if negative (N != 0)",
                            metavar="N", type=int)
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, line numbers, and whitespace (default: on)")
        parser.add_argument("--ends", action="store_true", help=f"display '{Whitespace.EOL}' at end of each line")
        parser.add_argument("--latin1", action="store_true", help="read FILES using iso-8859-1 (default: utf-8)")
        parser.add_argument("--spaces", action="store_true",
                            help=f"display spaces as '{Whitespace.SPACE}' and trailing spaces as '{Whitespace.TRAILING_SPACE}'")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--tabs", action="store_true", help=f"display tab characters as '{Whitespace.TAB}'")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_parsed_arguments(self) -> None:
        """
        Validate parsed command-line arguments.
        """
        if self.args.print < 1:  # --print
            self.print_error_and_exit("'print' must be >= 1")

        if self.args.start == 0:  # --start
            self.print_error_and_exit("'start' cannot = 0")

    @override
    def main(self) -> None:
        """
        Run the program logic.
        """
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:  # --stdin-files
                self.print_lines_from_files(sys.stdin)
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.print_lines_from_files(self.args.files)
        elif self.args.files:
            self.print_lines_from_files(self.args.files)
        else:
            self.print_lines_from_input()

    def print_file_header(self, file_name: str) -> None:
        """
        Print the file name or "(standard input)" if empty, followed by a colon, unless ``--no-file-name`` is set.

        :param file_name: File name to print.
        """
        if not self.args.no_file_name:  # --no-file-name
            file_name = os.path.relpath(file_name) if file_name else "(standard input)"

            if self.print_color:
                file_name = f"{Colors.FILE_NAME}{file_name}{Colors.COLON}:{ansi.RESET}"
            else:
                file_name = f"{file_name}:"

            print(file_name)

    def print_lines(self, lines: Collection[str]) -> None:
        """
        Print lines to standard output according to command-line arguments.

        :param lines: Iterable of lines to print.
        """
        line_start = len(lines) + self.args.start + 1 if self.args.start < 0 else self.args.start
        line_end = line_start + self.args.print - 1
        line_min = min(self.args.print, len(lines)) if self.args.print else len(lines)
        padding = len(str(line_min))

        for index, line in enumerate(lines, start=1):
            if line_start <= index <= line_end:
                line = self.show_spaces(line) if self.args.spaces else line  # --spaces
                line = self.show_tabs(line) if self.args.tabs else line  # --tabs
                line = self.show_ends(line) if self.args.ends else line  # --ends
                line = self.show_line_number(line, index, padding) if self.args.line_numbers else line  # --line-numbers
                io.print_line_normalized(line)

    def print_lines_from_files(self, files: Iterable[str]) -> None:
        """
        Read lines from each file and print them.

        :param files: Iterable of files to read.
        """
        for file_info in io.read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.print_file_header(file_info.file_name)
                self.print_lines(file_info.text.readlines())
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name}: unable to read with {self.encoding}")

    def print_lines_from_input(self) -> None:
        """
        Read lines from standard input until EOF and print them.
        """
        self.print_lines(sys.stdin)

    def show_ends(self, line: str) -> str:
        """
        Append the EOL character to the end of the line.

        :param line: Line to append.
        :return: Line with the EOL character appended.
        """
        end_index = -1 if line.endswith("\n") else len(line)
        newline = "\n" if end_index == -1 else ""

        if self.print_color:
            return f"{line[:end_index]}{Colors.EOL}{Whitespace.EOL}{ansi.RESET}{newline}"

        return f"{line[:end_index]}{Whitespace.EOL}{newline}"

    def show_line_number(self, line: str, line_number: int, padding: int) -> str:
        """
        Prepend the line with the line number.

        :param line: Line to prepend.
        :param line_number: Line number.
        :param padding: Line number padding.
        :return: Line with a line number prepended.
        """
        if self.print_color:
            return f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}{ansi.RESET} {line}"

        return f"{line_number:>{padding}} {line}"

    def show_spaces(self, line: str) -> str:
        """
        Replace spaces with Whitespace.SPACE or Whitespace.TRAILING_SPACE in the line.

        :param line: Line to replace spaces.
        :return: Line with spaces replaced.
        """
        has_newline = line.endswith("\n")
        trailing_count = len(line) - len(line.rstrip())  # Count trailing spaces.

        # Truncate trailing spaces.
        line = line[:-trailing_count] if trailing_count else line

        if has_newline:
            trailing_count -= 1

        if self.print_color:
            line = line.replace(" ", f"{Colors.SPACE}{Whitespace.SPACE}{ansi.RESET}")
            line = line + Colors.SPACE + (Whitespace.TRAILING_SPACE * trailing_count) + ansi.RESET
        else:
            line = line.replace(" ", Whitespace.SPACE)
            line = line + (Whitespace.TRAILING_SPACE * trailing_count)

        return line + "\n" if has_newline else line

    def show_tabs(self, line: str) -> str:
        """
        Replace tabs with Whitespace.TAB in the line.

        :param line: Line to replace tabs.
        :return: Line with tabs replaced.
        """
        if self.print_color:
            return line.replace("\t", f"{Colors.TAB}{Whitespace.TAB}{ansi.RESET}")

        return line.replace("\t", Whitespace.TAB)


if __name__ == "__main__":
    Show().run()
