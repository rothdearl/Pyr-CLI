#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that displays current IP-based location information."""

import argparse
import sys
from typing import Final

import requests

from cli import JsonObject


def build_arguments() -> argparse.ArgumentParser:
    """Build and return an argument parser."""
    parser = argparse.ArgumentParser(allow_abbrev=False, description="display current ip-based location information",
                                     epilog="location data provided by ipinfo.io", prog=Where.NAME)

    parser.add_argument("-c", "--coordinates", action="store_true",
                        help="display geographic coordinates")
    parser.add_argument("--coordinate-format", choices=("numeric", "cardinal"), default="numeric",
                        help="format geographic coordinates as signed values or with N/S/E/W suffixes (default: numeric; use with --coordinates)")
    parser.add_argument("--ip", action="store_true", help="display public ip address")
    parser.add_argument("--version", action="version", version=f"%(prog)s {Where.VERSION}")

    return parser


def format_coordinates_cardinal(coordinates: str) -> str:
    """Return coordinates in a human-readable cardinal format."""
    try:
        lat_str, lon_str = (part.strip() for part in coordinates.split(",", 1))

        # Determine directions for coordinates.
        lat = float(lat_str)
        lat_dir = "S" if lat < 0 else "N"
        lon = float(lon_str)
        lon_dir = "W" if lon < 0 else "E"

        return f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"
    except (AttributeError, ValueError):
        return "n/a"


def get_json_value(*, data: JsonObject, key: str) -> str:
    """Return the value for a key in the JSON data, or ``"n/a"`` if the key is missing."""
    value = data.get(key)

    return value if value not in (None, "") else "n/a"


class Where:
    """
    A program that displays current IP-based location information.

    :cvar IPINFO_URL: Endpoint returning public IP geolocation data in JSON.
    :cvar NAME: Program name.
    :cvar VERSION: Program version.
    :ivar args: Parsed command-line arguments.
    """

    IPINFO_URL: Final[str] = "https://ipinfo.io/json"
    NAME: Final[str] = "where"
    VERSION: Final[str] = "1.0.1"

    def __init__(self) -> None:
        """Initialize a new ``Where`` instance."""
        self.args: argparse.Namespace = build_arguments().parse_args()

    def main(self) -> None:
        """Run the program."""
        try:
            response = requests.get(Where.IPINFO_URL, timeout=5)

            # Ensure a successful response.
            response.raise_for_status()

            # Get JSON data.
            data = response.json()

            # Ensure response data is JSON.
            if not isinstance(data, dict):
                raise requests.RequestException()

            # Print geolocation information.
            for key in ("city", "region", "postal", "country", "timezone"):
                print(f"{key}: {get_json_value(data=data, key=key)}")

            # Optionally print geographic coordinates and public IP address.
            if self.args.coordinates:  # --coordinates
                coordinates = get_json_value(data=data, key='loc')

                if self.args.coordinate_format == "cardinal":
                    print(f"coordinates: {format_coordinates_cardinal(coordinates)}")
                else:
                    print(f"coordinates: {coordinates}")

            if self.args.ip:  # --ip
                print(f"ip: {get_json_value(data=data, key='ip')}")
        except requests.RequestException:
            print(f"{Where.NAME}: error: unable to retrieve location", file=sys.stderr)
            raise SystemExit(1)


if __name__ == "__main__":
    Where().main()
