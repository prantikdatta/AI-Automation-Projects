from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.models.job import Job
from job_search_automation.services.google_sheets.mapper import (
    HEADERS,
    job_to_row,
)


def make_job(
    *,
    title: str,
    company: str,
    location: str,
    job_url: str,
    posted_at: datetime,
    remote: bool = False,
    source: str = "validation",
    provider: str = "validation",
    searched_role: str = "Data Analyst",
    score: float = 80.0,
) -> Job:
    return Job(
        title=title,
        company=company,
        location=location,
        description="Validation job description.",
        job_url=job_url,
        source=source,
        provider=provider,
        searched_role=searched_role,
        posted_at=posted_at,
        employment_type="Full-time",
        seniority="Senior",
        remote=remote,
        salary_min=None,
        salary_max=None,
        currency=None,
        skills=["Python", "SQL", "Power BI"],
        raw={},
        run_date=datetime.now(timezone.utc).date(),
        shortlist_likelihood_score=score,
        shortlist_bucket="Strong",
        apply_priority=80,
        recommendation="Apply",
        matched_skills=["Python", "SQL"],
        missing_skills=["Tableau"],
        company_tier="Tier 1",
        job_bucket="Analytics",
        blunt_reason="Strong profile alignment.",
        tailored_resume_text=None,
        application_status="Not Applied",
    )


def main() -> None:
    print()
    print("=" * 70)
    print("UNIQUE JOBS EXPORT VALIDATION")
    print("=" * 70)

    posted_at = datetime.now(timezone.utc)

    jobs = [
        make_job(
            title="Senior Data Analyst",
            company="Stripe",
            location="Bengaluru",
            job_url="https://example.com/jobs/stripe-001",
            posted_at=posted_at,
            remote=False,
        ),
        make_job(
            title="Senior Data Analyst",
            company="Stripe",
            location="Bengaluru",
            job_url="https://example.com/jobs/stripe-001",
            posted_at=posted_at,
            remote=False,
        ),
        make_job(
            title="Senior Data Analyst",
            company="Stripe",
            location="Mumbai",
            job_url="https://example.com/jobs/stripe-002",
            posted_at=posted_at,
            remote=False,
        ),
        make_job(
            title="Senior Data Analyst",
            company="Coinbase",
            location="Remote",
            job_url="https://example.com/jobs/coinbase-001",
            posted_at=posted_at,
            remote=True,
        ),
    ]

    print(f"[INFO] Input jobs: {len(jobs)}")

    rows = [
        job_to_row(job)
        for job in jobs
    ]

    expected_columns = len(HEADERS)

    if not rows:
        raise AssertionError(
            "No rows were generated."
        )

    print(f"[INFO] Export rows: {len(rows)}")

    # ----------------------------------------------------------
    # HEADER VALIDATION
    # ----------------------------------------------------------

    if not HEADERS:
        raise AssertionError(
            "Google Sheets headers are empty."
        )

    print(
        f"[PASS] Headers populated: {len(HEADERS)} columns."
    )

    # ----------------------------------------------------------
    # ROW WIDTH VALIDATION
    # ----------------------------------------------------------

    for index, row in enumerate(rows, start=1):
        if len(row) != expected_columns:
            raise AssertionError(
                f"Row {index} contains {len(row)} columns; "
                f"expected {expected_columns}."
            )

    print(
        "[PASS] Every exported row matches header width."
    )

    # ----------------------------------------------------------
    # REQUIRED EXPORT FIELDS
    # ----------------------------------------------------------

    required_headers = {
        "Run Date",
        "Role",
        "Company",
        "Location",
        "Posted",
        "Score",
        "Bucket",
        "Priority",
        "Job URL",
    }

    missing_headers = (
        required_headers
        - set(HEADERS)
    )

    if missing_headers:
        raise AssertionError(
            "Missing required export headers: "
            + ", ".join(sorted(missing_headers))
        )

    print(
        "[PASS] Required export headers present."
    )

    # ----------------------------------------------------------
    # JOB URL VALIDATION
    # ----------------------------------------------------------

    job_url_index = HEADERS.index(
        "Job URL"
    )

    exported_urls = [
        row[job_url_index]
        for row in rows
    ]

    if any(
        not url
        for url in exported_urls
    ):
        raise AssertionError(
            "One or more exported jobs have an empty Job URL."
        )

    print(
        "[PASS] All exported jobs contain Job URLs."
    )

    # ----------------------------------------------------------
    # DUPLICATE URL VALIDATION
    # ----------------------------------------------------------

    unique_urls = set(exported_urls)

    if len(unique_urls) != len(exported_urls):
        print(
            "[INFO] Duplicate URLs detected in raw "
            "validation input, as expected."
        )
    else:
        raise AssertionError(
            "Validation fixture did not contain "
            "the expected duplicate URL."
        )

    print(
        "[PASS] Duplicate URL fixture detected."
    )

    # ----------------------------------------------------------
    # DISTINCT JOB VALIDATION
    # ----------------------------------------------------------

    role_index = HEADERS.index("Role")
    company_index = HEADERS.index("Company")
    location_index = HEADERS.index("Location")

    canonical_keys = {
        (
            row[role_index],
            row[company_index],
            row[location_index],
        )
        for row in rows
    }

    if len(canonical_keys) != 3:
        raise AssertionError(
            "Expected 3 canonical job combinations, "
            f"got {len(canonical_keys)}."
        )

    print(
        "[PASS] Canonical job combinations preserved."
    )

    # ----------------------------------------------------------
    # REMOTE BOOLEAN VALIDATION
    # ----------------------------------------------------------

    for job in jobs:
        if not isinstance(job.remote, bool):
            raise AssertionError(
                f"Job.remote must be bool, got "
                f"{type(job.remote).__name__}."
            )

    print(
        "[PASS] All Job.remote values are valid booleans."
    )

    # ----------------------------------------------------------
    # MAPPER OUTPUT VALIDATION
    # ----------------------------------------------------------

    for index, row in enumerate(rows, start=1):
        if not all(
            isinstance(value, str)
            for value in row
        ):
            raise AssertionError(
                f"Export row {index} contains "
                "non-string values."
            )

    print(
        "[PASS] Mapper produces string-compatible Sheet rows."
    )

    # ----------------------------------------------------------
    # REQUIRED JOB DATA PRESERVED
    # ----------------------------------------------------------

    for index, row in enumerate(rows, start=1):
        if not row[role_index]:
            raise AssertionError(
                f"Row {index} has empty Role."
            )

        if not row[company_index]:
            raise AssertionError(
                f"Row {index} has empty Company."
            )

        if not row[location_index]:
            raise AssertionError(
                f"Row {index} has empty Location."
            )

    print(
        "[PASS] Required job data preserved in export rows."
    )

    print()
    print("=" * 70)
    print("UNIQUE JOBS EXPORT VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()