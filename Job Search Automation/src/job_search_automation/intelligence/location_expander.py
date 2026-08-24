from __future__ import annotations

from typing import List

from job_search_automation.config.search_strategy import (
    SEARCH_LOCATIONS,
)


class LocationExpander:
    """
    Expands a search request into prioritized
    location buckets.

    The pipeline should never hardcode locations.
    """

    @staticmethod
    def expand() -> List[str]:

        return SEARCH_LOCATIONS.copy()