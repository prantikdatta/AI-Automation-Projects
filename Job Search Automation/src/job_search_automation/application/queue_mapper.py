from __future__ import annotations

from typing import Any

from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)


APPLICATION_QUEUE_HEADERS: list[str] = [
    "Created At",
    "Job ID",
    "Source",
    "Searched Role",
    "Company",
    "Role",
    "Location",
    "Job URL",
    "Overall Score",
    "Resume Match Score",
    "Decision",
    "Queue Status",
    "Eligibility",
    "Tailoring Required",
]


def application_queue_to_row(
    item: ApplicationQueueItem,
) -> list[str]:
    """
    Convert one ApplicationQueueItem into a Google Sheets row.

    No business logic is performed here.
    """

    return [
        _datetime(item.created_at),
        str(item.job_id or ""),
        _string(
            getattr(
                item,
                "source",
                "",
            )
        ),
        str(item.searched_role or ""),
        str(item.company or ""),
        str(item.title or ""),
        str(item.location or ""),
        str(item.job_url or ""),
        _number(item.score),
        _optional_number(
            item.resume_match_score
        ),
        _enum(item.decision),
        _queue_status(item.status),
        _boolean(item.eligible),
        _boolean(
            getattr(
                item,
                "resume_tailoring_required",
                False,
            )
        ),
    ]


def application_queue_rows(
    items: list[ApplicationQueueItem],
) -> list[list[str]]:
    """
    Convert application queue items into Sheets rows.
    """

    return [
        application_queue_to_row(item)
        for item in items
    ]


def _datetime(value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def _number(
    value: float | int | None,
) -> str:
    if value is None:
        return ""

    return f"{float(value):.2f}"


def _optional_number(
    value: float | int | None,
) -> str:
    if value is None:
        return ""

    return f"{float(value):.2f}"


def _enum(
    value: Any,
) -> str:
    if value is None:
        return ""

    enum_value = getattr(
        value,
        "value",
        value,
    )

    return str(enum_value)


def _queue_status(
    value: Any,
) -> str:
    """
    Serialize queue status using the legacy-compatible operational
    names expected by the existing application queue contract.
    """

    if value is None:
        return ""

    if isinstance(
        value,
        ApplicationQueueStatus,
    ):
        if value == ApplicationQueueStatus.READY:
            return "QUEUED"

        if value == ApplicationQueueStatus.READY_WITH_TAILORING:
            return "TAILORING_REQUIRED"

        if value == ApplicationQueueStatus.MANUAL_REVIEW:
            return "MANUAL_REVIEW"

        if value == ApplicationQueueStatus.REJECTED:
            return "REJECTED"

    raw = str(
        getattr(
            value,
            "value",
            value,
        )
    ).strip().upper()

    aliases = {
        "READY": "QUEUED",
        "QUEUED": "QUEUED",
        "READY_WITH_TAILORING": "TAILORING_REQUIRED",
        "TAILORING_REQUIRED": "TAILORING_REQUIRED",
        "MANUAL_REVIEW": "MANUAL_REVIEW",
        "REJECTED": "REJECTED",
    }

    return aliases.get(
        raw,
        raw,
    )


def _boolean(
    value: Any,
) -> str:
    return "TRUE" if bool(value) else "FALSE"


def _string(
    value: Any,
) -> str:
    if value is None:
        return ""

    return str(value)