from __future__ import annotations

from abc import ABC, abstractmethod

from job_search_automation.ats.board import ATSBoard
from job_search_automation.models.job import Job


class BaseATSProvider(ABC):
    """
    Abstract contract for all ATS providers.
    """

    @abstractmethod
    async def fetch_jobs(
        self,
        board: ATSBoard,
    ) -> list[Job]:
        """
        Fetch jobs from an ATS board.
        """
        pass