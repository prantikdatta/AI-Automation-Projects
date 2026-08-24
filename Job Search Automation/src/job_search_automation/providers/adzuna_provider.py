from __future__ import annotations

from job_search_automation.clients.adzuna_client import (
    AdzunaClient,
)
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.adzuna import (
    AdzunaNormalizer,
)
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.providers.base import BaseProvider
from job_search_automation.utils.skill_extractor import (
    SkillExtractor,
)


class AdzunaProvider(BaseProvider):

    def __init__(self):

        self.client = AdzunaClient()

        self.normalizer = AdzunaNormalizer()

    @property
    def name(self):

        return "Adzuna"

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        query = " ".join(
            request.keywords
        )

        payload = self.client.search_jobs(
            query=query,
        )

        jobs = []

        for raw_job in payload.get(
            "results",
            [],
        ):

            normalized = self.normalizer.normalize(
                raw=raw_job,
                searched_role=request.searched_role,
            )

            normalized.skills = SkillExtractor.extract(
                normalized.description
            )

            jobs.append(
                CanonicalMapper.to_job(
                    normalized
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