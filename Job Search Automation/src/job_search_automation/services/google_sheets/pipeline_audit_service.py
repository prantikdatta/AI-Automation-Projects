from __future__ import annotations

from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
)
from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)
from job_search_automation.services.google_sheets.pipeline_audit_mapper import (
    PIPELINE_AUDIT_HEADERS,
    audit_to_rows,
)


class PipelineAuditSheetsService:
    """
    Exports pipeline audit history to Google Sheets.
    """

    def __init__(
        self,
        sheets_service: GoogleSheetsService | None = None,
    ) -> None:
        self.sheets = (
            sheets_service
            or GoogleSheetsService()
        )

    def export_audit(
        self,
        audits: list[JobPipelineAudit],
    ) -> int:
        rows: list[list[str]] = []

        for audit in audits:
            rows.extend(
                audit_to_rows(audit)
            )

        if not rows:
            return 0

        self.sheets.append_audit_rows(
            headers=PIPELINE_AUDIT_HEADERS,
            rows=rows,
        )

        return len(rows)

    def export_single(
        self,
        audit: JobPipelineAudit,
    ) -> int:
        return self.export_audit(
            [audit]
        )