import unittest
from typing import final

from cli import ini


@final
class INITest(unittest.TestCase):
    """
    Tests the ini module.
    """

    def test_read(self) -> None:
        # File does not exist.
        self.assertFalse(ini.read_options("", clear_previous=False, on_error=print))

        # No options.
        self.assertTrue(ini.is_empty())
        self.assertFalse(ini.has_defaults())
        self.assertFalse(ini.has_sections())

        # Valid file with options.
        self.assertTrue(ini.read_options("../test/ini_test.ini", clear_previous=False, on_error=print))

        # Has options.
        self.assertFalse(ini.is_empty())
        self.assertTrue(ini.has_defaults())
        self.assertTrue(ini.has_sections())

    def test_values_booleans(self) -> None:
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
