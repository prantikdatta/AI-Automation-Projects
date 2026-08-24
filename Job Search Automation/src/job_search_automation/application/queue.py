from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from job_search_automation.application.decision import (
    ApplicationDecision,
    ApplicationReadinessResult,
)
from job_search_automation.models.job import Job


class ApplicationQueueStatus(str, Enum):
    """
    Canonical operational status for an application queue item.

    Legacy names are retained as compatibility aliases for existing
    execution, mapper, sheet, and test code.
    """

    READY = "READY"
    READY_WITH_TAILORING = "READY_WITH_TAILORING"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"

    # Canonical/newer names retained for compatibility.
    QUEUED = "READY"
    TAILORING_REQUIRED = "READY_WITH_TAILORING"


# Backward-compatible public name used by the existing application tests
# and execution layer.
QueueStatus = ApplicationQueueStatus


class ApplicationQueueItem(BaseModel):
    """
    Canonical representation of a job entering the application workflow.

    The canonical application workflow fields are retained alongside the
    earlier queue contract so existing execution, Sheets, and test layers
    continue to work without forcing a second queue model.
    """

    job_id: str
    title: str
    company: str
    location: str
    job_url: str

    provider: str = ""
    searched_role: str = ""

    overall_score: float = 0.0
    selection_bucket: str = ""

    readiness_decision: ApplicationDecision = ApplicationDecision.READY
    queue_status: ApplicationQueueStatus = ApplicationQueueStatus.READY

    eligible: bool = False
    reason: str = ""

    missing_information: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)

    resume_tailoring_required: bool = False

    application_status: str = "NOT_STARTED"

    metadata: dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Backward-compatible queue contract
    # ------------------------------------------------------------------

    score: float = 0.0
    decision: ApplicationQueueStatus = ApplicationQueueStatus.READY
    status: ApplicationQueueStatus = ApplicationQueueStatus.READY

    source: str = ""
    resume_match_score: float | None = None

    created_at: str = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    notes: list[str] = Field(default_factory=list)

    application_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_and_canonical_fields(
        cls,
        values: Any,
    ) -> Any:
        """
        Normalize the older queue contract into the canonical model.

        Supported legacy fields:
            score
            decision
            status
            source
            notes
            application_url
            created_at
            resume_match_score
        """

        if not isinstance(values, dict):
            return values

        data = dict(values)

        # --------------------------------------------------------------
        # Score
        # --------------------------------------------------------------
        if "overall_score" not in data:
            data["overall_score"] = data.get(
                "score",
                0.0,
            )

        if "score" not in data:
            data["score"] = data.get(
                "overall_score",
                0.0,
            )

        # --------------------------------------------------------------
        # Provider / source
        # --------------------------------------------------------------
        if "provider" not in data:
            data["provider"] = data.get(
                "source",
                "",
            )

        if "source" not in data:
            data["source"] = data.get(
                "provider",
                "",
            )

        # --------------------------------------------------------------
        # Queue status
        # --------------------------------------------------------------
        legacy_status = data.get("status")
        legacy_decision = data.get("decision")
        canonical_status = data.get("queue_status")

        status_value = (
            legacy_status
            if legacy_status is not None
            else legacy_decision
            if legacy_decision is not None
            else canonical_status
        )

        normalized_status = cls._normalize_status(
            status_value
        )

        if normalized_status is not None:
            data["queue_status"] = normalized_status
            data["status"] = normalized_status
            data["decision"] = normalized_status

        # --------------------------------------------------------------
        # Readiness decision
        # --------------------------------------------------------------
        if "readiness_decision" not in data:
            data["readiness_decision"] = (
                cls._decision_from_status(
                    normalized_status
                )
            )

        # --------------------------------------------------------------
        # Resume tailoring
        # --------------------------------------------------------------
        if "resume_tailoring_required" not in data:
            data["resume_tailoring_required"] = (
                normalized_status
                == ApplicationQueueStatus.READY_WITH_TAILORING
            )

        # --------------------------------------------------------------
        # Notes
        # --------------------------------------------------------------
        if "notes" not in data:
            data["notes"] = list(
                data.get(
                    "recommended_actions",
                    [],
                )
                or []
            )

        if "recommended_actions" not in data:
            data["recommended_actions"] = list(
                data.get(
                    "notes",
                    [],
                )
                or []
            )

        # --------------------------------------------------------------
        # Selection bucket
        # --------------------------------------------------------------
        if "selection_bucket" not in data:
            data["selection_bucket"] = str(
                data.get(
                    "final_selection_bucket",
                    "",
                )
                or ""
            )

        # --------------------------------------------------------------
        # Eligibility
        # --------------------------------------------------------------
        if "eligible" not in data:
            data["eligible"] = (
                normalized_status
                in {
                    ApplicationQueueStatus.READY,
                    ApplicationQueueStatus.READY_WITH_TAILORING,
                }
            )

        # --------------------------------------------------------------
        # Created timestamp
        # --------------------------------------------------------------
        if not data.get("created_at"):
            data["created_at"] = datetime.now(
                timezone.utc
            ).isoformat()

        return data

    @staticmethod
    def _normalize_status(
        value: Any,
    ) -> ApplicationQueueStatus | None:
        if value is None:
            return None

        if isinstance(
            value,
            ApplicationQueueStatus,
        ):
            return value

        raw = str(value).strip().upper()

        aliases = {
            "QUEUED": ApplicationQueueStatus.READY,
            "READY": ApplicationQueueStatus.READY,
            "TAILORING_REQUIRED": (
                ApplicationQueueStatus.READY_WITH_TAILORING
            ),
            "READY_WITH_TAILORING": (
                ApplicationQueueStatus.READY_WITH_TAILORING
            ),
            "MANUAL_REVIEW": (
                ApplicationQueueStatus.MANUAL_REVIEW
            ),
            "REJECTED": ApplicationQueueStatus.REJECTED,
        }

        return aliases.get(raw)

    @staticmethod
    def _decision_from_status(
        status: ApplicationQueueStatus | None,
    ) -> ApplicationDecision:
        if status == ApplicationQueueStatus.READY:
            return ApplicationDecision.READY

        if status == ApplicationQueueStatus.READY_WITH_TAILORING:
            return ApplicationDecision.READY_WITH_TAILORING

        if status == ApplicationQueueStatus.MANUAL_REVIEW:
            return ApplicationDecision.MANUAL_REVIEW

        if status == ApplicationQueueStatus.REJECTED:
            return ApplicationDecision.REJECTED

        return ApplicationDecision.READY


