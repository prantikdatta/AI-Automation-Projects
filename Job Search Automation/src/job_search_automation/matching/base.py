from __future__ import annotations

from abc import ABC, abstractmethod

from job_search_automation.models.job import Job
from job_search_automation.matching.models import MatchResult


class BaseMatcher(ABC):
    """
    Base interface for all matching engines.
    """


    @abstractmethod
    async def match(
        self,
        job: Job,
    ) -> MatchResult:
        ...