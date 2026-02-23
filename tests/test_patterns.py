import re
import unittest

from fyrcli.cli import patterns


class TestCompileCombinedPatterns(unittest.TestCase):
    def test_basic_combination(self):
        test_patterns = [re.compile(r"abc"), re.compile(r"def")]
        combined = patterns.compile_combined_patterns(test_patterns, ignore_case=False)

        self.assertTrue(combined.search("abc"))
        self.assertTrue(combined.search("def"))
        self.assertFalse(combined.search("xyz"))

    def test_ignore_case_enabled(self):
        test_patterns = [re.compile(r"abc")]
        combined = patterns.compile_combined_patterns(test_patterns, ignore_case=True)

        self.assertTrue(combined.search("ABC"))

    def test_ignore_case_disabled(self):
        test_patterns = [re.compile(r"abc")]
        combined = patterns.compile_combined_patterns(test_patterns, ignore_case=False)

        self.assertFalse(combined.search("ABC"))

    def test_single_pattern(self):
        test_patterns = [re.compile(r"abc")]
        combined = patterns.compile_combined_patterns(test_patterns, ignore_case=False)

        self.assertTrue(combined.search("abc"))

    def test_empty_pattern_list(self):
        combined = patterns.compile_combined_patterns([], ignore_case=False)

        # Empty pattern compiles to an empty regex, which matches everything
        self.assertTrue(combined.search("anything"))


class TestCompilePatterns(unittest.TestCase):
    def test_compile_valid_patterns(self):
        test_patterns = ["abc", "def"]
        errors = []
        compiled = patterns.compile_patterns(test_patterns, ignore_case=False, on_error=errors.append)

        self.assertEqual(len(compiled), 2)
        self.assertTrue(compiled[0].search("abc"))
        self.assertTrue(compiled[1].search("def"))
        self.assertEqual(errors, [])

    def test_empty_patterns_are_skipped(self):
        test_patterns = ["abc", "", "def"]
        errors = []
        compiled = patterns.compile_patterns(test_patterns, ignore_case=False, on_error=errors.append)

        self.assertEqual(len(compiled), 2)

    def test_invalid_pattern_triggers_error_callback(self):
        test_patterns = ["[a-z", "abc"]
        errors = []
        compiled = patterns.compile_patterns(test_patterns, ignore_case=False, on_error=errors.append)

        self.assertEqual(len(compiled), 1)
        self.assertEqual(errors, ["invalid pattern: '[a-z'"])

    def test_ignore_case_enabled(self):
        test_patterns = ["abc"]
        errors = []
        compiled = patterns.compile_patterns(test_patterns, ignore_case=True, on_error=errors.append)

        self.assertTrue(compiled[0].search("ABC"))

    def test_ignore_case_disabled(self):
        test_patterns = ["abc"]
        errors = []
        compiled = patterns.compile_patterns(
            test_patterns,
            ignore_case=False,
            on_error=errors.append,
        )

        self.assertFalse(compiled[0].search("ABC"))

    def test_all_invalid_patterns(self):
        test_patterns = ["[", "("]
        errors = []
        compiled = patterns.compile_patterns(test_patterns, ignore_case=False, on_error=errors.append)

        self.assertEqual(compiled, [])
        self.assertEqual(len(errors), 2)


class TestMatchesAllPatterns(unittest.TestCase):
    def test_all_patterns_match(self):
        text = "abcdef"
        test_patterns = [re.compile(r"abc"), re.compile(r"def")]

        self.assertTrue(patterns.matches_all_patterns(text, test_patterns))

    def test_one_pattern_does_not_match(self):
        text = "abcdef"
        test_patterns = [re.compile(r"abc"), re.compile(r"xyz")]

        self.assertFalse(patterns.matches_all_patterns(text, test_patterns))

    def test_empty_pattern_list_returns_true(self):
        text = "abcdef"
        test_patterns = []

        self.assertTrue(patterns.matches_all_patterns(text, test_patterns))

    def test_empty_text_no_match(self):
        text = ""
        test_patterns = [re.compile(r"abc")]

        self.assertFalse(patterns.matches_all_patterns(text, test_patterns))

    def test_pattern_matching_empty_string(self):
        text = ""
        test_patterns = [re.compile(r"^$")]

        self.assertTrue(patterns.matches_all_patterns(text, test_patterns))

    def test_multiple_patterns_partial_match(self):
        text = "abcdef"
        test_patterns = [re.compile(r"abc"), re.compile(r"cd")]

        self.assertTrue(patterns.matches_all_patterns(text, test_patterns))
