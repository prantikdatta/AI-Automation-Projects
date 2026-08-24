from __future__ import annotations

from abc import ABC
from typing import Any, Dict, Optional

from job_search_automation.services import HttpClient


class BaseClient(ABC):
    """
    Base class for every external API client.

    Responsibilities
    ----------------
    - Own the shared HttpClient
    - Store base_url
    - Store default headers
    - Provide reusable GET/POST wrappers

    Business logic belongs inside Providers.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:

        self.http = HttpClient()

        self.base_url = base_url.rstrip("/")

        self.headers = headers or {}

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return self.http.get(
            url=f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params,
        )

    def post(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return self.http.post(
            url=f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload,
        )

    def close(self) -> None:
        """
        Close shared HTTP session.
        """

        self.http.close()