"""CLI framework for the PyForge toolkit."""

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
    iter_stdin_file_names,
    read_text_files,
    write_text_to_file,
)

from .patterns import (
    compile_combined_patterns,
    compile_patterns,
    matches_all_patterns,
)

from .render import (
    color_pattern_matches,
    reverse_video,
)

from .terminal import (
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
    JsonObject,
)
