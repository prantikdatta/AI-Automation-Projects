from __future__ import annotations

from job_search_automation.normalizers.adzuna import AdzunaNormalizer
from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.jooble import JoobleNormalizer
from job_search_automation.normalizers.rapidapi import RapidAPINormalizer
from job_search_automation.normalizers.remotive import RemotiveNormalizer


class NormalizerFactory:
    """
    Returns the correct normalizer for each provider.

    Provider
        ↓
    Factory
        ↓
    Correct Normalizer
    """

    _NORMALIZERS: dict[str, type[BaseNormalizer]] = {
        "Remotive": RemotiveNormalizer,
        "RapidAPI": RapidAPINormalizer,
        "Adzuna": AdzunaNormalizer,
        "Jooble": JoobleNormalizer,
    }

    @classmethod
    def get(
        cls,
        provider_name: str,
    ) -> BaseNormalizer:
        normalizer = cls._NORMALIZERS.get(provider_name)

        if normalizer is None:
            raise ValueError(
                f"No normalizer registered for '{provider_name}'."
            )

        return normalizer()