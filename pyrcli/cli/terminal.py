"""Predicates describing whether the standard streams are attached to a terminal."""

import sys
from typing import Final, TextIO


def _is_terminal(stream: TextIO) -> bool:
    """Return ``True`` if the stream is attached to a terminal."""
    return stream.isatty()


def stderr_is_redirected() -> bool:
    """Return ``True`` if standard error is not attached to a terminal."""
    return not _is_terminal(sys.stderr)


def stderr_is_terminal() -> bool:
    """Return ``True`` if standard error is attached to a terminal."""
    return _is_terminal(sys.stderr)


def stdin_is_redirected() -> bool:
    """Return ``True`` if standard input is not attached to a terminal."""
    return not _is_terminal(sys.stdin)


def stdin_is_terminal() -> bool:
    """Return ``True`` if standard input is attached to a terminal."""
    return _is_terminal(sys.stdin)


def stdout_is_redirected() -> bool:
    """Return ``True`` if standard output is not attached to a terminal."""
    return not _is_terminal(sys.stdout)


def stdout_is_terminal() -> bool:
    """Return ``True`` if standard output is attached to a terminal."""
    return _is_terminal(sys.stdout)


__all__: Final[tuple[str, ...]] = (
    "stderr_is_redirected",
    "stderr_is_terminal",
    "stdin_is_redirected",
    "stdin_is_terminal",
    "stdout_is_redirected",
    "stdout_is_terminal",
)
