"""
Module for file-related functions.
"""

import os
from typing import Iterable, Iterator, NamedTuple, Protocol, TextIO


class _ErrorReporter(Protocol):
    """
    Protocol for reporting file-related errors.
    """

    def print_error(self, error_message: str) -> None:
        """
        Prints the error message to standard error.
        :param error_message: The error message to print.
        :return: None
        """
        ...


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    Attributes:
        file_index: Position of the file name in the input sequence.
        filename: The file name as provided.
        text: Open text stream for the file.
    """
    file_index: int
    filename: str
    text: TextIO


def print_line(line: str) -> None:
    """
    Prints a line, ensuring exactly one trailing newline (e.g., for input from files or standard input).
    :param line: The line to print.
    :return: None
    """
    print(line, end="" if line.endswith("\n") else "\n")


def read_files(files: Iterable[str] | TextIO, encoding: str, *, reporter: _ErrorReporter) -> Iterator[FileInfo]:
    """
    Opens the files for reading in text mode and returns an iterator yielding FileInfo objects.
    :param files: A list of file names or a text stream containing file names (e.g. standard input).
    :param encoding: The text encoding.
    :param reporter: The reporter for printing file-related errors.
    :return: An iterator of FileInfo objects.
    """
    for file_index, filename in enumerate(files):
        filename = filename.rstrip()

        try:
            if os.path.isdir(filename):
                reporter.print_error(f"{filename}: is a directory")
            else:
                with open(filename, "rt", encoding=encoding) as text:
                    yield FileInfo(file_index, filename, text)
        except FileNotFoundError:
            filename = filename or '""'
            reporter.print_error(f"{filename}: no such file or directory")
        except PermissionError:
            reporter.print_error(f"{filename}: permission denied")
        except OSError:
            reporter.print_error(f"{filename}: unable to read file")


def write_text_to_file(filename: str, text: Iterable[str], encoding: str, *, reporter: _ErrorReporter) -> None:
    """
    Write text lines to the file in text mode where each output line is written with exactly one trailing newline.
    :param filename: The filename.
    :param text: An iterable of strings (e.g., list, generator, or text stream).
    :param encoding: The text encoding.
    :param reporter: The reporter for printing file-related errors.
    :return: None
    """
    try:
        with open(filename, "wt", encoding=encoding) as f:
            for line in text:
                line = line.rstrip("\n")
                f.write(f"{line}\n")
    except PermissionError:
        reporter.print_error(f"{filename}: permission denied")
    except OSError:
        reporter.print_error(f"{filename}: unable to write file")
    except UnicodeEncodeError:
        reporter.print_error(f"{filename}: unable to write with {encoding}")
