"""
Module for working with INI configuration files.
"""

import configparser
import json

from .types import Json, Reporter

# Configuration parser for an INI options file (intentional single global ConfigParser instance).
_config: configparser.ConfigParser = configparser.ConfigParser()

# List of string values that are considered falsy.
_falsy_values: set[str] = {"0", "false", "off", "n", "no"}

# List of string values that are considered truthy.
_truthy_values: set[str] = {"1", "on", "true", "y", "yes"}


def get_bool_option(section: str, option: str) -> bool | None:
    """
    Gets a boolean option. Fallback is False if section or option are not found, or the value is empty.

    :param section: Section name.
    :param option: Option name.
    :return: True, False, or None if the value is neither truthy nor falsy.
    """
    value = get_str_option_with_fallback(section, option, fallback="false").lower()

    if value in _falsy_values:
        return False

    if value in _truthy_values:
        return True

    return None


def get_float_option(section: str, option: str) -> float | None:
    """
    Gets a floating point decimal option. Fallback is 0.0 if section or option are not found, or the value is empty.

    :param section: Section name.
    :param option: Option name.
    :return: A floating point decimal value or None if the value cannot be parsed.
    """
    value = get_str_option_with_fallback(section, option, fallback="0.0")

    try:
        return float(value)
    except ValueError:
        return None


def get_int_option(section: str, option: str) -> int | None:
    """
    Gets an integer option. Fallback is 0 if section or option are not found, or the value is empty.

    :param section: Section name.
    :param option: Option name.
    :return: An integer value or None if the value cannot be parsed.
    """
    value = get_str_option_with_fallback(section, option, fallback="0")

    try:
        return int(value)
    except ValueError:
        return None


def get_json_option(section: str, option: str) -> Json | None:
    """
    Gets a JSON option. Fallback is {} if section or option are not found, or the value is empty.

    :param section: Section name.
    :param option: Option name.
    :return: A JSON value or None if the value cannot be parsed.
    """
    value = get_str_option_with_fallback(section, option, fallback="{}")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def get_str_option(section: str, option: str) -> str:
    """
    Gets a string option. Fallback is an empty string if section or option are not found, or the value is empty.

    :param section: Section name.
    :param option: Option name.
    :return: A string value.
    """
    return get_str_option_with_fallback(section, option, fallback="")


def get_str_option_with_fallback(section: str, option: str, *, fallback: str) -> str:
    """
    Gets a string option.

    :param section: Section name.
    :param option: Option name.
    :param fallback: Fallback value if a section or option are not found, or the value is empty.
    :return: A string value.
    """
    return _config.get(section, option, fallback=fallback) or fallback


def get_str_options(section: str, option: str, *, separator: str = ",") -> list[str]:
    """
    Gets a string option and splits it on separator, ignoring empty values.

    :param section: Section name.
    :param option: Option name.
    :param separator: Value separator (default: ",").
    :return: A list of string values.
    """
    value = get_str_option_with_fallback(section, option, fallback="")

    return [s for sub in value.split(separator) if (s := sub.strip())]


def read_options(path: str, on_error: Reporter) -> bool:
    """
    Reads options from the configuration file, clearing previous reads, and returns whether the process was successful.

    :param path: Path to the configuration file.
    :param on_error: Callback invoked with an error message if the file cannot be read or parsed.
    :return: True or False.
    """
    try:
        path = path.strip()

        with open(path) as f:
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
