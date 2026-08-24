from __future__ import annotations

import asyncio


from job_search_automation.ats.orchestrator import (
    ATSOrchestrator,
)

from job_search_automation.sources.rapidapi_source import (
    RapidAPISource,
)

from job_search_automation.ats.deduplicator import (
    ATSDeduplicator,
)


class JobSourceOrchestrator:
    """
    Combines all job discovery sources.

    Sources:

    ATS
    RapidAPI
    Apify (future)

    Output:

    Canonical Job[]
    """


    def __init__(
        self,
        ats_source,
        rapidapi_source,
    ):

        self.ats_source = ats_source

        self.rapidapi_source = (
            rapidapi_source
        )



    @classmethod
    def create(cls):

        return cls(

            ats_source=(
                ATSOrchestrator.create()
            ),

            rapidapi_source=(
                RapidAPISource()
            ),

        )



    async def run(self):

        results = await asyncio.gather(

            self.ats_source.run(),

            self.rapidapi_source.fetch_jobs(),

        )


        jobs = []


        for batch in results:

            jobs.extend(
                batch
            )


        jobs = ATSDeduplicator.deduplicate(
            jobs
        )

        return jobs