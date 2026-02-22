"""Constants used throughout the command-line interface package."""

import os
import sys
from typing import Final

# OS-related constants.
OS_IS_LINUX: Final[bool] = sys.platform.startswith("linux")
OS_IS_MAC: Final[bool] = sys.platform == "darwin"
OS_IS_POSIX: Final[bool] = os.name == "posix"
OS_IS_WINDOWS: Final[bool] = sys.platform == "win32"

__all__: list[str] = [
    "OS_IS_LINUX",
    "OS_IS_MAC",
    "OS_IS_POSIX",
    "OS_IS_WINDOWS",
]
