from __future__ import annotations

from typing import Any

import httpx


class GreenhouseDetailClient:
    """
    Fetch complete Greenhouse job.
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1"

    def __init__(
        self,
        timeout: int = 20,
    ):

        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        )

    async def get_job(
        self,
        board: str,
        job_id: int,
    ) -> dict[str, Any]:

        url = (
            f"{self.BASE_URL}"
            f"/boards/{board}"
            f"/jobs/{job_id}"
        )

        print("=" * 100)
        print("DETAIL REQUEST")
        print(url)

        try:

            response = await self.client.get(url)

            print("STATUS :", response.status_code)
            print("HEADERS:", response.headers.get("content-type"))

            if response.status_code != 200:

                print("BODY:")
                print(response.text[:1000])

                return {}

            payload = response.json()

            print("SUCCESS")
            print(type(payload))
            print(payload.keys())

            return payload

        except Exception as exc:

            print("DETAIL EXCEPTION")
            print(type(exc))
            print(exc)

            return {}

    async def close(self):

        await self.client.aclose()