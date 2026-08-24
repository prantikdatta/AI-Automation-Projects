from __future__ import annotations

from job_search_automation.application.decision import (
    ApplicationDecision,
)
from job_search_automation.application.readiness import (
    ApplicationReadinessEngine,
)
from job_search_automation.models.job import Job


def make_job(
    score: float,
    eligible: bool = True,
    description: str = "Python SQL Power BI analytics project.",
) -> Job:
    return Job(
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        description=description,
        job_url="https://example.com/job",
        source="test",
        provider="test",
        searched_role="Senior Data Analyst",
        overall_score=score,
        final_selection_eligible=eligible,
        final_selection_bucket="Apply Now",
    )


def test_high_score_is_ready():
    engine = ApplicationReadinessEngine()

    result = engine.evaluate(
        make_job(85)
    )

    assert result.decision == ApplicationDecision.READY
    assert result.eligible is True


def test_medium_score_requires_tailoring():
    engine = ApplicationReadinessEngine()

    result = engine.evaluate(
        make_job(65)
    )

    assert (
        result.decision
        == ApplicationDecision.READY_WITH_TAILORING
    )
    assert result.eligible is True


def test_low_score_requires_manual_review():
    engine = ApplicationReadinessEngine()

    result = engine.evaluate(
        make_job(50)
    )

    assert (
        result.decision
        == ApplicationDecision.MANUAL_REVIEW
    )
    assert result.eligible is False


def test_unselected_job_is_rejected():
    engine = ApplicationReadinessEngine()

    result = engine.evaluate(
        make_job(
            90,
            eligible=False,
        )
    )

    assert result.decision == ApplicationDecision.REJECTED
    assert result.eligible is False


def test_missing_description_requires_manual_review():
    engine = ApplicationReadinessEngine()

    result = engine.evaluate(
        make_job(
            85,
            description="",
        )
    )

    assert (
        result.decision
        == ApplicationDecision.MANUAL_REVIEW
    )
    assert result.eligible is False
    assert "description" in result.missing_information