from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.application.execution import (
    ApplicationExecutionError,
    ApplicationExecutor,
)
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    QueueStatus,
)


def make_item(
    *,
    eligible: bool = True,
    status: QueueStatus | None = None,
) -> ApplicationQueueItem:
    queue_status = (
        status
        if status is not None
        else (
            QueueStatus.READY
            if eligible
            else QueueStatus.MANUAL_REVIEW
        )
    )

    return ApplicationQueueItem(
        job_id="job-001",
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        job_url="https://example.com/job-001",
        provider="test",
        searched_role="Data Analyst",
        overall_score=85.0,
        score=85.0,
        selection_bucket="A - Apply Now",
        readiness_decision=queue_status,
        queue_status=queue_status,
        eligible=eligible,
        reason=(
            "Eligible for application."
            if eligible
            else "Requires manual review."
        ),
        source="test",
        resume_match_score=85.0,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=[],
        application_url=None,
    )


def test_executor_returns_ready_without_handler() -> None:
    executor = ApplicationExecutor()

    result = executor.execute(
        make_item(
            eligible=True,
            status=QueueStatus.READY,
        )
    )

    assert result.job_id == "job-001"
    assert result.status == "READY"
    assert "no external handler configured" in result.message
    assert result.metadata["queue_status"] == "READY"


def test_executor_rejects_ineligible_item() -> None:
    executor = ApplicationExecutor()

    try:
        executor.execute(
            make_item(
                eligible=False,
                status=QueueStatus.MANUAL_REVIEW,
            )
        )
    except ApplicationExecutionError as exc:
        assert "not eligible" in str(exc)
    else:
        raise AssertionError(
            "Expected ApplicationExecutionError."
        )


def test_executor_calls_external_handler() -> None:
    calls: list[str] = []

    def handler(item: ApplicationQueueItem) -> dict:
        calls.append(item.job_id)

        return {
            "status": "SUBMITTED",
            "message": "Application submitted.",
            "metadata": {
                "channel": "test",
            },
        }

    executor = ApplicationExecutor(
        handler=handler,
    )

    result = executor.execute(
        make_item(
            eligible=True,
            status=QueueStatus.READY,
        )
    )

    assert calls == ["job-001"]
    assert result.job_id == "job-001"
    assert result.status == "SUBMITTED"
    assert result.message == "Application submitted."
    assert result.metadata["channel"] == "test"


def test_executor_wraps_handler_failure() -> None:
    def handler(
        item: ApplicationQueueItem,
    ) -> dict:
        raise RuntimeError(
            "simulated external failure"
        )

    executor = ApplicationExecutor(
        handler=handler,
    )

    try:
        executor.execute(
            make_item(
                eligible=True,
                status=QueueStatus.READY,
            )
        )
    except ApplicationExecutionError as exc:
        assert "Application execution failed" in str(exc)
        assert "simulated external failure" in str(exc)
    else:
        raise AssertionError(
            "Expected ApplicationExecutionError."
        )


def test_execute_many_preserves_success_and_failure() -> None:
    def handler(
        item: ApplicationQueueItem,
    ) -> dict:
        if item.job_id == "job-002":
            raise RuntimeError(
                "job-002 failed"
            )

        return {
            "status": "SUBMITTED",
            "message": "Submitted.",
        }

    first = make_item(
        eligible=True,
        status=QueueStatus.READY,
    )

    second = make_item(
        eligible=True,
        status=QueueStatus.READY,
    )
    second.job_id = "job-002"

    executor = ApplicationExecutor(
        handler=handler,
    )

    results = executor.execute_many(
        [first, second]
    )

    assert len(results) == 2

    assert results[0].job_id == "job-001"
    assert results[0].status == "SUBMITTED"

    assert results[1].job_id == "job-002"
    assert results[1].status == "FAILED"
    assert "job-002 failed" in results[1].message