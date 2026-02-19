#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that writes arguments to standard output."""

import argparse
import sys
from collections.abc import Iterable
from typing import override

from cli import CLIProgram, terminal, text


class Emit(CLIProgram):
    """A program that writes arguments to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Emit`` instance."""
        super().__init__(name="emit", version="1.0.0")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="write arguments to standard output",
                                         prog=self.name)

        parser.add_argument("strings", help="arguments to write", metavar="STRINGS", nargs="*")
        parser.add_argument("-n", "--no-newline", action="store_true", help="do not output trailing newline")
        parser.add_argument("-e", "--escape-sequences", action="store_true",
                            help="interpret backslash escape sequences")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def main(self) -> None:
        """Run the program."""
        print_newline = not self.args.no_newline

        self.write_arguments(self.args.strings)

        if terminal.stdin_is_redirected():
            self.write_arguments(sys.stdin)

        print(end="\n" if print_newline else "")

    def write_arguments(self, arguments: Iterable[str]) -> None:
        """Write arguments to standard output."""
        print_space = False

        for argument in text.iter_normalized_lines(arguments):
            if print_space:  # Prefix arguments with a space character to avoid a trailing space character.
                print(" ", end="")

            if self.args.escape_sequences:
                try:
                    print(text.decode_python_escape_sequences(argument), end="")
                except UnicodeDecodeError:
                    self.print_error_and_exit(f"invalid escape sequence in: {argument!r}")
            else:
                print(argument, end="")

            print_space = True


if __name__ == "__main__":
    Emit().run()
