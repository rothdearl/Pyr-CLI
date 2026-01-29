"""
Functions for reading and parsing values from INI configuration files.
"""

import configparser
import json

from .types import ErrorReporter, Json

# Configuration parser for an INI options file (intentional single global ConfigParser instance).
_config: configparser.ConfigParser = configparser.ConfigParser()

# Set of string values that are considered falsy.
_falsy_values: set[str] = {"0", "false", "off", "n", "no"}

# Set of string values that are considered truthy.
_truthy_values: set[str] = {"1", "on", "true", "y", "yes"}


def get_bool_option(section: str, option: str) -> bool | None:
    """
    Return a boolean value parsed from the option.

    :param section: Section name.
    :param option: Option name.
    :return: Boolean value or ``None`` if the value is not truthy or falsy.
    """
    value = get_str_option_with_fallback(section, option, fallback="false").lower()

    if value in _falsy_values:
        return False

    if value in _truthy_values:
        return True

    return None


def get_float_option(section: str, option: str) -> float | None:
    """
    Return a floating-point value parsed from the option.

    :param section: Section name.
    :param option: Option name.
    :return: Floating-point value or ``None`` if the value cannot be parsed.
    """
    value = get_str_option_with_fallback(section, option, fallback="0.0")

    try:
        return float(value)
    except ValueError:
        return None


def get_int_option(section: str, option: str) -> int | None:
    """
    Return an integer value parsed from the option.

    :param section: Section name.
    :param option: Option name.
    :return: Integer value or ``None`` if the value cannot be parsed.
    """
    value = get_str_option_with_fallback(section, option, fallback="0")

    try:
        return int(value)
    except ValueError:
        return None


def get_json_option(section: str, option: str) -> Json | None:
    """
    Return a JSON value parsed from the option.

    :param section: Section name.
    :param option: Option name.
    :return: Parsed JSON value or ``None`` if the value cannot be decoded.
    """
    value = get_str_option_with_fallback(section, option, fallback="{}")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def get_str_option(section: str, option: str) -> str:
    """
    Return a string value.

    :param section: Section name.
    :param option: Option name.
    :return: String value.
    """
    return get_str_option_with_fallback(section, option, fallback="")


def get_str_option_with_fallback(section: str, option: str, *, fallback: str) -> str:
    """
    Return a string value, using a fallback if the option is missing or empty.

    :param section: Section name.
    :param option: Option name.
    :param fallback: Fallback value if the option is missing or empty.
    :return: String value.
    """
    return _config.get(section, option, fallback=fallback) or fallback


def get_str_options(section: str, option: str, *, separator: str = ",") -> list[str]:
    """
    Return string values split on a separator, ignoring empty entries.

    :param section: Section name.
    :param option: Option name.
    :param separator: Value separator (default: ``","``).
    :return: List of string values.
    """
    value = get_str_option_with_fallback(section, option, fallback="")

    return [s for sub in value.split(separator) if (s := sub.strip())]


def has_defaults() -> bool:
    """
    Return whether the DEFAULT section contains any options.

    :return: ``True`` if the DEFAULT section has at least one option.
    """
    return bool(_config.defaults())


def has_sections() -> bool:
    """
    Return whether any non-default sections exist.

    :return: ``True`` if at least one non-default section exists.
    """
    return bool(_config.sections())


def is_empty() -> bool:
    """
    Return whether the configuration is empty.

    :return: ``True`` if there are no DEFAULT options and no non-default sections.
    """
    return not has_defaults() and not has_sections()


def read_options(path: str, *, clear_previous: bool = True, on_error: ErrorReporter) -> bool:
    """
    Read options from a configuration file and return whether the operation succeeded.

    :param path: Path to the configuration file.
    :param clear_previous: Whether to clear previously read options (default: ``True``).
    :param on_error: Callback invoked with an error message if the file cannot be read or parsed.
    :return: ``True`` if the process was successful.
    """
    try:
        path = path.strip()

        with open(path) as f:
            if clear_previous:
                _config.clear()

            _config.read_file(f)
    except (OSError, configparser.Error) as error:
        name = path or '""'

        match error:
            case FileNotFoundError():
                on_error(f"{name}: no such file or directory")
            case PermissionError():
                on_error(f"{name}: permission denied")
            case OSError():
                on_error(f"{name}: unable to read file")
            case configparser.Error():
                on_error(f"{name} is an invalid configuration file")

        return False

    return True


__all__ = [
    "get_bool_option",
    "get_float_option",
    "get_int_option",
    "get_json_option",
    "get_str_option",
    "get_str_option_with_fallback",
    "get_str_options",
    "has_defaults",
    "has_sections",
    "is_empty",
    "read_options"
]
