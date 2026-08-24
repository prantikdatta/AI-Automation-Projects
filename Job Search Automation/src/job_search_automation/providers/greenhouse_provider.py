from __future__ import annotations

from job_search_automation.clients.greenhouse_client import (
    GreenhouseClient,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import (
    SearchRequest,
)
from job_search_automation.models.response import (
    SearchResponse,
)
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.greenhouse import (
    GreenhouseNormalizer,
)
from job_search_automation.providers.base import (
    BaseProvider,
)
from job_search_automation.providers.provider_cache import (
    ProviderCache,
)
from job_search_automation.providers.capabilities import (
    ProviderCapabilities,
)
from job_search_automation.providers.metadata import (
    ProviderMetadata,
)
from job_search_automation.services import logger


class GreenhouseProvider(BaseProvider):

    BOARD_NAMES = [
        "stripe",
        "airbnb",
        "coinbase",
        "notion",
        "datadog",
        "duolingo",
        "affirm",
        "plaid",
        "discord",
        "robinhood",
    ]

    def __init__(self):

        self.client = GreenhouseClient()

        self.normalizer = GreenhouseNormalizer()

    @property
    def name(self):

        return "Greenhouse"

    @property
    def metadata(self) -> ProviderMetadata:

        return ProviderMetadata(
            name="greenhouse",
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

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        #
        # CACHE HIT
        #

        if ProviderCache.has(self.name):

            cached_jobs = ProviderCache.get(self.name)

            logger.info(
                "GREENHOUSE CACHE HIT (%d cached jobs)",
                len(cached_jobs),
            )

            filtered_jobs = self._filter_jobs(
                cached_jobs,
                request,
            )

            return SearchResponse(

                provider=self.name,

                jobs=filtered_jobs,

                total_found=len(cached_jobs),

                total_returned=len(filtered_jobs),

                success=True,

                message="CACHE",

            )

        #
        # CACHE MISS
        #

        logger.info(
            "GREENHOUSE CACHE MISS -> Downloading ATS jobs..."
        )

        jobs: list[Job] = []

        for board in self.BOARD_NAMES:

            try:

                payload = self.client.search_jobs(
                    board,
                )

            except Exception:

                continue

            for raw_job in payload.get(
                "jobs",
                [],
            ):

                normalized = self.normalizer.normalize(

                    raw=raw_job,

                    searched_role=request.searched_role,

                )

                jobs.append(

                    CanonicalMapper.to_job(
                        normalized,
                    )

                )

        ProviderCache.set(
            self.name,
            jobs,
        )

        filtered_jobs = self._filter_jobs(
            jobs,
            request,
        )

        return SearchResponse(

            provider=self.name,

            jobs=filtered_jobs,

            total_found=len(jobs),

            total_returned=len(filtered_jobs),

            success=True,

            message="OK",

        )

    def _filter_jobs(
        self,
        jobs: list[Job],
        request: SearchRequest,
    ) -> list[Job]:

        keywords = [

            keyword.lower()

            for keyword in request.keywords

        ]

        filtered = []

        for job in jobs:

            searchable = (

                f"{job.title} {job.description}"

            ).lower()

            if any(

                keyword in searchable

                for keyword in keywords

            ):

                filtered.append(job)

        return filtered