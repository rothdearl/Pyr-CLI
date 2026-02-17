"""Provides utilities for reading and writing text files and streams."""

import os
from collections.abc import Iterable, Iterator
from typing import NamedTuple, TextIO

from .types import ErrorReporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar file_name: Normalized file name.
    :ivar text_stream: Open text stream for the file, valid only until the next yield.
    """
    file_name: str
    text_stream: TextIO


def normalize_input_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield lines with a single trailing newline removed, if present."""
    for line in lines:
        yield remove_trailing_newline(line)


def read_text_files(files: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> Iterator[FileInfo]:
    """
    Open files for reading in text mode and yield ``FileInfo`` objects.

    :param files: Iterable of file names or a text stream yielding file names.
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    :return: Iterator yielding ``FileInfo`` objects, where the text stream is only valid until the next yield.
    """
    for file_index, raw_name in enumerate(files):
        file_name = remove_trailing_newline(raw_name)  # Normalize file name.

        try:
            if os.path.isdir(file_name):
                on_error(f"{file_name}: is a directory")
                continue

            with open(file_name, mode="rt", encoding=encoding) as text_stream:
                yield FileInfo(file_name, text_stream)
        except FileNotFoundError:
            visible_name = file_name or "(empty)"  # Use a visible placeholder for empty file names in messages.
            on_error(f"{visible_name}: no such file or directory")
        except PermissionError:
            on_error(f"{file_name}: permission denied")
        except OSError:
            on_error(f"{file_name}: unable to read file")


def remove_trailing_newline(string: str) -> str:
    """Remove a single trailing newline, if present."""
    return string.removesuffix("\n")


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
                f.write(remove_trailing_newline(line) + "\n")
    except PermissionError:
        on_error(f"{file_name}: permission denied")
    except UnicodeEncodeError:
        on_error(f"{file_name}: unable to write with {encoding}")
    except OSError:
        on_error(f"{file_name}: unable to write file")


__all__ = [
    "FileInfo",
    "normalize_input_lines",
    "read_text_files",
    "remove_trailing_newline",
    "write_text_to_file",
]
