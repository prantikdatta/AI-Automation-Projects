from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class BaseNormalizer(ABC):
    """
    Base class for every provider normalizer.

    Provider Payload
            ↓
      normalize()
            ↓
      NormalizedJob

    Providers never create Job() directly.
    """

    provider_name: str

    @abstractmethod
    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:
        """
        Convert a provider payload into a NormalizedJob.
        """
        raise NotImplementedError