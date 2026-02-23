"""A program that prints lines matching patterns in files."""

import argparse
import sys
from collections.abc import Iterable, Sequence
from typing import Final, NamedTuple, override

from fyrcli.cli import CompiledPatterns, TextProgram, ansi, io, patterns, render, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA
    LINE_NUMBER: Final[str] = ansi.Colors.BRIGHT_GREEN
    MATCH: Final[str] = ansi.Colors.BRIGHT_RED


class Match(NamedTuple):
    """Immutable container representing a single pattern match."""
    line_number: int
    line: str


class Scan(TextProgram):
    """
    A program that prints lines matching patterns in files.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_any_match: Whether any match was found.
    :ivar patterns: Compiled patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize a new ``Scan`` instance."""
        super().__init__(name="scan", error_exit_code=2)

        self.found_any_match: bool = False
        self.patterns: CompiledPatterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print lines matching patterns in FILES",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)
        count_group = parser.add_mutually_exclusive_group()

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-e", "--find", action="extend",
                            help="print lines that match PATTERN (repeat --find to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print lines that do not match")
        count_group.add_argument("-c", "--count", action="store_true", help="print count of matching lines per file")
        count_group.add_argument("-C", "--count-nonzero", action="store_true",
                                 help="print count of matching lines for files with a match")
        parser.add_argument("-n", "--line-number", action="store_true", help="show line number for each matching line")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("-q", "--quiet", "--silent", action="store_true",
                            help="suppress normal output (matches, counts, and file names)")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress file error messages")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names, matches, and line numbers (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true",
                            help="treat standard input as a list of FILES (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_for_errors(self) -> None:
        """Raise ``SystemExit(NO_MATCHES_EXIT_CODE)`` if a match was not found."""
        super().check_for_errors()

        if not self.found_any_match:
            raise SystemExit(self.NO_MATCHES_EXIT_CODE)

    def collect_matches(self, lines: Iterable[str]) -> list[Match]:
        """Return a list of ``Match`` objects for lines matching the configured patterns."""
        matches = []

        for line_number, line in enumerate(text.iter_normalized_lines(lines), start=1):
            if patterns.matches_all_patterns(line, self.patterns) != self.args.invert_match:
                self.found_any_match = True

                # Exit early if --quiet.
                if self.args.quiet:
                    raise SystemExit(0)

                if self.print_color and not self.args.invert_match:
                    line = render.color_pattern_matches(line, self.patterns, color=Colors.MATCH)

                matches.append(Match(line_number, line))

        return matches

    def compile_patterns(self) -> None:
        """Compile search patterns."""
        self.patterns = patterns.compile_patterns(self.args.find, ignore_case=self.args.ignore_case,
                                                  on_error=self.print_error_and_exit)

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_matches(file_info.text_stream, origin_file=file_info.file_name)

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        # Exit early if no --find patterns are provided.
        if not self.args.find:
            raise SystemExit(self.NO_MATCHES_EXIT_CODE)

        self.compile_patterns()

    def is_printing_counts(self) -> bool:
        """Return whether ``args.count`` or ``args.count_nonzero`` is set."""
        return self.args.count or self.args.count_nonzero

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            elif standard_input := sys.stdin.readlines():
                self.print_matches(standard_input, origin_file="")

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_matches_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_match_results(self, matches: Sequence[Match], *, origin_file: str) -> None:
        """Print match counts or matched lines according to command-line options."""
        file_name = ""

        if self.should_print_file_header():
            file_name = self.render_file_header(origin_file, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON)

        if self.is_printing_counts():
            print(f"{file_name}{len(matches)}")
        elif matches:
            padding = len(str(matches[-1][0]))  # Use the line number from the last match to determine pad width.

            if file_name:
                print(file_name)

            for line_number, line in matches:
                if self.args.line_number:
                    if self.print_color:
                        print(f"{Colors.LINE_NUMBER}{line_number:>{padding}}{Colors.COLON}:{ansi.RESET}", end="")
                    else:
                        print(f"{line_number:>{padding}}:", end="")

                print(line)

    def print_matches(self, lines: Iterable[str], *, origin_file: str) -> None:
        """Search lines and print matches or counts according to command-line options."""
        matches = self.collect_matches(lines)

        # With --count-nonzero, suppress output for inputs with zero matches.
        if self.args.count_nonzero and not matches:
            return

        self.print_match_results(matches, origin_file=origin_file)

    def print_matches_from_input(self) -> None:
        """Read and print matches from standard input until EOF."""
        if self.is_printing_counts():
            self.print_matches(sys.stdin.readlines(), origin_file="")
        else:
            self.print_matches(sys.stdin, origin_file="")


def main() -> int:
    """Run the program."""
    return Scan().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
