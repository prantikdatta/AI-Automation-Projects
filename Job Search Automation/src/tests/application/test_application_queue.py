from __future__ import annotations

from job_search_automation.application.queue import (
    ApplicationQueueStatus,
)
from job_search_automation.application.queue_builder import (
    ApplicationQueueBuilder,
)
from job_search_automation.models.job import Job


def make_job(
    score: float,
    eligible: bool = True,
) -> Job:
    return Job(
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        description="Python SQL Power BI analytics.",
        job_url="https://example.com/job",
        source="test",
        provider="test",
        searched_role="Senior Data Analyst",
        overall_score=score,
        final_selection_eligible=eligible,
        final_selection_bucket="Apply Now",
    )


def test_queue_contains_eligible_job() -> None:
    builder = ApplicationQueueBuilder()

    queue = builder.build(
        [make_job(85)]
    )

    assert len(queue) == 1
    assert (
        queue[0].queue_status
        == ApplicationQueueStatus.QUEUED
    )
    assert queue[0].title == "Senior Data Analyst"


def test_queue_excludes_rejected_job() -> None:
    builder = ApplicationQueueBuilder()

    queue = builder.build(
        [
            make_job(
                85,
                eligible=False,
            )
        ]
    )

    assert queue == []


def test_medium_score_enters_tailoring_queue() -> None:
    builder = ApplicationQueueBuilder()

    queue = builder.build(
        [make_job(65)]
    )

    assert len(queue) == 1
    assert (
        queue[0].queue_status
        == ApplicationQueueStatus.TAILORING_REQUIRED
    )


def test_queue_preserves_searched_role() -> None:
    builder = ApplicationQueueBuilder()

    queue = builder.build(
        [make_job(85)]
    )

    assert (
        queue[0].searched_role
        == "Senior Data Analyst"
    )


def test_queue_generates_stable_job_id() -> None:
    builder = ApplicationQueueBuilder()

    first = builder.build(
        [make_job(85)]
    )[0]

    second = builder.build(
        [make_job(85)]
    )[0]

    assert first.job_id == second.job_id