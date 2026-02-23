# Pyr-CLI

## Overview

Pyr-CLI is a toolkit of small, composable CLI programs designed for deterministic pipelines. It provides single-purpose
commands that share a common invocation model and stable output contract. Each tool performs one well-defined operation,
favors explicit behavior over implicit defaults, and composes predictably in shell pipelines unless interacting with
external state.

The project is intentionally **pedantic but practical**: behavior is specified precisely where it affects correct usage,
and kept simple where it does not.

All Pyr-CLI commands report a single, project-wide version sourced from `pyproject.toml`.

------------------------------------------------------------------------

## Design Philosophy

Pyr-CLI follows a small set of operational rules:

- **Single responsibility** --- each program performs one operation on a text stream or structured input.
- **Pipeline first** --- all tools read from `stdin` when no input file is provided and write results to `stdout`.
- **Deterministic by default** --- identical input produces identical output unless the program explicitly depends on
  time, environment, or filesystem state.
- **Explicit side effects** --- programs that touch the filesystem or external state document that behavior.
- **TTY-aware formatting** --- ANSI rendering is applied only when output is a terminal; otherwise plain text is
  emitted.
- **Stable output contracts** --- output shape and ordering are defined and suitable for downstream processing.

These constraints make the tools predictable, scriptable, and safe for composition.

------------------------------------------------------------------------

## Dependencies

Pyr-CLI targets Python ≥ 3.12.

The following third-party packages are required at runtime:

- colorama
- python-dateutil
- requests

These dependencies must be available in the active Python environment before running any Pyr-CLI commands.

------------------------------------------------------------------------

## Installation

Pyr-CLI is installed using `pip`.

### Development Install (Editable)

Create and activate a virtual environment, then install Pyr-CLI in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

This registers all Pyr-CLI commands as console scripts in the active environment.

### User Install

To install Pyr-CLI as a user-level CLI toolkit:

```bash
python3 -m pip install --user .
```

Ensure the user script directory is on your `PATH`.

------------------------------------------------------------------------

## Command Model

All Pyr-CLI commands follow the same execution model:

1. **Input resolution**
    - Read from `stdin` if no path is provided
    - Otherwise, read from the specified file(s)
2. **Normalization**
    - Input is converted to a canonical internal representation so downstream logic does not depend on superficial
      differences (line endings, trailing whitespace, etc.)
3. **Core operation**
    - A pure transformation whenever possible
4. **Output**
    - Written to `stdout`
    - Errors written to `stderr`
    - Non-zero exit codes only for user or system errors

Unless otherwise stated, tools are **stream-safe** and do not buffer the entire input unnecessarily.

------------------------------------------------------------------------

## Architecture

Pyr-CLI is layered to separate pure logic from side effects:

    Programs → CLI framework → Text/Pattern primitives → Rendering → I/O boundary

### CLI Framework

Provides:

- Program lifecycle
- Argument parsing
- Input routing
- Output discipline and exit codes

### Text and Pattern Layer

Pure, deterministic transformations used by multiple tools. These functions do not perform I/O.

### Rendering Layer

ANSI and formatting utilities. Rendering is applied only when writing to a TTY.

### I/O Boundary

All filesystem and terminal interaction is isolated here. This makes core logic testable and deterministic.

------------------------------------------------------------------------

## Output Conventions

- **stdout** --- primary program output
- **stderr** --- diagnostics and error messages
- **Exit codes**
    - `0` --- success
    - `>0` --- user error, invalid input, or system failure

Unless a tool explicitly documents ordering semantics, output preserves the input order.

------------------------------------------------------------------------

## Tools

Each tool performs one well-defined operation.

### `dupe`

A minimal, uniq-like command for filtering and reporting repeated lines.

### `emit`

A minimal, echo-like command for writing strings to standard output.

### `glue`

A minimal, cat-like command for concatenating files to standard output.

### `num`

A minimal, nl-like command for numbering lines in files.

### `order`

A minimal, sort-like command for sorting and printing lines.

### `peek`

A minimal, head-like command for printing the first part of files.

### `scan`

A minimal, grep-like command for printing lines that match patterns.

### `seek`

A minimal, find-like command for searching for files in a directory hierarchy.

### `show`

A minimal command for displaying files with optional whitespace rendering.

### `slice`

A program that splits lines in files into fields.

### `subs`

A minimal command for replacing matching text in files.

### `tally`

A minimal, wc-like command for counting lines, words, and characters in files.

### `track`

A minimal, tail-like command for printing the last part of files and following new lines.

### `when`

A minimal calendar command for displaying months, quarters, or years with optional date and time.

### `where`

A minimal command for displaying current IP-based location information.

> Each command documents its own flags and output shape via `--help`.

------------------------------------------------------------------------

## Error Handling Contract

