from __future__ import annotations

from job_search_automation.intelligence.final_selector import (
    FinalSelectionEngine,
)
from job_search_automation.models.job import Job


def make_job(
    *,
    title: str = "Data Analyst",
    company: str = "Test Company",
    location: str = "Mumbai",
    score: float | None = 75.0,
    remote: bool = False,
    searched_role: str = "Data Analyst",
    source: str = "test",
) -> Job:
    return Job(
        searched_role=searched_role,
        source=source,
        title=title,
        company=company,
        location=location,
        job_url=(
            "https://example.com/"
            + title.lower().replace(" ", "-")
        ),
        provider="test",
        description="Test job description.",
        overall_score=score,
        shortlist_likelihood_score=score,
        remote=remote,
    )


def test_apply_now_bucket() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Senior Data Analyst",
        location="Mumbai",
        score=75.0,
    )

    selected = engine.select([job])

    assert len(selected) == 1
    assert selected[0].final_selection_eligible is True
    assert selected[0].final_selection_bucket == "A - Apply Now"
    assert selected[0].final_selection_priority == 2


def test_strong_match_bucket() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Analytics Engineer",
        location="Bengaluru",
        score=65.0,
    )

    selected = engine.select([job])

    assert len(selected) == 1
    assert selected[0].final_selection_eligible is True
    assert selected[0].final_selection_bucket == "B - Strong Match"
    assert selected[0].final_selection_priority == 1


def test_review_bucket() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Risk Operations Analyst",
        location="Remote",
        score=55.0,
        remote=True,
    )

    selected = engine.select([job])

    assert len(selected) == 1
    assert job.final_selection_eligible is True
    assert job.final_selection_bucket == "C - Review"
    assert job.final_selection_priority == 1


def test_low_priority_review_bucket() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Senior Analytics Engineer",
        location="Remote",
        score=53.05,
        remote=True,
    )

    selected = engine.select([job])

    assert len(selected) == 1
    assert job.final_selection_eligible is True
    assert job.final_selection_bucket == "C - Review"
    assert job.final_selection_priority == 1


def test_score_below_relevance_floor_is_rejected() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Data Analyst",
        location="Mumbai",
        score=44.99,
    )

    selected = engine.select([job])

    assert len(selected) == 0
    assert job.final_selection_eligible is False
    assert job.final_selection_bucket == "Rejected"


def test_non_target_role_is_rejected() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Software Engineer",
        location="Mumbai",
        score=90.0,
    )

    selected = engine.select([job])

    assert len(selected) == 0
    assert job.final_selection_eligible is False
    assert job.final_selection_bucket == "Rejected"


def test_non_target_location_is_rejected() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Data Analyst",
        location="New York",
        score=90.0,
    )

    selected = engine.select([job])

    assert len(selected) == 0
    assert job.final_selection_eligible is False
    assert job.final_selection_bucket == "Rejected"


def test_remote_job_is_eligible() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Data Analyst",
        location="Worldwide",
        score=55.0,
        remote=True,
    )

    selected = engine.select([job])

    assert len(selected) == 1
    assert job.final_selection_eligible is True
    assert job.final_selection_bucket == "C - Review"
    assert job.final_selection_priority == 1


def test_worldwide_location_is_treated_as_remote() -> None:
    engine = FinalSelectionEngine()

    job = make_job(
        title="Analytics Engineer",
        location="Worldwide",
        score=53.05,
        remote=False,
    )

    selected = engine.select([job])

    assert len(selected) == 0
    assert job.final_selection_eligible is False
    assert job.final_selection_bucket == "Rejected"


def test_select_persists_decision_metadata() -> None:
    engine = FinalSelectionEngine()

    jobs = [
        make_job(
            title="Senior Data Analyst",
            location="Mumbai",
            score=75.0,
        ),
        make_job(
            title="Analytics Engineer",
            location="Remote",
            score=53.05,
            remote=True,
        ),
        make_job(
            title="Software Engineer",
            location="Mumbai",
            score=90.0,
        ),
    ]

    selected = engine.select(jobs)

    assert len(selected) == 2

    assert selected[0].title == "Senior Data Analyst"
    assert selected[0].final_selection_eligible is True
    assert selected[0].final_selection_bucket == "A - Apply Now"
    assert selected[0].final_selection_priority == 2
    assert selected[0].final_selection_reason
    assert "overall score 75.0" in selected[0].final_selection_reason
    assert selected[0].apply_priority == selected[0].final_selection_priority

    assert selected[1].title == "Analytics Engineer"
    assert selected[1].final_selection_eligible is True
    assert selected[1].final_selection_bucket == "C - Review"
    assert selected[1].final_selection_priority == 1
    assert selected[1].apply_priority == selected[1].final_selection_priority