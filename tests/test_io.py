import os
import unittest
from pathlib import Path
from typing import final

from pyrcli.cli import io


@final
class TestIO(unittest.TestCase):
    """Tests the io module."""

    def test_iter_descendant_paths(self) -> None:
        """Tests the iter_descendant_paths function."""
        for path in io.iter_descendant_paths(Path(os.curdir)):
            self.assertIsInstance(path, Path)

        for path in io.iter_descendant_paths(Path("/"), max_depth=1):
            self.assertIsInstance(path, Path)

    def test_read_text_files(self) -> None:
        """Tests the read_text_files function."""
        errors = []
        test_file_path = os.path.join("test_data", "io-test-file.txt")

        def on_error(error_message: str) -> None:
            """Callback for on_error."""
            errors.append(error_message)

        # 1) Empty file list.
        io.read_text_files(file_names=[], encoding="utf-8", on_error=on_error)
        self.assertEqual(errors, [])

        # 2) Valid file.
        for file_info in io.read_text_files(file_names=[test_file_path], encoding="utf-8", on_error=on_error):
            self.assertEqual(file_info.file_name, test_file_path)
        self.assertEqual(errors, [])

        # 3) File error: no such file or directory.
        for _ in io.read_text_files(file_names=["_init_.py"], encoding="utf-8", on_error=on_error):
            pass
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "'_init_.py': no such file or directory")
        errors.clear()

        # 4) File error: is a directory.
        for _ in io.read_text_files(file_names=["__pycache__"], encoding="utf-8", on_error=on_error):
            pass
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "'__pycache__': is a directory")

    def test_write_text_file(self) -> None:
        """Tests the write_text_file function."""
        errors = []
        test_file_path = os.path.join("test_data", "io-test-file.txt")

        def on_error(error_message: str) -> None:
            """Callback for on_error."""
            errors.append(error_message)

        # 1) Valid file.
        io.write_text_file(test_file_path, lines=["Unit testing."], encoding="utf-8", on_error=on_error)
        self.assertEqual(errors, [])

        # 2) Empty file name.
        io.write_text_file("", lines=[], encoding="utf-8", on_error=on_error)
        self.assertEqual(len(errors), 1)
        errors.clear()

        # 3) Invalid encoding.
        io.write_text_file(test_file_path, lines=["Unit testing."], encoding="invalid", on_error=on_error)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], f"'{test_file_path}': unknown encoding 'invalid'")
        errors.clear()
