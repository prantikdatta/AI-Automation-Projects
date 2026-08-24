from __future__ import annotations

from abc import abstractmethod

from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.providers.base import BaseProvider
from job_search_automation.providers.capabilities import (
    ProviderCapabilities,
)
from job_search_automation.providers.metadata import (
    ProviderMetadata,
)
from job_search_automation.providers.provider_cache import (
    ProviderCache,
)
from job_search_automation.utils.role_matcher import (
    RoleMatcher,
)


class ATSProvider(BaseProvider):
    """
    Base class shared by every ATS provider.

    Responsibilities
    ----------------
    • Download every available job
    • Cache provider results
    • Perform local relevance filtering
    • Return canonical SearchResponse
    """

    @property
    @abstractmethod
    def metadata(
        self,
    ) -> ProviderMetadata:
        """
        Immutable provider metadata.
        """

    @property
    def capabilities(
        self,
    ) -> ProviderCapabilities:

        return self.metadata.capabilities

    @abstractmethod
    def fetch_jobs(
        self,
    ) -> list[Job]:
        """
        Download every job exposed by this ATS.
        """

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        if ProviderCache.has(self.name):

            jobs = ProviderCache.get(
                self.name,
            )

        else:

            jobs = self.fetch_jobs()

            ProviderCache.set(
                self.name,
                jobs,
            )

        filtered_jobs = self.filter_jobs(
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

    def filter_jobs(
        self,
        jobs: list[Job],
        request: SearchRequest,
    ) -> list[Job]:

        return [

            job

            for job in jobs

            if RoleMatcher.is_relevant(
                job,
                request,
            )

        ]