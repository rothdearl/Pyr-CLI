"""A program that displays current IP-based location information."""

import argparse
from typing import Final, override

import requests

from pyforge.cli import CLIProgram, JsonObject


class Where(CLIProgram):
    """
    A program that displays current IP-based location information.

    :cvar IPINFO_URL: Endpoint returning public IP geolocation data in JSON.
    """

    IPINFO_URL: Final[str] = "https://ipinfo.io/json"

    def __init__(self) -> None:
        """Initialize a new ``Where`` instance."""
        super().__init__(name="where")

    @override
    def build_arguments(self) -> argparse.ArgumentParser:
        """Build and return an argument parser."""
        parser = argparse.ArgumentParser(allow_abbrev=False,
                                         description="display current ip-based location information",
                                         epilog="location data provided by ipinfo.io", prog=self.name)

        parser.add_argument("-c", "--coordinates", action="store_true", help="display geographic coordinates")
        parser.add_argument("--cardinal", action="store_true",
                            help="format coordinates with N/S/E/W suffixes (use with --coordinates)")
        parser.add_argument("--ip", action="store_true", help="display public ip address")
        parser.add_argument("--version", action="version", version=f"%(prog)s {self.version}")

        return parser

    @override
    def check_option_dependencies(self) -> None:
        """Enforce relationships and mutual constraints between command-line options."""
        # --cardinal is only meaningful with --coordinates.
        if self.args.cardinal and not self.args.coordinates:
            self.print_error_and_exit("--cardinal must be used with --coordinates")

    @staticmethod
    def format_coordinates_cardinal(coordinates: str) -> str:
        """Return coordinates in a human-readable cardinal format."""
        try:
            lat_str, lon_str = (part.strip() for part in coordinates.split(",", 1))

            # Determine hemispheres from sign.
            lat_degrees = float(lat_str)
            lat_hemisphere = "S" if lat_degrees < 0 else "N"
            lon_degrees = float(lon_str)
            lon_hemisphere = "W" if lon_degrees < 0 else "E"

            return f"{abs(lat_degrees):.4f}° {lat_hemisphere}, {abs(lon_degrees):.4f}° {lon_hemisphere}"
        except (TypeError, ValueError):
            return "n/a"

    @staticmethod
    def get_json_value(*, data: JsonObject, key: str) -> str:
        """Return the value for a key in the JSON data, or ``"n/a"`` if missing or blank."""
        value = data.get(key)

        return str(value) if value not in (None, "") else "n/a"

    @override
    def main(self) -> None:
        """Run the program."""
        try:
            response = requests.get(self.IPINFO_URL, timeout=5)

            # Ensure a successful response.
            response.raise_for_status()

            # Get JSON data.
            data = response.json()

            # Ensure response data is JSON.
            if not isinstance(data, dict):
                raise ValueError()

            # Print geolocation information.
            for key in ("city", "region", "postal", "country", "timezone"):
                print(f"{key}: {self.get_json_value(data=data, key=key)}")

            # Optionally print geographic coordinates and public IP address.
            if self.args.coordinates:
                coordinates = self.get_json_value(data=data, key='loc')

                if self.args.cardinal:
                    print(f"coordinates: {self.format_coordinates_cardinal(coordinates)}")
                else:
                    print(f"coordinates: {coordinates}")

            if self.args.ip:
                print(f"ip: {self.get_json_value(data=data, key='ip')}")
        except (ValueError, requests.RequestException):
            self.print_error_and_exit("unable to retrieve location")


def main() -> int:
    """Run the program."""
    return Where().run_program()


if __name__ == "__main__":
    raise SystemExit(main())
