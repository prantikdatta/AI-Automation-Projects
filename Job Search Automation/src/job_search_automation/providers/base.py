from __future__ import annotations

from abc import ABC, abstractmethod

from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse


class BaseProvider(ABC):
    """
    Abstract base class for every job provider.

    Every provider must:
        • expose a provider name
        • accept a SearchRequest
        • return a canonical SearchResponse

    Providers DO NOT:
        • rank jobs
        • deduplicate jobs
        • export jobs
        • call Gemini
        • filter jobs

    They only translate an external API into our internal Job model.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable provider name.
        """
        ...

    @abstractmethod
    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Execute a provider search.

        Parameters
        ----------
        request
            Canonical search request.

        Returns
        -------
        SearchResponse
            Canonical response containing Job objects.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"