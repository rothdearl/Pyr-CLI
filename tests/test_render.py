import re
import unittest

from pyrcli.cli import ansi, render


class TestRender(unittest.TestCase):
    """Tests the render module."""

    def test_single_pattern_single_match(self):
        text = "hello world"
        pattern = re.compile(r"hello")
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=[pattern], ansi_style=color)

        self.assertEqual(result, f"{color}hello{ansi.RESET} world")

    def test_multiple_patterns(self):
        text = "hello world"
        test_patterns = [re.compile(r"hello"), re.compile(r"world")]
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        self.assertEqual(result, f"{color}hello{ansi.RESET} {color}world{ansi.RESET}", )

    def test_overlapping_matches_are_merged(self):
        text = "apple"
        test_patterns = [re.compile(r"app"), re.compile(r"le")]
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        # Entire string should be colored once due to overlap.
        self.assertEqual(result, f"{color}apple{ansi.RESET}")

    def test_no_matches_returns_original_text(self):
        text = "hello world"
        test_patterns = [re.compile(r"xyz")]
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        self.assertEqual(result, text)

    def test_empty_text(self):
        text = ""
        test_patterns = [re.compile(r"hello")]
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        self.assertEqual(result, "")

    def test_empty_patterns(self):
        text = "hello world"
        test_patterns = []
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        self.assertEqual(result, text)

    def test_single_character_matches(self):
        text = "aabb"
        test_patterns = [re.compile(r"a")]
        color = "\033[31m"
        result = render.style_pattern_matches(text, patterns=test_patterns, ansi_style=color)

        self.assertEqual(result, f"{color}aa{ansi.RESET}bb")

    def test_bold(self):
        text = "word"
        result = render.bold(text)

        self.assertEqual(result, f"{ansi.TextAttributes.BOLD}word{ansi.RESET}")

    def test_dim(self):
        text = "word"
        result = render.dim(text)

        self.assertEqual(result, f"{ansi.TextAttributes.DIM}word{ansi.RESET}")

    def test_reverse_video(self):
        text = "word"
        result = render.reverse_video(text)

        self.assertEqual(result, f"{ansi.TextAttributes.REVERSE}word{ansi.RESET}")

    def test_style(self):
        text = "word"
        result = render.style(text, ansi_style=ansi.ForegroundColors.BLUE)

        self.assertEqual(result, f"{ansi.ForegroundColors.BLUE}word{ansi.RESET}")
