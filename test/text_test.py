import unittest
from typing import final


@final
class TextTest(unittest.TestCase):
    """Tests the text module."""

    def test_split_csv(self) -> None:
        ...

    def test_split_regex(self) -> None:
        ...

    def test_split_shell_style(self) -> None:
        ...
