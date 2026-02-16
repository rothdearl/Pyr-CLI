"""Provides an abstract base class (ABC) for command-line programs that process text streams."""

from abc import ABC
from typing import override

from .cli_program import CLIProgram


class TextProgram(CLIProgram, ABC):
    """
    Abstract base class (ABC) for command-line programs that process text streams.

    :ivar encoding: Encoding for reading and writing to files.
    """

    def __init__(self, *, name: str, version: str, error_exit_code: int = 1) -> None:
        """
        Initialize a new ``TextProgram`` instance.

        :param name: Name of the program.
        :param version: Program version.
        :param error_exit_code: Exit code when an error occurs (default: ``1``).
        """
        super().__init__(name=name, version=version, error_exit_code=error_exit_code)

        self.encoding: str = "utf-8"

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        self.encoding = "iso-8859-1" if self.args.latin1 else "utf-8"


__all__ = ["TextProgram"]
