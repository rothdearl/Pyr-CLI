#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from typing import final

from cli import ansi


@final
class ANSITest(unittest.TestCase):
    """
    Tests the ansi module.
    """

    def test_256_color_palette(self) -> None:
        self.assertEqual(len(ansi.BG_COLORS_256), 256)
        self.assertEqual(len(ansi.COLORS_256), 256)

        # Print the colors to the terminal.
        for index, (fg_color, bg_color) in enumerate(zip(ansi.COLORS_256, ansi.BG_COLORS_256)):
            print(
                f"[{index:>3}]: {fg_color}The quick brown fox jumps{ansi.RESET} {bg_color}over the lazy dog{ansi.RESET}")
