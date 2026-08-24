from __future__ import annotations

from job_search_automation.ats.ashby.client import (
    AshbyClient,
)
from job_search_automation.ats.ashby.provider import (
    AshbyProvider,
)
from job_search_automation.ats.greenhouse.client import (
    GreenhouseClient,
)
from job_search_automation.ats.greenhouse.detail_client import (
    GreenhouseDetailClient,
)
from job_search_automation.ats.greenhouse.provider import (
    GreenhouseProvider,
)
from job_search_automation.ats.lever.client import (
    LeverClient,
)
from job_search_automation.ats.lever.provider import (
    LeverProvider,
)


class ATSFactory:

    @staticmethod
    def greenhouse():

        return GreenhouseProvider(

            client=GreenhouseClient(),

            detail_client=GreenhouseDetailClient(),

        )

    @staticmethod
    def lever():

        return LeverProvider(

            LeverClient(),

        )

    @staticmethod
    def ashby():

        return AshbyProvider(

            AshbyClient(),

        )