"""Type aliases used throughout the command-line interface package."""

import re
from collections.abc import Callable, Mapping
from typing import Any, Final

#: List of compiled regular expression patterns.
type CompiledPatterns = list[re.Pattern[str]]

#: Callback for reporting error messages.
type ErrorReporter = Callable[[str], None]

#: A decoded JSON object represented as a dictionary.
type JsonObject = dict[str, Any]

#: String-to-string mappings used for HTTP headers or form payload fields.
type KeyValuePairs = dict[str, str]

#: Mapping of form field names to file objects in ``requests`` multipart format.
type MultipartFiles = Mapping[str, Any]

#: String-to-string mappings encoded into the URL query string.
type QueryParameters = dict[str, str]

__all__: Final[tuple[str, ...]] = (
    "CompiledPatterns",
    "ErrorReporter",
    "JsonObject",
    "KeyValuePairs",
    "MultipartFiles",
    "QueryParameters",
)
