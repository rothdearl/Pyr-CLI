"""
Module for terminal related functions.
"""

import sys


def input_is_redirected() -> bool:
    """
    Returns whether input is being redirected.
    :return: True or False.
    """
    return not sys.stdin.isatty()


def output_is_terminal() -> bool:
    """
    Returns whether output is to the terminal.
    :return: True or False.
    """
    return sys.stdout.isatty()
