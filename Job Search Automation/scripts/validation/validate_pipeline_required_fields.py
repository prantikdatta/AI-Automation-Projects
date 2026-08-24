from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.models.job import Job


REQUIRED_FIELDS = (
    "title",
    "company",
    "location",
    "job_url",
    "source",
    "provider",
    "searched_role",
)


def main() -> None:
    print()
    print("=" * 70)
    print("PIPELINE REQUIRED-FIELDS VALIDATION")
    print("=" * 70)

    job = Job(
        title="Analytics Engineer, GTM",
        company="Validation Company",
        location="Remote",
        description="Validation description",
        job_url="https://example.com/jobs/validation",
        source="validation",
        provider="validation",
        searched_role="Analytics Engineer",
        posted_at=datetime.now(timezone.utc),
        employment_type=None,
        seniority=None,
        remote=True,
        salary_min=None,
        salary_max=None,
        currency=None,
        skills=[],
        raw={},
    )

    for field in REQUIRED_FIELDS:
        value = getattr(job, field, None)

        if value is None or (
            isinstance(value, str)
            and not value.strip()
        ):
            raise AssertionError(
                f"Required field '{field}' is empty."
            )

        print(
            f"[PASS] Required field '{field}' populated."
        )

    print()
    print("=" * 70)
    print("PIPELINE REQUIRED-FIELDS VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()