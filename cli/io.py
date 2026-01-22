"""
Module for I/O related functions.
"""

import os
from typing import Iterable, Iterator, NamedTuple, Protocol, TextIO


class FileInfo(NamedTuple):
    """
    Immutable container for information about a file being read.

    Attributes:
        file_index: Position of the filename in the input sequence.
        filename: The file name as provided.
        text: Open text stream for the file.
    """
    file_index: int
    filename: str
    text: TextIO


class _Logger(Protocol):
    """
    Protocol for printing error messages pertaining to files.
    """

    def print_file_error(self, error_message: str) -> None:
        """
        Prints the error message to standard error.
        :param error_message: The error message to print.
        :return: None
        """
        ...


def print_line(line: str) -> None:
    """
    Prints a line, ensuring exactly one trailing newline (e.g., for input from files or standard input).
    :param line: The line to print.
    :return: None
    """
    print(line, end="" if line.endswith("\n") else "\n")


def read_files(files: TextIO | list[str], encoding: str, *, logger: _Logger) -> Iterator[FileInfo]:
    """
    Opens the files for reading in text mode and returns an iterator yielding FileInfo objects.
    :param files: A list of file names or a text stream containing file names (e.g. standard input).
    :param encoding: The text encoding.
    :param logger: The logger for printing errors.
    :return: An iterator of FileInfo objects.
    """
    for file_index, filename in enumerate(files):
        filename = filename.rstrip(" \n")

        try:
            if os.path.isdir(filename):
                logger.print_file_error(f"{filename}: is a directory")
            else:
                with open(filename, "rt", encoding=encoding) as text:
                    yield FileInfo(file_index, filename, text)
        except FileNotFoundError:
            filename = filename or '""'
            logger.print_file_error(f"{filename}: no such file or directory")
        except PermissionError:
            logger.print_file_error(f"{filename}: permission denied")
        except OSError:
            logger.print_file_error(f"{filename}: unable to read file")


def write_text_to_file(filename: str, text: Iterable[str], encoding: str, *, logger: _Logger) -> None:
    """
    Write text lines to the file in text mode where each output line is written with exactly one trailing newline.
    :param filename: The filename.
    :param text: An iterable of strings (e.g., list, generator, or text stream).
    :param encoding: The text encoding.
    :param logger: The logger for printing errors.
    :return: None
    """
    try:
        with open(filename, "wt", encoding=encoding) as f:
            for line in text:
                line = line.rstrip("\n")
                f.write(f"{line}\n")
    except PermissionError:
        logger.print_file_error(f"{filename}: permission denied")
    except OSError:
        logger.print_file_error(f"{filename}: unable to write file")
    except UnicodeEncodeError:
        logger.print_file_error(f"{filename}: unable to write with {encoding}")
