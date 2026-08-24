from __future__ import annotations

from job_search_automation.providers.ashby_provider import (
    AshbyProvider,
)
from job_search_automation.providers.greenhouse_provider import (
    GreenhouseProvider,
)


class ATSRegistry:
    """
    Registry for production ATS providers.

    Only providers that are currently maintained and validated
    should be listed here.
    """

    @staticmethod
    def providers():

        return [

            GreenhouseProvider(),

            AshbyProvider(),

        ]