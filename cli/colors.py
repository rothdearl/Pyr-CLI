"""
Module for ANSI escape sequences.
"""

# Escape with the Control Sequence Introducer.
_ESC = "\x1b["

# Controls.
RESET = f"{_ESC}0m"
REVERSE = f"{_ESC}7m"

# Text attributes.
BLINK = f"{_ESC}5m"
BOLD = f"{_ESC}1m"
DIM = f"{_ESC}2m"
INVISIBLE = f"{_ESC}8m"
ITALICS = f"{_ESC}3m"
STRIKETHROUGH = f"{_ESC}9m"
UNDERLINE = f"{_ESC}4m"

# Foreground colors.
BLACK = f"{_ESC}30m"
BLUE = f"{_ESC}34m"
BRIGHT_BLACK = f"{_ESC}90m"
BRIGHT_BLUE = f"{_ESC}94m"
BRIGHT_CYAN = f"{_ESC}96m"
BRIGHT_GREEN = f"{_ESC}92m"
BRIGHT_MAGENTA = f"{_ESC}95m"
BRIGHT_RED = f"{_ESC}91m"
BRIGHT_WHITE = f"{_ESC}97m"
BRIGHT_YELLOW = f"{_ESC}93m"
CYAN = f"{_ESC}36m"
GREEN = f"{_ESC}32m"
MAGENTA = f"{_ESC}35m"
RED = f"{_ESC}0;31m"
WHITE = f"{_ESC}37m"
YELLOW = f"{_ESC}33m"

# Background colors.
BG_BLACK = f"{_ESC}40m"
BG_BLUE = f"{_ESC}44m"
BG_BRIGHT_BLACK = f"{_ESC}100m"
BG_BRIGHT_BLUE = f"{_ESC}104m"
BG_BRIGHT_CYAN = f"{_ESC}106m"
BG_BRIGHT_GREEN = f"{_ESC}102m"
BG_BRIGHT_MAGENTA = f"{_ESC}105m"
BG_BRIGHT_RED = f"{_ESC}101m"
BG_BRIGHT_WHITE = f"{_ESC}107m"
BG_BRIGHT_YELLOW = f"{_ESC}103m"
BG_CYAN = f"{_ESC}46m"
BG_GREEN = f"{_ESC}42m"
BG_MAGENTA = f"{_ESC}45m"
BG_RED = f"{_ESC}41m"
BG_WHITE = f"{_ESC}47m"
BG_YELLOW = f"{_ESC}43m"