- Invalid user input results in a non-zero exit code and a concise diagnostic on `stderr`.
- Internal errors are not silently suppressed.
- Partial output is not emitted after a fatal error unless explicitly documented.

------------------------------------------------------------------------

## Development Notes

The codebase targets modern Python and follows these principles:

- Clarity over cleverness
- Explicit semantic contracts
- Weakest correct type annotations for inputs
- Pure functions separated from I/O
- Structured docstrings describing guarantees, not implementation trivia

Contributions should preserve the single-responsibility design and the pipeline-safe execution model.

------------------------------------------------------------------------

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You may redistribute and/or modify this software under the terms of the GPL-3.0.
A copy of the license is included in the `LICENSE` file and is also available
at: https://www.gnu.org/licenses/gpl-3.0.en.html

------------------------------------------------------------------------

## Writing a New Command-Line Program

This project provides two abstract base classes that define a consistent lifecycle, error model, and I/O behavior for
all command-line tools:

- **CLIProgram** -- for general programs
- **TextProgram** -- for programs that read and process text streams

All new programs **must inherit from one of these classes**.

------------------------------------------------------------------------

## Choosing a Base Class

### Use CLIProgram when

- The program does **not** read text files
- The program operates only on arguments, the network, the filesystem, etc.

### Use TextProgram when

- The program reads from files, standard input, or text streams
- The program needs consistent handling of encodings, file iteration, and UnicodeDecodeError reporting

------------------------------------------------------------------------

## Required Structure

### Class Definition

``` python
class MyProgram(CLIProgram):  # or TextProgram
```

### Constructor

All programs **must** call `super().__init__` with:

- program name
- error exit code (optional; defaults to 1)

``` python
def __init__(self) -> None:
    super().__init__(name="myprog")
```

------------------------------------------------------------------------

## Required Methods

### From CLIProgram

Every program **must implement**:

#### build_arguments(self) -\> argparse.ArgumentParser

Define all command-line options.

#### main(self) -\> None

Implement the program's core behavior.
This method is called **after** arguments are parsed, validated, normalized, and runtime state is initialized.

------------------------------------------------------------------------

### From TextProgram

Text-processing programs **must implement**:

#### handle_text_stream(self, file_info: FileInfo) -\> None

Process a single text stream.

- `file_info.file_name` -- normalized file name
- `file_info.text_stream` -- open TextIO stream
- May raise UnicodeDecodeError (handled by the base class)

Do **not** open files manually; use the provided stream.

------------------------------------------------------------------------

## Reading Text Files

Text programs **must use**:

``` python
self.process_text_files(files)
```

This function:

- Opens files using the configured encoding
- Delegates each stream to `handle_text_stream`
- Handles UnicodeDecodeError uniformly
- Returns a list of successfully processed file names

------------------------------------------------------------------------

## Reading File Names from Standard Input

When file names are supplied via a pipe rather than as positional arguments, text programs must use:

``` python
self.process_text_files_from_stdin()
```

This function:

- Reads file names from stdin (one per line)
- Filters empty lines
- Delegates to process_text_files using the collected file list
- Preserves the same error handling and return contract

This ensures that piped file lists and argument-based file lists follow identical processing semantics.

------------------------------------------------------------------------

## Option Validation Lifecycle

All argument validation and normalization **must** be organized across these hooks:

### check_option_dependencies(self)

Enforce relationships between options.

Examples:

- one option requires another
- mutually exclusive semantic constraints

### validate_option_ranges(self)

Validate numeric and logical ranges.

Examples:

- `--count-width >= 1`
- `--skip-fields >= 1`

### normalize_options(self)

Apply derived defaults and convert values to internal form.

Examples:

- convert one-based indices to zero-based
- sort and deduplicate field lists
- infer default flags

### initialize_runtime_state(self)

Prepare internal state derived from options.

Handled automatically in `CLIProgram`:

- color enablement (disabled when stdout is redirected)

Handled additionally in `TextProgram`:

- text encoding (`utf-8` or `iso-8859-1` via `--latin1`)

------------------------------------------------------------------------

## Optional Method

### check_for_errors(self)

Override **only if** the program needs additional end-of-run validation.

The default behavior exits if any errors were recorded via `print_error`.

------------------------------------------------------------------------

## Error Reporting

Programs **must use** the provided helpers:

### self.print_error(message)

- Records an error
- Prints a formatted message to stderr
- Allows the program to continue

### self.print_error_and_exit(message)

- Prints a formatted message to stderr
- Immediately terminates with the configured exit code

Do **not** print raw error messages.

------------------------------------------------------------------------

## Program Entry Point

All programs **must** use the standardized lifecycle:

``` python
def main() -> int:
    """Run the program."""
    return MyProgram().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
```

The `run_program()` method guarantees:

