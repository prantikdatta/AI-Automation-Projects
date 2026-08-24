from __future__ import annotations

import re


class LocationNormalizer:
    """
    Converts every provider's location string into one
    canonical location.

    Every provider automatically benefits.
    """

    LOCATION_MAP = {

        "mumbai": "Mumbai",

        "navi mumbai": "Mumbai",

        "thane": "Mumbai",

        "bangalore": "Bengaluru",

        "bengaluru": "Bengaluru",

        "hyderabad": "Hyderabad",

        "pune": "Pune",

        "gurgaon": "Delhi NCR",

        "gurugram": "Delhi NCR",

        "noida": "Delhi NCR",

        "new delhi": "Delhi NCR",

        "delhi": "Delhi NCR",

        "chennai": "Chennai",

        "kolkata": "Kolkata",

        "ahmedabad": "Ahmedabad",

        "remote": "Remote",

        "work from home": "Remote",

        "india": "India",

    }

    @classmethod
    def normalize(
        cls,
        location: str | None,
    ) -> str:

        if not location:

            return "Unknown"

        text = location.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        for key, value in cls.LOCATION_MAP.items():

            if key in text:

                return value

        return location.strip()