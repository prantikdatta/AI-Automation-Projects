from __future__ import annotations

from typing import List

from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
)


PIPELINE_AUDIT_HEADERS: List[str] = [
    "Run ID",
    "Job ID",
    "Source",
    "Provider",
    "Searched Role",
    "Searched Location",
    "Search Bucket",
    "Search Priority",
    "Title",
    "Company",
    "Location",
    "Job URL",
    "Posted At",
    "Stage",
    "Status",
    "Reason",
    "Metadata",
    "Current Stage",
    "Current Status",
    "Final Score",
    "Final Rank",
    "Final Bucket",
    "Final Status",
    "Recorded At",
]


def audit_to_rows(
    audit: JobPipelineAudit,
) -> List[List[str]]:
    """
    Convert one JobPipelineAudit into one Google Sheets
    row per recorded pipeline stage.
    """

    rows: List[List[str]] = []

    for result in audit.stages:
        provider = result.metadata.get(
            "provider",
            "",
        )

        metadata = dict(result.metadata)

        metadata_text = ", ".join(
            f"{key}={value}"
            for key, value in metadata.items()
            if key != "provider"
        )

        rows.append(
            [
                audit.run_id or "",
                audit.job_id,
                audit.source,
                str(provider),
                audit.searched_role or "",
                audit.searched_location or "",
                audit.search_bucket or "",
                (
                    str(audit.search_priority)
                    if audit.search_priority is not None
                    else ""
                ),
                audit.title or "",
                audit.company or "",
                audit.location or "",
                audit.job_url or "",
                (
                    audit.posted_at.isoformat()
                    if audit.posted_at
                    else ""
                ),
                result.stage.value,
                result.status.value,
                result.reason or "",
                metadata_text,
                audit.current_stage.value,
                audit.current_status.value,
                (
                    str(audit.final_score)
                    if audit.final_score is not None
                    else ""
                ),
                (
                    str(audit.final_rank)
                    if audit.final_rank is not None
                    else ""
                ),
                audit.final_bucket or "",
                audit.final_status or "",
                result.evaluated_at.isoformat(),
            ]
        )

    return rows


def audit_to_row(
    audit: JobPipelineAudit,
) -> List[List[str]]:
    """
    Backward-compatible wrapper for existing validation
    scripts.
    """

    return audit_to_rows(audit)