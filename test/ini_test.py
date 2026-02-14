import unittest
from typing import final

from cli import ini


@final
class INITest(unittest.TestCase):
    """Tests the ini module."""

    def test_read(self) -> None:
        # File does not exist.
        self.assertFalse(ini.read_options("", clear_previous=False, on_error=print))

        # File is invalid.
        self.assertFalse(ini.read_options("ini-test-invalid.ini", clear_previous=False, on_error=print))

        # No options.
        self.assertTrue(ini.is_empty())
        self.assertFalse(ini.has_defaults())
        self.assertFalse(ini.has_sections())

        # Valid file with options.
        self.assertTrue(ini.read_options("ini-test.ini", clear_previous=True, on_error=print))

        # Has options.
        self.assertFalse(ini.is_empty())
        self.assertTrue(ini.has_defaults())
        self.assertTrue(ini.has_sections())

    def test_values_bool(self) -> None:
        # Truthy.
        self.assertTrue(ini.get_bool_option("bool_options", "truthy_1"))
        self.assertTrue(ini.get_bool_option("bool_options", "truthy_on"))
        self.assertTrue(ini.get_bool_option("bool_options", "truthy_true"))
        self.assertTrue(ini.get_bool_option("bool_options", "truthy_y"))
        self.assertTrue(ini.get_bool_option("bool_options", "truthy_yes"))

        # Falsy.
        self.assertFalse(ini.get_bool_option("bool_options", "falsy_0"))
        self.assertFalse(ini.get_bool_option("bool_options", "falsy_false"))
        self.assertFalse(ini.get_bool_option("bool_options", "falsy_off"))
        self.assertFalse(ini.get_bool_option("bool_options", "falsy_n"))
        self.assertFalse(ini.get_bool_option("bool_options", "falsy_no"))

        # Fallback.
        self.assertFalse(ini.get_bool_option("bool_options", "empty_value"))
        self.assertFalse(ini.get_bool_option("bool_options", "missing_value"))
        self.assertFalse(ini.get_bool_option("missing_section", "truthy_1"))

        # Invalid.
        self.assertIsNone(ini.get_bool_option("bool_options", "invalid_value"))

    def test_values_float(self) -> None:
        # Valid.
        self.assertEqual(ini.get_float_option("float_options", "valid_float"), 3.14159)
        self.assertEqual(ini.get_float_option("float_options", "valid_int_like"), 10.0)
        self.assertEqual(ini.get_float_option("float_options", "negative_float"), -2.5)
        self.assertEqual(ini.get_float_option("float_options", "scientific"), 1000.0)

        # Fallback.
        self.assertEqual(ini.get_float_option("float_options", "empty_value"), 0.0)
        self.assertEqual(ini.get_float_option("float_options", "missing_value"), 0.0)
        self.assertEqual(ini.get_float_option("missing_section", "valid_float"), 0.0)

        # Invalid.
        self.assertIsNone(ini.get_float_option("float_options", "invalid_value"))

    def test_values_int(self) -> None:
        # Valid.
        self.assertEqual(ini.get_int_option("int_options", "valid_int"), 42)
        self.assertEqual(ini.get_int_option("int_options", "negative_int"), -7)
        self.assertEqual(ini.get_int_option("int_options", "zero"), 0)

        # Fallback.
        self.assertEqual(ini.get_int_option("int_options", "empty_value"), 0.0)
        self.assertEqual(ini.get_int_option("int_options", "missing_value"), 0.0)
        self.assertEqual(ini.get_int_option("missing_section", "valid_int"), 0.0)

        # Invalid.
        self.assertIsNone(ini.get_int_option("int_options", "invalid_value"))
        self.assertIsNone(ini.get_int_option("int_options", "invalid_string"))

    def test_values_json(self) -> None:
        # Valid.
        self.assertEqual(ini.get_json_option("json_options", "valid_object"), {"a": 1, "b": True})

        # Invalid.
        self.assertIsNone(ini.get_json_option("json_options", "invalid_array"))
        self.assertIsNone(ini.get_json_option("json_options", "invalid_string"))
        self.assertIsNone(ini.get_json_option("json_options", "invalid_number"))
        self.assertIsNone(ini.get_json_option("json_options", "invalid_bool"))
        self.assertIsNone(ini.get_json_option("json_options", "valid_null"))

        # Fallback.
        self.assertEqual(ini.get_json_option("json_options", "empty_value"), {})
        self.assertEqual(ini.get_json_option("json_options", "missing_value"), {})
        self.assertEqual(ini.get_json_option("missing_section", "valid_object"), {})

        # Invalid.
        self.assertIsNone(ini.get_json_option("json_options", "invalid_value"))

    def test_values_string(self) -> None:
        # Valid.
        self.assertEqual(ini.get_str_option("string_options", "normal_string"), "hello world")

        # Fallback.
        self.assertEqual(ini.get_str_option("string_options", "empty_value"), "")
        self.assertEqual(ini.get_str_option("string_options", "missing_value"), "")
        self.assertEqual(ini.get_str_option("missing_section", "normal_string"), "")

    def test_values_strings(self) -> None:
        # Valid.
        self.assertEqual(ini.get_str_options("string_list_options", "comma_separated"), ["a", "b", "c"])
        self.assertEqual(ini.get_str_options("string_list_options", "comma_with_spaces"), ["a", "b", "c"])
        self.assertEqual(ini.get_str_options("string_list_options", "leading_trailing"), ["a", "b"])
        self.assertEqual(ini.get_str_options("string_list_options", "only_separators"), [])
        self.assertEqual(ini.get_str_options("string_list_options", "single_value"), ["one"])

        # Fallback.
        self.assertEqual(ini.get_str_options("string_list_options", "empty_value"), [])
        self.assertEqual(ini.get_str_options("string_list_options", "missing_value"), [])
        self.assertEqual(ini.get_str_options("missing_section", "comma_separated"), [])
