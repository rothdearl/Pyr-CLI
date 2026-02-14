import unittest
from typing import final

from cli import ansi


@final
class ANSITest(unittest.TestCase):
    """Tests the ansi module."""

    def test_16_color_palette(self) -> None:
        # Verify lengths.
        bg_colors = [name for name, value in ansi.BgColors.__dict__.items() if
                     not name.startswith("__") and isinstance(value, str)]
        colors = [name for name, value in ansi.Colors.__dict__.items() if
                  not name.startswith("__") and isinstance(value, str)]
        test_attr = [name for name, value in ansi.TextAttributes.__dict__.items() if
                     not name.startswith("__") and isinstance(value, str)]

        self.assertEqual(len(bg_colors), 16)
        self.assertEqual(len(colors), 16)
        self.assertEqual(len(test_attr), 8)

        # Print the text attributes.
        print(f"Text attribute constants.")

        for name, color in ansi.TextAttributes.__dict__.items():
            if not name.startswith("__"):
                print(f"[{name:<13}]: {color}The quick brown fox jumps over the lazy dog{ansi.RESET}")

        print()

        # Print the foreground colors.
        print(f"Foreground color constants for the standard 16-color ANSI palette.")

        for name, color in ansi.Colors.__dict__.items():
            if not name.startswith("__"):
                print(f"[{name:<14}]: {color}The quick brown fox jumps over the lazy dog{ansi.RESET}")

        print()

        # Print the background colors.
        print(f"Background color constants for the standard 16-color ANSI palette.")

        for name, color in ansi.BgColors.__dict__.items():
            if not name.startswith("__"):
                print(f"[{name:<17}]: {color}The quick brown fox jumps over the lazy dog{ansi.RESET}")

        print()

    def test_256_color_palette(self) -> None:
        # Verify lengths.
        self.assertEqual(len(ansi.BG_COLORS_256), 256)
        self.assertEqual(len(ansi.COLORS_256), 256)

        # Print the ANSI 256-colors.
        print("ANSI 256-color palette (xterm-compatible)")

        for index, (fg_color, bg_color) in enumerate(zip(ansi.COLORS_256, ansi.BG_COLORS_256)):
            print(
                f"[{index:>3}]: {fg_color}The quick brown fox jumps{ansi.RESET} {bg_color}over the lazy dog{ansi.RESET}")
