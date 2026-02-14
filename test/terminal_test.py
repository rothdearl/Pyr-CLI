import unittest
from typing import final

from cli import terminal


@final
class TerminalTest(unittest.TestCase):
    """Tests the terminal module."""

    def test_terminal_predicates(self) -> None:
        self.assertFalse(terminal.stdin_is_redirected())
        self.assertTrue(terminal.stdin_is_terminal())
        self.assertFalse(terminal.stdout_is_redirected())
        self.assertTrue(terminal.stdout_is_terminal())
