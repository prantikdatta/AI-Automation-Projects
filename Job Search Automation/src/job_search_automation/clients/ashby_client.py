from __future__ import annotations

from typing import Any

from job_search_automation.services import HttpClient
from job_search_automation.services import logger


class AshbyClient:
    """
    Public Ashby Job Posting API client.

    Docs:
    https://api.ashbyhq.com/posting-api/job-board/{JOB_BOARD_NAME}
    """

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

    def __init__(self) -> None:

        self.http = HttpClient()

    def search_jobs(
        self,
        company: str,
    ) -> dict[str, Any]:

        logger.info(
            "ASHBY REQUEST -> %s",
            company,
        )

        url = f"{self.BASE_URL}/{company}"

        params = {
            "includeCompensation": "true",
        }

        return self.http.get(
            url=url,
            params=params,
        )