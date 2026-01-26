"""
Module for working with INI configuration files.
"""

import configparser
import json

from .types import Json, Reporter

# Configuration parser for an INI options file.
_config: configparser.ConfigParser = configparser.ConfigParser()

# List of string values that are considered truthy.
_truthy_values: set[str] = {"1", "on", "true", "y", "yes"}


def get_bool_option(section: str, option: str) -> bool:
    """
    Gets a boolean option. Defaults to False if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :return: True or False.
    """
    value = get_str_option_with_default(section, option, default_value="false").lower()

    return value in _truthy_values


def get_int_option(section: str, option: str) -> int:
    """
    Gets an integer option. Defaults to 0 if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :return: An integer value.
    :raises ValueError: If the value cannot be parsed.
    """
    value = get_str_option_with_default(section, option, default_value="0")

    return int(value)


def get_float_option(section: str, option: str) -> float:
    """
    Gets a floating point decimal option. Defaults to 0.0 if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :return: A floating point decimal value.
    :raises ValueError: If the value cannot be parsed.
    """
    value = get_str_option_with_default(section, option, default_value="0.0")

    return float(value)


def get_json_option(section: str, option: str) -> Json:
    """
    Gets a JSON option. Defaults to {} if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :return: A JSON value.
    :raises JSONDecodeError: If the value cannot be parsed.
    """
    value = get_str_option_with_default(section, option, default_value="{}")

    return json.loads(value)


def get_str_option(section: str, option: str) -> str:
    """
    Gets a string option. Defaults to an empty string if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :return: A string value.
    """
    return get_str_option_with_default(section, option, default_value="")


def get_str_option_with_default(section: str, option: str, *, default_value: str) -> str:
    """
    Gets a string option. Returns the default value if section or option are not found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :param default_value: Default value.
    :return: A string value.
    """
    try:
        value = _config.get(section, option)
    except configparser.Error:
        return default_value

    return value or default_value


def get_str_options(section: str, option: str, *, separator: str = ",") -> list[str]:
    """
    Gets a string option and splits it on separator, ignoring empty values. Defaults to [] if section or option are not
    found, or there is no value.

    :param section: Section name.
    :param option: Option name.
    :param separator: Value separator (default: ",").
    :return: A list of string values.
    """
    value = get_str_option_with_default(section, option, default_value="")

    return [s for sub in value.split(separator) if (s := sub.strip())]


def read_options(path: str, on_error: Reporter) -> bool:
    """
    Reads options from the configuration file and returns whether the process was successful.

    :param path: Path to the configuration file.
    :param on_error: Callback invoked with an error message if the file cannot be read or parsed.
    :return: True or False.
    """
    try:
        path = path.strip()

        with open(path) as f:
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