1. ANSI setup (Windows compatibility)
2. SIGPIPE handling (POSIX)
3. Argument parsing
4. Validation and normalization
5. Runtime state initialization
6. Program execution
7. Consistent error handling and exit codes

------------------------------------------------------------------------

## Implementation Checklist

### For all programs

- Inherit from `CLIProgram` or `TextProgram`
- Call `super().__init__(name=...)`
- Implement `build_arguments`
- Implement `main`
- Use validation hooks appropriately
- Use `print_error` / `print_error_and_exit`
- Use `run_program()` in the entry point

### For text programs

- Inherit from `TextProgram`
- Implement `handle_text_stream`
- Use `process_text_files` for file input
- Use `process_text_files_from_stdin` for file-name input from standard input
- Do not manually open text files

------------------------------------------------------------------------

## Design Principles

- Follow the standard lifecycle; do not bypass `run_program()`
- Separate dependency checks, range validation, normalization, and runtime initialization
- Comments should explain intent, not mechanics
- Functions should read clearly, behave predictably, and have documentation that matches reality

------------------------------------------------------------------------

## Versioning (Project-Wide)

Pyr-CLI uses a **single, project-wide version number**. Individual command-line programs **must not** define or hardcode
their own version values.

### Source of Truth

- The canonical version is stored in `pyrcli.__about__.__version__`.
- The base class (`CLIProgram`) assigns this value to `self.version` during initialization.
- Command implementations **must treat** `self.version` as **read-only**.

### Usage in Programs

- Do not import `__version__` in individual program modules.
- Use the `self.version` attribute provided by the base class.
- This ensures all commands report a consistent Pyr-CLI version and eliminates per-program version duplication.
- Programs that expose a `--version` flag must implement it using `version=f"%(prog)s {self.version}`".

### Rationale

This design provides:

- A single source of truth for versioning
- Zero boilerplate in command implementations
- Consistent CLI behavior across all Pyr-CLI programs

------------------------------------------------------------------------

## Minimal Examples

### Text program

``` python
"""A program that prints files to standard output."""

import argparse
import sys
from collections.abc import Iterable
from typing import Final, override

from pyrcli.cli import TextProgram, ansi, io, terminal, text


class Colors:
    """Namespace for terminal color constants."""
    COLON: Final[str] = ansi.Colors.BRIGHT_CYAN
    FILE_NAME: Final[str] = ansi.Colors.BRIGHT_MAGENTA


class Demo(TextProgram):
    """A program that prints files to standard output."""

    def __init__(self) -> None:
        """Initialize a new ``Demo`` instance."""
        super().__init__(name="demo")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="print FILES to standard output",
                                         epilog="read from standard input when no FILES are specified", prog=self.name)

        parser.add_argument("files", help="read from FILES", metavar="FILES", nargs="*")
        parser.add_argument("-H", "--no-file-name", action="store_true", help="suppress file name prefixes")
        parser.add_argument("--color", choices=("on", "off"), default="on",
                            help="use color for file names (default: on)")
        parser.add_argument("--latin1", action="store_true", help="read FILES as latin-1 (default: utf-8)")
        parser.add_argument("--stdin-files", action="store_true", help="read FILES from standard input (one per line)")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def handle_text_stream(self, file_info: io.FileInfo) -> None:
        """Process the text stream contained in ``FileInfo``."""
        self.print_file_header(file_info.file_name)
        self.print_lines(file_info.text_stream)

    @override
    def main(self) -> None:
        """Run the program."""
        if terminal.stdin_is_redirected():
            if self.args.stdin_files:
                self.process_text_files_from_stdin()
            else:
                if standard_input := sys.stdin.readlines():
                    self.print_file_header(file_name="")
                    self.print_lines(standard_input)

            if self.args.files:  # Process any additional files.
                self.process_text_files(self.args.files)
        elif self.args.files:
            self.process_text_files(self.args.files)
        else:
            self.print_lines_from_input()

    @override
    def normalize_options(self) -> None:
        """Apply derived defaults and adjust option values for consistent internal use."""
        # Set --no-file-name to True if there are no files and --stdin-files=False.
        if not self.args.files and not self.args.stdin_files:
            self.args.no_file_name = True

    def print_file_header(self, file_name: str) -> None:
        """Print the rendered file header for ``file_name``."""
        if self.should_print_file_header():
            print(self.render_file_header(file_name, file_name_color=Colors.FILE_NAME, colon_color=Colors.COLON))

    @staticmethod
    def print_lines(lines: Iterable[str]) -> None:
        """Print lines to standard output."""
        for line in text.iter_normalized_lines(lines):
            print(line)

    def print_lines_from_input(self) -> None:
        """Read and print lines from standard input until EOF."""
        self.print_lines(sys.stdin)


def main() -> int:
    """Run the program."""
    return Demo().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
```
