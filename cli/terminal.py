"""
Predicates for terminal-related state.
"""

import sys


def input_is_redirected() -> bool:
    """
    Return whether input is being redirected.

    :return: ``True`` if input is being redirected.
    """
    return not input_is_terminal()


def input_is_terminal() -> bool:
    """
    Return whether input is to the terminal.

    :return: ``True`` if input is to the terminal.
    """
    return sys.stdin.isatty()


def output_is_terminal() -> bool:
    """
    Return whether output is to the terminal.

    :return: ``True`` if output is to the terminal.
    """
    return sys.stdout.isatty()


__all__ = [
    "input_is_redirected",
    "input_is_terminal",
    "output_is_terminal"
]
