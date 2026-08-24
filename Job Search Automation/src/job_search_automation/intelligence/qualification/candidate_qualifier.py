from __future__ import annotations

from dataclasses import dataclass

from job_search_automation.intelligence.qualification.location_qualifier import (
    LocationQualifier,
    LocationQualificationResult,
)
from job_search_automation.intelligence.qualification.role_qualifier import (
    RoleQualifier,
    RoleQualificationResult,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest


@dataclass(frozen=True)
class CandidateQualificationResult:
    """
    Combined qualification result.

    Qualification happens BEFORE scoring.

    A job must pass both:
        1. Role qualification
        2. Location qualification
    """

    qualified: bool

    role: RoleQualificationResult

    location: LocationQualificationResult

    reason: str


class CandidateQualifier:
    """
    Hard-gate qualification engine.

    Responsibilities
    ----------------
    • Determine whether the job belongs to the requested role family.
    • Determine whether the job is in an acceptable location.
    • Produce an auditable qualification decision.

    Responsibilities explicitly excluded
    ------------------------------------
    • Resume matching
    • Score calculation
    • Employer scoring
    • Freshness scoring
    • Ranking
    • Final application decision
    """

    def __init__(
        self,
        role_qualifier: RoleQualifier | None = None,
        location_qualifier: LocationQualifier | None = None,
    ) -> None:

        self.role_qualifier = (
            role_qualifier
            or RoleQualifier()
        )

        self.location_qualifier = (
            location_qualifier
            or LocationQualifier()
        )

    # ----------------------------------------------------------
    # Main qualification
    # ----------------------------------------------------------

    def qualify(
        self,
        job: Job,
        request: SearchRequest,
    ) -> CandidateQualificationResult:

        role_result = self.role_qualifier.qualify(
            title=job.title,
            requested_roles=request.roles,
        )

        location_result = self.location_qualifier.qualify(
            job_location=job.location,
            requested_locations=request.locations,
            remote_only=request.remote_only,
        )

        qualified = (
            role_result.qualified
            and location_result.qualified
        )

        if qualified:

            reason = (
                "Job passed role and location qualification."
            )

        elif not role_result.qualified:

            reason = (
                f"Rejected: {role_result.reason}"
            )

        else:

            reason = (
                f"Rejected: {location_result.reason}"
            )

        return CandidateQualificationResult(
            qualified=qualified,
            role=role_result,
            location=location_result,
            reason=reason,
        )