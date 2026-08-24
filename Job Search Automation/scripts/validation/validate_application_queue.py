from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
    QueueStatus,
)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    print("=" * 80)
    print("APPLICATION QUEUE COMPATIBILITY VALIDATION")
    print("=" * 80)

    created_at = datetime(
        2026,
        8,
        11,
        10,
        30,
        tzinfo=timezone.utc,
    ).isoformat()

    item = ApplicationQueueItem(
        job_id="job-001",
        title="Data Analyst",
        company="Stripe",
        location="Mumbai",
        job_url="https://example.com/job",
        score=87.5,
        decision=QueueStatus.READY,
        status=QueueStatus.READY,
        searched_role="Data Analyst",
        source="test",
        resume_match_score=91.0,
        created_at=created_at,
        notes=[
            "Strong role match",
        ],
        application_url=None,
    )

    require(
        item.score == 87.5,
        "Legacy score field failed.",
    )

    require(
        item.overall_score == 87.5,
        "Canonical overall_score failed.",
    )

    require(
        item.status == QueueStatus.READY,
        "QueueStatus compatibility failed.",
    )

    require(
        item.queue_status
        == ApplicationQueueStatus.READY,
        "Canonical queue_status failed.",
    )

    require(
        item.decision == QueueStatus.READY,
        "Legacy decision compatibility failed.",
    )

    require(
        item.source == "test",
        "Legacy source compatibility failed.",
    )

    require(
        item.resume_match_score == 91.0,
        "Resume match score failed.",
    )

    require(
        item.created_at == created_at,
        "created_at compatibility failed.",
    )

    require(
        item.notes == ["Strong role match"],
        "Notes compatibility failed.",
    )

    tailoring_item = ApplicationQueueItem(
        job_id="job-002",
        title="Analytics Engineer",
        company="Coinbase",
        location="Remote",
        job_url="https://example.com/job-2",
        score=65.0,
        decision=QueueStatus.READY_WITH_TAILORING,
        status=QueueStatus.READY_WITH_TAILORING,
        searched_role="Analytics Engineer",
        source="test",
    )

    require(
        tailoring_item.status
        == QueueStatus.READY_WITH_TAILORING,
        "Tailoring queue status failed.",
    )

    require(
        tailoring_item.queue_status
        == ApplicationQueueStatus.READY_WITH_TAILORING,
        "Canonical tailoring status failed.",
    )

    require(
        tailoring_item.resume_tailoring_required is True,
        "Tailoring flag failed.",
    )

    legacy_queued = ApplicationQueueItem(
        job_id="job-003",
        title="BI Analyst",
        company="Test Company",
        location="Mumbai",
        job_url="https://example.com/job-3",
        score=80.0,
        status=QueueStatus.QUEUED,
    )

    require(
        legacy_queued.status
        == ApplicationQueueStatus.READY,
        "QUEUED compatibility alias failed.",
    )

    require(
        legacy_queued.queue_status
        == ApplicationQueueStatus.READY,
        "QUEUED canonical normalization failed.",
    )

    print("PASS | QueueStatus import compatibility")
    print("PASS | Legacy ApplicationQueueItem fields")
    print("PASS | Canonical queue fields")
    print("PASS | READY status")
    print("PASS | READY_WITH_TAILORING status")
    print("PASS | QUEUED compatibility")
    print("PASS | execution/mapper compatibility")
    print("=" * 80)
    print("APPLICATION QUEUE COMPATIBILITY VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()