from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LocationQualificationResult:
    """
    Result of evaluating whether a job location satisfies
    the requested location constraints.
    """

    qualified: bool
    matched_location: str | None = None
    remote: bool = False
    reason: str = ""


class LocationQualifier:
    """
    Normalizes and evaluates job locations.

    Location qualification is a HARD GATE.

    The qualifier accepts:
        - exact target cities
        - common city aliases
        - remote locations when remote is requested
    """

    LOCATION_ALIASES = {
        "mumbai": {
            "mumbai",
            "navi mumbai",
            "thane",
            "mumbai metropolitan region",
            "mumbai, india",
        },
        "bengaluru": {
            "bengaluru",
            "bangalore",
            "bengaluru, india",
            "bangalore, india",
        },
        "hyderabad": {
            "hyderabad",
            "hyderabad, india",
        },
        "gurugram": {
            "gurugram",
            "gurgaon",
            "gurugram, india",
            "gurgaon, india",
        },
        "remote india": {
            "remote india",
            "india remote",
            "remote - india",
            "remote, india",
        },
    }

    REMOTE_TERMS = {
        "remote",
        "work from home",
        "wfh",
        "fully remote",
        "remote india",
        "india remote",
    }

    # ----------------------------------------------------------
    # Normalization
    # ----------------------------------------------------------

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower().strip()

        value = value.replace("&", " and ")

        value = re.sub(r"[^a-z0-9\s,\-]", " ", value)

        value = re.sub(r"\s+", " ", value)

        return value.strip()

    # ----------------------------------------------------------
    # Remote detection
    # ----------------------------------------------------------

    @classmethod
    def is_remote(cls, location: str) -> bool:
        normalized = cls._normalize(location)

        return any(
            term in normalized
            for term in cls.REMOTE_TERMS
        )

    # ----------------------------------------------------------
    # Canonical location matching
    # ----------------------------------------------------------

    @classmethod
    def _canonical_locations(
        cls,
        requested_locations: Iterable[str],
    ) -> dict[str, set[str]]:

        result: dict[str, set[str]] = {}

        for location in requested_locations:

            if not location:
                continue

            normalized = cls._normalize(location)

            aliases = cls.LOCATION_ALIASES.get(
                normalized,
                {normalized},
            )

            result[normalized] = aliases

        return result

    # ----------------------------------------------------------
    # Qualification
    # ----------------------------------------------------------

    def qualify(
        self,
        job_location: str,
        requested_locations: Iterable[str],
        remote_only: bool = False,
    ) -> LocationQualificationResult:

        if not job_location:
            return LocationQualificationResult(
                qualified=False,
                reason="Job location is empty.",
            )

        requested = [
            location.strip()
            for location in requested_locations
            if location and location.strip()
        ]

        if not requested:
            return LocationQualificationResult(
                qualified=False,
                reason="No target locations were provided.",
            )

        normalized_job_location = self._normalize(
            job_location
        )

        job_is_remote = self.is_remote(
            normalized_job_location
        )

        # ------------------------------------------------------
        # Remote-only search
        # ------------------------------------------------------

        if remote_only:

            if job_is_remote:

                return LocationQualificationResult(
                    qualified=True,
                    matched_location="Remote",
                    remote=True,
                    reason=(
                        "Job is explicitly marked as remote."
                    ),
                )

            return LocationQualificationResult(
                qualified=False,
                remote=False,
                reason=(
                    "Job is not remote while remote-only "
                    "search is enabled."
                ),
            )

        # ------------------------------------------------------
        # Explicit requested locations
        # ------------------------------------------------------

        canonical_locations = self._canonical_locations(
            requested
        )

        for requested_location, aliases in (
            canonical_locations.items()
        ):

            for alias in aliases:

                if alias in normalized_job_location:

                    return LocationQualificationResult(
                        qualified=True,
                        matched_location=requested_location,
                        remote=job_is_remote,
                        reason=(
                            f"Location matched requested "
                            f"location '{requested_location}'."
                        ),
                    )

        # ------------------------------------------------------
        # Remote India
        # ------------------------------------------------------

        requested_remote = any(
            self._normalize(location)
            in {
                "remote",
                "remote india",
                "india remote",
            }
            for location in requested
        )

        if requested_remote and job_is_remote:

            return LocationQualificationResult(
                qualified=True,
                matched_location="Remote India",
                remote=True,
                reason=(
                    "Job is remote and Remote India is "
                    "included in the requested locations."
                ),
            )

        return LocationQualificationResult(
            qualified=False,
            remote=job_is_remote,
            reason=(
                f"Job location '{job_location}' is outside "
                f"the requested locations."
            ),
        )