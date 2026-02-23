"""Constants for ANSI escape sequences used for terminal text attributes and color output."""

from typing import Final, final

# Control Sequence Introducer (CSI).
_CSI: Final[str] = "\x1b["

#: Reset all text attributes and colors.
RESET: Final[str] = f"{_CSI}0m"

#: 256-color palettes (xterm-compatible SGR codes 38;5;0–255 and 48;5;0–255).
BG_COLORS_256: Final[tuple[str, ...]] = tuple(f"{_CSI}48;5;{code}m" for code in range(256))
COLORS_256: Final[tuple[str, ...]] = tuple(f"{_CSI}38;5;{code}m" for code in range(256))


@final
class BgColors:
    """Namespace for background color constants from the standard 16-color palette (SGR codes 40–47 and 100–107)."""
    BLACK: Final[str] = f"{_CSI}40m"
    RED: Final[str] = f"{_CSI}41m"
    GREEN: Final[str] = f"{_CSI}42m"
    YELLOW: Final[str] = f"{_CSI}43m"
    BLUE: Final[str] = f"{_CSI}44m"
    MAGENTA: Final[str] = f"{_CSI}45m"
    CYAN: Final[str] = f"{_CSI}46m"
    WHITE: Final[str] = f"{_CSI}47m"
    BRIGHT_BLACK: Final[str] = f"{_CSI}100m"
    BRIGHT_RED: Final[str] = f"{_CSI}101m"
    BRIGHT_GREEN: Final[str] = f"{_CSI}102m"
    BRIGHT_YELLOW: Final[str] = f"{_CSI}103m"
    BRIGHT_BLUE: Final[str] = f"{_CSI}104m"
    BRIGHT_MAGENTA: Final[str] = f"{_CSI}105m"
    BRIGHT_CYAN: Final[str] = f"{_CSI}106m"
    BRIGHT_WHITE: Final[str] = f"{_CSI}107m"


@final
class Colors:
    """Namespace for foreground color constants from the standard 16-color palette (SGR codes 30–37 and 90–97)."""
    BLACK: Final[str] = f"{_CSI}30m"
    RED: Final[str] = f"{_CSI}31m"
    GREEN: Final[str] = f"{_CSI}32m"
    YELLOW: Final[str] = f"{_CSI}33m"
    BLUE: Final[str] = f"{_CSI}34m"
    MAGENTA: Final[str] = f"{_CSI}35m"
    CYAN: Final[str] = f"{_CSI}36m"
    WHITE: Final[str] = f"{_CSI}37m"
    BRIGHT_BLACK: Final[str] = f"{_CSI}90m"
    BRIGHT_RED: Final[str] = f"{_CSI}91m"
    BRIGHT_GREEN: Final[str] = f"{_CSI}92m"
    BRIGHT_YELLOW: Final[str] = f"{_CSI}93m"
    BRIGHT_BLUE: Final[str] = f"{_CSI}94m"
    BRIGHT_MAGENTA: Final[str] = f"{_CSI}95m"
    BRIGHT_CYAN: Final[str] = f"{_CSI}96m"
    BRIGHT_WHITE: Final[str] = f"{_CSI}97m"


@final
class TextAttributes:
    """Namespace for text attribute constants (SGR codes 1–9, excluding 6, which is undefined)."""
    BOLD: Final[str] = f"{_CSI}1m"
    DIM: Final[str] = f"{_CSI}2m"
    ITALIC: Final[str] = f"{_CSI}3m"
    UNDERLINE: Final[str] = f"{_CSI}4m"
    BLINK: Final[str] = f"{_CSI}5m"
    REVERSE: Final[str] = f"{_CSI}7m"
    INVISIBLE: Final[str] = f"{_CSI}8m"
    STRIKETHROUGH: Final[str] = f"{_CSI}9m"


__all__: Final[tuple[str, ...]] = (
    "BG_COLORS_256",
    "BgColors",
    "COLORS_256",
    "Colors",
    "RESET",
    "TextAttributes",
)
