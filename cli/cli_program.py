import argparse
import sys
from abc import ABC, abstractmethod
from typing import Final, final


class CLIProgram(ABC):
    """
    ABC base class for command-line programs.
    """

    @abstractmethod
    def __init__(self, *, name: str, version: str, error_exit_code: int = 1) -> None:
        """
        Initializes a new instance.
        :param name: The name.
        :param version: The version.
        :param error_exit_code: The exit code when an error occurs; default is 1.
        """
        self.ERROR_EXIT_CODE: Final[int] = error_exit_code
        self.NAME: Final[str] = name
        self.VERSION: Final[str] = version
        self.args: argparse.Namespace | None = None
        self.encoding: str | None = None
        self.has_errors: bool = False
        self.print_color: bool = False

    @abstractmethod
    def build_arguments(self) -> argparse.ArgumentParser:
        """
        Builds an argument parser.
        :return: An argument parser.
        """

    def check_for_errors(self) -> None:
        """
        Raises a SystemExit if there are any errors.
        :return: None
        :raises SystemExit: Request to exit from the interpreter if there are any errors.
        """
        if self.has_errors:
            raise SystemExit(self.ERROR_EXIT_CODE)

    @staticmethod
    def input_is_redirected() -> bool:
        """
        Returns whether input is being redirected.
        :return: True or False.
        """
        return not sys.stdin.isatty()

    @final
    def log_error(self, error_message: str, *, raise_system_exit: bool = False) -> None:
        """
        Sets the error flag to True and prints the error message to standard error.
        :param error_message: The error message.
        :param raise_system_exit: Whether to raise a SystemExit; default is False.
        :return: None
        :raises SystemExit: Request to exit from the interpreter if raise_system_exit = True.
        """
        self.has_errors = True
        print(f"{self.NAME}: {error_message}", file=sys.stderr)

        if raise_system_exit:
            raise SystemExit(self.ERROR_EXIT_CODE)

    @final
    def log_file_error(self, error_message: str) -> None:
        """
        Sets the error flag to True and prints the error message to standard error.
        :param error_message: The error message to print.
        :return: None
        """
        self.has_errors = True

        if not getattr(self.args, "no_messages", False):
            print(f"{self.NAME}: {error_message}", file=sys.stderr)

    @abstractmethod
    def main(self) -> None:
        """
        The main function of the program.
        :return: None
        """

    @staticmethod
    def output_is_terminal() -> bool:
        """
        Returns whether output is to the terminal.
        :return: True or False.
        """
        return sys.stdout.isatty()

    @final
    def parse_arguments(self) -> None:
        """
        Parses the command line arguments to get the program options.
        :return: None
        """
        self.args = self.build_arguments().parse_args()
        self.encoding = "iso-8859-1" if getattr(self.args, "iso", False) else "utf-8"  # --iso
        self.print_color = self.args.color == "on" and CLIProgram.output_is_terminal()  # --color (terminal only)

    @staticmethod
    def print_line(line: str) -> None:
        """
        Prints a line to the terminal.
        :param line: The line to print.
        :return: None
        """
        print(line, end="" if line[-1] == "\n" else "\n")  # Avoid printing two newlines.
