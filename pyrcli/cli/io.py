"""Utilities for reading and writing text files and streams."""

import os
import pathlib
import sys
from collections.abc import Iterable, Iterator
from typing import Final, NamedTuple, TextIO

from .text import iter_nonempty_lines, iter_normalized_lines, strip_trailing_newline
from .types import ErrorReporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar file_name: File name (normalized by the caller).
    :ivar text_stream: Open text stream for the file, valid only until the next yield.
    """
    file_name: str
    text_stream: TextIO


def iter_descendant_paths(root: pathlib.Path, max_depth: int = sys.maxsize) -> Iterable[pathlib.Path]:
    """
    Yield descendant paths under ``root`` whose depth is less than or equal to ``max_depth``.

    - Depth is measured relative to ``root`` (depth 1 is an immediate child).
    - The ``root`` path itself is not yielded.
    - Subdirectories deeper than ``max_depth`` are not traversed.
    """
    root_depth = len(root.parts)

    for dir_path, dir_names, file_names in os.walk(top=root, topdown=True, followlinks=False):
        current = pathlib.Path(dir_path)
        depth = len(current.parts) - root_depth

        # Enforce --max-depth: prevent descent and suppress deeper children.
        if depth >= max_depth:
            dir_names[:] = []
            continue

        for name in dir_names:
            yield current / name

        for name in file_names:
            yield current / name


def iter_stdin_file_names() -> Iterator[str]:
    """Yield normalized file names from standard input."""
    yield from iter_nonempty_lines(sys.stdin)


def read_text_files(file_names: Iterable[str], *, encoding: str, on_error: ErrorReporter) -> Iterator[FileInfo]:
    """
    Open files for reading in text mode and yield ``FileInfo`` objects.

    - Each yielded ``FileInfo.text_stream`` is valid only until the next iteration.
    - ``on_error(message)`` is invoked for file-related errors; processing continues with the next file.
    - Errors reported: directory path, missing file, unknown encoding, permission denied, other OS read errors.
    """
    for file_name in iter_normalized_lines(file_names):
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


def write_text_to_file(file_name: str, *, lines: Iterable[str], encoding: str, on_error: ErrorReporter) -> None:
    """
    Write text lines to a file, ensuring exactly one trailing newline is written for each input line.

    - ``on_error(message)`` is invoked for file-related errors.
    - Errors reported: unknown encoding, permission denied, encoding failures, other OS write errors.
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
