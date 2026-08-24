from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.config.freshness_rules import (
    FRESHNESS_SCORE,
    MAX_JOB_AGE_DAYS,
)
from job_search_automation.intelligence.models import (
    FreshnessScoreResult,
)


class FreshnessScorer:
    """
    Scores jobs according to posting age.
    """

    def score(
        self,
        posted_at: datetime | None,
    ) -> FreshnessScoreResult:

        if posted_at is None:

            return FreshnessScoreResult(

                score=0,

                age_hours=0,

                age_days=0,

                freshness_bucket="Unknown",

                explanation=(
                    "Job posting date is unavailable."
                ),

                confidence=0.0,

                metadata={
                    "posted_at_available": False,
                },

            )

        if posted_at.tzinfo is None:

            posted_at = posted_at.replace(
                tzinfo=timezone.utc
            )

        age = (
            datetime.now(timezone.utc)
            - posted_at
        )

        hours = round(
            age.total_seconds() / 3600,
            2,
        )

        days = age.days

        if days > MAX_JOB_AGE_DAYS:

            bucket = "Expired"

            score = FRESHNESS_SCORE["expired"]

            explanation = (
                "Job is older than the maximum allowed age."
            )

        elif hours <= 24:

            bucket = "Today"

            score = FRESHNESS_SCORE["today"]

            explanation = (
                "Posted within the last 24 hours."
            )

        elif hours <= 72:

            bucket = "Recent"

            score = FRESHNESS_SCORE["recent"]

            explanation = (
                "Posted within the last 72 hours."
            )

        else:

            bucket = "This Week"

            score = FRESHNESS_SCORE["week"]

            explanation = (
                "Posted within the last seven days."
            )

        return FreshnessScoreResult(

            score=score,

            age_hours=hours,

            age_days=days,

            freshness_bucket=bucket,

            explanation=explanation,

            confidence=1.0,

            metadata={

                "posted_at_available": True,

                "age_hours": hours,

                "age_days": days,

                "bucket": bucket,

            },

        )