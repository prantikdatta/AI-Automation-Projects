from __future__ import annotations

"""
Controlled live-provider smoke test.

This script performs:
    1. RapidAPI/JSearch request
    2. One Apify Actor run

It validates:

    Provider response
        ↓
    Existing provider normalizer
        ↓
    Existing CanonicalMapper
        ↓
    Canonical Job

It does NOT:
    - run SearchPipeline
    - run Gemini
    - write Google Sheets
    - execute n8n
    - execute applications

RapidAPI HTTP 429 is treated as non-fatal so Apify can be tested
independently.

Default test:
    Role     : Data Analyst
    Location : Mumbai
    Limit    : 10
"""

import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Repository import setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.clients.apify_client import ApifyClient
from job_search_automation.clients.rapidapi_client import RapidAPIClient
from job_search_automation.models.job import Job
from job_search_automation.normalizers.apify import ApifyNormalizer
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.rapidapi import RapidAPINormalizer


# ---------------------------------------------------------------------------
# Controlled test configuration
# ---------------------------------------------------------------------------

TEST_ROLE = "Data Analyst"
TEST_LOCATION = "Mumbai"
TEST_LIMIT = 10
TEST_POSTED_WITHIN_DAYS = 7


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def validate_job(
    job: Job,
    provider: str,
    index: int,
) -> None:
    require(
        isinstance(job, Job),
        (
            f"{provider} normalized item #{index} is not "
            f"a canonical Job: {type(job).__name__}"
        ),
    )

    require(
        bool(str(job.title).strip()),
        f"{provider} Job #{index} has no title.",
    )

    require(
        bool(str(job.company).strip()),
        (
            f"{provider} Job #{index} has no company. "
            "The provider normalizer did not map the provider's "
            "company field into Job.company."
        ),
    )

    require(
        bool(str(job.location).strip()),
        f"{provider} Job #{index} has no location.",
    )

    require(
        bool(str(job.job_url).strip()),
        f"{provider} Job #{index} has no job_url.",
    )

    require(
        bool(str(job.provider).strip()),
        f"{provider} Job #{index} has no provider.",
    )


def print_job_sample(
    provider: str,
    jobs: list[Job],
) -> None:
    print()
    print(f"{provider} canonical Job sample:")

    for index, job in enumerate(
        jobs[:5],
        start=1,
    ):
        print(
            f"  {index:02d} | "
            f"{str(job.title)[:50]:50s} | "
            f"{str(job.company)[:30]:30s} | "
            f"{str(job.location)[:30]:30s}"
        )


def print_raw_schema(
    provider: str,
    raw_jobs: list[dict[str, Any]],
) -> None:
    """
    Print actual fields returned by the provider.
    """

    print()
    print(f"{provider} raw schema inspection:")

    if not raw_jobs:
        print("  No raw jobs available.")
        return

    fields: set[str] = set()

    for raw_job in raw_jobs[:5]:
        if isinstance(raw_job, dict):
            fields.update(
                str(key)
                for key in raw_job.keys()
            )

    for field in sorted(fields):
        print(f"  - {field}")


def print_url_candidates(
    provider: str,
    raw_jobs: list[dict[str, Any]],
) -> None:
    """
    Print URL-like fields from the live provider payload.
    """

    print()
    print(f"{provider} URL candidate inspection:")

    if not raw_jobs:
        print("  No raw jobs available.")
        return

    for index, raw_job in enumerate(
        raw_jobs[:10],
        start=1,
    ):
        print()
        print(f"  Job #{index}:")

        found = False

        for key, value in raw_job.items():
            key_text = str(key).lower()

            if (
                "url" in key_text
                or "link" in key_text
                or "apply" in key_text
            ):
                print(
                    f"    {key}: {value!r}"
                )
                found = True

        if not found:
            print("    No URL-like fields found.")


# ---------------------------------------------------------------------------
# RapidAPI
# ---------------------------------------------------------------------------


