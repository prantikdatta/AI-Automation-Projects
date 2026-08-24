from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Dict

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class AdzunaNormalizer(BaseNormalizer):
    """
    Converts raw Adzuna responses into the internal
    provider-independent NormalizedJob.
    """

    @staticmethod
    def normalize(
        raw: Dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        company = ""

        if raw.get("company"):
            company = raw["company"].get(
                "display_name",
                "",
            )

        location = ""

        if raw.get("location"):
            location = raw["location"].get(
                "display_name",
                "",
            )

        posted_at = None

        created = raw.get("created")

        if created:

            try:

                posted_at = datetime.fromisoformat(
                    created.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:

                posted_at = None

        return NormalizedJob(

            searched_role=searched_role,

            title=raw.get(
                "title",
                "",
            ),

            company=company,

            location=location,

            description=raw.get(
                "description",
                "",
            ),

            job_url=raw.get(
                "redirect_url",
                "",
            ),

            provider="Adzuna",

            source="Adzuna",

            posted_at=posted_at,

            employment_type=raw.get(
                "contract_type",
                "",
            ),

            remote=False,

            work_mode="",

            salary_min=raw.get(
                "salary_min",
            ),

            salary_max=raw.get(
                "salary_max",
            ),

            currency=raw.get(
                "salary_currency",
                "INR",
            ),

            skills=[],

            raw=raw,

        )