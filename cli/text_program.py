"""Provides an abstract base class (ABC) for command-line programs that process text streams."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import final, override

from .cli_program import CLIProgram
from .io import FileInfo, read_text_files


class TextProgram(CLIProgram, ABC):
    """
    Abstract base class (ABC) for command-line programs that process text streams.

    :ivar encoding: Encoding for reading and writing to files (default: ``"utf-8"``).
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

    @abstractmethod
    def handle_text_stream(self, file_info: FileInfo) -> None:
        """Process a single text stream contained in a ``FileInfo`` instance."""
        ...

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        self.encoding = "iso-8859-1" if getattr(self.args, "latin1", False) else "utf-8"

    @final
    def process_text_files(self, files: Iterable[str]) -> list[str]:
        """
         Process each file path, delegating stream handling to ``handle_text_stream``.

        :param files: Iterable of file names to process.
        :return: A list of file names processed successfully.
        """
        processed_files = []

        for file_info in read_text_files(files, self.encoding, on_error=self.print_error):
            try:
                self.handle_text_stream(file_info)
                processed_files.append(file_info.file_name)
            except UnicodeDecodeError:
                self.print_error(f"{file_info.file_name!r}: unable to read with {self.encoding!r}")

        return processed_files


__all__ = ["TextProgram"]
