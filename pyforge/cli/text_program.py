"""Provides an abstract base class (ABC) for command-line programs that process text files."""

import os
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import final, override

from .ansi import RESET
from .cli_program import CLIProgram
from .io import FileInfo, iter_stdin_file_names, read_text_files


class TextProgram(CLIProgram, ABC):
    """
    Abstract base class (ABC) for command-line programs that process text files.

    :ivar encoding: Encoding for reading and writing to files (default: ``"utf-8"``).
    """

    def __init__(self, *, name: str, error_exit_code: int = 1) -> None:
        """
        Initialize a new ``TextProgram`` instance.

        :param name: Name of the program.
        :param error_exit_code: Exit code when an error occurs (default: ``1``).
        """
        super().__init__(name=name, error_exit_code=error_exit_code)

        self.encoding: str = "utf-8"

    @abstractmethod
    def handle_text_stream(self, file_info: FileInfo) -> None:
        """Process the text stream in ``FileInfo``."""
        ...

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        self.encoding = "iso-8859-1" if getattr(self.args, "latin1", False) else "utf-8"

    @final
    def process_text_files(self, files: Iterable[str]) -> list[str]:
        """
        Process each file path and delegate handling of its text stream to ``handle_text_stream``.

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

    @final
    def process_text_files_from_stdin(self) -> list[str]:
        """Process file names read from standard input."""
        return self.process_text_files(iter_stdin_file_names())

    @final
    def render_file_header(self, file_name: str, *, file_name_color: str, colon_color: str) -> str:
        """Return a ``file_name:`` header (or ``"(standard input):"``), colorized when enabled."""
        rendered = os.path.relpath(file_name) if file_name else "(standard input)"

        if self.print_color:
            return f"{file_name_color}{rendered}{colon_color}:{RESET}"

        return f"{rendered}:"

    @final
    def should_print_file_header(self) -> bool:
        """Return whether file headers should be printed."""
        return not getattr(self.args, "no_file_name", False)


__all__: list[str] = ["TextProgram"]
