"""
Module for file-related functions.
"""

import os
from collections.abc import Iterable, Iterator
from typing import NamedTuple, TextIO

from .types import Reporter


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    :ivar int file_index: Position of the file name in the input sequence.
    :ivar str filename: File name as provided.
    :ivar TextIO text: Open text stream for the file.
    """
    file_index: int
    filename: str
    text: TextIO


def print_line(line: str) -> None:
    """
    Prints a line, ensuring exactly one trailing newline (e.g., for input from files or standard input).

    :param line: Line to print.
    """
    print(line, end="" if line.endswith("\n") else "\n")


def read_files(files: Iterable[str] | TextIO, encoding: str, *, on_error: Reporter) -> Iterator[FileInfo]:
    """
    Opens the files for reading in text mode and returns an iterator yielding FileInfo objects.

    :param files: List of file names or a text stream containing file names (e.g. standard input).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    :return: Iterator of FileInfo objects.
    """
    for file_index, filename in enumerate(files):
        filename = filename.strip()

        try:
            if os.path.isdir(filename):
                on_error(f"{filename}: is a directory")
            else:
                with open(filename, "rt", encoding=encoding) as text:
                    yield FileInfo(file_index, filename, text)
        except FileNotFoundError:
            filename = filename or '""'
            on_error(f"{filename}: no such file or directory")
        except PermissionError:
            on_error(f"{filename}: permission denied")
        except OSError:
            on_error(f"{filename}: unable to read file")


def write_text_to_file(filename: str, text: Iterable[str], encoding: str, *, on_error: Reporter) -> None:
    """
    Write text lines to the file in text mode where each output line is written with exactly one trailing newline.

    :param filename: File name.
    :param text: Iterable of strings (e.g., list, generator, or text stream).
    :param encoding: Text encoding.
    :param on_error: Callback invoked with an error message for file-related errors.
    """
    try:
        with open(filename, "wt", encoding=encoding) as f:
            for line in text:
                line = line.rstrip("\n")
                f.write(f"{line}\n")
    except PermissionError:
        on_error(f"{filename}: permission denied")
    except OSError:
        on_error(f"{filename}: unable to write file")
    except UnicodeEncodeError:
        on_error(f"{filename}: unable to write with {encoding}")
