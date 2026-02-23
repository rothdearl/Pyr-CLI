"""Provides an abstract base class (ABC) for command-line programs, defining a standard program lifecycle."""

import argparse
import sys
from abc import ABC, abstractmethod
from typing import Final, final

from fyrcli import __version__
from .constants import OS_IS_WINDOWS
from .terminal import stdout_is_terminal


class CLIProgram(ABC):
    """
    Abstract base class (ABC) for command-line programs, defining a standard program lifecycle.

    :ivar args: Parsed command-line arguments.
    :ivar error_exit_code: Exit code when an error occurs (default: ``1``).
    :ivar has_errors: Whether the program has encountered errors.
    :ivar name: Name of the program.
    :ivar print_color: Whether color output is enabled.
    :ivar version: Program version.
    """

    def __init__(self, *, name: str, error_exit_code: int = 1) -> None:
        """
        Initialize a new ``CLIProgram`` instance.

        :param name: Name of the program.
        :param error_exit_code: Exit code when an error occurs (default: ``1``).
        """
        self.args: argparse.Namespace | None = None
        self.error_exit_code: Final[int] = error_exit_code
        self.has_errors: bool = False
        self.name: Final[str] = name
        self.print_color: bool = False
        self.version: Final[str] = __version__

    @abstractmethod
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        ...

    def check_for_errors(self) -> None:
        """Raise ``SystemExit(error_exit_code)`` if the error flag is set."""
        if self.has_errors:
            raise SystemExit(self.error_exit_code)

    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        pass

    @final
    def check_parsed_arguments(self) -> None:
        """Check option dependencies, validate ranges, normalize options, and initialize runtime state."""
        self.check_option_dependencies()
        self.validate_option_ranges()
        self.normalize_options()
        self.initialize_runtime_state()

    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        # Disable color if standard output is redirected.
        self.print_color = getattr(self.args, "color", "off") == "on" and stdout_is_terminal()

    @abstractmethod
    def main(self) -> None:
        """Run the program."""
        ...

    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        pass

    @final
    def parse_arguments(self) -> None:
        """Parse command-line arguments to initialize program options."""
        self.args = self.build_arguments().parse_args()

    @final
    def print_error(self, error_message: str) -> None:
        """Set the error flag and print the message to standard error unless ``args.no_messages`` is present and set."""
        self.has_errors = True

        # --no-messages is a Unix convention to suppress per-file diagnostics but still set the error flag.
        if not getattr(self.args, "no_messages", False):
            print(f"{self.name}: error: {error_message}", file=sys.stderr)

    @final
    def print_error_and_exit(self, error_message: str) -> None:
        """Print the error message to standard error and raise ``SystemExit``."""
        print(f"{self.name}: error: {error_message}", file=sys.stderr)
        raise SystemExit(self.error_exit_code)

    @final
    def run_program(self) -> int:
        """
        Run the full program lifecycle and normalize process termination and exit codes.

        - Configure the environment.
        - Parse arguments and prepare runtime state.
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
            # Add a newline after Ctrl-C if standard output is attached to a terminal.
            if stdout_is_terminal():
                print()

            raise SystemExit(self.error_exit_code if OS_IS_WINDOWS else keyboard_interrupt_error_code)
        except OSError as error:
            # Normalize unexpected OS errors to a clean exit code.
            raise SystemExit(self.error_exit_code) from error

        return 0

    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        pass


__all__: Final[tuple[str, ...]] = ("CLIProgram",)
