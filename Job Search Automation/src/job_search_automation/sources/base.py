from __future__ import annotations

from abc import ABC, abstractmethod


class JobSource(
    ABC
):
    """
    Abstract interface for all job sources.
    """


    @abstractmethod
    async def fetch_jobs(
        self,
    ):

        pass