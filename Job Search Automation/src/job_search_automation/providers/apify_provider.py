from __future__ import annotations

from job_search_automation.clients.apify_client import (
    ApifyClient,
)
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.normalizers.apify import (
    ApifyNormalizer,
)
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.providers.base import BaseProvider


class ApifyProvider(BaseProvider):
    """
    Apify implementation.

    Responsibilities
    ----------------
    - Fetch raw jobs.
    - Normalize payload.
    - Convert to canonical Job.
    - Return SearchResponse.

    The ApifyClient owns provider-specific API failures,
    rate-limit handling, and quota suppression.

    The provider does NOT:
    - deduplicate jobs
    - apply final freshness rules
    - rank jobs
    - perform resume matching
    - perform final selection
    """

    name = "Apify"

    def __init__(self) -> None:

        self.client = ApifyClient()

        self.normalizer = ApifyNormalizer()

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Execute an Apify search using the canonical SearchRequest.

        If Apify is rate-limited or its quota is exhausted,
        ApifyClient returns an empty payload and the provider
        returns a successful zero-job response so the remaining
        provider pipeline can continue normally.
        """

        location = (
            request.locations[0]
            if request.locations
            else "India"
        )

        payload = self.client.search_jobs(
            query=request.searched_role,
            location=location,
            max_items=request.limit,
        )

        jobs = []

        for raw in payload:

            normalized = self.normalizer.normalize(
                raw,
                request.searched_role,
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
            message=(
                "OK"
                if jobs
                else "No Apify jobs available."
            ),
        )