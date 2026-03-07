"""Public API for the command-line interface framework."""

from typing import Final

from .ansi import (
    BACKGROUND_COLORS_256,
    BackgroundColors,
    FOREGROUND_COLORS_256,
    ForegroundColors,
    RESET,
    TextAttributes,
)
from .cli_program import CLIProgram
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
    iter_stdin_file_names,
    read_text_files,
    write_text_file,
)
from .os_info import (
    IS_LINUX,
    IS_MACOS,
    IS_POSIX,
    IS_WINDOWS,
)
from .patterns import (
    compile_combined_patterns,
    compile_patterns,
    matches_all_patterns,
)
from .render import (
    bold,
    dim,
    reverse_video,
    style,
    style_pattern_matches,
)
from .reporters import (
    raises,
    suppress,
)
from .terminal import (
    stderr_is_redirected,
    stderr_is_terminal,
    stdin_is_redirected,
    stdin_is_terminal,
    stdout_is_redirected,
    stdout_is_terminal,
)
from .text import (
    decode_python_escape_sequences,
    iter_nonempty_lines,
    iter_normalized_lines,
    split_csv,
    split_regex,
    split_shell_style,
    strip_trailing_newline,
)
from .text_program import TextProgram
from .types import (
    CompiledPatterns,
    ErrorReporter,
    JsonArray,
    JsonObject,
    KeyValuePairs,
    MultipartFiles,
    QueryParameters,
)

__all__: Final[tuple[str, ...]] = (
    # ansi
    "BACKGROUND_COLORS_256",
    "BackgroundColors",
    "FOREGROUND_COLORS_256",
    "ForegroundColors",
    "RESET",
    "TextAttributes",

    # base classes
    "CLIProgram",
    "TextProgram",

    # ini
    "get_bool_option",
    "get_float_option",
    "get_int_option",
    "get_json_option",
    "get_str_option",
    "get_str_option_with_fallback",
    "get_str_options",
    "has_defaults",
    "has_sections",
    "is_empty",
    "read_options",

    # io
    "FileInfo",
    "iter_stdin_file_names",
    "read_text_files",
    "write_text_file",

    # os_info
    "IS_LINUX",
    "IS_MACOS",
    "IS_POSIX",
    "IS_WINDOWS",

    # patterns
    "compile_combined_patterns",
    "compile_patterns",
    "matches_all_patterns",

    # render
    "bold",
    "dim",
    "reverse_video",
    "style",
    "style_pattern_matches",

    # reporters
    "raises",
    "suppress",

    # terminal
    "stderr_is_redirected",
    "stderr_is_terminal",
    "stdin_is_redirected",
    "stdin_is_terminal",
    "stdout_is_redirected",
    "stdout_is_terminal",

    # text
    "decode_python_escape_sequences",
    "iter_nonempty_lines",
    "iter_normalized_lines",
    "split_csv",
    "split_regex",
    "split_shell_style",
    "strip_trailing_newline",

    # types
    "CompiledPatterns",
    "ErrorReporter",
    "JsonArray",
    "JsonObject",
    "KeyValuePairs",
    "MultipartFiles",
    "QueryParameters",
)
