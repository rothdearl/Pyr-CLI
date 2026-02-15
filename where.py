#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A program that displays current ip-based location information."""

import argparse
import sys
from typing import Final

import requests


def build_arguments() -> argparse.ArgumentParser:
    """Build and return an argument parser."""
    parser = argparse.ArgumentParser(allow_abbrev=False, description="display current ip-based location information",
                                     prog=Where.NAME)

    parser.add_argument("-c", "--coordinates", action="store_true",
                        help="display geographic coordinates")
    parser.add_argument("--ip", action="store_true", help="display public ip address")
    parser.add_argument("--version", action="version", version=f"%(prog)s {Where.VERSION}")

    return parser


class Where:
    """
    A program that displays current ip-based location information.

    :cvar IPINFO_URL: Endpoint returning public IP geolocation data in JSON.
    :cvar NAME: Program name.
    :cvar VERSION: Program version.
    :ivar args: Parsed command-line arguments.
    """

    IPINFO_URL = "https://ipinfo.io/json"
    NAME: Final[str] = "where"
    VERSION: Final[str] = "1.0.0"

    def __init__(self) -> None:
        """Initialize a new ``When`` instance."""
        self.args: argparse.Namespace = build_arguments().parse_args()

    def main(self) -> None:
        """Run the program."""
        try:
            response = requests.get(Where.IPINFO_URL)
            data = response.json()

            # Print geolocation information, optionally geographic location, and public ip address.
            for key in ("city", "region", "postal", "country", "timezone"):
                print(f"{key}: {data[key]}")

            if self.args.coordinates:  # --coordinates
                latitude, longitude = data["loc"].split(",")

                print(f"latitude: {latitude}")
                print(f"longitude: {longitude}")

            if self.args.ip:  # --ip
                print(f"ip: {data['ip']}")
        except requests.RequestException:
            print(f"{Where.NAME}: error: unable to retrieve location", file=sys.stderr)
            raise SystemExit(1)


if __name__ == "__main__":
    Where().main()
