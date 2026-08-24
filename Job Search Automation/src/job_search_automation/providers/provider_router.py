from __future__ import annotations

from typing import List

from job_search_automation.models.request import SearchRequest
from job_search_automation.providers.base import BaseProvider
from job_search_automation.providers.provider_registry import ProviderRegistry


class ProviderRouter:
    """
    Decides which providers should execute
    for a given search request.
    """

    @staticmethod
    def route(
        request: SearchRequest,
    ) -> List[BaseProvider]:

        providers: List[BaseProvider] = []

        providers.extend(
            ProviderRegistry.api_providers()
        )

        if request.priority == 1:

            providers.extend(
                ProviderRegistry.ats_providers()
            )

        return providers