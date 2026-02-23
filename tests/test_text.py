import unittest
from typing import final

from fyrcli.cli import text


@final
class TestText(unittest.TestCase):
    """Tests the text module."""

    def test_iter_normalized_lines(self) -> None:
        """Tests the iter_normalized_lines function."""
        lines = (
            "Line 1\n",
            "Line 2",
            "Line 3\n",
            "Line 4",
            "Line 5\n"
        )

        for line in text.iter_normalized_lines(lines):
            self.assertFalse(line.endswith("\n"))

    def test_split_csv(self) -> None:
        """Tests the split_csv function."""
        errors = []

        def on_error(error_message: str) -> None:
            """Callback for on_error."""
            errors.append(error_message)

        # 1) Default behavior; CSV branch.
        self.assertEqual(text.split_csv("a  b", on_error=on_error), ["a", "", "b"])
        self.assertEqual(errors, [])

        # 2) Explicit single-character separator; CSV branch.
        self.assertEqual(text.split_csv("a,b,c", separator=",", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 3) CSV quoting; CSV branch.
        self.assertEqual(text.split_csv('a,"b,c",d', separator=",", on_error=on_error), ["a", "b,c", "d"])
        self.assertEqual(errors, [])

        # 4) Escape decoding in separator: r"\t" becomes a literal tab; CSV branch.
        self.assertEqual(text.split_csv("a\tb\tc", separator=r"\t", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 5) Multi-character separator; fallback to str.split(separator).
        self.assertEqual(text.split_csv("a::b::c", separator="::", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 6) Separator decodes to empty (e.g. "\x00" is valid, but "" should be invalid); fallback to str.split(separator).
        self.assertEqual(text.split_csv("a  b", separator="", on_error=on_error), ["a", "b"])
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid separator", errors[0])
        errors.clear()

        # 7) Invalid Unicode escape in separator; fallback to str.split(separator).
        self.assertEqual(text.split_csv("a  b", separator="\\x", on_error=on_error), ["a", "b"])
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid separator", errors[0])
        errors.clear()

        # 8) CSV disallowed separators: quote; fallback to str.split(separator).
        self.assertEqual(text.split_csv('a"b"c', separator='"', on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 9) CSV disallowed separators: newline; fallback to str.split(separator).
        self.assertEqual(text.split_csv("a\nb\nc", separator="\n", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 10) CSV disallowed separators: carriage return; fallback to str.split(separator).
        self.assertEqual(text.split_csv("a\rb\rc", separator="\r", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

    def test_split_regex(self) -> None:
        """Tests the split_regex function."""
        errors = []

        def on_error(error_message: str) -> None:
            """Callback for on_error."""
            errors.append(error_message)

        # 1) Basic regex splitting.
        self.assertEqual(text.split_regex("a,b,c", pattern=r",", on_error=on_error), ["a", "b", "c"])
        self.assertEqual(errors, [])

        # 2) Regex that can produce empty fields (similar to re.split behavior).
        self.assertEqual(text.split_regex("a,,b", pattern=r",", on_error=on_error), ["a", "", "b"])
        self.assertEqual(errors, [])

        # 3) Toggle ignore_case.
        self.assertEqual(text.split_regex("Xbox3", pattern=r"x", ignore_case=False, on_error=on_error), ["Xbo", "3"])
        self.assertEqual(text.split_regex("Xbox3", pattern=r"x", ignore_case=True, on_error=on_error), ["", "bo", "3"])
        errors.clear()

        # 4) Invalid regex pattern, raise re.error, fallback to whitespace split.
        self.assertEqual(text.split_regex("a  b", pattern=r"(", on_error=on_error), ["a", "b"])
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid pattern", errors[0])

    def test_split_shell_style(self) -> None:
        """Tests the split_shell_style function."""
        # 1) Whitespace split.
        self.assertEqual(text.split_shell_style(" a b   c "), ["a", "b", "c"])

        # 2) Shell-style quoting (default literal_quotes=False).
        self.assertEqual(text.split_shell_style(' a " b c " d '), ["a", " b c ", "d"])

        # 3) Treat quotes as ordinary characters (literal_quotes=True).
        self.assertEqual(text.split_shell_style('a "b c" d', literal_quotes=True), ["a", '"b', 'c"', "d"])

        # 4) Unmatched quotes, raise ValueError, fallback to a single field.
        raw = 'a "b '
        self.assertEqual(text.split_shell_style(raw), [raw])

    def test_strip_trailing_newline(self) -> None:
        """Tests the strip_trailing_newline function."""
        lines = (
            "Line 1\n",
            "Line 2",
            "Line 3\n",
            "Line 4",
            "Line 5\n"
        )

        for line in lines:
            self.assertFalse(text.strip_trailing_newline(line).endswith("\n"))
