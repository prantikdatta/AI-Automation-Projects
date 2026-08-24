from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class RemotiveNormalizer(BaseNormalizer):

    provider_name = "Remotive"

    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        posted_at = None

        publication_date = raw.get("publication_date")

        if publication_date:

            try:

                posted_at = datetime.fromisoformat(
                    publication_date.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:

                posted_at = None

        salary_text = raw.get("salary") or ""

        return NormalizedJob(

            searched_role=searched_role,

            title=raw.get(
                "title",
                "",
            ),

            company=raw.get(
                "company_name",
                "",
            ),

            location=raw.get(
                "candidate_required_location",
                "",
            ),

            description=raw.get(
                "description",
                "",
            ),

            job_url=raw.get(
                "url",
                "",
            ),

            provider="Remotive",

            source="Remotive",

            posted_at=posted_at,

            employment_type=raw.get(
                "job_type",
            ),

            seniority=None,

            remote=True,

            work_mode="Remote",

            salary_min=None,

            salary_max=None,

            currency=None,

            salary_confidence=(
                0.25 if salary_text else None
            ),

            skills=[],

            raw=raw,
        )