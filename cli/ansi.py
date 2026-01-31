"""
Constants and functions for ANSI escape sequences used for terminal text attributes and color output.
"""

from typing import Final

# Escape with the Control Sequence Introducer.
_CSI: Final[str] = "\x1b["

# Controls.
RESET: Final[str] = f"{_CSI}0m"

# Text attributes (SGR codes 1–9 except 6 which is undefined)
TEXT_ATTRIBUTES: Final[list[str]] = [f"{_CSI}{code}m" for code in (1, 2, 3, 4, 5, 7, 8, 9)]

# 16-color palettes.
BG_COLORS_16: Final[list[str]] = [f"{_CSI}{code}m" for code in (*range(40, 48), *range(100, 108))]
COLORS_16: Final[list[str]] = [f"{_CSI}{code}m" for code in (*range(30, 38), *range(90, 98))]

# 256-color palettes (xterm-compatible).
BG_COLORS_256: Final[list[str]] = [f"{_CSI}48;5;{code}m" for code in range(256)]
COLORS_256: Final[list[str]] = [f"{_CSI}38;5;{code}m" for code in range(256)]


def _normalize_index(index: int, max_index: int) -> int:
    """
    Normalize an index to a valid range, defaulting to ``0`` if the index is out of range.

    :param index: Index to normalize.
    :param max_index: Exclusive upper bound for valid indexes.
    :return: A normalized index.
    """
    return index if 0 <= index < max_index else 0


def text_attribute(index: int) -> str:
    """
    Return a text attribute, defaulting to ``0`` if the index is out of range.

    :param index: Index of the text attribute.
    :return: Text attribute.
    """
    return TEXT_ATTRIBUTES[_normalize_index(index, len(TEXT_ATTRIBUTES))]


def background_color_16(index: int) -> str:
    """
    Return a background color from the 16-color palette, defaulting to ``0`` if the index is out of range.

    :param index: Index of the background color.
    :return: Background color.
    """
    return BG_COLORS_16[_normalize_index(index, len(BG_COLORS_16))]


def background_color_256(index: int) -> str:
    """
    Return a background color from the 256-color palette, defaulting to ``0`` if the index is out of range.

    :param index: Index of the background color.
    :return: Background color.
    """
    return BG_COLORS_256[_normalize_index(index, len(BG_COLORS_256))]


def foreground_color_16(index: int) -> str:
    """
    Return a foreground color from the 16-color palette, defaulting to ``0`` if the index is out of range.

    :param index: Index of the foreground color.
    :return: Foreground color.
    """
    return COLORS_16[_normalize_index(index, len(COLORS_16))]


def foreground_color_256(index: int) -> str:
    """
    Return a foreground color from the 256-color palette, defaulting to ``0`` if the index is out of range.

    :param index: Index of the foreground color.
    :return: Foreground color.
    """
    return COLORS_256[_normalize_index(index, len(COLORS_256))]


__all__ = [
    "BG_COLORS_16",
    "BG_COLORS_256",
    "COLORS_16",
    "COLORS_256",
    "RESET",
    "TEXT_ATTRIBUTES",
    "background_color_16",
    "background_color_256",
    "foreground_color_16",
    "foreground_color_256",
    "text_attribute"
]
