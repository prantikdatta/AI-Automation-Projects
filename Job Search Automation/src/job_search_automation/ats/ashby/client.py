from __future__ import annotations

from typing import Any

import httpx


class AshbyClient:
    """
    Client for Ashby public jobs API.
    """

    BASE_URL = (
        "https://jobs.ashbyhq.com/api/non-user-application"
    )


    def __init__(
        self,
        timeout: int = 20,
    ):

        self.client = httpx.AsyncClient(
            timeout=timeout
        )


    async def get_jobs(
        self,
        board: str,
    ) -> list[dict[str, Any]]:

        url = (
            f"{self.BASE_URL}/{board}"
        )


        response = await self.client.get(
            url
        )


        if response.status_code == 404:

            return []


        response.raise_for_status()


        data = response.json()


        return data.get(
            "jobs",
            []
        )


    async def validate_board(
        self,
        board: str,
    ) -> bool:

        jobs = await self.get_jobs(
            board
        )

        return len(jobs) > 0


    async def close(self):

        await self.client.aclose()