from __future__ import annotations

from typing import Any

import httpx


class LeverClient:

    BASE_URL = (
        "https://api.lever.co/v0/postings"
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

        response = await self.client.get(
            f"{self.BASE_URL}/{board}",
            params={
                "mode": "json"
            },
        )


        if response.status_code == 404:
            return []


        response.raise_for_status()


        return response.json()


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