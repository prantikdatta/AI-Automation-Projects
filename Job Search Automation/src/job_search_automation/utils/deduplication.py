from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlunparse,
)

from job_search_automation.models.job import Job


_LOCATION_ALIASES = {
    "bengaluru": "bangalore",
    "bangalore urban": "bangalore",
    "bombay": "mumbai",
    "new delhi": "delhi",
    "navi mumbai": "mumbai",
    "gurugram": "gurgaon",
    "hyderabad district": "hyderabad",
}


_GENERIC_LOCATIONS = {
    "",
    "india",
    "remote",
    "work from home",
    "multiple locations",
    "pan india",
}


# Tracking/query parameters that should not make two application URLs
# appear different.
_TRACKING_QUERY_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "ref",
    "source",
}


def _normalize_text(value: str) -> str:
    """
    Normalize free text for deterministic comparisons.
    """

    if not value:
        return ""

    value = value.lower().strip()

    value = re.sub(r"\s+", " ", value)

    value = re.sub(r"[^\w\s]", "", value)

    return value


def _normalize_location(location: str) -> str:
    """
    Normalize location names.

    If the location is too generic, return an empty string so
    duplicate detection can rely on stronger identifiers.
    """

    normalized = _normalize_text(location)

    if normalized in _GENERIC_LOCATIONS:
        return ""

    return _LOCATION_ALIASES.get(
        normalized,
        normalized,
    )


def _normalize_job_url(url: str) -> str:
    """
    Normalize a job/application URL for duplicate detection.

    Rules:
        - trim surrounding whitespace
        - lowercase scheme and hostname
        - remove URL fragments
        - remove trailing slash from the path
        - remove known tracking parameters
        - preserve meaningful query parameters
        - sort remaining query parameters deterministically

    Examples:

        https://Example.com/jobs/123/
        https://example.com/jobs/123

    are treated as the same URL.

    Likewise, tracking parameters such as utm_source or gclid do not
    create a second job identity.
    """

    if not url:
        return ""

    raw = str(url).strip()

    if not raw:
        return ""

    try:
        parsed = urlparse(raw)

        scheme = parsed.scheme.lower()

        hostname = (
            parsed.hostname.lower()
            if parsed.hostname
            else ""
        )

        if not hostname:
            return raw.lower().rstrip("/")

        # Preserve an explicit non-default port.
        netloc = hostname

        try:
            port = parsed.port
        except ValueError:
            port = None

        if port is not None:
            is_default_port = (
                (scheme == "http" and port == 80)
                or (
                    scheme == "https"
                    and port == 443
                )
            )

            if not is_default_port:
                netloc = f"{hostname}:{port}"

        path = parsed.path or "/"

        # Normalize repeated trailing slashes.
        if path != "/":
            path = path.rstrip("/")

        # Remove tracking parameters while preserving meaningful ones.
        query_parameters = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if key.lower()
            not in _TRACKING_QUERY_PARAMETERS
        ]

        query_parameters.sort(
            key=lambda pair: (
                pair[0].lower(),
                pair[1],
            )
        )

        query = urlencode(
            query_parameters,
            doseq=True,
        )

        normalized = urlunparse(
            (
                scheme,
                netloc,
                path,
                "",
                query,
                "",
            )
        )

        return normalized.rstrip("/")

    except Exception:
        # Deduplication must never crash the production pipeline because
        # a provider supplied a malformed URL.
        return raw.lower().rstrip("/")


def _build_duplicate_key(job: Job) -> str:
    """
    Build a deterministic duplicate key.

    Priority:
        1. Normalized job URL, when available.
        2. Company + title + location.
        3. Company + title when location is generic/unavailable.

    URL identity is authoritative because the same job can legitimately
    have different titles, locations, or provider metadata across sources.
    """

    job_url = _normalize_job_url(
        getattr(
            job,
            "job_url",
            "",
        )
    )

    if job_url:
        return f"url|{job_url}"

    company = _normalize_text(
        getattr(
            job,
            "company",
            "",
        )
    )

    title = _normalize_text(
        getattr(
            job,
            "title",
            "",
        )
    )

    location = _normalize_location(
        getattr(
            job,
            "location",
            "",
        )
    )

    if location:
        return f"text|{company}|{title}|{location}"

    return f"text|{company}|{title}"


def deduplicate_jobs(
    jobs: List[Job],
) -> List[Job]:
    """
    Remove duplicate jobs deterministically.

    Duplicate definition
    --------------------
    When a valid job URL exists:

        normalized job URL

    is the authoritative identity.

    If no usable URL exists:

        Company + Title + Location

    is used.

    If location is generic/unavailable:

        Company + Title

    is used.

    First occurrence wins.

    The generated duplicate key is persisted on each Job as
    `duplicate_key` for downstream diagnostics and export.
    """

    unique_jobs: Dict[str, Job] = {}

    for job in jobs:
        duplicate_key = _build_duplicate_key(job)

        job.duplicate_key = duplicate_key

        if duplicate_key not in unique_jobs:
            unique_jobs[duplicate_key] = job

    return list(unique_jobs.values())