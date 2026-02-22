"""A program that writes strings to standard output."""

import argparse
import sys
from collections.abc import Iterable
from itertools import chain
from typing import override

from pyforge.cli import CLIProgram, terminal, text


class Emit(CLIProgram):
    """A program that writes strings to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Emit`` instance."""
        super().__init__(name="emit")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="write strings to standard output",
                                         prog=self.name)

        parser.add_argument("strings", help="strings to write", metavar="STRINGS", nargs="*")
        parser.add_argument("--stdin", action="store_true", help="read from standard input")
        parser.add_argument("--stdin-after", action="store_true",
                            help="process standard input after STRINGS (use with --stdin)")
        parser.add_argument("-n", "--no-newline", action="store_true", help="suppress trailing newline")
        parser.add_argument("-e", "--escapes", action="store_true", help="interpret backslash escape sequences")
        parser.add_argument("-s", "--strict-escapes", action="store_true",
                            help="fail on invalid escape sequences (use with --escapes)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        # --stdin-after is only meaningful with --stdin.
        if self.args.stdin_after and not self.args.stdin:
            self.print_error_and_exit("--stdin-after must be used with --stdin")

        # --strict-escapes is only meaningful with --escapes.
        if self.args.strict_escapes and not self.args.escapes:
            self.print_error_and_exit("--strict-escapes must be used with --escapes")

    @override
    def main(self) -> None:
        """Run the program."""
        strings = self.args.strings

        # Stream stdin (when enabled) with positional strings to avoid buffering.
        if terminal.stdin_is_redirected() and self.args.stdin:
            if self.args.stdin_after:
                strings = chain(strings, sys.stdin)
            else:
                strings = chain(sys.stdin, strings)

        self.write_strings(strings)

        if not self.args.no_newline:
            print()

    def write_strings(self, strings: Iterable[str]) -> None:
        """Write strings to standard output, separated by spaces."""
        needs_space = False

        for raw_string in strings:
            string = text.strip_trailing_newline(raw_string)

            if needs_space:
                sys.stdout.write(" ")

            if self.args.escapes:
                try:
                    string = text.decode_python_escape_sequences(string)
                except UnicodeDecodeError as error:
                    if self.args.strict_escapes:
                        self.print_error_and_exit(f"invalid escape sequence at index {error.start}: {string!r}")

            sys.stdout.write(string)
            needs_space = True


def main() -> int:
    """Run the program."""
    return Emit().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
