from __future__ import annotations

from datetime import datetime
from datetime import timezone

from job_search_automation.application.queue import (
    ApplicationQueueItem,
    QueueStatus,
)
from job_search_automation.services.google_sheets.application_queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
    application_queue_item_to_row,
)


def make_item() -> ApplicationQueueItem:
    return ApplicationQueueItem(
        job_id="stripe|data analyst|mumbai|https://example.com/job",
        title="Data Analyst",
        company="Stripe",
        location="Mumbai",
        job_url="https://example.com/job",
        score=87.5,
        decision=QueueStatus.READY,
        searched_role="Data Analyst",
        source="test",
        resume_match_score=91.0,
        created_at=datetime(
            2026,
            8,
            11,
            10,
            30,
            tzinfo=timezone.utc,
        ).isoformat(),
        status=QueueStatus.READY,
        notes=[
            "Strong role match",
            "Good resume alignment",
        ],
    )


def test_application_queue_headers_are_defined():
    assert APPLICATION_QUEUE_HEADERS
    assert "Job ID" in APPLICATION_QUEUE_HEADERS
    assert "Company" in APPLICATION_QUEUE_HEADERS
    assert "Role" in APPLICATION_QUEUE_HEADERS
    assert "Job URL" in APPLICATION_QUEUE_HEADERS
    assert "Application Status" in APPLICATION_QUEUE_HEADERS


def test_mapper_returns_same_number_of_columns_as_headers():
    row = application_queue_item_to_row(
        make_item()
    )

    assert len(row) == len(
        APPLICATION_QUEUE_HEADERS
    )


def test_mapper_preserves_core_job_information():
    row = application_queue_item_to_row(
        make_item()
    )

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Company")
    ] == "Stripe"

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Role")
    ] == "Data Analyst"

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Location")
    ] == "Mumbai"

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Job URL")
    ] == "https://example.com/job"


def test_mapper_preserves_scores():
    row = application_queue_item_to_row(
        make_item()
    )

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Overall Score")
    ] == "87.5"

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Resume Match Score")
    ] == "91.0"


def test_mapper_serializes_decision_and_status():
    row = application_queue_item_to_row(
        make_item()
    )

    assert row[
        APPLICATION_QUEUE_HEADERS.index(
            "Application Decision"
        )
    ] == "READY"

    assert row[
        APPLICATION_QUEUE_HEADERS.index(
            "Application Status"
        )
    ] == "READY"


def test_mapper_combines_notes():
    row = application_queue_item_to_row(
        make_item()
    )

    assert row[
        APPLICATION_QUEUE_HEADERS.index("Notes")
    ] == (
        "Strong role match | "
        "Good resume alignment"
    )


def test_mapper_handles_optional_values():
    item = make_item()
    item.resume_match_score = None

    row = application_queue_item_to_row(item)

    assert row[
        APPLICATION_QUEUE_HEADERS.index(
            "Resume Match Score"
        )
    ] == ""

    assert row[
        APPLICATION_QUEUE_HEADERS.index(
            "Application URL"
        )
    ] == ""