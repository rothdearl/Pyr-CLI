"""Initialization file for the command-line interface package."""

from .ansi import (
    BG_COLORS_256,
    BgColors,
    COLORS_256,
    Colors,
    RESET,
    TextAttributes,
)

from .cli_program import CLIProgram

from .constants import (
    OS_IS_LINUX,
    OS_IS_MAC,
    OS_IS_POSIX,
    OS_IS_WINDOWS,
)

from .ini import (
    get_bool_option,
    get_float_option,
    get_int_option,
    get_json_option,
    get_str_option,
    get_str_option_with_fallback,
    get_str_options,
    has_defaults,
    has_sections,
    is_empty,
    read_options,
)

from .io import (
    FileInfo,
    normalize_input_lines,
    read_text_files,
    remove_trailing_newline,
    write_text_to_file,
)

from .patterns import (
    color_pattern_matches,
    compile_combined_patterns,
    compile_patterns,
    matches_all_patterns,
)

from .terminal import (
    stdin_is_redirected,
    stdin_is_terminal,
    stdout_is_redirected,
    stdout_is_terminal,
)

from .text import (
    split_csv,
    split_regex,
    split_shell_style,
)

from .types import (
    CompiledPatterns,
    ErrorReporter,
    JsonObject,
)
