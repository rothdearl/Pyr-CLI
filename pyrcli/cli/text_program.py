"""Abstract base class (ABC) for command-line programs that process text files."""

import os
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Final, final, override

from .ansi import RESET
from .cli_program import CLIProgram
from .io import FileInfo, iter_stdin_file_names, read_text_files


class TextProgram(CLIProgram, ABC):
    """
    Base class for command-line programs that process text files.

    :ivar encoding: Encoding for reading and writing to files (default: ``"utf-8"``).
    """

    def __init__(self, *, name: str, error_exit_code: int = 1) -> None:
        """Initialize the instance."""
        super().__init__(name=name, error_exit_code=error_exit_code)

        self.encoding: str = "utf-8"

    @abstractmethod
    def handle_text_stream(self, file_info: FileInfo) -> None:
        """Process the text stream in ``file_info``."""
        ...

    @override
    def initialize_runtime_state(self) -> None:
        """Initialize internal state derived from parsed options."""
        super().initialize_runtime_state()

        self.encoding = "iso-8859-1" if getattr(self.args, "latin1", False) else "utf-8"

    @final
    def process_text_files(self, files: Iterable[str]) -> list[str]:
        """
        Process each text file.

        - Delegates stream handling to ``handle_text_stream``.
        - Returns the names of files successfully processed.
        """
        processed_files = []

        for file_info in read_text_files(files, encoding=self.encoding, on_error=self.print_error):
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
    def render_file_header(self, file_name: str, *, file_name_style: str, colon_style: str) -> str:
        """Return a ``file_name:`` header (or ``"(standard input):"``), styled when enabled."""
        display_name = os.path.relpath(file_name) if file_name else "(standard input)"

        if self.print_color:
            return (
                f"{file_name_style}"
                f"{display_name}"
                f"{colon_style}:"
                f"{RESET}"
            )

        return f"{display_name}:"

    @final
    def should_print_file_header(self) -> bool:
        """Return ``True`` if file headers should be printed."""
        return not getattr(self.args, "no_file_name", False)


__all__: Final[tuple[str, ...]] = ("TextProgram",)
