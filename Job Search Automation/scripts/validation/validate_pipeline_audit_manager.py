from __future__ import annotations

from datetime import UTC, datetime

from job_search_automation.models.job import Job
from job_search_automation.models.pipeline_audit import (
    PipelineStage,
    PipelineStatus,
)
from job_search_automation.pipeline.audit_manager import (
    PipelineAuditManager,
)


def make_job() -> Job:
    return Job(
        title="Data Analyst",
        company="Validation Corp",
        location="Mumbai",
        description="Data analytics role.",
        job_url="https://example.com/jobs/001",
        source="validation",
        provider="validation",
        searched_role="Data Analyst",
        posted_at=datetime.now(UTC),
        remote=False,
        skills=[],
        raw={},
    )


def main() -> None:
    print()
    print("=" * 70)
    print("PIPELINE AUDIT MANAGER VALIDATION")
    print("=" * 70)

    job = make_job()

    manager = PipelineAuditManager(
        run_id="validation-run-001"
    )

    audit = manager.create(job)

    if audit.job_id != job.job_url:
        raise AssertionError(
            "Audit job ID is incorrect."
        )

    if audit.run_id != "validation-run-001":
        raise AssertionError(
            "Run ID is incorrect."
        )

    print(
        "[PASS] Audit created from canonical job."
    )

    same_audit = manager.create(job)

    if same_audit is not audit:
        raise AssertionError(
            "Duplicate audit object created for same job."
        )

    print(
        "[PASS] One audit maintained per job."
    )

    manager.record_pass(
        job,
        PipelineStage.SEARCH,
        reason="Job discovered.",
        metadata={
            "provider": job.provider,
        },
    )

    manager.record_pass(
        job,
        PipelineStage.DEDUPLICATION,
        reason="Unique job.",
    )

    manager.record_pass(
        job,
        PipelineStage.FRESHNESS,
        reason="Posted within 7 days.",
        metadata={
            "age_days": 2,
            "max_days_old": 7,
        },
    )

    audit = manager.get(job)

    if len(audit.stages) != 3:
        raise AssertionError(
            f"Expected 3 stages, got {len(audit.stages)}."
        )

    print(
        "[PASS] Pipeline stages recorded."
    )

    if (
        audit.current_stage
        != PipelineStage.FRESHNESS
    ):
        raise AssertionError(
            "Current stage is incorrect."
        )

    if (
        audit.current_status
        != PipelineStatus.PASSED
    ):
        raise AssertionError(
            "Current status is incorrect."
        )

    print(
        "[PASS] Current pipeline state correct."
    )

    if not audit.has_passed(
        PipelineStage.SEARCH
    ):
        raise AssertionError(
            "Search stage was not recorded as passed."
        )

    print(
        "[PASS] Stage lookup works."
    )

    search_result = audit.latest_result(
        PipelineStage.SEARCH
    )

    if search_result is None:
        raise AssertionError(
            "Search result missing."
        )

    if (
        search_result.metadata.get("provider")
        != "validation"
    ):
        raise AssertionError(
            "Stage metadata was not preserved."
        )

    print(
        "[PASS] Stage metadata preserved."
    )

    audits = manager.all_audits()

    if len(audits) != 1:
        raise AssertionError(
            "Expected exactly one audit."
        )

    print(
        "[PASS] Audit collection correct."
    )

    print()
    print("=" * 70)
    print("PIPELINE AUDIT MANAGER VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()