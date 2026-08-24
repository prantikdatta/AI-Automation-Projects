from __future__ import annotations

from job_search_automation.ats.base import (
    BaseATSProvider,
)

from job_search_automation.ats.board import (
    ATSBoard,
)

from job_search_automation.ats.lever.client import (
    LeverClient,
)

from job_search_automation.ats.lever.adapter import (
    LeverAdapter,
)


class LeverProvider(
    BaseATSProvider
):
    """
    Lever ATS implementation.
    """


    def __init__(
        self,
        client: LeverClient,
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

            LeverAdapter.normalize(
                job,
                board.company,
            )

            for job in raw_jobs

        ]