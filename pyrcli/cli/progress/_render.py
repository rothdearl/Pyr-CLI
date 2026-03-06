"""Internal rendering primitives for terminal progress indicators that update a single line in-place."""

import re
from dataclasses import dataclass, field
from typing import Final, TextIO

from .types import ProgressMessage, ProgressMessagePosition

# Regular expression for ANSI CSI escape sequences.
_ANSI_RE: Final[re.Pattern[str]] = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _compose_line(*, indicator: str, message: ProgressMessage, position: ProgressMessagePosition) -> str:
    """Return a rendered line by placing ``message`` to the left or right of ``indicator``."""
    if not message:
        return indicator

    if position == "left":
        return f"{message} {indicator}"

    return f"{indicator} {message}"


def _strip_ansi(text: str) -> str:
    """Return ``text`` with ANSI CSI escape sequences removed."""
    return _ANSI_RE.sub(repl="", string=text)


def _visible_width(message: str) -> int:
    """
    Return the visible character width of ``message``, excluding ANSI CSI escape sequences.

    - Does not account for Unicode double-width characters.
    """
    return len(_strip_ansi(message))


@dataclass(kw_only=True, slots=True)
class _LineWriter:
    """Stateful helper for rewriting a single terminal line in-place."""

    text_stream: TextIO
    enabled: bool = True
    _last_visible_width: int = field(default=0, init=False, repr=False)

    def clear(self) -> None:
        """Clear the current line, if enabled."""
        if not self.enabled:
            return

        self.text_stream.write("\r" + (" " * self._last_visible_width) + "\r")
        self.text_stream.flush()
        self._last_visible_width = 0

    def newline(self) -> None:
        """Write a terminating newline, leaving the current line content as-is, if enabled."""
        if not self.enabled:
            return

        self.text_stream.write("\n")
        self.text_stream.flush()
        self._last_visible_width = 0

    def write(self, text: str) -> None:
        """Overwrite the current line with ``text`` (no trailing newline), if enabled."""
        if not self.enabled:
            return

        # Pad with spaces to fully overwrite any leftover characters from the previous render.
        visible_width = _visible_width(text)
        pad = max(0, self._last_visible_width - visible_width)

        self.text_stream.write("\r" + text + (" " * pad))
        self.text_stream.flush()
        self._last_visible_width = visible_width

    def write_composed(self, *, indicator: str, message: ProgressMessage, position: ProgressMessagePosition) -> None:
        """Write an indicator line with an optional message placed to the left or right."""
        self.write(_compose_line(indicator=indicator, message=message, position=position))
