import os
from abc import ABC
from typing import final

from cli import CLIProgram


@final
class CLIProgramRunner(ABC):
    """
    Utility class for running a CLI program.
    """

    @staticmethod
    def run(program: CLIProgram) -> None:
        """
        Runs the program.
        :param program: The command-line program.
        :return: None
        """
        keyboard_interrupt_error_code = 130
        windows = os.name == "nt"

        try:
            if windows:  # Fix ANSI escape sequences on Windows.
                from colorama import just_fix_windows_console

                just_fix_windows_console()
            else:  # Prevent broken pipe errors (not supported on Windows).
                from signal import SIG_DFL, SIGPIPE, signal

                signal(SIGPIPE, SIG_DFL)

            program.parse_arguments()
            program.main()
            program.check_for_errors()
        except KeyboardInterrupt:
            print()  # Add a newline after Ctrl-C.
            raise SystemExit(program.ERROR_EXIT_CODE if windows else keyboard_interrupt_error_code)
        except OSError:
            raise SystemExit(program.ERROR_EXIT_CODE)
