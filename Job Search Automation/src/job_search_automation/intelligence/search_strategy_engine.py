from __future__ import annotations

from typing import Any

from job_search_automation.config.search_queries import SEARCH_BUCKETS
from job_search_automation.config.search_strategy import SEARCH_LOCATIONS


class SearchStrategyEngine:
    """
    Builds provider-independent search plans.

    Flow

    Role Taxonomy
            ↓
    Search Buckets
            ↓
    Search Locations
            ↓
    Search Plans
    """

    @staticmethod
    def build() -> list[dict[str, Any]]:
        plans: list[dict[str, Any]] = []

        for bucket in sorted(
            SEARCH_BUCKETS,
            key=lambda bucket: bucket["priority"],
        ):
            for location in SEARCH_LOCATIONS:
                plans.append(
                    {
                        "priority": bucket["priority"],
                        "bucket": bucket["name"],
                        "roles": list(bucket["roles"]),
                        "location": location,
                        "target_jobs": bucket["target_jobs"],
                    }
                )

        return plans