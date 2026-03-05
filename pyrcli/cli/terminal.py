"""Predicates describing whether the standard streams are attached to a terminal."""

import sys
from typing import Final


def stderr_is_redirected() -> bool:
    """Return ``True`` if standard error is not attached to a terminal."""
    return not sys.stderr.isatty()


def stderr_is_terminal() -> bool:
    """Return ``True`` if standard error is attached to a terminal."""
    return sys.stderr.isatty()


def stdin_is_redirected() -> bool:
    """Return ``True`` if standard input is not attached to a terminal."""
    return not sys.stdin.isatty()


def stdin_is_terminal() -> bool:
    """Return ``True`` if standard input is attached to a terminal."""
    return sys.stdin.isatty()


def stdout_is_redirected() -> bool:
    """Return ``True`` if standard output is not attached to a terminal."""
    return not sys.stdout.isatty()


def stdout_is_terminal() -> bool:
    """Return ``True`` if standard output is attached to a terminal."""
    return sys.stdout.isatty()


__all__: Final[tuple[str, ...]] = (
    "stderr_is_redirected",
    "stderr_is_terminal",
    "stdin_is_redirected",
    "stdin_is_terminal",
    "stdout_is_redirected",
    "stdout_is_terminal",
)
