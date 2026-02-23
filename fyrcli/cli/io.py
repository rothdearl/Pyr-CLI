"""Provides utilities for reading and writing text files and streams."""

import os
import sys
from collections.abc import Iterable, Iterator
from typing import Final, NamedTuple, TextIO

from .text import iter_nonempty_lines, iter_normalized_lines, strip_trailing_newline
from .types import ErrorReporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar file_name: File name with a single trailing newline removed, if present.
    :ivar text_stream: Open text stream for the file, valid only until the next yield.
    """
    file_name: str
    text_stream: TextIO


def iter_stdin_file_names() -> Iterator[str]:
    """Yield normalized file names from standard input."""
    yield from iter_nonempty_lines(sys.stdin)


def read_text_files(files: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> Iterator[FileInfo]:
    """
    Open files for reading in text mode and yield ``FileInfo`` objects.

    :param files: Iterable of file names (e.g., command-line arguments or lines read from standard input).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    :return: Iterator yielding ``FileInfo`` objects, where the text stream is only valid until the next yield.
    """
    for file_name in iter_normalized_lines(files):
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


def write_text_to_file(file_name: str, lines: Iterable[str], encoding: str, *, on_error: ErrorReporter) -> None:
    """
    Write text lines to a file, ensuring exactly one trailing newline is written for each input line.

    :param file_name: File name.
    :param lines: Iterable of lines (e.g., list, generator, or text stream).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    """
    try:
        with open(file_name, mode="wt", encoding=encoding) as f:
            for line in lines:
                f.write(strip_trailing_newline(line) + "\n")
    except LookupError:
        on_error(f"{file_name!r}: unknown encoding {encoding!r}")
    except PermissionError:
        on_error(f"{file_name!r}: permission denied")
    except UnicodeEncodeError:
        on_error(f"{file_name!r}: unable to write with {encoding!r}")
    except OSError:
        on_error(f"{file_name!r}: unable to write")


__all__: Final[tuple[str, ...]] = (
    "FileInfo",
    "iter_stdin_file_names",
    "read_text_files",
    "write_text_to_file",
)
