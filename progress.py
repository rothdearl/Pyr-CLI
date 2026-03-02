#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that demos using progress indicators."""

import argparse
import sys
import time
from typing import NoReturn, override

from pyrcli.cli import CLIProgram, terminal
from pyrcli.cli.progress import ProgressBar, Spinner


class CLIProgramDemo(CLIProgram):
    def __init__(self) -> None:
        """Initialize a new ``CLIProgramDemo`` instance."""
        super().__init__(name="demo")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False, description="demo using progress indicators",
                                         prog=self.name)

        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def execute(self) -> None:
        files = ("file_1", "file_2", "file_3", "file_4", "file_5", "file_6", "file_7", "file_8")
        files_to_update = len(files)
        text_stream = sys.stderr
        visible = terminal.stderr_is_terminal()

        # Find files to update.
        with Spinner(text_stream=text_stream, visible=visible, message_position="left",
                     final_message=f"Found {files_to_update} files that require an update.") as spin:
            for _ in range(files_to_update * 2):
                spin.advance(message="Finding files to update")
                time.sleep(0.125)  # Simulate finding a file.

        # Download updates.
        with ProgressBar(total=files_to_update, text_stream=text_stream, visible=visible, clear_on_finish=True,
                         final_message="Updates downloaded.") as bar:
            bar.start(message="Connecting to server...")
            time.sleep(.5)  # Simulate connecting to a server.

            for file_index, _ in enumerate(files, start=1):
                time.sleep(.5)  # Simulate downloading a file.
                bar.advance(message=f"Downloaded{file_index:>2} of {files_to_update}")

        # Apply updates.
        with ProgressBar(total=files_to_update, text_stream=text_stream, visible=visible, clear_on_finish=True,
                         final_message="Updates applied.") as bar:
            bar.start(message="Applying updates to files...")
            time.sleep(.25)  # Simulate starting the update process.

            for file_index, _ in enumerate(files, start=1):
                time.sleep(.25)  # Simulate updating a file.
                bar.advance(message=f"Updated {file_index:>2} of {files_to_update}")

        # Perform any cleanup.
        with Spinner(text_stream=text_stream, visible=visible, message_position="left") as spin:
            for _ in range(files_to_update):
                spin.advance(message="Cleaning up")
                time.sleep(0.125)  # Simulate cleaning up.

        # Print summary.
        print(f"Downloaded and updated {files_to_update} files:")

        for file_index, file_name in enumerate(files, start=1):
            print(f"{file_index:>2}: {file_name}")


def main() -> int | NoReturn:
    """Run the command and return the exit code."""
    return CLIProgramDemo().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
