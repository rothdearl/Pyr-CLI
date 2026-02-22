"""A program that splits lines in files into fields."""

import argparse
import sys
from collections.abc import Iterable
from typing import Final, override

from pyforge.cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Slice(TextProgram):
    """
    A program that splits lines in files into fields.

    :ivar selected_fields: Selected fields to print.
    """

    def __init__(self) -> None:
        """Initialize a new ``Slice`` instance."""
        super().__init__(name="slice")

        self.selected_fields: list[int] = []

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="split lines in FILES into fields",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-f", "--fields", action="extend",
                            help="print only the specified fields (numbered from 1; order preserved; duplicates allowed)",
                            metavar="N", nargs="+", type=int)
        parser.add_argument("-u", "--unique", action="store_true",
                            help="normalize field selection to unique field numbers in ascending order (use with --fields)")
        parser.add_argument("-m", "--mode", choices=("csv", "regex", "shell"), default="csv",
                            help="set field parsing mode (default: csv)")
        parser.add_argument("--field-separator", help="split fields using SEP (default: <space>; use with --mode csv)",
                            metavar="SEP")
        parser.add_argument("--field-pattern",
                            help="split fields using PATTERN (default: <whitespace>; use with --mode regex)",
                            metavar="PATTERN")
        parser.add_argument("--literal-quotes", action="store_true",
                            help="treat quotes as ordinary characters (use with --mode shell)")
        parser.add_argument("--keep-empty", action="store_true", help="keep empty fields (default: drop)")
        parser.add_argument("--keep-empty-lines", action="store_true",
                            help="print empty lines when no fields are produced (default: drop)")
        parser.add_argument("-s", "--separator", default="\t", help="separate output fields with SEP (default: <tab>)",
                            metavar="SEP")
        parser.add_argument("--quotes", choices=("d", "s"), help="wrap fields in double (d) or single (s) quotes")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    def check_mode_option_dependencies(self) -> None:
        """Enforce mode-specific options are only used with their corresponding mode."""
        allowed_option_by_mode = {
            "csv": "--field-separator",
            "regex": "--field-pattern",
            "shell": "--literal-quotes"
        }
        provided_options = {
            "--field-pattern": self.args.field_pattern is not None,
            "--field-separator": self.args.field_separator is not None,
            "--literal-quotes": self.args.literal_quotes
        }

        # Any mismatched option is an error.
        allowed = allowed_option_by_mode[self.args.mode]
        mismatched = [name for name, is_set in provided_options.items() if is_set and name != allowed]

        if mismatched:
            self.print_error_and_exit(f"{', '.join(mismatched)} not valid with --mode={self.args.mode}")

    @override
    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        self.check_mode_option_dependencies()

        # --unique is only meaningful with --fields.
        if self.args.unique and self.args.fields is None:
            self.print_error_and_exit("--unique must be used with --fields")

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.split_and_print_lines(file_info.text_stream)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.split_and_print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.split_and_print_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        if self.args.unique:
            self.selected_fields = sorted(set(self.selected_fields))

        # Convert one-based input to zero-based.
        self.selected_fields = [i - 1 for i in self.selected_fields]

        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the rendered file header for ``file_name``."""
        if self.should_print_file_header():
            print(self.render_file_header(file_name, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON))

    def split_and_print_lines(self, lines: Iterable[str]) -> None:
        """Split lines into fields and print them."""
        quote = '"' if self.args.quotes == "d" else "'" if self.args.quotes == "s" else ""

        for line in text.iter_normalized_lines(lines):
            fields = self.split_line(line)

            # Do not print blank lines unless --keep-empty-lines=True.
            if not fields and not self.args.keep_empty_lines:
                continue

            print(self.args.separator.join(f"{quote}{field}{quote}" for field in fields))

    def split_and_print_lines_from_input(self) -> None:
        """Read, split, and print lines from standard input until EOF."""
        self.split_and_print_lines(sys.stdin)

    def split_line(self, line: str) -> list[str]:
        """Split the line into fields, optionally filter empty fields, and apply field selection if configured."""
        fields = []

        match self.args.mode:
            case "csv":
                field_separator = self.args.field_separator or " "

                fields = text.split_csv(line, separator=field_separator, on_error=self.print_error_and_exit)
            case "regex":
                field_pattern = self.args.field_pattern or r"\s+"

                fields = text.split_regex(line, pattern=field_pattern, on_error=self.print_error_and_exit)
            case _:
                fields = text.split_shell_style(line, literal_quotes=self.args.literal_quotes)

        # Filter empty fields unless --keep-empty=True.
        if not self.args.keep_empty:
            fields = [field for field in fields if field]

        # If --fields, collect the selected fields.
        if self.selected_fields:
            fields = [fields[index] for index in self.selected_fields if index < len(fields)]

        return fields

    @override
    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        self.selected_fields = self.args.fields or []

        for field in self.selected_fields:
            if field < 1:
                self.print_error_and_exit("--fields must contain numbers >= 1")


def main() -> int:
    """Run the program."""
    return Slice().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
