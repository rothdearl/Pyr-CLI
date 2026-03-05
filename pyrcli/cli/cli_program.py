"""Provides an abstract base class (ABC) for command-line programs, defining a standard program lifecycle."""

import argparse
import sys
from abc import ABC, abstractmethod
from typing import Final, final

from pyrcli import __version__
from .os_info import IS_WINDOWS
from .terminal import stdout_is_terminal


class CLIProgram(ABC):
    """
    Base class for command-line programs, defining a standard program lifecycle.

    :ivar args: Parsed command-line arguments.
    :ivar error_exit_code: Exit code when an error occurs (default: ``1``).
    :ivar has_errors: Whether the program has encountered errors.
    :ivar name: Name of the program.
    :ivar print_color: Whether color output is enabled.
    :ivar version: Program version.
    """

    def __init__(self, *, name: str, error_exit_code: int = 1) -> None:
        """Initialize the instance."""
        self.args: argparse.Namespace | None = None
        self.error_exit_code: Final[int] = error_exit_code
        self.has_errors: bool = False
        self.name: Final[str] = name
        self.print_color: bool = False
        self.version: Final[str] = __version__

    def _configure_from_options(self) -> None:
        """
        Configure the program from parsed options.

        - Check option dependencies.
        - Validate ranges.
        - Normalize options.
        - Initialize runtime state.
        """
        self.check_option_dependencies()
        self.validate_option_ranges()
        self.normalize_options()
        self.initialize_runtime_state()

    def _parse_arguments(self) -> None:
        """Parse command-line arguments to initialize program options."""
        self.args = self.build_arguments().parse_args()

    @abstractmethod
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        ...

    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        pass  # Optional hook; no action by default.

    @abstractmethod
    def execute(self) -> None:
        """Execute the command using the prepared runtime state."""
        ...

    def exit_if_errors(self) -> None:
        """Raise ``SystemExit(error_exit_code)`` if the error flag is set."""
        if self.has_errors:
            raise SystemExit(self.error_exit_code)

    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        # Disable color if standard output is redirected.
        self.print_color = getattr(self.args, "color", "off") == "on" and stdout_is_terminal()

    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        pass  # Optional hook; no action by default.

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
        Run the full program lifecycle and normalize process termination.

        - Configure the environment.
        - Parse arguments and prepare runtime state.
        - Execute the command.
        - Handle errors.

        :return: ``0`` on success.
        :raises SystemExit: With an exit code on failure.
        """
        keyboard_interrupt_error_code = 130
        sigpipe_exit_code = 141

        try:
            if IS_WINDOWS:  # Enable ANSI color support on Windows (via colorama).
                from colorama import just_fix_windows_console

                just_fix_windows_console()
            else:  # Prevent broken pipe errors (not supported on Windows).
                from signal import SIG_DFL, SIGPIPE, signal

                signal(SIGPIPE, SIG_DFL)

            self._parse_arguments()
            self._configure_from_options()
            self.execute()
            self.exit_if_errors()
        except BrokenPipeError:
            raise SystemExit(self.error_exit_code if IS_WINDOWS else sigpipe_exit_code)
        except KeyboardInterrupt:
            # Add a newline after Ctrl-C if standard output is attached to a terminal.
            if stdout_is_terminal():
                print()

            raise SystemExit(self.error_exit_code if IS_WINDOWS else keyboard_interrupt_error_code)
        except OSError as error:
            # Normalize unexpected OS errors to a clean exit code.
            raise SystemExit(self.error_exit_code) from error

        return 0

    def validate_option_ranges(self) -> None:
        """Validate that option values fall within their allowed numeric or logical ranges."""
        pass  # Optional hook; no action by default.


__all__: Final[tuple[str, ...]] = ("CLIProgram",)
