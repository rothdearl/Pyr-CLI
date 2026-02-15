#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that displays the current calendar, with optional date and time."""

import argparse
import calendar
import datetime
import sys
from typing import Final, NamedTuple

from cli import ansi, OS_IS_POSIX


class CalendarQuarterColumnBounds(NamedTuple):
    """Column bounds for a month within a quarter row from ``calendar.calendar(..., m=3)`` output."""
    start: int
    end: int


def build_arguments() -> argparse.ArgumentParser:
    """Build and return an argument parser."""
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                     description="display a calendar, optionally with date and time",
                                     epilog="datetime format is interpreted using strftime(3)", prog=When.NAME)

    parser.add_argument("-c", "--calendar", choices=("m", "q", "y"), default="m",
                        help="print calendar as a month, quarter, or year (default: m)")
    parser.add_argument("-w", "--week-start", choices=("mon", "sun"), default="mon",
                        help="use monday or sunday as first day of the week (default: mon)")
    parser.add_argument("-d", "--datetime", action="store_true", help="print current date and time after calendar")
    parser.add_argument("--datetime-format", help="use STRING as datetime format", metavar="STRING")
    parser.add_argument("--version", action="version", version=f"%(prog)s {When.VERSION}")

    return parser


def get_quarter_column_bounds_for_month(month: int) -> CalendarQuarterColumnBounds:
    """Return character column bounds for a month within a quarter row of ``calendar.calendar(..., m=3)`` output."""
    bounds_by_index = (
        CalendarQuarterColumnBounds(0, 20),
        CalendarQuarterColumnBounds(26, 46),
        CalendarQuarterColumnBounds(52, 72)
    )

    return bounds_by_index[(month - 1) % 3]


def highlight(text: str) -> str:
    """Return the text wrapped in reverse-video ANSI escape codes."""
    return f"{ansi.TextAttributes.REVERSE}{text}{ansi.RESET}"


def highlight_day_within_bounds(line: str, day: str, bounds: CalendarQuarterColumnBounds) -> str:
    """Return the line with a day highlighted only within the bounds."""
    colored_text = line[bounds.start:bounds.end].replace(day, highlight(day))

    return line[:bounds.start] + colored_text + line[bounds.end:]


def print_month(text_calendar: calendar.TextCalendar) -> None:
    """Print the current month."""
    date = datetime.date.today()
    month = text_calendar.formatmonth(date.year, date.month, w=0, l=0).splitlines()

    # Print year header and the days of the week.
    print(month[0])
    print(month[1])

    # Print weeks highlighting the current day of the month.
    day = f"{date.day:>2}"
    found_day = False

    for output in month[2:]:
        if not found_day and day in output:
            output = output.replace(day, highlight(day))
            found_day = True

        print(output)


def print_quarter(text_calendar: calendar.TextCalendar) -> None:
    """Print all months in the current quarter."""
    date = datetime.date.today()
    month_name = calendar.month_name[date.month]
    quarter_bounds = get_quarter_column_bounds_for_month(date.month)
    year = text_calendar.formatyear(date.year, w=2, l=1, c=6, m=3).splitlines()  # Use defaults for consistency.

    # Print year header.
    print(year[0])
    print()

    # Find current quarter.
    quarter_start = 2

    for output in year[quarter_start:]:
        if month_name in output:
            break

        quarter_start += 1

    # Highlight current month name.
    year[quarter_start] = year[quarter_start].replace(month_name, highlight(month_name))

    # Print month names and weekdays.
    print(year[quarter_start])
    print(year[quarter_start + 1])

    # Print weeks highlighting the current day of the month.
    day = f"{date.day:>2}"
    found_day = False

    for output in year[quarter_start + 2:]:
        if not output:  # End of quarter?
            break

        if not found_day and day in output[quarter_bounds.start:quarter_bounds.end]:
            output = highlight_day_within_bounds(output, day, quarter_bounds)
            found_day = True

        print(output)


def print_year(text_calendar: calendar.TextCalendar) -> None:
    """Print all months in the current year."""
    date = datetime.date.today()
    month_name = calendar.month_name[date.month]
    quarter_bounds = get_quarter_column_bounds_for_month(date.month)
    year = text_calendar.formatyear(date.year, w=2, l=1, c=6, m=3).splitlines()  # Use defaults for consistency.

    # Print months highlighting the current month and day.
    day = f"{date.day:>2}"
    found_day, found_month = False, False

    for output in year:
        if not found_month and month_name in output:
            output = output.replace(month_name, highlight(month_name))
            found_month = True

        if not found_day and found_month and day in output[quarter_bounds.start:quarter_bounds.end]:
            output = highlight_day_within_bounds(output, day, quarter_bounds)
            found_day = True

        print(output)


class When:
    """
    A program that displays the current calendar, with optional date and time.

    :cvar DEFAULT_DATETIME_FORMAT: Default format for printing the date and time.
    :cvar NAME: Program name.
    :cvar VERSION: Program version.
    :ivar args: Parsed command-line arguments.
    """

    DEFAULT_DATETIME_FORMAT: Final[str] = "%a %b %-d %-I:%M%p" if OS_IS_POSIX else "%a %b %d %I:%M%p"
    NAME: Final[str] = "when"
    VERSION: Final[str] = "1.0.8"

    def __init__(self) -> None:
        """Initialize a new ``When`` instance."""
        self.args: argparse.Namespace = build_arguments().parse_args()

    def main(self) -> None:
        """Run the program."""
        text_calendar = calendar.TextCalendar(calendar.SUNDAY if self.args.week_start == "sun" else calendar.MONDAY)

        match self.args.calendar:  # --calendar
            case "m":
                print_month(text_calendar)
            case "q":
                print_quarter(text_calendar)
            case _:
                print_year(text_calendar)

        if self.args.datetime:  # --datetime
            date_format = self.args.datetime_format or When.DEFAULT_DATETIME_FORMAT  # --datetime-format
            now = datetime.datetime.now()

            try:
                print()
                print(now.strftime(date_format))
            except ValueError:  # Raised for invalid format directives on Windows; unreachable on POSIX.
                print(f"{When.NAME}: error: invalid datetime format", file=sys.stderr)
                raise SystemExit(1)


if __name__ == "__main__":
    When().main()
