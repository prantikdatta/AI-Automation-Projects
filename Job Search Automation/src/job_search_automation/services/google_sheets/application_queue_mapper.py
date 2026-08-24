from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.application.queue import (
    ApplicationQueueItem,
)


APPLICATION_QUEUE_HEADERS = [
    "Run Date",
    "Job ID",
    "Company",
    "Role",
    "Location",
    "Job URL",
    "Overall Score",
    "Resume Match Score",
    "Searched Role",
    "Application Decision",
    "Application Status",
    "Application URL",
    "Notes",
    "Created At",
]


def _format_datetime(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def _format_run_date(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.date().isoformat()

    value = str(value).strip()

    if not value:
        return ""

    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return value[:10]


def application_queue_item_to_row(
    item: ApplicationQueueItem,
) -> list[str]:
    """
    Convert an ApplicationQueueItem into a Google Sheets row.

    The mapper is deliberately independent of gspread.
    """

    run_date = _format_run_date(item.created_at)

    notes = " | ".join(
        str(note).strip()
        for note in item.notes
        if str(note).strip()
    )

    application_url = getattr(
        item,
        "application_url",
        None,
    )

    return [
        run_date,
        str(item.job_id),
        str(item.company),
        str(item.title),
        str(item.location),
        str(item.job_url),
        str(item.score),
        (
            ""
            if item.resume_match_score is None
            else str(item.resume_match_score)
        ),
        str(item.searched_role),
        str(item.decision.value),
        str(item.status.value),
        str(application_url or ""),
        notes,
        _format_datetime(item.created_at),
    ]