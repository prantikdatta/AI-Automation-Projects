from __future__ import annotations

from job_search_automation.config import settings
from job_search_automation.services import HttpClient
from job_search_automation.services import logger


class JoobleClient:
    """
    Thin HTTP wrapper around the Jooble API.

    Responsibilities
    ----------------
    • Execute one HTTP request
    • Return raw JSON
    • No pagination logic
    • No normalization
    """

    BASE_URL = "https://jooble.org/api"

    def __init__(self):

        self.http = HttpClient()

    def search_jobs(
        self,
        query: str,
        location: str = "",
    ) -> dict:

        logger.info(
            "JOOBLE REQUEST -> %s",
            query,
        )

        url = (
            f"{self.BASE_URL}/"
            f"{settings.JOOBLE_API_KEY}"
        )

        payload = {

            "keywords": query,

            "location": location,

        }

        return self.http.post(

            url=url,

            json=payload,

        )