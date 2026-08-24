from __future__ import annotations

from threading import Lock
from typing import Dict, List

from job_search_automation.models.job import Job


class ProviderCache:
    """
    Thread-safe in-memory cache.

    Lifetime
    --------
    One SearchPipeline execution.

    Purpose
    -------
    Prevent ATS providers from downloading the
    same jobs repeatedly for every search query.

    Key
    ---
    provider_name

    Value
    -----
    List[Job]
    """

    _cache: Dict[str, List[Job]] = {}

    _lock = Lock()

    @classmethod
    def has(
        cls,
        provider: str,
    ) -> bool:

        with cls._lock:

            return provider in cls._cache

    @classmethod
    def get(
        cls,
        provider: str,
    ) -> List[Job]:

        with cls._lock:

            return cls._cache.get(
                provider,
                [],
            )

    @classmethod
    def set(
        cls,
        provider: str,
        jobs: List[Job],
    ) -> None:

        with cls._lock:

            cls._cache[provider] = jobs

    @classmethod
    def clear(
        cls,
    ) -> None:

        with cls._lock:

            cls._cache.clear()