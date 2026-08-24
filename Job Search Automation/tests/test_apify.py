from __future__ import annotations

from job_search_automation.normalizers.apify import ApifyNormalizer


def test_apify_prefers_real_apply_option_over_google_result_url() -> None:
    raw = {
        "title": "Senior Data Analyst",
        "companyName": "Example Company",
        "location": "Mumbai",
        "url": "https://www.google.com/search?q=senior+data+analyst",
        "applyOptions": [
            {
                "title": "Apply on company website",
                "link": "https://careers.example.com/jobs/123",
            }
        ],
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Data Analyst",
    )

    assert job.job_url == "https://careers.example.com/jobs/123"


def test_apify_uses_explicit_job_url_first() -> None:
    raw = {
        "title": "Data Analyst",
        "companyName": "Example Company",
        "jobUrl": "https://careers.example.com/jobs/456",
        "applyOptions": [
            {
                "link": "https://jobs.example.com/456",
            }
        ],
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Data Analyst",
    )

    assert job.job_url == "https://careers.example.com/jobs/456"


def test_apify_uses_apply_option_when_generic_url_is_google() -> None:
    raw = {
        "title": "Business Analyst",
        "companyName": "Example Company",
        "url": "https://www.google.co.in/search?q=business+analyst",
        "applyOptions": [
            {
                "url": "https://jobs.example.com/business-analyst-789",
            }
        ],
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Business Analyst",
    )

    assert job.job_url == (
        "https://jobs.example.com/business-analyst-789"
    )


def test_apify_falls_back_to_non_google_generic_url() -> None:
    raw = {
        "title": "Product Analyst",
        "companyName": "Example Company",
        "url": "https://careers.example.com/jobs/999",
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Product Analyst",
    )

    assert job.job_url == "https://careers.example.com/jobs/999"


def test_apify_does_not_use_google_result_url_as_canonical_job_url() -> None:
    raw = {
        "title": "Data Analyst",
        "companyName": "Example Company",
        "url": "https://www.google.com/search?q=data+analyst",
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Data Analyst",
    )

    assert job.job_url == ""


def test_apify_supports_nested_job_url() -> None:
    raw = {
        "title": "Data Analyst",
        "companyName": "Example Company",
        "job": {
            "jobUrl": "https://careers.example.com/jobs/nested-123",
        },
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Data Analyst",
    )

    assert job.job_url == (
        "https://careers.example.com/jobs/nested-123"
    )


def test_apify_normalizes_core_fields() -> None:
    raw = {
        "title": "Senior Data Analyst",
        "companyName": "Example Company",
        "location": "Mumbai",
        "description": "Analyze business data.",
        "postedAtIso": "2026-08-20T10:00:00Z",
        "jobType": "Full-time",
        "workFromHome": True,
        "salaryMin": 1000000,
        "salaryMax": 1500000,
        "salaryCurrency": "INR",
        "applyOptions": [
            {
                "link": "https://careers.example.com/jobs/321",
            }
        ],
    }

    job = ApifyNormalizer().normalize(
        raw,
        "Data Analyst",
    )

    assert job.title == "Senior Data Analyst"
    assert job.company == "Example Company"
    assert job.location == "Mumbai"
    assert job.description == "Analyze business data."
    assert job.job_url == "https://careers.example.com/jobs/321"
    assert job.provider == "Apify"
    assert job.remote is True
    assert job.work_mode == "Remote"
    assert job.salary_min == 1000000
    assert job.salary_max == 1500000
    assert job.currency == "INR"
    assert job.employment_type == "Full-time"
    assert job.posted_at is not None