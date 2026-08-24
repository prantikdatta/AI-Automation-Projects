from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.models.job import Job


class LeverAdapter:
    """
    Converts Lever jobs into canonical Job model.
    """

    @staticmethod
    def normalize(
        raw_job: dict,
        company: str,
    ) -> Job:

        categories = raw_job.get(
            "categories",
            {},
        )

        location = categories.get(
            "location",
        ) or ""

        title = raw_job.get(
            "text",
        ) or ""

        return Job(
            searched_role=title,
            company=company,
            source="lever",
            provider="lever",
            title=title,
            location=location,
            job_url=raw_job.get(
                "hostedUrl",
            ) or "",
            posted_at=datetime.now(
                timezone.utc,
            ),
        )