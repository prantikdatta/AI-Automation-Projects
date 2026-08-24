from __future__ import annotations

from job_search_automation.services import HttpClient
from job_search_automation.services import logger


class SmartRecruitersClient:
    """
    SmartRecruiters public Jobs API.
    """

    BASE_URL = "https://api.smartrecruiters.com/v1/companies"

    def __init__(self) -> None:

        self.http = HttpClient()

    def search_jobs(
        self,
        company: str,
    ) -> dict:

        logger.info(
            "SMARTRECRUITERS REQUEST -> %s",
            company,
        )

        url = f"{self.BASE_URL}/{company}/postings"

        return self.http.get(
            url=url,
        )