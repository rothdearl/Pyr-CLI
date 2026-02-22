"""A program that prints the last part of files, optionally following new lines."""

import argparse
import sys
import time
from collections.abc import Iterable, Sequence
from threading import Thread
from typing import Final, override

from pyforge.cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Track(TextProgram):
    """A program that prints the last part of files, optionally following new lines."""

    def __init__(self) -> None:
        """Initialize a new ``Track`` instance."""
        super().__init__(name="track")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="print the last part of FILES, optionally following new lines",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-n", "--lines", default=10,
                            help="print the last N lines, or all but the first N if N < 0 (default: 10)", metavar="N",
                            type=int)
        parser.add_argument("-f", "--follow", action="store_true", help="output appended lines as the file grows")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

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
            self.print_error(f"{file_name!r} has been deleted")
        except (UnicodeDecodeError, OSError):
            self.print_error(f"{file_name!r} is no longer accessible")

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.print_lines(file_info.text_stream.readlines())

    @override
    def main(self) -> None:
        """Run the program."""
        printed_files = []

        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                printed_files.extend(self.process_text_files_from_stdin())
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                printed_files.extend(self.process_text_files(self.args.files))
        elif self.args.files:
            printed_files.extend(self.process_text_files(self.args.files))
        else:
            self.print_lines_from_input()

        if self.args.follow and printed_files:
            # Start threads and wait for them to terminate.
            for thread in self.start_following_threads(printed_files, print_file_name_on_update=len(printed_files) > 1):
                thread.join()

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

    def print_lines(self, lines: Sequence[str]) -> None:
        """Print lines to standard output."""
        skip_to_line = len(lines) - self.args.lines

        # Print all but the first 'N' lines.
        if self.args.lines < 0:
            skip_to_line = abs(self.args.lines)

        for index, line in enumerate(text.iter_normalized_lines(lines), start=1):
            if index > skip_to_line:
                print(line)

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


def main() -> int:
    """Run the program."""
    return Track().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
