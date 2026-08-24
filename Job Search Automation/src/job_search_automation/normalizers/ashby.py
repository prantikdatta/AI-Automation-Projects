from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class AshbyNormalizer(BaseNormalizer):

    provider_name = "Ashby"

    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        posted_at = None

        if raw.get("publishedAt"):

            try:

                posted_at = datetime.fromisoformat(
                    raw["publishedAt"].replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:

                posted_at = None

        description = (
            raw.get("descriptionPlain")
            or raw.get("descriptionHtml")
            or ""
        )

        return NormalizedJob(

            searched_role=searched_role,

            title=raw.get(
                "title",
                "",
            ),

            company="",

            location=raw.get(
                "location",
                "",
            ),

            description=description,

            job_url=raw.get(
                "jobUrl",
                "",
            ),

            provider="Ashby",

            source="Ashby",

            posted_at=posted_at,

            employment_type=raw.get(
                "employmentType",
                "",
            ),

            seniority=None,

            remote=bool(
                raw.get("isRemote")
            ),

            work_mode=raw.get(
                "workplaceType",
                "",
            )
            or "",

            salary_min=None,

            salary_max=None,

            currency=None,

            salary_confidence=None,

            skills=[],

            raw=raw,
        )