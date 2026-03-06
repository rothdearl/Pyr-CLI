"""Terminal spinner for tracking work with an unknown total."""

from dataclasses import dataclass, field
from typing import Final, final

from ._base import _ProgressIndicator
from .types import ProgressMessage

# Default glyphs when no custom sequence is provided (cycled in order).
_DEFAULT_SPINNER_FRAMES: Final[tuple[str, ...]] = ("-", "\\", "|", "/")


@final
@dataclass(kw_only=True, slots=True)
class Spinner(_ProgressIndicator):
    """
    Terminal spinner for tracking work with an unknown total.

    - Displays a spinner by cycling through configured glyphs for work with an unknown total.
    - Advances by cycling through configured glyphs.
    - Clears the rendered frame on finalization.
    - Writes a final message followed by a newline when a message is provided, even when the indicator is not visible.
    - Treats empty messages as no message.

    Attributes:
        frames: Spinner glyph sequence cycled on each call to ``advance``.
    """

    frames: tuple[str, ...] = _DEFAULT_SPINNER_FRAMES
    _frame_index: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize and normalize configuration."""
        # Explicit super() call required for slotted dataclass inheritance on Python ≤ 3.12.
        super(Spinner, self).__post_init__()

        self.frames = tuple(self.frames) or _DEFAULT_SPINNER_FRAMES

    def _render_final(self, message: ProgressMessage) -> None:
        """Render the final indicator state and terminate the line when appropriate."""
        self._finalize_with_message(message)

    def advance(self, *, message: ProgressMessage = None) -> None:
        """Advance the spinner by one frame and redraw the current line."""
        if self._finished:
            return

        glyph = self.frames[self._frame_index % len(self.frames)]

        self._writer.write_composed(indicator=glyph, message=message, position=self.message_position)
        self._frame_index += 1


__all__: Final[tuple[str, ...]] = ("Spinner",)