class ApplicationQueueEngine:
    """
    Converts application-readiness decisions into application-queue items.

    This layer does NOT:
        - search providers
        - score jobs
        - call Gemini
        - modify resumes
        - generate cover letters
        - submit applications
        - write to Google Sheets

    It only determines the operational queue state.
    """

    def build(
        self,
        job: Job,
        readiness: ApplicationReadinessResult,
    ) -> ApplicationQueueItem:
        job_id = self._job_id(job)

        decision = readiness.decision

        if decision == ApplicationDecision.READY:
            queue_status = ApplicationQueueStatus.READY
            tailoring_required = False

        elif decision == ApplicationDecision.READY_WITH_TAILORING:
            queue_status = (
                ApplicationQueueStatus.READY_WITH_TAILORING
            )
            tailoring_required = True

        elif decision == ApplicationDecision.MANUAL_REVIEW:
            queue_status = ApplicationQueueStatus.MANUAL_REVIEW
            tailoring_required = False

        else:
            queue_status = ApplicationQueueStatus.REJECTED
            tailoring_required = False

        score = self._score(job)

        provider = self._text(
            getattr(
                job,
                "provider",
                "",
            )
        )

        searched_role = self._text(
            getattr(
                job,
                "searched_role",
                "",
            )
        )

        selection_bucket = self._text(
            getattr(
                job,
                "final_selection_bucket",
                "",
            )
        )

        recommended_actions = list(
            getattr(
                readiness,
                "recommended_actions",
                [],
            )
            or []
        )

        return ApplicationQueueItem(
            job_id=job_id,
            title=self._text(
                getattr(
                    job,
                    "title",
                    "",
                )
            ),
            company=self._text(
                getattr(
                    job,
                    "company",
                    "",
                )
            ),
            location=self._text(
                getattr(
                    job,
                    "location",
                    "",
                )
            ),
            job_url=self._text(
                getattr(
                    job,
                    "job_url",
                    "",
                )
            ),
            provider=provider,
            source=provider,
            searched_role=searched_role,
            overall_score=score,
            score=score,
            selection_bucket=selection_bucket,
            readiness_decision=decision,
            queue_status=queue_status,
            decision=queue_status,
            status=queue_status,
            eligible=bool(
                readiness.eligible
            ),
            reason=self._text(
                readiness.reason
            ),
            missing_information=list(
                getattr(
                    readiness,
                    "missing_information",
                    [],
                )
                or []
            ),
            checks=list(
                getattr(
                    readiness,
                    "checks",
                    [],
                )
                or []
            ),
            recommended_actions=recommended_actions,
            notes=recommended_actions,
            resume_tailoring_required=tailoring_required,
            resume_match_score=self._resume_match_score(job),
            application_url=getattr(
                job,
                "application_url",
                None,
            ),
            metadata={
                "final_selection_eligible": bool(
                    getattr(
                        job,
                        "final_selection_eligible",
                        False,
                    )
                ),
                "final_selection_bucket": selection_bucket,
            },
        )

    @staticmethod
    def _job_id(
        job: Job,
    ) -> str:
        """
        Resolve a stable job identifier without imposing a new
        requirement on the existing Job model.
        """

        for field in (
            "id",
            "job_id",
        ):
            value = getattr(
                job,
                field,
                None,
            )

            if value is not None and str(value).strip():
                return str(value).strip()

        job_url = getattr(
            job,
            "job_url",
            None,
        )

        if job_url is not None and str(job_url).strip():
            return str(job_url).strip()

        return (
            f"{str(getattr(job, 'company', '')).strip()}:"
            f"{str(getattr(job, 'title', '')).strip()}"
        )

    @staticmethod
    def _score(
        job: Job,
    ) -> float:
        value = getattr(
            job,
            "overall_score",
            0,
        )

        try:
            return float(value or 0)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _resume_match_score(
        job: Job,
    ) -> float | None:
        value = getattr(
            job,
            "resume_match_score",
            None,
        )

        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()