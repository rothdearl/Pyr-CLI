"""
Initialization file for the command-line interface package.
"""

from .ansi import *
from .cli_program import CLIProgram
from .constants import *

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
    read_options
)

from .io import (
    FileInfo,
    print_normalized_line,
    read_files,
    write_text_to_file
)

from .patterns import (
    color_pattern_matches,
    combine_patterns,
    compile_patterns,
    text_matches_patterns
)

from .terminal import (
    input_is_redirected,
    input_is_terminal,
    output_is_terminal
)

from .types import (
    CompiledPatterns,
    ErrorReporter,
    Json,
    PatternGroups
)
