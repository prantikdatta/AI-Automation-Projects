from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.providers.base import BaseProvider
from job_search_automation.providers.provider_executor import (
    ProviderExecutor,
)
from job_search_automation.services import logger


class ProviderManager:
    """
    Coordinates execution of all registered providers.

    Provider categories
    -------------------
    API providers:
        Executed for every SearchRequest.

    ATS providers:
        Providers such as Ashby and Greenhouse are responsible
        for caching their complete ATS dataset internally and
        filtering that dataset for each SearchRequest.

    Responsibilities
    ----------------
    ProviderManager:
        - separates API and ATS providers
        - executes providers
        - executes independent ATS providers concurrently
        - groups results by provider
        - converts provider failures into logged failures
        - returns canonical Job objects

    ProviderManager does NOT:
        - normalize provider payloads
        - construct Job objects
        - perform deduplication
        - perform freshness filtering
        - perform resume matching
        - rank jobs
    """

    ATS_WORKERS = 8

    def __init__(
        self,
        providers: List[BaseProvider],
    ) -> None:

        self.providers = providers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        grouped = self.search_by_provider(request)

        jobs: List[Job] = []

        for provider_jobs in grouped.values():
            jobs.extend(provider_jobs)

        return SearchResponse(
            provider="ProviderManager",
            jobs=jobs,
            total_found=len(jobs),
            total_returned=len(jobs),
            success=True,
            message="Provider search completed.",
        )

    # ------------------------------------------------------------------
    # Provider-grouped execution
    # ------------------------------------------------------------------

    def search_by_provider(
        self,
        request: SearchRequest,
    ) -> Dict[str, List[Job]]:

        grouped: Dict[str, List[Job]] = defaultdict(list)

        api_providers: List[BaseProvider] = []
        ats_providers: List[BaseProvider] = []

        for provider in self.providers:

            metadata = getattr(
                provider,
                "metadata",
                None,
            )

            if (
                metadata is not None
                and metadata.capabilities.is_ats_provider
            ):
                ats_providers.append(provider)

            else:
                api_providers.append(provider)

        logger.info(
            "ProviderManager -> API=%d | ATS=%d",
            len(api_providers),
            len(ats_providers),
        )

        # --------------------------------------------------------------
        # API PROVIDERS
        #
        # ProviderExecutor already owns normal provider execution.
        # --------------------------------------------------------------

        if api_providers:

            try:

                api_results = ProviderExecutor.execute_grouped(
                    api_providers,
                    request,
                )

                for provider_name, jobs in api_results.items():

                    grouped[provider_name].extend(jobs)

            except Exception:

                logger.exception(
                    "API provider execution failed.",
                )

        # --------------------------------------------------------------
        # ATS PROVIDERS
        #
        # Run independent ATS providers concurrently.
        #
        # IMPORTANT:
        # We do NOT use ProviderCache here.
        #
        # Each ATS provider is responsible for caching its complete
        # dataset and applying request-specific filtering.
        # --------------------------------------------------------------

        if ats_providers:

            ats_results = self._execute_ats_providers(
                ats_providers,
                request,
            )

            for provider_name, jobs in ats_results.items():

                grouped[provider_name].extend(jobs)

        return dict(grouped)

    # ------------------------------------------------------------------
    # Concurrent ATS execution
    # ------------------------------------------------------------------

    def _execute_ats_providers(
        self,
        providers: List[BaseProvider],
        request: SearchRequest,
    ) -> Dict[str, List[Job]]:

        grouped: Dict[str, List[Job]] = defaultdict(list)

        worker_count = min(
            self.ATS_WORKERS,
            len(providers),
        )

        logger.info(
            "Executing %d ATS providers concurrently (%d workers).",
            len(providers),
            worker_count,
        )

        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="ats-provider",
        ) as executor:

            futures = {
                executor.submit(
                    self._execute_single_provider,
                    provider,
                    request,
                ): provider
                for provider in providers
            }

            for future in as_completed(futures):

                provider = futures[future]

                try:

                    provider_name, jobs = future.result()

                    grouped[provider_name].extend(jobs)

                    logger.info(
                        "%s returned %d jobs.",
                        provider_name,
                        len(jobs),
                    )

                except Exception:

                    logger.exception(
                        "ProviderManager failed for ATS provider '%s'.",
                        provider.name,
                    )

        return dict(grouped)

    # ------------------------------------------------------------------
    # Single provider execution
    # ------------------------------------------------------------------

    @staticmethod
    def _execute_single_provider(
        provider: BaseProvider,
        request: SearchRequest,
    ) -> tuple[str, List[Job]]:

        logger.info(
            "Executing ATS provider -> %s",
            provider.name,
        )

        response = provider.search(request)

        if not response.success:

            raise RuntimeError(
                response.message
                or f"{provider.name} search failed."
            )

        return (
            provider.name,
            response.jobs,
        )