def run_rapidapi_test() -> list[Job]:
    print("=" * 90)
    print("1/2 - RAPIDAPI LIVE SMOKE TEST")
    print("=" * 90)

    print(f"Role     : {TEST_ROLE}")
    print(f"Location : {TEST_LOCATION}")
    print(f"Limit    : {TEST_LIMIT}")
    print(f"Freshness: {TEST_POSTED_WITHIN_DAYS} days")

    client = RapidAPIClient()

    payload = client.search_jobs(
        query=f"{TEST_ROLE} {TEST_LOCATION}",
        limit=TEST_LIMIT,
        posted_within_days=TEST_POSTED_WITHIN_DAYS,
        remote_only=False,
    )

    require(
        isinstance(payload, dict),
        (
            "RapidAPI returned an unexpected response type: "
            f"{type(payload).__name__}"
        ),
    )

    if payload.get("rate_limited"):
        print()
        print("STATUS: RATE_LIMITED")
        print("RapidAPI returned HTTP 429.")
        print("Continuing to Apify.")
        print()

        return []

    raw_jobs = payload.get(
        "data",
        [],
    )

    require(
        isinstance(raw_jobs, list),
        (
            "RapidAPI payload['data'] must be a list; "
            f"received {type(raw_jobs).__name__}."
        ),
    )

    print(
        f"Raw jobs returned: {len(raw_jobs)}"
    )

    normalizer = RapidAPINormalizer()

    jobs: list[Job] = []

    for raw_job in raw_jobs:
        require(
            isinstance(raw_job, dict),
            (
                "RapidAPI dataset item is not a dictionary: "
                f"{type(raw_job).__name__}"
            ),
        )

        normalized = normalizer.normalize(
            raw=raw_job,
            searched_role=TEST_ROLE,
        )

        job = CanonicalMapper.to_job(
            normalized,
        )

        jobs.append(job)

    print(
        f"Canonical jobs   : {len(jobs)}"
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        validate_job(
            job,
            "RapidAPI",
            index,
        )

    print_job_sample(
        "RapidAPI",
        jobs,
    )

    print()
    print("PASS: RapidAPI → Normalizer → Canonical Job")

    return jobs


# ---------------------------------------------------------------------------
# Apify
# ---------------------------------------------------------------------------


def run_apify_test() -> list[Job]:
    print()
    print("=" * 90)
    print("2/2 - APIFY LIVE SMOKE TEST")
    print("=" * 90)

    print(f"Role     : {TEST_ROLE}")
    print(f"Location : {TEST_LOCATION}")

    print(
        "WARNING  : This performs ONE real Apify Actor run."
    )

    client = ApifyClient()

    payload = client.search_jobs(
        query=TEST_ROLE,
        location=TEST_LOCATION,
        max_items=TEST_LIMIT,
    )

    print(
        f"Apify response type: {type(payload).__name__}"
    )

    if isinstance(payload, list):
        raw_jobs = payload

    elif isinstance(payload, dict):
        data = payload.get(
            "data",
            [],
        )

        require(
            isinstance(data, list),
            (
                "Apify response['data'] must be a list; "
                f"received {type(data).__name__}."
            ),
        )

        raw_jobs = data

    else:
        raise AssertionError(
            "Apify response must be a list or dictionary; "
            f"received {type(payload).__name__}."
        )

    print(
        f"Raw jobs returned: {len(raw_jobs)}"
    )

    require(
        len(raw_jobs) > 0,
        (
            "Apify returned zero raw jobs. "
            "Inspect the Actor configuration or search query."
        ),
    )

    print_raw_schema(
        "Apify",
        raw_jobs,
    )

    print_url_candidates(
        "Apify",
        raw_jobs,
    )

    normalizer = ApifyNormalizer()

    jobs: list[Job] = []

    for raw_index, raw_job in enumerate(
        raw_jobs,
        start=1,
    ):
        require(
            isinstance(raw_job, dict),
            (
                f"Apify dataset item #{raw_index} is not a dictionary: "
                f"{type(raw_job).__name__}"
            ),
        )

        normalized = normalizer.normalize(
            raw_job,
            TEST_ROLE,
        )

        job = CanonicalMapper.to_job(
            normalized,
        )

        jobs.append(job)

    print()
    print(
        f"Canonical jobs   : {len(jobs)}"
    )

    require(
        len(jobs) == len(raw_jobs),
        (
            "Apify canonical-job count does not match raw-job count: "
            f"raw={len(raw_jobs)}, canonical={len(jobs)}."
        ),
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        validate_job(
            job,
            "Apify",
            index,
        )

    validate_apify_url_authenticity(
        raw_jobs,
        jobs,
    )

    print_job_sample(
        "Apify",
        jobs,
    )

    print()
    print("PASS: Apify → Normalizer → Canonical Job")

    return jobs


# ---------------------------------------------------------------------------
# Apify URL validation
# ---------------------------------------------------------------------------


def _is_usable_url(
    value: Any,
) -> bool:
    """
    Return True for a real HTTP/HTTPS URL.
    """

    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    try:
        parsed = urlparse(value)
    except ValueError:
        return False

    return parsed.scheme in {
        "http",
        "https",
    } and bool(parsed.netloc)


def _is_placeholder_url(
    value: str,
) -> bool:
    """
    Detect known placeholder hosts.
    """

    placeholder_hosts = {
        "example.com",
        "www.example.com",
        "example.org",
        "www.example.org",
        "example.net",
        "www.example.net",
    }

    try:
        hostname = (
            urlparse(value).hostname
            or ""
        ).lower()
    except ValueError:
        return False

    return hostname in placeholder_hosts


def validate_apify_url_authenticity(
    raw_jobs: list[dict[str, Any]],
    canonical_jobs: list[Job],
) -> None:
    """
    Validate the actual canonical URL contract for Apify.

    Current Actor:
        thirdwatch/linkedin-jobs-scraper

    Expected direct URL field:
        apply_url

    The test deliberately requires:
        raw usable apply URL
        +
        canonical Job.job_url
        +
        no placeholder URLs
    """

    missing_raw_urls: list[int] = []
    placeholder_raw_urls: list[str] = []
    invalid_raw_urls: list[str] = []

    direct_url_fields = (
        "apply_url",
        "applyUrl",
        "job_url",
        "jobUrl",
        "application_url",
        "applicationUrl",
        "url",
        "link",
    )

    for index, raw_job in enumerate(
        raw_jobs,
        start=1,
    ):
        candidates: list[Any] = []

        for field in direct_url_fields:
            if field in raw_job:
                candidates.append(
                    raw_job.get(field)
                )

        found_usable = False

        for candidate in candidates:
            if not isinstance(candidate, str):
                continue

            candidate = candidate.strip()

            if not candidate:
                continue

            if not _is_usable_url(candidate):
                invalid_raw_urls.append(
                    f"Job #{index}: {candidate}"
                )
                continue

            if _is_placeholder_url(candidate):
                placeholder_raw_urls.append(
                    f"Job #{index}: {candidate}"
                )
                continue

            found_usable = True
            break

        if not found_usable:
            missing_raw_urls.append(index)

    canonical_missing_urls: list[int] = []
    canonical_placeholder_urls: list[str] = []

    for index, job in enumerate(
        canonical_jobs,
        start=1,
    ):
        job_url = str(
            getattr(
                job,
                "job_url",
                "",
            ) or "",
        ).strip()

        if not job_url:
            canonical_missing_urls.append(index)
            continue

        if not _is_usable_url(job_url):
            raise AssertionError(
                f"Apify canonical Job #{index} has an invalid job_url: "
                f"{job_url!r}"
            )

        if _is_placeholder_url(job_url):
            canonical_placeholder_urls.append(
                f"Job #{index}: {job_url}"
            )

    if missing_raw_urls:
        print()
        print(
            "FAIL: Apify jobs without a usable direct URL:"
        )
        print(
            f"  Jobs: {missing_raw_urls}"
        )

    if placeholder_raw_urls:
        print()
        print(
            "FAIL: Apify returned placeholder URLs:"
        )

        for value in placeholder_raw_urls[:10]:
            print(
                f"  {value}"
            )

    if invalid_raw_urls:
        print()
        print(
            "FAIL: Apify returned invalid URL values:"
        )

        for value in invalid_raw_urls[:10]:
            print(
                f"  {value}"
            )

    if canonical_missing_urls:
        print()
        print(
            "FAIL: Canonical Apify jobs without job_url:"
        )
        print(
            f"  Jobs: {canonical_missing_urls}"
        )

    if canonical_placeholder_urls:
        print()
        print(
            "FAIL: Canonical Apify jobs contain placeholder URLs:"
        )

        for value in canonical_placeholder_urls[:10]:
            print(
                f"  {value}"
            )

    if (
        missing_raw_urls
        or placeholder_raw_urls
        or invalid_raw_urls
        or canonical_missing_urls
        or canonical_placeholder_urls
    ):
        raise AssertionError(
            "Apify live smoke test failed URL authenticity validation."
        )

    print(
        "PASS: Apify returned usable non-placeholder application URLs."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 90)
    print("CONTROLLED LIVE PROVIDER SMOKE TEST")
    print("=" * 90)

    print("Production SearchPipeline : NOT RUN")
    print("Gemini                    : NOT RUN")
    print("Google Sheets             : NOT WRITTEN")
    print("n8n                       : NOT CALLED")
    print("Applications              : NOT SUBMITTED")
    print()

    rapidapi_jobs = run_rapidapi_test()

    apify_jobs = run_apify_test()

    print()
    print("=" * 90)
    print("LIVE PROVIDER SMOKE TEST SUMMARY")
    print("=" * 90)

    print(
        f"RapidAPI canonical jobs    : {len(rapidapi_jobs)}"
    )

    print(
        f"Apify canonical jobs       : {len(apify_jobs)}"
    )

    print()
    print("External provider calls    : 2")
    print("Production pipeline calls : 0")
    print("Google Sheets writes       : 0")
    print("Application submissions    : 0")

    if not rapidapi_jobs:
        print()
        print(
            "RapidAPI: RATE_LIMITED or returned zero jobs."
        )

        print(
            "This is non-fatal for the controlled provider test."
        )

    require(
        len(apify_jobs) > 0,
        (
            "Apify returned zero canonical jobs. "
            "Inspect the Actor configuration before the full run."
        ),
    )

    print()
    print("=" * 90)
    print("CONTROLLED LIVE PROVIDER SMOKE TEST PASSED")
    print("=" * 90)

    print(
        "Apify returned real jobs and the existing "
        "ApifyNormalizer produced valid canonical Job objects."
    )

    print(
        "The production SearchPipeline was NOT modified or executed."
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()
        print("=" * 90)
        print("CONTROLLED LIVE PROVIDER SMOKE TEST FAILED")
        print("=" * 90)

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print("=" * 90)

        raise