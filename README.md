# Writing a New Command-Line Program

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
- version string
- error exit code (optional; defaults to 1)

``` python
def __init__(self) -> None:
    super().__init__(name="myprog", version="1.0.0")
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

Handled automatically in CLIProgram:

- color enablement (disabled when stdout is redirected)

Handled additionally in TextProgram:

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
if __name__ == "__main__":
    MyProgram().run()
```

The `run()` method guarantees:

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

- Inherit from CLIProgram or TextProgram
- Call `super().__init__(name=..., version=...)`
- Implement `build_arguments`
- Implement `main`
- Use validation hooks appropriately
- Use `print_error` / `print_error_and_exit`
- Use `run()` in the entry point

### For text programs

- Inherit from TextProgram
- Implement `handle_text_stream`
- Use `process_text_files` for file input
- Do not manually open text files

------------------------------------------------------------------------

## Design Principles

- Follow the standard lifecycle; do not bypass `run()`
- Separate dependency checks, range validation, normalization, and runtime initialization
- Comments should explain intent, not mechanics
- Functions should read clearly, behave predictably, and have documentation that matches reality

------------------------------------------------------------------------

## Minimal Examples

### Non-text program

``` python
class Echo(CLIProgram):
    def __init__(self) -> None:
        super().__init__(name="echo", version="1.0.0")

    def build_arguments(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("message")
        parser.add_argument("--color", choices=("on", "off"), default="on")
        return parser

    def main(self) -> None:
        print(self.args.message)
```

------------------------------------------------------------------------

### Text-processing program

``` python
class CountLines(TextProgram):
    def __init__(self) -> None:
        super().__init__(name="countlines", version="1.0.0")

    def build_arguments(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("files", nargs="*")
        parser.add_argument("--color", choices=("on", "off"), default="on")
        parser.add_argument("--latin1", action="store_true")
        return parser

    def handle_text_stream(self, file_info: FileInfo) -> None:
        count = sum(1 for _ in file_info.text_stream)
        print(f"{count} {file_info.file_name}")

    def main(self) -> None:
        self.process_text_files(self.args.files)
```
