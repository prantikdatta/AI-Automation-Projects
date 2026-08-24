from __future__ import annotations

from job_search_automation.providers.adzuna_provider import (
    AdzunaProvider,
)
from job_search_automation.providers.apify_provider import (
    ApifyProvider,
)
from job_search_automation.providers.ats_registry import (
    ATSRegistry,
)
from job_search_automation.providers.rapidapi_provider import (
    RapidAPIProvider,
)
from job_search_automation.providers.remotive_provider import (
    RemotiveProvider,
)


class ProviderRegistry:
    """
    Singleton provider registry.

    Every provider is instantiated exactly once.
    """

    _API_PROVIDERS = [
        RapidAPIProvider(),
        AdzunaProvider(),
        RemotiveProvider(),
        ApifyProvider(),
    ]

    _ATS_PROVIDERS = ATSRegistry.providers()

    @classmethod
    def api_providers(cls):
        return cls._API_PROVIDERS

    @classmethod
    def ats_providers(cls):
        return cls._ATS_PROVIDERS

    @classmethod
    def get_providers(cls):
        return (
            cls._API_PROVIDERS
            + cls._ATS_PROVIDERS
        )