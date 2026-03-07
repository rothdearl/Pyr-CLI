"""Type aliases for the CLI framework."""

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any, BinaryIO, Final

#: List of compiled regular expression patterns.
type CompiledPatterns = Sequence[re.Pattern[str]]

#: Callback for reporting error messages.
type ErrorReporter = Callable[[str], None]

#: A decoded JSON array represented as a list.
type JsonArray = list[Any]

#: A decoded JSON object represented as a dictionary.
type JsonObject = dict[str, Any]

#: String-to-string mappings used for HTTP headers.
type KeyValuePairs = Mapping[str, str]

#: Mapping of form field names to (filename, binary file object) tuples for multipart uploads.
type MultipartFiles = Mapping[str, tuple[str, BinaryIO]]

#: String-to-string mappings encoded into the URL query string.
type QueryParameters = Mapping[str, str]

__all__: Final[tuple[str, ...]] = (
    "CompiledPatterns",
    "ErrorReporter",
    "JsonArray",
    "JsonObject",
    "KeyValuePairs",
    "MultipartFiles",
    "QueryParameters",
)
