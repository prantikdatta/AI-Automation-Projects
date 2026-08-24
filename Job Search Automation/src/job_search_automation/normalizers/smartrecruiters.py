from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class SmartRecruitersNormalizer(BaseNormalizer):

    provider_name = "SmartRecruiters"

    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        posted_at = None

        released = raw.get(
            "releasedDate",
        )

        if released:

            try:

                posted_at = datetime.fromisoformat(
                    released.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:

                posted_at = None

        location = ""

        if raw.get("location"):

            location = raw["location"].get(
                "city",
                "",
            )

        return NormalizedJob(

            searched_role=searched_role,

            title=raw.get(
                "name",
                "",
            ),

            company=raw.get(
                "company",
                "",
            ),

            location=location,

            description=raw.get(
                "jobAd",
                "",
            ),

            job_url=raw.get(
                "ref",
                "",
            ),

            provider="SmartRecruiters",

            source="SmartRecruiters",

            posted_at=posted_at,

            employment_type=raw.get(
                "typeOfEmployment",
            ),

            seniority=None,

            remote=False,

            work_mode="Unknown",

            salary_min=None,

            salary_max=None,

            currency=None,

            salary_confidence=None,

            skills=[],

            raw=raw,
        )