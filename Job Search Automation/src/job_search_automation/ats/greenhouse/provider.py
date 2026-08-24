from __future__ import annotations

import asyncio

from job_search_automation.ats.base import BaseATSProvider
from job_search_automation.ats.board import ATSBoard
from job_search_automation.ats.greenhouse.adapter import GreenhouseAdapter
from job_search_automation.ats.greenhouse.client import GreenhouseClient
from job_search_automation.ats.greenhouse.detail_client import (
    GreenhouseDetailClient,
)
from job_search_automation.models.job import Job


class GreenhouseProvider(BaseATSProvider):

    DETAIL_CONCURRENCY_LIMIT = 20

    def __init__(
        self,
        client: GreenhouseClient,
        detail_client: GreenhouseDetailClient,
    ):
        self.client = client
        self.detail_client = detail_client

    async def fetch_jobs(
        self,
        board: ATSBoard,
    ) -> list[Job]:

        listing = await self.client.get_jobs(
            board.board
        )

        #
        # Greenhouse returns either
        # {"jobs":[...]}
        # OR
        # [...]
        #

        if isinstance(listing, dict):
            listing = listing.get("jobs", [])

        if not listing:
            return []

        #
        # Limit concurrent detail requests
        # Prevent thousands of simultaneous API calls
        #

        semaphore = asyncio.Semaphore(
            self.DETAIL_CONCURRENCY_LIMIT
        )

        async def fetch_detail(job_id: int):
            async with semaphore:
                return await self.detail_client.get_job(
                    board=board.board,
                    job_id=job_id,
                )

        detail_tasks = [
            fetch_detail(
                job["id"]
            )
            for job in listing
        ]

        details = await asyncio.gather(
            *detail_tasks,
            return_exceptions=True,
        )

        jobs: list[Job] = []

        for summary, detail in zip(
            listing,
            details,
        ):

            #
            # Ignore failed detail requests
            #

            if isinstance(detail, Exception):
                detail = {}

            #
            # Detail should overwrite summary
            #

            merged = dict(summary)

            if isinstance(detail, dict):
                merged.update(detail)

            #
            # Fallback if detail endpoint
            # did not return description
            #

            if (
                not merged.get("content")
                and summary.get("content")
            ):
                merged["content"] = summary["content"]

            #
            # Debug
            #

            print("=" * 80)
            print("TITLE:", merged.get("title"))
            print("DETAIL SUCCESS:", bool(detail))
            print(
                "HAS CONTENT:",
                bool(merged.get("content"))
            )
            print(
                "CONTENT LENGTH:",
                len(merged.get("content", "")),
            )

            jobs.append(
                GreenhouseAdapter.normalize(
                    board=board,
                    raw=merged,
                )
            )

        return jobs

    async def close(self):

        await self.client.close()
        await self.detail_client.close()