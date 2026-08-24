from __future__ import annotations

from job_search_automation.clients.rapidapi_client import (
    RapidAPIClient,
)
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.rapidapi import (
    RapidAPINormalizer,
)
from job_search_automation.providers.base import BaseProvider
from job_search_automation.utils.skill_extractor import SkillExtractor


class RapidAPIProvider(BaseProvider):
    """
    RapidAPI (JSearch) implementation.

    Responsibilities
    ----------------
    - Build the provider-specific search query.
    - Pass SearchRequest controls to RapidAPIClient.
    - Fetch the requested candidate volume.
    - Normalize provider payloads.
    - Extract skills.
    - Convert normalized jobs into canonical Job objects.

    The provider does NOT:
    - deduplicate jobs
    - apply final freshness rules
    - rank jobs
    - perform resume matching
    - perform final selection
    """

    name = "RapidAPI"

    def __init__(self) -> None:
        self.client = RapidAPIClient()
        self.normalizer = RapidAPINormalizer()

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Execute a JSearch request using the canonical SearchRequest.
        """

        query = self._build_query(
            request,
        )

        payload = self.client.search_jobs(
            query=query,
            limit=request.limit,
            posted_within_days=request.posted_within_days,
            remote_only=request.remote_only,
        )

        jobs = []

        for raw_job in payload.get(
            "data",
            [],
        ):
            normalized = self.normalizer.normalize(
                raw=raw_job,
                searched_role=request.searched_role,
            )

            normalized.skills = SkillExtractor.extract(
                normalized.description,
            )

            job = CanonicalMapper.to_job(
                normalized,
            )

            jobs.append(job)

        return SearchResponse(
            provider=self.name,
            jobs=jobs,
            total_found=len(jobs),
            total_returned=len(jobs),
            success=True,
            message="OK",
        )

    @staticmethod
    def _build_query(
        request: SearchRequest,
    ) -> str:
        """
        Build a provider-specific JSearch query.

        Roles come from SearchStrategyEngine.
        Locations come from SearchRequest.

        Example:

            Data Analyst OR BI Analyst Mumbai

        or:

            Product Analyst OR Business Analyst Bangalore

        Remote searches explicitly include remote in the query when
        remote_only is enabled.
        """

        roles = [
            role.strip()
            for role in request.roles
            if role and role.strip()
        ]

        if not roles:
            roles = [
                request.searched_role.strip(),
            ]

        role_query = " OR ".join(
            roles,
        )

        locations = [
            location.strip()
            for location in request.locations
            if location and location.strip()
        ]

        location_query = ""

        if locations:
            location_query = (
                " "
                + " OR ".join(locations)
            )

        remote_query = ""

        if request.remote_only:
            remote_query = " remote"

        return (
            f"{role_query}"
            f"{location_query}"
            f"{remote_query}"
        ).strip()