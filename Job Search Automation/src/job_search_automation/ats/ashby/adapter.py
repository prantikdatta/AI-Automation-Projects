from __future__ import annotations

from datetime import datetime
from datetime import timezone

from job_search_automation.models.job import Job


class AshbyAdapter:
    """
    Converts Ashby jobs into canonical Job model.
    """

    @staticmethod
    def normalize(
        raw_job: dict,
        company: str,
    ) -> Job:
        title = raw_job.get(
            "title",
        ) or ""

        location = raw_job.get(
            "location",
        ) or ""

        job_url = raw_job.get(
            "jobUrl",
        ) or ""

        return Job(
            searched_role=title,
            company=company,
            source="ashby",
            provider="ashby",
            title=title,
            location=location,
            job_url=job_url,
            posted_at=datetime.now(
                timezone.utc,
            ),
        )