"""
Module for defining type aliases for the command-line interface package.
"""

import re
from collections.abc import Callable, Iterable
from typing import Any, TypeAlias

CompiledPatterns: TypeAlias = list[re.Pattern[str]]
Json: TypeAlias = dict[str, Any]
PatternIterable: TypeAlias = Iterable[re.Pattern[str]]
Reporter: TypeAlias = Callable[[str], None]
