from __future__ import annotations

from job_search_automation.ats.base import (
    BaseATSProvider,
)

from job_search_automation.ats.board import (
    ATSBoard,
)

from job_search_automation.ats.ashby.client import (
    AshbyClient,
)

from job_search_automation.ats.ashby.adapter import (
    AshbyAdapter,
)


class AshbyProvider(
    BaseATSProvider
):
    """
    Ashby ATS implementation.
    """


    def __init__(
        self,
        client: AshbyClient,
    ):

        self.client = client



    async def fetch_jobs(
        self,
        board: ATSBoard,
    ):


        raw_jobs = await self.client.get_jobs(
            board.board
        )


        return [

            AshbyAdapter.normalize(
                job,
                board.company,
            )

            for job in raw_jobs

        ]