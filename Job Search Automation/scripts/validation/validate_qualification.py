from __future__ import annotations

import logging
import sys
from pathlib import Path

# ----------------------------------------------------------
# Ensure project root is importable when this script is
# executed directly from the repository root.
# ----------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from job_search_automation.intelligence.qualification import (
    CandidateQualifier,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(
    "qualification-validation"
)


def require(
    condition: bool,
    message: str,
) -> None:

    if not condition:
        raise AssertionError(message)


def make_job(
    title: str,
    location: str,
) -> Job:

    return Job(
        title=title,
        company="Validation Company",
        location=location,
        description="Validation job description",
        job_url=(
            "https://example.com/"
            + title.lower().replace(" ", "-")
        ),
        source="validation",
    )


def main() -> None:

    print("=" * 80)
    print("QUALIFICATION ENGINE VALIDATION")
    print("=" * 80)

    request = SearchRequest(
        searched_role="Program Management",
        keywords=[],
        locations=[
            "Mumbai",
            "Bengaluru",
            "Hyderabad",
            "Remote India",
        ],
        bucket="Program Management",
        roles=[
            "Program Manager",
            "Technical Program Manager",
            "Project Manager",
            "Delivery Manager",
            "PMO",
            "PMO Analyst",
            "Transformation Manager",
            "Implementation Manager",
            "Operations Manager",
        ],
        priority=3,
        limit=50,
        remote_only=False,
        posted_within_days=3,
    )

    qualifier = CandidateQualifier()

    # ======================================================
    # POSITIVE CASES
    # ======================================================

    positive_cases = [
        (
            "Senior Program Manager",
            "Mumbai",
        ),
        (
            "Technical Program Manager",
            "Bengaluru",
        ),
        (
            "Project Manager",
            "Hyderabad",
        ),
        (
            "PMO Analyst",
            "Mumbai",
        ),
        (
            "Transformation Manager",
            "Remote India",
        ),
        (
            "Implementation Manager",
            "Bengaluru",
        ),
        (
            "Operations Manager",
            "Hyderabad",
        ),
    ]

    print("\nPOSITIVE CASES")

    for title, location in positive_cases:

        job = make_job(
            title=title,
            location=location,
        )

        result = qualifier.qualify(
            job=job,
            request=request,
        )

        print(
            f"[{'PASS' if result.qualified else 'FAIL'}] "
            f"{title:40} | "
            f"{location:15} | "
            f"{result.reason}"
        )

        require(
            result.qualified,
            (
                f"Expected qualification to PASS for "
                f"'{title}' / '{location}'."
            ),
        )

    # ======================================================
    # NEGATIVE ROLE CASES
    # ======================================================

    negative_role_cases = [
        (
            "Data Analyst",
            "Mumbai",
        ),
        (
            "Finance & Strategy Analyst",
            "Mumbai",
        ),
        (
            "Risk Operations Analyst",
            "Mumbai",
        ),
        (
            "Freelance Copywriter",
            "Remote India",
        ),
        (
            "Software Engineer",
            "Mumbai",
        ),
    ]

    print("\nNEGATIVE ROLE CASES")

    for title, location in negative_role_cases:

        job = make_job(
            title=title,
            location=location,
        )

        result = qualifier.qualify(
            job=job,
            request=request,
        )

        print(
            f"[{'PASS' if not result.qualified else 'FAIL'}] "
            f"{title:40} | "
            f"{location:15} | "
            f"{result.reason}"
        )

        require(
            not result.qualified,
            (
                f"Expected role qualification to REJECT "
                f"'{title}'."
            ),
        )

    # ======================================================
    # NEGATIVE LOCATION CASES
    # ======================================================

    negative_location_cases = [
        (
            "Program Manager",
            "New York",
        ),
        (
            "Technical Program Manager",
            "Singapore",
        ),
        (
            "Project Manager",
            "London",
        ),
        (
            "Operations Manager",
            "Dublin, Ireland",
        ),
    ]

    print("\nNEGATIVE LOCATION CASES")

    for title, location in negative_location_cases:

        job = make_job(
            title=title,
            location=location,
        )

        result = qualifier.qualify(
            job=job,
            request=request,
        )

        print(
            f"[{'PASS' if not result.qualified else 'FAIL'}] "
            f"{title:40} | "
            f"{location:15} | "
            f"{result.reason}"
        )

        require(
            not result.qualified,
            (
                f"Expected location qualification to "
                f"REJECT '{title}' / '{location}'."
            ),
        )

    # ======================================================
    # ALIAS CASES
    # ======================================================

    alias_cases = [
        (
            "Technical Program Management Lead",
            "Bangalore",
        ),
        (
            "Project Management Lead",
            "Navi Mumbai",
        ),
        (
            "Program Management Manager",
            "Gurugram",
        ),
    ]

    print("\nALIAS / NORMALIZATION CASES")

    for title, location in alias_cases:

        job = make_job(
            title=title,
            location=location,
        )

        result = qualifier.qualify(
            job=job,
            request=request,
        )

        print(
            f"[{'PASS' if result.qualified else 'FAIL'}] "
            f"{title:40} | "
            f"{location:15} | "
            f"{result.reason}"
        )

    # ======================================================
    # REMOTE CASE
    # ======================================================

    remote_job = make_job(
        title="Senior Program Manager",
        location="Remote",
    )

    remote_result = qualifier.qualify(
        job=remote_job,
        request=request,
    )

    print("\nREMOTE CASE")

    print(
        f"[{'PASS' if remote_result.qualified else 'FAIL'}] "
        f"Senior Program Manager | Remote | "
        f"{remote_result.reason}"
    )

    # Remote is not automatically Remote India unless the
    # location/request explicitly supports it.
    require(
        remote_result.qualified,
        "Remote India request should accept a remote job.",
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    print("\n" + "=" * 80)
    print("QUALIFICATION VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()