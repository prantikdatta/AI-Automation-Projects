from __future__ import annotations

"""
Controlled live Apify Actor validation.

Purpose
-------
Validate that the configured Apify Actor returns:

1. Real-looking job records.
2. Real company names.
3. Requested location.
4. Valid source/application URLs.
5. Non-Google application destinations where available.
6. No explicit mock/sample records.
7. No synthetic titles such as "Data Analyst 1".
8. No placeholder/example URLs.

This script does NOT:
    - run SearchPipeline
    - run Gemini
    - write Google Sheets
    - call n8n
    - submit applications
    - modify provider code
    - modify production configuration

IMPORTANT
---------
The configured Actor is read from settings.APIFY_ACTOR_ID.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


# ============================================================================
# REPOSITORY IMPORT SETUP
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.config import settings


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_ROLE = "Data Analyst"
TEST_LOCATION = "Mumbai"
TEST_COUNTRY = "in"
TEST_LANGUAGE = "en"
TEST_MAX_RESULTS = 10
TEST_INCLUDE_DETAILS = True


# ============================================================================
# APIFY
# ============================================================================

APIFY_BASE_URL = "https://api.apify.com/v2"


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    try:
        parsed = urlparse(value)
    except ValueError:
        return False

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


def hostname(value: str) -> str:
    try:
        return (
            urlparse(value).hostname
            or ""
        ).lower()
    except Exception:
        return ""


def is_google_url(value: str) -> bool:
    host = hostname(value)

    return (
        host == "google.com"
        or host.endswith(".google.com")
        or host == "google.co.in"
        or host.endswith(".google.co.in")
        or host == "google.co.uk"
        or host.endswith(".google.co.uk")
    )


def is_placeholder_url(value: str) -> bool:
    host = hostname(value)

    placeholder_hosts = {
        "example.com",
        "www.example.com",
        "example.org",
        "www.example.org",
        "example.net",
        "www.example.net",
        "localhost",
    }

    return host in placeholder_hosts


def is_synthetic_title(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    title = value.strip().lower()

    if not title:
        return False

    patterns = (
        r"^data analyst\s+\d+$",
        r"^business analyst\s+\d+$",
        r"^software engineer\s+\d+$",
        r"^data scientist\s+\d+$",
        r"^analyst\s+\d+$",
        r"^job\s+\d+$",
        r"^test\s+\d+$",
        r"^sample\s+\d+$",
        r"^mock\s+\d+$",
    )

    return any(
        re.match(
            pattern,
            title,
        )
        for pattern in patterns
    )


def is_mock_record(
    record: dict[str, Any],
) -> bool:
    if record.get("_mock") is True:
        return True

    notice = record.get("_notice")

    if isinstance(notice, str):
        notice_lower = notice.lower()

        mock_terms = (
            "mock",
            "sample data",
            "sample record",
            "not real",
            "placeholder",
            "synthetic",
        )

        if any(
            term in notice_lower
            for term in mock_terms
        ):
            return True

    title = record.get("title")

    if is_synthetic_title(title):
        return True

    return False


def get_source_url(
    record: dict[str, Any],
) -> str:
    for field in (
        "sourceUrl",
        "source_url",
        "jobUrl",
        "job_url",
        "url",
        "link",
    ):
        value = record.get(field)

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    return ""


def get_apply_url(
    record: dict[str, Any],
) -> str:
    for field in (
        "applyUrl",
        "apply_url",
        "applicationUrl",
        "application_url",
    ):
        value = record.get(field)

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    apply_options = record.get(
        "applyOptions",
        [],
    )

    if isinstance(apply_options, list):
        for option in apply_options:
            if not isinstance(option, dict):
                continue

            for field in (
                "link",
                "url",
                "applyUrl",
                "apply_url",
                "applicationUrl",
                "application_url",
            ):
                value = option.get(field)

                if isinstance(value, str):
                    value = value.strip()

                    if value:
                        return value

    return ""


def print_record(
    index: int,
    record: dict[str, Any],
) -> None:
    print()
    print(f"JOB #{index}")

    print(
        f"  title        : "
        f"{record.get('title')!r}"
    )

    print(
        f"  company      : "
        f"{record.get('companyName', record.get('company'))!r}"
    )

    print(
        f"  location     : "
        f"{record.get('location')!r}"
    )

    print(
        f"  datePosted   : "
        f"{record.get('datePosted', record.get('postedAt'))!r}"
    )

    print(
        f"  sourceUrl    : "
        f"{get_source_url(record)!r}"
    )

    print(
        f"  applyUrl     : "
        f"{get_apply_url(record)!r}"
    )

    print(
        f"  sourceDomain : "
        f"{record.get('sourceDomain')!r}"
    )

    print(
        f"  _mock        : "
        f"{record.get('_mock')!r}"
    )

    print(
        f"  _notice      : "
        f"{record.get('_notice')!r}"
    )


# ============================================================================
# ACTOR REQUEST
# ============================================================================


def run_actor_directly() -> list[dict[str, Any]]:
    actor_id = settings.APIFY_ACTOR_ID.replace(
        "/",
        "~",
    )

    url = (
        f"{APIFY_BASE_URL}/acts/"
        f"{actor_id}/run-sync-get-dataset-items"
    )

    payload = {
        "queries": [
            TEST_ROLE,
        ],
        "location": TEST_LOCATION,
        "maxResults": TEST_MAX_RESULTS,
        "country": TEST_COUNTRY,
        "language": TEST_LANGUAGE,
        "includeDetails": TEST_INCLUDE_DETAILS,
    }

    headers = {
        "Authorization": (
            f"Bearer {settings.APIFY_API_TOKEN}"
        ),
        "Content-Type": "application/json",
    }

    print("=" * 90)
    print("CONTROLLED APIFY ACTOR VALIDATION")
    print("=" * 90)

    print(
        "SearchPipeline : NOT RUN"
    )
    print(
        "Gemini         : NOT RUN"
    )
    print(
        "Google Sheets  : NOT WRITTEN"
    )
    print(
        "n8n            : NOT CALLED"
    )
    print(
        "Applications   : NOT SUBMITTED"
    )

    print("=" * 90)
    print("APIFY ACTOR")
    print("=" * 90)

    print(
        f"Actor       : {actor_id}"
    )

    print(
        f"Role        : {TEST_ROLE}"
    )

    print(
        f"Location    : {TEST_LOCATION}"
    )

    print(
        f"Country     : {TEST_COUNTRY}"
    )

    print(
        f"Language    : {TEST_LANGUAGE}"
    )

    print(
        f"Max results : {TEST_MAX_RESULTS}"
    )

    print(
        f"Details     : {TEST_INCLUDE_DETAILS}"
    )

    print()
    print("WARNING: ONE REAL APIFY ACTOR RUN")
    print()

    print("Input:")
    print(
        json.dumps(
            payload,
            indent=2,
        )
    )

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=180.0,
        )
    except Exception as exc:
        raise AssertionError(
            f"Apify request failed: {exc}"
        ) from exc

    print()
    print(
        f"HTTP status : {response.status_code}"
    )

    body_text = response.text

    require(
        response.status_code in {
            200,
            201,
        },
        (
            f"Apify Actor failed. "
            f"HTTP {response.status_code}: "
            f"{body_text[:5000]}"
        ),
    )

    try:
        payload_response = response.json()
    except Exception as exc:
        raise AssertionError(
            "Apify returned a non-JSON response."
        ) from exc

    if isinstance(
        payload_response,
        list,
    ):
        raw_jobs = payload_response

    elif isinstance(
        payload_response,
        dict,
    ):
        data = payload_response.get(
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
            "Apify returned an unexpected response shape: "
            f"{type(payload_response).__name__}"
        )

    print(
        f"Raw jobs returned: {len(raw_jobs)}"
    )

    require(
        len(raw_jobs) > 0,
        (
            "Apify returned zero raw jobs."
        ),
    )

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        require(
            isinstance(record, dict),
            (
                f"Apify record #{index} is not a dictionary: "
                f"{type(record).__name__}"
            ),
        )

    return raw_jobs


# ============================================================================
# RAW SCHEMA
# ============================================================================


def print_raw_schema(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("RAW ACTOR SCHEMA")
    print("=" * 90)

    fields: set[str] = set()

    for record in raw_jobs:
        fields.update(
            str(key)
            for key in record.keys()
        )

    for field in sorted(fields):
        print(
            f"  - {field}"
        )


# ============================================================================
# RAW SAMPLE
# ============================================================================


def print_raw_sample(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("RAW JOB SAMPLE")
    print("=" * 90)

    for index, record in enumerate(
        raw_jobs[:10],
        start=1,
    ):
        print_record(
            index,
            record,
        )


# ============================================================================
# MOCK VALIDATION
# ============================================================================


def validate_no_mock_records(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("MOCK / SYNTHETIC DATA VALIDATION")
    print("=" * 90)

    failures: list[str] = []

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        if record.get("_mock") is True:
            failures.append(
                f"Job #{index}: _mock=True"
            )

        notice = record.get("_notice")

        if isinstance(notice, str):
            notice_lower = notice.lower()

            if any(
                term in notice_lower
                for term in (
                    "mock",
                    "sample data",
                    "sample record",
                    "not real",
                    "placeholder",
                    "synthetic",
                )
            ):
                failures.append(
                    f"Job #{index}: mock/sample notice={notice!r}"
                )

        title = record.get("title")

        if is_synthetic_title(title):
            failures.append(
                f"Job #{index}: synthetic title={title!r}"
            )

    print(
        f"Mock/synthetic failures: "
        f"{len(failures)}"
    )

    if failures:
        for failure in failures[:20]:
            print(
                f"  FAIL -> {failure}"
            )

        raise AssertionError(
            "Apify Actor returned mock/synthetic records. "
            "The Actor is not suitable for production."
        )

    print(
        "PASS: No explicit mock/synthetic records detected."
    )


# ============================================================================
# JOB FIELD VALIDATION
# ============================================================================


def validate_job_fields(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("JOB FIELD VALIDATION")
    print("=" * 90)

    failures: list[str] = []

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        title = record.get(
            "title",
        )

        company = (
            record.get("companyName")
            or record.get("company")
        )

        location = record.get(
            "location",
        )

        if not isinstance(title, str) or not title.strip():
            failures.append(
                f"Job #{index}: missing title"
            )

        if not isinstance(company, str) or not company.strip():
            failures.append(
                f"Job #{index}: missing company"
            )

        if not isinstance(location, str) or not location.strip():
            failures.append(
                f"Job #{index}: missing location"
            )

    print(
        f"Field validation failures: "
        f"{len(failures)}"
    )

    if failures:
        for failure in failures[:20]:
            print(
                f"  FAIL -> {failure}"
            )

        raise AssertionError(
            "One or more Actor records are missing "
            "required job fields."
        )

    print(
        "PASS: Required job fields are present."
    )


# ============================================================================
# LOCATION VALIDATION
# ============================================================================


def validate_location(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("LOCATION VALIDATION")
    print("=" * 90)

    location_tokens = (
        "mumbai",
        "maharashtra",
        "remote",
        "india",
    )

    failures: list[str] = []

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        location = str(
            record.get(
                "location",
                "",
            )
            or ""
        ).strip().lower()

        if not location:
            failures.append(
                f"Job #{index}: empty location"
            )
            continue

        if not any(
            token in location
            for token in location_tokens
        ):
            failures.append(
                f"Job #{index}: unexpected location={location!r}"
            )

    print(
        f"Location failures: {len(failures)}"
    )

    if failures:
        for failure in failures[:20]:
            print(
                f"  FAIL -> {failure}"
            )

        raise AssertionError(
            "Actor returned jobs outside the requested "
            "Mumbai/India location scope."
        )

    print(
        "PASS: Location values are consistent with the test."
    )


# ============================================================================
# SOURCE URL VALIDATION
# ============================================================================


def validate_source_urls(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("SOURCE URL VALIDATION")
    print("=" * 90)

    valid = 0
    google = 0
    invalid = 0
    placeholder = 0

    failures: list[str] = []

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        source_url = get_source_url(
            record,
        )

        if not is_http_url(source_url):
            invalid += 1

            failures.append(
                f"Job #{index}: invalid sourceUrl={source_url!r}"
            )

            continue

        if is_placeholder_url(source_url):
            placeholder += 1

            failures.append(
                f"Job #{index}: placeholder sourceUrl={source_url!r}"
            )

            continue

        if is_google_url(source_url):
            google += 1

        valid += 1

    print(
        f"Valid sourceUrl values : {valid}"
    )

    print(
        f"Google sourceUrl values : {google}"
    )

    print(
        f"Invalid sourceUrl values: {invalid}"
    )

    print(
        f"Placeholder URLs       : {placeholder}"
    )

    if failures:
        print()

        for failure in failures[:20]:
            print(
                f"  FAIL -> {failure}"
            )

    require(
        not failures,
        (
            "One or more Actor records have an invalid, "
            "missing, or placeholder sourceUrl."
        ),
    )

    print(
        "PASS: Source URLs are valid."
    )


# ============================================================================
# APPLICATION URL VALIDATION
# ============================================================================


def validate_application_urls(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("APPLICATION URL VALIDATION")
    print("=" * 90)

    valid_apply = 0
    missing_apply = 0
    google_apply = 0
    placeholder_apply = 0

    for index, record in enumerate(
        raw_jobs,
        start=1,
    ):
        apply_url = get_apply_url(
            record,
        )

        if not apply_url:
            missing_apply += 1
            continue

        if not is_http_url(apply_url):
            raise AssertionError(
                f"Job #{index} has invalid applyUrl: "
                f"{apply_url!r}"
            )

        if is_placeholder_url(apply_url):
            placeholder_apply += 1

        if is_google_url(apply_url):
            google_apply += 1

        valid_apply += 1

    print(
        f"Valid apply URLs       : {valid_apply}"
    )

    print(
        f"Missing apply URLs     : {missing_apply}"
    )

    print(
        f"Google apply URLs      : {google_apply}"
    )

    print(
        f"Placeholder apply URLs : {placeholder_apply}"
    )

    require(
        placeholder_apply == 0,
        (
            "Actor returned placeholder application URLs."
        ),
    )

    if valid_apply == 0:
        print()
        print(
            "WARNING: Actor returned zero application URLs."
        )

        print(
            "This means the Actor may be useful for discovery "
            "but is NOT currently suitable for direct application routing."
        )

    else:
        print(
            "PASS: Application URL fields contain usable URLs."
        )


# ============================================================================
# SOURCE DOMAIN VALIDATION
# ============================================================================


def validate_source_domains(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("SOURCE DOMAIN VALIDATION")
    print("=" * 90)

    domains: dict[str, int] = {}

    for record in raw_jobs:
        domain = record.get(
            "sourceDomain",
        )

        if isinstance(domain, str):
            domain = domain.strip()

            if domain:
                domains[domain] = (
                    domains.get(
                        domain,
                        0,
                    )
                    + 1
                )

    if not domains:
        print(
            "WARNING: No sourceDomain values returned."
        )

        return

    for domain, count in sorted(
        domains.items(),
    ):
        print(
            f"  {domain}: {count}"
        )

    print(
        "PASS: Source-domain inspection completed."
    )


# ============================================================================
# ACTOR SUITABILITY
# ============================================================================


def validate_actor_suitability(
    raw_jobs: list[dict[str, Any]],
) -> None:
    print()
    print("=" * 90)
    print("ACTOR SUITABILITY")
    print("=" * 90)

    real_jobs = 0
    with_application_urls = 0

    for record in raw_jobs:
        if not is_mock_record(record):
            real_jobs += 1

        if get_apply_url(record):
            with_application_urls += 1

    print(
        f"Real/non-mock jobs      : {real_jobs}/{len(raw_jobs)}"
    )

    print(
        f"Jobs with apply URL     : "
        f"{with_application_urls}/{len(raw_jobs)}"
    )

    require(
        real_jobs == len(raw_jobs),
        (
            "Actor contains mock/synthetic records. "
            "Do not connect this Actor to the production pipeline."
        ),
    )

    require(
        with_application_urls > 0,
        (
            "Actor returned no application URLs. "
            "It cannot currently satisfy the production requirement "
            "for application routing."
        ),
    )

    print()
    print(
        "PASS: Actor satisfies the minimum production suitability checks."
    )


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    raw_jobs = run_actor_directly()

    print_raw_schema(
        raw_jobs,
    )

    print_raw_sample(
        raw_jobs,
    )

    validate_no_mock_records(
        raw_jobs,
    )

    validate_job_fields(
        raw_jobs,
    )

    validate_location(
        raw_jobs,
    )

    validate_source_urls(
        raw_jobs,
    )

    validate_application_urls(
        raw_jobs,
    )

    validate_source_domains(
        raw_jobs,
    )

    validate_actor_suitability(
        raw_jobs,
    )

    print()
    print("=" * 90)
    print("CONTROLLED APIFY VALIDATION PASSED")
    print("=" * 90)

    print(
        f"Actor : {settings.APIFY_ACTOR_ID}"
    )

    print(
        f"Jobs  : {len(raw_jobs)}"
    )

    print()
    print(
        "The Actor returned non-mock jobs with usable source "
        "and application URL data."
    )

    print(
        "Production SearchPipeline was NOT run."
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()
        print("=" * 90)
        print("CONTROLLED APIFY VALIDATION FAILED")
        print("=" * 90)

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print("=" * 90)

        raise