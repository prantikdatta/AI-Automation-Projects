from __future__ import annotations

from types import SimpleNamespace

from job_search_automation.utils.job_prefilter import (
    should_reject,
)


def make_job(
    *,
    title: str = "Data Analyst",
    company: str = "Test Company",
    location: str = "Mumbai, India",
    description: str = "3 years of experience",
    job_url: str = "https://example.com/job",
):
    return SimpleNamespace(
        title=title,
        company=company,
        location=location,
        description=description,
        job_url=job_url,
    )


def validate() -> None:

    print("=" * 70)
    print("JOB PREFILTER VALIDATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Valid job
    # ---------------------------------------------------------

    job = make_job()

    assert should_reject(job) is False

    print(
        "[PASS] Valid job accepted."
    )

    # ---------------------------------------------------------
    # Internship
    # ---------------------------------------------------------

    job = make_job(
        title="Data Analyst Intern",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Internship rejected."
    )

    # ---------------------------------------------------------
    # Senior leadership
    # ---------------------------------------------------------

    job = make_job(
        title="Director of Analytics",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Senior leadership role rejected."
    )

    # ---------------------------------------------------------
    # Excessive experience
    # ---------------------------------------------------------

    job = make_job(
        description="15 years of experience required",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Excessive experience requirement rejected."
    )

    # ---------------------------------------------------------
    # Foreign opportunity
    # ---------------------------------------------------------

    job = make_job(
        description=(
            "This position is based in the United States."
        ),
    )

    assert should_reject(job) is True

    print(
        "[PASS] Foreign opportunity rejected."
    )

    # ---------------------------------------------------------
    # Missing company
    # ---------------------------------------------------------

    job = make_job(
        company="",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Missing company rejected."
    )

    # ---------------------------------------------------------
    # Missing title
    # ---------------------------------------------------------

    job = make_job(
        title="",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Missing title rejected."
    )

    # ---------------------------------------------------------
    # Missing location
    # ---------------------------------------------------------

    job = make_job(
        location="",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Missing location rejected."
    )

    # ---------------------------------------------------------
    # Missing URL
    # ---------------------------------------------------------

    job = make_job(
        job_url="",
    )

    assert should_reject(job) is True

    print(
        "[PASS] Missing job URL rejected."
    )

    print()
    print("=" * 70)
    print("JOB PREFILTER VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    validate()