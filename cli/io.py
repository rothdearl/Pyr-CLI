"""Provides utilities for reading and writing text files and streams."""

import os
from collections.abc import Iterable, Iterator
from typing import NamedTuple, TextIO

from .types import ErrorReporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar file_name: File name with a single trailing newline removed, if present.
    :ivar text_stream: Open text stream for the file, valid only until the next yield.
    """
    file_name: str
    text_stream: TextIO


def filter_empty_file_names(stdin_files: Iterable[str]) -> Iterator[str]:
    """Yield file names, excluding lines that are empty after removing one trailing newline."""
    for file_name in normalize_input_lines(stdin_files):
        if not file_name:
            continue

        yield file_name


def normalize_input_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield lines with a single trailing newline removed, if present."""
    for line in lines:
        yield remove_trailing_newline(line)


def read_text_files(files: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> Iterator[FileInfo]:
    """
    Open files for reading in text mode and yield ``FileInfo`` objects.

    :param files: Iterable of file names (e.g., command-line arguments or lines read from standard input).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    :return: Iterator yielding ``FileInfo`` objects, where the text stream is only valid until the next yield.
    """
    for file_name in normalize_input_lines(files):
        try:
            if os.path.isdir(file_name):
                on_error(f"{file_name!r}: is a directory")
                continue

            with open(file_name, mode="rt", encoding=encoding) as text_stream:
                yield FileInfo(file_name, text_stream)
        except FileNotFoundError:
            on_error(f"{file_name!r}: no such file or directory")
        except LookupError:
            on_error(f"{file_name!r}: unknown encoding {encoding!r}")
        except PermissionError:
            on_error(f"{file_name!r}: permission denied")
        except OSError:
            on_error(f"{file_name!r}: unable to read")


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
    except LookupError:
        on_error(f"{file_name!r}: unknown encoding {encoding!r}")
    except PermissionError:
        on_error(f"{file_name!r}: permission denied")
    except UnicodeEncodeError:
        on_error(f"{file_name!r}: unable to write with {encoding!r}")
    except OSError:
        on_error(f"{file_name!r}: unable to write")


__all__ = [
    "FileInfo",
    "filter_empty_file_names",
    "normalize_input_lines",
    "read_text_files",
    "remove_trailing_newline",
    "write_text_to_file",
]
