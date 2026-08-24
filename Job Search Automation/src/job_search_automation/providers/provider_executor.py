from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from typing import Dict
from typing import List

from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.providers.base import BaseProvider
from job_search_automation.services import logger

MAX_PROVIDER_WORKERS = 5


class ProviderExecutor:
    """
    Executes providers concurrently.

    Exposes two APIs

    execute()
        Returns a flat list of jobs.

    execute_grouped()
        Returns jobs grouped by provider.
    """

    # ==========================================================
    # Legacy API
    # ==========================================================

    @staticmethod
    def execute(
        providers: List[BaseProvider],
        request: SearchRequest,
    ) -> List[Job]:

        grouped = ProviderExecutor.execute_grouped(
            providers,
            request,
        )

        jobs: List[Job] = []

        for provider_jobs in grouped.values():

            jobs.extend(
                provider_jobs,
            )

        return jobs

    # ==========================================================
    # Validation API
    # ==========================================================

    @staticmethod
    def execute_grouped(
        providers: List[BaseProvider],
        request: SearchRequest,
    ) -> Dict[str, List[Job]]:

        grouped: Dict[str, List[Job]] = {}

        if not providers:

            return grouped

        with ThreadPoolExecutor(

            max_workers=min(
                MAX_PROVIDER_WORKERS,
                len(providers),
            )

        ) as executor:

            future_map = {

                executor.submit(

                    provider.search,

                    request,

                ): provider

                for provider in providers

            }

            for future in as_completed(

                future_map,

            ):

                provider = future_map[
                    future
                ]

                try:

                    response: SearchResponse = future.result()

                    grouped[
                        provider.name
                    ] = response.jobs or []
                    logger.info(

                        "%s returned %d jobs.",

                        provider.name,

                        len(
                            response.jobs
                        ),

                    )

                except Exception:

                    grouped[
                        provider.name
                    ] = []

                    logger.exception(

                        "%s failed. Continuing...",

                        provider.name,

                    )

        return grouped