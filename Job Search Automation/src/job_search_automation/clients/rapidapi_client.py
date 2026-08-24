from __future__ import annotations

from typing import Any, Dict

import httpx

from job_search_automation.config import settings
from job_search_automation.services import HttpClient


class RapidAPIClient:
    """
    Client responsible for communicating with the JSearch RapidAPI.

    Responsibilities:
        - Build JSearch search requests
        - Convert requested job limits into JSearch page counts
        - Apply date-posted and remote filters
        - Execute HTTP requests through the shared HttpClient
        - Gracefully handle provider rate limits
        - Return the raw JSearch response

    This client does NOT:
        - normalize jobs
        - deduplicate jobs
        - apply eligibility rules
        - score jobs
        - rank jobs
    """

    SEARCH_ENDPOINT = "/search-v2"

    # JSearch generally returns approximately 10 jobs per page.
    DEFAULT_JOBS_PER_PAGE = 10

    # Prevent accidentally requesting an excessive number of pages.
    MAX_PAGES = 10

    def __init__(self) -> None:
        self.http = HttpClient()

        self.base_url = (
            settings.RAPIDAPI_BASE_URL.rstrip("/")
        )

        self.headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": settings.RAPIDAPI_HOST,
            "Content-Type": "application/json",
        }

    # ==========================================================
    # DATE FILTER
    # ==========================================================

    @staticmethod
    def _map_posted_days(
        days: int | None,
    ) -> str:
        """
        Convert application-level freshness requirements
        into JSearch date_posted values.
        """

        if days is None:
            return "all"

        if days <= 1:
            return "today"

        if days <= 3:
            return "3days"

        if days <= 7:
            return "week"

        if days <= 30:
            return "month"

        return "all"

    # ==========================================================
    # PAGE CALCULATION
    # ==========================================================

    @classmethod
    def _calculate_num_pages(
        cls,
        limit: int,
    ) -> int:
        """
        Convert requested job count into JSearch pages.

        Examples:

            10 jobs  -> 1 page
            25 jobs  -> 3 pages
            50 jobs  -> 5 pages
            100 jobs -> 10 pages

        The provider is intentionally capped at MAX_PAGES.
        """

        if limit <= 0:
            return 1

        return max(
            1,
            min(
                cls.MAX_PAGES,
                (
                    limit
                    + cls.DEFAULT_JOBS_PER_PAGE
                    - 1
                )
                // cls.DEFAULT_JOBS_PER_PAGE,
            ),
        )

    # ==========================================================
    # SEARCH
    # ==========================================================

    def search_jobs(
        self,
        query: str,
        *,
        limit: int = 100,
        country: str = "in",
        posted_within_days: int = 30,
        remote_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Search JSearch using the requested parameters.

        Parameters
        ----------
        query:
            Natural-language job search query.

        limit:
            Maximum number of jobs requested.

        country:
            JSearch country code.

        posted_within_days:
            Number of days used for JSearch date filtering.

        remote_only:
            Restrict results to remote jobs.

        Returns
        -------
        Dict[str, Any]
            Raw JSearch response.

        Rate-limit behaviour
        --------------------
        HTTP 429 is treated as a provider failure.

        The method returns:

            {
                "data": [],
                "provider": "rapidapi",
                "rate_limited": True,
                "status_code": 429,
            }

        instead of crashing the entire search pipeline.
        """

        num_pages = self._calculate_num_pages(
            limit,
        )

        params: Dict[str, Any] = {
            "query": query,
            "page": 1,
            "num_pages": num_pages,
            "country": country,
            "date_posted": self._map_posted_days(
                posted_within_days,
            ),
        }

        if remote_only:
            params["work_from_home"] = "true"

        url = (
            f"{self.base_url}"
            f"{self.SEARCH_ENDPOINT}"
        )

        # ======================================================
        # REQUEST LOGGING
        # ======================================================

        print("\n" + "=" * 80)
        print("RAPIDAPI REQUEST")
        print("=" * 80)
        print(f"URL        : {url}")
        print("Headers    :")

        print(
            "  X-RapidAPI-Key  : "
            f"{self._masked_api_key()}"
        )

        print(
            "  X-RapidAPI-Host : "
            f"{settings.RAPIDAPI_HOST}"
        )

        print(f"Parameters : {params}")

        print(
            f"Requested  : {limit} jobs "
            f"across {num_pages} page(s)"
        )

        print("=" * 80 + "\n")

        # ======================================================
        # HTTP REQUEST
        # ======================================================

        try:
            response = self.http.get(
                url=url,
                headers=self.headers,
                params=params,
            )

        except httpx.HTTPStatusError as exc:
            status_code = (
                exc.response.status_code
            )

            # --------------------------------------------------
            # RATE LIMIT
            # --------------------------------------------------

            if status_code == 429:
                print("\n" + "=" * 80)
                print("RAPIDAPI RATE LIMIT")
                print("=" * 80)
                print(
                    "RapidAPI/JSearch returned HTTP 429."
                )
                print(
                    "RapidAPI results will be skipped "
                    "for this search."
                )
                print(
                    "Other providers can continue normally."
                )
                print("=" * 80 + "\n")

                return {
                    "data": [],
                    "provider": "rapidapi",
                    "rate_limited": True,
                    "status_code": 429,
                    "error": (
                        "RapidAPI rate limit exceeded."
                    ),
                }

            # --------------------------------------------------
            # OTHER HTTP ERRORS
            # --------------------------------------------------

            print("\n" + "=" * 80)
            print("RAPIDAPI HTTP ERROR")
            print("=" * 80)
            print(
                f"Status Code : {status_code}"
            )
            print(
                f"URL         : {url}"
            )
            print("=" * 80 + "\n")

            return {
                "data": [],
                "provider": "rapidapi",
                "rate_limited": False,
                "status_code": status_code,
                "error": str(exc),
            }

        except Exception as exc:
            # --------------------------------------------------
            # UNEXPECTED PROVIDER ERROR
            # --------------------------------------------------

            print("\n" + "=" * 80)
            print("RAPIDAPI CLIENT ERROR")
            print("=" * 80)
            print(
                f"Error : {exc}"
            )
            print(
                "RapidAPI results will be skipped."
            )
            print("=" * 80 + "\n")

            return {
                "data": [],
                "provider": "rapidapi",
                "rate_limited": False,
                "status_code": None,
                "error": str(exc),
            }

        # ======================================================
        # RESPONSE
        # ======================================================

        jobs = response.get(
            "data",
            [],
        )

        print("\n" + "=" * 100)
        print("RAPIDAPI RESPONSE SUMMARY")
        print("=" * 100)
        print(
            f"Jobs Returned : {len(jobs)}"
        )
        print(
            f"Pages Used    : {num_pages}"
        )
        print(
            f"Requested     : {limit}"
        )
        print("=" * 100)

        return response

    # ==========================================================
    # API KEY MASKING
    # ==========================================================

    @staticmethod
    def _mask_value(
        value: str | None,
        visible_chars: int = 4,
    ) -> str:
        """
        Safely mask secrets in logs.
        """

        if not value:
            return "NOT_SET"

        if len(value) <= visible_chars:
            return "*" * len(value)

        return (
            value[:visible_chars]
            + "*" * 8
        )

    @classmethod
    def _masked_api_key(
        cls,
    ) -> str:
        """
        Return a masked RapidAPI key for logging.
        """

        return cls._mask_value(
            settings.RAPIDAPI_KEY,
            visible_chars=4,
        )