from __future__ import annotations

from typing import Any

from job_search_automation.models.job import Job


class UniqueJobsExportStage:
    """
    Exports the deduplicated job pool before freshness filtering.

    Pipeline position:

        Search
          ↓
        Normalize
          ↓
        Deduplication
          ↓
        UNIQUE JOB EXPORT  ← this stage
          ↓
        Freshness
          ↓
        Relevance
          ↓
        Location / Work Mode
          ↓
        Scoring
          ↓
        Enrichment
          ↓
        Ranking
          ↓
        Final Export

    This stage owns only the transformation of unique jobs into
    export rows and delegates Google Sheets I/O to GoogleSheetsService.
    """

    STAGE_NAME = "unique_jobs_export"

    HEADERS = [
        "pipeline_stage",
        "pipeline_status",
        "title",
        "company",
        "location",
        "job_url",
        "source",
        "provider",
        "searched_role",
        "posted_at",
    ]

    def __init__(self, sheets_service: Any) -> None:
        self.sheets_service = sheets_service

    @classmethod
    def build_rows(
        cls,
        jobs: list[Job],
    ) -> list[list[Any]]:
        rows: list[list[Any]] = []

        for job in jobs:
            rows.append(
                [
                    "UNIQUE",
                    "PASSED",
                    job.title,
                    job.company,
                    job.location,
                    job.job_url,
                    job.source,
                    job.provider,
                    job.searched_role,
                    job.posted_at,
                ]
            )

        return rows

    def export(
        self,
        jobs: list[Job],
    ) -> int:
        if not jobs:
            return 0

        rows = self.build_rows(jobs)

        return self.sheets_service.append_unique_jobs(
            headers=self.HEADERS,
            rows=rows,
        )