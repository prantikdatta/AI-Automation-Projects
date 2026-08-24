from __future__ import annotations

from typing import Any

import httpx

from job_search_automation.config import settings
from job_search_automation.services import HttpClient
from job_search_automation.services import logger


class ApifyClient:
    """
    Thin HTTP client for the Apify Actor API.

    The current Actor is:
        thirdwatch/linkedin-jobs-scraper

    Responsibilities
    ----------------
    - Execute one Apify Actor request.
    - Return raw dataset items.
    - Keep provider-specific API details isolated.
    - Gracefully handle Apify rate limits / quota exhaustion.
    - Suppress repeated Apify calls after quota exhaustion during
      the lifetime of the current Python process.

    This client does NOT:
    - normalize jobs
    - deduplicate jobs
    - rank jobs
    - perform resume matching
    - perform final selection
    """

    BASE_URL = "https://api.apify.com/v2"

    # Process-local circuit breaker.
    _quota_exhausted = False

    def __init__(self) -> None:
        self.http = HttpClient()

    # ==========================================================
    # QUOTA STATE
    # ==========================================================

    @classmethod
    def quota_exhausted(cls) -> bool:
        """
        Return whether Apify has already reported quota/rate-limit
        exhaustion during the current Python process.
        """

        return cls._quota_exhausted

    @classmethod
    def _mark_quota_exhausted(
        cls,
        reason: str,
    ) -> None:
        """
        Mark Apify unavailable for the remainder of the current
        Python process.
        """

        cls._quota_exhausted = True

        logger.warning(
            "APIFY DISABLED FOR CURRENT RUNTIME -> %s",
            reason,
        )

    # ==========================================================
    # ERROR CLASSIFICATION
    # ==========================================================

    @staticmethod
    def _response_text(
        response: httpx.Response,
    ) -> str:
        """
        Safely extract a lowercase response body for classification.
        """

        try:
            return response.text.lower()
        except Exception:
            return ""

    @classmethod
    def _is_quota_exhausted_response(
        cls,
        response: httpx.Response,
    ) -> bool:
        """
        Determine whether an Apify response indicates quota,
        usage, billing, or rate-limit exhaustion.

        429:
            always treated as temporarily unavailable.

        402:
            treated as an Apify usage/billing limit.

        403:
            treated as quota exhaustion only when the response
            explicitly contains quota/usage/billing terminology.
        """

        status_code = response.status_code

        if status_code == 429:
            return True

        if status_code == 402:
            return True

        if status_code != 403:
            return False

        body = cls._response_text(response)

        quota_terms = (
            "quota",
            "usage limit",
            "usage-limit",
            "monthly limit",
            "monthly quota",
            "rate limit",
            "rate-limit",
            "billing limit",
            "spending limit",
            "exceeded",
            "limit reached",
        )

        return any(
            term in body
            for term in quota_terms
        )

    # ==========================================================
    # MOCK / PLACEHOLDER DETECTION
    # ==========================================================

    @staticmethod
    def _is_mock_item(
        item: dict[str, Any],
    ) -> bool:
        """
        Return True when an Apify dataset item explicitly identifies
        itself as mock/sample data.

        Mock records must never enter the production pipeline.
        """

        if item.get("_mock") is True:
            return True

        notice = item.get("_notice")

        if isinstance(notice, str):
            notice_lower = notice.lower()

            mock_terms = (
                "mock",
                "sample data",
                "sample record",
                "not real",
                "placeholder",
                "synthetic",
                "upgrade at https://apify.com/pricing",
            )

            if any(
                term in notice_lower
                for term in mock_terms
            ):
                return True

        return False

    @classmethod
    def _contains_mock_items(
        cls,
        items: list[dict[str, Any]],
    ) -> bool:
        """
        Return True when any returned Apify item is mock/sample data.
        """

        return any(
            cls._is_mock_item(item)
            for item in items
        )

    # ==========================================================
    # SEARCH
    # ==========================================================

    def search_jobs(
        self,
        query: str,
        location: str = "India",
        max_items: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Execute a LinkedIn Jobs Apify Actor search.

        Actor:
            thirdwatch/linkedin-jobs-scraper

        Returns
        -------
        list[dict[str, Any]]
            Raw dataset items.

        Failure behaviour
        -----------------
        Rate-limit / quota exhaustion:
            Returns [] and disables further Apify calls for the
            current Python process.

        Other HTTP/API failures:
            Returns [] and allows a future call to retry.
        """

        # ------------------------------------------------------
        # PROCESS-LOCAL QUOTA CIRCUIT BREAKER
        # ------------------------------------------------------

        if self.quota_exhausted():
            logger.warning(
                "APIFY SKIPPED -> quota/rate limit already "
                "exhausted during this runtime.",
            )

            return []

        search_query = (
            f"{query} {location}"
        ).strip()

        logger.info(
            "APIFY REQUEST -> %s",
            search_query,
        )

        actor_id = settings.APIFY_ACTOR_ID.replace(
            "/",
            "~",
        )

        url = (
            f"{self.BASE_URL}/acts/"
            f"{actor_id}/run-sync-get-dataset-items"
        )

        # ------------------------------------------------------
        # THIRDWATCH LINKEDIN JOBS SCRAPER INPUT
        # ------------------------------------------------------

        payload = {
            "queries": [
                query.strip(),
            ],
            "location": location.strip(),
            "country": "india",
            "maxResultsPerQuery": max(
                1,
                max_items,
            ),
            "maxPages": 1,
            "scrapeMode": "standard",
            "datePosted": "pastWeek",
            "proxyConfiguration": {
                "useApifyProxy": True,
                "apifyProxyGroups": [
                    "RESIDENTIAL",
                ],
            },
        }

        headers = {
            "Authorization": (
                f"Bearer {settings.APIFY_API_TOKEN}"
            ),
            "Content-Type": "application/json",
        }

        logger.info(
            "APIFY ACTOR -> %s",
            actor_id,
        )

        # ------------------------------------------------------
        # HTTP REQUEST
        # ------------------------------------------------------

        try:
            response = self.http.post_once(
                url=url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            # --------------------------------------------------
            # QUOTA / RATE LIMIT
            # --------------------------------------------------

            if self._is_quota_exhausted_response(
                exc.response,
            ):
                self._mark_quota_exhausted(
                    (
                        "Apify returned HTTP "
                        f"{status_code} indicating "
                        "quota/rate-limit exhaustion."
                    ),
                )

                logger.warning(
                    "APIFY RESULTS -> 0 jobs. "
                    "Other providers will continue normally.",
                )

                return []

            # --------------------------------------------------
            # OTHER HTTP ERRORS
            # --------------------------------------------------

            logger.error(
                "APIFY HTTP ERROR -> status=%s url=%s",
                status_code,
                url,
            )

            logger.warning(
                "Apify results will be skipped. "
                "Other providers will continue normally.",
            )

            return []

        except Exception as exc:
            # --------------------------------------------------
            # UNEXPECTED PROVIDER ERROR
            # --------------------------------------------------

            logger.exception(
                "APIFY CLIENT ERROR -> %s",
                exc,
            )

            logger.warning(
                "Apify results will be skipped. "
                "Other providers will continue normally.",
            )

            return []

        # ======================================================
        # RESPONSE
        # ======================================================

        if isinstance(response, list):
            logger.info(
                "APIFY RESPONSE -> %s jobs",
                len(response),
            )

            if self._contains_mock_items(response):
                logger.error(
                    "APIFY MOCK DATA DETECTED -> "
                    "Actor returned sample/mock records.",
                )

                logger.error(
                    "APIFY RESULTS REJECTED -> "
                    "Mock jobs must never enter the production pipeline.",
                )

                return []

            return response

        if isinstance(response, dict):
            data = response.get(
                "data",
                [],
            )

            if isinstance(data, list):
                logger.info(
                    "APIFY RESPONSE -> %s jobs",
                    len(data),
                )

                if self._contains_mock_items(data):
                    logger.error(
                        "APIFY MOCK DATA DETECTED -> "
                        "Actor returned sample/mock records.",
                    )

                    logger.error(
                        "APIFY RESULTS REJECTED -> "
                        "Mock jobs must never enter the production pipeline.",
                    )

                    return []

                return data

        logger.warning(
            "Apify returned an unexpected response shape: %s",
            type(response).__name__,
        )

        return []