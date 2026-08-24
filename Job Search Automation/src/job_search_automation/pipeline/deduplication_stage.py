from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from job_search_automation.models.job import Job
from job_search_automation.services.dedupe_service import (
    DedupeService,
)


@dataclass(frozen=True)
class DeduplicationStageResult:
    """
    Result produced by the deduplication pipeline stage.
    """

    input_jobs: list[Job]
    unique_jobs: list[Job]
    duplicate_jobs: list[Job]
    decisions: dict[str, Any]

    @property
    def input_count(self) -> int:
        return len(self.input_jobs)

    @property
    def unique_count(self) -> int:
        return len(self.unique_jobs)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicate_jobs)


class DeduplicationStage:
    """
    Pipeline stage responsible only for deduplication.

    No freshness, scoring, ranking, enrichment, or resume
    matching occurs here.
    """

    def __init__(
        self,
        dedupe_service: DedupeService | None = None,
    ) -> None:
        self.dedupe_service = (
            dedupe_service
            or DedupeService()
        )

    def run(
        self,
        jobs: list[Job],
    ) -> DeduplicationStageResult:
        """
        Deduplicate the supplied jobs while preserving
        the canonical first occurrence.
        """

        unique_jobs, decisions = (
            self.dedupe_service.deduplicate(jobs)
        )

        unique_ids = {
            self._job_id(job)
            for job in unique_jobs
        }

        duplicate_jobs = [
            job
            for job in jobs
            if self._job_id(job)
            not in unique_ids
        ]

        return DeduplicationStageResult(
            input_jobs=jobs,
            unique_jobs=unique_jobs,
            duplicate_jobs=duplicate_jobs,
            decisions=decisions,
        )

    @staticmethod
    def _job_id(job: Job) -> str:
        if job.job_url:
            return job.job_url.strip().lower().rstrip("/")

        return "|".join(
            [
                (job.company or "").strip().lower(),
                (job.title or "").strip().lower(),
                (job.location or "").strip().lower(),
            ]
        )