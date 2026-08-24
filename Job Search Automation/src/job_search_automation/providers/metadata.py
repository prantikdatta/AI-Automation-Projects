from __future__ import annotations

from dataclasses import dataclass

from job_search_automation.providers.capabilities import (
    ProviderCapabilities,
)


@dataclass(frozen=True)
class ProviderMetadata:
    """
    Immutable provider description.

    This is used by the registry, planner and monitoring layer.
    """

    name: str

    version: str

    provider_type: str

    capabilities: ProviderCapabilities

    enabled: bool = True