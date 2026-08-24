from __future__ import annotations

from datetime import UTC, datetime

from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
    PipelineStage,
    PipelineStatus,
)
from job_search_automation.services.google_sheets.pipeline_audit_service import (
    PipelineAuditSheetsService,
)


class FakeSheetsService:
    def __init__(self) -> None:
        self.headers = []
        self.rows = []

    def append_jobs(
        self,
        headers,
        rows,
    ) -> None:
        self.headers = headers
        self.rows.extend(rows)


def main() -> None:
    print()
    print("=" * 70)
    print("PIPELINE AUDIT SHEETS SERVICE VALIDATION")
    print("=" * 70)

    audit = JobPipelineAudit(
        job_id="validation-job-001",
        source="validation",
        company="Validation Corp",
        title="Data Analyst",
        location="Mumbai",
        job_url="https://example.com/job/001",
        posted_at=datetime.now(UTC),
        run_id="validation-run-001",
        searched_role="Data Analyst",
        searched_location="Mumbai",
    )

    audit.record(
        stage=PipelineStage.SEARCH,
        status=PipelineStatus.PASSED,
        reason="Job discovered.",
    )

    audit.record(
        stage=PipelineStage.DEDUPLICATION,
        status=PipelineStatus.PASSED,
        reason="Unique job.",
    )

    fake_sheets = FakeSheetsService()

    service = PipelineAuditSheetsService(
        sheets_service=fake_sheets,
    )

    exported = service.export_audit(
        [audit]
    )

    if exported != 2:
        raise AssertionError(
            f"Expected 2 exported rows, got {exported}."
        )

    print(
        "[PASS] Audit stages exported."
    )

    if len(fake_sheets.rows) != 2:
        raise AssertionError(
            "Unexpected number of sheet rows."
        )

    print(
        "[PASS] Sheet row count correct."
    )

    if not fake_sheets.headers:
        raise AssertionError(
            "Sheet headers were not populated."
        )

    print(
        "[PASS] Sheet headers populated."
    )

    if len(fake_sheets.rows[0]) != len(
        fake_sheets.headers
    ):
        raise AssertionError(
            "Audit row/header width mismatch."
        )

    print(
        "[PASS] Audit rows match headers."
    )

    print()
    print("=" * 70)
    print("PIPELINE AUDIT SHEETS SERVICE VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()