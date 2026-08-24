from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from job_search_automation.config.scoring_rules import (
    FRESHNESS_SCORE,
    SEARCH_LIMITS,
)
from job_search_automation.models.job import Job


@dataclass(frozen=True)
class FreshnessDecision:
    accepted: bool
    age_days: float | None
    score: float
    reason: str


class JobFreshnessEvaluator:
    """
    Evaluates whether a job falls within the configured
    freshness window.

    Jobs older than the configured maximum are rejected
    from downstream processing but are never deleted from
    the audit trail.
    """

    def __init__(
        self,
        max_days_old: int | None = None,
    ) -> None:
        self.max_days_old = (
            max_days_old
            if max_days_old is not None
            else SEARCH_LIMITS["max_days_old"]
        )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    def evaluate(
        self,
        posted_at: datetime | None,
        now: datetime | None = None,
    ) -> FreshnessDecision:
        if posted_at is None:
            return FreshnessDecision(
                accepted=False,
                age_days=None,
                score=0.0,
                reason="Posted date unavailable.",
            )

        current_time = (
            now
            if now is not None
            else datetime.now(UTC)
        )

        current_time = self._normalize_datetime(
            current_time
        )

        posted_at = self._normalize_datetime(
            posted_at
        )

        age_seconds = (
            current_time - posted_at
        ).total_seconds()

        age_days = max(
            0.0,
            age_seconds / 86400,
        )

        if age_days <= 1:
            score = FRESHNESS_SCORE[
                "within_24_hours"
            ]

            reason = (
                "Job posted within 24 hours."
            )

            accepted = True

        elif age_days <= 3:
            score = FRESHNESS_SCORE[
                "within_72_hours"
            ]

            reason = (
                "Job posted within 72 hours."
            )

            accepted = True

        elif age_days <= self.max_days_old:
            score = FRESHNESS_SCORE[
                "within_7_days"
            ]

            reason = (
                "Job is within configured "
                "freshness window."
            )

            accepted = True

        else:
            score = FRESHNESS_SCORE[
                "older_than_7_days"
            ]

            reason = (
                "Job exceeds configured "
                "freshness window."
            )

            accepted = False

        return FreshnessDecision(
            accepted=accepted,
            age_days=age_days,
            score=float(score),
            reason=reason,
        )

    def evaluate_job(
        self,
        job: Job,
        now: datetime | None = None,
    ) -> FreshnessDecision:
        return self.evaluate(
            posted_at=job.posted_at,
            now=now,
        )