from __future__ import annotations

from job_search_automation.clients.jooble_client import (
    JoobleClient,
)
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.jooble import (
    JoobleNormalizer,
)
from job_search_automation.providers.base import BaseProvider
from job_search_automation.utils.skill_extractor import SkillExtractor


class JoobleProvider(BaseProvider):

    name = "Jooble"

    def __init__(self):

        self.client = JoobleClient()

        self.normalizer = JoobleNormalizer()

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        payload = self.client.search_jobs(

            query=request.searched_role,

            location="India",

        )

        jobs = []

        for raw in payload.get("jobs", []):

            normalized = self.normalizer.normalize(

                raw,

                request.searched_role,

            )

            normalized.skills = SkillExtractor.extract(
                normalized.description
            )

            jobs.append(

                CanonicalMapper.to_job(

                    normalized,

                )

            )

        return SearchResponse(

            provider=self.name,

            jobs=jobs,

            total_found=len(jobs),

            total_returned=len(jobs),

            success=True,

            message="OK",

        )