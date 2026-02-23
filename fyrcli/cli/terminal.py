"""Predicates describing whether standard input and output are attached to a terminal."""

import sys
from typing import Final


def stdin_is_redirected() -> bool:
    """Return whether standard input is redirected."""
    return not stdin_is_terminal()


def stdin_is_terminal() -> bool:
    """Return whether standard input is attached to a terminal."""
    return sys.stdin.isatty()


def stdout_is_redirected() -> bool:
    """Return whether standard output is redirected."""
    return not stdout_is_terminal()


def stdout_is_terminal() -> bool:
    """Return whether standard output is attached to a terminal."""
    return sys.stdout.isatty()


__all__: Final[tuple[str, ...]] = (
    "stdin_is_redirected",
    "stdin_is_terminal",
    "stdout_is_redirected",
    "stdout_is_terminal",
)
