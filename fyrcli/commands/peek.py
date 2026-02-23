"""A program that prints the first part of files."""

import argparse
import sys
from collections import deque
from collections.abc import Iterable
from typing import Final, override

from fyrcli.cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Peek(TextProgram):
    """A program that prints the first part of files."""

    def __init__(self) -> None:
        """Initialize a new ``Peek`` instance."""
        super().__init__(name="peek")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print the first part of FILES",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the first N lines, or all but the last N if N < 0 (default: 10)", metavar="N",
                            type=int)
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.print_lines(file_info.text_stream)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the rendered file header for ``file_name``."""
        if self.should_print_file_header():
            print(self.render_file_header(file_name, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON))

    def print_lines(self, lines: Iterable[str]) -> None:
        """Print lines to standard output."""
        # If --lines is positive or zero: print the first N lines.
        if self.args.lines >= 0:
            for index, line in enumerate(text.iter_normalized_lines(lines)):
                if index >= self.args.lines:
                    break

                print(line)

            return

        # --lines is negative: print all but the last |N| lines.
        buffer = deque(maxlen=-self.args.lines)

        for line in text.iter_normalized_lines(lines):
            if len(buffer) == buffer.maxlen:
                print(buffer.popleft())

            buffer.append(line)

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input (negative ``args.lines`` is treated as ``|N|``)."""
        self.args.lines = abs(self.args.lines)  # Normalize --lines before reading from standard input.
        self.print_lines(sys.stdin)


def main() -> int:
    """Run the program."""
    return Peek().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
