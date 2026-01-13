"""
Module for command-line programs to access I/O.
"""

import os
from typing import Iterator, TextIO

from cli import CLIProgram


def print_line(line: str) -> None:
    """
    Prints a line, ensuring exactly one trailing newline (e.g., for input from files or standard input).
    :param line: The line to print.
    :return: None
    """
    print(line, end="" if line.endswith("\n") else "\n")


def read_files(program: CLIProgram, files: TextIO | list[str], encoding: str) -> Iterator[tuple[int, str, TextIO]]:
    """
    Opens the files for reading in text mode and returns a tuple with the index, file name and text.
    :param program: The program reading the files.
    :param files: A list of file names or a text stream containing file names (e.g. standard input).
    :param encoding: The text encoding.
    :return: A tuple with the index, file name and text.
    """
    for index, file in enumerate(files):
        file = file.rstrip(" \n")

        try:
            if os.path.isdir(file):
                program.print_file_error(f"{file}: is a directory")
            else:
                with open(file, "r", encoding=encoding) as text:
                    yield index, file, text
        except FileNotFoundError:
            program.print_file_error(f"{file if file else "\"\""}: no such file or directory")
        except PermissionError:
            program.print_file_error(f"{file}: permission denied")
        except OSError:
            program.print_file_error(f"{file}: unable to read file")
