"""Type aliases used throughout the command-line interface package."""

import re
from collections.abc import Callable
from typing import Any, Final

type CompiledPatterns = list[re.Pattern[str]]
"""List of compiled regular expression patterns."""

type ErrorReporter = Callable[[str], None]
"""Callback for reporting error messages."""

type JsonObject = dict[str, Any]
"""A decoded JSON object represented as a dictionary."""

__all__: Final[tuple[str, ...]] = (
    "CompiledPatterns",
    "ErrorReporter",
    "JsonObject",
)
