from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.models.job import Job
from job_search_automation.pipeline.deduplication_stage import (
    DeduplicationStage,
)


def make_job(
    *,
    title: str,
    company: str,
    location: str,
    job_url: str,
    searched_role: str = "Risk Analyst",
    provider: str = "validation",
) -> Job:
    return Job(
        title=title,
        company=company,
        location=location,
        description="Validation job description.",
        job_url=job_url,
        source=provider,
        provider=provider,
        searched_role=searched_role,
        posted_at=datetime.now(timezone.utc),
        employment_type=None,
        seniority=None,
        remote=False,
        salary_min=None,
        salary_max=None,
        currency=None,
        skills=[],
        raw={},
    )


def main() -> None:
    print()
    print("=" * 70)
    print("DEDUPLICATION VALIDATION")
    print("=" * 70)

    jobs = [
        # 1. Canonical job.
        make_job(
            title="Risk Analyst",
            company="Acme Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/100",
        ),

        # 2. Exact URL duplicate.
        make_job(
            title="Risk Analyst",
            company="Acme Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/100/",
        ),

        # 3. Same company/title/location but different URL.
        make_job(
            title="Risk Analyst",
            company="Acme Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/101",
        ),

        # 4. Different title.
        make_job(
            title="Senior Risk Analyst",
            company="Acme Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/102",
        ),

        # 5. Unique role.
        make_job(
            title="Credit Risk Analyst",
            company="Acme Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/103",
        ),

        # 6. Same title/company but different location.
        make_job(
            title="Risk Analyst",
            company="Acme Bank",
            location="Bangalore",
            job_url="https://example.com/jobs/104",
        ),

        # 7. Different company.
        make_job(
            title="Risk Analyst",
            company="Other Bank",
            location="Mumbai",
            job_url="https://example.com/jobs/105",
        ),
    ]

    stage = DeduplicationStage()

    result = stage.run(jobs)

    print(
        f"[INFO] Input jobs: {result.input_count}"
    )

    print(
        f"[INFO] Unique jobs: {result.unique_count}"
    )

    print(
        f"[INFO] Duplicate jobs: {result.duplicate_count}"
    )

    # ------------------------------------------------------------------
    # Expected result
    # ------------------------------------------------------------------

    assert result.input_count == 7

    if result.unique_count != 5:
        raise AssertionError(
            "Expected 5 unique jobs, "
            f"got {result.unique_count}."
        )

    if result.duplicate_count != 1:
        raise AssertionError(
            "Expected 1 duplicate job, "
            f"got {result.duplicate_count}."
        )

    print(
        "[PASS] Exact URL duplicate detected."
    )

    # ------------------------------------------------------------------
    # Validate canonical jobs
    # ------------------------------------------------------------------

    unique_titles = [
        job.title
        for job in result.unique_jobs
    ]

    assert "Risk Analyst" in unique_titles
    assert "Senior Risk Analyst" in unique_titles
    assert "Credit Risk Analyst" in unique_titles

    print(
        "[PASS] Canonical unique jobs preserved."
    )

    # ------------------------------------------------------------------
    # Validate different locations
    # ------------------------------------------------------------------

    locations = {
        job.location
        for job in result.unique_jobs
    }

    assert "Mumbai" in locations
    assert "Bangalore" in locations

    print(
        "[PASS] Same role in different locations "
        "is preserved."
    )

    # ------------------------------------------------------------------
    # Validate different companies
    # ------------------------------------------------------------------

    companies = {
        job.company
        for job in result.unique_jobs
    }

    assert "Acme Bank" in companies
    assert "Other Bank" in companies

    print(
        "[PASS] Same role at different companies "
        "is preserved."
    )

    # ------------------------------------------------------------------
    # Validate duplicate decision
    # ------------------------------------------------------------------

    duplicate_decisions = [
        decision
        for decision in result.decisions.values()
        if decision.is_duplicate
    ]

    if len(duplicate_decisions) != 2:
        raise AssertionError(
            "Expected exactly two recorded "
            "duplicate decisions, "
            f"got {len(duplicate_decisions)}."
        )

    print(
        "[PASS] All duplicate decisions recorded."
    )

    for decision in duplicate_decisions:
        assert decision.canonical_job_id is not None
        assert decision.similarity == 1.0

        assert decision.reason in {
            "Exact job URL duplicate.",
            "Exact company/title/location duplicate.",
        }

    print(
        "[PASS] Duplicate decisions contain "
        "canonical job information."
    )

    # ------------------------------------------------------------------
    # Final validation
    # ------------------------------------------------------------------

    print()
    print("=" * 70)
    print("DEDUPLICATION VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()