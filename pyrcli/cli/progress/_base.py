"""Abstract base class for terminal progress indicators that update a single line in place and emit an optional final message."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import TracebackType
from typing import Final, Self, TextIO, final

from ._render import _LineWriter
from .types import ProgressMessage, ProgressMessagePosition


@dataclass(kw_only=True, slots=True)
class _ProgressIndicator(ABC):
    """
    Base class for terminal progress indicators that update a single line in place and emit an optional final message.

    Attributes:
        text_stream: Text stream where output is written.
        visible: Whether dynamic progress output is rendered.
        final_message: Optional message written on finalization (empty strings are treated as no message).
        message_position: Whether the message appears to the left or right of the indicator (default: ``right``).
    """

    text_stream: Final[TextIO]
    visible: Final[bool] = True
    final_message: ProgressMessage = None
    message_position: ProgressMessagePosition = "right"
    _finished: bool = field(default=False, init=False, repr=False)
    _writer: _LineWriter = field(init=False, repr=False)

    def __enter__(self) -> Self:
        """Return the indicator for use in a context manager."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        """Finalize the indicator on context exit."""
        self.finalize()
        return False

    def __post_init__(self) -> None:
        """Initialize internal state."""
        self._writer = _LineWriter(text_stream=self.text_stream, enabled=self.visible)

    @final
    def _finalize_with_message(self, message: ProgressMessage) -> None:
        """Clear the indicator line and, if ``message`` is non-empty, write it followed by a newline."""
        self._writer.clear()

        if message:
            self._writer.write(message)
            self._writer.newline()

    @abstractmethod
    def _render_final(self, message: ProgressMessage) -> None:
        """Render the final indicator state and terminate the line when appropriate."""
        ...

    @final
    def finalize(self) -> None:
        """Finalize the indicator (idempotent) and emit any final output."""
        if self._finished:
            return

        self._finished = True

        if self.visible:
            self._render_final(self.final_message)
        elif self.final_message:
            self.text_stream.write(self.final_message + "\n")
            self.text_stream.flush()
