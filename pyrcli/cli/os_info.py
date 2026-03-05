"""OS/platform predicates for use by CLI programs and supporting modules."""

import os
import sys
from typing import Final

IS_LINUX: Final[bool] = sys.platform.startswith("linux")
IS_MACOS: Final[bool] = sys.platform == "darwin"
IS_POSIX: Final[bool] = os.name == "posix"  # Covers BSD, Linux, and macOS.
IS_WINDOWS: Final[bool] = sys.platform == "win32"

__all__: Final[tuple[str, ...]] = (
    "IS_LINUX",
    "IS_MACOS",
    "IS_POSIX",
    "IS_WINDOWS",
)
