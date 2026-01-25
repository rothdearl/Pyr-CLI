#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: cal.py
Author: Roth Earl
Version: 0.0.0
Description: A program to ... TODO.
License: GNU GPLv3
"""

import calendar
import datetime
from typing import Final, NamedTuple

from cli import colors

# Define constants.
DEFAULT_DATETIME_FORMAT: Final[str] = "%a %b %-d %-I:%M%p"

QUARTER_RANGES: dict[int, tuple[int, int]] = {
    0: (52, 72),
    1: (0, 20),
    2: (26, 46)
}


class CalendarQuarterIndex(NamedTuple):
    """
    Immutable container for information about a calendar quarter index.

    :ivar start: Start of the quarter index.
    :ivar end: End of the quarter index.
    """
    start: int
    end: int


def _color_day_in_week(week: str, quarter: tuple[int, int], day: str) -> str:
    """
    TODO
    :param week: TODO
    :param quarter: TODO
    :param day: TODO
    :return: TODO
    """
    start, end = quarter

    # Split into quarters, replacing only within the middle slice.
    prefix = week[:start]
    middle = week[start:end].replace(day, _color_value(day))
    suffix = week[end:]

    return prefix + middle + suffix


def _color_value(value: str) -> str:
    """
    TODO
    :param value: TODO
    :return: TODO
    """
    return f"{colors.REVERSE}{value}{colors.RESET}"


def main() -> None:
    """
    The main function of the program.
    """
    today = datetime.date.today()

    # Weekday start will be an option, either monday (m) or sunday (s)
    if True:  # --weekday-start
        calendar.setfirstweekday(calendar.SUNDAY)

    # Which to print will be an option.
    print_month(today)
    print_quarter(today)
    print_year(today)

    # Printing the current datetime, including format, will be options: https://strftime.org/
    if True:  # --datetime
        print()
        print(datetime.datetime.now().strftime(DEFAULT_DATETIME_FORMAT), "\n")  # --datetime-format


def print_month(today: datetime.date) -> None:
    """
    Prints the current month.

    :param today: Current date.
    """
    month = calendar.month(today.year, today.month).splitlines()

    # Print the year header and the days of the week.
    print(month[0])
    print(month[1])

    # Print the weeks highlighting the current day of the month.
    day = f"{today.day:>2}"
    found_day = False

    for week in month[2:]:
        if not found_day and day in week:
            week = week.replace(day, _color_value(day))
            found_day = True

        print(week)


def print_quarter(today: datetime.date) -> None:
    """
    Prints the current quarter.

    :param today: Current date.
    """
    month_name = calendar.month_name[today.month]
    quarter = QUARTER_RANGES[today.month % 3]
    year = calendar.calendar(today.year).splitlines()

    # Print the year header.
    print(year[0])
    print()

    # Find the current quarter.
    quarter_start = 2

    for line in year[quarter_start:]:
        if month_name in line:
            break

        quarter_start += 1

    # Highlight the current month name.
    year[quarter_start] = year[quarter_start].replace(month_name, _color_value(month_name))

    # Print the month names and weekdays.
    print(year[quarter_start])
    print(year[quarter_start + 1])

    # Print the weeks highlighting the current day of the current month.
    day = f"{today.day:>2}"
    found_day = False

    for week in year[quarter_start + 2:]:
        if not week:  # End of quarter?
            break

        if not found_day and day in week[quarter[0]:quarter[1]]:
            week = _color_day_in_week(week, quarter, day)
            found_day = True

        print(week)


def print_year(today: datetime.date) -> None:
    """
    Prints the current year.

    :param today: Current date.
    """
    month_name = calendar.month_name[today.month]
    quarter = QUARTER_RANGES[today.month % 3]
    year = calendar.calendar(today.year).splitlines()

    # Print the weeks highlighting the current day of the current month.
    day = f"{today.day:>2}"
    found_day, found_month = False, False

    for line in year:
        if not found_month and month_name in line:
            line = line.replace(month_name, _color_value(month_name))
            found_month = True

        if not found_day and found_month and day in line[quarter[0]:quarter[1]]:
            line = _color_day_in_week(line, quarter, day)
            found_day = True

        print(line)


if __name__ == "__main__":
    main()
