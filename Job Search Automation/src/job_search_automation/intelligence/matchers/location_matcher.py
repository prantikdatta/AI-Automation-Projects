from __future__ import annotations

from job_search_automation.config.location_preferences import (
    ALLOW_HYBRID,
    ALLOW_REMOTE,
    PREFERRED_CITIES,
    PREFERRED_STATES,
)
from job_search_automation.config.scoring_rules import (
    LOCATION_SCORE,
)
from job_search_automation.intelligence.models import (
    LocationMatchResult,
)


class LocationMatcher:
    """
    Scores a job based on location and work mode.

    The matcher is completely configuration driven and
    contains no candidate-specific business logic.
    """

    def match(
        self,
        location: str,
        remote: bool = False,
        work_mode: str | None = None,
    ) -> LocationMatchResult:

        location = (location or "").strip()

        location_lower = location.lower()

        # ---------------------------------------------------------
        # Detect location categories
        # ---------------------------------------------------------

        preferred_city = any(
            city.lower() in location_lower
            for city in PREFERRED_CITIES
        )

        preferred_state = any(
            state.lower() in location_lower
            for state in PREFERRED_STATES
        )

        remote_match = (
            remote
            or "remote" in location_lower
        )

        hybrid_match = (
            work_mode is not None
            and work_mode.lower() == "hybrid"
        )

        # ---------------------------------------------------------
        # Apply configured location score
        # ---------------------------------------------------------

        if preferred_city:

            score = LOCATION_SCORE["primary"]

            explanation = (
                "Primary preferred location matched."
            )

        elif remote_match and ALLOW_REMOTE:

            score = LOCATION_SCORE["remote"]

            explanation = (
                "Remote work is supported."
            )

        elif hybrid_match and ALLOW_HYBRID:

            score = LOCATION_SCORE["hybrid"]

            explanation = (
                "Hybrid work is supported."
            )

        elif preferred_state:

            score = LOCATION_SCORE["state"]

            explanation = (
                "Preferred state matched."
            )

        else:

            score = LOCATION_SCORE["other"]

            explanation = (
                "Location is outside preferred "
                "geographical regions."
            )

        # ---------------------------------------------------------
        # Return canonical location result
        # ---------------------------------------------------------

        return LocationMatchResult(
            score=score,
            location=location,
            preferred_location=(
                preferred_city
                or preferred_state
            ),
            remote_match=remote_match,
            work_mode=work_mode,
            explanation=explanation,
            confidence=1.0,
            metadata={
                "preferred_city": preferred_city,
                "preferred_state": preferred_state,
                "remote_match": remote_match,
                "hybrid_match": hybrid_match,
                "work_mode": work_mode,
            },
        )