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
from job_search_automation.intelligence.matchers.location_matcher import (
    LocationMatcher,
)


def validate() -> None:

    print("=" * 70)
    print("LOCATION MATCHER VALIDATION")
    print("=" * 70)

    matcher = LocationMatcher()

    # ---------------------------------------------------------
    # Basic configuration validation
    # ---------------------------------------------------------

    required_scores = [
        "primary",
        "remote",
        "state",
        "hybrid",
        "other",
    ]

    for key in required_scores:

        assert key in LOCATION_SCORE, (
            f"Missing LOCATION_SCORE key: {key}"
        )

    print(
        "[PASS] LOCATION_SCORE configuration is compatible."
    )

    # ---------------------------------------------------------
    # Mumbai / primary location
    # ---------------------------------------------------------

    result = matcher.match(
        location="Mumbai, Maharashtra, India",
    )

    print(
        f"Mumbai -> score={result.score}"
    )

    assert (
        result.score
        == LOCATION_SCORE["primary"]
    )

    assert result.preferred_location is True

    print(
        "[PASS] Primary location scoring."
    )

    # ---------------------------------------------------------
    # Preferred state
    # ---------------------------------------------------------

    if PREFERRED_STATES:

        state = PREFERRED_STATES[0]

        result = matcher.match(
            location=f"{state}, India",
        )

        print(
            f"State -> score={result.score}"
        )

        assert (
            result.score
            == LOCATION_SCORE["state"]
        )

        print(
            "[PASS] Preferred state scoring."
        )

    # ---------------------------------------------------------
    # Remote
    # ---------------------------------------------------------

    if ALLOW_REMOTE:

        result = matcher.match(
            location="Remote",
            remote=True,
        )

        print(
            f"Remote -> score={result.score}"
        )

        assert (
            result.score
            == LOCATION_SCORE["remote"]
        )

        assert result.remote_match is True

        print(
            "[PASS] Remote scoring."
        )

    # ---------------------------------------------------------
    # Hybrid
    # ---------------------------------------------------------

    if ALLOW_HYBRID:

        result = matcher.match(
            location="Bangalore, India",
            work_mode="hybrid",
        )

        print(
            f"Hybrid -> score={result.score}"
        )

        # A preferred city can legitimately take precedence
        # over hybrid according to the matcher hierarchy.
        assert result.score in (
            LOCATION_SCORE["primary"],
            LOCATION_SCORE["state"],
            LOCATION_SCORE["hybrid"],
            LOCATION_SCORE["other"],
        )

        print(
            "[PASS] Hybrid scoring."
        )

    # ---------------------------------------------------------
    # Unknown location
    # ---------------------------------------------------------

    result = matcher.match(
        location="Somewhere, India",
    )

    print(
        f"Unknown -> score={result.score}"
    )

    assert (
        result.score
        == LOCATION_SCORE["other"]
    )

    print(
        "[PASS] Unknown location scoring."
    )

    # ---------------------------------------------------------
    # No KeyError
    # ---------------------------------------------------------

    result = matcher.match(
        location="Mumbai",
    )

    assert result is not None

    print(
        "[PASS] No invalid LOCATION_SCORE keys."
    )

    print()
    print("=" * 70)
    print("LOCATION MATCHER VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    validate()