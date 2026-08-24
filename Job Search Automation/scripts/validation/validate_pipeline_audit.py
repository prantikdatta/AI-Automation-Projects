from __future__ import annotations

from datetime import UTC, datetime

from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
    PipelineStage,
    PipelineStatus,
)


def main() -> None:
    print()
    print("=" * 70)
    print("PIPELINE AUDIT MODEL VALIDATION")
    print("=" * 70)

    audit = JobPipelineAudit(
        job_id="test-001",
        source="Greenhouse",
        company="Stripe",
        title="Risk Analyst",
        location="Mumbai",
        job_url="https://example.com/job/1",
        posted_at=datetime.now(UTC),
        run_id="validation-run",
        searched_role="Risk Analyst",
        searched_location="Mumbai",
        search_bucket="FinTech Analytics",
        search_priority=1,
    )

    print("[PASS] JobPipelineAudit created.")

    audit.record(
        stage=PipelineStage.SEARCH,
        status=PipelineStatus.PASSED,
        reason="Job discovered by provider.",
    )

    print("[PASS] Search stage recorded.")

    audit.record(
        stage=PipelineStage.DEDUPLICATION,
        status=PipelineStatus.PASSED,
        reason="Job is unique.",
        metadata={
            "duplicate_key": "stripe|risk analyst|mumbai",
        },
    )

    print("[PASS] Deduplication stage recorded.")

    audit.record(
        stage=PipelineStage.FRESHNESS,
        status=PipelineStatus.PASSED,
        reason="Job is within freshness window.",
        metadata={
            "age_days": 2,
            "max_days_old": 7,
        },
    )

    print("[PASS] Freshness stage recorded.")

    audit.record(
        stage=PipelineStage.RELEVANCE,
        status=PipelineStatus.REJECTED,
        reason="Role is outside target taxonomy.",
    )

    print("[PASS] Relevance rejection recorded.")

    latest = audit.latest_result(
        PipelineStage.RELEVANCE
    )

    assert latest is not None
    assert latest.status == PipelineStatus.REJECTED

    print("[PASS] Latest stage lookup.")

    assert audit.has_passed(
        PipelineStage.DEDUPLICATION
    )

    print("[PASS] Passed-stage lookup.")

    assert audit.has_failed(
        PipelineStage.RELEVANCE
    )

    print("[PASS] Failed-stage lookup.")

    assert len(audit.stages) == 4

    print("[PASS] Full stage history preserved.")

    assert audit.current_stage == PipelineStage.RELEVANCE
    assert audit.current_status == PipelineStatus.REJECTED

    print("[PASS] Current pipeline state correct.")

    print()
    print("=" * 70)
    print("PIPELINE AUDIT MODEL VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()