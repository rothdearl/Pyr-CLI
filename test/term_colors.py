#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: term-colors.py
Author: Roth Earl
Version: 0.0.0
Description: A program to display the ANSI 256-color palette.
License: GNU GPLv3
"""

from cli import ansi


def main() -> None:
    """
    Run the program logic.
    """
    for index, (fg_color, bg_color) in enumerate(zip(ansi.COLORS_256, ansi.BG_COLORS_256)):
        print(f"[{index:>3}]: {fg_color}The quick brown fox jumps{ansi.RESET} {bg_color}over the lazy dog{ansi.RESET}")


if __name__ == "__main__":
    main()
