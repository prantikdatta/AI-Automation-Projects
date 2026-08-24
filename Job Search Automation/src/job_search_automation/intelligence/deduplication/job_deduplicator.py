from __future__ import annotations

import re
from dataclasses import dataclass

from job_search_automation.models.job import Job


@dataclass(frozen=True)
class DuplicateDecision:
    is_duplicate: bool
    canonical_job_id: str | None
    reason: str
    similarity: float


class JobDeduplicator:
    """
    Deterministic job deduplication.

    Duplicate detection is based on:
        1. Exact job URL
        2. Exact normalized company/title/location
        3. Fuzzy title similarity for the same company/location
    """

    def __init__(
        self,
        similarity_threshold: float = 0.90,
    ) -> None:
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def normalize_text(value: str | None) -> str:
        if not value:
            return ""

        value = value.lower().strip()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    @classmethod
    def normalize_url(cls, value: str | None) -> str:
        if not value:
            return ""

        value = value.strip().lower()

        value = re.sub(
            r"^https?://",
            "",
            value,
        )

        value = value.rstrip("/")

        return value

    @classmethod
    def canonical_key(
        cls,
        job: Job,
    ) -> tuple[str, str, str]:
        return (
            cls.normalize_text(job.company),
            cls.normalize_text(job.title),
            cls.normalize_text(job.location),
        )

    @classmethod
    def exact_url_key(
        cls,
        job: Job,
    ) -> str:
        return cls.normalize_url(job.job_url)

    @staticmethod
    def title_similarity(
        first: str,
        second: str,
    ) -> float:
        first_tokens = set(first.split())
        second_tokens = set(second.split())

        if not first_tokens or not second_tokens:
            return 0.0

        intersection = first_tokens & second_tokens
        union = first_tokens | second_tokens

        return len(intersection) / len(union)

    def find_duplicate(
        self,
        job: Job,
        canonical_jobs: list[Job],
    ) -> DuplicateDecision:
        url_key = self.exact_url_key(job)

        if url_key:
            for canonical in canonical_jobs:
                if (
                    self.exact_url_key(canonical)
                    == url_key
                ):
                    return DuplicateDecision(
                        is_duplicate=True,
                        canonical_job_id=self.job_id(
                            canonical
                        ),
                        reason="Exact job URL duplicate.",
                        similarity=1.0,
                    )

        company = self.normalize_text(job.company)
        location = self.normalize_text(job.location)
        title = self.normalize_text(job.title)

        for canonical in canonical_jobs:
            canonical_company = self.normalize_text(
                canonical.company
            )
            canonical_location = self.normalize_text(
                canonical.location
            )
            canonical_title = self.normalize_text(
                canonical.title
            )

            if (
                company
                and company == canonical_company
                and location
                and location == canonical_location
                and title
                and title == canonical_title
            ):
                return DuplicateDecision(
                    is_duplicate=True,
                    canonical_job_id=self.job_id(
                        canonical
                    ),
                    reason=(
                        "Exact company/title/location "
                        "duplicate."
                    ),
                    similarity=1.0,
                )

            if (
                company
                and company == canonical_company
                and location
                and location == canonical_location
            ):
                similarity = self.title_similarity(
                    title,
                    canonical_title,
                )

                if (
                    similarity
                    >= self.similarity_threshold
                ):
                    return DuplicateDecision(
                        is_duplicate=True,
                        canonical_job_id=self.job_id(
                            canonical
                        ),
                        reason=(
                            "Near-duplicate title for "
                            "same company and location."
                        ),
                        similarity=similarity,
                    )

        return DuplicateDecision(
            is_duplicate=False,
            canonical_job_id=None,
            reason="Unique job.",
            similarity=0.0,
        )

    @staticmethod
    def job_id(job: Job) -> str:
        if job.job_url:
            return JobDeduplicator.normalize_url(
                job.job_url
            )

        return "|".join(
            [
                JobDeduplicator.normalize_text(
                    job.company
                ),
                JobDeduplicator.normalize_text(
                    job.title
                ),
                JobDeduplicator.normalize_text(
                    job.location
                ),
            ]
        )

    def deduplicate(
        self,
        jobs: list[Job],
    ) -> tuple[list[Job], dict[str, DuplicateDecision]]:
        canonical_jobs: list[Job] = []

        decisions: dict[str, DuplicateDecision] = {}

        for job in jobs:
            job_id = self.job_id(job)

            decision = self.find_duplicate(
                job,
                canonical_jobs,
            )

            decisions[job_id] = decision

            if not decision.is_duplicate:
                canonical_jobs.append(job)

        return canonical_jobs, decisions