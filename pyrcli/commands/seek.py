"""Provides a program for searching for files in a directory hierarchy."""

import argparse
import os
import pathlib
import sys
import time
from collections.abc import Iterable
from typing import Final, NoReturn, override

from pyrcli.cli import CLIProgram, CompiledPatterns, ansi, io, patterns, render, terminal, text


class Styles:
    """Namespace for ANSI styling constants."""
    MATCH: Final[str] = ansi.ForegroundColors.BRIGHT_RED


class Seek(CLIProgram):
    """
    Program for searching for files in a directory hierarchy.

    :cvar NO_MATCHES_EXIT_CODE: Exit code when no matches are found.
    :ivar found_any_match: Whether any match was found.
    :ivar name_patterns: Compiled name patterns to match.
    :ivar path_patterns: Compiled path patterns to match.
    """

    NO_MATCHES_EXIT_CODE: Final[int] = 1

    def __init__(self) -> None:
        """Initialize the instance."""
        super().__init__(name="seek", error_exit_code=2)

        self.found_any_match: bool = False
        self.name_patterns: CompiledPatterns = []
        self.path_patterns: CompiledPatterns = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="search for files in a directory hierarchy",
                                         epilog="use the current directory as the default starting point",
                                         prog=self.name)
        modified_group = parser.add_mutually_exclusive_group()

        parser.add_argument("directories", help="search starting points", metavar="DIRECTORIES", nargs="*")
        parser.add_argument("-n", "--name", action="extend",
                            help="print files whose names match PATTERN (repeat --name to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-p", "--path", action="extend",
                            help="print files whose paths match PATTERN (repeat --path to require all patterns)",
                            metavar="PATTERN", nargs=1)
        parser.add_argument("-i", "--ignore-case", action="store_true", help="ignore case when matching")
        parser.add_argument("-v", "--invert-match", action="store_true", help="print files that do not match")
        parser.add_argument("--type", choices=("d", "f"), help="print only directories (d) or regular files (f)")
        parser.add_argument("--empty-only", action="store_true", help="print only empty files")
        modified_group.add_argument("--mtime-days",
                                    help="print files by modification time (+N: older than N days; -N: within last N days)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-hours",
                                    help="print files by modification time (+N: older than N hours; -N: within last N hours)",
                                    metavar="N", type=int)
        modified_group.add_argument("--mtime-mins",
                                    help="print files by modification time (+N: older than N minutes; -N: within last N minutes)",
                                    metavar="N", type=int)
        parser.add_argument("--max-depth", default=sys.maxsize,
                            help="descend at most N levels below the starting points (N >= 1)", metavar="N", type=int)
        parser.add_argument("--abs", action="store_true", help="print absolute paths")
        parser.add_argument("--dot-prefix", action="store_true",
                            help="prefix relative paths with './' (print '.' for current directory)")
        parser.add_argument("--quotes", action="store_true", help="print file paths in double quotes")
        parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="suppress normal output")
        parser.add_argument("-s", "--no-messages", action="store_true", help="suppress file error messages")
        parser.add_argument("--color", choices=("on", "off"), default="on", help="use color for matches (default: on)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def compile_patterns(self) -> None:
        """Compile search patterns."""
        if self.args.name:
            self.name_patterns = patterns.compile_patterns(self.args.name, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

        if self.args.path:
            self.path_patterns = patterns.compile_patterns(self.args.path, ignore_case=self.args.ignore_case,
                                                           on_error=self.print_error_and_exit)

    @override
    def execute(self) -> None:
        """Execute the command using the prepared runtime state."""
        if terminal.stdin_is_redirected():
            self.print_paths(io.iter_stdin_file_names())

            if self.args.directories:  # Process any additional directories.
                self.print_paths(self.args.directories)
        else:
            self.print_paths(self.args.directories or [os.curdir])

    @override
    def exit_if_errors(self) -> None:
        """Raise ``SystemExit(NO_MATCHES_EXIT_CODE)`` if a match was not found."""
        super().exit_if_errors()

        if not self.found_any_match:
            raise SystemExit(self.NO_MATCHES_EXIT_CODE)

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        self.compile_patterns()

    def path_matches_filters(self, path: pathlib.Path) -> bool:
        """Return ``True`` if the path matches all enabled filters."""
        try:
            if self.args.type:
                is_dir = path.is_dir()

                if self.args.type == "d" and not is_dir:
                    return False
                elif self.args.type == "f" and is_dir:
                    return False

            if self.args.empty_only:
                if path.is_dir():
                    if os.listdir(path):
                        return False
                else:
                    if path.lstat().st_size:
                        return False

            if any((self.args.mtime_days, self.args.mtime_hours, self.args.mtime_mins)):
                if self.args.mtime_days:
                    threshold_seconds = self.args.mtime_days * 86400
                elif self.args.mtime_hours:
                    threshold_seconds = self.args.mtime_hours * 3600
                else:
                    threshold_seconds = self.args.mtime_mins * 60

                age_seconds = time.time() - path.lstat().st_mtime

                if threshold_seconds < 0:
                    return age_seconds < abs(threshold_seconds)

                return age_seconds > threshold_seconds
        except PermissionError:
            self.print_error(f"{path!r}: permission denied")
            return False

        return True

    def path_matches_patterns(self, name_part: str, path_part: str) -> bool:
        """Return ``True`` if the ``name_part`` and ``path_part`` match all provided pattern groups."""
        if not patterns.matches_all_patterns(name_part, compiled_patterns=self.name_patterns):
            return False

        if not patterns.matches_all_patterns(path_part, compiled_patterns=self.path_patterns):
            return False

        return True

    def print_path(self, path: pathlib.Path) -> None:
        """Print the path if it matches the specified search criteria."""
        is_current_directory = path.name == ""
        name_part = path.name or os.curdir  # The current directory has no name component.
        path_part = str(path.parent) if len(path.parts) > 1 else ""  # Do not include '.' in the path part.

        if is_current_directory and not self.args.dot_prefix:  # Skip the current directory unless --dot-prefix is set.
            return

        # Check if the path matches the search criteria and whether to invert the result.
        matches = self.path_matches_patterns(name_part, path_part) and self.path_matches_filters(path)

        if matches == self.args.invert_match:
            return

        if self.args.quiet:  # Exit early if --quiet.
            raise SystemExit(0)

        self.found_any_match = True

        if self.print_color and not self.args.invert_match:
            name_part = render.style_pattern_matches(name_part, patterns=self.name_patterns, ansi_style=Styles.MATCH)
            path_part = render.style_pattern_matches(path_part, patterns=self.path_patterns, ansi_style=Styles.MATCH)

        if self.args.abs:
            if is_current_directory:  # Do not join the current working directory with '.'.
                display_path = os.path.join(pathlib.Path.cwd(), path_part)
            else:
                display_path = os.path.join(pathlib.Path.cwd(), path_part, name_part)
        else:
            if self.args.dot_prefix and not is_current_directory:  # Do not join the current directory with '.'.
                display_path = os.path.join(os.curdir, path_part, name_part)
            else:
                display_path = os.path.join(path_part, name_part)

        if self.args.quotes:
            display_path = f'"{display_path}"'

        print(display_path)

    def print_paths(self, directories: Iterable[str]) -> None:
        """Traverse each starting directory up to ``args.max_depth`` and print paths that match the search criteria."""
        for directory in text.iter_normalized_lines(directories):
            if os.path.exists(directory):
                root = pathlib.Path(directory)

                self.print_path(root)

                try:
                    for path in io.iter_descendant_paths(root, max_depth=self.args.max_depth):
                        self.print_path(path)
                except PermissionError as error:
                    self.print_error(f"{error.filename!r}: permission denied")
            else:
                self.print_error(f"{directory!r}: no such file or directory")

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        if self.args.max_depth < 1:
            self.print_error_and_exit("--max-depth must be >= 1")


def main() -> int | NoReturn:
    """Run the command and return the exit code."""
    return Seek().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
