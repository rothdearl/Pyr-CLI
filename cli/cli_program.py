"""Provides an abstract base class (ABC) for command-line programs, defining a standard program lifecycle."""

import argparse
import sys
from abc import ABC, abstractmethod
from typing import final

from .constants import OS_IS_WINDOWS
from .terminal import stdout_is_terminal


class CLIProgram(ABC):
    """
    Abstract base class (ABC) for command-line programs, defining a standard program lifecycle.

    :ivar args: Parsed command-line arguments.
    :ivar encoding: Encoding for reading and writing to files.
    :ivar error_exit_code: Exit code when an error occurs (default: ``1``).
    :ivar has_errors: Whether the program has encountered errors.
    :ivar name: Name of the program.
    :ivar print_color: Whether color output is enabled.
    :ivar version: Program version.
    """

    def __init__(self, *, name: str, version: str, error_exit_code: int = 1) -> None:
        """
        Initialize a new ``CLIProgram`` instance.

        :param name: Name of the program.
        :param version: Program version.
        :param error_exit_code: Exit code when an error occurs (default: ``1``).
        """
        self.args: argparse.Namespace | None = None
        self.encoding: str | None = None
        self.error_exit_code: int = error_exit_code
        self.has_errors: bool = False
        self.name: str = name
        self.print_color: bool = False
        self.version: str = version

    @abstractmethod
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        ...

    def check_for_errors(self) -> None:
        """Raise ``SystemExit(error_exit_code)`` if the error flag is set."""
        if self.has_errors:
            raise SystemExit(self.error_exit_code)

    @abstractmethod
    def check_parsed_arguments(self) -> None:
        """Validate and normalize parsed command-line arguments."""
        ...

    @abstractmethod
    def main(self) -> None:
        """Run the program."""
        ...

    @final
    def parse_arguments(self) -> None:
        """Parse command-line arguments to initialize program options."""
        self.args = self.build_arguments().parse_args()

        # Set default values for encoding and print_color.
        self.encoding = "iso-8859-1" if getattr(self.args, "latin1", False) else "utf-8"  # --latin1
        self.print_color = getattr(self.args, "color", "off") == "on" and stdout_is_terminal()  # --color

    @final
    def print_error(self, error_message: str) -> None:
        """Set the error flag and print the message to standard error unless ``args.no_messages`` is present and set."""
        self.has_errors = True

        if not getattr(self.args, "no_messages", False):
            print(f"{self.name}: error: {error_message}", file=sys.stderr)

    @final
    def print_error_and_exit(self, error_message: str) -> None:
        """Print the error message to standard error and raise ``SystemExit``."""
        print(f"{self.name}: error: {error_message}", file=sys.stderr)
        raise SystemExit(self.error_exit_code)

    @final
    def run(self) -> None:
        """
        Run the full program lifecycle and normalize process termination and exit codes.

        - Configure the environment.
        - Parse and validate arguments.
        - Run the program.
        - Handle errors.
        """
        keyboard_interrupt_error_code = 130
        sigpipe_exit_code = 141

        try:
            if OS_IS_WINDOWS:  # Fix ANSI escape sequences on Windows.
                from colorama import just_fix_windows_console

                just_fix_windows_console()
            else:  # Prevent broken pipe errors (not supported on Windows).
                from signal import SIG_DFL, SIGPIPE, signal

                signal(SIGPIPE, SIG_DFL)

            self.parse_arguments()
            self.check_parsed_arguments()
            self.main()
            self.check_for_errors()
        except BrokenPipeError:
            raise SystemExit(self.error_exit_code if OS_IS_WINDOWS else sigpipe_exit_code)
        except KeyboardInterrupt:
            print()  # Add a newline after Ctrl-C.
            raise SystemExit(self.error_exit_code if OS_IS_WINDOWS else keyboard_interrupt_error_code)
        except OSError as error:
            raise SystemExit(self.error_exit_code) from error


__all__ = ["CLIProgram"]
