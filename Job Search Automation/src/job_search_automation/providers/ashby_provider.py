from __future__ import annotations

from job_search_automation.clients.ashby_client import (
    AshbyClient,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.ashby import (
    AshbyNormalizer,
)
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.providers.ats_provider import (
    ATSProvider,
)
from job_search_automation.providers.capabilities import (
    ProviderCapabilities,
)
from job_search_automation.providers.metadata import (
    ProviderMetadata,
)
from job_search_automation.providers.provider_cache import (
    ProviderCache,
)
from job_search_automation.services import logger


class AshbyProvider(ATSProvider):

    COMPANY_BOARDS = [
        "openai",
        "notion",
        "scale-ai",
        "vercel",
        "cursor",
        "retool",
        "pinecone",
        "runway",
        "modal",
        "character",
    ]

    def __init__(self):

        self.client = AshbyClient()

        self.normalizer = AshbyNormalizer()

    @property
    def name(self):

        return "Ashby"

    @property
    def metadata(self) -> ProviderMetadata:

        return ProviderMetadata(
            name="ashby",
            version="1.0",
            provider_type="ATS",
            capabilities=ProviderCapabilities(
                is_ats_provider=True,
                supports_location=False,
                supports_remote=True,
                supports_salary=False,
                supports_company_filter=True,
                supports_posted_date=True,
                supports_multiple_roles=True,
                requires_local_filtering=True,
            ),
        )

    def fetch_jobs(
        self,
    ) -> list[Job]:

        jobs: list[Job] = []

        for company in self.COMPANY_BOARDS:

            try:

                payload = self.client.search_jobs(
                    company,
                )

            except Exception as exc:

                logger.warning(
                    "Skipping %s (%s)",
                    company,
                    exc,
                )
                continue

            for raw_job in payload.get(
                "jobs",
                [],
            ):

                normalized = self.normalizer.normalize(
                    raw=raw_job,
                    searched_role="",
                )

                jobs.append(
                    CanonicalMapper.to_job(
                        normalized,
                    )
                )

        logger.info(
            "Ashby downloaded %d jobs",
            len(jobs),
        )

        return jobs

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        if ProviderCache.has(self.name):

            all_jobs = ProviderCache.get(self.name)

            logger.info(
                "ASHBY CACHE HIT (%d jobs)",
                len(all_jobs),
            )

        else:

            logger.info(
                "ASHBY CACHE MISS -> downloading jobs"
            )

            all_jobs = self.fetch_jobs()

            ProviderCache.set(
                self.name,
                all_jobs,
            )

        filtered = self._filter_jobs(
            jobs=all_jobs,
            request=request,
        )

        return SearchResponse(
            provider=self.name,
            jobs=filtered,
            total_found=len(all_jobs),
            total_returned=len(filtered),
            success=True,
            message="OK",
        )

    def _filter_jobs(
        self,
        jobs: list[Job],
        request: SearchRequest,
    ) -> list[Job]:

        keywords = {
            keyword.lower()
            for keyword in request.keywords
        }

        filtered: list[Job] = []

        for job in jobs:

            searchable = (
                f"{job.title} "
                f"{job.description} "
                f"{job.job_bucket} "
                f"{' '.join(job.skills)}"
            ).lower()

            if any(
                keyword in searchable
                for keyword in keywords
            ):
                filtered.append(job)

        filtered.sort(
            key=lambda job: (
                job.posting_priority,
                job.posted_at,
            ),
            reverse=True,
        )

        if request.limit:

            filtered = filtered[: request.limit]

        logger.info(
            "Ashby filtered %d -> %d jobs",
            len(jobs),
            len(filtered),
        )

        return filtered