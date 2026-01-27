"""
Module for terminal-related functions.
"""

import sys


def input_is_redirected() -> bool:
    """
    Check whether input is being redirected.

    :return: True if input is being redirected.
    """
    return not sys.stdin.isatty()


def output_is_terminal() -> bool:
    """
    Check whether output is to the terminal.

    :return: True if output is to the terminal.
    """
    return sys.stdout.isatty()
