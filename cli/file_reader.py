import os
from abc import ABC
from io import TextIOWrapper
from typing import Iterator, TextIO
from typing import final

from cli import CLIProgram

# Define type aliases.
FileInfo = tuple[int, str, TextIOWrapper]


@final
class FileReader(ABC):
    """
    Utility class for programs to reads files.
    """

    @staticmethod
    def read_files(program: CLIProgram, files: TextIO | list[str], encoding: str) -> Iterator[FileInfo]:
        """
        Opens the files for reading in text mode and returns a tuple with the index, file name and text.
        :param program: The program reading the files.
        :param files: The files.
        :param encoding: The text encoding.
        :return: A tuple with the index, file name and text.
        """
        for index, file in enumerate(files):
            file = file.rstrip(" \n")

            try:
                if os.path.isdir(file):
                    program.log_error(f"{file}: is a directory")
                else:
                    with open(file, "r", encoding=encoding) as text:
                        yield index, file, text
            except FileNotFoundError:
                program.log_error(f"{file if file else "\"\""}: no such file or directory")
            except PermissionError:
                program.log_error(f"{file}: permission denied")
            except OSError:
                program.log_error(f"{file}: unable to read file")
