from __future__ import annotations

from typing import Any, Dict

from job_search_automation.config.settings import settings
from job_search_automation.services.http_client import HttpClient
from job_search_automation.services import logger


class AdzunaClient:
    """
    Low-level Adzuna API client.
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self) -> None:

        self.http = HttpClient()

    def search_jobs(
        self,
        query: str,
        page: int = 1,
        results_per_page: int = 50,
    ) -> Dict[str, Any]:

        url = (
            f"{self.BASE_URL}/in/search/{page}"
        )

        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_APP_KEY,
            "results_per_page": results_per_page,
            "what": query,
            "content-type": "application/json",
        }

        logger.info(
            "ADZUNA REQUEST -> %s",
            query,
        )

        return self.http.get(
            url=url,
            params=params,
        )