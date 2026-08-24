from __future__ import annotations

import json as json_lib
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from job_search_automation.services.logger import logger


class HttpClient:
    """
    Shared HTTP client for all providers.

    Features
    --------
    - Connection pooling
    - Automatic retries for normal requests
    - Shared error handling
    - Shared logging
    - Supports GET and POST
    - Supports per-request timeout overrides
    - Supports non-retrying requests for long-running operations
    """

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
        )

    # ==========================================================
    # INTERNAL REQUEST
    # ==========================================================

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=10,
        ),
        reraise=True,
    )
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute a normal HTTP request with automatic retries.

        Used by regular providers.
        """

        return self._request_once(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=timeout,
        )

    def _request_once(
        self,
        *,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute exactly one HTTP request.

        No retry is performed here.

        This is important for long-running or non-idempotent operations
        where automatically repeating the request could trigger the
        remote operation multiple times.
        """

        logger.info(
            "HTTP %s -> %s",
            method,
            url,
        )

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": params,
            "json": json,
        }

        if timeout is not None:
            request_kwargs["timeout"] = timeout

        response = self.client.request(
            **request_kwargs,
        )

        logger.info(
            "HTTP Response <- %s (%s)",
            response.status_code,
            url,
        )

        # ------------------------------------------------------
        # Rate Limit
        # ------------------------------------------------------

        if response.status_code == 429:
            logger.warning(
                "HTTP 429 Rate Limit reached."
            )

            response.raise_for_status()

        # ------------------------------------------------------
        # HTTP Errors
        # ------------------------------------------------------

        if response.status_code >= 400:
            logger.error(
                "HTTP %s for %s",
                response.status_code,
                url,
            )

            response.raise_for_status()

        # ------------------------------------------------------
        # Empty Response
        # ------------------------------------------------------

        if not response.content:
            return {}

        data = response.json()

        # ======================================================
        # TEMP DEBUG : SmartRecruiters
        # ======================================================

        if "smartrecruiters" in url.lower():

            print("\n" + "=" * 120)
            print("SMARTRECRUITERS RAW RESPONSE")
            print("=" * 120)

            try:
                print(
                    json_lib.dumps(
                        data,
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            except Exception:
                print(data)

            print("=" * 120 + "\n")

        return data

    # ==========================================================
    # GET
    # ==========================================================

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:

        return self.request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            timeout=timeout,
        )

    # ==========================================================
    # POST
    # ==========================================================

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:

        return self.request(
            method="POST",
            url=url,
            headers=headers,
            json=json,
            timeout=timeout,
        )

    # ==========================================================
    # NON-RETRYING POST
    # ==========================================================

    def post_once(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute exactly one POST request without automatic retries.

        Intended for operations where repeating the POST can cause the
        remote service to execute the operation multiple times.
        """

        return self._request_once(
            method="POST",
            url=url,
            headers=headers,
            json=json,
            timeout=timeout,
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self) -> None:
        self.client.close()