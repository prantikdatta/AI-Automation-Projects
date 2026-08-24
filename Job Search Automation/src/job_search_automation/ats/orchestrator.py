from __future__ import annotations

import asyncio

from job_search_automation.ats.factory import (
    ATSFactory,
)

from job_search_automation.ats.registry import (
    ATSRegistry,
)

from job_search_automation.ats.filter import (
    ATSJobFilter,
)

from job_search_automation.ats.deduplicator import (
    ATSDeduplicator,
)

from job_search_automation.filtering.analytics_filter import (
    AnalyticsJobFilter,
)

class ATSOrchestrator:
    """
    Coordinates ATS ingestion pipeline.

    Flow:

    ATS Registry
        ↓
    ATS Providers
        ↓
    Normalize Jobs
        ↓
    Filter
        ↓
    Deduplicate
        ↓
    Return Jobs
    """


    def __init__(
        self,
        greenhouse_provider,
        lever_provider,
        ashby_provider,
        job_filter: ATSJobFilter,
    ):

        self.greenhouse_provider = (
            greenhouse_provider
        )

        self.lever_provider = (
            lever_provider
        )

        self.ashby_provider = (
            ashby_provider
        )

        self.job_filter = (
            job_filter
        )


    @classmethod
    def create(cls):

        return cls(

            greenhouse_provider=(
                ATSFactory.greenhouse()
            ),

            lever_provider=(
                ATSFactory.lever()
            ),

            ashby_provider=(
                ATSFactory.ashby()
            ),

            job_filter=ATSJobFilter(

                target_locations=[

                    "Mumbai",
                    "Bangalore",
                    "Bengaluru",
                    "Hyderabad",
                    "India",
                    "Remote",

                ],

                keywords=[

                    "data analyst",
                    "business analyst",
                    "analytics",
                    "business intelligence",
                    "product analyst",
                    "BI",

                ],
            ),
        )


    async def run(self):

        jobs = await self.fetch()

        jobs = AnalyticsJobFilter.filter(
            jobs
        )


        jobs = self.job_filter.filter(
            jobs
        )


        jobs = ATSDeduplicator.deduplicate(
            jobs
        )


        return jobs



    async def fetch(self):

        greenhouse_boards = (
            ATSRegistry.boards(
                "greenhouse"
            )
        )


        lever_boards = [

            board

            for board in ATSRegistry.boards(
                "lever"
            )

            if board.verified

        ]


        ashby_boards = [

            board

            for board in ATSRegistry.boards(
                "ashby"
            )

            if board.verified

        ]


        greenhouse_tasks = [

            self.greenhouse_provider.fetch_jobs(
                board
            )

            for board in greenhouse_boards

        ]


        lever_tasks = [

            self.lever_provider.fetch_jobs(
                board
            )

            for board in lever_boards

        ]


        ashby_tasks = [

            self.ashby_provider.fetch_jobs(
                board
            )

            for board in ashby_boards

        ]


        results = await asyncio.gather(
            *greenhouse_tasks,
            *lever_tasks,
            *ashby_tasks,
        )


        jobs = []


        for batch in results:

            jobs.extend(
                batch
            )


        return jobs