from __future__ import annotations

from typing import Any

from job_search_automation.application.decision import (
    ApplicationDecision,
    ApplicationReadinessResult,
)
from job_search_automation.models.job import Job


class ApplicationReadinessEngine:
    """
    Determines whether a selected job is ready to enter
    the application queue.

    This layer does NOT:
        - search providers
        - score jobs
        - call Gemini
        - modify resume content
        - submit applications

    It only evaluates application readiness.
    """

    # Final Selection and Application Readiness are intentionally
    # separate gates.
    #
    # A job can survive Final Selection but still be unsuitable
    # for immediate application.
    MIN_READY_SCORE = 70.0
    MIN_TAILOR_SCORE = 60.0

    def evaluate(
        self,
        job: Job,
    ) -> ApplicationReadinessResult:
        checks: list[str] = []
        missing: list[str] = []
        actions: list[str] = []

        if not self._selected(job):
            return ApplicationReadinessResult(
                decision=ApplicationDecision.REJECTED,
                eligible=False,
                reason="Job was not selected by FinalSelectionEngine.",
                checks=[],
            )

        self._check_required_fields(
            job,
            missing,
        )

        if missing:
            return ApplicationReadinessResult(
                decision=ApplicationDecision.MANUAL_REVIEW,
                eligible=False,
                reason="Required job information is missing.",
                checks=checks,
                missing_information=missing,
                recommended_actions=[
                    "Verify the original job posting.",
                    "Complete missing job metadata.",
                ],
            )

        score = self._score(job)
        bucket = self._bucket(job)

        checks.append(
            f"Overall score={score:.2f}"
        )

        checks.append(
            f"Selection bucket={bucket}"
        )

        checks.append(
            f"Location={job.location}"
        )

        checks.append(
            f"Job URL present={bool(str(job.job_url).strip())}"
        )

        checks.append(
            f"Description present={bool(str(job.description).strip())}"
        )

        # ------------------------------------------------------------------
        # Immediate application readiness
        # ------------------------------------------------------------------
        if score >= self.MIN_READY_SCORE:
            return ApplicationReadinessResult(
                decision=ApplicationDecision.READY,
                eligible=True,
                reason=(
                    "Selected job satisfies the application-readiness "
                    "threshold."
                ),
                checks=checks,
                recommended_actions=actions,
            )

        # ------------------------------------------------------------------
        # Resume tailoring required
        # ------------------------------------------------------------------
        if score >= self.MIN_TAILOR_SCORE:
            actions.extend(
                [
                    "Tailor resume to the job description.",
                    "Review matched and missing skills.",
                    "Verify role and location alignment before applying.",
                ]
            )

            return ApplicationReadinessResult(
                decision=ApplicationDecision.READY_WITH_TAILORING,
                eligible=True,
                reason=(
                    "Job is potentially suitable but requires resume "
                    "tailoring before application."
                ),
                checks=checks,
                recommended_actions=actions,
            )

        # ------------------------------------------------------------------
        # Weak candidate
        # ------------------------------------------------------------------
        return ApplicationReadinessResult(
            decision=ApplicationDecision.MANUAL_REVIEW,
            eligible=False,
            reason=(
                "Job survived Final Selection but does not satisfy "
                "the minimum application-readiness score."
            ),
            checks=checks,
            recommended_actions=[
                "Review role alignment manually.",
                "Confirm resume alignment.",
                "Do not submit automatically.",
            ],
        )

    @staticmethod
    def _selected(
        job: Job,
    ) -> bool:
        return bool(
            getattr(
                job,
                "final_selection_eligible",
                False,
            )
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
    def _bucket(
        job: Job,
    ) -> str:
        return str(
            getattr(
                job,
                "final_selection_bucket",
                "",
            )
            or ""
        )

    @staticmethod
    def _check_required_fields(
        job: Job,
        missing: list[str],
    ) -> None:
        required_fields: tuple[
            tuple[str, Any],
            ...
        ] = (
            ("title", getattr(job, "title", None)),
            ("company", getattr(job, "company", None)),
            ("location", getattr(job, "location", None)),
            ("job_url", getattr(job, "job_url", None)),
            ("description", getattr(job, "description", None)),
        )

        for name, value in required_fields:
            if value is None:
                missing.append(name)
                continue

            if isinstance(value, str) and not value.strip():
                missing.append(name)