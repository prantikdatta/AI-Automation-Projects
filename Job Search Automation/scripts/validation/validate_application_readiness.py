from __future__ import annotations

from job_search_automation.application.decision import ApplicationDecision
from job_search_automation.application.readiness import (
    ApplicationReadinessEngine,
)
from job_search_automation.models.job import Job


def build_job(
    score: float,
    selected: bool = True,
) -> Job:
    job = Job(
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        description=(
            "Senior Data Analyst responsible for analytics, SQL, "
            "business intelligence, stakeholder management, and reporting."
        ),
        job_url="https://example.com/job/123",
        source="test",
        searched_role="Senior Data Analyst",
        provider="test",
    )

    job.overall_score = score
    job.final_selection_eligible = selected
    job.final_selection_bucket = "C - Review"

    return job


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    engine = ApplicationReadinessEngine()

    print("=" * 80)
    print("APPLICATION READINESS VALIDATION")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1. High-quality job
    # ------------------------------------------------------------------
    result = engine.evaluate(
        build_job(75.0)
    )

    require(
        result.decision == ApplicationDecision.READY,
        "75 score must produce READY.",
    )

    require(
        result.eligible is True,
        "75 score must be eligible.",
    )

    print("PASS | score=75.00 -> READY")

    # ------------------------------------------------------------------
    # 2. Tailoring candidate
    # ------------------------------------------------------------------
    result = engine.evaluate(
        build_job(65.0)
    )

    require(
        result.decision == ApplicationDecision.READY_WITH_TAILORING,
        "65 score must produce READY_WITH_TAILORING.",
    )

    require(
        result.eligible is True,
        "65 score must remain eligible with tailoring.",
    )

    print("PASS | score=65.00 -> READY_WITH_TAILORING")

    # ------------------------------------------------------------------
    # 3. Weak candidate
    # ------------------------------------------------------------------
    result = engine.evaluate(
        build_job(57.75)
    )

    require(
        result.decision == ApplicationDecision.MANUAL_REVIEW,
        "57.75 score must produce MANUAL_REVIEW.",
    )

    require(
        result.eligible is False,
        "57.75 score must not be application eligible.",
    )

    print("PASS | score=57.75 -> MANUAL_REVIEW")

    # ------------------------------------------------------------------
    # 4. Very weak candidate
    # ------------------------------------------------------------------
    result = engine.evaluate(
        build_job(53.05)
    )

    require(
        result.decision == ApplicationDecision.MANUAL_REVIEW,
        "53.05 score must produce MANUAL_REVIEW.",
    )

    require(
        result.eligible is False,
        "53.05 score must not be application eligible.",
    )

    print("PASS | score=53.05 -> MANUAL_REVIEW")

    # ------------------------------------------------------------------
    # 5. Non-selected job
    # ------------------------------------------------------------------
    result = engine.evaluate(
        build_job(
            score=90.0,
            selected=False,
        )
    )

    require(
        result.decision == ApplicationDecision.REJECTED,
        "Non-selected job must be REJECTED.",
    )

    require(
        result.eligible is False,
        "Non-selected job must not be eligible.",
    )

    print("PASS | non-selected -> REJECTED")

    # ------------------------------------------------------------------
    # 6. Missing required information
    # ------------------------------------------------------------------
    job = build_job(80.0)
    job.job_url = ""

    result = engine.evaluate(job)

    require(
        result.decision == ApplicationDecision.MANUAL_REVIEW,
        "Missing job URL must produce MANUAL_REVIEW.",
    )

    require(
        result.eligible is False,
        "Missing required information must not be eligible.",
    )

    require(
        "job_url" in result.missing_information,
        "job_url must be reported as missing.",
    )

    print("PASS | missing job_url -> MANUAL_REVIEW")

    print("=" * 80)
    print("APPLICATION READINESS VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()