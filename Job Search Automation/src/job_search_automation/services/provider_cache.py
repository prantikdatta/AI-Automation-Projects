from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from job_search_automation.models.job import Job
from job_search_automation.services import logger


class ProviderCache:
    """
    Simple in-memory cache for expensive providers.

    Cache is maintained separately for every provider.

    Example
    -------
    Greenhouse
        jobs...
        expires_at

    Ashby
        jobs...
        expires_at
    """

    _cache: Dict[str, tuple[list[Job], datetime]] = {}

    DEFAULT_TTL = timedelta(hours=6)

    @classmethod
    def get(
        cls,
        provider: str,
    ) -> list[Job] | None:

        item = cls._cache.get(provider)

        if item is None:
            return None

        jobs, expires_at = item

        if datetime.now(timezone.utc) >= expires_at:

            logger.info(
                "CACHE EXPIRED -> %s",
                provider,
            )

            del cls._cache[provider]

            return None

        logger.info(
            "CACHE HIT -> %s (%d jobs)",
            provider,
            len(jobs),
        )

        return jobs

    @classmethod
    def set(
        cls,
        provider: str,
        jobs: list[Job],
        ttl: timedelta | None = None,
    ) -> None:

        ttl = ttl or cls.DEFAULT_TTL

        cls._cache[provider] = (
            jobs,
            datetime.now(timezone.utc) + ttl,
        )

        logger.info(
            "CACHE STORE -> %s (%d jobs)",
            provider,
            len(jobs),
        )

    @classmethod
    def clear(
        cls,
    ) -> None:

        cls._cache.clear()

        logger.info(
            "Provider cache cleared."
        )