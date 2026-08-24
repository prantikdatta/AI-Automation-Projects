from __future__ import annotations

from typing import TypedDict

from job_search_automation.config.role_taxonomy import ROLE_TAXONOMY


class SearchBucket(TypedDict):
    priority: int
    name: str
    roles: list[str]
    target_jobs: int


SEARCH_BUCKETS: list[SearchBucket] = [
    {
        "priority": 1,
        "name": "Core Analytics",
        "roles": ROLE_TAXONOMY["CORE_ANALYTICS"],
        "target_jobs": 60,
    },
    {
        "priority": 1,
        "name": "Business Analytics",
        "roles": ROLE_TAXONOMY["BUSINESS_ANALYTICS"],
        "target_jobs": 50,
    },
    {
        "priority": 2,
        "name": "Product Analytics",
        "roles": ROLE_TAXONOMY["PRODUCT_ANALYTICS"],
        "target_jobs": 45,
    },
    {
        "priority": 2,
        "name": "FinTech Analytics",
        "roles": ROLE_TAXONOMY["FINTECH_ANALYTICS"],
        "target_jobs": 40,
    },
    {
        "priority": 3,
        "name": "Program Management",
        "roles": ROLE_TAXONOMY["PROGRAM_MANAGEMENT"],
        "target_jobs": 30,
    },
]