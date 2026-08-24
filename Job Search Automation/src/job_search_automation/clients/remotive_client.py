from __future__ import annotations

from typing import Any, Dict

from job_search_automation.services import HttpClient


class RemotiveClient:
    """
    Thin HTTP client for Remotive Jobs API.
    """

    BASE_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self) -> None:
        self.http = HttpClient()

    def search_jobs(
        self,
        search: str,
    ) -> Dict[str, Any]:

        return self.http.get(
            url=self.BASE_URL,
            params={
                "search": search,
            },
        )