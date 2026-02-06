"""
Functions for file-related operations.
"""

import os
from collections.abc import Iterable, Iterator
from typing import NamedTuple, TextIO

from .types import ErrorReporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar file_index: Position of the file name in the original input sequence.
    :ivar file_name: Normalized file name.
    :ivar text: Open text stream for the file, valid only until the next iteration.
    """
    file_index: int
    file_name: str
    text: TextIO


def print_line_normalized(line: str) -> None:
    """
    Print a line of text, ensuring exactly one trailing newline.

    :param line: Line to print.
    """
    print(line, end="" if line.endswith("\n") else "\n")


def read_text_files(files: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> Iterator[FileInfo]:
    """
    Open files for reading in text mode and yield ``FileInfo`` objects.

    :param files: Iterable of file names or a text stream yielding file names.
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    :return: Iterator yielding ``FileInfo`` objects, where the text stream is only valid until the next iteration.
    """
    for file_index, file_name in enumerate(files):
        file_name = file_name.rstrip("\n")  # Normalize file name.

        try:
            if os.path.isdir(file_name):
                on_error(f"{file_name}: is a directory")
                continue

            with open(file_name, mode="rt", encoding=encoding) as text:
                yield FileInfo(file_index, file_name, text)
        except FileNotFoundError:
            name = file_name or '""'  # Make empty file names visible in errors.
            on_error(f"{name}: no such file or directory")
        except PermissionError:
            on_error(f"{file_name}: permission denied")
        except OSError:
            on_error(f"{file_name}: unable to read file")


def write_text_to_file(file_name: str, text: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> None:
    """
    Write text lines to a file, ensuring exactly one trailing newline is written for each input line.

    :param file_name: File name.
    :param text: Iterable of strings (e.g., list, generator, or text stream).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    """
    try:
        with open(file_name, mode="wt", encoding=encoding) as f:
            for line in text:
                f.write(line.rstrip("\n") + "\n")
    except PermissionError:
        on_error(f"{file_name}: permission denied")
    except OSError:
        on_error(f"{file_name}: unable to write file")
    except UnicodeEncodeError:
        on_error(f"{file_name}: unable to write with {encoding}")


__all__ = [
    "FileInfo",
    "print_line_normalized",
    "read_text_files",
    "write_text_to_file",
]
