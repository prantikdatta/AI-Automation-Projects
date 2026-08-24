from __future__ import annotations

from datetime import UTC, datetime

from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
    PipelineStage,
    PipelineStatus,
)
from job_search_automation.services.google_sheets.pipeline_audit_mapper import (
    PIPELINE_AUDIT_HEADERS,
    audit_to_rows,
)


def main() -> None:
    print()
    print("=" * 70)
    print("PIPELINE AUDIT EXPORT VALIDATION")
    print("=" * 70)

    audit = JobPipelineAudit(
        job_id="validation-job-001",
        source="validation",
        company="Validation Corp",
        title="Senior Data Analyst",
        location="Mumbai",
        job_url="https://example.com/job/001",
        posted_at=datetime.now(UTC),
        run_id="validation-run-001",
        searched_role="Data Analyst",
        searched_location="Mumbai",
        search_bucket="Analytics",
        search_priority=1,
        final_score=87.5,
        final_rank=1,
        final_bucket="Excellent",
        final_status="selected",
    )

    audit.record(
        stage=PipelineStage.SEARCH,
        status=PipelineStatus.PASSED,
        reason="Job discovered.",
        metadata={
            "provider": "validation",
        },
    )

    audit.record(
        stage=PipelineStage.DEDUPLICATION,
        status=PipelineStatus.PASSED,
        reason="Unique job.",
        metadata={
            "provider": "validation",
        },
    )

    audit.record(
        stage=PipelineStage.FRESHNESS,
        status=PipelineStatus.PASSED,
        reason="Posted within 7 days.",
        metadata={
            "provider": "validation",
            "age_days": 2,
        },
    )

    rows = audit_to_rows(audit)

    if not rows:
        raise AssertionError(
            "Audit mapper produced no rows."
        )

    print(
        f"[PASS] Audit rows generated: {len(rows)}"
    )

    if not PIPELINE_AUDIT_HEADERS:
        raise AssertionError(
            "Pipeline audit headers are empty."
        )

    print(
        "[PASS] Pipeline audit headers populated."
    )

    expected_width = len(
        PIPELINE_AUDIT_HEADERS
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        if len(row) != expected_width:
            raise AssertionError(
                f"Audit row {index} has "
                f"{len(row)} columns; expected "
                f"{expected_width}."
            )

    print(
        "[PASS] Audit rows match header width."
    )

    required_headers = {
        "Run ID",
        "Job ID",
        "Source",
        "Searched Role",
        "Title",
        "Company",
        "Location",
        "Job URL",
        "Stage",
        "Status",
        "Reason",
        "Current Stage",
        "Current Status",
        "Final Score",
        "Final Rank",
        "Recorded At",
    }

    missing = (
        required_headers
        - set(PIPELINE_AUDIT_HEADERS)
    )

    if missing:
        raise AssertionError(
            "Missing audit headers: "
            + ", ".join(sorted(missing))
        )

    print(
        "[PASS] Required audit headers present."
    )

    stages = {
        row[
            PIPELINE_AUDIT_HEADERS.index("Stage")
        ]
        for row in rows
    }

    expected_stages = {
        "search",
        "deduplication",
        "freshness",
    }

    if not expected_stages.issubset(stages):
        raise AssertionError(
            "Not all expected pipeline stages "
            "were exported."
        )

    print(
        "[PASS] Search, deduplication, and freshness "
        "stages exported."
    )

    job_ids = {
        row[
            PIPELINE_AUDIT_HEADERS.index("Job ID")
        ]
        for row in rows
    }

    if job_ids != {"validation-job-001"}:
        raise AssertionError(
            "Unexpected job IDs in audit export."
        )

    print(
        "[PASS] Job identity preserved."
    )

    run_ids = {
        row[
            PIPELINE_AUDIT_HEADERS.index("Run ID")
        ]
        for row in rows
    }

    if run_ids != {"validation-run-001"}:
        raise AssertionError(
            "Run ID was not preserved."
        )

    print(
        "[PASS] Run ID preserved."
    )

    final_scores = {
        row[
            PIPELINE_AUDIT_HEADERS.index("Final Score")
        ]
        for row in rows
    }

    if final_scores != {"87.5"}:
        raise AssertionError(
            "Final score was not preserved."
        )

    print(
        "[PASS] Final ranking information preserved."
    )

    print()
    print("=" * 70)
    print("PIPELINE AUDIT EXPORT VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()