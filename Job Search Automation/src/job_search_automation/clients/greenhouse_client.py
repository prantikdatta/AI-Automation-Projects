from __future__ import annotations

from job_search_automation.services import HttpClient
from job_search_automation.services import logger


class GreenhouseClient:
    """
    Greenhouse Job Board API client.

    Public API.
    No authentication required.
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self) -> None:

        self.http = HttpClient()

    def search_jobs(
        self,
        board: str,
    ) -> dict:

        logger.info(
            "GREENHOUSE REQUEST -> %s",
            board,
        )

        url = f"{self.BASE_URL}/{board}/jobs"

        return self.http.get(
            url=url,
        )