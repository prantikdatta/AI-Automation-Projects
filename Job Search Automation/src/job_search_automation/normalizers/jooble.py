from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class JoobleNormalizer(BaseNormalizer):

    provider_name = "Jooble"

    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        posted_at = None

        updated = raw.get("updated")

        if updated:

            try:

                posted_at = datetime.fromisoformat(
                    updated.replace("Z", "+00:00")
                )

            except Exception:

                posted_at = None

        return NormalizedJob(

            searched_role=searched_role,

            title=raw.get("title", ""),

            company=raw.get("company", ""),

            location=raw.get("location", ""),

            description=raw.get("snippet", ""),

            job_url=raw.get("link", ""),

            provider=self.provider_name,

            source=self.provider_name,

            posted_at=posted_at,

            employment_type=None,

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