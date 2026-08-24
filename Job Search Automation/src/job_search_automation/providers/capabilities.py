from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    """
    Describes what a provider can natively support.

    The search planner will use these capabilities to decide
    which filters can be delegated to the provider and which
    require local post-processing.
    """

    supports_location: bool = False

    supports_remote: bool = False

    supports_salary: bool = False

    supports_company_filter: bool = False

    supports_posted_date: bool = False

    supports_multiple_roles: bool = False

    supports_pagination: bool = True

    supports_job_details: bool = False

    requires_local_filtering: bool = False

    is_ats_provider: bool = False