from __future__ import annotations

from typing import Any

import httpx


class GreenhouseClient:
    """
    Client for the Greenhouse public job board API.
    """

    BASE_URL = (
        "https://boards-api.greenhouse.io/v1/boards"
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
            f"{self.BASE_URL}/{board}/jobs"
        )

        response = await self.client.get(
            url
        )

        if response.status_code == 404:

            return []

        response.raise_for_status()

        payload = response.json()

        #
        # Greenhouse API returns:
        #
        # {
        #     "jobs": [...]
        # }
        #

        return payload.get(
            "jobs",
            [],
        )

    async def close(
        self,
    ):

        await self.client.aclose()