from __future__ import annotations

from job_search_automation.clients.remotive_client import (
    RemotiveClient,
)
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.remotive import (
    RemotiveNormalizer,
)
from job_search_automation.providers.base import BaseProvider
from job_search_automation.utils.skill_extractor import (
    SkillExtractor,
)


class RemotiveProvider(BaseProvider):

    def __init__(self) -> None:

        self.client = RemotiveClient()

        self.normalizer = RemotiveNormalizer()

    @property
    def name(self) -> str:

        return "Remotive"

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        query = " ".join(
            request.keywords
        )

        payload = self.client.search_jobs(
            query
        )

        jobs = []

        for raw_job in payload.get(
            "jobs",
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