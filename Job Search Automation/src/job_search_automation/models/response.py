from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from job_search_automation.models.job import Job


class SearchResponse(BaseModel):
    """
    Canonical response returned by every provider.

    Every provider MUST return this object.

    Provider
        ↓
    SearchResponse
        ↓
    Pipeline
    """

    provider: str

    jobs: List[Job] = Field(default_factory=list)

    total_found: int = 0

    total_returned: int = 0

    success: bool = True

    message: str = ""