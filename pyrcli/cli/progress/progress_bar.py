"""Terminal progress bar for tracking work with a known total."""

from dataclasses import dataclass, field
from typing import ClassVar, Final, final

from pyrcli.cli import ansi
from ._base import _ProgressIndicator
from .types import ProgressMessage


@final
@dataclass(kw_only=True, slots=True)
class ProgressBarLayout:
    """
    Configuration for rendering a terminal progress bar.

    :ivar width: Number of character cells used for the bar body.
    :ivar fill: Glyph used to represent completed progress.
    :ivar empty: Glyph used to represent remaining progress.
    :ivar left: Left delimiter placed before the bar body.
    :ivar right: Right delimiter placed after the bar body.
    :ivar show_percent: Whether to append a percentage suffix (value + ``%``).
    :ivar percent_style: ANSI SGR prefix applied to the percent value (empty disables styling).
    :ivar percent_symbol_style: ANSI SGR prefix applied to the percent symbol (empty disables styling).
    :ivar percent_reset: ANSI reset sequence appended after styled percent segments; empty disables automatic reset.
    """
    _DEFAULT_WIDTH: ClassVar[int] = 20

    width: int = _DEFAULT_WIDTH
    fill: str = "·"
    empty: str = " "
    left: str = "["
    right: str = "]"
    show_percent: bool = True
    percent_style: str = ""
    percent_symbol_style: str = ""
    percent_reset: str = ansi.RESET

    def __post_init__(self) -> None:
        """Initialize and normalize configuration."""
        self.width = self.width if self.width > 0 else self._DEFAULT_WIDTH


@final
@dataclass(kw_only=True, slots=True)
class ProgressBar(_ProgressIndicator):
    """
    Terminal progress bar for tracking work with a known total.

    - Displays a horizontal progress bar for work with a known total.
    - Updates the rendered bar when progress advances.
    - Clamps progress to ``[0, total]`` when total > 0; otherwise clamps to ``[0, ∞]`` while rendering as permanently 100%.
    - Treats non-positive totals as permanently 100%.
    - Finalizes by either retaining or clearing the bar according to ``clear_on_finish``.
    - Writes a final message followed by a newline when a message is provided, even when the indicator is not visible.
    - Treats empty messages as no message.

    :ivar total: Total number of units representing 100% completion (non-positive values render as permanently 100%).
    :ivar layout: Rendering layout for the progress bar.
    :ivar clear_on_finish: Whether to clear the progress bar on finalization (message behavior is unchanged).
    """

    total: int
    layout: ProgressBarLayout = field(default_factory=ProgressBarLayout)
    clear_on_finish: bool = False
    _completed: int = field(default=0, init=False, repr=False)

    def _fraction_completed(self, completed: int) -> float:
        """Return the fraction of work completed, or ``1.0`` if ``total <= 0``."""
        if self.total <= 0:
            return 1.0

        return float(completed / self.total)

    def _render_bar(self, fraction: float) -> str:
        """Return a rendered progress bar for a completion fraction in ``[0, 1]``."""
        filled_cells = int(fraction * self.layout.width)
        empty_cells = self.layout.width - filled_cells
        bar = f"{self.layout.left}{self.layout.fill * filled_cells}{self.layout.empty * empty_cells}{self.layout.right}"

        if not self.layout.show_percent:
            return bar

        return f"{bar} {self._render_percent(int(fraction * 100))}"

    def _render_final(self, message: ProgressMessage) -> None:
        """Render the final indicator state and terminate the line when appropriate."""
        if self.clear_on_finish:
            self._finalize_with_message(message)
            return

        bar = self._render_bar(self._fraction_completed(self._completed))

        self._writer.write_composed(indicator=bar, message=message, position=self.message_position)
        self._writer.newline()

    def _render_percent(self, percent: int) -> str:
        """Return a percent suffix (e.g., ``100%``), applying layout SGR styles when configured."""
        return (
            f"{self.layout.percent_style}"
            f"{percent:3d}"
            f"{self.layout.percent_symbol_style}%"
            f"{self.layout.percent_reset}"
        )

    def advance(self, step: int = 1, *, message: ProgressMessage = None) -> None:
        """Increment progress by ``step`` units and redraw the bar."""
        self.update(self._completed + step, message=message)

    def complete(self) -> None:
        """Mark all units as completed and redraw the bar."""
        self.update(self.total)

    def start(self, *, message: ProgressMessage = None) -> None:
        """Render the initial 0% progress state with an optional message."""
        self.update(0, message=message)

    def update(self, completed: int, *, message: ProgressMessage = None) -> None:
        """Redraw the progress bar for the completed units."""
        if self._finished:
            return

        if self.total <= 0:
            clamped = max(0, completed)
        else:
            clamped = max(0, min(self.total, completed))

        bar = self._render_bar(self._fraction_completed(clamped))

        self._writer.write_composed(indicator=bar, message=message, position=self.message_position)
        self._completed = clamped


__all__: Final[tuple[str, ...]] = (
    "ProgressBar",
    "ProgressBarLayout",
)
