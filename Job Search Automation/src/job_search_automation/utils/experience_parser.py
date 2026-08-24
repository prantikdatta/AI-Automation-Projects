from __future__ import annotations

import re
from typing import Optional


class ExperienceParser:
    """
    Utility class for extracting the minimum required years of
    experience from unstructured job descriptions.

    Returns:
        float | None
    """

    PATTERNS = [

        # 5-7 years
        r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        # 5 to 7 years
        r"(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        # 5+ years
        r"(\d+(?:\.\d+)?)\+\s*(?:years?|yrs?)",

        # minimum 5 years
        r"(?:minimum|min\.?)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        # at least 5 years
        r"(?:at\s+least)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        # 5 years
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
    ]

    @classmethod
    def parse(
        cls,
        text: str,
    ) -> Optional[float]:

        if not text:
            return None

        text = text.lower()

        if "fresher" in text or "freshers" in text:
            return 0.0

        for pattern in cls.PATTERNS:

            match = re.search(pattern, text)

            if not match:
                continue

            try:
                return float(match.group(1))
            except ValueError:
                continue

        return None